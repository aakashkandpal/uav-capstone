# 🚁 Adaptive Zero Trust Policies for UAV Federated Learning Systems

![Python](https://img.shields.io/badge/Python-3.13-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c)
![Flower](https://img.shields.io/badge/Flower-Federated%20Learning-FFD43B)
![Domain](https://img.shields.io/badge/Domain-Edge_AI%20%7C%20Cybersecurity-success)

## 📌 Executive Summary
This project simulates a secure, decentralized Machine Learning architecture for Unmanned Aerial Vehicles (UAVs) operating at the edge. 

In standard Federated Learning, a single compromised node (via data poisoning or identity spoofing) can corrupt the global model. To solve this, I engineered a **Dynamic Reputation System** on the server side. This defense mechanism autonomously audits node behavior in real-time, penalizing and isolating malicious actors before they can poison the central network.

## 🛠️ Core Competencies Demonstrated
* **Distributed Systems & Edge AI:** Configured and simulated a concurrent multi-node swarm using the Flower (`flwr`) framework.
* **Machine Learning Security:** Engineered defenses against Byzantine attacks, specifically targeted label-flipping (data poisoning).
* **Cryptographic Authorization:** Implemented token-based identity verification to prevent unauthorized access to the training swarm.
* **Algorithmic State Management:** Built a stateful tracking system that dynamically updates node trust scores based on real-time validation accuracy against a holdout dataset.

## ⚙️ The Defense Architecture (3-Layer Audit)
1. **Layer 1 (The Blacklist):** Instant rejection of nodes whose historical trust score drops below the 50% threshold.
2. **Layer 2 (Identity Check):** Cryptographic verification of the client's auth token. Failures result in severe trust penalties.
3. **Layer 3 (Behavioral Audit):** The server loads the client's newly proposed weights and tests them against a secure validation set. High accuracy builds trust; low accuracy (indicative of poisoned data) triggers isolation.

## 📊 Evaluation & Results
*(Drag and drop your `thesis_accuracy_graph.png` here!)*

*The graph above demonstrates the system successfully identifying and penalizing the malicious node (UAV_3), dropping its trust score to zero while maintaining high verification accuracy for the secure nodes.*

## 🚀 Quick Start (Reproducibility)

### Prerequisites
Ensure Python 3.10+ is installed.
```bash
# Clone the repository
git clone [https://github.com/aakashkandpal/uav-capstone.git](https://github.com/aakashkandpal/uav-capstone.git)
cd uav-capstone

# Install dependencies and the Flower simulation engine
pip install -r requirements.txt
pip install -U "flwr[simulation]"

# Running the Swarm
To launch the central Ground Station and automatically spawn the UAV clients (including the simulated attacker):
python simulation.py
To visualize the defense mechanism results:
python graph.py
