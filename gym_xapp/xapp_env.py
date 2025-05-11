#!/usr/bin/env python3

import gymnasium as gym
import numpy as np
import torch as th
import signal
import threading
import queue
import os
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from my_xapp import MonRcApp
from enum import Enum
from datetime import date

class xAppEnv(gym.Env):
    def __init__(self, xapp: MonRcApp, queue: queue.Queue, n_steps: int):
        super(xAppEnv, self).__init__()
        # DRL Action + State
        self.current_step = 0
        self.n_steps = n_steps
        self.observation_space = spaces.Box(low=-1, high=1, shape=(12,), dtype=np.float32)
        self.action_space = spaces.MultiDiscrete([3, 3]) # Selects 1 UE, changes PRB limit
        self.state = np.zeros(12)
        self.kpm_queue = queue

        # Values specific for the use case
        # Got by trial and error, for 10MHz bandwidth
        self.max_throughput = 29712
        self.max_prbs = 45
        self.max_packets = 1000
        self.ues = 3
        self.prb_diff = 3
        self.prbs = [int(self.max_prbs/3), int(self.max_prbs/3), int(self.max_prbs/3)]

        self.xapp = xapp
        self.xapp_thread = threading.Thread(target=self.xapp.start)
        self.xapp_thread.start()

    def reset(self, seed=None, options=None):
        self.current_step = 0
        self.prbs = [int(self.max_prbs/3), int(self.max_prbs/3), int(self.max_prbs/3)]
        self._apply_prbs()
        self.state = np.zeros(12, dtype=np.float32)
        return self.state, {}

    def step(self, action):
        # Action: [UE index, PRB change]
        ue_idx, prb_change = action
        prb_delta = {0: -self.prb_diff, 1: 0, 2: self.prb_diff}[prb_change]
        
        # Adjust PRBs with constraints
        new_prbs = self.prbs[ue_idx] + prb_delta
        legal_action = False
        if 0 <= new_prbs <= self.max_prbs and sum(self.prbs) - self.prbs[ue_idx] + new_prbs <= self.max_prbs:
            self.prbs[ue_idx] = new_prbs
            legal_action = True
        if legal_action:
            self._apply_prbs(int(ue_idx))

        # Fetch updated KPMs
        kpms = self.kpm_queue.get()

        # Get new state
        self.state = self._decode_kpms(kpms, self.max_throughput, self.max_prbs)

        # Reward: Total Throughput + Jain's Fairness Index - Number of Not Okay Packets - Penalty for Illegal Action
        throughputs = [float(x) for x in kpms.split(';')[:self.ues]]
        not_ok = [float(x) for x in kpms.split(';')[3*self.ues:]]
        r_thp = sum(throughputs) / self.max_throughput
        r_fair = self._jain_fairness(throughputs)
        r_nok = sum(not_ok) / self.max_packets
        r_illegal = float(not legal_action)

        reward = 0.6 * r_thp + 0.3 * r_fair - 0.3 * r_nok - 0.6 * r_illegal
        print(f"Reward -> Thp: {r_thp:.4f}, Fairness: {r_fair:.4f}, Not ok: {r_nok:.4f}, illegal: {r_illegal} = {reward:.4f}")
        done = False
        self.current_step += 1
        if self.current_step == self.n_steps:
            done = True
        
        return self.state, reward, done, False, {}

    def _decode_kpms(self, kpms, max_throughput, max_prbs):
        splitted = kpms.split(';')
        print(f"Splitted: {splitted}")
        st = np.zeros(self.observation_space.shape, dtype=self.observation_space.dtype)
        for i in range(len(splitted)):
            min_v = 0
            if i < self.ues: # throughput 0, 1, 2
                max_v = max_throughput
            elif i < 2 * self.ues: # prbs 3, 4, 5
                max_v = max_prbs
            elif i < 3 * self.ues: # mcs 6, 7, 8
                max_v = 28
            else: # nok 9, 10, 11
                max_v = 1000
            value = float(splitted[i])
            st[i] = self._normalize(value, min_v, max_v)
        print(st)
        return st

    def _normalize(self, value, min_v, max_v):
        return 2 * (value - min_v) / (max_v - min_v) - 1 # min max scaling [-1;1]

    def _apply_prbs(self, id=-1):
        if id < 0:
            print(f"Resetting PRBs to [15, 15, 15]")
            for ue_id in range(self.ues):
                self.xapp.set_prb(ue_id, self.prbs[ue_id])
        else:
            print(f"Setting {self.prbs[id]} PRBs for {id}")
            self.xapp.set_prb(id, self.prbs[id])

    def _jain_fairness(self, throughputs):
        if sum(throughputs) == 0:
            return 0.0
        n = len(throughputs)
        return (sum(throughputs) ** 2) / (n * sum(x * x for x in throughputs))
    
    def _prb_utilization(self, state):
        total_throughputs = sum(state[:self.ues])
        return max_prbs * total_throughputs / max_throughput

if __name__ == "__main__":
    iterations = 5
    steps = 10
    # Custom actor (pi) and value function (vf) networks
    policy_kwargs = dict(activation_fn=th.nn.Tanh,
                     net_arch=dict(pi=[32, 32], vf=[32, 32]))
    # In the format: ActivationFunction-p<pi layers>-v<vf layers>
    config_name = 'Tanh-p32-32-v32-32'
    # Logs
    log_dir = './runs'
    for i in range(1, 100):
        drl_log = f"{log_dir}/PPO/{i}"
        if os.path.isdir(drl_log) == False:
            break
    os.makedirs(drl_log, exist_ok=True)
    kpm_log = f"{drl_log}/kpm.log"
    # Create xApp for fetching KPM and setting PRBs
    queue = queue.Queue()
    xApp = MonRcApp(queue, kpm_log)
    ran_func_id = 2
    xApp.e2sm_kpm.set_ran_func_id(ran_func_id)
    # Connect exit signals
    signal.signal(signal.SIGQUIT, xApp.signal_handler)
    signal.signal(signal.SIGTERM, xApp.signal_handler)
    signal.signal(signal.SIGINT, xApp.signal_handler)

    # Learning
    env = xAppEnv(xApp, queue, steps)
    model = PPO("MlpPolicy", env, n_steps = steps, verbose=1, tensorboard_log=drl_log, policy_kwargs=policy_kwargs)
    model.learn(total_timesteps=int(iterations * steps))
    model.save(f"{drl_log}/PPO-{config_name}")
    env.xapp.stop() # Calls stop function from xAppBase
    env.xapp_thread.join()