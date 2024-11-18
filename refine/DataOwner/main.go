package main

import (
	"fmt"
	policymanager "main/InformationManager/PolicyManager"
)

func logo() {
	fmt.Println("=====================================================")
	fmt.Println("")
	fmt.Println("Data Owner")
	fmt.Println("")
	fmt.Println("=====================================================")
}

func menu() {
	fmt.Println("1. Execute PM operation")
	fmt.Println("2. Close")
}

func main() {

	menu()
	var input int
	fmt.Print("Enter a number: ")
	fmt.Scanln(&input)

	for {
		switch input {
		case 1:
			var folderName string
			fmt.Print("Enter the name of the folder containing the policy.json file: ")
			fmt.Scanln(&folderName)

			if folderName == "" {
				fmt.Println("Error: folderName parameter is required")
				return
			}

			// Call SendPolicy method from PolicyManager
			policymanager.SendPolicy(folderName)
		case 2:
			break
		default:
			fmt.Println("You entered a number other than one, two")
		}

		menu()
		var input int
		fmt.Print("Enter a number: ")
		fmt.Scanln(&input)
	}

}

/*
func main() {
	// Define a command-line flag for the folder name
	folderName := flag.String("folderName", "", "The name of the folder containing the policy.json file")
	flag.Parse()

	if *folderName == "" {
		fmt.Println("Error: folderName parameter is required")
		return
	}

	// Call SendPolicy method from PolicyManager
	policymanager.SendPolicy(*folderName)
}
*/
