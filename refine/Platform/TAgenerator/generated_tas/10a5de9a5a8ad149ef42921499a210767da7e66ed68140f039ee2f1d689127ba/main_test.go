package main

import (
	"fmt"
	"refine/ta1/taPackage/config"
)

func main() {
	err := config.LoadMappings("mapping.json")
	if err != nil {
		panic(err)
	}

	m, err := config.GetMapping("01")
	if err != nil {
		panic(err)
	}

	fmt.Println("Config Path:", m.ConfigPath)
	fmt.Println("Log File:", m.LogFile)
	fmt.Println("Utenti autorizzati al log:", m.AuthorizedUsers["logUsage"])
}
