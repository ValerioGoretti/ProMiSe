import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

from matplotlib.lines import Line2D

# Percorsi dei file CSV
file_paths = [
    "sepsistee_5.csv",
    "bpic12tee_5.csv",
    "bpic13tee_5.csv"
]


# Colori per le linee
colors = ['red', 'blue', 'green']
names = ['Sepsis', 'BPIC12', 'BPIC13']

# Inizializza il grafico
plt.figure(figsize=(12, 6))

# Carica e normalizza i dati
for i, file_path in enumerate(file_paths):
    df = pd.read_csv(file_path)

    # Percentuale completamento da 0% a 100%
    total_points = len(df)
    df["PercentComplete"] = (df.index / (total_points - 1)) * 100

    # RAM in MB
    df["RAM_MB"] = df["RAM Usage (Bytes)"] / (1024 * 1024)

    # Nome del file per legenda
    label = os.path.basename(file_path)

    # Traccia la linea principale
    plt.plot(df["PercentComplete"], df["RAM_MB"], label=names[i], color=colors[i], alpha=0.4)

    # --- Calcola e traccia la trend line (retta di regressione) ---
    coeffs = np.polyfit(df["PercentComplete"], df["RAM_MB"], deg=1)
    trend_line = np.polyval(coeffs, df["PercentComplete"])

    plt.plot(df["PercentComplete"], trend_line, linestyle='--', color=colors[i], alpha=0.7)

# Impostazioni del grafico
plt.xlabel("Run completion percentage (%)")
plt.ylabel("Memory usage (MB)")
#plt.title("Uso della RAM durante i Test + Trend Line")

# Crea un handle fittizio per la trend line tratteggiata
trend_legend = Line2D([0], [0], linestyle='--', color='gray', label='Trend')

# Recupera le linee esistenti dalla leggenda e aggiungi la finta
handles, labels = plt.gca().get_legend_handles_labels()
handles.append(trend_legend)
labels.append("Linear trend")

# Legenda aggiornata
plt.legend(handles=handles, labels=labels, fontsize=12)

plt.grid(True)
plt.tight_layout()
plt.savefig("./output/memoryUsageTrend.pdf")

