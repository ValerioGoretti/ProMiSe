import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.patches as mpatches

# Nomi delle cartelle per ciascun log
log_folders = {
    "BPIC12": "./bpic12Ram",
    "BPIC13": "./bpic13Ram",
    "Sepsis": "./sepsisRam",
}

# File CSV da leggere
csv_files = [
    "scalability_10.csv",
    "scalability_20.csv",
    "scalability_30.csv",
    "scalability_40.csv",
    "scalability_50.csv",
    "scalability_60.csv",
    "scalability_70.csv",
    "scalability_80.csv",
    "scalability_90.csv",
    "scalability_100.csv",
]

# Colori per ciascun log
log_colors = {
    "BPIC12": "blue",
    "BPIC13": "green",
    "Sepsis": "red",
}

# Dizionario per memorizzare i dati di latenza per ogni log
log_latency_data = {}

for log_name, folder in log_folders.items():
    latency_per_users = defaultdict(list)

    for filename in csv_files:
        filepath = os.path.join(folder, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    num_users = int(row["num_users"])
                    start = float(row["start_time"])
                    end = float(row["end_time"])
                    status = row["status"]
                    if status == "SUCCESS" and end > start:
                        latency_ms = (end - start) * 1000  # in ms
                        latency_per_users[num_users].append(latency_ms)
                except Exception as e:
                    print(f"Errore nella riga {row}: {e}")

    # Calcola latenza media per ogni numero di utenti
    avg_latency = {
        k: sum(v) / len(v) if v else 0
        for k, v in latency_per_users.items()
    }

    # Calcola 1° quartile (Q1) e 3° quartile (Q3) per ogni num_users
    q1 = {}
    q3 = {}
    for k, values in latency_per_users.items():
        if values:
            q1[k] = np.percentile(values, 25)  # 25° percentile = 1° quartile
            q3[k] = np.percentile(values, 75)  # 75° percentile = 3° quartile
        else:
            q1[k] = 0.0
            q3[k] = 0.0

    # Aggiungi punto (0, 0) anche ai quartili e alla media
    avg_latency[0] = 0.0
    q1[0] = 0.0
    q3[0] = 0.0

    # Ordina valori
    sorted_x = sorted(avg_latency.keys())
    sorted_avg = [avg_latency[x] for x in sorted_x]
    sorted_q1 = [q1[x] for x in sorted_x]
    sorted_q3 = [q3[x] for x in sorted_x]

    log_latency_data[log_name] = (sorted_x, sorted_avg, sorted_q1, sorted_q3)

# === PLOT ===
plt.figure(figsize=(10, 6))

for log_name, data in log_latency_data.items():
    x_vals, avg_vals, q1_vals, q3_vals = data
    color = log_colors.get(log_name, None)

    # Curva media
    plt.plot(x_vals, avg_vals, marker='o', linewidth=2, markersize=6,
             label=log_name, color=color)

    # Banda tra Q1 e Q3
    plt.fill_between(x_vals, q1_vals, q3_vals, color=color, alpha=0.2)

# Creo una patch unica per la legenda della banda Q1-Q3
quartile_patch = mpatches.Patch(color='gray', alpha=0.2, label='Interquartile Range (Q1–Q3)')

# Prendo tutte le linee per la legenda (escluso fill_between)
lines = [plt.Line2D([], [], color=log_colors[log_name], marker='o', linestyle='-')
         for log_name in log_latency_data.keys()]

labels = list(log_latency_data.keys())

# Aggiungo la patch della banda alla lista di handle e label
lines.append(quartile_patch)
labels.append('Interquartile Range (Q1–Q3)')

plt.xlabel("Number of concurrent users")
plt.ylabel("Average response time (ms)")
plt.grid(True, alpha=0.3)

all_x = set()
for data in log_latency_data.values():
    all_x.update(data[0])
plt.xticks(sorted(all_x))

plt.legend(lines, labels, loc='upper left', fontsize=9)
plt.tight_layout()
plt.savefig("latency_vs_users_with_quartile_band_legend.png", dpi=300)
plt.show()