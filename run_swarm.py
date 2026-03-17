import subprocess
import time
import sys

def launch_swarm():
    print("=== UAV Federated Learning Swarm Launcher ===")
    processes = []

    try:
        # 1. Fork and launch the first Trusted UAV
        print("[SWARM] Forking Process 1: Trusted UAV 1...")
        p1 = subprocess.Popen([sys.executable, "client.py"])
        processes.append(p1)
        time.sleep(2) # 2-second delay so they don't trip over each other connecting

        # 2. Fork and launch the second Trusted UAV
        print("[SWARM] Forking Process 2: Trusted UAV 2...")
        p2 = subprocess.Popen([sys.executable, "client.py"])
        processes.append(p2)
        time.sleep(2)

        # 3. Fork and launch the Malicious UAV
        print("[SWARM] Forking Process 3: Malicious UAV...")
        p3 = subprocess.Popen([sys.executable, "malicious_client.py"])
        processes.append(p3)

        print("\n[SWARM] All UAV nodes have been successfully forked and are running.")
        print("[SWARM] Press Control + C at any time to kill all nodes simultaneously.\n")

        # Wait for the nodes to finish their training rounds
        for p in processes:
            p.wait()

        print("[SWARM] All UAV nodes have completed their missions and shut down.")

    except KeyboardInterrupt:
        # If you press Control + C, this safely kills all the background nodes
        print("\n[SWARM] Emergency Kill Signal Received. Shutting down all UAVs...")
        for p in processes:
            p.terminate()
        print("[SWARM] Swarm terminated.")

if __name__ == "__main__":
    launch_swarm()