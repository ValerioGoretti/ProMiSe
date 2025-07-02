MAIN_GO_TEMPLATE = """
// main.go - Trusted Application for Policy Enforcement
package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type RequestPayload struct {
	LogID     string `json:"logID"`
	User      string `json:"user"`
	Location  string `json:"location"`
	Operation string `json:"operation"`
	Algorithm string `json:"algorithm,omitempty"`
}

type PolicyConfig struct {
	LogFile        string                 `json:"log_file"`
	LogUsageRules  map[string]interface{} `json:"logUsageRules"`
	OutputRules    map[string]interface{} `json:"outputRules"`
	ProcessingRules map[string]interface{} `json:"processingRules"`
}

type AccessState struct {
	AccessCount   int  `json:"accessCount"`
	Filtered      bool `json:"filtered"`
	LogDeleted    bool `json:"logDeleted"`
	OutputDeleted bool `json:"outputDeleted"`
}

func main() {
	fmt.Println("[TA] Starting Trusted Application for Policy Enforcement...")
	http.HandleFunc("/get-log", handleGetLog)
	http.HandleFunc("/run-algorithm", handleRunAlgorithm)
	http.ListenAndServe(":8080", nil)
}

func handleGetLog(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}
	var req RequestPayload
	json.NewDecoder(r.Body).Decode(&req)
	dir := filepath.Join("logs", req.LogID)
	policy := loadPolicyConfig(dir)
	state := loadAccessState(dir)

	if !checkExpiration(policy.LogUsageRules["logExpiration"], &state, filepath.Join(dir, policy.LogFile), "log") {
		http.Error(w, "Log expired or deleted", 403)
		return
	}
	if !checkAccess(req.User, policy.LogUsageRules["accessControlRules"]) {
		http.Error(w, "Unauthorized user", 403)
		return
	}
	if !checkLocation(req.Location, policy.LogUsageRules["allowedLocations"]) {
		http.Error(w, "Unauthorized location", 403)
		return
	}
	if !checkAccessCount(&state, policy.LogUsageRules["maxAccessCount"]) {
		deleteFile(filepath.Join(dir, policy.LogFile))
		state.LogDeleted = true
		saveAccessState(dir, &state)
		http.Error(w, "Access count exceeded", 403)
		return
	}
	state.AccessCount++
	saveAccessState(dir, &state)
	logAudit(dir, req, "get-log", true)
	http.ServeFile(w, r, filepath.Join(dir, policy.LogFile))
}

func handleRunAlgorithm(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}
	var req RequestPayload
	json.NewDecoder(r.Body).Decode(&req)
	dir := filepath.Join("logs", req.LogID)
	policy := loadPolicyConfig(dir)
	state := loadAccessState(dir)

	if !checkExpiration(policy.ProcessingRules["outputExpiration"], &state, filepath.Join(dir, "output.txt"), "output") {
		http.Error(w, "Output expired or deleted", 403)
		return
	}
	if !checkAccess(req.User, policy.ProcessingRules["accessControlRules"]) {
		http.Error(w, "Unauthorized user", 403)
		return
	}
	if !checkLocation(req.Location, policy.OutputRules["allowedLocations"]) {
		http.Error(w, "Unauthorized location", 403)
		return
	}
	if !isAlgorithmAllowed(req.Algorithm, policy.ProcessingRules["allowedTechniques"]) {
		http.Error(w, "Algorithm not permitted", 403)
		return
	}
	logAudit(dir, req, "run-algorithm", true)
	fmt.Fprintf(w, "Algorithm %s executed successfully on log %s\n", req.Algorithm, req.LogID)
}

func loadPolicyConfig(dir string) PolicyConfig {
	file, _ := ioutil.ReadFile(filepath.Join(dir, "policy_config.json"))
	var config PolicyConfig
	json.Unmarshal(file, &config)
	return config
}

func loadAccessState(dir string) AccessState {
	file, _ := ioutil.ReadFile(filepath.Join(dir, "access_state.json"))
	var state AccessState
	json.Unmarshal(file, &state)
	return state
}

func saveAccessState(dir string, state *AccessState) {
	data, _ := json.MarshalIndent(state, "", "  ")
	ioutil.WriteFile(filepath.Join(dir, "access_state.json"), data, 0644)
}

func checkAccess(user string, allowed interface{}) bool {
	for _, u := range strings.Split(fmt.Sprint(allowed), ",") {
		if strings.TrimSpace(u) == user {
			return true
		}
	}
	return false
}

func checkLocation(loc string, allowed interface{}) bool {
	for _, l := range strings.Split(fmt.Sprint(allowed), ",") {
		if strings.TrimSpace(l) == loc {
			return true
		}
	}
	return false
}

func checkExpiration(val interface{}, state *AccessState, filepath string, what string) bool {
	if state.LogDeleted && what == "log" || state.OutputDeleted && what == "output" {
		return false
	}
	ts := fmt.Sprint(val)
	t, err := time.Parse(time.RFC3339, ts)
	if err != nil || time.Now().After(t) {
		deleteFile(filepath)
		if what == "log" {
			state.LogDeleted = true
		} else {
			state.OutputDeleted = true
		}
		return false
	}
	return true
}

func checkAccessCount(state *AccessState, max interface{}) bool {
	maxInt, _ := strconv.Atoi(fmt.Sprint(max))
	return state.AccessCount < maxInt
}

func deleteFile(path string) {
	os.Remove(path)
}

func logAudit(dir string, req RequestPayload, action string, result bool) {
	entry := fmt.Sprintf("%s | %s | user=%s | location=%s | result=%t\n",
		time.Now().Format(time.RFC3339), action, req.User, req.Location, result)
	f, _ := os.OpenFile(filepath.Join(dir, "audit.log"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	defer f.Close()
	f.WriteString(entry)
}

func isAlgorithmAllowed(algo string, list interface{}) bool {
	for _, a := range strings.Split(fmt.Sprint(list), ",") {
		if strings.TrimSpace(a) == algo {
			return true
		}
	}
	return false
}
"""
