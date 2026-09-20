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
RESERVATION_STATUSES = frozenset({"failed", "blocked", "not-run"})
RESERVATION_DECISION = "accept-and-close-with-reservations"


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


def reservation_policy(model: Model) -> dict:
    """Resolve the opt-in exception policy without granting a default waiver."""
    governance = [entry for entry in model.by_kind("decision")
                  if entry.meta.get("category") == "delivery-governance"
                  and entry.meta.get("state") in {"confirmed", "approved"}]
    if len(governance) != 1:
        raise ContractError("A single confirmed delivery governance decision is required")
    value = governance[0].meta.get("verification_reservation_policy")
    if value is None:
        return {"rules": [], "fingerprint": fingerprint([])}
    if not isinstance(value, dict) or not isinstance(value.get("rules"), list):
        raise ContractError("Verification reservation policy must declare rules")
    rules, identifiers = [], set()
    for rule in value["rules"]:
        if not isinstance(rule, dict):
            raise ContractError("Verification reservation rule must be an object")
        identifier = rule.get("id")
        environments, stages = rule.get("environments"), rule.get("stages")
        scopes, statuses = rule.get("gate_scopes"), rule.get("statuses")
        if (not isinstance(identifier, str) or not re.fullmatch(r"RES-POL-\d{3,}", identifier)
                or identifier in identifiers or not isinstance(environments, list) or not environments
                or not all(isinstance(item, str) and item for item in environments)
                or not isinstance(stages, list) or not set(stages) <= set(STAGES)
                or not isinstance(scopes, list) or not scopes or not set(scopes) <= {"component", "contract", "composition", "user-flow", "persistence", "visual"}
                or not isinstance(statuses, list) or not statuses or not set(statuses) <= RESERVATION_STATUSES):
            raise ContractError("Invalid verification reservation policy rule")
        identifiers.add(identifier)
        rules.append({"id": identifier, "environments": sorted(set(environments)), "stages": sorted(set(stages)),
                      "gate_scopes": sorted(set(scopes)), "statuses": sorted(set(statuses))})
    return {"rules": sorted(rules, key=lambda rule: rule["id"]), "fingerprint": fingerprint(sorted(rules, key=lambda rule: rule["id"]))}


def _reservation_rule(policy: dict, environment: str, stage: str, check: dict, status: str) -> str | None:
    scopes = set(check.get("scopes", check.get("gate", {}).get("scopes", [])))
    for rule in policy["rules"]:
        if (environment in rule["environments"] and stage in rule["stages"] and status in rule["statuses"]
                and scopes and scopes <= set(rule["gate_scopes"])):
            return rule["id"]
    return None


def _reservation_eligible(check: dict) -> bool:
    """Only availability failures may turn a blocked observer into a reservation."""
    if check.get("status") != "blocked":
        return True
    reason = str(check.get("reason", ""))
    return reason.startswith(("Observer process unavailable:", "Observer timed out"))


def materialize_reservations(model: Model, tasks: list[str], environment: str, stage: str,
                             checks: list[dict], reservations) -> list[dict]:
    """Bind explicit reservation claims to actual, policy-permitted observations."""
    if any(model.elements[task].meta.get("critical") for task in tasks):
        raise ContractError("Critical TASK verification cannot close with reservations")
    if not isinstance(reservations, list) or not reservations:
        raise ContractError("At least one explicit reservation is required")
    policy = reservation_policy(model)
    observations = {check.get("gate_id"): check for check in checks if check.get("required")}
    materialized, identifiers, gates = [], set(), set()
    for item in reservations:
        if not isinstance(item, dict):
            raise ContractError("Reservation must be an object")
        identifier, gate = item.get("id"), item.get("gate_id")
        reason, follow_up = item.get("reason"), item.get("follow_up")
        if (not isinstance(identifier, str) or not re.fullmatch(r"RES-\d{3,}", identifier) or identifier in identifiers
                or not isinstance(gate, str) or not gate or gate in gates
                or not isinstance(reason, str) or not reason.strip()
                or not isinstance(follow_up, str) or not follow_up.strip()):
            raise ContractError("Reservation needs unique id, gate, reason and follow-up")
        check = observations.get(gate)
        if not check or check.get("status") not in RESERVATION_STATUSES:
            raise ContractError("Reservation must reference an observed failed, blocked or not-run required gate: " + str(gate))
        if not _reservation_eligible(check):
            raise ContractError("Reservation cannot waive this observer integrity or isolation failure: " + gate)
        rule = _reservation_rule(policy, environment, stage, check, check["status"])
        if rule is None:
            raise ContractError("No reservation policy permits this gate outcome: " + gate)
        identifiers.add(identifier)
        gates.add(gate)
        materialized.append({"id": identifier, "gate_id": gate, "status": check["status"],
                             "reason": reason.strip(), "follow_up": follow_up.strip(), "policy_rule_id": rule})
    return sorted(materialized, key=lambda item: item["id"])


