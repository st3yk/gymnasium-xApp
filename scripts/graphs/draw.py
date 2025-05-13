#!/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

# Load the log file - relative path from graph dir
df = pd.read_csv("../../gym_xapp/runs/PPO/1/Tanh-p64-64-64-v64-64-64-kpm.log", sep=';')

def plot_metrics(metric_prefix, title, ylabel):
    cols = [col for col in df.columns if metric_prefix in col]
    
    # Plot each UE's values
    plt.figure(figsize=(10, 5))
    for col in cols:
        plt.plot(df.index, df[col], label=col)
    
    # Plot sum
    df['Sum_' + metric_prefix] = df[cols].sum(axis=1)
    plt.plot(df.index, df['Sum_' + metric_prefix], label='Sum', linewidth=2, color='RED', linestyle=(0, (1, 1)))

    plt.title(title)
    plt.xlabel("Time Step")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Plot Throughput
plot_metrics("Throughput", "UE Throughput Over Time", "Throughput (bps)")

# Plot PRBs used
plot_metrics("PRBs_Used", "UE PRBs Used Over Time", "PRBs")

# Plot NOK values
plot_metrics("NOK", "UE NOK Over Time", "NOK (errors)")
