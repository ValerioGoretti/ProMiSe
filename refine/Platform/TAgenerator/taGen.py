import rdflib
import hashlib
import os


def parse_turtle_policy(policy_path):
    g = rdflib.Graph()
    g.parse(policy_path, format="turtle")

    policies = []
    for s, p, o in g:
        policies.append((s, p, o))

    return policies


def extract_policy_structure(policies):
    structure = []
    for s, p, o in policies:
        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue  # Ignora completamente i Blank Nodes
        if p in [rdflib.URIRef("http://example.org/ucon#allowedActions"),
                 rdflib.URIRef("http://example.org/ucon#object_id"),
                 rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")]:
            structure.append((s, p, o))  # Mantiene solo triplette rilevanti

    structure.sort()  # Assicura ordine stabile per hashing
    return structure


'''
def extract_policy_structure(policies):
    structure = []
    bnode_map = {}  # Mappa per stabilizzare i BNodes

    def stable_bnode_id(bnode):
        """Genera un ID stabile per un Blank Node basato sui suoi collegamenti"""
        if bnode not in bnode_map:
            linked_triples = sorted([(p, o) for subj, p, o in policies if subj == bnode or o == bnode])
            bnode_hash = hashlib.sha256(str(linked_triples).encode()).hexdigest()
            bnode_map[bnode] = rdflib.URIRef(f"urn:blank:{bnode_hash[:12]}")  # Usa primi 12 caratteri per stabilità
        return bnode_map[bnode]

    normalized_policies = []
    for s, p, o in policies:
        if isinstance(s, rdflib.BNode):
            s = stable_bnode_id(s)
        if isinstance(o, rdflib.BNode):
            o = stable_bnode_id(o)
        if not isinstance(o, rdflib.Literal):  # Manteniamo solo la struttura
            normalized_policies.append((s, p, o))

    normalized_policies.sort()  # Assicura ordine stabile per hashing
    return normalized_policies
'''

def generate_policy_id(structure):
    print(structure)
    structure_str = str(structure)  # Stringa consistente
    return hashlib.sha256(structure_str.encode()).hexdigest()

def generate_go_ta(policy_id, policies):
    ta_dir = f"generated_tas/{policy_id}"
    os.makedirs(ta_dir, exist_ok=True)
    module = "main"
    go_mod = f"""
    module {module}

    go 1.22.3
    """

    with open(os.path.join(ta_dir, "go.mod"), "w") as f:
        f.write(go_mod)

    go_code = f"""
    package {module}

    import (
        "fmt"
        "log"
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

    func heuristicMiner(logFile string) {{
        fmt.Println("Running Heuristic Miner on", logFile)
        // Placeholder: Replace with actual Heuristic Miner logic
    }}

    func main() {{
        enforcePolicy("{policy_id}")
        heuristicMiner("event_log.xes")
    }}
    """

    with open(os.path.join(ta_dir, "main.go"), "w") as f:
        f.write(go_code)

    print(f"Generated TA environment: {ta_dir}")


def main(policy_path):
    policies = parse_turtle_policy(policy_path)
    structure = extract_policy_structure(policies)
    policy_id = generate_policy_id(structure)

    existing_tas = os.listdir("generated_tas") if os.path.exists("generated_tas") else []
    if policy_id not in existing_tas:
        generate_go_ta(policy_id, policies)
    else:
        print("TA already exists. Skipping generation.")


if __name__ == "__main__":
    policy_file = "policy.ttl"  # Example policy file
    main(policy_file)