def _reservation_gaps(value: dict, reservations: list[dict]) -> list[str]:
    """Return technical gaps not covered by reservations; never treat them as passes."""
    reserved_gates = {item["gate_id"] for item in reservations}
    check_by_gate = {check.get("gate_id"): check for check in value["checks"]}
    non_passing = {gate for gate, check in check_by_gate.items()
                   if check.get("required") and check.get("status") != "passed"}
    gaps = sorted(non_passing - reserved_gates)
    reserved_scopes = {scope for gate in reserved_gates for scope in check_by_gate[gate].get("scopes", [])}
    reserved_interfaces = {interface for gate in reserved_gates
                           for interface in check_by_gate[gate].get("interfaces", [])}
    gaps.extend("scope:" + scope for scope in value.get("missing_scopes", []) if scope not in reserved_scopes)
    gaps.extend("interface:" + interface for interface in value.get("missing_interfaces", [])
                if interface not in reserved_interfaces)
    gate_failures = {check.get("gate_id") for check in value["checks"]
                     if check.get("required") and check.get("status") != "passed"}
    gaps.extend("failure:" + item for item in value.get("failures", []) if item not in gate_failures)
    return sorted(set(gaps))


def reservation_acceptance(model: Model, tasks: list[str], value: dict, request: dict) -> tuple[list[dict], str]:
    """Validate an explicit human reservation decision against immutable evidence."""
    if not isinstance(request, dict) or request.get("decision") != RESERVATION_DECISION:
        raise ContractError("Reservation closure requires the explicit accept-and-close-with-reservations decision")
    reservations = materialize_reservations(
        model, tasks, value["environment"], value["stage"], value["checks"], request.get("reservations")
    )
    if value.get("reservations") and reservations != value["reservations"]:
        raise ContractError("Reservation acceptance differs from the exact verification evidence")
    gaps = _reservation_gaps(value, reservations)
    if gaps:
        raise ContractError("Reservations do not cover all technical gaps: " + ", ".join(gaps))
    return reservations, fingerprint(reservations)


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
    policy = reservation_policy(model)
    material = {"project": model.manifest["project_id"], "tasks": sorted(tasks), "files": guard["files"],
                "contract": authorization["fingerprint"], "environment": environment, "technology": technology,
                "engine": engine_hash(), "interfaces": sorted(interfaces), "scopes": sorted(scopes),
                "observers": [check["definition"] for check in checks],
                "reservation_policy": policy["fingerprint"]}
    return {"status": "blocked" if missing or observer_blockers else "planned", "missing_critical_gates": missing,
            "blockers": observer_blockers, "checks": checks, "subject": fingerprint(material), "material": material, "technology": technology,
            "task_ids": tasks, "environment": environment, "stage": stage, "execution": execution.id,
            "required_scopes": sorted(scopes), "required_interfaces": sorted(interfaces),
            "required_gates": sorted(required),
            "allow_task_closure": not missing and not observer_blockers, "cache_max_age_hours": 0,
            "human_review_required": quality["human_review_required"], "processes_executed": 0, "writes": []}


