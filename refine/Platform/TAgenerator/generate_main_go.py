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

def generate_main_go(ta_hash):
    base_dir = Path("generated_tas") / ta_hash
    main_go_path = base_dir / "main.go"

    content = f"""package main

import (
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
    "path/filepath"
)

type Request struct {{
    TaHash     string `json:"ta_hash"`
    ConfigID   string `json:"config_id"`
    User       string `json:"user"`
    Location   string `json:"location"`
    Algorithm  string `json:"algorithm,omitempty"`
}}

func main() {{
    http.HandleFunc("/access_log", handleAccessLog)
    http.HandleFunc("/process", handleProcess)
    http.HandleFunc("/get_output", handleGetOutput)
    http.HandleFunc("/policy", handleGetPolicy)

    fmt.Println("Trusted App started on port 8080")
    http.ListenAndServe(":8080", nil)
}}

func handleAccessLog(w http.ResponseWriter, r *http.Request) {{
    if r.Method != "POST" {{
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }}

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }}

    // TODO: Validate user, location, and policy constraints
    fmt.Fprintf(w, "Accessing log for config_id=%s\n", req.ConfigID)
}}

func handleProcess(w http.ResponseWriter, r *http.Request) {{
    if r.Method != "POST" {{
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }}

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }}

    // TODO: Validate algorithm, location, access rights
    fmt.Fprintf(w, "Processing log using algorithm=%s for config_id=%s\n", req.Algorithm, req.ConfigID)
}}

func handleGetOutput(w http.ResponseWriter, r *http.Request) {{
    if r.Method != "POST" {{
        http.Error(w, "Invalid method", http.StatusMethodNotAllowed)
        return
    }}

    var req Request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }}

    // TODO: Check access rights and return output
    fmt.Fprintf(w, "Retrieving output for config_id=%s\n", req.ConfigID)
}}

func handleGetPolicy(w http.ResponseWriter, r *http.Request) {{
    taHash := r.URL.Query().Get("ta_hash")
    configID := r.URL.Query().Get("config_id")

    if taHash == "" || configID == "" {{
        http.Error(w, "Missing ta_hash or config_id", http.StatusBadRequest)
        return
    }}

    policyPath := filepath.Join("generated_tas", taHash, "configs", configID, "policy_config.json")
    data, err := os.ReadFile(policyPath)
    if err != nil {{
        http.Error(w, "Policy not found", http.StatusNotFound)
        return
    }}

    w.Header().Set("Content-Type", "application/json")
    w.Write(data)
}}
"""

    main_go_path.write_text(content)
    print(f"main.go created in {main_go_path}")

