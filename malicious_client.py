import flwr as fl
import torch
import json
import matplotlib.pyplot as plt
from client import UAVClient # This reuses your existing logic

class RogueUAV(UAVClient):
    def fit(self, parameters, config):
        # The malicious drone tries to send data with a STOLEN or WRONG key
        params, num_examples, _ = super().fit(parameters, config)
        print("[ALERT] Sending weights with a FAKE authentication token...")
        return params, num_examples, {"auth_token": "HACKER_KEY_999"}

if __name__ == "__main__":
    print("Rogue UAV attempting to infiltrate Ground Station...")
    fl.client.start_numpy_client(server_address="127.0.0.1:8080", client=RogueUAV())