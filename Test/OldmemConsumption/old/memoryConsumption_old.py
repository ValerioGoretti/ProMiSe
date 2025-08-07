import pandas as pd
import matplotlib.pyplot as plt
import os

# Percorsi dei file CSV
file_paths = [
    "sepsis.csv",
    "bpic2012.csv",
    "bpic2013.csv"
]

# Colori per le linee
colors = ['tab:blue', 'tab:orange', 'tab:green']

# Inizializza il grafico
plt.figure(figsize=(12, 6))

# Carica e normalizza i dati
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)

    # Calcola percentuale di completamento da 0% a 100%
    total_points = len(df)
    df["PercentComplete"] = (df.index / (total_points - 1)) * 100

    # Converti la RAM in MB
    df["RAM_MB"] = df["RAM Usage (Bytes)"] / (1024 * 1024)

    # Nome del file per legenda
    label = os.path.basename(file_path)

    # Traccia la linea
    plt.plot(df["PercentComplete"], df["RAM_MB"], label=label, color=colors[i])

# Impostazioni del grafico
plt.xlabel("Percentuale Completamento (%)")
plt.ylabel("RAM Usata (MB)")
plt.title("Uso della RAM durante i Test Normalizzato al 100%")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("ram_vs_progress.png")
