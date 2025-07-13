// taPackage/config/policy_loader.go

package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// Definizione strutture dati per il parsing della policy

type TimeRange struct {
	EventAttribute string    `json:"eventAttribute"`
	StartDate      time.Time `json:"startDate"`
	EndDate        time.Time `json:"endDate"`
}

type AttributeExclusionRules struct {
	Scope              string   `json:"scope"`
	EventAttribute     string   `json:"eventAttribute"`
	ExcludedAttributes []string `json:"excludedAttributes"`
}

type SemanticLogConstraints struct {
	EventAttribute string   `json:"eventAttribute"`
	MustInclude    []string `json:"mustInclude"`
	MustExclude    []string `json:"mustExclude"`
}

type LogUsageRules struct {
	LogExpiration           time.Time               `json:"logExpiration"`
	MaxAccessCount          int                     `json:"maxAccessCount"`
	AllowedLocations        []string                `json:"allowedLocations"`
	AccessControlRules      []string                `json:"accessControlRules"`
	AttributeExclusionRules AttributeExclusionRules `json:"attributeExclusionRules"`
	AllowedTimeRange        TimeRange               `json:"allowedTimeRange"`
	SemanticLogConstraints  SemanticLogConstraints  `json:"semanticLogConstraints"`
}

type OutputRules struct {
	OutputExpiration   time.Time `json:"outputExpiration"`
	MaxAccessCount     int       `json:"maxAccessCount"`
	AllowedLocations   []string  `json:"allowedLocations"`
	AccessControlRules []string  `json:"accessControlRules"`
	AllowedTimeRange   TimeRange `json:"allowedTimeRange"`
}

type ProcessingRuleAlgorithm struct {
	TechniqueType string `json:"techniqueType"`
	Algorithm     string `json:"algorithm"`
}

type ProcessingRules struct {
	AccessControlRules []string                  `json:"accessControlRules"`
	AllowedTechniques  []ProcessingRuleAlgorithm `json:"allowedTechniques"`
	AllowedLocations   []string                  `json:"allowedLocations"`
}

type Policy struct {
	LogFile         string          `json:"log_file"`
	LogUsageRules   LogUsageRules   `json:"logUsageRules"`
	OutputRules     OutputRules     `json:"outputRules"`
	ProcessingRules ProcessingRules `json:"processingRules"`
	LastUpdated     time.Time       `json:"last_updated"`
}

// Custom UnmarshalJSON per gestire LastUpdated con formati diversi
func (p *Policy) UnmarshalJSON(data []byte) error {
	type Alias Policy
	aux := &struct {
		LastUpdated string `json:"last_updated"`
		*Alias
	}{
		Alias: (*Alias)(p),
	}

	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}

	// Provo parsing RFC3339 con offset
	t, err := time.Parse(time.RFC3339, aux.LastUpdated)
	if err != nil {
		// Provo formato senza offset (es. "2006-01-02T15:04:05")
		t, err = time.Parse("2006-01-02T15:04:05", aux.LastUpdated)
		if err != nil {
			return fmt.Errorf("cannot parse last_updated: %w", err)
		}
	}
	p.LastUpdated = t
	return nil
}

// Wrapper per eventuali più policy nel file JSON
type Policies struct {
	Policies []Policy `json:"policies"`
}

// LoadPolicy carica e deserializza la policy da configs/<config_id>/policy_config.json
func LoadPolicy(configDir string) (*Policy, error) {
	policyPath := filepath.Join(configDir, "policy_config.json")

	file, err := os.ReadFile(policyPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read policy_config.json: %w", err)
	}

	var policies Policies
	if err := json.Unmarshal(file, &policies); err != nil {
		return nil, fmt.Errorf("failed to unmarshal policy json: %w", err)
	}

	if len(policies.Policies) == 0 {
		return nil, fmt.Errorf("no policies found in file")
	}

	// Prendiamo la prima policy (modificabile in futuro)
	return &policies.Policies[0], nil
}
