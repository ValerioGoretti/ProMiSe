package main

import (
    "fmt"
    "log"
    "./AutomatedDiscovery/AlphaMiner"
)


    type Policy struct {
        ID string
    }

    func enforcePolicy(policyID string) {
        if policyID != "01ac7b929a53644f2e59dc940caefcb6d4732282027e5aaaa74ba0603a88f5d1" {
            log.Fatal("Policy mismatch. Access denied.")
        }
        fmt.Println("Policy enforced successfully.")
    }
    
        func AlphaMiner(logFile string) {
            fmt.Println("Executing AlphaMiner on", logFile)
            AlphaMiner.Run(logFile) // Call the external implementation
        }
        
    func main() {
        enforcePolicy("01ac7b929a53644f2e59dc940caefcb6d4732282027e5aaaa74ba0603a88f5d1")
    
        AlphaMiner("event_log.xes")
    }