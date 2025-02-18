package main

import (
    "fmt"
    "log"
    "./AutomatedDiscovery/HeuristicMiner"
)


    type Policy struct {
        ID string
    }

    func enforcePolicy(policyID string) {
        if policyID != "8416deae5f5942b2f2b7ae4a87e0e71a5c7099d447ec4422ff9cb83835df9364" {
            log.Fatal("Policy mismatch. Access denied.")
        }
        fmt.Println("Policy enforced successfully.")
    }
    
        func HeuristicMiner(logFile string) {
            fmt.Println("Executing HeuristicMiner on", logFile)
            HeuristicMiner.Run(logFile) // Call the external implementation
        }
        
    func main() {
        enforcePolicy("8416deae5f5942b2f2b7ae4a87e0e71a5c7099d447ec4422ff9cb83835df9364")
    
        HeuristicMiner("event_log.xes")
    }