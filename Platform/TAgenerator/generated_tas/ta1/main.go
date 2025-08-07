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
	parsedTEE, errFlag := strconv.ParseBool(*teeStr)\n\tif errFlag != nil {\n\t\tfmt.Println(\"Errore: il valore di --tee deve essere 'true' o 'false'\")\n\t\tos.Exit(1)\n\t}\n\ttest.TEE = parsedTEE\n\n\tfmt.Println(\"TEE mode:\", test.TEE)\n\n\terr := config.LoadMappings(\"mapping.json\")\n\tif err != nil {\n\t\tlog.Fatal(\"Errore mapping:\", err)\n\t}\n\n\thttp.HandleFunc(\"/log\", rpc.HandleLogAccess)\n\thttp.HandleFunc(\"/process\", rpc.HandleProcessing)\n\thttp.HandleFunc(\"/output\", rpc.HandleOutputAccess)\n\thttp.HandleFunc(\"/policy\", rpc.HandlePolicyInfo)\n\thttp.HandleFunc(\"/monitoring\", rpc.HandleMonitoring)\n\n\tlog.Println(\"Server in ascolto sulla porta 8080...")
		errList := http.ListenAndServe(":8080", nil)
		if errList != nil{
		log.Fatalf("Errore nell'avvio del server: %v", errList)
	}
	}

	// quando inizo la call go test.PrintRamUsage
	//
