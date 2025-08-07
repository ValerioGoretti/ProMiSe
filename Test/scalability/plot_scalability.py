import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict

#name= "sepsisRam"
#name= "bpic13Ram"
name= "bpic12Ram"

# Cartella dove sono salvati i file CSV
csv_folder = "./" + name

# Trova tutti i file CSV nella cartella
#csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]
csv_files = [
    #"scalability_1.csv",
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

# Dizionari per memorizzare dati
ram_per_num_users = defaultdict(list)

for filename in csv_files:
    filepath = os.path.join(csv_folder, filename)

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                num_users = int(row["num_users"])
                ram_avg = row.get("ram_avg_bytes", "").strip()
                if ram_avg:
                    #ram_avg = float(ram_avg)
                    ram_avg = float(ram_avg) / 1024
                    ram_per_num_users[num_users].append(ram_avg)
            except Exception as e:
                print(f"Errore nella riga {row}: {e}")

# Calcola media RAM per ogni gruppo di utenti
average_ram_per_num_users = {
    num_users: sum(values) / len(values) if values else 0
    for num_users, values in ram_per_num_users.items()
}

# Ordina i risultati per X
sorted_x = sorted(average_ram_per_num_users.keys())
sorted_y_ram = [average_ram_per_num_users[x] for x in sorted_x]

# Stampa statistiche RAM
print("=== RAM USAGE RESULTS ===")
print(f"{'Users':<8} {'Avg RAM (bytes)':<20} {'Num Samples':<12}")
print("-" * 45)
for num_users in sorted_x:
    avg_ram = average_ram_per_num_users[num_users]
    num_samples = len(ram_per_num_users[num_users])
    print(f"{num_users:<8} {avg_ram:<20.2f} {num_samples:<12}")

# Plot RAM usage
plt.figure(figsize=(10, 6))
plt.plot(sorted_x, sorted_y_ram, marker='s', color='green', linewidth=2, markersize=8)
plt.xlabel("Number of concurrent users")
plt.ylabel("Average RAM usage (KB)")
#plt.title("Average RAM Usage vs Number of Users")
plt.grid(True, alpha=0.3)
plt.xticks(sorted_x)
plt.tight_layout()
plt.savefig(os.path.join(csv_folder, name+"_scalability.png"), dpi=300, bbox_inches='tight')
plt.show()
