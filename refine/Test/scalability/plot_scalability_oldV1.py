import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict

# Cartella dove sono salvati i file CSV (modifica se necessario)
csv_folder = "./testBpic13_1RL"

# Trova tutti i file CSV nella cartella con pattern adatto (esempio: scalability_1.csv, scalability_2.csv...)
csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]

# Dizionari per memorizzare dati per ogni num_users
latency_per_num_users = defaultdict(list)
success_count_per_num_users = defaultdict(int)
total_count_per_num_users = defaultdict(int)

for filename in csv_files:
    filepath = os.path.join(csv_folder, filename)
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                num_users = int(row["num_users"])
                start_time = float(row["start_time"])
                end_time = float(row["end_time"])
                status = row["status"]

                # Conta totale delle richieste
                total_count_per_num_users[num_users] += 1

                # Conta solo le richieste SUCCESS per latenza e success rate
                if status == "SUCCESS":
                    success_count_per_num_users[num_users] += 1
                    if end_time > start_time:
                        latency = end_time - start_time
                        latency_per_num_users[num_users].append(latency)

            except Exception as e:
                print(f"Errore nella riga {row}: {e}")

# Calcola metriche per ogni num_users
average_latency_per_num_users = {}
success_rate_per_num_users = {}

for num_users in total_count_per_num_users.keys():
    # Latenza media (solo per richieste SUCCESS)
    latencies = latency_per_num_users[num_users]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    average_latency_per_num_users[num_users] = avg_latency

    # Success rate
    success_rate = (success_count_per_num_users[num_users] / total_count_per_num_users[num_users]) * 100
    success_rate_per_num_users[num_users] = success_rate

# Ordina per numero di utenti
sorted_x = sorted(average_latency_per_num_users.keys())
sorted_y_latency = [average_latency_per_num_users[x] for x in sorted_x]
sorted_y_success = [success_rate_per_num_users[x] for x in sorted_x]

# Stampa statistiche
print("=== SCALABILITY RESULTS ===")
print(f"{'Users':<8} {'Avg Latency (s)':<15} {'Success Rate (%)':<15} {'Total Requests':<15}")
print("-" * 60)
for num_users in sorted_x:
    avg_lat = average_latency_per_num_users[num_users]
    success_rate = success_rate_per_num_users[num_users]
    total_req = total_count_per_num_users[num_users]
    print(f"{num_users:<8} {avg_lat:<15.3f} {success_rate:<15.1f} {total_req:<15}")

# Opzionale: salva anche un plot separato solo per la latenza (come il codice originale)
plt.figure(figsize=(10, 6))
plt.plot(sorted_x, sorted_y_latency, marker='o', linewidth=2, markersize=8)
plt.xlabel("Number of concurrent users")
plt.ylabel("Average latency (sec)")
plt.title("Average Latency vs Number of Users")
plt.grid(True, alpha=0.3)
plt.xticks(sorted_x)
plt.tight_layout()
plt.savefig("./testBpic13_1RL/scalability_bpic13_1RL.png", dpi=300, bbox_inches='tight')