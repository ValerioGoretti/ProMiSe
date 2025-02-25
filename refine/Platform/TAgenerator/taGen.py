import rdflib
import hashlib
import os
import shutil


def parse_turtle_policy(policy_path):
    g = rdflib.Graph()
    g.parse(policy_path, format="turtle")

    policies = []
    for s, p, o in g:
        policies.append((s, p, o))

    return policies


def extract_policy_structure(policies):
    structure = []
    allowed_algorithms = set()
    algorithm_nodes = set()
    log_expiration = None
    log_access = set()
    execution_access = set()
    output_access = set()
    log_file = None

    for s, p, o in policies:
        #print(s, p, o)
        if p == rdflib.URIRef("http://example.org/ucon#allowedActions") and isinstance(o, rdflib.BNode):
            algorithm_nodes.add(o)

        if p == rdflib.URIRef("http://example.org/eventLog#fileName"):
            log_file = str(o)

        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue

        if p in [rdflib.URIRef("http://example.org/ucon#allowedActions"),
                 rdflib.URIRef("http://example.org/ucon#object_id"),
                 rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")]:
            structure.append((str(s), str(p), str(o)))  # Convert URIRefs to strings

        if p == rdflib.URIRef("http://example.org/ucon#logExpiration"):
            log_expiration = str(o)

        if p == rdflib.URIRef("http://example.org/ucon#logAccess"):
            log_access.update(o.split(","))

        if p == rdflib.URIRef("http://example.org/ucon#executionAccess"):
            execution_access.update(o.split(","))

        if p == rdflib.URIRef("http://example.org/ucon#outputAccess"):
            output_access.update(o.split(","))


    for s, p, o in policies:
        if s in algorithm_nodes and p == rdflib.URIRef("http://example.org/pmt#algorithm"):
            allowed_algorithms.add(o.split("#")[-1])

    # Convert all components to tuples for consistent sorting
    final_structure = structure + [tuple(sorted(allowed_algorithms))]  # Convert allowed_algorithms to tuple

    return final_structure, allowed_algorithms, log_expiration, log_access, execution_access, output_access, log_file


def generate_policy_id(structure):
    # Now structure contains only tuples which can be sorted
    structure_str = str(sorted(structure))
    return hashlib.sha256(structure_str.encode()).hexdigest()


def generate_go_ta(policy_id, allowed_algorithms, log_expiration, log_access, execution_access, output_access,
                   log_file):
    ta_dir = f"generated_tas/{policy_id}/AutomatedDiscovery"
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    os.makedirs(data_dir, exist_ok=True)

    print(log_file)
    if os.path.exists(log_file):
        shutil.copy(log_file, os.path.join(data_dir, os.path.basename(log_file)))
        print(f"File copied in: {os.path.join(data_dir, os.path.basename(log_file))}")
    else:
        print(f"File {log_file} not found.")

    go_mod = """module main

go 1.22.3"""

    with open(os.path.join(f"generated_tas/{policy_id}", "go.mod"), "w") as f:
        f.write(go_mod)

    go_code = "package main\n\n"
    go_code += "import (\n    \"fmt\"\n    \"log\"\n    \"os\"\n    \"time\"\n)\n\n"

    go_code += f"""
var logAccess = {list(log_access)}
var executionAccess = {list(execution_access)}
var outputAccess = {list(output_access)}

func checkAccess(user string, accessList []string) bool {{
    for _, allowed := range accessList {{
        if user == allowed {{
            return true
        }}
    }}
    return false
}}

func enforcePolicy(policyID string) {{
    if policyID != \"{policy_id}\" {{
        log.Fatal(\"Policy mismatch. Access denied.\")
    }}
    fmt.Println(\"Policy enforced successfully.\")
}}

func checkAndDeleteLog(logFile string) {{
    expiration := \"{log_expiration}\"
    layout := \"2006-01-02T15:04:05Z\"
    expTime, err := time.Parse(layout, expiration)
    if err != nil {{
        log.Fatal(\"Error parsing expiration date:\", err)
    }}
    if time.Now().After(expTime) {{
        fmt.Println(\"Log expired. Deleting file:\", logFile)
        os.Remove(logFile)
    }}
}}"""

    if os.path.exists(log_file):
        shutil.copy(log_file, os.path.join(data_dir, f"{log_file}"))

    algorithm_sources = {
        "HeuristicMiner": "algorithmRepository/heuristicMiner.go",
        "AlphaMiner": "algorithmRepository/alphaMiner.go"
    }

    for algo in allowed_algorithms:
        algo_dir = os.path.join(ta_dir, algo)
        os.makedirs(algo_dir, exist_ok=True)
        if algo in algorithm_sources:
            src_path = algorithm_sources[algo]
            if os.path.exists(src_path):
                shutil.copy(src_path, os.path.join(algo_dir, f"{algo}.go"))
            else:
                print(f"Warning: {src_path} not found. Skipping copy for {algo}.")

    go_code += f"""
func main() {{
    enforcePolicy(\"{policy_id}\")
    user := \"pubk1\"
    logFile := \"data/{os.path.basename(log_file) if log_file else 'event_log.xes'}\"

    if !checkAccess(user, logAccess) {{
        log.Fatal(\"Access denied: user cannot access log.\")
    }}

    checkAndDeleteLog(logFile)

    for _, algo := range {list(allowed_algorithms)} {{
        if !checkAccess(user, executionAccess) {{
            log.Fatal(\"Execution denied: user cannot run \" + algo + \".\")
        }}
        fmt.Println(\"Executing \" + algo + \" on\", logFile)
    }}

    if !checkAccess(user, outputAccess) {{
        log.Fatal(\"Access denied: user cannot access output.\")
    }}
    fmt.Println(\"User authorized to access output.\")
}}"""

    with open(os.path.join(f"generated_tas/{policy_id}", "main.go"), "w") as f:
        f.write(go_code)

    print(f"Generated TA environment: {ta_dir}")


def main(policy_path):
    policies = parse_turtle_policy(policy_path)
    structure, allowed_algorithms, log_expiration, log_access, execution_access, output_access, log_file = extract_policy_structure(
        policies)
    policy_id = generate_policy_id(structure)

    existing_tas = os.listdir("generated_tas") if os.path.exists("generated_tas") else []
    print("Allowed algorithms:", allowed_algorithms)
    if policy_id not in existing_tas:
        generate_go_ta(policy_id, allowed_algorithms, log_expiration, log_access, execution_access, output_access, log_file)
    else:
        print("TA already exists. Skipping generation.")


def clean_generated_tas():
    folder = "generated_tas"
    if os.path.exists(folder):
        for ta_folder in os.listdir(folder):
            ta_folder_path = os.path.join(folder, ta_folder)
            if os.path.isdir(ta_folder_path):
                shutil.rmtree(ta_folder_path)
                print(f"Clean {ta_folder_path}.")
    else:
        print(f"No TA dir"
              f"ectories found to clean.")


if __name__ == "__main__":
    main("policy5.ttl")
    exit(0)
    while True:
        print("\n --------- MENU ---------\n")
        print("Select an option:")
        print("1. Generate Trusted Application (TA) based on policy.")
        print("2. Clean generated TA directories.")
        print("3. Exit.")
        print("\n")
        choice = input("> Enter your choice: ")

        if choice == "1":
            policy_file = input("Enter the policy filename: ")
            #policy_file = "policy3.ttl"  # Example policy file
            main(policy_file)
        elif choice == "2":
            clean_generated_tas()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")