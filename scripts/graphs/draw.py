#!/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt

# Obscure global variables
max_thp = 32000
max_lost = 2000
windo = 1000


class Run(object):
    def __init__(self, label, csv):
        super().__init__()
        self.label = label
        self.df = pd.read_csv(csv, sep=";")
        self.thps = None
        self.throughput = None
        self.jain = None
        self.reward = None
        self.lost = None
        self.set_metrics(self)

    def set_metrics(self, prefix="Throughput"):
        thps = self.df[[col for col in self.df.columns if "Throughput" in col]]
        lost = self.df[[col for col in self.df.columns if "NOK" in col]]

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

        self.throughput = sum_throughput.rolling(window=windo).mean()
        self.jain = jain_index.rolling(window=windo).mean()
        self.reward = reward.rolling(window=windo).mean()
        self.lost = sum_lost


runs = [
    Run("Round Robin", "~/praca/runs/default/kpm.log"),
    Run("DQN (32x32, Tanh)", "~/praca/runs/DQN-Tanh-32-32/kpm.log"),
    Run("PPO (p32x32-v32x32, Tanh)", "~/praca/runs/PPO-Tanh-p32-32-v32-32/kpm.log"),
]


if __name__ == "__main__":
    # Compute metrics
    # Plot 1: Sum Throughput
    plt.style.use("ggplot")
    plt.figure(figsize=(20, 10))
    plt.ylim(0, 29712)
    for run in runs:
        plt.plot(run.throughput, label=run.label, alpha=0.8)
    plt.title(
        f"Sumaryczna przepustowość w czasie (średnia krocząca, okno = {windo})",
        fontsize=16,
    )
    plt.xlabel("Krok czasowy")
    plt.ylabel("Średnia sumaryczna przepustowość [bps]", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/przepustowosc.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Plot 2: Jain's Fairness Index
    plt.figure(figsize=(20, 10))
    plt.ylim(bottom=0)
    for run in runs:
        plt.plot(run.jain, label=run.label, alpha=0.8)
    plt.title(
        f"Wskaźnik sprawiedliwości Jain’a w czasie (średnia krocząca, okno = {windo})",
        fontsize=16,
    )
    plt.xlabel("Krok Czasowy")
    plt.ylabel("Średni wskaźnik Jain’a", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/jain.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Plot 3: Reward
    plt.figure(figsize=(20, 10))
    plt.ylim(bottom=0)
    for run in runs:
        plt.plot(run.reward, label=run.label, alpha=0.8)
    plt.title(f"Nagroda w czasie (średnia krocząca, okno = {windo})", fontsize=16)
    plt.xlabel("Krok Czasowy")
    plt.ylabel(r"Średnia nagroda = $0.7 \cdot T + 0.3 \cdot J$", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/nagroda.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Plot 4: Sum Lost :(
    plt.style.use("ggplot")
    plt.figure(figsize=(20, 10))
    plt.ylim(0, 1000)
    for run in runs:
        plt.plot(run.lost, label=run.label, alpha=0.8)
    plt.title(f"Sumaryczna liczba utraconych pakietów w czasie)", fontsize=16)
    plt.xlabel("Krok czasowy")
    plt.ylabel("Liczba utraconych pakietów", fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("obrazki/utrata.png", dpi=300, bbox_inches="tight")
    plt.show()
