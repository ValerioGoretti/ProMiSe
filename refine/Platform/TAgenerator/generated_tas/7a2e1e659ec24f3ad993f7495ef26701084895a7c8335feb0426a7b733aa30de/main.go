package main

import (
    "fmt"
    "log"
    "./AutomatedDiscovery/HeuristicMiner"
    "./AutomatedDiscovery/AlphaMiner"
)


    type Policy struct {
        ID string
    }

    func enforcePolicy(policyID string) {
        if policyID != "7a2e1e659ec24f3ad993f7495ef26701084895a7c8335feb0426a7b733aa30de" {
            log.Fatal("Policy mismatch. Access denied.")
        }
        fmt.Println("Policy enforced successfully.")
    }
    
        func HeuristicMiner(logFile string) {
            fmt.Println("Executing HeuristicMiner on", logFile)
            HeuristicMiner.Run(logFile) // Call the external implementation
        }
        
        func AlphaMiner(logFile string) {
            fmt.Println("Executing AlphaMiner on", logFile)
            AlphaMiner.Run(logFile) // Call the external implementation
        }
        
    func main() {
        enforcePolicy("7a2e1e659ec24f3ad993f7495ef26701084895a7c8335feb0426a7b733aa30de")
    
        HeuristicMiner("event_log.xes")
        AlphaMiner("event_log.xes")
    }