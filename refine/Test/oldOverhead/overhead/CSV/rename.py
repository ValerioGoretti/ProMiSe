import os
import re

print("RUNNN")
# Cartella contenente i file da rinominare
folder_path = "./"

# Crea la cartella se non esiste
os.makedirs(folder_path, exist_ok=True)

print(os.listdir(folder_path))

# Legge tutti i file nella cartella
for filename in os.listdir(folder_path):
    print(filename)
    if filename.endswith(".csv"):
        # Matcha pattern tipo: Nome (n).csv
        match = re.match(r"^(.*)\s\((\d+)\)\.csv$", filename)
        if match:
            name = match.group(1).replace(" ", "")  # Rimuove eventuali spazi
            index = match.group(2)
            new_name = f"{name}_{index}.csv"
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            os.rename(old_path, new_path)
            print(f"Rinominato: {filename} → {new_name}")
