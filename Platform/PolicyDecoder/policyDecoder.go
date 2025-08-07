package policydecoder

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
)

// Define a struct. This struct will bind all the RPC methods
type PolicyManager struct{}

// Arguments for sending policy
type PolicyArgs struct {
	Policy string
}

// Arguments for sending file content
type FileArgs struct {
	FilePath    string
	FileContent []byte
}

// StorePolicy stores the policy and requests the file content from the client
func (pm *PolicyManager) StorePolicy(args *PolicyArgs, reply *string) error {
	if args == nil {
		return errors.New("arguments cannot be nil")
	}

	// Print the policy JSON content
	fmt.Printf("Received policy JSON: %s\n", args.Policy)

	// Parse the policy JSON to extract the file path
	var policyData map[string]string
	err := json.Unmarshal([]byte(args.Policy), &policyData)
	if err != nil {
		return err
	}

	filePath, ok := policyData["fileName"]
	if !ok {
		return errors.New("filePath not found in policy")
	}

	// Store the policy (for simplicity, just print it)
	fmt.Printf("Storing policy for file %s: %s\n", filePath, args.Policy)

	// Request the file content from the client
	*reply = "SendFile"
	return nil
}

// StoreFile stores the file content received from the client
func (pm *PolicyManager) StoreFile(args *FileArgs, reply *string) error {
	if args == nil {
		return errors.New("arguments cannot be nil")
	}

	// Store the file content (for simplicity, just save it to a file)
	err := os.WriteFile(args.FilePath, args.FileContent, 0644)
	if err != nil {
		return err
	}

	fmt.Printf("Stored file %s\n", args.FilePath)
	*reply = "File stored successfully"
	return nil
}
