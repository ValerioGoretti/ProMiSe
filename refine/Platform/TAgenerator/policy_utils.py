from rdflib import Graph, Namespace, RDF, URIRef, Literal
from rdflib.collection import Collection
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
from generate_main_go import generate_main_go, generate_go_mod

UCON = Namespace("http://example.org/ucon#")
EVENTLOG = Namespace("http://example.org/eventLog#")
PMT = Namespace("http://example.org/pmt#")
LOC = Namespace("http://id.loc.gov/vocabulary/countries/")

def node_to_str(val):
    if isinstance(val, URIRef):
        return val.split('#')[-1]
    elif isinstance(val, Literal):
        return str(val)
    else:
        return str(val)

def extract_structure(obj):
    if isinstance(obj, dict):
        # Se è una tecnica, estrai i nomi degli algoritmi
        if "allowedTechniques" in obj:
            return {
                "allowedTechniques": sorted(
                    [
                        tech.get("algorithm", "unknown")
                        for tech in obj.get("allowedTechniques", [])
                    ]
                )
            }
        return {k: extract_structure(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [extract_structure(obj[0])] if obj else []
    else:
        return type(obj).__name__

def compute_policy_structure_hash(policy_json):
    structure_only = extract_structure(policy_json)
    structure_str = json.dumps(structure_only, sort_keys=True)
    return hashlib.sha256(structure_str.encode('utf-8')).hexdigest()

def parse_policy_turtle(g):
    policies = []
    for policy in g.subjects(RDF.type, UCON.Authorization):
        pol = {}

        obj_id = g.value(policy, UCON.object_id)
        if obj_id:
            file_name = g.value(obj_id, EVENTLOG.fileName)
            if file_name:
                pol["log_file"] = str(file_name)

        log_usage_node = g.value(policy, UCON.logUsageRules)
        pol["logUsageRules"] = {}
        if log_usage_node:
            g_lu = pol["logUsageRules"]

            exp = g.value(log_usage_node, UCON.logExpiration)
            if exp:
                g_lu["logExpiration"] = str(exp)

            max_access = g.value(log_usage_node, UCON.maxAccessCount)
            if max_access:
                g_lu["maxAccessCount"] = int(str(max_access))

            allowed_locs = list(g.objects(log_usage_node, UCON.allowedLocations))
            if allowed_locs:
                g_lu["allowedLocations"] = [node_to_str(loc) for loc in allowed_locs]

            acrs = list(g.objects(log_usage_node, UCON.accessControlRules))
            if acrs:
                g_lu["accessControlRules"] = [str(a) for a in acrs]

            aer_node = g.value(log_usage_node, UCON.attributeExclusionRules)
            if aer_node:
                aer = {}
                scope = g.value(aer_node, UCON.scope)
                if scope:
                    aer["scope"] = str(scope)

                event_attr = g.value(aer_node, UCON.eventAttribute)
                if event_attr:
                    aer["eventAttribute"] = str(event_attr)

                excluded_attrs_nodes = list(g.objects(aer_node, UCON.excludedAttributes))
                excluded_attrs = []
                for ex_node in excluded_attrs_nodes:
                    key = g.value(ex_node, UCON.attributeKey)
                    if key:
                        excluded_attrs.append(str(key))
                aer["excludedAttributes"] = excluded_attrs
                g_lu["attributeExclusionRules"] = aer

            atn_node = g.value(log_usage_node, UCON.allowedTimeRange)
            if atn_node:
                atn = {}
                event_attr = g.value(atn_node, UCON.eventAttribute)
                if event_attr:
                    atn["eventAttribute"] = str(event_attr)
                start_date = g.value(atn_node, UCON.startDate)
                if start_date:
                    atn["startDate"] = str(start_date)
                end_date = g.value(atn_node, UCON.endDate)
                if end_date:
                    atn["endDate"] = str(end_date)
                g_lu["allowedTimeRange"] = atn

            slc_node = g.value(log_usage_node, UCON.semanticLogConstraints)
            if slc_node:
                slc = {}
                event_attr = g.value(slc_node, UCON.eventAttribute)
                if event_attr:
                    slc["eventAttribute"] = str(event_attr)

                must_include_node = g.value(slc_node, UCON.mustInclude)
                if must_include_node:
                    col = Collection(g, must_include_node)
                    slc["mustInclude"] = [node_to_str(item) for item in col]

                must_exclude_node = g.value(slc_node, UCON.mustExclude)
                if must_exclude_node:
                    col = Collection(g, must_exclude_node)
                    slc["mustExclude"] = [node_to_str(item) for item in col]

                g_lu["semanticLogConstraints"] = slc

        output_node = g.value(policy, UCON.outputRules)
        pol["outputRules"] = {}
        if output_node:
            g_or = pol["outputRules"]

            exp = g.value(output_node, UCON.outputExpiration)
            if exp:
                g_or["outputExpiration"] = str(exp)

            allowed_locs = list(g.objects(output_node, UCON.allowedLocations))
            if allowed_locs:
                g_or["allowedLocations"] = [node_to_str(loc) for loc in allowed_locs]

            acrs = list(g.objects(output_node, UCON.accessControlRules))
            if acrs:
                g_or["accessControlRules"] = [str(a) for a in acrs]

            atn_node = g.value(output_node, UCON.allowedTimeRange)
            if atn_node:
                atn = {}
                event_attr = g.value(atn_node, UCON.eventAttribute)
                if event_attr:
                    atn["eventAttribute"] = str(event_attr)
                start_date = g.value(atn_node, UCON.startDate)
                if start_date:
                    atn["startDate"] = str(start_date)
                end_date = g.value(atn_node, UCON.endDate)
                if end_date:
                    atn["endDate"] = str(end_date)
                g_or["allowedTimeRange"] = atn

        processing_node = g.value(policy, UCON.processingRules)
        pol["processingRules"] = {}
        if processing_node:
            g_pr = pol["processingRules"]

            acrs = list(g.objects(processing_node, UCON.accessControlRules))
            if acrs:
                g_pr["accessControlRules"] = [str(a) for a in acrs]

            allowed_techniques_node = g.value(processing_node, UCON.allowedTechinique)
            if allowed_techniques_node:
                col = Collection(g, allowed_techniques_node)
                techs = []
                for item in col:
                    tech = {}
                    tech_type = g.value(item, PMT.techniqueType)
                    alg = g.value(item, PMT.algorithm)
                    if tech_type:
                        tech["techniqueType"] = node_to_str(tech_type)
                    if alg:
                        tech["algorithm"] = node_to_str(alg)
                    techs.append(tech)
                g_pr["allowedTechniques"] = techs

        pol["last_updated"] = datetime.now().isoformat(timespec='seconds')
        policies.append(pol)

    if not policies:
        raise ValueError("Nessuna policy trovata nel file RDF.")

    return {"policies": policies}

def save_policy_instance(graph, policy_json, policy_bytes, log_filename, log_bytes):
    hash_val = compute_policy_structure_hash(policy_json)
    base_dir = Path("generated_tas") / hash_val
    configs_dir = base_dir / "configs"
    data_dir = base_dir / "data"
    configs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Carica mapping esistente o inizializza
    mapping_path = base_dir / "mapping.json"
    mapping = json.loads(mapping_path.read_text()) if mapping_path.exists() else {}

    # Calcolo hash del log e owner
    owner = policy_json["policies"][0].get("owner", "owner")
    log_hash = hashlib.sha256(log_bytes).hexdigest()
    dedup_key = f"{owner}:{hash_val}:{log_hash}"

    # Verifica duplicati
    for entry_id, entry in mapping.items():
        if entry.get("dedup_key") == dedup_key:
            return {
                "duplicate": True,
                "existing_id": entry_id,
                "config_path": entry["config_path"],
                "data_path": entry["data_path"],
                "log_filename": entry["log_file"]
            }

    # Non duplicato, crea nuova istanza
    existing_ids = [int(p.name) for p in configs_dir.iterdir() if p.is_dir() and p.name.isdigit()]
    next_id = f"{(max(existing_ids) + 1) if existing_ids else 1:02}"
    config_subdir = configs_dir / next_id
    data_subdir = data_dir / next_id
    config_subdir.mkdir()
    data_subdir.mkdir()

    # Salva policy TTL
    (config_subdir / "policy.ttl").write_bytes(policy_bytes)
    # Salva JSON config
    (config_subdir / "policy_config.json").write_text(json.dumps(policy_json, indent=2))
    # Salva file di log
    (data_subdir / log_filename).write_bytes(log_bytes)

    main_go_path = base_dir / "main.go"
    if not main_go_path.exists():
        generate_main_go(ta_hash=hash_val)
        generate_go_mod(ta_hash=hash_val)

    # Autorizzazioni per fase
    auth = policy_json["policies"][0]
    authorized_users = {
        "logUsage": auth.get("logUsageRules", {}).get("accessControlRules", []),
        "output": auth.get("outputRules", {}).get("accessControlRules", []),
        "processing": auth.get("processingRules", {}).get("accessControlRules", [])
    }
    if owner:
        for phase in authorized_users:
            if owner not in authorized_users[phase]:
                authorized_users[phase].append(owner)

    # 🔁 Copia algoritmi richiesti e crea manifest
    algorithm_subdir = base_dir / "algorithms"
    algorithm_subdir.mkdir(exist_ok=True)

    techniques = auth.get("processingRules", {}).get("allowedTechniques", [])
    algorithm_manifest = []

    for tech in techniques:
        algorithm_name = tech.get("algorithm")
        technique_type = tech.get("techniqueType", "")

        if not algorithm_name:
            continue

        source_path = Path("algorithmRepository") / f"{algorithm_name}.go"
        target_path = algorithm_subdir / f"{algorithm_name}.go"

        if not target_path.exists():
            if source_path.exists():
                shutil.copy(source_path, target_path)
            else:
                raise FileNotFoundError(f"L'algoritmo '{algorithm_name}' non è presente in 'algorithmRepository'.")

        # Calcola hash dell'algoritmo copiato
        algo_bytes = target_path.read_bytes()
        algo_hash = hashlib.sha256(algo_bytes).hexdigest()

        algorithm_manifest.append({
            "algorithm": algorithm_name,
            "techniqueType": technique_type,
            "path": str(target_path.resolve()),
            "hash": algo_hash
        })

    # Salva manifest
    manifest_path = algorithm_subdir / "algorithm_manifest.json"
    manifest_path.write_text(json.dumps(algorithm_manifest, indent=2))

    # Aggiungi voce al mapping
    mapping[next_id] = {
        "log_file": log_filename,
        "config_path": str(config_subdir),
        "data_path": str(data_subdir),
        "authorized_users": authorized_users,
        "owner": owner,
        "dedup_key": dedup_key
    }
    mapping_path.write_text(json.dumps(mapping, indent=2))

    return {
        "duplicate": False,
        "hash": hash_val,
        "id": next_id,
        "config_path": str(config_subdir),
        "data_path": str(data_subdir),
        "log_filename": log_filename
    }



