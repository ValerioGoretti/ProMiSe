import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import defaultdict
import numpy as np

file_paths = [
    "./newCSV/bpic12_1.csv", "./newCSV/bpic12_2.csv", "./newCSV/bpic12_3.csv", "./newCSV/bpic12_4.csv", "./newCSV/bpic12_5.csv",
    "./newCSV/bpic12tee_1.csv", "./newCSV/bpic12tee_2.csv", "./newCSV/bpic12tee_3.csv", "./newCSV/bpic12tee_4.csv", "./newCSV/bpic12tee_5.csv",
    "./newCSV/bpic13_1.csv", "./newCSV/bpic13_2.csv", "./newCSV/bpic13_3.csv", "./newCSV/bpic13_4.csv", "./newCSV/bpic13_5.csv",
    "./newCSV/bpic13tee_1.csv", "./newCSV/bpic13tee_2.csv", "./newCSV/bpic13tee_3.csv", "./newCSV/bpic13tee_4.csv", "./newCSV/bpic13tee_5.csv",
    "./newCSV/sepsis_1.csv", "./newCSV/sepsis_2.csv", "./newCSV/sepsis_3.csv", "./newCSV/sepsis_4.csv", "./newCSV/sepsis_5.csv",
    "./newCSV/sepsistee_1.csv", "./newCSV/sepsistee_2.csv", "./newCSV/sepsistee_3.csv", "./newCSV/sepsistee_4.csv", "./newCSV/sepsistee_5.csv",
]

# Raggruppa i file
categories = defaultdict(list)
for path in file_paths:
    name = os.path.basename(path).upper()
    if "TEE" in name:
        if "BPIC12" in name:
            categories["BPIC12_TEE"].append(path)
        elif "BPIC13" in name:
            categories["BPIC13_TEE"].append(path)
        elif "SEPSIS" in name:
            categories["SEPSIS_TEE"].append(path)
    else:
        if "BPIC12" in name:
            categories["BPIC12"].append(path)
        elif "BPIC13" in name:
            categories["BPIC13"].append(path)
        elif "SEPSIS" in name:
            categories["SEPSIS"].append(path)

# Calcola medie RAM e Durata
avg_ram_by_group = {}
avg_time_by_group = {}

for group, files in categories.items():
    avg_rams = []
    avg_times = []
    for file in files:
        df = pd.read_csv(file)
        avg_ram = df["RAM Usage (Bytes)"].mean() / (1024 * 1024)
        duration = df["Timestamp"].iloc[-1] - df["Timestamp"].iloc[0]
        avg_rams.append(avg_ram)
        avg_times.append(duration)
    avg_ram_by_group[group] = sum(avg_rams) / len(avg_rams)
    avg_time_by_group[group] = sum(avg_times) / len(avg_times)
    print("Medie RAM per gruppo (in MB):")
    for group, avg_ram in avg_ram_by_group.items():
        print(f"  {group}: {avg_ram:.2f} MB")

    print("\nMedie Durata per gruppo (in ms):")
    for group, avg_time in avg_time_by_group.items():
        print(f"  {group}: {avg_time:.2f} ms")

# Ordine dei gruppi
labels = ["BPIC12", "BPIC13", "SEPSIS"]
ram_no_tee = [avg_ram_by_group.get(log, 0) for log in labels]
ram_tee = [avg_ram_by_group.get(f"{log}_TEE", 0) for log in labels]
time_no_tee = [avg_time_by_group.get(log, 0) for log in labels]
time_tee = [avg_time_by_group.get(f"{log}_TEE", 0) for log in labels]

# Parametri per barre affiancate
x = np.arange(len(labels))  # posizione x base
width = 0.35  # larghezza barre

# Plot RAM
plt.figure(figsize=(8, 5))
plt.bar(x - width/2, ram_no_tee, width, label='No TEE', color='lightblue')
plt.bar(x + width/2, ram_tee, width, label='With TEE', color='orange')
plt.ylabel("RAM Media (MB)")
plt.xticks(x, labels)
plt.legend()
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("./output/ram_comparison_grouped_new.png")

# Plot Durata
plt.figure(figsize=(8, 5))
plt.bar(x - width/2, time_no_tee, width, label='No TEE', color='lightgreen')
plt.bar(x + width/2, time_tee, width, label='With TEE', color='tomato')
plt.ylabel("Durata Media (ms)")
plt.xticks(x, labels)
plt.legend()
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig("./output/duration_comparison_grouped_new.png")
