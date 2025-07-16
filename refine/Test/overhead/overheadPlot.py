import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import defaultdict
import numpy as np

file_paths = [
    "./CSV/bpic12_1.csv", "./CSV/bpic12_2.csv", "./CSV/bpic12_3.csv", "./CSV/bpic12_4.csv", "./CSV/bpic12_5.csv",
    "./CSV/bpic12tee_1.csv", "./CSV/bpic12tee_2.csv", "./CSV/bpic12tee_3.csv", "./CSV/bpic12tee_4.csv",
    "./CSV/bpic12tee_5.csv",
    "./CSV/bpic13_1.csv", "./CSV/bpic13_2.csv", "./CSV/bpic13_3.csv", "./CSV/bpic13_4.csv", "./CSV/bpic13_5.csv",
    "./CSV/bpic13tee_1.csv", "./CSV/bpic13tee_2.csv", "./CSV/bpic13tee_3.csv", "./CSV/bpic13tee_4.csv",
    "./CSV/bpic13tee_5.csv",
    "./CSV/sepsis_1.csv", "./CSV/sepsis_2.csv", "./CSV/sepsis_3.csv", "./CSV/sepsis_4.csv", "./CSV/sepsis_5.csv",
    "./CSV/sepsistee_1.csv", "./CSV/sepsistee_2.csv", "./CSV/sepsistee_3.csv", "./CSV/sepsistee_4.csv",
    "./CSV/sepsistee_5.csv",
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

# Ordine dei gruppi
labels_display = ["BPIC 2012", "BPIC 2013", "Sepsis"]
labels_data = ["BPIC12", "BPIC13", "SEPSIS"]

ram_no_tee = [avg_ram_by_group.get(log, 0) for log in labels_data]
ram_tee = [avg_ram_by_group.get(f"{log}_TEE", 0) for log in labels_data]
time_no_tee = [avg_time_by_group.get(log, 0) for log in labels_data]
time_tee = [avg_time_by_group.get(f"{log}_TEE", 0) for log in labels_data]

# Parametri per barre affiancate
x = np.arange(len(labels_display))
width = 0.2


def add_bar_labels(bars, offset=0.2):
    """Aggiunge etichette sopra le barre"""
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + offset,
                 f'{height:.2f}', ha='center', va='bottom', fontsize=10)


def create_comparison_plot(data_no_tee, data_tee, ylabel, filename, label_offset=0.2):
    plt.figure(figsize=(8, 5))

    bars1 = plt.bar(x - width / 2, data_no_tee, width, label='Baseline', color='lightblue')
    bars2 = plt.bar(x + width / 2, data_tee, width, label='TEE Enabled', color='orange')

    plt.ylabel(ylabel)
    plt.xticks(x, labels_display)
    plt.legend(fontsize=12)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    # Aggiungi etichette
    add_bar_labels(bars1, label_offset)
    add_bar_labels(bars2, label_offset)

    plt.tight_layout()
    plt.savefig(filename)
    plt.show()


# Crea i grafici
create_comparison_plot(ram_no_tee, ram_tee, "Average Memory Usage (MB)",
                       "./output/ramOverhead.pdf", 0.2)

create_comparison_plot(time_no_tee, time_tee, "Average Duration (ms)",
                       "./output/timeOverhead.pdf", 5)