def _blocked_observations(selection: dict) -> list[dict]:
    checks = {check["gate_id"]: check for check in selection["checks"]}
    observations = []
    for gate_id in selection["required_gates"]:
        check = checks.get(gate_id)
        reasons = [blocker for blocker in selection["blockers"] if gate_id in blocker]
        reason = "; ".join(reasons) if reasons else "Required gate cannot run because verification planning is blocked"
        observations.append({
            "gate_id": gate_id,
            "status": "not-run" if check else "blocked",
            "disposition": "omitted",
            "observed_at": now(),
            "reason": reason,
            "scopes": check["gate"]["scopes"] if check else [],
            "interfaces": check["gate"]["interfaces"] if check else [],
            "required": True,
            "input_key": check["input_key"] if check else fingerprint(
                {"subject": selection["subject"], "gate_id": gate_id, "reason": reason}
            ),
        })
    return observations


def _current_selection(model: Model, tasks: list[str], selection: dict) -> Model:
    fresh = load(model.root)
    fresh.require_valid()
    refreshed = verification_plan(fresh, tasks, selection["environment"], selection["stage"])
    if refreshed["subject"] != selection["subject"] or refreshed["execution"] != selection["execution"]:
        raise ContractError("Verification subject changed before evidence could be recorded")
    return fresh


def _record_evidence(model: Model, fresh: Model, selection: dict, tasks: list[str], evidence_id: str,
                     observations: list[dict], blobs: dict[str, bytes], processes: int, *,
                     reservations=None, blocked_preflight=False) -> dict:
    reservations = reservations or []
    passed = [observation for observation in observations if observation["status"] == "passed"]
    scopes = {scope for observation in passed for scope in observation["scopes"]}
    interfaces = {interface for observation in passed for interface in observation["interfaces"]}
    failures = [observation["gate_id"] for observation in observations
                if observation["required"] and observation["status"] != "passed"]
    missing_scopes = sorted(set(selection["required_scopes"]) - scopes)
    missing_interfaces = sorted(set(selection["required_interfaces"]) - interfaces)
    from v2_quality import visual_coverage_errors
    visual_errors = visual_coverage_errors(fresh, tasks, observations)
    failures.extend(visual_errors)
    candidate = {
        "checks": observations,
        "failures": failures,
        "missing_scopes": missing_scopes,
        "missing_interfaces": missing_interfaces,
    }
    unresolved = _reservation_gaps(candidate, reservations)
    classification = "not-verified" if unresolved else (
        "verified-with-reservations" if reservations else "verified"
    )
    value = {"schema_version": "2.0", "evidence_id": evidence_id, "recorded_at": now(),
             "subject": selection["subject"], "material": selection["material"],
             "task_ids": tasks, "execution_id": selection["execution"], "environment": selection["environment"],
             "stage": selection["stage"], "workspace_revision": "workspace-sha256:" + fingerprint(selection["material"]["files"]),
             "build_id": "observation-set-sha256:" + fingerprint(sorted({artifact["sha256"] for observation in observations
                                                                           for artifact in observation.get("artifacts", [])})),
             "artifact_digests": sorted({artifact["sha256"] for observation in observations
                                         for artifact in observation.get("artifacts", [])}),
             "deliverable_artifact_digests": sorted({artifact["sha256"] for observation in observations if observation["status"] == "passed"
                 for artifact in observation.get("observations", {}).get("build_artifacts", []) if artifact.get("kind") == "deployable"
                 and any(artifact.get("path") == bound.get("path") and artifact.get("sha256") == bound.get("sha256")
                         for bound in observation.get("artifacts", []))}),
             "cache_max_age_hours": selection["cache_max_age_hours"],
             "human_review_required": selection["human_review_required"],
             "definition_refs": [{"id": entry.id, "uid": entry.meta["uid"], "revision": entry.meta["revision"],
                                  "normative_sha256": fingerprint(entry.normative()), "source": entry.source()}
                                 for entry in fresh.by_kind("feature")
                                 if any(entry.id in fresh.elements[task].targets("implements", "contributes_to") for task in tasks)],
             "contract_source_hashes": {path: digest for path, digest in fresh.hashes.items() if path.startswith(DOCS + "/")
                                       and "/evidence/" not in path and "/history/" not in path},
             "checks": observations, "classification": classification, "allow_task_closure": selection["allow_task_closure"],
             "failures": failures, "unresolved_failures": unresolved, "missing_scopes": missing_scopes,
             "missing_interfaces": missing_interfaces, "reservations": reservations,
             "blocked_preflight": blocked_preflight,
             "build_identity_kind": "observation-set-not-deployment-proof",
             "delivery": "not-assessed", "human_acceptance": "not-assessed"}
    value["integrity_sha256"] = fingerprint(value)
    from v2_schema import validate
    validate("verification-evidence", value)
    evidence_relative = DOCS + "/evidence/" + evidence_id + ".json"
    changes = {**blobs, evidence_relative: canonical(value) + b"\n"}
    plan = preview(model.root, changes, sources=fresh.hashes, operation="record-verification")
    applied = apply(model.root, changes, plan, plan["preview_hash"])
    return {"status": classification, "evidence_id": evidence_id, "processes_executed": processes,
            "checks": observations, "writes": applied["writes"], "delivery": "not-assessed",
            "blocked_preflight": blocked_preflight}


