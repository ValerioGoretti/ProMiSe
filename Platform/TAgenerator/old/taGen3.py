import rdflib
import hashlib
import os
import shutil
import json
from datetime import datetime
import flask
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from rdflib.namespace import RDF
import rdflib



def parse_turtle_policy(policy):
    g = rdflib.Graph()
    g.parse(data=policy, format="turtle")

    policies = []
    for s, p, o in g:
        policies.append((s, p, o))

    return policies

def extract_rdf_list(graph, list_node):
    """Extracts an RDF list (rdf:List) as a Python list of RDF terms (can be BNode, URI, Literal)."""
    elements = []
    while list_node and list_node != RDF.nil:
        first = graph.value(list_node, RDF.first)
        if first:
            elements.append(first)
        list_node = graph.value(list_node, RDF.rest)
    return elements



def extract_policy_structure(policies):
    structure = []
    dynamic_config = {
        "log_file": None,
        "logUsageRules": {},
        "outputRules": {},
        "processingRules": {}
    }

    g = rdflib.Graph()
    for s, p, o in policies:
        g.add((s, p, o))

    # === Log file name ===
    for s in g.subjects(rdflib.URIRef("http://example.org/ucon#object_id")):
        for _, _, obj_node in g.triples((s, rdflib.URIRef("http://example.org/ucon#object_id"), None)):
            for _, p2, o2 in g.triples((obj_node, rdflib.URIRef("http://example.org/eventLog#fileName"), None)):
                dynamic_config["log_file"] = str(o2)

    # === LOG USAGE RULES ===
    for rule_node in g.objects(None, rdflib.URIRef("http://example.org/ucon#logUsageRules")):
        for _, p, o in g.triples((rule_node, None, None)):
            pname = p.split("#")[-1]

            if pname == "logExpiration":
                dynamic_config["logUsageRules"]["logExpiration"] = str(o)
            elif pname == "maxAccessCount":
                dynamic_config["logUsageRules"]["maxAccessCount"] = int(str(o))
            elif pname == "allowedLocations":
                dynamic_config["logUsageRules"].setdefault("allowedLocations", []).append(str(o))
            elif pname == "accessControlRules":
                # Supporta sia liste che singoli string literal
                dynamic_config["logUsageRules"].setdefault("accessControlRules", []).extend(
                    [s.strip().strip('"') for s in str(o).split(",")]
                )
            elif pname == "attributeExclusionRules":
                excl = {}
                for _, p2, o2 in g.triples((o, None, None)):
                    if p2.endswith("scope"):
                        excl["scope"] = str(o2)
                    elif p2.endswith("eventAttribute"):
                        excl["eventAttribute"] = str(o2)
                    elif p2.endswith("excludedAttributes"):
                        keys = []
                        for _, _, o3 in g.triples((o2, rdflib.URIRef("http://example.org/ucon#attributeKey"), None)):
                            keys.append(str(o3))
                        excl["excludedAttributes"] = keys
                dynamic_config["logUsageRules"]["attributeExclusionRules"] = excl
            elif pname == "allowedTimeRange":
                time_range = {}
                for _, p2, o2 in g.triples((o, None, None)):
                    key = p2.split("#")[-1]
                    time_range[key] = str(o2)
                dynamic_config["logUsageRules"]["allowedTimeRange"] = time_range
            elif pname == "semanticLogConstraints":
                sem = {}
                for _, p2, o2 in g.triples((o, None, None)):
                    if p2.endswith("eventAttribute"):
                        sem["eventAttribute"] = str(o2)
                    elif p2.endswith("mustInclude"):
                        sem["mustInclude"] = extract_rdf_list(g, o2)
                    elif p2.endswith("mustExclude"):
                        sem["mustExclude"] = extract_rdf_list(g, o2)
                dynamic_config["logUsageRules"]["semanticLogConstraints"] = sem

    # === OUTPUT RULES ===
    for rule_node in g.objects(None, rdflib.URIRef("http://example.org/ucon#outputRules")):
        for _, p, o in g.triples((rule_node, None, None)):
            pname = p.split("#")[-1]

            if pname == "allowedLocations":
                dynamic_config["outputRules"].setdefault("allowedLocations", []).append(str(o))
            elif pname == "outputExpiration":
                dynamic_config["outputRules"]["outputExpiration"] = str(o)
            elif pname == "accessControlRules":
                dynamic_config["outputRules"].setdefault("accessControlRules", []).extend(
                    [s.strip().strip('"') for s in str(o).split(",")]
                )
            elif pname == "allowedTimeRange":
                time_range = {}
                for _, p2, o2 in g.triples((o, None, None)):
                    key = p2.split("#")[-1]
                    time_range[key] = str(o2)
                dynamic_config["outputRules"]["allowedTimeRange"] = time_range

    # === PROCESSING RULES ===
    allowed_algorithms = []
    for rule_node in g.objects(None, rdflib.URIRef("http://example.org/ucon#processingRules")):
        for _, p, o in g.triples((rule_node, None, None)):
            pname = p.split("#")[-1]

            if pname == "accessControlRules":
                dynamic_config["processingRules"].setdefault("accessControlRules", []).extend(
                    [s.strip().strip('"') for s in str(o).split(",")]
                )
            elif pname == "allowedTechinique":
                algo_nodes = extract_rdf_list(g, o)
                for algo_node in algo_nodes:
                    for _, p2, o2 in g.triples((algo_node, rdflib.URIRef("http://example.org/pmt#algorithm"), None)):
                        algo_name = str(o2).split("#")[-1]
                        allowed_algorithms.append(algo_name)

    dynamic_config["processingRules"]["allowedTechniques"] = allowed_algorithms

    static_structure = [tuple(sorted(allowed_algorithms))]

    return static_structure, allowed_algorithms, dynamic_config

