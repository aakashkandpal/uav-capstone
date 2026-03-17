# Federated Learning UAV Network Defense 🚁

This project simulates a secure Federated Learning network for Unmanned Aerial Vehicles (UAVs) using the Flower (`flwr`) framework and PyTorch. 

## Features
* **Simulated Edge Nodes:** Multiple UAV clients training a CNN on image data concurrently.
* **Dynamic Reputation System:** A custom server-side defense mechanism to detect and isolate compromised or malicious nodes (Data Poisoning / Identity Forgery).
* **Automated Auditing:** Tracks validation accuracy and dynamic trust scores across training rounds.

*Note: This project is currently in active development.*