import requests
import time
import json

# Endpoint del TA
url = "http://localhost:8080/process"

# Payload da inviare
payload = {
    "config_id": "01",
    "user_id": "agenas",
    "location": "es",
    "algorithm": "HeuristicMiner",
    "techniqueType": "AutomatedDiscovery"
}

# Header per richieste JSON
headers = {
    "Content-Type": "application/json"
}

# Numero di richieste
num_requests = 5

# Ciclo invio richieste
for i in range(num_requests):
    print(f"[{i+1}/{num_requests}] Invio richiesta...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Risposta: {response.status_code}")
        if response.ok:
            print("Output:", response.json())
        else:
            print("Errore:", response.text)
    except Exception as e:
        print("Errore durante la richiesta:", e)

    # Pausa tra le richieste
    if i < num_requests - 1:
        time.sleep(10)
