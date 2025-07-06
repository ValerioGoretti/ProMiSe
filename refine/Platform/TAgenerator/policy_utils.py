from rdflib import Graph, Namespace, RDF, URIRef, Literal
from rdflib.collection import Collection
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

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

def save_policy_instance(graph, policy_json, policy_file, log_file):
    hash_val = compute_policy_structure_hash(policy_json)
    base_dir = Path("generated_tas") / hash_val
    configs_dir = base_dir / "configs"
    data_dir = base_dir / "data"

    configs_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    existing_ids = [int(p.name) for p in configs_dir.iterdir() if p.is_dir() and p.name.isdigit()]
    next_id = f"{(max(existing_ids) + 1) if existing_ids else 1:02}"

    config_subdir = configs_dir / next_id
    data_subdir = data_dir / next_id
    config_subdir.mkdir()
    data_subdir.mkdir()

    policy_path = config_subdir / "policy.ttl"
    with open(policy_path, "wb") as f:
        f.write(policy_file)

    config_path = config_subdir / "policy_config.json"
    with open(config_path, "w") as f:
        json.dump(policy_json, f, indent=2)

    log_path = data_subdir / log_file.filename
    with open(log_path, "wb") as f:
        f.write(log_file.read())

    # Estrai utenti autorizzati per ciascuna fase
    auth = policy_json["policies"][0]
    authorized_users = {
        "logUsage": auth.get("logUsageRules", {}).get("accessControlRules", []),
        "output": auth.get("outputRules", {}).get("accessControlRules", []),
        "processing": auth.get("processingRules", {}).get("accessControlRules", [])
    }

    # Proprietario del dato con accesso universale
    owner = auth.get("owner", "owner")
    if owner:
        for phase in authorized_users:
            if owner not in authorized_users[phase]:
                authorized_users[phase].append(owner)

    mapping_path = base_dir / "mapping.json"
    if mapping_path.exists():
        with open(mapping_path, "r") as f:
            mapping = json.load(f)
    else:
        mapping = {}

    mapping[next_id] = {
        "log_file": log_file.filename,
        "config_path": str(config_subdir),
        "data_path": str(data_subdir),
        "authorized_users": authorized_users,
        "owner": owner
    }

    with open(mapping_path, "w") as f:
        json.dump(mapping, f, indent=2)

    return {
        "hash": hash_val,
        "config_path": str(config_subdir),
        "data_path": str(data_subdir),
        "log_filename": log_file.filename
    }
