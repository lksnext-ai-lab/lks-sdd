"""Exact-subject verification for v2 using local declarations and explicit evidence."""
from __future__ import annotations

from datetime import timedelta
import copy
import json
from pathlib import Path
import re

from v2_contract import ContractError, DOCS, Model, canonical, fingerprint, load, path_at, read_bytes, sha
from v2_authoring import edit_elements
from v2_lifecycle import (active_execution, current_authorization, diff_guard, next_id, now,
                          planning, record, timestamp, work_inventory)
from v2_storage import apply, preview

ROOT = Path(__file__).resolve().parents[1]
STAGES = {"diagnostic": -1, "development": 0, "integration": 1, "preproduction": 1, "release": 2, "production": 2}
PINNED_IMAGE = re.compile(r"^[^\s@]+@sha256:[a-f0-9]{64}$")


def technology_readiness(model: Model, tasks: list[str], environment: str, stage="development") -> dict:
    from v2_contract import technology_readiness as declaration_readiness
    result = declaration_readiness(model, tasks)
    return {**result, "environment": environment, "stage": stage}

def engine_hash():
    names = ("v2_verification.py", "v2_contract.py", "v2_lifecycle.py", "v2_quality.py", "consumer_observer.py",
             "observation_contract.py", "evidence_safety.py", "v2_composition.py", "v2_schema.py",
             "composition_contract.py", "integration_contract.py", "v2_features.py", "v2_authoring.py",
             "v2_storage.py", "v2_controls.py", "v2_preparation.py", "query_sources.py", "query_runtime.py")
    files = {"scripts/" + name: sha((ROOT / "scripts" / name).read_bytes()) for name in names}
    files["requirements-runtime.txt"] = sha((ROOT / "requirements-runtime.txt").read_bytes())
    for path in (ROOT / "schemas").glob("*-2.0.schema.json"):
        files[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    files["schemas/consumer-observation.schema.json"] = sha((ROOT / "schemas/consumer-observation.schema.json").read_bytes())
    return fingerprint(files)

def evidence(model: Model, identifier: str) -> dict:
    if not re.fullmatch(r"EVID-\d{3,}", identifier):
        raise ContractError("Expected EVID identifier")
    value = json.loads(read_bytes(model.root, DOCS + "/evidence/" + identifier + ".json"))
    from v2_schema import validate
    validate("verification-evidence", value)
    if value.get("schema_version") != "2.0" or value.get("evidence_id") != identifier:
        raise ContractError("Evidence contract/identity mismatch")
    if fingerprint({k: v for k, v in value.items() if k != "integrity_sha256"}) != value.get("integrity_sha256"):
        raise ContractError("Evidence integrity mismatch")
    for check in value.get("checks", []):
        for artifact in check.get("artifacts", []):
            if sha(read_bytes(model.root, artifact["evidence_path"], limit=32 * 1024 * 1024)) != artifact["sha256"]:
                raise ContractError("Evidence artifact altered")
    return value


def _variant_applies(declaration, variant: dict, tasks: set[str], environment: str, stage: str) -> bool:
    scope = set(variant["scope"])
    declared_scope = set(declaration.meta["technology"]["scope"])
    if ("global" in scope and len(scope) != 1) or ("global" in declared_scope and len(declared_scope) != 1):
        raise ContractError("Technology variant scope cannot mix global and TASK selectors: " + variant["id"])
    if "global" in scope and "global" not in declared_scope:
        raise ContractError("Technology variant global scope exceeds its declaration: " + variant["id"])
    if "global" not in declared_scope and not scope <= declared_scope:
        raise ContractError("Technology variant scope exceeds its declaration: " + variant["id"])
    return ("global" in scope or bool(scope & tasks)) and environment in variant["environments"] and stage in variant["stages"]


def _approved_observer_check(model: Model, declaration, variant: dict, observer: dict,
                             required_scopes: set[str], required_interfaces: set[str]) -> tuple[dict | None, list[str]]:
    identity = f"{declaration.id}/{variant['id']}/{observer['id']}"
    errors = []
    command = observer["command"]
    if observer["source"] != "approved-consumer":
        errors.append(identity + ": observer source is not approved for execution")
    if not PINNED_IMAGE.fullmatch(observer["image"]):
        errors.append(identity + ": observer image must be pinned by sha256")
    if not command or any(not isinstance(item, str) or not item or "\x00" in item for item in command):
        errors.append(identity + ": observer command is invalid")
    if type(observer["timeout_seconds"]) is not int or not 1 <= observer["timeout_seconds"] <= 600:
        errors.append(identity + ": observer timeout must be between 1 and 600 seconds")
    if type(observer["requires_containers"]) is not bool:
        errors.append(identity + ": observer container requirement is invalid")
    scopes, interfaces = set(observer["scopes"]), set(observer["interfaces"])
    if not scopes <= required_scopes:
        errors.append(identity + ": observer covers scopes outside the selected subject")
    if not interfaces <= required_interfaces:
        errors.append(identity + ": observer covers interfaces outside the selected subject")
    hashes = {}
    for item in observer["inputs"]:
        relative, expected = item["path"], item["sha256"]
        if relative in hashes:
            errors.append(identity + ": observer input appears more than once: " + relative)
            continue
        try:
            actual = sha(read_bytes(model.root, relative, limit=64 * 1024 * 1024))
        except ContractError as exc:
            errors.append(identity + ": observer input is unsafe or unavailable: " + relative + " (" + str(exc) + ")")
            continue
        if actual != expected:
            errors.append(identity + ": observer input hash mismatch: " + relative)
            continue
        hashes[relative] = expected
    if not hashes:
        errors.append(identity + ": observer needs at least one approved input")
    if errors:
        return None, errors
    definition = {"technology_id": declaration.id, "variant_id": variant["id"], "observer_id": observer["id"],
                  "gate_id": observer["gate_id"], "source": observer["source"], "image": observer["image"],
                  "command": list(command), "inputs": hashes, "timeout_seconds": observer["timeout_seconds"],
                  "requires_containers": observer["requires_containers"], "scopes": sorted(scopes),
                  "interfaces": sorted(interfaces)}
    gate = {"id": observer["gate_id"], "source": observer["source"], "image": observer["image"],
            "observer": {"command": list(command)}, "timeout_seconds": observer["timeout_seconds"],
            "scopes": sorted(scopes), "interfaces": sorted(interfaces)}
    return {"gate_id": observer["gate_id"], "gate": gate, "definition": definition, "input_hashes": hashes,
            "input_key": fingerprint(definition), "required": True, "disposition": "execute",
            "requires_containers": observer["requires_containers"]}, []


def _approved_checks(model: Model, tasks: list[str], environment: str, stage: str, required: set[str],
                     scopes: set[str], interfaces: set[str]) -> tuple[list[dict], list[str], list[str]]:
    candidates, invalid = {gate: [] for gate in required}, {gate: [] for gate in required}
    selected_tasks = set(tasks)
    variant_ids = set()
    for declaration in model.technology_declarations:
        if declaration.meta["state"] != "confirmed":
            continue
        declaration_scope = set(declaration.meta["technology"]["scope"])
        if "global" not in declaration_scope and not declaration_scope & selected_tasks:
            continue
        for variant in declaration.meta["technology"].get("variants", []):
            identity = (declaration.id, variant["id"])
            if identity in variant_ids:
                raise ContractError("Duplicate technology variant identity: " + variant["id"])
            variant_ids.add(identity)
            if not _variant_applies(declaration, variant, selected_tasks, environment, stage):
                continue
            for observer in variant["observers"]:
                if observer["gate_id"] not in required:
                    continue
                check, errors = _approved_observer_check(model, declaration, variant, observer, scopes, interfaces)
                if errors:
                    invalid[observer["gate_id"]].extend(errors)
                elif check:
                    candidates[observer["gate_id"]].append(check)
    checks, blockers, missing = [], [], []
    for gate in sorted(required):
        valid = candidates[gate]
        if len(valid) == 1:
            checks.append(valid[0])
        elif len(valid) > 1:
            blockers.append("Ambiguous approved observers for required gate " + gate)
            missing.append(gate)
        elif invalid[gate]:
            blockers.extend(sorted(set(invalid[gate])))
            missing.append(gate)
        else:
            blockers.append("No approved observer applies to required gate " + gate + f" for {environment}/{stage}")
            missing.append(gate)
    covered_scopes = {scope for check in checks for scope in check["gate"]["scopes"]}
    covered_interfaces = {interface for check in checks for interface in check["gate"]["interfaces"]}
    absent_scopes = sorted(scopes - covered_scopes)
    absent_interfaces = sorted(interfaces - covered_interfaces)
    if absent_scopes:
        blockers.append("Approved observers do not cover required scopes: " + ", ".join(absent_scopes))
    if absent_interfaces:
        blockers.append("Approved observers do not cover required interfaces: " + ", ".join(absent_interfaces))
    return checks, sorted(set(blockers)), sorted(set(missing))


def verification_plan(model: Model, tasks: list[str], environment: str, stage: str, *, assessor=None) -> dict:
    if stage not in STAGES:
        raise ContractError("Unknown verification stage")
    if stage == "diagnostic":
        return {"status": "diagnostic", "processes_executed": 0, "checks": [], "writes": []}
    authorization = current_authorization(model, tasks, environment)
    execution = active_execution(model, tasks)
    if any(model.elements[t].meta["state"] != "in-review" for t in tasks):
        raise ContractError("Verification requires completed implementation handoff (in-review)")
    guard = diff_guard(model, execution)
    if guard["status"] != "within-scope":
        raise ContractError("; ".join(guard["blockers"]))
    technology = (assessor or technology_readiness)(model, tasks, environment, stage)
    if technology["status"] == "blocked":
        raise ContractError("Technology declaration is unresolved: " + "; ".join(technology.get("blockers", [])))
    from v2_quality import obligations
    quality = obligations(model, tasks)
    if quality["blockers"]:
        raise ContractError("; ".join(quality["blockers"]))
    required, scopes, interfaces = (set(quality[key]) for key in ("gates", "scopes", "interfaces"))
    checks, observer_blockers, missing = _approved_checks(model, tasks, environment, stage, required, scopes, interfaces)
    material = {"project": model.manifest["project_id"], "tasks": sorted(tasks), "files": guard["files"],
                "contract": authorization["fingerprint"], "environment": environment, "technology": technology,
                "engine": engine_hash(), "interfaces": sorted(interfaces), "scopes": sorted(scopes),
                "observers": [check["definition"] for check in checks]}
    return {"status": "blocked" if missing or observer_blockers else "planned", "missing_critical_gates": missing,
            "blockers": observer_blockers, "checks": checks, "subject": fingerprint(material), "material": material, "technology": technology,
            "task_ids": tasks, "environment": environment, "stage": stage, "execution": execution.id,
            "required_scopes": sorted(scopes), "required_interfaces": sorted(interfaces),
            "allow_task_closure": not missing and not observer_blockers, "cache_max_age_hours": 0,
            "human_review_required": quality["human_review_required"], "processes_executed": 0, "writes": []}

def verify(model: Model, tasks: list[str], environment: str, stage: str, *, evidence_id: str,
           execute: bool = False, containers: bool = False, assessor=None, runner=None) -> dict:
    selection = verification_plan(model, tasks, environment, stage, assessor=assessor)
    if not execute or selection["status"] in {"diagnostic", "blocked"}:
        return selection
    if not re.fullmatch(r"EVID-\d{3,}", evidence_id):
        raise ContractError("New EVID identifier required")
    evidence_relative = DOCS + "/evidence/" + evidence_id + ".json"
    if path_at(model.root, evidence_relative, missing=True).exists():
        raise ContractError("Evidence is immutable; reuse observations under a new EVID, not overwrite")
    observations, blobs, processes = [], {}, 0
    if not containers and runner is None and any(c["disposition"] == "execute" and c["requires_containers"]
                                                 for c in selection["checks"]):
        raise ContractError("This verification plan requires explicit --containers authorization")
    from consumer_observer import execute as run_observer
    for entry in selection["checks"]:
        if entry["disposition"] == "omitted":
            observations.append({"gate_id": entry["gate_id"], "status": "not-run", "disposition": "omitted",
                                 "observed_at": now(), "reason": entry["reason"], "scopes": [], "interfaces": [],
                                 "required": entry["required"], "input_key": entry["input_key"]})
            continue
        if entry["disposition"] == "reused":
            observations.append({**copy.deepcopy(entry["reuse"]), "disposition": "reused", "reused_from": entry["reused_from"]})
            continue
        processes += 1
        if runner:
            observation, artifacts = runner(model.root, entry)
        elif "gate" in entry:
            observation, artifacts = run_observer(model.root, entry["gate"], entry["input_hashes"])
        else:
            raise ContractError("Verification commands must be explicit local observers")
        observation = {**observation, "scopes": observation.get("evidence_scopes", observation.get("scopes", [])),
                       "interfaces": observation.get("interface_ids", observation.get("interfaces", [])),
                       "observed_at": now(), "disposition": "executed", "input_key": entry["input_key"],
                       "required": entry["required"]}
        from v2_quality import observation_errors
        errors = observation_errors(observation, entry)
        if errors:
            observation.update(status="failed", sufficiency_errors=errors)
        for artifact in observation.get("artifacts", []):
            if artifact["sha256"] not in artifacts or sha(artifacts[artifact["sha256"]]) != artifact["sha256"]:
                raise ContractError("Observation artifact missing or not bound to this run")
            artifact["evidence_path"] = DOCS + "/evidence/artifacts/" + artifact["sha256"]
        blobs.update({DOCS + "/evidence/artifacts/" + key: value for key, value in artifacts.items()})
        observations.append(observation)
    fresh = load(model.root)
    fresh.require_valid()
    for entry in selection["checks"]:
        for input_path, expected in entry.get("input_hashes", {}).items():
            if sha(read_bytes(fresh.root, input_path, limit=64 * 1024 * 1024)) != expected:
                raise ContractError("Approved observer input changed during execution: " + input_path)
    guard = diff_guard(fresh, fresh.elements[selection["execution"]])
    if guard["files"] != selection["material"]["files"] or guard["status"] == "blocked":
        raise ContractError("Verification changed source inputs; evidence not applicable")
    current_authorization(fresh, tasks, environment)
    if engine_hash() != selection["material"]["engine"]:
        raise ContractError("Verification engine changed during execution")
    passed = [o for o in observations if o["status"] == "passed"]
    scopes = {s for o in passed for s in o["scopes"]}
    interfaces = {i for o in passed for i in o["interfaces"]}
    failures = [o["gate_id"] for o in observations if o["required"] and o["status"] != "passed"]
    missing_scopes = sorted(set(selection["required_scopes"]) - scopes)
    missing_interfaces = sorted(set(selection["required_interfaces"]) - interfaces)
    from v2_quality import visual_coverage_errors
    visual_errors = visual_coverage_errors(fresh, tasks, observations)
    failures.extend(visual_errors)
    classification = "not-verified" if failures or missing_scopes or missing_interfaces else (
        "verified")
    value = {"schema_version": "2.0", "evidence_id": evidence_id, "recorded_at": now(),
             "subject": selection["subject"], "material": selection["material"],
             "task_ids": tasks, "execution_id": selection["execution"], "environment": environment,
             "stage": stage, "workspace_revision": "workspace-sha256:" + fingerprint(selection["material"]["files"]),
             "build_id": "observation-set-sha256:" + fingerprint(sorted({a["sha256"] for o in observations for a in o.get("artifacts", [])})),
             "artifact_digests": sorted({a["sha256"] for o in observations for a in o.get("artifacts", [])}),
             "deliverable_artifact_digests": sorted({a["sha256"] for o in observations if o["status"] == "passed"
                 for a in o.get("observations", {}).get("build_artifacts", []) if a.get("kind") == "deployable"
                 and any(a.get("path") == b.get("path") and a.get("sha256") == b.get("sha256") for b in o.get("artifacts", []))}),
             "cache_max_age_hours": selection["cache_max_age_hours"],
             "human_review_required": selection["human_review_required"],
             "definition_refs": [{"id": e.id, "uid": e.meta["uid"], "revision": e.meta["revision"],
                                  "normative_sha256": fingerprint(e.normative()), "source": e.source()}
                                 for e in fresh.by_kind("feature")
                                 if any(e.id in fresh.elements[t].targets("implements", "contributes_to") for t in tasks)],
             "contract_source_hashes": {p: h for p, h in fresh.hashes.items() if p.startswith(DOCS + "/")
                                       and "/evidence/" not in p and "/history/" not in p},
             "checks": observations, "classification": classification, "allow_task_closure": selection["allow_task_closure"],
             "failures": failures, "missing_scopes": missing_scopes, "missing_interfaces": missing_interfaces,
             "build_identity_kind": "observation-set-not-deployment-proof",
             "delivery": "not-assessed", "human_acceptance": "not-assessed"}
    value["integrity_sha256"] = fingerprint(value)
    from v2_schema import validate
    validate("verification-evidence", value)
    changes = {**blobs, evidence_relative: canonical(value) + b"\n"}
    plan = preview(model.root, changes, sources=fresh.hashes, operation="record-verification")
    # --execute --evidence-id explicitly authorizes recording this actual run.
    applied = apply(model.root, changes, plan, plan["preview_hash"])
    return {"status": classification, "evidence_id": evidence_id, "processes_executed": processes,
            "checks": observations, "writes": applied["writes"], "delivery": "not-assessed"}


def close(model: Model, tasks: list[str], evidence_id: str, *, actor: str, at: str,
          authorized_hash: str | None = None) -> dict:
    value = evidence(model, evidence_id)
    execution = active_execution(model, tasks)
    auth = current_authorization(model, tasks, value["environment"])
    guard = diff_guard(model, execution)
    if (not set(tasks) <= set(value["task_ids"]) or value["execution_id"] != execution.id
            or value["classification"] not in {"verified", "verified-with-reservations"}
            or not value["allow_task_closure"] or value["material"]["files"] != guard["files"]
            or value["material"]["contract"] != auth["fingerprint"] or guard["status"] == "blocked"):
        raise ContractError("Evidence does not close this exact authorized subject")
    if any(model.elements[t].meta["state"] != "in-review" for t in tasks):
        raise ContractError("Only in-review TASKs may complete")
    if value["material"]["engine"] != engine_hash():
        raise ContractError("Verification engine changed; reassess evidence")
    fresh = verification_plan(model, tasks, value["environment"], value["stage"])
    if fresh["status"] != "planned" or fresh["subject"] != value["subject"]:
        raise ContractError("Technology declaration, obligation or verification subject changed")
    if not actor.strip() or timestamp(at) > timestamp(now()):
        raise ContractError("A declared reviewer and non-future closure time are required")
    max_age = value.get("cache_max_age_hours", 0)
    if max_age and any(not timedelta(0) <= timestamp(now()) - timestamp(c["observed_at"]) < timedelta(hours=max_age)
                       for c in value["checks"] if c.get("required")):
        raise ContractError("Evidence expired; run verification again without refreshing prior observations")
    from v2_quality import review_satisfied
    if value.get("human_review_required") and not review_satisfied(model, tasks, value):
        raise ContractError("Exact-result human/visual acceptance remains pending")
    identifier = next_id(model, "CKPT")
    path, data = record(model, identifier, "checkpoint", "Verificación del trabajo", "Evidencia: " + evidence_id + ". Entrega y aceptación humana independientes.",
                        state="active", actor=actor, recorded_at=at, next_action="Revisar condiciones de entrega",
                        files=guard["files"], evidence_ids=[evidence_id], relations={"execution": [execution.id], "implements": tasks})
    updates = {t: dict(model.elements[t].meta, state="done", health="verified", evidence_ids=[*model.elements[t].meta.get("evidence_ids", []), evidence_id]) for t in tasks}
    if set(tasks) == execution.targets("implements"):
        updates[execution.id] = dict(execution.meta, state="completed")
    for problem in model.by_kind("problem"):
        if problem.targets("affects") <= set(tasks) and problem.meta["state"] != "resolved":
            if any(timestamp(c["observed_at"]) <= timestamp(problem.meta["recorded_at"])
                   for c in value["checks"] if c.get("required")):
                raise ContractError("Problem requires evidence observed after the finding")
            updates[problem.id] = dict(problem.meta, state="resolved", evidence_id=evidence_id)
    changes = {path: data, **edit_elements(model, updates)}
    plan = preview(model.root, changes, sources=model.hashes, operation="complete-verified-task")
    return apply(model.root, changes, plan, authorized_hash) if authorized_hash else plan
