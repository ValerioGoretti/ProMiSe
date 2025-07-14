// taPackage/rpc/handlers.go

package rpc

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"ta1/taPackage/test"

	//"github.com/edgelesssys/ego/ecrypto"
	"github.com/edgelesssys/ego/enclave"
	"net/http"
	"os"
	"path/filepath"
	"ta1/taPackage/algorithms"
	"ta1/taPackage/config"
	"ta1/taPackage/enforcement"
	"time"
)

type RequestPayload struct {
	UserID     string `json:"user_id"`
	ConfigID   string `json:"config_id"`
	Algorithm  string `json:"algorithm,omitempty"`
	Technique  string `json:"techniqueType,omitempty"`
	Location   string `json:"location"`
	OutputFile string `json:"outputFile,omitempty"`
}

func HandleLogAccess(w http.ResponseWriter, r *http.Request) {
	fmt.Println("[DEBUG] Chiamata ricevuta")

	if r.Method != http.MethodPost {
		fmt.Println("[DEBUG] Metodo non consentito")
		http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
		return
	}

	fmt.Println("[DEBUG] Metodo POST ricevuto")

	var payload RequestPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		fmt.Println("[DEBUG] Payload non valido:", err)
		http.Error(w, "Payload non valido", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Payload non valido")
		return
	}

	fmt.Println("[DEBUG] Payload decodificato")

	mapping, err := config.GetMapping(payload.ConfigID)
	if err != nil {
		fmt.Println("[DEBUG] invalid config ID:", err)
		http.Error(w, "Invalid config ID", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Invalid config ID")
		return
	}

	fmt.Println("[DEBUG] Mapping ottenuto")

	policy, err := config.LoadPolicy(mapping.ConfigPath)
	if err != nil {
		fmt.Println("[DEBUG] Errore caricamento policy:", err)
		http.Error(w, "Errore caricamento policy", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento policy")
		return
	}

	fmt.Println("[DEBUG] Policy caricata")

	_, err = config.LoadCounters(payload.ConfigID)
	if err != nil {
		fmt.Println("[DEBUG] Errore caricamento contatori:", err)
		http.Error(w, "Errore caricamento contatori", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento contatori")
		return
	}

	fmt.Println("[DEBUG] contatori caricati")

	if err := enforcement.ValidateLogAccess(payload.UserID, payload.Location, policy); err != nil {
		http.Error(w, err.Error(), http.StatusForbidden)
		fmt.Println("[DEBUG] Accesso log negato:", err)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso log negato")
		return
	}

	fmt.Println("[DEBUG] Accesso log consentito")

	if !config.CheckLogAccessLimit(payload.ConfigID, policy.LogUsageRules.MaxAccessCount) {
		fmt.Println("[DEBUG] Superato limite accessi log")
		http.Error(w, "Superato limite accessi log", http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Superato limite accessi log")
		return
	}

	fmt.Println("[DEBUG]  Limite accessi log non superato")

	// Incrementa accessi log
	if err := config.IncrementLogAccess(payload.ConfigID); err != nil {
		fmt.Println("[DEBUG] Errore incremento accessi log:", err)
		http.Error(w, "Errore incremento accessi log", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore incremento accessi log")
		return
	}

	fmt.Println("[DEBUG]  Accessi log incrementati")

	// Ottieni path completo file log
	logFilePath := filepath.Join(mapping.DataPath, policy.LogFile)

	fmt.Println("[DEBUG]  Path file log:", logFilePath)

	// Carica e filtra il log XES in base alle regole della policy
	filteredLog, err := config.LoadAndFilterXesLog(logFilePath, policy.LogUsageRules)
	if err != nil {
		fmt.Println("[DEBUG] Errore caricamento o filtro log:", err)
		http.Error(w, "Errore caricamento o filtro log", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento o filtro log")
		return
	}

	fmt.Println("[DEBUG]  Log filtrato ottenuto")

	// Scrivi audit log esito positivo
	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso log consentito - log filtrato restituito")

	fmt.Println("[DEBUG] Audit log scritto con successo")

	// Ritorna il log filtrato come JSON
	w.Header().Set("Content-Type", "application/json")
	// extrct string from filteredLog
	filteredLogString := config.ExtractFilteredLogString(filteredLog)
	filteredByteArray := []byte(filteredLogString)
	filteredByteArrayhash := sha256.Sum256(filteredByteArray)
	teeSignedLog, err := enclave.GetRemoteReport(filteredByteArrayhash[:])
	if err != nil {
		fmt.Println("[DEBUG] Errore ottenimento remote report:", err)
		http.Error(w, "Errore ottenimento remote report", http.StatusInternalServerError)
		return
	}
	encodedTeeSignedLog := base64.StdEncoding.EncodeToString(teeSignedLog)

	//Rispondi alla richiesta con il log filtrato e encodedTeeSignedLog
	response := map[string]string{
		"filtered_log":   filteredLogString,
		"tee_signed_log": encodedTeeSignedLog,
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Errore serializzazione log", http.StatusInternalServerError)
		return
	}

}

func HandleProcessing(w http.ResponseWriter, r *http.Request) {
	go test.PrintRamUsage()
	if r.Method != http.MethodPost {
		http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
		return
	}

	var payload RequestPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Payload non valido", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Payload non valido")
		return
	}

	mapping, err := config.GetMapping(payload.ConfigID)
	if err != nil {
		http.Error(w, "Invalid config ID", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Invalid config ID")
		return
	}

	policy, err := config.LoadPolicy(mapping.ConfigPath)
	if err != nil {
		http.Error(w, "Errore caricamento policy", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento policy")
		return
	}

	if err := enforcement.ValidateProcessing(payload.UserID, payload.Location, payload.Algorithm, payload.Technique, policy); err != nil {
		http.Error(w, err.Error(), http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso processing negato")
		return
	}

	// Costruisci i path input/output
	inputPath := filepath.Join(mapping.DataPath, policy.LogFile)

	// Timestamp per filename univoco
	timestamp := fmt.Sprintf("%d", time.Now().Unix())

	// Path output: output/<configID>/<algoritmo>/model_<timestamp>.json
	outputDir := filepath.Join("outputs", payload.ConfigID, payload.Algorithm)
	if err := os.MkdirAll(outputDir, os.ModePerm); err != nil {
		http.Error(w, "Errore creazione cartella output", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore creazione cartella output")
		return
	}
	outputFilename := fmt.Sprintf("model_%s.json", timestamp)
	outputPath := filepath.Join(outputDir, outputFilename)

	// Solo se serve, crea la matrice eventi
	var eventMatrix [][]string
	if payload.Algorithm == "HeuristicMiner" {
		//filteredLog, err := config.LoadAndFilterXesLog(inputPath, policy.LogUsageRules)
		filteredLog, err := config.LoadFullXesLog(inputPath)
		if err != nil {
			http.Error(w, "Errore filtro log: "+err.Error(), http.StatusInternalServerError)
			return
		}
		for _, trace := range filteredLog.Traces {
			var eventSeq []string
			for _, event := range trace.Events {
				name := config.GetAttributeValue(event.Attributes, "concept:name")
				if name != "" {
					eventSeq = append(eventSeq, name)
				}
			}
			if len(eventSeq) > 0 {
				eventMatrix = append(eventMatrix, eventSeq)
			}
		}
	}

	// Chiamata centralizzata
	outputF, err := algorithms.RunAlgorithm(payload.Algorithm, inputPath, outputPath, eventMatrix, payload.ConfigID)
	if err != nil {
		http.Error(w, "Errore esecuzione algoritmo: "+err.Error(), http.StatusInternalServerError)
		return
	}

	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, fmt.Sprintf("Processing eseguito con algoritmo %s", payload.Algorithm))

	//Calculate output Report
	// Leggi e restituisci il contenuto del file
	outputFilePath := outputDir + "/" + outputF
	fmt.Println(outputFilePath)

	data, err := os.ReadFile(outputFilePath)
	if err != nil {
		http.Error(w, "Errore lettura file di output", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore lettura file di output")
		return
	}

	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Output restituito: "+filepath.Base(outputFilePath))

	filteredByteArrayhash := sha256.Sum256(data)
	teeSignedLog, err := enclave.GetRemoteReport(filteredByteArrayhash[:])
	if err != nil {
		fmt.Println("[DEBUG] Errore ottenimento remote report:", err)
		http.Error(w, "Errore ottenimento remote report", http.StatusInternalServerError)
		return
	}
	encodedTeeSignedOutput := base64.StdEncoding.EncodeToString(teeSignedLog)
	//encodedOutput := base64.StdEncoding.EncodeToString(data)

	//Rispondi alla richiesta con il file di ouput e encodedTeeSignedOutput
	response := map[string]string{
		"message":          fmt.Sprintf("Processing eseguito con algoritmo %s", payload.Algorithm),
		"output_signature": encodedTeeSignedOutput,
	}
	test.STOPMONITORING = true

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Errore serializzazione log", http.StatusInternalServerError)
		return
	}
}

func HandleOutputAccess(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
		return
	}

	var payload RequestPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Payload non valido", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Payload non valido")
		return
	}

	mapping, err := config.GetMapping(payload.ConfigID)
	if err != nil {
		http.Error(w, "Invalid config ID", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Invalid config ID")
		return
	}

	policy, err := config.LoadPolicy(mapping.ConfigPath)
	if err != nil {
		http.Error(w, "Errore caricamento policy", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento policy")
		return
	}

	// Validazione accesso
	if err := enforcement.ValidateOutputAccess(payload.UserID, payload.Location, policy); err != nil {
		http.Error(w, err.Error(), http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso output negato")
		return
	}

	if !config.CheckOutputAccessLimit(payload.ConfigID, policy.OutputRules.MaxAccessCount) {
		http.Error(w, "Superato limite accessi output", http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Superato limite accessi output")
		return
	}

	_ = config.IncrementOutputAccess(payload.ConfigID)

	// Path alla cartella output dell’algoritmo
	outputDir := filepath.Join("outputs", payload.ConfigID, payload.Algorithm)

	var outputFilePath string
	if payload.OutputFile != "" {
		outputFilePath = filepath.Join(outputDir, payload.OutputFile)
	} else {
		// Recupera l’ultimo file creato
		files, err := os.ReadDir(outputDir)
		if err != nil || len(files) == 0 {
			http.Error(w, "Nessun file di output disponibile", http.StatusNotFound)
			return
		}

		var latest os.DirEntry
		var latestModTime time.Time
		for _, file := range files {
			info, err := file.Info()
			if err == nil && !info.IsDir() && info.ModTime().After(latestModTime) {
				latest = file
				latestModTime = info.ModTime()
			}
		}

		if latest == nil {
			http.Error(w, "Nessun file di output trovato", http.StatusNotFound)
			return
		}

		outputFilePath = filepath.Join(outputDir, latest.Name())
	}

	// Leggi e restituisci il contenuto del file
	data, err := os.ReadFile(outputFilePath)
	if err != nil {
		http.Error(w, "Errore lettura file di output", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore lettura file di output")
		return
	}

	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Output restituito: "+filepath.Base(outputFilePath))

	filteredByteArrayhash := sha256.Sum256(data)
	teeSignedLog, err := enclave.GetRemoteReport(filteredByteArrayhash[:])
	if err != nil {
		fmt.Println("[DEBUG] Errore ottenimento remote report:", err)
		http.Error(w, "Errore ottenimento remote report", http.StatusInternalServerError)
		return
	}
	encodedTeeSignedOutput := base64.StdEncoding.EncodeToString(teeSignedLog)
	//encodedOutput := base64.StdEncoding.EncodeToString(data)

	//Rispondi alla richiesta con il file di ouput e encodedTeeSignedOutput
	response := map[string]string{
		"output_file":      string(data),
		"output_signature": encodedTeeSignedOutput,
	}

	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Errore serializzazione log", http.StatusInternalServerError)
		return
	}

	//w.Header().Set("Content-Disposition", "attachment; filename="+filepath.Base(outputFilePath))
	//w.Header().Set("Content-Type", "application/octet-stream")
	//w.Write(data)
}

func HandlePolicyInfo(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
		return
	}

	configID := r.URL.Query().Get("config_id")
	if configID == "" {
		http.Error(w, "Config ID mancante", http.StatusBadRequest)
		return
	}

	mapping, err := config.GetMapping(configID)
	if err != nil {
		http.Error(w, "Mapping non trovato", http.StatusBadRequest)
		_ = config.WriteAuditLogFromRequest(configID, r, "Mapping non trovato")
		return
	}

	policy, err := config.LoadPolicy(mapping.ConfigPath)
	if err != nil {
		http.Error(w, "Errore caricamento policy", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(configID, r, "Errore caricamento policy")
		return
	}

	_ = config.WriteAuditLogFromRequest(configID, r, "Policy restituita")
	json.NewEncoder(w).Encode(policy)
}

func HandleMonitoring(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Metodo non consentito", http.StatusMethodNotAllowed)
		return
	}

	configID := r.URL.Query().Get("config_id")
	if configID == "" {
		http.Error(w, "Config ID mancante", http.StatusBadRequest)
		return
	}

	auditPath := filepath.Join("configs", configID, "audit.txt")
	data, err := os.ReadFile(auditPath)
	if err != nil {
		http.Error(w, "Errore lettura file audit", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Write(data)
}

func signResult(result []byte) (report []byte) {
	report, err := enclave.GetRemoteReport(result[:])
	if err != nil {
		fmt.Println("[DEBUG] Errore ottenimento remote report:", err)
		return
	}
	return report
}
