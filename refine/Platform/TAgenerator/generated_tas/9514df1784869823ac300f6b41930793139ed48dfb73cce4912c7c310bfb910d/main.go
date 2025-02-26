package main

import (
    "fmt"
    "log"
    "os"
    "time"
    "path/filepath"
    "strings"
)


var logAccess = []
var executionAccess = []
var outputAccess = []

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

func checkAndDeleteLog(logFile string, user string) {
    expiration := "None"
    layout := "2006-01-02T15:04:05Z"
    expTime, err := time.Parse(layout, expiration)
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
func processLogFile(logFile string, fileHash string, user string) {
    // Only proceed if user has access to this specific log file
    if !checkAccess(user, logAccess) {
        log.Fatal("Access denied: user cannot access log: " + logFile)
    }

    // Log the access to this specific file only
    logFileAccess(fileHash, "ACCESS", user)

    // Check expiration for this specific file
    checkAndDeleteLog(logFile, user)

    // Execute algorithms on this specific file
    for _, algo := range ['AlphaMiner', 'HeuristicMiner'] {
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
    user := "pubk1"

    // First log file (from the policy)
    logFile1 := "data/8b7490bd9e567112d36eaf362269ad689cb3dab2aadd948de96733e09cb94bc6.xes"
    fileHash1 := "8b7490bd9e567112d36eaf362269ad689cb3dab2aadd948de96733e09cb94bc6"

    // Process the first log file independently
    processLogFile(logFile1, fileHash1, user)

    // This is where you would process additional log files if present
    // Each file would be processed independently, with its own usage log

    // Example if you had a second file:
    // logFile2 := "data/second_log_file.xes" 
    // fileHash2 := extractHashFromFilename(logFile2)
    // processLogFile(logFile2, fileHash2, user)

    // Process additional log file
    logFileAdditional := "data/1c3dfd4e0e402eaf2e781c76e7dbb7403b4d6d41bd7935b974faff39eea5d9e6.xes"
    fileHashAdditional := "1c3dfd4e0e402eaf2e781c76e7dbb7403b4d6d41bd7935b974faff39eea5d9e6"
    processLogFile(logFileAdditional, fileHashAdditional, user)
}