package main

import (
	"log"
	"net/http"
	"ta1/taPackage/config"
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

}

// quando inizo la call go test.PrintRamUsage
//
