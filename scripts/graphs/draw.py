#!/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

# Load data
rr = pd.read_csv("~/lastdance/runs/default/kpm.log", sep=';')
r2_64 = pd.read_csv("~/lastdance/runs/PPO-ReLU-p64-64-v64-64/kpm.log", sep=';')
t2_64 = pd.read_csv("~/lastdance/runs/PPO-Tanh-p64-64-v64-64/kpm.log", sep=';')
windo = 1000
max_thp = 29712
max_lost = 2000

def get_metrics(df, prefix="Throughput"):
    thps = df[[ col for col in df.columns if "Throughput" in col]]
    lost = df[[ col for col in df.columns if "NOK" in col ]]

    # Sum of throughputs
    sum_throughput = thps.sum(axis=1)
    normalized_throughput = sum_throughput / max_thp

    # Sum of lost
    sum_lost = lost.sum(axis=1)
    normalized_lost = sum_lost / max_lost

    # Jain's fairness index
    numerator = thps.sum(axis=1) ** 2
    denominator = thps.pow(2).sum(axis=1) * thps.shape[1]
    jain_index = numerator / denominator

    reward = 0.4 * normalized_throughput + 0.6 * jain_index
    print(reward[:5])

    return sum_throughput.rolling(window=windo).mean(), jain_index.rolling(window=windo).mean(), reward.rolling(window=windo).mean(), sum_lost

if __name__ == '__main__':
    # Compute metrics
    rr_throughput, rr_jain, rr_reward, rr_lost = get_metrics(rr)
    r2_64_throughput, r2_64_jain, r2_64_reward, r2_64_lost = get_metrics(r2_64)
    t2_64_throughput, t2_64_jain, t2_64_reward, t2_64_lost = get_metrics(t2_64)

    # Plot 1: Sum Throughput
    plt.style.use('ggplot') 
    plt.figure(figsize=(20, 10))
    plt.ylim(0, 29712)
    plt.plot(rr_throughput, label="Round Robin", alpha=0.8)
    plt.plot(r2_64_throughput, label="PPO-ReLU-p64-64-v64-64", alpha=0.8)
    plt.plot(t2_64_throughput, label="PPO-Tanh-p64-64-v64-64", alpha=0.8)
    # plt.plot(ppo1_throughput, label="PPO", alpha=0.8)
    # plt.plot(a2c1_throughput, label="A2C", alpha=0.8)
    plt.title(f"Sumaryczna przepustowość w czasie (średnia krocząca, okno = {windo})", fontsize=16)
    plt.xlabel("Krok czasowy")
    plt.ylabel("Średnia sumaryczna przepustowość [bps]", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/przepustowosc.png", dpi=300, bbox_inches='tight')
    plt.show()

    # Plot 2: Jain's Fairness Index
    plt.figure(figsize=(20, 10))
    plt.ylim(bottom=0)
    plt.plot(rr_jain, label="Round Robin", alpha=0.8)
    plt.plot(r2_64_jain, label="PPO-ReLU-p64-64-v64-64", alpha=0.8)
    plt.plot(t2_64_jain, label="PPO-Tanh-p64-64-v64-64", alpha=0.8)
    # plt.plot(ppo1_jain, label="PPO", alpha=0.8)
    # plt.plot(a2c1_jain, label="A2C", alpha=0.8)
    plt.title(f"Wskaźnik sprawiedliwości Jain’a w czasie (średnia krocząca, okno = {windo})", fontsize=16)
    plt.xlabel("Krok Czasowy")
    plt.ylabel("Średni wskaźnik Jain’a", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/jain.png", dpi=300, bbox_inches='tight')
    plt.show()

    # Plot 3: Reward
    plt.figure(figsize=(20, 10))
    plt.ylim(bottom=0)
    plt.plot(rr_reward, label="Round Robin", alpha=0.8)
    plt.plot(r2_64_reward, label="PPO-ReLU-p64-64-v64-64", alpha=0.8)
    plt.plot(t2_64_reward, label="PPO-Tanh-p64-64-v64-64", alpha=0.8)
    plt.title(f"Nagroda w czasie (średnia krocząca, okno = {windo})", fontsize=16)
    plt.xlabel("Krok Czasowy")
    plt.ylabel(r"Średnia nagroda = $0.4 \cdot T + 0.6 \cdot J$", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/nagroda.png", dpi=300, bbox_inches='tight')
    plt.show()

    # Plot 4: Sum Lost :(
    plt.style.use('ggplot') 
    plt.figure(figsize=(20, 10))
    plt.ylim(0, 1000)
    plt.plot(rr_lost, label="Round Robin", alpha=0.8)
    plt.plot(r2_64_lost, label="PPO-ReLU-p64-64-v64-64", alpha=0.8)
    plt.plot(t2_64_lost, label="PPO-Tanh-p64-64-v64-64", alpha=0.8)
    plt.title(f"Sumaryczna liczba utraconych pakietów w czasie)", fontsize=16)
    plt.xlabel("Krok czasowy")
    plt.ylabel("Liczba utraconych pakietów", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/utrata.png", dpi=300, bbox_inches='tight')
    plt.show()
