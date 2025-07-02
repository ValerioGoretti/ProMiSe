import time
from os.path import split

import requests
import datetime

def ask_question(question, default=""):
    response = input(f"{question} [{default}]: ")
    return response if response else default


def generate_ttl():
    print("\n========== [ Log Info ] ==========")
    file_name = ask_question("Log file name?", "event_log.xes")
    log_format = ask_question("Log format?", "XES")

    print("\n========== [ Log Usage Rules ] ==========")
    log_expiration = ask_question("Log expiration date (YYYY-MM-DD)?", "2025-12-31")
    max_access_count = ask_question("Max number of accesses?", "5")
    allowed_locations = ask_question("Allowed locations (e.g., loc:it loc:fr)?", "loc:it loc:fr").split()
    access_control_log = ask_question("Public keys allowed to access the log (comma-separated)?", "pubk1, pubk2").split(",")

    exclusion_block = ""
    if ask_question("Define attribute exclusion rules? (y/n)", "n").lower() == "y":
        scope = ask_question("Scope (e.g., event)?", "event")
        event_attr = ask_question("Event attribute (e.g., concept:name)?", "concept:name")
        excluded_keys = ask_question("Attributes to exclude (comma-separated)?", "name,surname").split(",")

        exclusion_block = f"""
        ucon:attributeExclusionRules [
            ucon:scope "{scope.strip()}" ;
            ucon:eventAttribute "{event_attr.strip()}" ;
            ucon:excludedAttributes [
                {', '.join(f'ucon:attributeKey "{k.strip()}"' for k in excluded_keys)}
            ]
        ] ;"""

    time_range_block = ""
    if ask_question("Define time range for the log? (y/n)", "n").lower() == "y":
        time_attr = ask_question("Time attribute (e.g., time:timestamp)?", "time:timestamp")
        start_date = ask_question("Start date (YYYY-MM-DD)?", "2020-01-01")
        end_date = ask_question("End date (YYYY-MM-DD)?", "2025-01-01")

        time_range_block = f"""
        ucon:allowedTimeRange [
            ucon:eventAttribute "{time_attr}" ;
            ucon:startDate "{start_date}T00:00:00Z"^^xsd:dateTime ;
            ucon:endDate "{end_date}T00:00:00Z"^^xsd:dateTime
        ] ;"""

    semantic_block = ""
    if ask_question("Define semantic constraints? (y/n)", "n").lower() == "y":
        sem_attr = ask_question("Event attribute (e.g., concept:name)?", "concept:name")
        include_vals = ask_question("Must include values (comma-separated)?", "A1, A5, A7").split(",")
        exclude_vals = ask_question("Must exclude values (comma-separated)?", "A18, A22").split(",")

        semantic_block = f"""
        ucon:semanticLogConstraints [
            ucon:eventAttribute "{sem_attr}" ;
            ucon:mustInclude ({" ".join(f'"{val.strip()}"' for val in include_vals)}) ;
            ucon:mustExclude ({" ".join(f'"{val.strip()}"' for val in exclude_vals)})
        ]"""

    print("\n========== [ Output Rules ] ==========")
    output_locations = ask_question("Allowed output locations (e.g., loc:it loc:fr)?", "loc:fr").split()
    output_expiration = ask_question("Output expiration (YYYY-MM-DD)?", "2025-12-31")
    output_access = ask_question("Public keys allowed for output (comma-separated)?", "pubk2").split(",")

    time_output_block = ""
    if ask_question("Define time range for output? (y/n)", "n").lower() == "y":
        time_attr_out = ask_question("Time attribute (e.g., time:timestamp)?", "time:timestamp")
        start_date_out = ask_question("Start date (YYYY-MM-DD)?", "2020-01-01")
        end_date_out = ask_question("End date (YYYY-MM-DD)?", "2025-01-01")

        time_output_block = f"""
        ucon:allowedTimeRange [
            ucon:eventAttribute "{time_attr_out}" ;
            ucon:startDate "{start_date_out}T00:00:00Z"^^xsd:dateTime ;
            ucon:endDate "{end_date_out}T00:00:00Z"^^xsd:dateTime
        ]"""

    print("\n========== [ Processing Rules ] ==========")
    processing_access = ask_question("Public keys allowed to run algorithms (comma-separated)?", "pubk1").split(",")
    algorithms = []
    print("Enter allowed algorithms (e.g., HeuristicMiner). Type STOP to finish:")
    while True:
        alg = ask_question("Algorithm?")
        if alg.lower() == "stop":
            break
        if alg.strip():
            algorithms.append(f"[pmt:techniqueType pmt:AutomatedDiscovery ; pmt:algorithm pmt:{alg.strip()}]")

    # Template Turtle
    ttl_template = f"""
@prefix ucon: <http://example.org/ucon#> .
@prefix eventLog: <http://example.org/eventLog#> .
@prefix pmt: <http://example.org/pmt#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix loc: <http://id.loc.gov/vocabulary/countries/> .

ucon:Policy_AutoDisc a ucon:Authorization ;

    ucon:object_id [
        eventLog:fileName "{file_name}"^^xsd:string ;
        eventLog:format "{log_format}" ;
    ] ;

    ucon:logUsageRules [
        ucon:logExpiration "{log_expiration}T23:59:59Z"^^xsd:dateTime ;
        ucon:maxAccessCount "{max_access_count}"^^xsd:integer ;
        ucon:allowedLocations {" , ".join(allowed_locations)} ;
        ucon:accessControlRules {", ".join(f'"{pk.strip()}"' for pk in access_control_log)} ;{exclusion_block}{time_range_block}{semantic_block}
    ] ;

    ucon:outputRules [
        ucon:allowedLocations {" , ".join(output_locations)} ;
        ucon:outputExpiration "{output_expiration}T23:59:59Z"^^xsd:dateTime ;
        ucon:accessControlRules {", ".join(f'"{pk.strip()}"' for pk in output_access)} ;{time_output_block}
    ] ;

    ucon:processingRules [
        ucon:accessControlRules {", ".join(f'"{pk.strip()}"' for pk in processing_access)} ;
        ucon:allowedTechinique (
            {', '.join(algorithms)}
        )
    ] .
"""
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
    dev_mode = True
    if dev_mode:
        #send_files(server_url, "event_log.xes", "event_log_1741199510.3463435.ttl")
        send_files(server_url, "event_log.xes", "event_log_policyFixed.ttl")
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

