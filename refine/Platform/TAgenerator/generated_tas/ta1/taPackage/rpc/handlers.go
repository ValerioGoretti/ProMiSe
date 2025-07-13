// taPackage/rpc/handlers.go

package rpc

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"ta1/taPackage/config"
	"ta1/taPackage/enforcement"
)

type RequestPayload struct {
	UserID    string `json:"user_id"`
	ConfigID  string `json:"config_id"`
	Algorithm string `json:"algorithm,omitempty"`
	Technique string `json:"techniqueType,omitempty"`
	Location  string `json:"location"`
}

func HandleLogAccess(w http.ResponseWriter, r *http.Request) {
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

	_, err = config.LoadCounters(payload.ConfigID)
	if err != nil {
		http.Error(w, "Errore caricamento contatori", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento contatori")
		return
	}

	if err := enforcement.ValidateLogAccess(payload.UserID, payload.Location, policy); err != nil {
		http.Error(w, err.Error(), http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso log negato")
		return
	}

	if !config.CheckLogAccessLimit(payload.ConfigID, policy.LogUsageRules.MaxAccessCount) {
		http.Error(w, "Superato limite accessi log", http.StatusForbidden)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Superato limite accessi log")
		return
	}

	_ = config.IncrementLogAccess(payload.ConfigID)
	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso log consentito")

	response := map[string]string{
		"message": "Accesso log consentito",
		"logFile": mapping.LogFile,
	}
	json.NewEncoder(w).Encode(response)
}

func HandleProcessing(w http.ResponseWriter, r *http.Request) {
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

	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, fmt.Sprintf("Processing eseguito con algoritmo %s", payload.Algorithm))

	response := map[string]string{
		"message": fmt.Sprintf("Processing eseguito con algoritmo %s", payload.Algorithm),
	}
	json.NewEncoder(w).Encode(response)
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

	_, err = config.LoadCounters(payload.ConfigID)
	if err != nil {
		http.Error(w, "Errore caricamento contatori", http.StatusInternalServerError)
		_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Errore caricamento contatori")
		return
	}

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
	_ = config.WriteAuditLogFromRequest(payload.ConfigID, r, "Accesso output consentito")

	response := map[string]string{
		"message": "Accesso output consentito",
	}
	json.NewEncoder(w).Encode(response)
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
