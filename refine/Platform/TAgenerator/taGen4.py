from flask import Flask, request, jsonify
import os
import json
import hashlib
import time
import shutil
from  go_template import MAIN_GO_TEMPLATE

app = Flask(__name__)

@app.route("/setup", methods=["POST"])
def setup_ta():
    log_file = request.files.get("log_file")
    policy_file = request.files.get("policy_file")

    if not log_file or not policy_file:
        return "Missing log or policy file", 400

    log_data = log_file.read()
    policy_data = policy_file.read()

    dynamic_config = json.loads(policy_data)
    static_structure = [tuple(sorted(dynamic_config.get("processingRules", {}).get("allowedTechniques", [])))]

    log_filename = log_file.filename
    tmp_log_path = "tmp_log.xes"
    with open(tmp_log_path, "wb") as f:
        f.write(log_data)

    ta_path, log_id = generate_go_ta(static_structure, dynamic_config["processingRules"]["allowedTechniques"], dynamic_config, tmp_log_path)

    return jsonify({
        "status": "TA generated",
        "ta_path": ta_path,
        "log_id": log_id
    })

def hash_policy_structure(static_structure):
    stringified = json.dumps(static_structure, sort_keys=True)
    return hashlib.sha256(stringified.encode()).hexdigest()[:16]

def store_log_file(ta_path, log_file_path):
    with open(log_file_path, "rb") as f:
        content = f.read()
    hash_value = hashlib.sha256(content).hexdigest()[:16]
    log_filename = os.path.basename(log_file_path)
    log_id = log_filename.split(".")[0] + "_" + str(time.time()).replace('.', '')
    log_dir = os.path.join(ta_path, "logs", log_id)
    os.makedirs(log_dir, exist_ok=True)
    shutil.copy(log_file_path, os.path.join(log_dir, log_filename))
    return log_id, log_dir, log_filename

def generate_go_ta(static_structure, allowed_algorithms, dynamic_config, log_file_path):
    ta_hash = hash_policy_structure(static_structure)
    ta_path = os.path.join("generated_tas", ta_hash)
    os.makedirs(ta_path, exist_ok=True)

    algo_repo = "algorithmRepository"
    algo_dst = os.path.join(ta_path, "AutomatedDiscovery")
    os.makedirs(algo_dst, exist_ok=True)
    for algo in allowed_algorithms:
        src = os.path.join(algo_repo, algo + ".go")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(algo_dst, algo + ".go"))
        else:
            print(f"[WARN] Algorithm source not found: {src}")

    log_id, log_dir, log_filename = store_log_file(ta_path, log_file_path)

    with open(os.path.join(log_dir, "policy_config.json"), "w") as f:
        json.dump(dynamic_config, f, indent=2)

    with open(os.path.join(log_dir, "access_state.json"), "w") as f:
        json.dump({
            "accessCount": 0,
            "filtered": False,
            "logDeleted": False,
            "outputDeleted": False
        }, f, indent=2)

    open(os.path.join(log_dir, "audit.log"), "w").close()

    # Generate main.go
    with open(os.path.join(ta_path, "main.go"), "w") as f:
        f.write(MAIN_GO_TEMPLATE)

    # Generate go.mod
    with open(os.path.join(ta_path, "go.mod"), "w") as f:
        f.write("module trustedapp\n\ngo 1.20\n")

    # Optional: create build.sh for easy compilation
    with open(os.path.join(ta_path, "build.sh"), "w") as f:
        f.write("""#!/bin/bash
cd "$(dirname "$0")"
go build -o ta_app main.go
""")
        os.chmod(os.path.join(ta_path, "build.sh"), 0o755)

    return ta_path, log_id

if __name__ == "__main__":
    os.makedirs("generated_tas", exist_ok=True)
    app.run(port=5000)
