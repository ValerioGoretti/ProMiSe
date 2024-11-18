package policymanager

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/rpc"
	"os"
	"path/filepath"
)

// Arguments to pass to the remote method
type PolicyArgs struct {
	Policy string
}

type FileArgs struct {
	FilePath    string
	FileContent []byte
}

// SendPolicy sends a policy to the RPC server and then sends the file content
func SendPolicy(folderName string) {
	fmt.Println("Sending Policy")
	client, err := rpc.Dial("tcp", "localhost:8080") // Connect to server at localhost:8080
	if err != nil {
		fmt.Println("Error connecting:", err)
		return
	}
	defer client.Close()

	wd, err := os.Getwd()
	if err != nil {
		fmt.Println("Errore nel recuperare la directory corrente:", err)
		return
	}

	policyFilePath := filepath.Join(wd, "InformationManager", "PolicyManager", "data", folderName, "policy.json")
	fmt.Println("Percorso completo al file:", policyFilePath)

	// Read the policy.json file
	policyContent, err := os.ReadFile(policyFilePath)
	if err != nil {
		fmt.Println("Error reading policy.json file:", err)
		return
	}

	// Prepare arguments
	policyArgs := PolicyArgs{Policy: string(policyContent)}

	var reply string

	// Call StorePolicy method on the server
	err = client.Call("PolicyManager.StorePolicy", policyArgs, &reply)
	if err != nil {
		fmt.Println("Error calling PolicyManager.StorePolicy:", err)
		return
	}

	if reply == "SendFile" {
		// Parse the policy JSON to extract the file path
		var policyData map[string]string
		err = json.Unmarshal(policyContent, &policyData)
		if err != nil {
			fmt.Println("Error parsing policy JSON:", err)
			return
		}

		fileName, ok := policyData["fileName"]
		filePath := filepath.Join(wd, "InformationManager", "PolicyManager", "data", folderName, fileName)
		if !ok {
			fmt.Println("filePath not found in policy")
			return
		}

		// Read the file content
		fileContent, err := ioutil.ReadFile(filePath)
		if err != nil {
			fmt.Println("Error reading file:", err)
			return
		}

		// Prepare file arguments
		fileArgs := FileArgs{FilePath: filePath, FileContent: fileContent}

		// Call StoreFile method on the server
		err = client.Call("PolicyManager.StoreFile", fileArgs, &reply)
		if err != nil {
			fmt.Println("Error calling PolicyManager.StoreFile:", err)
			return
		}

		fmt.Println(reply)
	}
}
