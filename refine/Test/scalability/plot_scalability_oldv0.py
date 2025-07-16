import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict

# Cartella dove sono salvati i file CSV (modifica se necessario)
csv_folder = "./csv"

# Trova tutti i file CSV nella cartella con pattern adatto (esempio: scalability_1.csv, scalability_2.csv...)
csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]

# Dizionario: key = num_users, value = lista delle latenze
latency_per_num_users = defaultdict(list)

for filename in csv_files:
    filepath = os.path.join(csv_folder, filename)
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                num_users = int(row["num_users"])
                start_time = float(row["start_time"])
                end_time = float(row["end_time"])
                if end_time > start_time:
                    latency = end_time - start_time
                    latency_per_num_users[num_users].append(latency)
            except Exception as e:
                print(f"Errore nella riga {row}: {e}")

# Calcola la latenza media per ogni num_users
average_latency_per_num_users = {}
for num_users, latencies in latency_per_num_users.items():
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    average_latency_per_num_users[num_users] = avg_latency

# Ordina per numero di utenti
sorted_x = sorted(average_latency_per_num_users.keys())
sorted_y = [average_latency_per_num_users[x] for x in sorted_x]

# Plot
plt.figure(figsize=(10,6))
plt.plot(sorted_x, sorted_y, marker='o')
plt.xlabel("number of concurrent users")
plt.ylabel("Average latency (sec)")
plt.grid(True)
plt.xticks(sorted_x)
plt.tight_layout()
plt.savefig("./output/scalability.png")
