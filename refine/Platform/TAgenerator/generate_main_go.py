import os
from pathlib import Path

def generate_go_mod(ta_hash: str):
    ta_dir = Path("generated_tas") / ta_hash
    go_mod_path = ta_dir / "go.mod"

    if go_mod_path.exists():
        print(f"[info] go.mod già presente per {ta_hash}")
        return

    content = """module main

go 1.21
"""
    go_mod_path.write_text(content)
    print(f"[build] go.mod creato in {go_mod_path}")


def generate_main_header():
    return """package main

import (
    "encoding/json"
    "encoding/xml"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "time"
)

type Request struct {
    TaHash     string `json:"ta_hash"`
    ConfigID   string `json:"config_id"`
    User       string `json:"user"`
    Location   string `json:"location"`
    Algorithm  string `json:"algorithm,omitempty"`
}

type XES struct {
    XMLName xml.Name `xml:"log"`
    Traces  []Trace  `xml:"trace"`
}

type Trace struct {
    Events []Event `xml:"event"`
}

type Event struct {
    Strings []AttributeString `xml:"string"`
    Dates   []AttributeDate   `xml:"date"`
}

type AttributeString struct {
    Key   string `xml:"key,attr"`
    Value string `xml:"value,attr"`
}

type AttributeDate struct {
    Key   string    `xml:"key,attr"`
    Value time.Time `xml:"value,attr"`
}

func main() {
    http.HandleFunc("/access_log", handleAccessLog)
    http.HandleFunc("/process", handleProcess)
    http.HandleFunc("/get_output", handleGetOutput)
    http.HandleFunc("/policy", handleGetPolicy)

    fmt.Println("Trusted App started on port 8080")
    http.ListenAndServe(":8080", nil)
}
"""


def generate_access_log_handler():
    return """func handleAccessLog(w http.ResponseWriter, r *http.Request) {
    if r.Method != "POST" {
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    base := filepath.Join("generated_tas", req.TaHash)
    policyPath := filepath.Join(base, "configs", req.ConfigID, "policy_config.json")
    dataPath := filepath.Join(base, "data", req.ConfigID)

    policyBytes, err := os.ReadFile(policyPath)
    if err != nil {
        http.Error(w, "Policy not found", http.StatusNotFound)
        return
    }

    var policy map[string]interface{}
    if err := json.Unmarshal(policyBytes, &policy); err != nil {
        http.Error(w, "Failed to parse policy", http.StatusInternalServerError)
        return
    }

    pol := policy["policies"].([]interface{})[0].(map[string]interface{})
    logRules := pol["logUsageRules"].(map[string]interface{})

    // Controllo accessControlRules
    authorizedUsers := logRules["accessControlRules"].([]interface{})
    allowed := false
    for _, u := range authorizedUsers {
        if u.(string) == req.User {
            allowed = true
            break
        }
    }
    if !allowed {
        http.Error(w, "User not authorized", http.StatusForbidden)
        return
    }

    // Controllo allowedLocations
    if locs, ok := logRules["allowedLocations"]; ok {
        locationAllowed := false
        for _, loc := range locs.([]interface{}) {
            if loc.(string) == req.Location {
                locationAllowed = true
                break
            }
        }
        if !locationAllowed {
            http.Error(w, "Location not authorized", http.StatusForbidden)
            return
        }
    }

    // Controllo logExpiration
    if expRaw, ok := logRules["logExpiration"]; ok {
        expiration, err := time.Parse(time.RFC3339, expRaw.(string))
        if err == nil && time.Now().After(expiration) {
            http.Error(w, "Log expired", http.StatusForbidden)
            return
        }
    }

    // Controllo maxAccessCount
    accessCountFile := filepath.Join(dataPath, "access_count.txt")
    accessCount := 0
    if bytes, err := os.ReadFile(accessCountFile); err == nil {
        fmt.Sscanf(string(bytes), "%d", &accessCount)
    }
    if maxCountRaw, ok := logRules["maxAccessCount"]; ok {
        maxCount := int(maxCountRaw.(float64))
        if accessCount >= maxCount {
            http.Error(w, "Max access count exceeded", http.StatusForbidden)
            return
        }
    }
    accessCount += 1
    os.WriteFile(accessCountFile, []byte(fmt.Sprintf("%d", accessCount)), 0644)

    // Parsing del log XES
    xesPath := filepath.Join(dataPath, "log.xes")
    xesContent, err := os.ReadFile(xesPath)
    if err != nil {
        http.Error(w, "Log file not found", http.StatusNotFound)
        return
    }

    var logData XES
    if err := xml.Unmarshal(xesContent, &logData); err != nil {
        http.Error(w, "Invalid XES format", http.StatusInternalServerError)
        return
    }

    // Filtri
    required := map[string]bool{}
    excluded := map[string]bool{}
    if sem, ok := logRules["semanticLogConstraints"].(map[string]interface{}); ok {
        for _, inc := range sem["mustInclude"].([]interface{}) {
            required[inc.(string)] = true
        }
        for _, exc := range sem["mustExclude"].([]interface{}) {
            excluded[exc.(string)] = true
        }
    }

    var startTime, endTime time.Time
    if trange, ok := logRules["allowedTimeRange"].(map[string]interface{}); ok {
        startTime, _ = time.Parse(time.RFC3339, trange["startDate"].(string))
        endTime, _ = time.Parse(time.RFC3339, trange["endDate"].(string))
    }

    excludedAttrs := map[string]bool{}
    if excl, ok := logRules["attributeExclusionRules"].(map[string]interface{}); ok {
        if list, ok := excl["excludedAttributes"].(map[string]interface{}); ok {
            if key, ok := list["attributeKey"].(string); ok {
                excludedAttrs[key] = true
            }
        }
    }

    filteredTraces := []Trace{}
    for _, trace := range logData.Traces {
        traceHasRequired := len(required) == 0
        traceHasExcluded := false
        newEvents := []Event{}
        for _, event := range trace.Events {
            newStrs := []AttributeString{}
            newDates := []AttributeDate{}
            includeEvent := true
            conceptName := ""

            for _, s := range event.Strings {
                if s.Key == "concept:name" {
                    conceptName = s.Value
                    if required[s.Value] {
                        traceHasRequired = true
                    }
                    if excluded[s.Value] {
                        traceHasExcluded = true
                    }
                }
                if !excludedAttrs[s.Key] {
                    newStrs = append(newStrs, s)
                }
            }

            for _, d := range event.Dates {
                if d.Key == "time:timestamp" {
                    if !startTime.IsZero() && d.Value.Before(startTime) {
                        includeEvent = false
                    }
                    if !endTime.IsZero() && d.Value.After(endTime) {
                        includeEvent = false
                    }
                }
                newDates = append(newDates, d)
            }

            if includeEvent {
                newEvents = append(newEvents, Event{Strings: newStrs, Dates: newDates})
            }
        }

        if traceHasRequired && !traceHasExcluded {
            filteredTraces = append(filteredTraces, Trace{Events: newEvents})
        }
    }

    output, err := xml.MarshalIndent(XES{Traces: filteredTraces}, "", "  ")
    if err != nil {
        http.Error(w, "Failed to serialize filtered log", http.StatusInternalServerError)
        return
    }
    
    logAudit(filepath.Join(base, "configs", req.ConfigID), req.User, "access log", "true", req.Location)
    w.Header().Set("Content-Type", "application/xml")
    w.Write(output)
}"""


