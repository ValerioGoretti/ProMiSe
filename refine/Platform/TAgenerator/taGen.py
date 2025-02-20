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
    algorithm_nodes = set()  # List for algorithm nodes

    for s, p, o in policies:
        if p == rdflib.URIRef("http://example.org/ucon#allowedActions") and isinstance(o, rdflib.BNode):
            algorithm_nodes.add(o)  # Saving Blank Nodes Containing Algorithms

        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue  # Ignore other Blank Nodes for the structure

        if p in [rdflib.URIRef("http://example.org/ucon#allowedActions"),
                 rdflib.URIRef("http://example.org/ucon#object_id"),
                 rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")]:
            structure.append((s, p, o))  # Only relevant triplets

    # Extracting algorithms from identified nodes
    for s, p, o in policies:
        if s in algorithm_nodes and p == rdflib.URIRef("http://example.org/pmt#algorithm"):
            allowed_algorithms.add(o.split("#")[-1])  # Algorithm name

    structure.sort()  # Assicura ordine stabile per hashing
    structure.append(tuple(sorted(allowed_algorithms)))  # Adding the name of the algorithm to the structure

    return structure, allowed_algorithms


def generate_policy_id(structure):
    structure_str = str(sorted(structure))  # Ensure consistent ordering
    return hashlib.sha256(structure_str.encode()).hexdigest()


def generate_go_ta(policy_id, policies, allowed_algorithms):
    ta_dir = f"generated_tas/{policy_id}/AutomatedDiscovery"
    os.makedirs(ta_dir, exist_ok=True)

    go_mod = f"""
    module main

    go 1.22.3
    """

    with open(os.path.join(f"generated_tas/{policy_id}", "go.mod"), "w") as f:
        f.write(go_mod)

    go_code = "package main\n\n"
    go_code += "import (\n    \"fmt\"\n    \"log\"\n"
    for algo in allowed_algorithms:
        go_code += f"    \"./AutomatedDiscovery/{algo}\"\n"
    go_code += ")\n\n"

    go_code += f"""
    type Policy struct {{
        ID string
    }}

    func enforcePolicy(policyID string) {{
        if policyID != "{policy_id}" {{
            log.Fatal("Policy mismatch. Access denied.")
        }}
        fmt.Println("Policy enforced successfully.")
    }}
    """

    for algo in allowed_algorithms:
        go_code += f"""
        func {algo}(logFile string) {{
            fmt.Println("Executing {algo} on", logFile)
            {algo}.Run(logFile) // Call the external implementation
        }}
        """

    go_code += f"""
    func main() {{
        enforcePolicy("{policy_id}")
    """

    for algo in allowed_algorithms:
        go_code += f"\n        {algo}(\"event_log.xes\")"

    go_code += "\n    }"

    with open(os.path.join(f"generated_tas/{policy_id}", "main.go"), "w") as f:
        f.write(go_code)

    algorithm_sources = {
        "HeuristicMiner": "algorithmRepository/heuristicMiner.go",
        "AlphaMiner": "algorithmRepository/alphaMiner.go"
    }

    for algo in allowed_algorithms:
        algo_dir = os.path.join(ta_dir, algo)
        os.makedirs(algo_dir, exist_ok=True)

        if algo in algorithm_sources:
            src_path = os.path.abspath(algorithm_sources[algo])

            if os.path.exists(src_path):
                print(f"Copying {src_path} to {algo_dir}")
                shutil.copy2(src_path, os.path.join(algo_dir, f"{algo}.go"))
            else:
                print(f"Error: {src_path} not found! Skipping copy.")

    print(f"Generated TA environment: {ta_dir}")


def main(policy_path):
    policies = parse_turtle_policy(policy_path)
    structure, allowed_algorithms = extract_policy_structure(policies)
    policy_id = generate_policy_id(structure)


    existing_tas = os.listdir("generated_tas") if os.path.exists("generated_tas") else []
    print("Allowed algorithms:", allowed_algorithms)
    if policy_id not in existing_tas:
        generate_go_ta(policy_id, policies, allowed_algorithms)
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