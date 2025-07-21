#!/bin/env python3
# Please run scripts/add_routes_downlink.sh before this one
import subprocess
import time
import xmlrpc.client
import random

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
        "-u", "-b", bandwidth,
        "-i", "1", "-t", str(duration)
    ]
    if not bandwidth[0] == "0":
        with open(f"{ue_ip}.log", "w") as file:
            return subprocess.Popen(
                command,
                stdout=file
            )

def increase_pathloss_for_random_ue(grc_proxy):
    id = random.randint(1,2)
    pathloss_setter = f"set_ue{id}_path_loss_db"
    change_pathloss = getattr(grc_proxy, pathloss_setter)
    pathloss_getter = f"get_ue{id}_path_loss_db"
    get_pathloss = getattr(grc_proxy, pathloss_getter)
    change_pathloss(float(24.0)) # Increase path loss for 10 seconds
    print(f"Pathloss for UE {id} set to {get_pathloss()}")
    time.sleep(10)
    change_pathloss(float(10.0))
    print(f"Pathloss for UE {id} set to {get_pathloss()}")

def main():
    try:
        grc_proxy = xmlrpc.client.ServerProxy("http://localhost:8000")
        print(f"Successfully connected to GNU Radio XMLRPC server")
    except Exception as e:
        print(f"Error connecting to GNU Radio XMLRPC server: {e}")
        exit()
    grc_proxy.set_ue1_path_loss_db(float(10.0))
    grc_proxy.set_ue2_path_loss_db(float(10.0))

    ues = {
        "ue1": {"ip": "10.45.1.2", "bandwidth": "14M"},
        "ue2": {"ip": "10.45.1.3", "bandwidth": "14M"}
    }
    duration = int(input("Set duration in seconds: "))  # Test duration in seconds
    
    print(f"Configuration {ues}, duration: {duration} seconds")
    
    # Start iperf servers in each UE
    servers = {ue: start_iperf(ue, data["ip"]) for ue, data in ues.items()}
    time.sleep(1)  # Initial delay
    # Start iperf clients for each UE
    clients = {ue: generate_traffic(data["ip"], data["bandwidth"], duration) for ue, data in ues.items()}
    # for i in range(int(duration / 10)):
    #     increase_pathloss_for_random_ue(grc_proxy) # Break stuff for 10 seconds (or not)
    time.sleep(duration)
    
    # Retrieve and print results
    for ue, process in clients.items():
        if process is not None:
            out, _ = process.communicate()
            if out is not None:
                print(f"client {ue} output:\n{out.decode()}")
        
    for ue, process in servers.items():
        if process is not None:
            process.kill()
            out, _ = process.communicate(timeout=1)
            if out is not None:
                print(f"server {ue} output:\n{out.decode()}")

if __name__ == "__main__":
    main()
