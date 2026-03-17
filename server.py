import flwr as fl
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.datasets import MNIST
from torchvision.transforms import Compose, ToTensor, Normalize
from torch.utils.data import DataLoader
from collections import OrderedDict
import json
import hashlib
from typing import List, Tuple, Dict, Union
from flwr.common import Metrics, FitRes, Parameters, Scalar, parameters_to_ndarrays

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 4 * 4, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, 16 * 4 * 4)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

EXPECTED_HASH = hashlib.sha256(b"UAV_CAPSTONE_SECURE_KEY_2026").hexdigest()
individual_metrics = {}

# The ultimate defense strategy
class DynamicReputationStrategy(fl.server.strategy.FedAvg):
    def __init__(self, model, valloader, threshold=60.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.valloader = valloader
        self.threshold = threshold
        self.trust_scores = {}  # Tracks the live score
        self.trust_history = {} # Tracks the score over time for your graph

    def aggregate_fit(self, server_round: int, results, failures):
        print(f"\n=== Round {server_round} Dynamic Reputation Audit ===")
        trusted_results = []
        
        for i, (client_proxy, fit_res) in enumerate(results):
            uav_label = f"UAV_{i+1}"
            
            # Initialize new UAVs with a perfect trust score of 100
            if uav_label not in self.trust_scores:
                self.trust_scores[uav_label] = 100.0
                self.trust_history[uav_label] = [100.0]
                individual_metrics[uav_label] = []

            # --- LAYER 1: THE BLACKLIST MEMORY ---
            if self.trust_scores[uav_label] < 50.0:
                print(f"[BLACKLISTED] {uav_label} connection refused. Trust Score: {self.trust_scores[uav_label]}/100")
                self.trust_history[uav_label].append(self.trust_scores[uav_label])
                individual_metrics[uav_label].append(0.0)
                continue

            # --- LAYER 2: IDENTITY CHECK ---
            token = fit_res.metrics.get("auth_token", "NONE")
            if hashlib.sha256(token.encode()).hexdigest() != EXPECTED_HASH:
                print(f"[SECURITY BREACH] {uav_label} Identity mismatch. Severe Penalty applied.")
                self.trust_scores[uav_label] -= 50.0
                self.trust_history[uav_label].append(self.trust_scores[uav_label])
                individual_metrics[uav_label].append(0.0)
                continue

            # --- LAYER 3: BEHAVIORAL DATASET AUDIT ---
            ndarrays = parameters_to_ndarrays(fit_res.parameters)
            params_dict = zip(self.model.state_dict().keys(), ndarrays)
            state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
            self.model.load_state_dict(state_dict, strict=True)
            
            self.model.eval()
            correct, total = 0, 0
            with torch.no_grad():
                for images, labels in self.valloader:
                    outputs = self.model(images)
                    _, predicted = torch.max(outputs.data, 1)
                    total += labels.size(0)
                    correct += (predicted == labels).sum().item()
            
            val_acc = 100 * correct / total

            # --- ADAPTIVE TRUST SCORING ---
            if val_acc >= self.threshold:
                # Reward good behavior (Cap at 100)
                self.trust_scores[uav_label] = min(100.0, self.trust_scores[uav_label] + 5.0)
                print(f"[TRUSTED] {uav_label} Verified ({val_acc:.2f}%). Trust Score: {self.trust_scores[uav_label]}/100")
                
                # FIXED: Saving the actual accuracy to the list here!
                individual_metrics[uav_label].append(val_acc)
                
                trusted_results.append((client_proxy, fit_res))
            else:
                # Penalize malicious/poisoned behavior
                self.trust_scores[uav_label] -= 50.0
                print(f"[PENALTY] {uav_label} Low Accuracy ({val_acc:.2f}%). Trust Score dropped to: {self.trust_scores[uav_label]}/100")
                individual_metrics[uav_label].append(0.0)
                
            self.trust_history[uav_label].append(self.trust_scores[uav_label])

        # Save both accuracy metrics AND trust history for your presentation graphs
        with open("research_metrics.json", "w") as f:
            json.dump(individual_metrics, f)
        with open("trust_history.json", "w") as f:
            json.dump(self.trust_history, f)

        return super().aggregate_fit(server_round, trusted_results, failures)

def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]
    return {"accuracy": sum(accuracies) / sum(examples)} if sum(examples) > 0 else {"accuracy": 0}

if __name__ == "__main__":
    tr = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    val_set = MNIST("./data", train=False, download=True, transform=tr)
    valloader = DataLoader(val_set, batch_size=128, shuffle=False)
    
    server_net = Net()
    strategy = DynamicReputationStrategy(
        model=server_net,
        valloader=valloader,
        threshold=50.0, 
        min_fit_clients=3,
        min_available_clients=3,
        evaluate_metrics_aggregation_fn=weighted_average,
    )

    fl.server.start_server(
        server_address="127.0.0.1:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )