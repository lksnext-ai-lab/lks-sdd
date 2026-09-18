"""Exact-subject verification for v2, reusing reviewed profile/observer engines."""
from __future__ import annotations

from datetime import timedelta
import copy
import json
import os
from pathlib import Path
import re
import sys

from v2_contract import ContractError, DOCS, Model, canonical, fingerprint, load, path_at, read_bytes, sha
from v2_authoring import edit_elements
from v2_lifecycle import (active_execution, current_authorization, diff_guard, next_id, now,
                          planning, record, timestamp, work_inventory)
from v2_storage import apply, preview

ROOT = Path(__file__).resolve().parents[1]
STAGES = {"diagnostic": -1, "development": 0, "integration": 1, "preproduction": 1, "release": 2, "production": 2}


def variant_context(root: Path, variant: dict, *, execution=False) -> dict:
    from project_variants import VariantError
    model = load(root)
    model.require_valid()
    tasks = variant["task_ids"]
    assessment = planning(model, tasks)
    auth = current_authorization(model, tasks, variant["environment"])
    rows, details = {}, {}
    bindings = set()
    for task_id in tasks:
        task = model.elements[task_id]
        if variant["increment"] not in task.targets("increment") or variant["release"] not in task.targets("release"):
            raise VariantError("Variant TASK/release/increment is outside canonical scope")
        bindings.update(task.targets("bindings"))
        rows[task_id] = {"ID": task_id, "Increment": variant["increment"], "Release": variant["release"],
                         "Workflow state": task.meta["state"], "Profile binding": ", ".join(task.targets("bindings"))}
        details[task_id] = {"definition": [{"Technical gates": ", ".join(task.meta.get("gates", []))}]}
    if not bindings:
        raise VariantError("TASKs require an explicitly selected profile binding")
    binding_rows = {}
    for identifier in sorted(bindings):
        item = model.elements[identifier]
        if item.kind != "binding" or item.meta.get("profile_id") != variant["profile_id"]:
            raise VariantError("Variant reference differs from selected binding")
        binding_rows[identifier] = {"binding_id": identifier, "profile_id": item.meta["profile_id"],
                                    "unit_path": item.meta.get("unit_path", "."),
                                    "lock_path": item.meta.get("lock_path", f".lks-sdd/profiles/{identifier}.lock.json")}
    executions = [e for e in model.by_kind("execution") if set(tasks) <= e.targets("implements")
                  and e.meta["state"] not in {"completed", "cancelled"}]
    if execution and len(executions) != 1:
        raise VariantError("Unique active execution required")
    return {"root": root, "manifest": model.manifest, "model": model, "definitions": {},
            "authorization": auth, "execution": {"execution_id": executions[0].id, **executions[0].meta} if len(executions) == 1 else None,
            "bindings": sorted(bindings), "planning": {"specification_fingerprint": assessment["fingerprint"], "planning_fingerprint": assessment["fingerprint"]},
            "delivery": {"tasks": rows, "task_details": details, "bindings": binding_rows,
                         "interfaces": {e.id: e.meta for e in model.by_kind("interface")},
                         "environments": {e.id: {"Role": e.meta.get("role", "unknown"), **e.meta} for e in model.by_kind("environment")}}}


def technology_readiness(model: Model, tasks: list[str], environment: str, stage="development") -> dict:
    from project_variants import load_config, proposal, current_approval, diagnose
    config = load_config(model.root)
    variants = [v for v in (config or {}).get("variants", []) if set(tasks) & set(v["task_ids"])]
    if variants and config["policy"]["mode"] == "approved-project-variants":
        if len(variants) != 1 or not set(tasks) <= set(variants[0]["task_ids"]):
            raise ContractError("Select a single exact variant TASK scope")
        value = proposal(model.root, variants[0]["id"], environment, stage)
        approval = current_approval(model.root, value)
        return {"status": "approved-project-variant", "variant_id": variants[0]["id"],
                "approval_id": approval["approval_id"], "stage": stage, "environment": environment,
                "profile_id": variants[0]["profile_id"], "consumer_certified": False}
    bindings = {b for t in tasks for b in model.elements[t].targets("bindings")}
    if not bindings:
        return {"status": "not-assessed", "reason": "No explicit technology binding"}
    results = []
    for identifier in sorted(bindings):
        item = model.elements[identifier]
        if item.kind != "binding" or item.meta["state"] not in {"confirmed", "approved"}:
            return {"status": "not-assessed", "reason": "Binding not confirmed"}
        unit = item.meta.get("unit_path", ".")
        location = model.root if unit == "." else path_at(model.root, unit)
        result = diagnose(location, item.meta.get("profile_id"))
        if result["compatibility"] != "exact-certified":
            return {"status": result["compatibility"], "binding": identifier, "diagnostic": result}
        from profile_registry import load_profile_bundle
        bundle = load_profile_bundle(item.meta["profile_id"])
        expected = (bundle.root / "technology-profile.lock.json").read_bytes()
        lock = item.meta.get("lock_path", f".lks-sdd/profiles/{identifier}.lock.json")
        target = path_at(model.root, lock, missing=True)
        if target.exists() and target.read_bytes() != expected:
            raise ContractError("Consumer profile lock differs from exact certified reference")
        results.append({"binding_id": identifier, "profile_id": item.meta["profile_id"],
                        "lock_path": lock, "lock_sha256": sha(expected)})
    return {"status": "exact-certified", "bindings": results, "stage": stage, "environment": environment}


