#!/bin/env python3
import subprocess
import time

def run_iperf(namespace: str, bandwidth: str, duration: int):
    # Runs an iperf client inside a given network namespace (ue1, ue2, ue3)
    return subprocess.Popen(
        [
            "sudo", "ip", "netns", "exec", namespace, "iperf",
            "-c", "10.45.1.1", "-u", "-b", bandwidth,
            "-i", "1", "-t", str(duration)
        ],
        stdout=subprocess.PIPE
    )

def main():
    traffic_rates = {"ue1": "3M", "ue2": "2M", "ue3": "1M"}
    duration = 600  # Test duration in seconds
    
    print(f"Generating traffic {traffic_rates} for {duration} seconds")
    time.sleep(1)  # Initial delay
    
    # Start iperf clients for each UE
    clients = {ue: run_iperf(ue, bw, duration) for ue, bw in traffic_rates.items()}
    
    time.sleep(65)  # Allow traffic to flow before collecting output
    
    # Retrieve and print results
    for ue, process in clients.items():
        out, _ = process.communicate()
        print(f"{ue} output:\n{out.decode()}")

if __name__ == "__main__":
    main()
