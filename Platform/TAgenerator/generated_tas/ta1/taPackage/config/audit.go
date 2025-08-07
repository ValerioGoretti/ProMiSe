package config

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

func getAuditPath(configID string) string {
	return filepath.Join("configs", configID, "audit.txt")
}

func WriteAuditLog(configID string, message string) error {
	path := getAuditPath(configID)
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("errore apertura audit log: %w", err)
	}
	defer f.Close()

	timestamp := time.Now().Format("2006-01-02 15:04:05")
	entry := fmt.Sprintf("[%s] %s\n", timestamp, message)

	if _, err := f.WriteString(entry); err != nil {
		return fmt.Errorf("errore scrittura audit log: %w", err)
	}

	return nil
}

func WriteAuditLogFromRequest(configID string, r *http.Request, result string) error {
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	method := r.Method
	endpoint := r.URL.Path
	ip := r.RemoteAddr
	message := fmt.Sprintf("[%s] %s %s - IP: %s - Esito: %s\n", timestamp, method, endpoint, ip, result)

	auditPath := filepath.Join("configs", configID, "audit.txt")
	f, err := os.OpenFile(auditPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("errore apertura audit file: %w", err)
	}
	defer f.Close()

	if _, err := f.WriteString(message); err != nil {
		return fmt.Errorf("errore scrittura audit file: %w", err)
	}

	return nil
}
