"""Explicit retention and reversible archival of closed operational records."""
from __future__ import annotations

import json

from v2_contract import ContractError, DOCS, Model, canonical, load, path_at, read_bytes, sha
from v2_lifecycle import ACTIVE_EXECUTION_STATES, timestamp
from v2_storage import apply, preview

RETENTION_STORE = ".lks-sdd/retention.json"
ARCHIVE_ROOT = DOCS + "/00-control/history/operational"
OPERATIONAL_KINDS = frozenset({"authorization", "execution", "checkpoint", "problem", "receipt"})
ACTIVE_RECORD_STATES = frozenset({"active", "in-progress", "in-review", "paused", "blocked", "open"})


def _archive_store(model: Model) -> dict:
    path = path_at(model.root, RETENTION_STORE, missing=True)
    if not path.exists():
        return {"schema_version": "2.0", "records": []}
    try:
        value = json.loads(read_bytes(model.root, RETENTION_STORE, limit=16 * 1024 * 1024))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Retention store is not valid JSON") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "2.0":
        raise ContractError("Retention store has an unsupported schema")
    if not isinstance(value.get("records"), list):
        raise ContractError("Retention store records must be a list")
    return value


def _active_execution_ids(model: Model) -> set[str]:
    return {entry.id for entry in model.by_kind("execution")
            if entry.meta.get("state") in ACTIVE_EXECUTION_STATES}


def _active_task_ids(model: Model) -> set[str]:
    return {entry.id for entry in model.by_kind("task")
            if entry.meta.get("state") not in {"done", "done-with-reservations", "cancelled"}}


def _references_active(model: Model, entry) -> bool:
    active_executions = _active_execution_ids(model)
    active_tasks = _active_task_ids(model)
    if entry.targets("execution") & active_executions:
        return True
    if entry.targets("implements", "authorizes", "affects", "verifies") & active_tasks:
        return True
    if entry.kind == "execution" and entry.id in active_executions:
        return True
    return False


def _eligible(model: Model, entry) -> bool:
    if entry.kind not in OPERATIONAL_KINDS or _references_active(model, entry):
        return False
    state = entry.meta.get("state")
    if state in ACTIVE_RECORD_STATES:
        return False
    if entry.kind == "problem" and state != "resolved":
        return False
    if entry.kind == "authorization" and state not in {"revoked", "expired", "cancelled"}:
        return False
    if entry.kind == "execution" and state in ACTIVE_EXECUTION_STATES:
        return False
    return True


def report(model: Model, task_ids: list[str] | None = None) -> dict:
    """Return a bounded derived view; it never writes a project file."""
    selected = set(task_ids or [])
    if selected and any(task not in model.elements or model.elements[task].kind != "task" for task in selected):
        raise ContractError("Retention scope requires existing TASKs")
    entries = [entry for entry in model.elements.values() if entry.kind in OPERATIONAL_KINDS]
    if selected:
        entries = [entry for entry in entries
                   if entry.targets("implements", "authorizes", "affects", "verifies") & selected
                   or (entry.kind == "execution" and entry.targets("implements") & selected)]
    archived = [item for item in _archive_store(model)["records"] if isinstance(item, dict)]
    archived_ids = {item["id"] for item in archived}
    candidates = [entry for entry in entries if entry.id not in archived_ids and _eligible(model, entry)]
    by_kind = {}
    for entry in entries:
        by_kind[entry.kind] = by_kind.get(entry.kind, 0) + 1
    candidate_paths = [entry.path for entry in candidates]
    return {
        "schema_version": "2.0",
        "status": "ready",
        "scope": sorted(selected),
        "active": {
            "executions": sorted(_active_execution_ids(model)),
            "tasks": sorted(_active_task_ids(model)),
        },
        "records": {"total": len(entries), "by_kind": dict(sorted(by_kind.items()))},
        "archived": {"total": len(archived), "by_kind": {
            kind: sum(1 for item in archived if item.get("kind") == kind)
            for kind in sorted({item.get("kind") for item in archived if item.get("kind")})
        }},
        "candidates": [{"id": entry.id, "kind": entry.kind, "source": entry.path,
                        "state": entry.meta.get("state")} for entry in sorted(candidates, key=lambda item: item.id)],
        "candidate_count": len(candidates),
        "candidate_bytes": sum(len(model.documents.get(path, "").encode("utf-8")) for path in candidate_paths),
        "preserved": ["normative Markdown", "EVID JSON", "active AUTH/EXEC/CKPT", "open PROB", "active references"],
        "writes": [],
    }


def compact(model: Model, task_ids: list[str] | None = None, *, at: str | None = None,
            authorized_hash: str | None = None) -> dict:
    model.require_valid()
    if not at:
        raise ContractError("Retention compact requires explicit --at")
    timestamp(at)
    assessment = report(model, task_ids)
    store = _archive_store(model)
    known = {item["id"] for item in store["records"] if isinstance(item, dict)}
    changes = {}
    records = list(store["records"])
    for candidate in assessment["candidates"]:
        if candidate["id"] in known:
            continue
        source = candidate["source"]
        destination = ARCHIVE_ROOT + "/" + candidate["kind"] + "/" + candidate["id"] + ".md"
        if path_at(model.root, destination, missing=True).exists():
            raise ContractError("Archive destination already exists without a retention entry: " + destination)
        raw = read_bytes(model.root, source, limit=16 * 1024 * 1024)
        changes[source] = None
        changes[destination] = raw
        records.append({"id": candidate["id"], "kind": candidate["kind"], "source": source,
                        "archive": destination, "sha256": sha(raw), "archived_at": at,
                        "state": candidate["state"]})
    changes[RETENTION_STORE] = canonical({"schema_version": "2.0", "records": sorted(records, key=lambda item: item["id"])})
    plan = preview(model.root, changes, sources=model.hashes, operation="compact-closed-operational-records")
    plan["retention"] = assessment
    plan["archived_records"] = [item["id"] for item in records if item["id"] not in known]
    return apply(model.root, changes, plan, authorized_hash,
                  validator=lambda: load(model.root).require_valid()) if authorized_hash else plan


def restore(model: Model, identifiers: list[str], *, authorized_hash: str | None = None) -> dict:
    if not identifiers:
        raise ContractError("Retention restore requires at least one record id")
    store = _archive_store(model)
    selected = [item for item in store["records"] if item.get("id") in set(identifiers)]
    if len(selected) != len(set(identifiers)):
        raise ContractError("Retention store has no exact entry for every requested record")
    changes = {}
    remaining = []
    for item in store["records"]:
        if item.get("id") not in set(identifiers):
            remaining.append(item)
            continue
        raw = read_bytes(model.root, item["archive"], limit=16 * 1024 * 1024)
        if sha(raw) != item.get("sha256"):
            raise ContractError("Archived record integrity mismatch: " + item["id"])
        if path_at(model.root, item["source"], missing=True).exists():
            raise ContractError("Cannot restore over an existing record: " + item["source"])
        changes[item["source"]] = raw
        changes[item["archive"]] = None
    changes[RETENTION_STORE] = canonical({"schema_version": "2.0", "records": remaining})
    plan = preview(model.root, changes, sources=model.hashes, operation="restore-archived-operational-records")
    plan["restored_records"] = sorted(identifiers)
    return apply(model.root, changes, plan, authorized_hash,
                  validator=lambda: load(model.root).require_valid()) if authorized_hash else plan
