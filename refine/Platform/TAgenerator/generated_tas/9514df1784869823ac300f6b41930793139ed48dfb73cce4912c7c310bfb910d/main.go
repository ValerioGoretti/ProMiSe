package main

import (
    "fmt"
    "log"
    "os"
    "time"
)


var logAccess = []
var executionAccess = []
var outputAccess = []

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

func checkAndDeleteLog(logFile string) {
    expiration := "None"
    layout := "2006-01-02T15:04:05Z"
    expTime, err := time.Parse(layout, expiration)
    if err != nil {
        log.Fatal("Error parsing expiration date:", err)
    }
    if time.Now().After(expTime) {
        fmt.Println("Log expired. Deleting file:", logFile)
        os.Remove(logFile)
    }
}
func main() {
    enforcePolicy("9514df1784869823ac300f6b41930793139ed48dfb73cce4912c7c310bfb910d")
    user := "pubk1"
    logFile := "data/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.xes"

    if !checkAccess(user, logAccess) {
        log.Fatal("Access denied: user cannot access log.")
    }

    checkAndDeleteLog(logFile)

    for _, algo := range ['AlphaMiner', 'HeuristicMiner'] {
        if !checkAccess(user, executionAccess) {
            log.Fatal("Execution denied: user cannot run " + algo + ".")
        }
        fmt.Println("Executing " + algo + " on", logFile)
    }

    if !checkAccess(user, outputAccess) {
        log.Fatal("Access denied: user cannot access output.")
    }
    fmt.Println("User authorized to access output.")
}