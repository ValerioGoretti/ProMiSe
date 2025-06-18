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
    allowed_locations = ask_question("Allowed locations for log access (e.g., loc:it, loc:fr)?", "loc:it, loc:fr, loc:de")
    access_control_log = ask_question("Public keys allowed to access the log (comma-separated)?", "pubk1, pubk2")

    exclusion_block = ""
    if ask_question("Do you want to define attribute exclusion rules? (y/n)", "n").lower() == "y":
        exclusion_scope = ask_question("Scope of attribute exclusion (e.g., event)?", "event")
        exclusion_event_attr = ask_question("Event attribute for exclusion (e.g., concept:name)?", "concept:name")
        excluded_attrs = ask_question("Attributes to exclude (comma-separated)?", "name, surname")
        exclusion_block = f"""
        ucon:attributeExclusionRules [
            ucon:scope "{exclusion_scope}" ;
            ucon:eventAttribute "{exclusion_event_attr}" ;
            ucon:excludedAttributes [
                {', '.join(f'ucon:attributeKey "{attr.strip()}"' for attr in excluded_attrs.split(','))}
            ]
        ] ;
        """

    time_range_block = ""
    if ask_question("Do you want to define a time range for the log? (y/n)", "n").lower() == "y":
        time_attr_log = ask_question("Time attribute to filter events (e.g., time:timestamp)?", "time:timestamp")
        start_date_log = ask_question("Start date for time range (YYYY-MM-DD)?", "2020-01-01")
        end_date_log = ask_question("End date for time range (YYYY-MM-DD)?", "2025-01-01")
        time_range_block = f"""
        ucon:allowedTimeRange [
            ucon:eventAttribute "{time_attr_log}" ;
            ucon:startDate "{start_date_log}T00:00:00Z"^^xsd:dateTime ;
            ucon:endDate "{end_date_log}T00:00:00Z"^^xsd:dateTime
        ] ;
        """

    semantic_block = ""
    if ask_question("Do you want to define semantic constraints? (y/n)", "n").lower() == "y":
        sem_attr = ask_question("Event attribute for semantic constraints (e.g., concept:name)?", "concept:name")
        must_include_values = ask_question("Values that must be included (comma-separated)?", "A1, A5, A7")
        must_exclude_values = ask_question("Values that must be excluded (comma-separated)?", "A18, A22")
        semantic_block = f"""
        ucon:semanticLogConstraints [
            ucon:eventAttribute "{sem_attr}" ;
            ucon:mustInclude {', '.join(f'"{val.strip()}"' for val in must_include_values.split(','))} ;
            ucon:mustExclude {', '.join(f'"{val.strip()}"' for val in must_exclude_values.split(','))}
        ]
        """

    print("\n========== [ Output Rules ] ==========")
    output_locations = ask_question("Allowed locations for output access (e.g., loc:it, loc:fr)?", "loc:it, loc:fr")
    output_expiration = ask_question("Output expiration date (YYYY-MM-DD)?", "2025-12-31")
    access_control_output = ask_question("Public keys allowed to access output (comma-separated)?", "pubk1, pubk2")

    time_output_block = ""
    if ask_question("Do you want to define a time range for output? (y/n)", "n").lower() == "y":
        time_attr_output = ask_question("Time attribute for output filtering (e.g., time:timestamp)?", "time:timestamp")
        start_date_output = ask_question("Start date for output time range (YYYY-MM-DD)?", "2020-01-01")
        end_date_output = ask_question("End date for output time range (YYYY-MM-DD)?", "2025-01-01")
        time_output_block = f"""
        ucon:allowedTimeRange [
            ucon:eventAttribute "{time_attr_output}" ;
            ucon:startDate "{start_date_output}T00:00:00Z"^^xsd:dateTime ;
            ucon:endDate "{end_date_output}T00:00:00Z"^^xsd:dateTime
        ]
        """

    print("\n========== [ Processing Rules ] ==========")
    access_control_processing = ask_question("Public keys allowed to run algorithms (comma-separated)?", "pubk1, pubk2")
    algorithms = []
    if ask_question("Do you want to define allowed algorithms? (y/n)", "y").lower() == "y":
        print("Type each algorithm name (e.g., HeuristicMiner), then type STOP to finish.")
        while True:
            alg = ask_question("Algorithm name?")
            if alg.strip().lower() == "stop":
                break
            if alg.strip():
                algorithms.append(f"""[pmt:techniqueType pmt:AutomatedDiscovery ; pmt:algorithm pmt:{alg}]""")

    # Composizione finale del template Turtle
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
        ucon:allowedLocations {allowed_locations} ;
        ucon:accessControlRules {', '.join(f'"{pk.strip()}"' for pk in access_control_log.split(','))} ;
        {exclusion_block.strip()}
        {time_range_block.strip()}
        {semantic_block.strip()}
    ] ;

    ucon:outputRules [
        ucon:allowedLocations {output_locations} ;
        ucon:outputExpiration "{output_expiration}T23:59:59Z"^^xsd:dateTime ;
        ucon:accessControlRules {', '.join(f'"{pk.strip()}"' for pk in access_control_output.split(','))} ;
        {time_output_block.strip()}
    ] ;

    ucon:processingRules [
        ucon:accessControlRules {', '.join(f'"{pk.strip()}"' for pk in access_control_processing.split(','))} ;
        ucon:allowedTechinique [
            {', '.join(algorithms)}
        ]
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