def verify(model: Model, tasks: list[str], environment: str, stage: str, *, evidence_id: str,
           execute: bool = False, containers: bool = False, assessor=None, runner=None,
           reservation_request: dict | None = None) -> dict:
    model.require_valid()
    selection = verification_plan(model, tasks, environment, stage, assessor=assessor)
    if not execute or selection["status"] == "diagnostic":
        return selection
    if not re.fullmatch(r"EVID-\d{3,}", evidence_id):
        raise ContractError("New EVID identifier required")
    evidence_relative = DOCS + "/evidence/" + evidence_id + ".json"
    if path_at(model.root, evidence_relative, missing=True).exists():
        raise ContractError("Evidence is immutable; reuse observations under a new EVID, not overwrite")
    if selection["status"] == "blocked":
        fresh = _current_selection(model, tasks, selection)
        return _record_evidence(
            model, fresh, selection, tasks, evidence_id, _blocked_observations(selection), {}, 0,
            blocked_preflight=True,
        )
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
    reservations = []
    if reservation_request is not None:
        if not isinstance(reservation_request, dict) or "reservations" not in reservation_request:
            raise ContractError("Verification reservation request requires explicit reservations")
        reservations = materialize_reservations(
            fresh, tasks, environment, stage, observations, reservation_request["reservations"]
        )
    # --execute --evidence-id explicitly authorizes recording this actual run.
    return _record_evidence(model, fresh, selection, tasks, evidence_id, observations, blobs, processes,
                            reservations=reservations)


def _accepted_reservation_receipt(model: Model, tasks: list[str], value: dict) -> dict | None:
    for receipt in model.by_kind("receipt"):
        if (receipt.meta.get("category") != "result-reservation-review" or receipt.meta.get("state") != "approved"
                or receipt.meta.get("evidence_id") != value["evidence_id"]
                or receipt.meta.get("evidence_sha256") != value["integrity_sha256"]
                or receipt.meta.get("technical_classification") != value["classification"]
                or not set(tasks) <= receipt.targets("verifies")):
            continue
        reservations = receipt.meta.get("reservations")
        if not isinstance(reservations, list) or receipt.meta.get("reservation_digest") != fingerprint(reservations):
            continue
        if value.get("reservations") and reservations != value["reservations"]:
            continue
        if not _reservation_gaps(value, reservations):
            return receipt.meta
    return None


