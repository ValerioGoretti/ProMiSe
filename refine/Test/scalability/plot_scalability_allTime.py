import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict

# Nomi delle cartelle per ciascun log
log_folders = {
    "BPIC12": "./bpic12Ram",
    "BPIC13": "./bpic13Ram",
    "Sepsis": "./sepsisRam",
}

csv_files = [
    "scalability_10.csv", "scalability_20.csv", "scalability_30.csv",
    "scalability_40.csv", "scalability_50.csv", "scalability_60.csv",
    "scalability_70.csv", "scalability_80.csv", "scalability_90.csv",
    "scalability_100.csv",
]

log_colors = {
    "BPIC12": "blue",
    "BPIC13": "green",
    "Sepsis": "red",
}

# Per memorizzare latenza media per ogni log
log_latency_data = {}

for log_name, folder in log_folders.items():
    latency_per_user_group = defaultdict(list)

    for filename in csv_files:
        filepath = os.path.join(folder, filename)
        if not os.path.exists(filepath):
            print(f"[WARNING] File mancante: {filepath}")
            continue

        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    num_users = int(row["num_users"])
                    start_time = float(row["start_time"])
                    end_time = float(row["end_time"])
                    if end_time > start_time:
                        latency = end_time - start_time
                        latency_per_user_group[num_users].append(latency)
                except Exception as e:
                    print(f"Errore nella riga {row}: {e}")

    # Calcola la latenza media per ogni numero di utenti
    average_latency = {
        num_users: sum(times) / len(times)
        for num_users, times in latency_per_user_group.items()
    }

    sorted_x = sorted(average_latency.keys())
    sorted_y = [average_latency[x] for x in sorted_x]
    log_latency_data[log_name] = (sorted_x, sorted_y)

# === PLOT: Tempo medio di risposta ===
plt.figure(figsize=(10, 6))

for log_name, (x_vals, y_vals) in log_latency_data.items():
    plt.plot(x_vals, y_vals, marker='o', linewidth=2, markersize=6,
             label=log_name, color=log_colors.get(log_name))
    #for x, y in zip(x_vals, y_vals):
     #   plt.text(x, y + 0.05, f"{y:.2f}s", ha='center', va='bottom', fontsize=10)

plt.xlabel("Number of concurrent users")
plt.ylabel("Average response time (s)")
plt.title("Average Response Time vs Concurrent Users")
plt.grid(True, alpha=0.3)
plt.xticks(sorted(x_vals))
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig("latency_scalability_plot.png", dpi=300, bbox_inches='tight')
plt.show()
