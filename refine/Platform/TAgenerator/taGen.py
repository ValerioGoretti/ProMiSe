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
    for s, p, o in policies:
        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue  # Ignora completamente i Blank Nodes
        if p in [rdflib.URIRef("http://example.org/ucon#allowedActions"),
                 rdflib.URIRef("http://example.org/ucon#object_id"),
                 rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")]:
            structure.append((s, p, o))  # Mantiene solo triplette rilevanti
        if p == rdflib.URIRef("http://example.org/ucon#allowedActions"):
            allowed_algorithms.add(o.split("#")[-1])  # Estrae il nome dell'algoritmo

    structure.sort()  # Assicura ordine stabile per hashing
    return structure, allowed_algorithms


def generate_policy_id(structure):
    structure_str = str(sorted(structure))  # Ensure consistent ordering
    return hashlib.sha256(structure_str.encode()).hexdigest()


def generate_go_ta(policy_id, policies, allowed_algorithms):
    ta_dir = f"generated_tas/{policy_id}/AutomatedDiscovery/HeuristicMiner"
    os.makedirs(ta_dir, exist_ok=True)

    go_mod = f"""
    module main

    go 1.22.3
    """

    with open(os.path.join(f"generated_tas/{policy_id}", "go.mod"), "w") as f:
        f.write(go_mod)

    go_code = f"""
    package main

    import (
        "fmt"
        "log"
        "./AutomatedDiscovery/HeuristicMiner"
    )

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
            HeuristicMiner.Run(logFile) // Call the external implementation
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

    heuristic_miner_src = "heuristicMiner.go"  # Percorso del file originale
    heuristic_miner_dst = os.path.join(ta_dir, "heuristicMiner.go")
    shutil.copy(heuristic_miner_src, heuristic_miner_dst)  # Copia il file

    print(f"Generated TA environment: {ta_dir}")


def main(policy_path):
    policies = parse_turtle_policy(policy_path)
    structure, allowed_algorithms = extract_policy_structure(policies)
    policy_id = generate_policy_id(structure)

    existing_tas = os.listdir("generated_tas") if os.path.exists("generated_tas") else []
    if policy_id not in existing_tas:
        generate_go_ta(policy_id, policies, allowed_algorithms)
    else:
        print("TA already exists. Skipping generation.")


if __name__ == "__main__":
    policy_file = "policy.ttl"  # Example policy file
    main(policy_file)