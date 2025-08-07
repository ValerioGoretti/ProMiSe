package config

import (
	"encoding/json"
	"errors"
	"os"
	"sync"
)

type Mapping struct {
	LogFile         string              `json:"log_file"`
	ConfigPath      string              `json:"config_path"`
	DataPath        string              `json:"data_path"`
	AuthorizedUsers map[string][]string `json:"authorized_users"`
	Owner           string              `json:"owner"`
	DedupKey        string              `json:"dedup_key"`
}

var (
	mappings map[string]Mapping
	mutex    sync.RWMutex
)

// LoadMappings carica il mapping all'avvio dell'app
func LoadMappings(path string) error {
	mutex.Lock()
	defer mutex.Unlock()

	file, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var result map[string]Mapping
	err = json.Unmarshal(file, &result)
	if err != nil {
		return err
	}

	mappings = result
	return nil
}

// GetMapping restituisce la configurazione per un config_id
func GetMapping(configID string) (Mapping, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	if m, ok := mappings[configID]; ok {
		return m, nil
	}
	return Mapping{}, errors.New("config ID non trovato nel mapping")
}
