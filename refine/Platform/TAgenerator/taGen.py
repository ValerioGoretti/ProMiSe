import rdflib
import hashlib
import os
import shutil
import json
import time
from datetime import datetime


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

    # Extract dynamic configuration values
    dynamic_config = {
        "log_expiration": None,
        "log_access": [],
        "execution_access": [],
        "output_access": [],
        "log_file": None
    }

    for s, p, o in policies:
        if p == rdflib.URIRef("http://example.org/ucon#allowedActions") and isinstance(o, rdflib.BNode):
            algorithm_nodes.add(o)

        if p == rdflib.URIRef("http://example.org/eventLog#fileName"):
            log_file = str(o)
            dynamic_config["log_file"] = str(o)

        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue

        if p in [rdflib.URIRef("http://example.org/ucon#allowedActions"),
                 rdflib.URIRef("http://example.org/ucon#object_id"),
                 rdflib.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")]:
            structure.append((str(s), str(p), str(o)))  # Convert URIRefs to strings

        if p == rdflib.URIRef("http://example.org/ucon#logExpiration"):
            log_expiration = str(o)
            dynamic_config["log_expiration"] = str(o)

        if p == rdflib.URIRef("http://example.org/ucon#logAccess"):
            access_users = [user.strip() for user in o.split(",")]
            log_access.update(access_users)
            dynamic_config["log_access"] = access_users

        if p == rdflib.URIRef("http://example.org/ucon#executionAccess"):
            exec_users = [user.strip() for user in o.split(",")]
            execution_access.update(exec_users)
            dynamic_config["execution_access"] = exec_users

        if p == rdflib.URIRef("http://example.org/ucon#outputAccess"):
            out_users = [user.strip() for user in o.split(",")]
            output_access.update(out_users)
            dynamic_config["output_access"] = out_users

    for s, p, o in policies:
        if s in algorithm_nodes and p == rdflib.URIRef("http://example.org/pmt#algorithm"):
            algo = o.split("#")[-1]
            allowed_algorithms.add(algo)

    # Convert all components to tuples for consistent sorting
    final_structure = structure + [tuple(sorted(allowed_algorithms))]  # Convert allowed_algorithms to tuple

    return final_structure, allowed_algorithms, dynamic_config


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


def store_log_file(log_file, data_dir, policy_id=None):
    """Store log file using content hash as filename, avoid duplicates"""
    if not log_file or not os.path.exists(log_file):
        print(f"Log file {log_file} not found.")
        return None, None

    # Generate hash from file content
    content_hash = hash_file_content(log_file)
    if not content_hash:
        return None, None

    # Get file extension
    _, file_extension = os.path.splitext(log_file)

    # Create new filename based on content hash
    hashed_filename = f"{content_hash}{file_extension}"
    destination_path = os.path.join(data_dir, hashed_filename)

    # Check if this exact file (based on content) already exists
    if os.path.exists(destination_path):
        print(f"File with identical content already exists at {destination_path}")
    else:
        # Copy file with hashed name
        shutil.copy(log_file, destination_path)
        print(f"File copied to: {destination_path}")

        # Log the file addition - only for this specific file
        if policy_id:
            log_file_access(policy_id, content_hash, "ADD", "system")

    return hashed_filename, content_hash


def update_file_mapping(data_dir, log_file, content_hash, policy_id):
    """Update the JSON mapping file with file metadata"""
    # Create mapping file path
    mapping_file = os.path.join(data_dir, "file_mapping.json")

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get file size
    file_size = os.path.getsize(log_file)

    # File metadata
    file_metadata = {
        "original_name": os.path.basename(log_file),
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

        print(f"Updated file mapping with new entry: {os.path.basename(log_file)}")

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


def generate_go_ta(policy_id, allowed_algorithms, dynamic_config, original_policy_path):
    ta_dir = f"generated_tas/{policy_id}/AutomatedDiscovery"
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    os.makedirs(ta_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Save dynamic configuration
    config_file = save_policy_config(policy_id, dynamic_config, original_policy_path)

    # Store log file with content hash as name if it exists
    log_file = dynamic_config.get("log_file")
    hashed_filename = None
    content_hash = None

    if log_file and os.path.exists(log_file):
        hashed_filename, content_hash = store_log_file(log_file, data_dir, policy_id)

        # Update the JSON mapping file
        if content_hash:
            update_file_mapping(data_dir, log_file, content_hash, policy_id)

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


def update_existing_ta(policy_id, log_file, dynamic_config, original_policy_path):
    """Update an existing TA with a new log file and/or policy configuration"""
    data_dir = os.path.join(f"generated_tas/{policy_id}", "data")
    if not os.path.exists(data_dir):
        print(f"Data directory for policy {policy_id} does not exist.")
        return False

    # Update policy configuration
    save_policy_config(policy_id, dynamic_config, original_policy_path)

    # If there's a log file, store it
    if log_file and os.path.exists(log_file):
        # Store log file with content hash
        hashed_filename, content_hash = store_log_file(log_file, data_dir, policy_id)

        # Update the JSON mapping file
        if content_hash:
            updated = update_file_mapping(data_dir, log_file, content_hash, policy_id)
            if updated:
                print(f"Updated TA {policy_id} with new log file: {os.path.basename(log_file)} (hash: {content_hash})")
                return True

    print(f"Updated TA {policy_id} with new policy configuration")
    return True


def main(policy_path):
    policies = parse_turtle_policy(policy_path)
    structure, allowed_algorithms, dynamic_config = extract_policy_structure(policies)
    policy_id = generate_policy_id(structure)

    existing_tas = os.listdir("generated_tas") if os.path.exists("generated_tas") else []
    print("Allowed algorithms:", allowed_algorithms)

    if policy_id not in existing_tas:
        print(f"Creating new TA with ID: {policy_id}")
        generate_go_ta(policy_id, allowed_algorithms, dynamic_config, policy_path)
    else:
        print(f"TA with ID {policy_id} already exists. Updating configuration.")
        update_existing_ta(policy_id, dynamic_config.get("log_file"), dynamic_config, policy_path)


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
            main(policy_file)
        elif choice == "2":
            clean_generated_tas()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")