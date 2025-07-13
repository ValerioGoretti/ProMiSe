// taPackage/config/counter.go

package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

type Counters struct {
	LogAccessCount    int `json:"logAccessCount"`
	OutputAccessCount int `json:"outputAccessCount"`
}

var (
	countersMap  = make(map[string]*Counters)
	counterMutex sync.RWMutex
)

// Percorso del file counters per una determinata config
func getCounterPath(configID string) string {
	return filepath.Join("configs", configID, "counters.json")
}

// Carica i counters da file
func LoadCounters(configID string) (*Counters, error) {
	path := getCounterPath(configID)
	file, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read counters for %s: %w", configID, err)
	}

	var c Counters
	err = json.Unmarshal(file, &c)
	if err != nil {
		return nil, fmt.Errorf("failed to parse counters for %s: %w", configID, err)
	}

	counterMutex.Lock()
	countersMap[configID] = &c
	counterMutex.Unlock()

	return &c, nil
}

// SaveCounters salva un oggetto Counters già protetto da lock
func SaveCounters(configID string, c *Counters) error {
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	path := getCounterPath(configID)
	return os.WriteFile(path, data, 0644)
}

func IncrementLogAccess(configID string) error {
	counterMutex.Lock()
	defer counterMutex.Unlock()

	c, ok := countersMap[configID]
	if !ok {
		loaded, err := LoadCounters(configID)
		if err != nil {
			return err
		}
		c = loaded
		countersMap[configID] = c
	}

	c.LogAccessCount++
	err := SaveCounters(configID, c)
	if err != nil {
		return err
	}

	return WriteAuditLog(configID, fmt.Sprintf("Increment LogAccessCount: %d", c.LogAccessCount))
}

func IncrementOutputAccess(configID string) error {
	counterMutex.Lock()
	defer counterMutex.Unlock()

	c, ok := countersMap[configID]
	if !ok {
		loaded, err := LoadCounters(configID)
		if err != nil {
			return err
		}
		c = loaded
		countersMap[configID] = c
	}

	c.OutputAccessCount++
	err := SaveCounters(configID, c)
	if err != nil {
		return err
	}

	return WriteAuditLog(configID, fmt.Sprintf("Increment OutputAccessCount: %d", c.OutputAccessCount))
}

/*
	func CheckLogAccessLimit(configID string, max int) bool {
		counterMutex.RLock()
		defer counterMutex.RUnlock()
		c, ok := countersMap[configID]
		if !ok {
			return false
		}
		return c.LogAccessCount < max
	}

	func CheckOutputAccessLimit(configID string, max int) bool {
		counterMutex.RLock()
		defer counterMutex.RUnlock()
		c, ok := countersMap[configID]
		if !ok {
			return false
		}
		return c.OutputAccessCount < max
	}
*/
func ReloadCounters(configID string) error {
	path := getCounterPath(configID)
	file, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("failed to read counters for %s: %w", configID, err)
	}

	var c Counters
	err = json.Unmarshal(file, &c)
	if err != nil {
		return fmt.Errorf("failed to parse counters for %s: %w", configID, err)
	}

	counterMutex.Lock()
	countersMap[configID] = &c
	counterMutex.Unlock()

	return nil
}

func CheckLogAccessLimit(configID string, max int) bool {
	_ = ReloadCounters(configID) // ricarica da file sempre
	counterMutex.RLock()
	defer counterMutex.RUnlock()
	c, ok := countersMap[configID]
	if !ok {
		return false
	}
	return c.LogAccessCount < max
}

func CheckOutputAccessLimit(configID string, max int) bool {
	_ = ReloadCounters(configID) // ricarica da file sempre
	counterMutex.RLock()
	defer counterMutex.RUnlock()
	c, ok := countersMap[configID]
	if !ok {
		return false
	}
	return c.OutputAccessCount < max
}
