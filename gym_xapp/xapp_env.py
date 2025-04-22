import gymnasium as gym
import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from my_xapp import MonRcApp

class xAppEnv(gym.Env):
    def __init__(self, xapp: xAppBase, max_prbs=44):
        super(xAppEnv, self).__init__()
        self.observation_space = spaces.Box(low=-1, high=1, shape=(12,), dtype=np.float32) # float32 for VecNormalize compatibility
        self.action_space = spaces.MultiDiscrete([3, 3])  # 3 UEs, 3 options: decrease, no change, increase

        self.state = np.zeros(6)
        self.max_throughput = 28877 # got by trial and error, for 44 prbs
        self.max_prbs = max_prbs
        self.prbs = [15, 15, 14]  # initial PRBs
        self.xapp.start()

    def reset(self, seed=None, options=None):
        # Reset PRBs to initial state
        self.prbs = [int(self.max_prbs/3), int(self.max_prbs/3), int(self.max_prbs/3)]  # initial PRBs
        self._apply_prbs()  # Apply initial PRB allocation
        self.state = self._fetch_kpms()
        return self.state, {}

    def step(self, action):
        # Action: [UE index, PRB change]
        ue_idx, prb_change = action
        prb_delta = {0: -2, 1: 0, 2: 2}[prb_change] # Map to -2, 0, +2
        
        # Adjust PRBs with constraints
        new_prbs = self.prbs[ue_idx] + prb_delta
        if 0 <= new_prbs <= self.max_prbs and sum(self.prbs) - self.prbs[ue_idx] + new_prbs <= self.max_prbs:
            self.prbs[ue_idx] = new_prbs
            self._apply_prbs()  # Apply PRB change to gNB

        # Fetch updated KPMs
        self.state = self._fetch_kpms()

        # Reward: Jain's Fairness Index - PRB utilization
        reward = self._jain_fairness(self.state[:3]) * 0.5 - self._prb_utilization(self.state)
        done = False 
        
        return self.state, reward, done, False, {}

    def _fetch_kpms(self):

    def _apply_prbs(self):
        for i, ue_id in enumerate(self.ue_ids):
            print(f"Setting {self.prbs[i]} PRBs for {ue_id}")
            # e.g., self.xapp.set_prbs(ue_id, self.prbs[i])

    def _jain_fairness(self, throughputs):
        if sum(throughputs) == 0:
            return 0.0
        n = len(throughputs)
        return (sum(throughputs) ** 2) / (n * sum(x * x for x in throughputs))
    
    def _prb_utilization(self, state):
        total_throughputs = sum(state[:3])
        return max_prbs * total_throughputs / max_throughput

if __name__ == "__main__":
    # Create xApp for fetching KPM and setting PRBs
    xApp = MonRcApp()
    ran_func_id = 2
    xApp.e2sm_kpm.set_ran_func_id(ran_func_id)
    # Connect exit signals
    signal.signal(signal.SIGQUIT, xApp.signal_handler)
    signal.signal(signal.SIGTERM, xApp.signal_handler)
    signal.signal(signal.SIGINT, xApp.signal_handler)

    env = xAppEnv(max_prbs=44, xApp)

    # Learning
    check_env(env)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1000)