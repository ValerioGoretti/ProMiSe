package main

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
        return config, fmt.Errorf("error reading config file: %v", err)
    }

    err = json.Unmarshal(data, &config)
    if err != nil {
        return config, fmt.Errorf("error parsing config file: %v", err)
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
    logEntry := fmt.Sprintf("%s %s %s\n", operation, actioner, timestamp)

    // Append to the specific file's log
    f, err := os.OpenFile(logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        return err
    }
    defer f.Close()

    if _, err := f.WriteString(logEntry); err != nil {
        return err
    }

    fmt.Printf("Logged '%s' operation by '%s' for file with hash '%s'\n", operation, actioner, fileHash)
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
    if policyID != "9514df1784869823ac300f6b41930793139ed48dfb73cce4912c7c310bfb910d" {
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
            log.Printf("Error deleting file: %v", err)
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
    for _, algo := range []string{"AlphaMiner", "HeuristicMiner"} {
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
    enforcePolicy("9514df1784869823ac300f6b41930793139ed48dfb73cce4912c7c310bfb910d")
    user := "pubk1" // This could be passed as an argument or environment variable

    // Load dynamic policy configuration
    config, err := loadPolicyConfig()
    if err != nil {
        log.Fatalf("Failed to load policy config: %v", err)
    }

    // Get all files in the data directory
    dataDir := "data"
    files, err := ioutil.ReadDir(dataDir)
    if err != nil {
        log.Fatalf("Error reading data directory: %v", err)
    }

    // Process all log files, checking policy for each
    for _, file := range files {
        if file.IsDir() || strings.HasPrefix(file.Name(), ".") {
            continue // Skip directories and hidden files
        }

        logFilePath := filepath.Join(dataDir, file.Name())
        fileHash := extractHashFromFilename(file.Name())

        fmt.Printf("Processing file: %s (hash: %s)\n", logFilePath, fileHash)

        // For each file, try to find a policy that applies
        // For now, we'll use the first policy, but this could be enhanced
        if len(config.Policies) > 0 {
            processLogFile(logFilePath, fileHash, user, 0, config)
        }
    }
}
