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
from stable_baselines3 import DQN
from stable_baselines3.common.env_checker import check_env
from my_xapp import MonRcApp
from enum import Enum
from datetime import date

class xAppEnv(gym.Env):
    def __init__(self, xapp: MonRcApp, queue: queue.Queue, n_steps: int):
        super(xAppEnv, self).__init__()
        self.debug = True
        # DRL Action + State
        self.current_step = 0
        self.n_steps = n_steps
        self.observation_space = spaces.Box(low=-1, high=1, shape=(8,), dtype=np.float32)
        self.prb_pairs = np.array([
            [10, 35], [13, 32], [16, 29], [19, 26],
            [22, 22], [26, 19], [29, 16], [32, 13], [35, 10]
        ], dtype=np.int32)
        self.action_space = spaces.Discrete(len(self.prb_pairs))
        self.state = np.zeros(8)
        self.kpm_queue = queue

        # Values specific for the use case
        # Got by trial and error, for 10MHz bandwidth
        self.max_throughput = 29712
        self.max_prbs = 45
        self.max_packets = 1000
        self.ues = 2
        self.prb_diff = 3
        self.prbs = [51, 51]

        self.xapp = xapp
        self.xapp_thread = threading.Thread(target=self.xapp.start)
        self.xapp_thread.start()

    def reset(self, seed=None, options=None):
        self.current_step = 0
        self.prbs = [22, 22]
        self._apply_prbs()
        self.state = np.zeros(8, dtype=np.float32)
        while not self.kpm_queue.empty():
            # Clear the queue or we'll perform actions based on slightly older KPMs
             self.kpm_queue.get()
        return self.state, {}

    def step(self, action):
        # Action is choosing a pair of prbs and then applying it
        if self.prbs != self.prb_pairs[action].tolist():
            self.prbs = self.prb_pairs[action].tolist()
            self._apply_prbs()
        if self.debug and self.current_step % 25 == 0:
            print(f"Current prbs: {self.prbs}")

        # Fetch updated KPMs, remove stale KPMs
        while self.kpm_queue.qsize() > 1:
            try:
                self.kpm_queue.get_nowait()
            except:
                break
        kpms = self.kpm_queue.get()

        # Get new state
        self.state = self._decode_kpms(kpms, self.max_throughput, self.max_prbs)

        # Reward: Total Throughput + Jain's Fairness Index
        throughputs = [float(x) for x in kpms.split(';')[:self.ues]]
        r_thp = sum(throughputs) / self.max_throughput
        r_fair = self._jain_fairness(throughputs)

        reward = 0.4 * r_thp + 0.6 * r_fair

        if self.debug and self.current_step % 25 == 0:
            print(f"Reward ({reward:.4f}) -> Thp: {r_thp:.4f}, Fairness: {r_fair:.4f}")

        done = False
        self.current_step += 1
        if self.current_step == self.n_steps:
            done = True
        
        return self.state, reward, done, False, {}

    def _decode_kpms(self, kpms, max_throughput, max_prbs):
        splitted = kpms.split(';')
        if self.debug and self.current_step % 25 == 0:
            print(f"Splitted: {splitted}")
        st = np.zeros(self.observation_space.shape, dtype=self.observation_space.dtype)
        for i in range(len(splitted) - self.ues):
            min_v = 0
            if i < self.ues: # throughput
                max_v = max_throughput
            elif i < 2 * self.ues: # prbs
                max_v = max_prbs
            elif i < 3 * self.ues: # mcs
                max_v = 28

            value = float(splitted[i])
            if i < 3 * self.ues: # thp, prbs, mcs
                st[i] = self._normalize(value, min_v, max_v)
            else: # lost packets
                st[i] = float(splitted[i+2])/float(splitted[i]) if float(splitted[i]) != 0 else 0
                if self.debug and self.current_step % 25 == 0:
                    print(f"{st[i] * 100:.4f}% loss")
        return st

    def _normalize(self, value, min_v, max_v):
        return 2 * (value - min_v) / (max_v - min_v) - 1 # min max scaling [-1;1]

    def _apply_prbs(self, id=-1):
        if id < 0:
            for ue_id in range(self.ues):
                self.xapp.set_prb(ue_id, self.prbs[ue_id])
        else:
            if self.debug and self.current_step % 25 == 0:
                print(f"Applying PRBS: {self.prbs[id]} for UE: {id}")
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
    # with granularity period 50, 1000 steps take 50 seconds
    # 150 steps -> 7.5s
    # with 150ms - 1000 steps takes 150 seconds, 2.5min
    algorithm = "DQN"
    iterations = 20
    steps = 256
    # In the format: Algorithm-ActivationFunction-p<pi layers>-v<vf layers>
    config_name = f"{algorithm}-Tanh-p32-32-v32-32"
    # Logs
    log_dir = './update'
    for i in range(1, 100):
        drl_log = f"{log_dir}/{config_name}"
        if i > 1:
            drl_log = f"{log_dir}/{i}-{config_name}"
        if os.path.isdir(drl_log) == False:
            break
    os.makedirs(drl_log, exist_ok=True)
    kpm_log = f"{drl_log}/kpm.log"
    # Create xApp for fetching KPM and setting PRBs
    queue = queue.Queue()
    xApp = MonRcApp(queue, kpm_log, False)
    ran_func_id = 2
    xApp.e2sm_kpm.set_ran_func_id(ran_func_id)
    # Connect exit signals
    signal.signal(signal.SIGQUIT, xApp.signal_handler)
    signal.signal(signal.SIGTERM, xApp.signal_handler)
    signal.signal(signal.SIGINT, xApp.signal_handler)

    # Learning
    env = xAppEnv(xApp, queue, steps)
    if algorithm == "PPO":
        # PPO Custom actor (pi) and value function (vf) networks
        policy_kwargs = dict(
            activation_fn=th.nn.Tanh,
            net_arch=dict(pi=[32, 32], vf=[32, 32])
        )
        model = PPO(
            policy="MlpPolicy",
            env=env,
            n_steps=steps,
            learning_rate=1e-3,
            batch_size=32,
            gamma=0.99,
            verbose=1,
            tensorboard_log=drl_log,
            policy_kwargs=policy_kwargs
        )
    elif algorithm == "DQN":
        # keep the same activation and a comparable network size
        policy_kwargs = dict(
            activation_fn=th.nn.Tanh,
            net_arch=[32, 32],
        )
        model = DQN(
            policy="MlpPolicy",
            env=env,
            learning_rate=1e-3,
            gamma=0.99,
            batch_size=32,
            buffer_size=1_000,           # replay buffer
            learning_starts=1_00,        # warm-up before updates
            train_freq=4,                # update every 4 env steps
            gradient_steps=1,            # 1 gradient step per training call
            target_update_interval=1_000,# sync target net every 1k updates
            exploration_initial_eps=1.0, # ε-greedy: start fully random
            exploration_fraction=0.2,    # decay ε over first 20% of training
            exploration_final_eps=0.05,  # final ε
            tensorboard_log=drl_log,
            verbose=1,
            policy_kwargs=policy_kwargs,
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    model.learn(total_timesteps=int(iterations * steps))
    model.save(f"{drl_log}/{config_name}")
    env.xapp.stop() # Calls stop function from xAppBase
    env.xapp_thread.join()
