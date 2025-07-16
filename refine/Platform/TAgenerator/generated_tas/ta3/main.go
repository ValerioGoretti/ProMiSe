package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"ta1/taPackage/config"
	"ta1/taPackage/rpc"
	"ta1/taPackage/test"
)

func main() {
	teeStr := flag.String("tee", "true", "Execution mode: true or false")
	flag.Parse()

	// Converte la stringa in booleano
	parsedTEE, errFlag := strconv.ParseBool(*teeStr)
	if errFlag != nil {
		fmt.Println("Errore: il valore di --tee deve essere 'true' o 'false'")
		os.Exit(1)
	}
	test.TEE = parsedTEE

	fmt.Println("TEE mode:", test.TEE)

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
