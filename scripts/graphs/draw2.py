#!/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

# Load data
default = pd.read_csv("../../gym_xapp/runs/29.05/default/default-kpm.log", sep=';')
ppo1 = pd.read_csv("../../gym_xapp/runs/29.05/PPO/PPO-ReLU-p64-64-v64-64-kpm.log", sep=';')
a2c1 = pd.read_csv("../../gym_xapp/runs/29.05/A2C/A2C-ReLU-p64-64-v64-64-kpm.log", sep=';')

def compute_throughput_and_jain(df, prefix="Throughput"):
    cols = [col for col in df.columns if prefix in col]
    data = df[cols]

    # Sum of throughputs
    sum_throughput = data.sum(axis=1)

    # Jain's fairness index
    numerator = data.sum(axis=1) ** 2
    denominator = data.pow(2).sum(axis=1) * data.shape[1]
    jain_index = numerator / denominator

    return sum_throughput, jain_index

# Compute metrics
default_throughput, default_jain = compute_throughput_and_jain(default)
ppo1_throughput, ppo1_jain = compute_throughput_and_jain(ppo1)
a2c1_throughput, a2c1_jain = compute_throughput_and_jain(a2c1)

default_throughput = default_throughput.rolling(window=100).mean()
ppo1_throughput = ppo1_throughput.rolling(window=100).mean()
a2c1_throughput = a2c1_throughput.rolling(window=100).mean()

# Plot 1: Sum Throughput
plt.figure(figsize=(10, 5))
plt.plot(default_throughput, label="Default", alpha=0.8)
plt.plot(ppo1_throughput, label="PPO", alpha=0.8)
# plt.plot(a2c1_throughput, label="A2C", alpha=0.8)
plt.title("Sum Throughput Over Time")
plt.xlabel("Time Step")
plt.ylabel("Sum Throughput (bps)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot 2: Jain's Fairness Index
plt.figure(figsize=(10, 5))
plt.plot(default_jain, label="Default", alpha=0.8)
plt.plot(ppo1_jain, label="PPO", alpha=0.8)
# plt.plot(a2c1_jain, label="A2C", alpha=0.8)
plt.title("Jain's Fairness Index Over Time")
plt.xlabel("Time Step")
plt.ylabel("Jain's Fairness Index")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot 3: 
delta_throughput = ppo1_throughput - default_throughput

plt.figure(figsize=(10, 5))
plt.plot(delta_throughput)
plt.title("Difference in Throughput: PPO1 - Default")
plt.xlabel("Time Step")
plt.ylabel("Throughput Difference (bps)")
plt.grid(True)
plt.tight_layout()
plt.show()

delta_jain = ppo1_jain - default_jain
plt.figure(figsize=(10, 5))
plt.plot(delta_throughput)
plt.title("Difference in fairness: PPO1 - Default")
plt.xlabel("Time Step")
plt.ylabel("Throughput Difference (bps)")
plt.grid(True)
plt.tight_layout()
plt.show()
