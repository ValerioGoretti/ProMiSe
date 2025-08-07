package enforcement

import (
	"errors"
	"strings"
	"ta1/taPackage/config"
	"time"
)

// Verifica se l'utente è autorizzato a una certa operazione (logUsage, processing, output)
func IsUserAuthorized(user string, authorizedUsers []string) bool {
	for _, u := range authorizedUsers {
		if strings.EqualFold(u, user) {
			return true
		}
	}
	return false
}

// Verifica se una location è consentita
func IsLocationAllowed(location string, allowed []string) bool {
	for _, loc := range allowed {
		if strings.EqualFold(loc, location) {
			return true
		}
	}
	return false
}

// Verifica se l’algoritmo richiesto è consentito per il tipo specificato
func IsAlgorithmAllowed(requestedAlg string, techniqueType string, allowed []config.ProcessingRuleAlgorithm) bool {
	for _, alg := range allowed {
		if strings.EqualFold(alg.Algorithm, requestedAlg) && strings.EqualFold(alg.TechniqueType, techniqueType) {
			return true
		}
	}
	return false
}

// Verifica se la data corrente è prima della scadenza
func IsValidTime(now time.Time, expiration time.Time) bool {
	return now.Before(expiration)
}

// Validazione completa accesso al log
func ValidateLogAccess(user, location string, policy *config.Policy) error {
	if !IsUserAuthorized(user, policy.LogUsageRules.AccessControlRules) {
		return errors.New("utente non autorizzato al log")
	}
	if !IsLocationAllowed(location, policy.LogUsageRules.AllowedLocations) {
		return errors.New("location non autorizzata al log")
	}
	if !IsValidTime(time.Now(), policy.LogUsageRules.LogExpiration) {
		return errors.New("data oltre la scadenza del log")
	}
	return nil
}

// Validazione completa accesso all’output
func ValidateOutputAccess(user, location string, policy *config.Policy) error {
	if !IsUserAuthorized(user, policy.OutputRules.AccessControlRules) {
		return errors.New("utente non autorizzato all’output")
	}
	if !IsLocationAllowed(location, policy.OutputRules.AllowedLocations) {
		return errors.New("location non autorizzata all’output")
	}
	if !IsValidTime(time.Now(), policy.OutputRules.OutputExpiration) {
		return errors.New("data oltre la scadenza dell’output")
	}
	return nil
}

// Validazione algoritmo per il processing
func ValidateProcessing(user, location, algorithm, techniqueType string, policy *config.Policy) error {
	if !IsUserAuthorized(user, policy.ProcessingRules.AccessControlRules) {
		return errors.New("utente non autorizzato al processamento")
	}
	if !IsLocationAllowed(location, policy.ProcessingRules.AllowedLocations) {
		return errors.New("location non autorizzata al processamento")
	}
	if !IsAlgorithmAllowed(algorithm, techniqueType, policy.ProcessingRules.AllowedTechniques) {
		return errors.New("algoritmo non autorizzato")
	}
	return nil
}
