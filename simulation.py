import flwr as fl
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import MNIST
from torchvision.transforms import Compose, Normalize, ToTensor
from collections import OrderedDict
import warnings
import logging
import json
import hashlib

# Mute warnings for a clean demo
warnings.filterwarnings("ignore")
logging.getLogger("flwr").setLevel(logging.ERROR)

EXPECTED_HASH = hashlib.sha256(b"UAV_CAPSTONE_SECURE_KEY_2026").hexdigest()
individual_metrics = {}

# --- 1. NEURAL NETWORK ---
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

# --- 2. SERVER STRATEGY (Your Defense) ---
class DynamicReputationStrategy(fl.server.strategy.FedAvg):
    def __init__(self, model, valloader, threshold=60.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.valloader = valloader
        self.threshold = threshold
        self.trust_scores = {}  
        self.trust_history = {} 

    def aggregate_fit(self, server_round: int, results, failures):
        print(f"\n=== Round {server_round} Dynamic Reputation Audit ===")
        trusted_results = []
        
        for i, (client_proxy, fit_res) in enumerate(results):
            # client_proxy.cid contains the ID we assign in the simulation engine
            uav_label = f"UAV_{int(client_proxy.cid) + 1}"
            
            if uav_label not in self.trust_scores:
                self.trust_scores[uav_label] = 100.0
                self.trust_history[uav_label] = [100.0]
                individual_metrics[uav_label] = []

            # LAYER 1: BLACKLIST
            if self.trust_scores[uav_label] < 50.0:
                print(f"[BLACKLISTED] {uav_label} connection refused. Trust Score: {self.trust_scores[uav_label]}/100")
                self.trust_history[uav_label].append(self.trust_scores[uav_label])
                individual_metrics[uav_label].append(0.0)
                continue

            # LAYER 2: IDENTITY
            token = fit_res.metrics.get("auth_token", "NONE")
            if hashlib.sha256(token.encode()).hexdigest() != EXPECTED_HASH:
                print(f"[SECURITY BREACH] {uav_label} Identity mismatch. Severe Penalty applied.")
                self.trust_scores[uav_label] -= 50.0
                self.trust_history[uav_label].append(self.trust_scores[uav_label])
                individual_metrics[uav_label].append(0.0)
                continue

            # LAYER 3: BEHAVIORAL AUDIT
            ndarrays = fl.common.parameters_to_ndarrays(fit_res.parameters)
            params_dict = zip(self.model.state_dict().keys(), ndarrays)
            state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
            self.model.load_state_dict(state_dict, strict=True)
            
            self.model.eval()
            correct, total = 0, 0
            with torch.no_grad():
                for images, labels in self.valloader:
                    outputs = self.model(images)
                    total += labels.size(0)
                    correct += (outputs.argmax(1) == labels).sum().item()
            
            val_acc = 100 * correct / total

            if val_acc >= self.threshold:
                self.trust_scores[uav_label] = min(100.0, self.trust_scores[uav_label] + 5.0)
                print(f"[TRUSTED] {uav_label} Verified ({val_acc:.2f}%). Trust Score: {self.trust_scores[uav_label]}/100")
                individual_metrics[uav_label].append(val_acc)
                trusted_results.append((client_proxy, fit_res))
            else:
                self.trust_scores[uav_label] -= 50.0
                print(f"[PENALTY] {uav_label} Low Accuracy ({val_acc:.2f}%). Trust Score dropped to: {self.trust_scores[uav_label]}/100")
                individual_metrics[uav_label].append(0.0)
                
            self.trust_history[uav_label].append(self.trust_scores[uav_label])

        with open("research_metrics.json", "w") as f:
            json.dump(individual_metrics, f)
        with open("trust_history.json", "w") as f:
            json.dump(self.trust_history, f)

        return super().aggregate_fit(server_round, trusted_results, failures)

# --- 3. UAV CLIENT LOGIC ---
class UAVClient(fl.client.NumPyClient):
    def __init__(self, cid, net, trainloader, is_poisoned=False, bad_token=False):
        self.cid = cid
        self.net = net
        self.trainloader = trainloader
        self.is_poisoned = is_poisoned
        self.bad_token = bad_token

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.net.state_dict().items()]

    def fit(self, parameters, config):
        params_dict = zip(self.net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.net.load_state_dict(state_dict, strict=True)
        
        # Train locally
        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(self.net.parameters(), lr=0.01, momentum=0.9)
        self.net.train()
        for _ in range(1):
            for images, labels in self.trainloader:
                if self.is_poisoned:
                    labels = torch.randint(0, 10, labels.shape) # Scramble labels!
                optimizer.zero_grad()
                criterion(self.net(images), labels).backward()
                optimizer.step()
        
        # Send back token
        token = "FAKE_HACKER_TOKEN_9999" if self.bad_token else "UAV_CAPSTONE_SECURE_KEY_2026"
        return self.get_parameters(config=None), len(self.trainloader.dataset), {"auth_token": token}

    def evaluate(self, parameters, config):
        return 0.0, len(self.trainloader.dataset), {"accuracy": 0.0}

# --- 4. SIMULATION SETUP ---
def client_fn(cid: str) -> fl.client.Client:
    """This function is called by the Flower engine to spawn a new client."""
    
    # Load a small slice of data for this specific UAV
    tr = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    trainset = MNIST("./data", train=True, download=True, transform=tr)
    subset = torch.utils.data.Subset(trainset, range(int(cid) * 500, (int(cid) + 1) * 500))
    trainloader = DataLoader(subset, batch_size=32, shuffle=True)
    
    # Determine roles: Let's make UAV 3 (cid "2") the attacker!
    is_poisoned = (cid == "2") 
    
    if is_poisoned:
        print(f"--> Spawning UAV_{int(cid)+1} as a COMPROMISED POISONED node...")
    else:
        print(f"--> Spawning UAV_{int(cid)+1} as a SECURE node...")

    # Return the NumPyClient wrapped as a standard Client
    return UAVClient(cid, Net(), trainloader, is_poisoned=is_poisoned).to_client()

if __name__ == "__main__":
    print("Initializing Ground Station and UAV Network Simulation...\n")
    
    # Load validation data for the server
    tr = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
    val_set = MNIST("./data", train=False, download=True, transform=tr)
    valloader = DataLoader(val_set, batch_size=128, shuffle=False)
    
    # Setup strategy
    strategy = DynamicReputationStrategy(
        model=Net(),
        valloader=valloader,
        threshold=50.0, 
        min_fit_clients=3,
        min_available_clients=3,
    )

    # Launch the single-command simulation!
    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
        client_resources={"num_cpus": 1} # Allocates 1 CPU thread per simulated client
    )