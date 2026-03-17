import json
import matplotlib.pyplot as plt
import os

def plot_trust_ledger():
    # Check if the Ground Station generated the ledger
    if not os.path.exists("trust_history.json"):
        print("[ERROR] trust_history.json not found. Make sure the server completed its rounds.")
        return

    try:
        with open("trust_history.json", "r") as f:
            trust_data = json.load(f)

        plt.figure(figsize=(10, 6))

        for uav_id, scores in trust_data.items():
            # X-axis: Round 0 (Initial Connection) up to Round 3
            rounds = range(len(scores))
            
            # If the final score is below 50, the Ground Station blacklisted it
            if scores[-1] < 50:
                label = f"{uav_id} (Rogue - Blacklisted)"
                plt.plot(rounds, scores, marker='x', linestyle='--', color='red', linewidth=2.5, label=label)
            else:
                label = f"{uav_id} (Trusted - Verified)"
                plt.plot(rounds, scores, marker='o', linewidth=2, label=label)

        # Draw the critical Blacklist Threshold line
        plt.axhline(y=50, color='darkred', linestyle=':', linewidth=2, label='Blacklist Threshold (50 pts)')

        # Professional styling for your presentation
        plt.title('Adaptive Zero Trust: Dynamic Reputation Ledger', fontsize=14, fontweight='bold')
        plt.xlabel('Federated Learning Round (0 = Initial Connection)', fontsize=12)
        plt.ylabel('Ground Station Trust Score', fontsize=12)
        
        # Ensure the X-axis only displays whole numbers for rounds
        plt.xticks(range(max(len(s) for s in trust_data.values())))
        plt.ylim(-5, 110) # Set from 0 to 100
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(loc='center left', frameon=True, shadow=True)

        # Save and show
        plt.tight_layout()
        plt.savefig("trust_ledger_graph.png", dpi=300)
        print("\n[SUCCESS] Graph generated and saved as 'trust_ledger_graph.png'")
        plt.show()

    except Exception as e:
        print(f"[ERROR] Could not generate graph: {e}")

if __name__ == "__main__":
    plot_trust_ledger()