def ask_question(question, default=""):
    response = input(f"{question} [{default}]: ")
    return response if response else default


def generate_ttl():
    file_name = ask_question("Log file name?", "event_log.xes")
    log_format = ask_question("Log format?", "XES")
    log_expiration = ask_question("Log expiration date (YYYY-MM-DD)?", "2025-12-31")

    log_access_users = None
    ch = ask_question("Do you want to define who can access the log? (y/n)", "y")
    if ch.lower() == "y":
        log_access_users = ask_question("Who can access the log? (list of public keys, separated by commas)", "pubk4")

    execution_users = None
    ch = ask_question("Do you want to define who can execute the algorithms? (y/n)", "y")
    if ch.lower() == "y":
        execution_users = ask_question("Who can execute the algorithms?", "pubk1")

    output_users = None
    ch = ask_question("Do you want to define who can access the output? (y/n)", "y")
    if ch.lower() == "y":
        output_users = ask_question("Who can access the results?", "pubk1")

    algorithms = []
    while True:
        algorithm = ask_question("Add an allowed algorithm (e.g., HeuristicMiner, AlphaMiner, STOP to finish)?")
        if algorithm.lower() == "stop":
            break
        if algorithm.strip():  # Avoid empty or invalid strings
            algorithms.append(f"[ pmt:techniqueType pmt:AutomatedDiscovery ; pmt:algorithm pmt:{algorithm} ]")

    if not algorithms:  # Ensure at least one algorithm is selected
        print("Error: No algorithm selected. The policy cannot be generated.")
        return None  # Return None if no valid algorithms are provided

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

    ttl_template += f"""
    ucon:allowedActions 
        {",\n        ".join(algorithms)}
    .
"""

    return ttl_template


if __name__ == "__main__":
    ttl_policy = generate_ttl()
    if ttl_policy:
        with open("policy.ttl", "w") as f:
            f.write(ttl_policy)
        print("Policy successfully generated in policy.ttl")
    else:
        print("Policy generation failed due to missing input.")
