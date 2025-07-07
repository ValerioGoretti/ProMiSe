from flask import Flask, request, jsonify
from rdflib import Graph
from policy_utils import parse_policy_turtle, save_policy_instance

app = Flask(__name__)

def validate_policy(policy_json):
    print("Validating policy...")
    # Placeholder: aggiungi controlli su structure, valori, vincoli, etc.
    return True

@app.route("/setup", methods=["POST"])
def setup_policy():
    if "policy_file" not in request.files or "log_file" not in request.files:
        return jsonify({"error": "Both policy_file and log_file are required."}), 400

    policy_file = request.files["policy_file"]
    log_file = request.files["log_file"]

    policy_bytes = policy_file.read()
    log_bytes = log_file.read()

    # parse RDF dalla stringa di policy
    g = Graph()
    g.parse(data=policy_bytes, format="ttl")
    policy_json = parse_policy_turtle(g)

    # Validazione della policy
    validate_policy(policy_json)

    log_file.seek(0)
    log_bytes = log_file.read()

    # Salvataggio
    #result = save_policy_instance(g, policy_json, policy_bytes, log_file.filename, log_bytes)
    result = save_policy_instance(g, policy_json, policy_bytes, log_file.filename, log_bytes)

    policy_json["policies"][0]["source_policy"] = str(result["config_path"]) + "/policy.ttl"

    return jsonify({
        "message": "Policy and log saved successfully.",
        "details": result
    })

if __name__ == "__main__":
    app.run(debug=True)
