"""Compose current task transactions; the existing journal is the retry authority.

Correlation lives in the hashed technical operation name, never in new canonical
states or permissions. Each material stage uses the ordinary fresh core writer.
"""
from pathlib import Path
import base64
import copy
import json

from v3_contract import ContractError, DOCS, HISTORY, INDEX, canonical, fingerprint, load, read_bytes, sha

REQUEST = "lks-sdd-operation-request/1"
RESULT = "lks-sdd-operation-result/1"
OPERATIONS = {"work-continue", "work-record-results"}
CAPABILITY_SOURCES = ("v4_work_operations.py", "v3_cli.py", "lks_sdd.py")
EXCLUDED = (HISTORY + "/", DOCS + "/evidence/", DOCS + "/00-control/migrations/")


def _text(value, name, limit=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ContractError("Missing or invalid " + name)
    return value


def request(root, operation, data):
    root = Path(root).resolve()
    if operation not in OPERATIONS: raise ContractError("Unknown composed work operation")
    if not isinstance(data, dict) or set(data) - {"format", "version", "operation_id", "task", "actor", "basis", "parameters"}:
        raise ContractError("Unknown composed work request fields")
    if data.get("format") != REQUEST or type(data.get("version")) is not int or data["version"] != 1:
        raise ContractError("Unsupported composed work request version")
    for key in ("task", "actor", "operation_id"): _text(data.get(key), key, 256)
    basis = data.get("basis")
    if not isinstance(basis, dict) or set(basis) != {"source_snapshot", "subject", "git", "code_inventory_digest", "state"}:
        raise ContractError("Explicit source, subject, Git, inventory and state basis required")
    if not isinstance(basis["git"], dict) or set(basis["git"]) != {"branch", "head"}:
        raise ContractError("Exact Git branch/head basis required")
    for key in ("source_snapshot", "code_inventory_digest", "state"): _text(basis[key], key, 256)
    if not isinstance(basis["subject"], dict) or set(basis["subject"]) != {"scope", "files", "digest"}:
        raise ContractError("Exact observed subject required")
    params = data.get("parameters")
    allowed = {"action", "reason"} if operation == "work-continue" else {"target", "reason", "evidence"}
    if not isinstance(params, dict) or set(params) - allowed: raise ContractError("Unknown composed work parameters")
    _text(params.get("reason"), "reason")
    if operation == "work-continue":
        if params.get("action") not in {"start", "resume"}: raise ContractError("Only start/resume may continue work")
    else:
        if params.get("target") not in {"implemented", "evidence", "verified", "closed"}:
            raise ContractError("Select a technical result target; integration and acceptance are separate")
        evidence = params.get("evidence", [])
        if not isinstance(evidence, list) or len(evidence) > 20: raise ContractError("At most 20 explicit evidence items")
        for row in evidence:
            if not isinstance(row, dict) or set(row) != {"tests", "outcome", "source", "artifact", "artifact_sha256", "subject", "explanation"}:
                raise ContractError("Exact evidence fields required")
            if not isinstance(row["tests"], list) or not row["tests"] or any(not isinstance(t, str) for t in row["tests"]) or len(row["tests"]) != len(set(row["tests"])):
                raise ContractError("Distinct evidence tests required")
            for test in row["tests"]: _text(test, "test", 256)
            for field in ("artifact", "artifact_sha256", "explanation"): _text(row[field], field)
            if row["outcome"] not in {"passed", "failed", "not-run"} or row["source"] not in {"automated", "human-observation", "external-report"}:
                raise ContractError("Invalid evidence origin/outcome")
            if row["subject"] != basis["subject"]: raise ContractError("Evidence describes another subject")
        if params["target"] == "implemented" and evidence:
            raise ContractError("Evidence would exceed the requested implementation-only goal")
        if params["target"] == "evidence" and not evidence:
            raise ContractError("An evidence goal requires explicit observed evidence")
        params = {**params, "evidence": evidence}
    chosen = {"root": str(root), "operation": operation, "task": data["task"], "actor": data["actor"],
              "basis": copy.deepcopy(basis), "parameters": copy.deepcopy(params)}
    identifier = "wo-" + fingerprint(chosen)
    if data["operation_id"] not in {"auto", identifier}:
        raise ContractError("operation_id conflicts with this exact request; use auto for a new intent")
    return {**chosen, "operation_id": identifier}


def _steps(chosen):
    p = chosen["parameters"]; initial = chosen["basis"]["state"]
    if chosen["operation"] == "work-continue": return [p["action"]]
    ranks = {"in-progress": 0, "implemented": 1, "in-review": 1, "verified": 2}
    if initial not in ranks: raise ContractError("Results require an active technical task, not reopening")
    target = {"implemented": 1, "evidence": 1, "verified": 2, "closed": 3}[p["target"]]
    if ranks[initial] > target: raise ContractError("Target precedes the observed technical state")
    result = ["implement"] if initial == "in-progress" else []
    result += ["evidence:" + str(i) for i in range(len(p["evidence"]))]
    if ranks[initial] < 2 and target >= 2: result.append("verify")
    if ranks[initial] < 3 and target >= 3: result.append("close")
    return result


def _document(path):
    return path == INDEX or (path.startswith(DOCS + "/") and path.endswith(".md") and not path.startswith(EXCLUDED))


def _prefix(step, identifier, number):
    operation = "evidence" if step.startswith("evidence:") else "transition:" + step
    return "v3:" + operation + ":work:" + identifier + ":" + str(number) + ":"


def _tag(packet, step, identifier, number, basis_sources):
    # Only these two mappings change. Do not duplicate the immutable prepared
    # bodies/objects or spool simply to add technical correlation metadata.
    packet = {**packet, "guards": dict(packet["guards"]), "preview": dict(packet["preview"])}
    packet["guards"]["work_basis"] = {"source_hashes": dict(basis_sources), "snapshot": fingerprint(basis_sources)}
    packet["preview"]["operation"] = _prefix(step, identifier, number) + base64.b64encode(canonical(packet["guards"])).decode()
    packet["preview"]["preview_hash"] = fingerprint({k: packet["preview"][k] for k in
        ("operation", "sources", "before", "after", "document_inventory")})
    return packet


def _validate_event(root, journal, chosen, step):
    """A matching label locates a receipt; its actual event must match the intent."""
    from v2_storage import _payload
    from v3_contract import parse
    from v3_inventories import subject as resolve_subject
    expected_kind = "evidence" if step.startswith("evidence:") else "execution"
    events = []
    for path, encoded in journal["after"].items():
        if not _document(path) or path == INDEX or encoded is None: continue
        events += [e for e in parse(_payload(root, journal, encoded), path)[0] if e.kind == expected_kind]
    if len(events) != 1: raise ContractError("Stage receipt does not contain exactly its expected fact")
    event = events[0]; data = event.data
    if data.get("task") != chosen["task"] or data.get("actor", {}).get("member") != chosen["actor"]:
        raise ContractError("Stage receipt belongs to another task or actor")
    if resolve_subject(root, data["subject"]) != chosen["basis"]["subject"]:
        raise ContractError("Stage receipt belongs to another subject")
    if expected_kind == "execution":
        if data.get("action") != step or event.body.strip() != chosen["parameters"]["reason"].strip():
            raise ContractError("Stage receipt describes another transition or reason")
    else:
        row = chosen["parameters"]["evidence"][int(step.split(":")[1])]
        if any(data.get(k) != row[k] for k in ("tests", "source", "outcome", "artifact_sha256")) or data.get("original_path") != row["artifact"] or event.body.strip() != row["explanation"].strip():
            raise ContractError("Stage receipt describes different evidence")
        if sha(read_bytes(root, data["artifact"])) != data["artifact_sha256"]:
            raise ContractError("Stored evidence bytes changed after the recorded stage")


def _receipts(root, chosen, steps):
    from v2_storage import _read_transaction_store, _expand_journal, _load_transaction, TRANSACTION_STORE, PENDING
    rows = {}
    store = _read_transaction_store(root)
    for key, record in store["transactions"].items():
        journal = _expand_journal(root, record)
        operation = journal["preview"]["operation"]
        if (":work:" + chosen["operation_id"] + ":") not in operation: continue
        matches = [i for i, step in enumerate(steps) if operation.startswith(_prefix(step, chosen["operation_id"], i))]
        if len(matches) != 1 or matches[0] in rows: raise ContractError("Conflicting work stage receipts")
        index = matches[0]
        preview = journal["preview"]
        if fingerprint({k: preview[k] for k in ("operation", "sources", "before", "after", "document_inventory")}) != key or preview["preview_hash"] != key:
            raise ContractError("Corrupt work stage receipt")
        if journal["state"] != "completed": raise ContractError("Work stage was rolled back; prepare a new operation")
        _validate_event(root, journal, chosen, steps[index])
        rows[index] = {"stage": steps[index], "preview_hash": key, "receipt": TRANSACTION_STORE, "preview": preview}
    if sorted(rows) != list(range(len(rows))): raise ContractError("Missing preceding work stage receipt")
    pending = None
    if (root / PENDING).exists():
        journal, _ = _load_transaction(root, "", None)
        preview = journal["preview"]
        if (":work:" + chosen["operation_id"] + ":") not in preview["operation"]:
            raise ContractError("Another operation has an interrupted transaction; preserve it")
        pending = {"preview_hash": preview["preview_hash"], "action": "recover-or-rollback", "receipt": PENDING,
                   "reason": "Use the existing explicit journal recovery before retrying; no automatic rollback"}
    return rows, pending


def _expected(chosen, rows):
    if not rows: return None
    def basis(preview):
        guards = json.loads(base64.b64decode(preview["operation"].rsplit(":", 1)[-1], validate=True))
        value = guards["work_basis"]; hashes = value["source_hashes"]
        if fingerprint(hashes) != value["snapshot"] or any(preview["sources"].get(p) != h for p, h in hashes.items()):
            raise ContractError("Work stage basis is not covered by exact sources")
        return hashes
    initial = basis(rows[0]["preview"])
    if fingerprint(initial) != chosen["basis"]["source_snapshot"]:
        raise ContractError("First stage does not match the requested original basis")
    expected = {p: h for p, h in initial.items() if _document(p)}
    for index in sorted(rows):
        preview = rows[index]["preview"]
        observed = {p: h for p, h in basis(preview).items() if _document(p)}
        if observed != expected:
            raise ContractError("Work stage sources are not a continuation of preceding receipts")
        for p, h in preview["after"].items():
            if _document(p):
                if h is None: expected.pop(p, None)
                else: expected[p] = h
    return expected


def _fresh(root, chosen, rows):
    from v3_current import require_current
    from v3_git import observe, code_inventory, subject
    model = require_current(root, {"task": chosen["task"]})
    task = model.get(chosen["task"], "task")
    if task.uid != chosen["task"]: raise ContractError("Use the canonical task UID from work-prepare")
    if task.retired: raise ContractError("Retired task cannot continue")
    lock = json.loads(read_bytes(root, ".lks-sdd/distribution-lock.json", package_data=True))
    for name in CAPABILITY_SOURCES:
        raw = (Path(__file__).parent / name).read_bytes().replace(b"\r\n", b"\n")
        if lock["runtime_files"].get("scripts/" + name) != sha(raw):
            raise ContractError("needs-runtime-update: composed work differs from pinned runtime: " + name)
    expected = _expected(chosen, rows)
    # Referenced object bytes are checked by the normal loader. Their membership
    # follows the exact canonical documents; unreferenced immutable objects carry
    # no authority and may survive interrupted preparation.
    changed = {p:h for p,h in model.hashes.items() if _document(p)} != expected if expected is not None else model.snapshot() != chosen["basis"]["source_snapshot"]
    if changed:
        raise ContractError("Documentary basis changed; preserve applied stages and prepare remaining work on a new basis")
    git = observe(root)
    if {k: git[k] for k in ("branch", "head")} != chosen["basis"]["git"]:
        raise ContractError("Git branch/base changed during composed work")
    if fingerprint(code_inventory(root)) != chosen["basis"]["code_inventory_digest"]:
        raise ContractError("Code/artifact inventory changed during composed work")
    if subject(root, task.data["scope"]) != chosen["basis"]["subject"]:
        raise ContractError("The observed subject changed")
    if not rows:
        from v3_workflow import state
        if state(model, task) != chosen["basis"]["state"]: raise ContractError("Task state differs from requested basis")
    from v3_policy import operator, policy_for
    permission = "implement" if chosen["operation"] == "work-continue" or chosen["parameters"].get("target") == "implemented" or chosen["basis"]["state"] == "in-progress" else "verify"
    identity = operator(model, chosen["actor"], permission, policy_for(model, task))
    if identity["member"] != chosen["actor"]: raise ContractError("Use the canonical actor UID")
    return model, task


def _prepare(root, chosen, step):
    from v3_contract import query_evaluation
    from v3_evaluation import evaluation
    from v3_git import observation_evaluation
    # Only immutable preparation shares calculations. Both physical freshness
    # checks and current=True application remain outside this scope.
    with query_evaluation(), observation_evaluation(root):
        with evaluation(load(root).require_valid()):
            return _prepare_stage(root, chosen, step)


def _prepare_stage(root, chosen, step):
    from v3_workflow import transition
    from v3_verification import evidence
    if step.startswith("evidence:"):
        row = chosen["parameters"]["evidence"][int(step.split(":")[1])]
        if sha(read_bytes(root, row["artifact"])) != row["artifact_sha256"]:
            raise ContractError("Evidence artifact changed or is stale")
        return evidence(root, chosen["actor"], chosen["task"], row["tests"], row["outcome"], row["source"], row["artifact"], row["explanation"])
    # No implicit review, offer acceptance, refresh, reopening or human decision.
    return transition(root, chosen["actor"], chosen["task"], step, chosen["parameters"]["reason"])


def _effect(row):
    return {k: row[k] for k in ("stage", "preview_hash", "receipt")}


def run(root, operation, data, *, apply=False):
    from v4_activity import checkpoint, phase, defer, OperationInterrupted
    root = Path(root).resolve()
    chosen = request(root, operation, data); steps = _steps(chosen)
    value = {"format": RESULT, "version": 1, "operation": operation + "/1", "operation_id": chosen["operation_id"],
             "task": chosen["task"], "actor": chosen["actor"], "basis": chosen["basis"], "status": "blocked",
             "conditions": [], "contract": {"sources": [], "attachments": []}, "effects": [], "writes": [],
             "stages": steps, "diagnostic_ref": None, "next": "Resolve the stated condition; no new authority is granted"}
    rows = {}
    try:
        phase("inspect")
        rows, pending = _receipts(root, chosen, steps)
        value["effects"] = [_effect(rows[i]) for i in sorted(rows)]
        if pending:
            value.update(status="partial", recovery=pending, next=pending["reason"])
            return value
        phase("guard")
        model, task = _fresh(root, chosen, rows)
        from v3_context import context
        value["contract"] = context(root, [task.uid], chosen["parameters"].get("action", "implement"))
        if not value["contract"].get("sources"): raise ContractError("Literal contract is missing")
        if any(a.get("requires_observation") for a in value["contract"].get("attachments", [])):
            raise ContractError("Observe applicable attachments before continuing")
        if not steps:
            value.update(status="completed", next="The requested technical state already existed; no effect attributed to this operation")
            return value
        while len(rows) < len(steps):
            number = len(rows); step = steps[number]
            phase("prepare")
            # The original writer reads current policy, sources and Git while
            # preparing this stage. The independent physical check below binds
            # its result back to this intent before the first material effect.
            packet = _prepare(root, chosen, step)
            # Core preparation observes its own current inputs. Bind those inputs
            # back to this intent before either delivering readiness or writing:
            # a change while preparing must not become one effect before a stop.
            phase("guard")
            model, task = _fresh(root, chosen, rows)
            packet = _tag(packet, step, chosen["operation_id"], number, model.hashes)
            if not apply:
                value.update(status="ready", next_stage={"stage": step, "preview_hash": packet["preview"]["preview_hash"]}, packet=packet,
                             next="Apply only this exact authorized intent; later stages are evaluated after the preceding effect")
                break
            from v3_storage import apply as apply_packet
            phase("apply")
            with defer():
                receipt = apply_packet(root, packet, packet["preview"]["preview_hash"], current=True)
            rows[number] = {**receipt, "stage": step, "preview": packet["preview"]}
            value["effects"] = [_effect(rows[i]) for i in sorted(rows)]
            value["writes"] += receipt.get("writes", [])
            checkpoint()
        else:
            phase("guard")
            model, task = _fresh(root, chosen, rows)
            from v3_workflow import state
            value.update(status="completed", task_state=state(model, task),
                         current_conformance="Journal facts checked; completed receipts grant no future authority. Later transitions recheck quality and expiry.",
                         next="Technical goal recorded; integration, publication and functional acceptance remain separate")
        value["conditions"].append({"rule": "fresh-stage-guards", "satisfied": True,
            "scope": "Each applied or next prepared stage; completed receipts alone do not reauthorize future work"})
    except (OperationInterrupted, ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, OperationInterrupted): value["interruption"] = exc.interruption
        # Re-read durable receipts: an interruption may follow a successful write
        # but precede delivery of its result. Never infer completion from task state.
        try:
            rows, pending = _receipts(root, chosen, steps)
            value["effects"] = [_effect(rows[i]) for i in sorted(rows)]
            if pending: value["recovery"] = pending
        except (ContractError, OSError, ValueError, KeyError, TypeError) as recovery_error:
            value["recovery"] = {"status": "inspection-required", "cause": str(recovery_error)}
        value.update(status="partial" if value["effects"] or value.get("recovery") else "blocked", cause=str(exc))
        value["conditions"].append({"rule": "next-stage", "satisfied": False, "cause": str(exc)})
        value["next"] = "Preserve receipts and later work; resolve this condition before preparing or recovering the remaining stages"
    return value
