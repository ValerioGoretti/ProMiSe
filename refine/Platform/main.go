package main

import (
	"fmt"
	"main/PolicyDecoder"
	"net"
	"net/rpc"
)

func main() {
	// Create an instance of the service PolicyManager
	pm := new(policydecoder.PolicyManager)

	// Register the RPC service
	err := rpc.Register(pm)
	if err != nil {
		fmt.Println("Error registering PolicyManager:", err)
		return
	}

	// Start the server
	listener, err := net.Listen("tcp", ":8080") // Listen on port 8080
	if err != nil {
		fmt.Println("Error starting server:", err)
		return
	}
	defer listener.Close()

	fmt.Println("Server is listening on port 8080...")
	rpc.Accept(listener) // Accept RPC connections
}
