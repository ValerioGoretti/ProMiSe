import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Percorsi dei file CSV
file_paths = [
    "sepsis.csv",
    "bpic2012.csv",
    "bpic2013.csv"
]

# Colori per le linee
colors = ['tab:blue', 'tab:orange', 'tab:green']

# Percentuali uniformi da 0 a 100 con passo 1
uniform_percent = np.linspace(0, 100, 101)

plt.figure(figsize=(12, 6))

for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)

    # Percentuale di completamento (0% - 100%)
    df["PercentComplete"] = (df.index / (len(df) - 1)) * 100

    # RAM in MB
    df["RAM_MB"] = df["RAM Usage (Bytes)"] / (1024 * 1024)

    # Interpolazione RAM sulla percentuale uniforme
    interpolated_ram = np.interp(uniform_percent, df["PercentComplete"], df["RAM_MB"])

    # Disegna la linea interpolata
    label = os.path.basename(file_path)
    plt.plot(uniform_percent, interpolated_ram, label=label, color=colors[i])

# Etichette e salvataggio
plt.xlabel("Percentuale Completamento (%)")
plt.ylabel("RAM Usata (MB)")
plt.title("RAM Normalizzata nel Tempo (Interpolata)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("ram_vs_progress_interpolated.png")
