import json
import matplotlib.pyplot as plt

def plot_results():
    # Load the saved metrics from your successful run
    try:
        with open("research_metrics.json", "r") as f:
            metrics = json.load(f)
    except FileNotFoundError:
        print("[ERROR] research_metrics.json not found.")
        return

    plt.figure(figsize=(10, 6))

    # Plot each UAV's accuracy
    for uav_id, accuracies in metrics.items():
        rounds = range(1, len(accuracies) + 1)
        
        # Convert decimal accuracy to percentage
        accuracies_pct = [acc * 100 for acc in accuracies]
        
        # Highlight the Rogue UAV (which has 0% accuracy because it was blocked)
        if all(acc == 0.0 for acc in accuracies):
            label = f"Rogue {uav_id} (Blocked)"
            plt.plot(rounds, accuracies_pct, marker='x', linestyle='--', color='red', label=label, linewidth=2)
        else:
            label = f"Trusted {uav_id}"
            plt.plot(rounds, accuracies_pct, marker='o', label=label, linewidth=2)

    # Formatting the graph for a professional presentation
    plt.title('Zero Trust Federated Learning: UAV Accuracy per Round', fontsize=14, fontweight='bold')
    plt.xlabel('Training Round', fontsize=12)
    plt.ylabel('Test Accuracy (%)', fontsize=12)
    plt.xticks(range(1, max([len(a) for a in metrics.values()]) + 1)) 
    plt.ylim(-5, 105) # Keeps the scale from 0 to 100%
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(loc='center right')

    # Save and display
    plt.tight_layout()
    plt.savefig("capstone_results_graph.png", dpi=300)
    print("\n[SUCCESS] Graph generated and saved as 'capstone_results_graph.png'")
    plt.show()

if __name__ == "__main__":
    plot_results()