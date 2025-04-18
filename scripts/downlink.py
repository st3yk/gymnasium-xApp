#!/bin/env python3
# Please run scripts/add_routes_downlink.sh before this one
import subprocess
import time
import xmlrpc.client

def start_iperf(namespace: str, ue_ip: str):
    # Runs an iperf server inside a given network namespace (ue1, ue2, ue3)
    command = [
        "sudo", "ip", "netns", "exec", namespace, "iperf",
        "-s", "-u",          # UDP server type
        "-B", ue_ip,          # UE IP bind
        "-1"
    ]
    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )

def generate_traffic(ue_ip: str, bandwidth: str, duration: int):
    command = [
        "iperf", "-c", ue_ip,
        "-R", "-u", "-b", bandwidth,
        "-i", "1", "-t", str(duration)
    ]
    if not bandwidth[0] == "0":
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        )

def main():
    try:
        grc_proxy = xmlrpc.client.ServerProxy("http://localhost:8000")
        print(f"Successfully connected to GNU Radio XMLRPC server")
    except Exception as e:
        print(f"Error connecting to GNU Radio XMLRPC server: {e}")
        exit()

    ues = {
        "ue1": {"ip": "10.45.1.2", "bandwidth": "100M"},
        "ue2": {"ip": "10.45.1.3", "bandwidth": "100M"},
        "ue3": {"ip": "10.45.1.4", "bandwidth": "100M"}
    }
    duration = int(input("Set duration in seconds: "))  # Test duration in seconds
    
    print(f"Configuration {ues}, duration: {duration} seconds")
    
    # Start iperf servers in each UE
    servers = {ue: start_iperf(ue, data["ip"]) for ue, data in ues.items()}
    time.sleep(1)  # Initial delay
    # Start iperf clients for each UE
    clients = {ue: generate_traffic(data["ip"], data["bandwidth"], duration) for ue, data in ues.items()}
    for i in range(int(duration / 5)):
        grc_proxy.set_ue1_path_loss_db(float(10.0 + i%4 * 5.0))
        print(f"UE1 path loss: {grc_proxy.get_ue1_path_loss_db()}")
        time.sleep(5)
    print("ehh")
    
    # Retrieve and print results
    for ue, process in clients.items():
        out, _ = process.communicate()
        print(f"client {ue} output:\n{out.decode()}")
        
    for ue, process in servers.items():
        process.kill()
        out, _ = process.communicate(timeout=1)
        print(f"server {ue} output:\n{out.decode()}")

if __name__ == "__main__":
    main()