def close(model: Model, tasks: list[str], evidence_id: str, *, actor: str, at: str,
          authorized_hash: str | None = None, reservation_request: dict | None = None,
          reason: str = "") -> dict:
    value = evidence(model, evidence_id)
    final_states = {"done", "done-with-reservations"}
    if (all(model.elements.get(task) and model.elements[task].kind == "task"
            and model.elements[task].meta["state"] in final_states for task in tasks)
            and all(evidence_id in model.elements[task].meta.get("evidence_ids", []) for task in tasks)):
        return {"status": "already-closed", "task_ids": sorted(tasks), "evidence_id": evidence_id, "writes": []}
    execution = active_execution(model, tasks)
    auth = current_authorization(model, tasks, value["environment"])
    guard = diff_guard(model, execution)
    if (not set(tasks) <= set(value["task_ids"]) or value["execution_id"] != execution.id
            or value["classification"] not in {"verified", "verified-with-reservations", "not-verified"}
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
    receipt_id, receipt_changes = None, {}
    reservations = []
    if reservation_request is not None:
        if not reason.strip():
            raise ContractError("Explicit acceptance reason is required")
        decision = reservation_request.get("decision") if isinstance(reservation_request, dict) else None
        if value["classification"] == "verified":
            if decision != "accept-and-close" or reservation_request.get("reservations") not in (None, []):
                raise ContractError("Verified evidence requires the explicit accept-and-close decision without reservations")
            from v2_controls import receipt_record
            receipt_id, receipt_changes = receipt_record(model, "result-review", reason, {
                "actor": actor, "recorded_at": at, "state": "approved", "evidence_id": evidence_id,
                "evidence_sha256": value["integrity_sha256"], "technical_classification": value["classification"],
                "identity_assurance": "declared-not-authenticated", "relations": {"verifies": tasks},
            })
        else:
            reservations, reservation_digest = reservation_acceptance(model, tasks, value, reservation_request)
            from v2_controls import receipt_record
            receipt_id, receipt_changes = receipt_record(model, "result-reservation-review", reason, {
                "actor": actor, "recorded_at": at, "state": "approved", "evidence_id": evidence_id,
                "evidence_sha256": value["integrity_sha256"], "technical_classification": value["classification"],
                "execution_id": value["execution_id"], "subject": value["subject"], "reservations": reservations,
                "reservation_digest": reservation_digest, "identity_assurance": "declared-not-authenticated",
                "relations": {"verifies": tasks},
            })
    elif value["classification"] != "verified":
        accepted = _accepted_reservation_receipt(model, tasks, value)
        if not accepted:
            raise ContractError("Explicit reservation acceptance remains pending")
        reservations = accepted["reservations"]
    if value["classification"] == "verified" and value.get("human_review_required") and not (
            receipt_id or review_satisfied(model, tasks, value)):
        raise ContractError("Exact-result human/visual acceptance remains pending")
    identifier = next_id(model, "CKPT")
    completion = "with accepted reservations" if value["classification"] != "verified" else "verified"
    path, data = record(model, identifier, "checkpoint", "Verificación del trabajo", "Evidencia: " + evidence_id + ". Entrega y aceptación humana independientes.",
                        state="active", actor=actor, recorded_at=at, next_action="Revisar condiciones de entrega",
                        files=guard["files"], evidence_ids=[evidence_id], completion=completion,
                        reservations=reservations, acceptance_receipt_id=receipt_id,
                        relations={"execution": [execution.id], "implements": tasks})
    task_state = "done-with-reservations" if value["classification"] != "verified" else "done"
    health = "accepted-with-reservations" if task_state == "done-with-reservations" else "verified"
    updates = {task: dict(model.elements[task].meta, state=task_state, health=health,
                          evidence_ids=[*model.elements[task].meta.get("evidence_ids", []), evidence_id])
               for task in tasks}
    if set(tasks) == execution.targets("implements"):
        updates[execution.id] = dict(execution.meta, state="completed", completion=completion)
    for problem in model.by_kind("problem"):
        if problem.targets("affects") <= set(tasks) and problem.meta["state"] != "resolved":
            if any(timestamp(c["observed_at"]) <= timestamp(problem.meta["recorded_at"])
                   for c in value["checks"] if c.get("required")):
                raise ContractError("Problem requires evidence observed after the finding")
            updates[problem.id] = dict(problem.meta, state="resolved", evidence_id=evidence_id)
    changes = {path: data, **receipt_changes, **edit_elements(model, updates)}
    operation = "complete-task-with-reservations" if task_state == "done-with-reservations" else "complete-verified-task"
    plan = preview(model.root, changes, sources=model.hashes, operation=operation)
    return apply(model.root, changes, plan, authorized_hash) if authorized_hash else plan
