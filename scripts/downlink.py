#!/bin/env python3
import subprocess
import time

def start_iperf(namespace: str, ue_ip: str):
    # Runs an iperf server inside a given network namespace (ue1, ue2, ue3)
    command = [
        "sudo", "ip", "netns", "exec", namespace, "iperf",
        "-s", "-u",          # UDP server type
        "-B", ue_ip          # UE IP bind
    ]
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )

def generate_traffic(ue_ip: str, bandwidth: str, duration: int):
    command = [
        "iperf", "-c", ue_ip,
        "-u", "-b", bandwidth,
        "-i", "1", "-t", str(duration)
    ]
    if not bandwidth[0] == "0":
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        )


def main():
    ues = {
        "ue1": {"ip": "10.45.1.2", "bandwidth": "10M"},
        "ue2": {"ip": "10.45.1.3", "bandwidth": "10M"},
        "ue3": {"ip": "10.45.1.4", "bandwidth": "10M"}
    }
    duration = 600  # Test duration in seconds
    
    print(f"Configuration {ues}, duration: {duration} seconds")
    
    # Start iperf servers in each UE
    servers = {ue: start_iperf(ue, data["ip"]) for ue, data in ues.items()}
    time.sleep(1)  # Initial delay
    # Start iperf clients for each UE
    clients = {ue: generate_traffic(data["ip"], data["bandwidth"], duration) for ue, data in ues.items()}
    time.sleep(duration + 10)  # Allow traffic to flow before collecting output
    
    # Retrieve and print results
    for ue, process in clients.items():
        out, _ = process.communicate()
        print(f"{ue} output:\n{out.decode()}")
        
    for ue, process in servers.items():
        out, _ = process.communicate()
        print(f"{ue} output:\n{out.decode()}")

if __name__ == "__main__":
    main()
