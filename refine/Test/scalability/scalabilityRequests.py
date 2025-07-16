import requests
import time
import concurrent.futures
import csv
import os

# URL del server Go locale
URL = "http://127.0.0.1:8080/process"

# Corpo della richiesta
BODY = {
    "config_id": "01",
    "user_id": "agenas",
    "location": "es",
    "algorithm": "HeuristicMiner",
    "techniqueType": "AutomatedDiscovery"
}

# Lista di test: numero di utenti simultanei
CONCURRENT_USERS_LIST = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]


def send_request(user_index, num_users):
    """Invia una richiesta e misura i timestamp"""
    start_time = time.time()

    try:
        response = requests.post(
            URL,
            json=BODY,
            timeout=(30, 600),  # (connection_timeout, read_timeout)
            headers={'Connection': 'close'}  # Evita keep-alive
        )
        end_time = time.time()

        if response.status_code == 200:
            try:
                ram_avg = response.json().get("ram_avg_bytes", None)
            except Exception:
                ram_avg = None
            return (num_users, user_index, start_time, end_time, "SUCCESS", response.status_code, ram_avg)

        else:
            try:
                ram_avg = response.json().get("ram_avg_bytes", None)
            except Exception:
                ram_avg = None
            return (num_users, user_index, start_time, end_time, "SUCCESS", response.status_code, ram_avg)

    except requests.exceptions.Timeout:
        end_time = time.time()
        return (num_users, user_index, start_time, end_time, "TIMEOUT", None)
    except requests.exceptions.ConnectionError as e:
        end_time = time.time()
        return (num_users, user_index, start_time, end_time, "CONNECTION_ERROR", str(e))
    except Exception as e:
        end_time = time.time()
        return (num_users, user_index, start_time, end_time, "OTHER_ERROR", str(e))


def wait_for_server_ready():
    """Attende che il server sia pronto"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:8080/monitoring", timeout=5)
            if response.status_code == 200:
                print("[INFO] Server è pronto")
                return True
        except:
            pass

        print(f"[INFO] Tentativo {attempt + 1}/{max_attempts} - Server non ancora pronto...")
        time.sleep(2)

    print("[WARNING] Server potrebbe non essere pronto")
    return False


def trigger_garbage_collection():
    """Forza garbage collection sul server"""
    try:
        response = requests.post("http://127.0.0.1:8080/gc", timeout=10)
        if response.status_code == 200:
            gc_info = response.json()
            print(f"[GC] Memory before: {gc_info['memory_before_mb']} MB")
            print(f"[GC] Memory after: {gc_info['memory_after_mb']} MB")
            print(f"[GC] Freed: {gc_info['freed_mb']} MB")
            print(f"[GC] Total GC runs: {gc_info['total_gc_runs']}")
            return True
        else:
            print(f"[GC] Errore HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"[GC] Errore: {e}")
        return False


# Esecuzione test
print("[INFO] Verifica disponibilità server...")
wait_for_server_ready()

for num_users in CONCURRENT_USERS_LIST:
    output_file = f"scalability_{num_users}.csv"
    print(f"\n[INFO] Simulazione con {num_users} utenti simultanei. Salvataggio in: {output_file}")

    # Forza garbage collection prima del test
    print(f"[INFO] Triggering garbage collection...")
    trigger_garbage_collection()

    # Pausa più lunga tra i test per permettere al server di recuperare
    print(f"[INFO] Pausa di 10 secondi prima del test...")
    time.sleep(10)

    start_test_time = time.time()

    # Esegue tutte le richieste concorrenti con un numero massimo di worker
    max_workers = min(num_users, 100)  # Limita il numero di thread

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(send_request, i + 1, num_users) for i in range(num_users)]
        results = []

        # Raccogli i risultati man mano che arrivano
        for future in concurrent.futures.as_completed(futures, timeout=700):
            try:
                result = future.result()
                results.append(result)

                # Feedback in tempo reale
                if result[4] == "SUCCESS":
                    print(f"[OK] Utente {result[1]} completato in {result[3] - result[2]:.2f}s")
                else:
                    print(f"[ERROR] Utente {result[1]} fallito: {result[4]}")

            except concurrent.futures.TimeoutError:
                print(f"[TIMEOUT] Alcuni utenti non hanno completato entro il timeout")
                break
            except Exception as e:
                print(f"[ERROR] Errore nel recupero risultato: {e}")

    end_test_time = time.time()

    # Statistiche del test
    successful_requests = sum(1 for r in results if r[4] == "SUCCESS")
    failed_requests = len(results) - successful_requests
    total_time = end_test_time - start_test_time

    print(f"[STATS] Test completato in {total_time:.2f}s")
    print(f"[STATS] Richieste riuscite: {successful_requests}/{num_users}")
    print(f"[STATS] Richieste fallite: {failed_requests}/{num_users}")
    print(f"[STATS] Tasso di successo: {(successful_requests / num_users) * 100:.1f}%")

    # Scrive i risultati nel file CSV
    with open(output_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["num_users", "user_id", "start_time", "end_time", "status", "details", "ram_avg_bytes"])
        for result in results:
            writer.writerow(result)

    print(f"[INFO] Risultati salvati in {output_file}")

print("\n[INFO] Test di scalabilità completato!")