def engine_hash():
    names = ("v2_verification.py", "v2_contract.py", "v2_lifecycle.py", "v2_quality.py", "consumer_observer.py",
             "project_variants.py", "observation_contract.py", "evidence_safety.py", "profile_registry.py",
             "v2_composition.py", "v2_schema.py", "composition_contract.py", "integration_contract.py",
             "v2_features.py", "v2_authoring.py", "v2_storage.py", "v2_controls.py", "v2_preparation.py", "query_sources.py", "query_runtime.py")
    files = {"scripts/" + name: sha((ROOT / "scripts" / name).read_bytes()) for name in names}
    executor = "skills/lks-sdd-verify/scripts/run_verification.py"
    files[executor] = sha((ROOT / executor).read_bytes())
    for path in (ROOT / "schemas").glob("*-2.0.schema.json"):
        files[path.relative_to(ROOT).as_posix()] = sha(path.read_bytes())
    for name in ("consumer-observation.schema.json", "project-variants.schema.json"):
        files["schemas/" + name] = sha((ROOT / "schemas" / name).read_bytes())
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
    if technology["status"] not in {"exact-certified", "approved-project-variant"}:
        raise ContractError("Technology verification is not authorized")
    from v2_quality import obligations
    quality = obligations(model, tasks)
    if quality["blockers"]:
        raise ContractError("; ".join(quality["blockers"]))
    required, scopes, interfaces = (set(quality[k]) for k in ("gates", "scopes", "interfaces"))
    checks, ttl, closure = [], 0, True
    from project_variants import load_config, proposal, input_hashes
    if technology["status"] == "approved-project-variant":
        config = load_config(model.root)
        variant = next(v for v in config["variants"] if v["id"] == technology["variant_id"])
        value = proposal(model.root, variant["id"], environment, stage)
        ttl, closure = config["policy"]["cache_max_age_hours"], config["policy"]["allow_task_closure"]
        for gate in variant["gates"]:
            paths = list(dict.fromkeys(gate.get("inputs", variant["inputs"]) +
                                       ([gate["observer"]["path"]] + gate["observer"].get("inputs", []) if gate.get("observer") else [])))
            hashes = input_hashes(model.root, paths)
            selected = STAGES[gate["stage"]] <= STAGES[stage]
            checks.append({"gate_id": gate["id"], "gate": gate, "input_hashes": hashes,
                           "required": gate["id"] in required or stage in {"release", "production"},
                           "disposition": "execute" if selected else "omitted", "reason": "stage:" + gate["stage"]})
    else:
        from profile_registry import load_profile_bundle
        for binding in technology["bindings"]:
            item = model.elements[binding["binding_id"]]
            bundle = load_profile_bundle(binding["profile_id"])
            for gate in bundle.driver["verify"]["checks"]:
                if gate["kind"] != "command" or gate.get("phase") == "G4":
                    continue
                selected = stage in {"integration", "preproduction", "release", "production"} or gate["id"] in required
                checks.append({"gate_id": gate["id"], "packaged": gate,
                               "binding": {**binding, "unit_path": item.meta.get("unit_path", ".")},
                               "required": gate["id"] in required or bool(gate.get("required")) and stage != "development",
                               "disposition": "execute" if selected else "omitted", "reason": "certified-profile-stage",
                               "input_hashes": guard["files"]})
    if technology["status"] == "exact-certified":
        from v2_composition import resolve
        for composition in resolve(model, tasks, require_locks=True):
            bundle = load_profile_bundle(composition["profile_id"])
            gate = next(g for g in bundle.driver["verify"]["checks"] if g["id"] == composition["gate_id"])
            if any(c["gate_id"] == gate["id"] and c.get("binding", {}).get("profile_id") == composition["profile_id"] for c in checks):
                continue
            checks.append({"gate_id": gate["id"], "packaged": gate, "composition": composition, "required": True,
                           "disposition": "execute" if stage != "development" or gate["id"] in required else "omitted",
                           "reason": "exact-composition-obligation", "input_hashes": guard["files"]})
    known = {c["gate_id"] for c in checks}
    missing = sorted(required - known)
    if stage in {"release", "production"} and technology["status"] == "approved-project-variant":
        from profile_registry import load_profile_bundle
        bundle = load_profile_bundle(technology["profile_id"])
        missing += sorted({c["id"] for c in bundle.driver["verify"]["checks"] if c.get("required") and c.get("phase") != "G4"} - known)
    material = {"project": model.manifest["project_id"], "tasks": sorted(tasks), "files": guard["files"],
                "contract": authorization["fingerprint"], "environment": environment, "technology": technology,
                "engine": engine_hash(), "interfaces": sorted(interfaces), "scopes": sorted(scopes)}
    subject = fingerprint(material)
    cache = []
    directory = path_at(model.root, DOCS + "/evidence", missing=True)
    if directory.exists():
        for path in sorted(directory.glob("EVID-*.json")):
            raw = json.loads(read_bytes(model.root, path.relative_to(model.root).as_posix()))
            if raw.get("schema_version") == "2.0":
                cache.append(evidence(model, path.stem))
    for check in checks:
        from v2_quality import interface_obligation
        check["interface_obligations"] = [interface_obligation(model.elements[i]) for i in sorted(interfaces)
                                            if check["gate_id"] in model.elements[i].meta.get("gates", [])]
        check["input_key"] = fingerprint({"subject": material, "gate": check.get("gate", check.get("packaged")), "inputs": check["input_hashes"]})
        if check["disposition"] != "execute" or not check.get("gate", {}).get("deterministic") or stage in {"release", "production"}:
            continue
        for previous in reversed(cache):
            for observation in previous["checks"]:
                age = timestamp(now()) - timestamp(observation["observed_at"])
                if (observation.get("input_key") == check["input_key"] and observation["status"] == "passed"
                        and timedelta(0) <= age < timedelta(hours=ttl)):
                    check.update(disposition="reused", reuse=observation, reused_from=previous["evidence_id"], reason="unchanged-deterministic-evidence")
    return {"status": "blocked" if missing else "planned", "missing_critical_gates": sorted(set(missing)),
            "checks": checks, "subject": subject, "material": material, "technology": technology,
            "task_ids": tasks, "environment": environment, "stage": stage, "execution": execution.id,
            "required_scopes": sorted(scopes), "required_interfaces": sorted(interfaces),
            "allow_task_closure": closure, "cache_max_age_hours": ttl,
            "human_review_required": quality["human_review_required"], "processes_executed": 0, "writes": []}


