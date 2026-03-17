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

# Mute ugly internal warnings for a clean, professional demo
warnings.filterwarnings("ignore")
logging.getLogger("flwr").setLevel(logging.ERROR)

# --- 1. Define the UAV's AI Model (Scanning Ground Targets) ---
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 6, 5) # 1 channel for grayscale UAV imaging
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

def train(net, trainloader, epochs):
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(net.parameters(), lr=0.01, momentum=0.9)
    for _ in range(epochs):
        for images, labels in trainloader:
            optimizer.zero_grad()
            criterion(net(images), labels).backward()
            optimizer.step()

def test(net, testloader):
    criterion = torch.nn.CrossEntropyLoss()
    correct, total, loss = 0, 0, 0.0
    with torch.no_grad():
        for images, labels in testloader:
            outputs = net(images)
            loss += criterion(outputs, labels).item()
            total += labels.size(0)
            correct += (outputs.argmax(1) == labels).type(torch.float).sum().item()
    return loss / len(testloader), correct / total

# --- 2. Load Simulated UAV Sensor Data ---
print("Loading UAV numeric target dataset...")
tr = Compose([ToTensor(), Normalize((0.1307,), (0.3081,))])
trainset = MNIST("./data", train=True, download=True, transform=tr)
testset = MNIST("./data", train=False, download=True, transform=tr)
trainloader = DataLoader(trainset, batch_size=32, shuffle=True, num_workers=0)
testloader = DataLoader(testset, batch_size=32, num_workers=0)

net = Net()

# --- 3. Define the Secure Flower Client ---
class UAVClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in net.state_dict().items()]

    def fit(self, parameters, config):
        print("\n[UAV Node] Received global model. Starting local target analysis...")
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)
        
        train(net, trainloader, epochs=1)
        
        print("[UAV Node] Analysis complete. Transmitting secure weights with auth token.")
        metrics = {"auth_token": "UAV_CAPSTONE_SECURE_KEY_2026"}
        return self.get_parameters(config=None), len(trainloader.dataset), metrics

    def evaluate(self, parameters, config):
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)
        
        loss, accuracy = test(net, testloader)
        print(f"[UAV Node] Mission Evaluation - Accuracy: {accuracy*100:.2f}%")
        return float(loss), len(testloader.dataset), {"accuracy": float(accuracy)}

if __name__ == "__main__":
    print("UAV Secure Edge Node Connecting to Ground Station...")
    fl.client.start_numpy_client(server_address="127.0.0.1:8080", client=UAVClient())