def generate_process_handler():
    return """func handleProcess(w http.ResponseWriter, r *http.Request) {
    if r.Method != "POST" {
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    base := filepath.Join("generated_tas", req.TaHash)
    configPath := filepath.Join(base, "configs", req.ConfigID, "policy_config.json")
    dataPath := filepath.Join(base, "data", req.ConfigID)
    algorithmPath := filepath.Join(base, "algorithms", req.Algorithm + ".go")

    policyBytes, err := os.ReadFile(configPath)
    if err != nil {
        http.Error(w, "Policy not found", http.StatusNotFound)
        return
    }

    var policy map[string]interface{}
    if err := json.Unmarshal(policyBytes, &policy); err != nil {
        http.Error(w, "Failed to parse policy", http.StatusInternalServerError)
        return
    }

    pol := policy["policies"].([]interface{})[0].(map[string]interface{})
    procRules := pol["processingRules"].(map[string]interface{})
    logRules := pol["logUsageRules"].(map[string]interface{})

    // Verifica accessControlRules
    authorized := false
    for _, u := range procRules["accessControlRules"].([]interface{}) {
        if u.(string) == req.User {
            authorized = true
            break
        }
    }
    if !authorized {
        http.Error(w, "User not authorized for processing", http.StatusForbidden)
        return
    }

    // Verifica location
    if locs, ok := procRules["allowedLocations"]; ok {
        allowed := false
        for _, loc := range locs.([]interface{}) {
            if loc.(string) == req.Location {
                allowed = true
                break
            }
        }
        if !allowed {
            http.Error(w, "Location not authorized", http.StatusForbidden)
            return
        }
    }

    // Verifica algoritmo consentito
    algoAllowed := false
    for _, tech := range procRules["allowedTechniques"].([]interface{}) {
        if tech.(map[string]interface{})["algorithm"].(string) == req.Algorithm {
            algoAllowed = true
            break
        }
    }
    if !algoAllowed {
        http.Error(w, "Algorithm not allowed", http.StatusForbidden)
        return
    }

    // Verifica esistenza file algoritmo
    if _, err := os.Stat(algorithmPath); os.IsNotExist(err) {
        http.Error(w, "Algorithm file missing", http.StatusInternalServerError)
        return
    }

    // Log expiration
    if expRaw, ok := logRules["logExpiration"]; ok {
        expiration, err := time.Parse(time.RFC3339, expRaw.(string))
        if err == nil && time.Now().After(expiration) {
            http.Error(w, "Log expired", http.StatusForbidden)
            return
        }
    }

    // Max access count
    accessCountFile := filepath.Join(dataPath, "process_access_count.txt")
    accessCount := 0
    if bytes, err := os.ReadFile(accessCountFile); err == nil {
        fmt.Sscanf(string(bytes), "%d", &accessCount)
    }
    if maxCountRaw, ok := procRules["maxAccessCount"]; ok {
        maxCount := int(maxCountRaw.(float64))
        if accessCount >= maxCount {
            http.Error(w, "Max processing count exceeded", http.StatusForbidden)
            return
        }
    }
    accessCount += 1
    os.WriteFile(accessCountFile, []byte(fmt.Sprintf("%d", accessCount)), 0644)

    // Caricamento e filtraggio log.xes
    xesPath := filepath.Join(dataPath, "log.xes")
    xesContent, err := os.ReadFile(xesPath)
    if err != nil {
        http.Error(w, "Log file not found", http.StatusNotFound)
        return
    }

    var logData XES
    if err := xml.Unmarshal(xesContent, &logData); err != nil {
        http.Error(w, "Invalid XES format", http.StatusInternalServerError)
        return
    }

    // Apply semantic filters
    required := map[string]bool{}
    excluded := map[string]bool{}
    if sem, ok := logRules["semanticLogConstraints"].(map[string]interface{}); ok {
        for _, inc := range sem["mustInclude"].([]interface{}) {
            required[inc.(string)] = true
        }
        for _, exc := range sem["mustExclude"].([]interface{}) {
            excluded[exc.(string)] = true
        }
    }

    filteredTraces := []Trace{}
    for _, trace := range logData.Traces {
        traceHasRequired := len(required) == 0
        traceHasExcluded := false
        newEvents := []Event{}
        for _, event := range trace.Events {
            keep := true
            for _, s := range event.Strings {
                if s.Key == "concept:name" {
                    if required[s.Value] {
                        traceHasRequired = true
                    }
                    if excluded[s.Value] {
                        traceHasExcluded = true
                    }
                }
            }
            if keep {
                newEvents = append(newEvents, event)
            }
        }
        if traceHasRequired && !traceHasExcluded {
            filteredTraces = append(filteredTraces, Trace{Events: newEvents})
        }
    }
    
    logAudit(filepath.Join(base, "configs", req.ConfigID), req.User, "processing", "true", req.Location)
    fmt.Fprintf(w, "Processing with algorithm=%s on %d filtered traces\\n", req.Algorithm, len(filteredTraces))
}"""



