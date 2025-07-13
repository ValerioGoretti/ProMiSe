package main

import (
	"fmt"
	"log"
	"net/http"
	"ta1/taPackage/config"
	"ta1/taPackage/enforcement"
	"ta1/taPackage/rpc"
)

func main() {
	//printConfig()
	err := config.LoadMappings("mapping.json")
	if err != nil {
		log.Fatal("Errore mapping:", err)
	}

	http.HandleFunc("/log", rpc.HandleLogAccess)
	http.HandleFunc("/process", rpc.HandleProcessing)
	http.HandleFunc("/output", rpc.HandleOutputAccess)
	http.HandleFunc("/policy", rpc.HandlePolicyInfo)
	http.HandleFunc("/monitoring", rpc.HandleMonitoring)

	log.Println("Server in ascolto sulla porta 8080...")
	http.ListenAndServe(":8080", nil)
	/*
		log.Println("Server in ascolto sulla porta 8080...")
		if err := http.ListenAndServe(":8080", nil); err != nil {
			log.Fatal("Errore nell'avvio del server:", err)
		}
	*/
}

func printConfig() {
	err := config.LoadMappings("mapping.json")
	if err != nil {
		log.Fatalf("Errore caricamento mapping: %v", err)
	}

	configID := "01" // esempio, cambia secondo la tua struttura

	// Costruisco il path alla cartella della config
	//configDir := fmt.Sprintf("configs/%s", configID)

	mapping, err := config.GetMapping(configID)
	if err != nil {
		log.Fatalf("Errore mapping: %v", err)
	}
	policy, err := config.LoadPolicy(mapping.ConfigPath)
	if err != nil {
		log.Fatalf("Errore caricamento policy: %v", err)
	}

	fmt.Println("Policy caricata correttamente:")
	fmt.Printf("Log file: %s\n", policy.LogFile)
	fmt.Printf("LogExpiration: %v\n", policy.LogUsageRules.LogExpiration)
	fmt.Printf("Max Access Count: %d\n", policy.LogUsageRules.MaxAccessCount)
	fmt.Printf("Allowed Locations: %v\n", policy.LogUsageRules.AllowedLocations)
	fmt.Printf("Algoritmi permessi in processing:\n")
	for _, alg := range policy.ProcessingRules.AllowedTechniques {
		fmt.Printf("- %s: %s\n", alg.TechniqueType, alg.Algorithm)
	}

	// Caricamento contatori
	counters, err := config.LoadCounters(configID)
	if err != nil {
		log.Fatalf("Errore caricamento contatori: %v", err)
	}

	fmt.Printf("Accessi log: %d\n", counters.LogAccessCount)
	fmt.Printf("Accessi output: %d\n", counters.OutputAccessCount)

	// Incremente test
	config.IncrementLogAccess(configID)
	config.IncrementOutputAccess(configID)

	// Salvataggio
	if err := config.SaveCounters(configID); err != nil {
		log.Fatalf("Errore salvataggio contatori: %v", err)
	}

	fmt.Println("Contatori aggiornati e salvati.")

	err = enforcement.ValidateLogAccess("agenas", "it", policy)
	if err != nil {
		fmt.Println("Accesso negato al log:", err)
	} else {
		fmt.Println("Accesso al log consentito")
	}

	err = enforcement.ValidateProcessing("agenas", "it", "HeuristicMiner", "AutomatedDiscovery", policy)
	if err != nil {
		fmt.Println("Accesso negato al log:", err)
	} else {
		fmt.Println("Accesso al log consentito")
	}
}
