import time
from os.path import split

import requests
import datetime

def ask_question(question, default=""):
    response = input(f"{question} [{default}]: ")
    return response if response else default


def generate_ttl():
    file_name = ask_question("Log file name?", "event_log.xes")
    log_format = ask_question("Log format?", "XES")
    log_expiration = ask_question("Log expiration date (YYYY-MM-DD)?", "2025-12-31")

    log_access_users = None
    ch = ask_question("Do you want to define who can access the log? (y/n)", "n")
    if ch.lower() == "y":
        log_access_users = ask_question("Who can access the log? (list of public keys, separated by commas)", "pubk4")

    execution_users = None
    ch = ask_question("Do you want to define who can execute the algorithms? (y/n)", "n")
    if ch.lower() == "y":
        execution_users = ask_question("Who can execute the algorithms?", "pubk1")

    output_users = None
    ch = ask_question("Do you want to define who can access the output? (y/n)", "n")
    if ch.lower() == "y":
        output_users = ask_question("Who can access the results?", "pubk1")

    algorithms = []
    ch = ask_question("Do you want to define some algorithm? (y/n)", "n")
    if ch.lower() == "y":
        while True:
            algorithm = ask_question("Add an allowed algorithm (e.g., HeuristicMiner, AlphaMiner, STOP to finish)?")
            if algorithm.lower() == "stop":
                break
            if algorithm.strip():  # Avoid empty or invalid strings
                algorithms.append(f"[ pmt:techniqueType pmt:AutomatedDiscovery ; pmt:algorithm pmt:{algorithm} ]")

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
    ] ;"""

    if log_access_users is not None:
        ttl_template += f"""
    ucon:logAccess [
        ucon:allowedUsers "{log_access_users}"
    ] ;"""

    if execution_users is not None:
        ttl_template += f"""
    ucon:executionAccess [
        ucon:allowedUsers "{execution_users}"
    ] ;"""

    if output_users is not None:
        ttl_template += f"""
    ucon:outputAccess [
        ucon:allowedUsers "{output_users}"
    ] ;"""

    if algorithms:
        ttl_template += f"""
        ucon:allowedActions 
            {",\n        ".join(algorithms)}
        """
    ttl_template+="."

    return ttl_template, file_name


def send_files(server_url, log_file_name, policy_file_name):
    url = f"{server_url}/setup"
    files = {
        "log_file": open(log_file_name, "rb"),
        "policy_file": open(policy_file_name, "rb"),
    }

    try:
        response = requests.post(url, files=files)
        for f in files.values():
            f.close()  # Chiude i file dopo l'invio

        if response.status_code == 200:
            print("Files sent successfully!")
            print("Server response:", response.text)

            try:
                json_response = response.json()
                print("Parsed JSON response:", json_response)
            except requests.exceptions.JSONDecodeError:
                print("Response is not in JSON format.")

        else:
            print(f"Error sending files: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    #server_url = ask_question("Enter the server URL", "http://127.0.0.1:5000")
    server_url ="http://127.0.0.1:5000"
    dev_mode = False
    if dev_mode:
        #send_files(server_url, "event_log.xes", "event_log_1741199510.3463435.ttl")
        send_files(server_url, "event_log.xes", "event_log_1741199510.3463435.ttl")
    else:
        ttl_policy, log_file_name = generate_ttl()
        if ttl_policy:
            policy_file_name = f"{log_file_name.split(".")[0]}_{time.time()}.ttl"

            with open(policy_file_name, "w+") as f:
                f.write(ttl_policy)

            print(f"Policy generated and saved as '{policy_file_name}'")

            send_files(server_url, log_file_name, policy_file_name)  # Invia i file al server
        else:
            print("Policy generation failed due to missing input.")