def generate_get_output_handler():
    return """func handleGetOutput(w http.ResponseWriter, r *http.Request) {
    if r.Method != "POST" {
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    base := filepath.Join("generated_tas", req.TaHash)
    configPath := filepath.Join(base, "configs", req.ConfigID, "policy_config.json")
    outputPath := filepath.Join(base, "data", req.ConfigID, "output.txt")

    policyBytes, err := os.ReadFile(configPath)
    if err != nil {
        http.Error(w, "Policy not found", http.StatusNotFound)
        return
    }

    var policy map[string]interface{}
    if err := json.Unmarshal(policyBytes, &policy); err != nil {
        http.Error(w, "Failed to parse policy", http.StatusInternalServerError)
        return
    }

    pol := policy["policies"].([]interface{})[0].(map[string]interface{})
    outputRules := pol["outputRules"].(map[string]interface{})

    // Verifica accessControlRules
    authorized := false
    for _, u := range outputRules["accessControlRules"].([]interface{}) {
        if u.(string) == req.User {
            authorized = true
            break
        }
    }
    if !authorized {
        http.Error(w, "User not authorized for output access", http.StatusForbidden)
        return
    }

    // Verifica allowedLocations
    if locs, ok := outputRules["allowedLocations"]; ok {
        allowed := false
        for _, loc := range locs.([]interface{}) {
            if loc.(string) == req.Location {
                allowed = true
                break
            }
        }
        if !allowed {
            http.Error(w, "Location not authorized", http.StatusForbidden)
            return
        }
    }

    // Verifica outputExpiration
    if expRaw, ok := outputRules["outputExpiration"]; ok {
        expiration, err := time.Parse(time.RFC3339, expRaw.(string))
        if err == nil && time.Now().After(expiration) {
            http.Error(w, "Output expired", http.StatusForbidden)
            return
        }
    }

    // Output max access
    outputCountFile := filepath.Join(base, "data", req.ConfigID, "output_access_count.txt")
    outputCount := 0
    if bytes, err := os.ReadFile(outputCountFile); err == nil {
        fmt.Sscanf(string(bytes), "%d", &outputCount)
    }
    if maxRaw, ok := outputRules["maxAccessCount"]; ok {
        maxAllowed := int(maxRaw.(float64))
        if outputCount >= maxAllowed {
            http.Error(w, "Max output access count exceeded", http.StatusForbidden)
            return
        }
    }
    outputCount += 1
    os.WriteFile(outputCountFile, []byte(fmt.Sprintf("%d", outputCount)), 0644)

    // Restituzione output
    outputData, err := os.ReadFile(outputPath)
    if err != nil {
        http.Error(w, "Output not found", http.StatusNotFound)
        return
    }

    logAudit(filepath.Join(base, "configs", req.ConfigID), req.User, "access output", "true", req.Location)
    w.Header().Set("Content-Type", "text/plain")
    w.Write(outputData)
}"""



def generate_policy_handler():
    return """func handleGetPolicy(w http.ResponseWriter, r *http.Request) {
    taHash := r.URL.Query().Get("ta_hash")
    configID := r.URL.Query().Get("config_id")

    if taHash == "" || configID == "" {
        http.Error(w, "Missing ta_hash or config_id", http.StatusBadRequest)
        return
    }

    policyPath := filepath.Join("generated_tas", taHash, "configs", configID, "policy_config.json")

    policyBytes, err := os.ReadFile(policyPath)
    if err != nil {
        http.Error(w, "Policy not found", http.StatusNotFound)
        return
    }

    logAudit(filepath.Join(base, "configs", req.ConfigID), req.User, "get policy", "true", req.Location)
    w.Header().Set("Content-Type", "application/json")
    w.Write(policyBytes)
}"""

def generate_audit_logger():
    return """func logAudit(basePath, user, operation string, allowed bool, location string) {
    logPath := filepath.Join(basePath, "audit.txt")
    now := time.Now()
    line := fmt.Sprintf("%s, %s, %t, %s, %s, %s\\n",
        user,
        operation,
        allowed,
        now.Format("15:04"),
        now.Format("02/01/2006"),
        location,
    )
    f, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
    if err != nil {
        fmt.Println("Errore scrittura audit:", err)
        return
    }
    defer f.Close()
    f.WriteString(line)
}
"""


def generate_main_go(ta_hash):
    base_dir = Path("generated_tas") / ta_hash
    main_go_path = base_dir / "main.go"

    content = generate_main_header() + "\n\n\n"
    content += generate_audit_logger() + "\n\n\n"
    content += generate_access_log_handler() + "\n\n\n"
    content += generate_process_handler() + "\n\n\n"
    content += generate_get_output_handler() + "\n\n\n"
    content += generate_policy_handler() + "\n\n\n"

    main_go_path.write_text(content)
    print(f"[build] main.go creato in {main_go_path}")
