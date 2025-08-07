package main

import (
	"log"
	"net/http"
	"ta2/taPackage/config"
	"ta2/taPackage/rpc"
)

func main() {
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
	errList := http.ListenAndServe(":8080", nil)
	if errList != nil {
		log.Fatalf("Errore nell'avvio del server: %v", errList)
	}
}

// quando inizo la call go test.PrintRamUsage
//