def generate_policy_id(structure):
    # Now structure contains only tuples which can be sorted
    structure_str = str(sorted(structure))
    return hashlib.sha256(structure_str.encode()).hexdigest()


def hash_file_content(file_path):
    """Generate SHA256 hash based on file content"""
    if not os.path.exists(file_path):
        return None

    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def hash_content(content: bytes) -> str:
    """Generate SHA256 hash based on file content"""
    hash_sha256 = hashlib.sha256()
    if isinstance(content, str):
        content = content.encode('utf-8')

    hash_sha256.update(content)
    return hash_sha256.hexdigest()



def log_file_access(policy_id, file_hash, operation, actioner):
    """
    Log file access information in a file-specific log
    Each file has its own dedicated usage log that is updated independently
    """
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    usage_log_dir = os.path.join(data_dir, "usage_logs")
    os.makedirs(usage_log_dir, exist_ok=True)

    # Create a log file specific to this file hash - ensuring each file has its own log
    usage_log_file = os.path.join(usage_log_dir, f"{file_hash}_usage.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = f"{operation} {actioner} {timestamp}\n"

    # Append to the specific file's log
    with open(usage_log_file, "a") as f:
        f.write(log_entry)

    print(f"Logged '{operation}' by '{actioner}' for file with hash '{file_hash}'")
    return True


def store_log_file(log_file, log_file_content, data_dir, policy_id=None):
    """Store log file using content hash as filename, avoid duplicates"""
    '''if not log_file or not os.path.exists(log_file):
        print(f"Log file {log_file} not found.")
        return None, None
    '''
    # Generate hash from file content
    content_hash = hash_content(log_file_content)
    if not content_hash:
        return None, None

    # Get file extension
    _, file_extension = os.path.splitext(log_file.filename)

    # Create new filename based on content hash
    hashed_filename = f"{content_hash}{file_extension}"
    destination_path = os.path.join(data_dir, hashed_filename)

    # Check if this exact file (based on content) already exists
    if os.path.exists(destination_path):
        print(f"File with identical content already exists at {destination_path}")
    else:
        # Copy file with hashed name
        with open(destination_path, "wb") as f:
            f.write(log_file_content.encode("utf-8"))

        print(f"File copied to: {destination_path}")

        # Log the file addition - only for this specific file
        if policy_id:
            log_file_access(policy_id, content_hash, "ADD", "system")

    return hashed_filename, content_hash


def update_file_mapping(data_dir, log_file, content_hash, policy_id, hashed_file_name):
    """Update the JSON mapping file with file metadata"""

    # Create mapping file path
    mapping_file = os.path.join(data_dir, "file_mapping.json")

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get file size
    file_path = os.path.join(data_dir, hashed_file_name)
    file_size = os.path.getsize(file_path)

    # File metadata
    file_metadata = {
        "original_name": os.path.basename(log_file.filename),
        "content_hash": content_hash,
        "date_added": timestamp,
        "file_size": file_size,
        "data_owner": "default_owner"  # Static for now as requested
    }

    # Read existing mapping if it exists
    if os.path.exists(mapping_file):
        with open(mapping_file, "r") as f:
            try:
                mapping_data = json.load(f)
            except json.JSONDecodeError:
                mapping_data = {"files": []}
    else:
        mapping_data = {"files": []}

    # Check if this file is already in the mapping
    file_exists = False
    for file_entry in mapping_data["files"]:
        if file_entry["content_hash"] == content_hash:
            file_exists = True
            break

    # Add new file if it doesn't exist
    if not file_exists:
        mapping_data["files"].append(file_metadata)

        # Write updated mapping
        with open(mapping_file, "w") as f:
            json.dump(mapping_data, f, indent=4)

        print(f"Updated file mapping with new entry: {os.path.basename(log_file.filename)}")

        # Log the mapping update - only for this specific file
        log_file_access(policy_id, content_hash, "MAP", "system")

        return True

    return False

def save_policy_config(policy_id, dynamic_config, original_policy_path):
    """Save the dynamic configuration values to a JSON file"""
    config_dir = os.path.join(f"generated_tas/{policy_id}", "config")
    os.makedirs(config_dir, exist_ok=True)

    # Add source policy path to configuration
    config_with_source = dynamic_config.copy()
    config_with_source["source_policy"] = original_policy_path
    config_with_source["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the policy configuration file
    config_file = os.path.join(config_dir, "policy_config.json")

    # Check if config already exists and merge if it does
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                existing_config = json.load(f)

            # Add this policy to the policies array
            if "policies" not in existing_config:
                existing_config["policies"] = []

            # Check if this policy source already exists
            policy_exists = False
            for i, policy in enumerate(existing_config["policies"]):
                if policy.get("source_policy") == original_policy_path:
                    # Update existing policy
                    existing_config["policies"][i] = config_with_source
                    policy_exists = True
                    break

            if not policy_exists:
                existing_config["policies"].append(config_with_source)

            with open(config_file, "w") as f:
                json.dump(existing_config, f, indent=4)
        except Exception as e:
            print(f"Error updating existing config: {e}")
            # If error, overwrite with new config
            with open(config_file, "w") as f:
                json.dump({"policies": [config_with_source]}, f, indent=4)
    else:
        # Create new config file
        with open(config_file, "w") as f:
            json.dump({"policies": [config_with_source]}, f, indent=4)

    print(f"Saved policy configuration to {config_file}")
    return config_file



def generate_go_ta(policy_id, allowed_algorithms, dynamic_config, original_policy_path, log_file, log_file_content):
    print("entra generate_go_ta")
    ta_dir = f"generated_tas/{policy_id}/AutomatedDiscovery"
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    os.makedirs(ta_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    print("prima save_policy_config")

    # Save dynamic configuration
    config_file = save_policy_config(policy_id, dynamic_config, original_policy_path)

    print("dopo save_policy_config")

    # Store log file with content hash as name if it exists
    #log_file = dynamic_config.get("log_file")
    hashed_filename = None
    content_hash = None
    print(log_file)
    print(log_file.filename)
    print(log_file.read().decode('utf-8'))

    print("prima store_log_file")
    hashed_filename, content_hash = store_log_file(log_file, log_file_content, data_dir, policy_id)
    print("dopo store_log_file")

    print(hashed_filename)
    print(content_hash)


    # Update the JSON mapping file
    if content_hash:
        #TODO: Check it
        update_file_mapping(data_dir, log_file, content_hash, policy_id, hashed_filename)

    go_mod = """module main

go 1.22.3"""

    with open(os.path.join(f"generated_tas/{policy_id}", "go.mod"), "w") as f:
        f.write(go_mod)

    # The Go code with properly escaped format specifiers
    go_code = """package main

import (
    "encoding/json"
    "fmt"
    "io/ioutil"
    "log"
    "os"
    "path/filepath"
    "strings"
    "time"
)

// PolicyConfig holds the dynamic configuration values
type PolicyConfig struct {
    Policies []struct {
        LogExpiration   string   `json:"log_expiration"`
        LogAccess       []string `json:"log_access"`
        ExecutionAccess []string `json:"execution_access"`
        OutputAccess    []string `json:"output_access"`
        LogFile         string   `json:"log_file"`
        SourcePolicy    string   `json:"source_policy"`
        LastUpdated     string   `json:"last_updated"`
    } `json:"policies"`
}

// loadPolicyConfig loads the policy configuration from the JSON file
func loadPolicyConfig() (PolicyConfig, error) {
    var config PolicyConfig
    configFile := "config/policy_config.json"

    data, err := ioutil.ReadFile(configFile)
    if err != nil {
        return config, fmt.Errorf("error reading config file: %%v", err)
    }

    err = json.Unmarshal(data, &config)
    if err != nil {
        return config, fmt.Errorf("error parsing config file: %%v", err)
    }

    if len(config.Policies) == 0 {
        return config, fmt.Errorf("no policies found in config")
    }

    return config, nil
}

// findPolicyBySource finds a policy in the config by its source file
func findPolicyBySource(config PolicyConfig, sourcePolicy string) (int, bool) {
    for i, policy := range config.Policies {
        if policy.SourcePolicy == sourcePolicy {
            return i, true
        }
    }
    return 0, false
}

// logFileAccess records an access event to the usage log for a specific file only
func logFileAccess(fileHash string, operation string, actioner string) error {
    timestamp := time.Now().Format("2006-01-02 15:04:05")
    logDir := filepath.Join("data", "usage_logs")

    // Create the directory if it doesn't exist
    if err := os.MkdirAll(logDir, 0755); err != nil {
        return err
    }

    // Each file has its own dedicated log file based on its hash
    logFile := filepath.Join(logDir, fileHash + "_usage.log")
    logEntry := fmt.Sprintf("%%s %%s %%s\\n", operation, actioner, timestamp)

    // Append to the specific file's log
    f, err := os.OpenFile(logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        return err
    }
    defer f.Close()

    if _, err := f.WriteString(logEntry); err != nil {
        return err
    }

    fmt.Printf("Logged '%%s' operation by '%%s' for file with hash '%%s'\\n", operation, actioner, fileHash)
    return nil
}

// extractHashFromFilename extracts the hash portion from a filename
func extractHashFromFilename(filename string) string {
    // Get just the filename without path
    base := filepath.Base(filename)

    // Find the first dot which separates hash from extension
    dotIndex := strings.Index(base, ".")

    // If there's no dot, return the whole name
    if dotIndex == -1 {
        return base
    }

    // Return just the hash part
    return base[:dotIndex]
}

func checkAccess(user string, accessList []string) bool {
    for _, allowed := range accessList {
        if user == allowed {
            return true
        }
    }
    return false
}

func enforcePolicy(policyID string) {
    if policyID != "%s" {
        log.Fatal("Policy mismatch. Access denied.")
    }
    fmt.Println("Policy enforced successfully.")
}

func checkAndDeleteLog(logFile string, user string, logExpiration string) {
    layout := "2006-01-02T15:04:05Z"
    expTime, err := time.Parse(layout, logExpiration)
    if err != nil {
        log.Fatal("Error parsing expiration date:", err)
    }

    // Extract the hash from the filename for logging
    fileHash := extractHashFromFilename(logFile)

    // Log that we checked this specific file
    logFileAccess(fileHash, "CHECK", user)

    if time.Now().After(expTime) {
        fmt.Println("Log expired. Deleting file:", logFile)

        // Log the deletion attempt for this specific file
        logFileAccess(fileHash, "DELETE", user)

        err := os.Remove(logFile)
        if err != nil {
            log.Printf("Error deleting file: %%v", err)
        }
    }
}

func processLogFile(logFile string, fileHash string, user string, policy int, config PolicyConfig) {
    // Get dynamic values for this policy
    logAccess := config.Policies[policy].LogAccess
    executionAccess := config.Policies[policy].ExecutionAccess
    outputAccess := config.Policies[policy].OutputAccess
    logExpiration := config.Policies[policy].LogExpiration

    // Only proceed if user has access to this specific log file
    if !checkAccess(user, logAccess) {
        log.Fatal("Access denied: user cannot access log: " + logFile)
    }

    // Log the access to this specific file only
    logFileAccess(fileHash, "ACCESS", user)

    // Check expiration for this specific file
    checkAndDeleteLog(logFile, user, logExpiration)

    // Execute algorithms on this specific file
    for _, algo := range []string{%s} {
        if !checkAccess(user, executionAccess) {
            log.Fatal("Execution denied: user cannot run " + algo + ".")
        }
        fmt.Println("Executing " + algo + " on", logFile)

        // Log the execution for this specific file only
        logFileAccess(fileHash, "EXECUTE_" + algo, user)
    }

    // Check output access for this specific file
    if !checkAccess(user, outputAccess) {
        log.Fatal("Access denied: user cannot access output for " + logFile)
    }

    // Log the output access for this specific file only
    logFileAccess(fileHash, "OUTPUT", user)

    fmt.Println("User authorized to access output for: " + logFile)
}

func main() {
    enforcePolicy("%s")
    user := "pubk1" // This could be passed as an argument or environment variable

    // Load dynamic policy configuration
    config, err := loadPolicyConfig()
    if err != nil {
        log.Fatalf("Failed to load policy config: %%v", err)
    }

    // Get all files in the data directory
    dataDir := "data"
    files, err := ioutil.ReadDir(dataDir)
    if err != nil {
        log.Fatalf("Error reading data directory: %%v", err)
    }

    // Process all log files, checking policy for each
    for _, file := range files {
        if file.IsDir() || strings.HasPrefix(file.Name(), ".") {
            continue // Skip directories and hidden files
        }

        logFilePath := filepath.Join(dataDir, file.Name())
        fileHash := extractHashFromFilename(file.Name())

        fmt.Printf("Processing file: %%s (hash: %%s)\\n", logFilePath, fileHash)

        // For each file, try to find a policy that applies
        // For now, we'll use the first policy, but this could be enhanced
        if len(config.Policies) > 0 {
            processLogFile(logFilePath, fileHash, user, 0, config)
        }
    }
}
""" % (policy_id, ", ".join([f'"{algo}"' for algo in allowed_algorithms]), policy_id)

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

    with open(os.path.join(f"generated_tas/{policy_id}", "main.go"), "w") as f:
        f.write(go_code)

    print(f"Generated TA environment: {ta_dir}")
    return True

#TODO: check it
def update_existing_ta(policy_id, dynamic_config, original_policy_path, log_file, log_file_content):
    print("ENTRA IN UPDATE EXISTING TA")
    """Update an existing TA with a new log file and/or policy configuration"""
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    if not os.path.exists(data_dir):
        print(f"Data directory for policy {policy_id} does not exist.")
        return False

    # Update policy configuration
    save_policy_config(policy_id, dynamic_config, original_policy_path)


    hashed_filename, content_hash = store_log_file(log_file, log_file_content, data_dir, policy_id)

    # Update the JSON mapping file
    if content_hash:
        updated = update_file_mapping(data_dir, log_file, content_hash, policy_id, hashed_filename)
        if updated:
            print(f"Updated TA {policy_id} with new log file: {os.path.basename(log_file.filename)} (hash: {content_hash})")
            return True

    print(f"Updated TA {policy_id} with new policy configuration")
    return True

def clean_generated_tas():
    folder = "generated_tas"
    if os.path.exists(folder):
        for ta_folder in os.listdir(folder):
            ta_folder_path = os.path.join(folder, ta_folder)
            if os.path.isdir(ta_folder_path):
                shutil.rmtree(ta_folder_path)
                print(f"Cleaned {ta_folder_path}.")
    else:
        print("No TA directories found to clean.")


def main(files):
    policy_file = files['policy_file']
    log_file = files['log_file']

    # Access file content
    policy_file_content = policy_file.read().decode('utf-8')  # Assuming text-based files
    policy_file.seek(0)

    log_file_content = log_file.read().decode('utf-8')
    log_file.seek(0)

    policies = parse_turtle_policy(policy_file_content)
    structure, allowed_algorithms, dynamic_config = extract_policy_structure(policies)
    policy_id = generate_policy_id(structure)

    existing_tas = os.listdir("../generated_tas") if os.path.exists("../generated_tas") else []
    print("Allowed algorithms:", allowed_algorithms)

    if policy_id not in existing_tas:
        print(f"Creating new TA with ID: {policy_id}")
        generate_go_ta(policy_id, allowed_algorithms, dynamic_config, policy_file.filename, log_file, log_file_content)
    else:
        print(f"TA with ID {policy_id} already exists. Updating configuration.")
        update_existing_ta(policy_id, dynamic_config, policy_file.filename, log_file, log_file_content)



def create_flask_app():
    app = Flask(__name__)

    @app.route('/setup', methods=['POST'])
    def setup_ta():
        if 'policy_file' not in request.files or 'log_file' not in request.files:
            return jsonify({"error": "Both policy_file and log_file are required"}), 400

        print("Received files:", request.files)
        '''
        files = {}
        for key in ['policy_file', 'log_file']:
            file = request.files[key]
            print(file)

            if file.filename == '':
                return jsonify({"error": f"No file selected for {key}"}), 400

            filename = secure_filename(file.filename)
            files[key] = filename'''

        #clean_generated_tas()
        main(request.files)
        '''return jsonify({
            "message": "Files uploaded successfully",
            "policy_file": files['policy_file'],
            "log_file": files['log_file']
        }), 200'''
        return "ok"

    return app

if __name__ == "__main__":
    app = create_flask_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
















'''
if __name__ == "__main__":
    #main("policy5.ttl")
    while True:
        print("\n --------- MENU ---------\n")
        print("Select an option:")
        print("1. Generate Trusted Application (TA) based on policy.")
        print("2. Clean generated TA directories.")
        print("3. Exit.")
        print("\n")
        choice = input("> Enter your choice: ")

        if choice == "1":
            main_server()
        elif choice == "2":
            clean_generated_tas()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
'''