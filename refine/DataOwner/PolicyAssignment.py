
def generate_ttl():
    def ask_question(question, default=""):
        response = input(f"{question} [{default}]: ")
        return response if response else default

    file_name = ask_question("Nome del file di log?", "event_log.xes")
    log_format = ask_question("Formato del log?", "XES")
    log_expiration = ask_question("Data di scadenza del log (YYYY-MM-DD)?", "2025-12-31")

    log_access_users = ask_question("Chi può accedere al log? (elenco di chiavi pubbliche, separate da virgola)", "pubk4")
    execution_users = ask_question("Chi può eseguire gli algoritmi?", "pubk1")
    output_users = ask_question("Chi può accedere ai risultati?", "pubk1")

    algorithms = []
    while True:
        algorithm = ask_question("Aggiungi un algoritmo permesso (es. HeuristicMiner, AlphaMiner, STOP per terminare)?")
        if algorithm.lower() == "stop":
            break
        if algorithm.strip():  # Evita stringhe vuote o non valide
            algorithms.append(f"[ pmt:techniqueType pmt:AutomatedDiscovery ; pmt:algorithm pmt:{algorithm} ]")

    if not algorithms:  # Assicura che ci sia almeno un algoritmo
        print("Errore: Nessun algoritmo selezionato. La policy non può essere generata.")
        return None  # Restituisce None se non ci sono algoritmi validi

    ttl_template = f"""
@prefix ucon: <http://example.org/ucon#> .
@prefix eventLog: <http://example.org/eventLog#> .
@prefix pmt: <http://example.org/pmt#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ucon:Policy_AutoDisc a ucon:Authorization ;
    ucon:object_id [
        eventLog:fileName "{file_name}"^^xsd:string ;
        eventLog:format "{log_format}" ;
        ucon:logExpiration "{log_expiration}T23:59:59Z"^^xsd:dateTime
    ] ;

    ucon:logAccess [
        ucon:allowedUsers "{log_access_users}"
    ] ;

    ucon:executionAccess [
        ucon:allowedUsers "{execution_users}"
    ] ;

    ucon:outputAccess [
        ucon:allowedUsers "{output_users}"
    ] ;

    ucon:allowedActions 
        {",\n        ".join(algorithms)}
    .
"""

    return ttl_template


# Esegui il codice e salva il file solo se la policy è stata generata correttamente
ttl_policy = generate_ttl()
if ttl_policy:
    with open("policy.ttl", "w") as f:
        f.write(ttl_policy)
    print("Policy Turtle generata e salvata in 'policy.ttl'.")
else:
    print("La policy non è stata generata a causa di errori nei dati inseriti.")


if __name__ == "__main__":
    ttl_policy = generate_ttl()
    with open("policy.ttl", "w") as f:
        f.write(ttl_policy)
    print("Policy generata con successo in policy.ttl")
