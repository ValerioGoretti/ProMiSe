package main

import (
	"fmt"
	"log"
	"net/http"
	"refine/ta1/taPackage/config"
	//"./taPackage/rpc"
)

func testConfigLoad() {
	// Caricamento mapping.json
	err := config.LoadMappings("mapping.json")
	if err != nil {
		log.Fatalf("Errore nel caricamento del mapping: %v", err)
	}

	/*
		// Avvio server HTTP
		http.HandleFunc("/log", rpc.HandleLogAccess)
		http.HandleFunc("/process", rpc.HandleProcessing)
		http.HandleFunc("/output", rpc.HandleOutputAccess)
		http.HandleFunc("/policy", rpc.HandlePolicyInfo)
	*/
	fmt.Println("Trusted App attiva su http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
