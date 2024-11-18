package main

import (
	"ProcessMiningPlatform/PolicyDecoder/policydecoder"
	"log"
	"net"
	"net/rpc"
)

func main() {
	pd := &policydecoder.PolicyDecoder{}
	err := rpc.Register(pd)
	if err != nil {
		log.Fatalf("Errore durante la registrazione del server RPC: %v", err)
	}

	listener, err := net.Listen("tcp", ":1234")
	if err != nil {
		log.Fatalf("Errore durante l'ascolto: %v", err)
	}
	defer listener.Close()

	log.Println("Server RPC in ascolto sulla porta 1234...")
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Errore durante l'accettazione della connessione: %v", err)
			continue
		}
		go rpc.ServeConn(conn)
	}
}