def run_packaged(root: Path, entry: dict) -> tuple[dict, dict]:
    # Import the existing exact-profile executor from the plugin, not the consumer.
    sys.path.insert(0, str(ROOT / "skills/lks-sdd-verify/scripts"))
    from run_verification import _profile_command, _execute_profile_command
    if "composition" in entry:
        from v2_composition import command as composition_command
        command = composition_command(root, entry)
    else:
        command = _profile_command(root, entry["binding"], entry["packaged"])
    command["interface_ids"] = [o["interface_id"] for o in entry.get("interface_obligations", [])]
    candidate = command.get("evidence_path")
    old = candidate.read_bytes() if candidate and candidate.is_file() else None
    old_time = candidate.stat().st_mtime_ns if old is not None else None
    environment = dict(os.environ, COMPOSE_PROJECT_NAME="lkssddv2verify" + str(os.getpid()))
    try:
        outcome = _execute_profile_command(command, environment)
    finally:
        from run_verification import _cleanup_profile_compositions
        cleanup = _cleanup_profile_compositions(root, [command], environment) if command.get("requires_containers") else []
    if any(c.get("status") not in {"passed", "not-applicable"} for c in cleanup):
        outcome.update(status="failed", cleanup=cleanup)
    if candidate and outcome["status"] == "passed" and old_time is not None and candidate.stat().st_mtime_ns == old_time:
        outcome.update(status="failed", reason="structured-evidence-not-produced-by-this-run")
    blobs = {}
    if outcome.get("structured_evidence"):
        relative = Path(outcome.pop("structured_evidence")).relative_to(root).as_posix()
        data = read_bytes(root, relative, limit=16 * 1024 * 1024)
        blobs[sha(data)] = data
    log = canonical(outcome)
    blobs[sha(log)] = log
    outcome["artifacts"] = [{"path": "observation-" + digest + ".json", "sha256": digest} for digest in blobs]
    return outcome, blobs


def verify(model: Model, tasks: list[str], environment: str, stage: str, *, evidence_id: str,
           execute: bool = False, containers: bool = False, assessor=None, runner=None) -> dict:
    selection = verification_plan(model, tasks, environment, stage, assessor=assessor)
    if not execute or selection["status"] in {"diagnostic", "blocked"}:
        return selection
    if not re.fullmatch(r"EVID-\d{3,}", evidence_id):
        raise ContractError("New EVID identifier required")
    relative = DOCS + "/evidence/" + evidence_id + ".json"
    if path_at(model.root, relative, missing=True).exists():
        raise ContractError("Evidence is immutable; reuse observations under a new EVID, not overwrite")
    observations, blobs, processes = [], {}, 0
    if not containers and runner is None and any(c["disposition"] == "execute" and
            ("gate" in c or c.get("packaged", {}).get("requires_containers")) for c in selection["checks"]):
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
            observation, artifacts = run_observer(model.root, entry["gate"], entry["input_hashes"], profile_id=selection["technology"]["profile_id"])
        else:
            observation, artifacts = run_packaged(model.root, entry)
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
        "verified-with-reservations" if selection["technology"]["status"] == "approved-project-variant" else "verified")
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
    changes = {**blobs, relative: canonical(value) + b"\n"}
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
        raise ContractError("Technology approval, obligation or verification subject changed")
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
