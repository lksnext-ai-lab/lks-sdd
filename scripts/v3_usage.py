"""Bounded usage observations; diagnostic facts never confer project authority."""
from __future__ import annotations

import copy
from contextlib import contextmanager
from contextvars import ContextVar
import json
from pathlib import Path
import time
import uuid
from functools import lru_cache

from v3_contract import ContractError, canonical, element, fingerprint, load, sha

FORMAT = "lks-sdd-usage/1"
BATCH_BYTES = 1024 * 1024
BATCH_COUNT = 1000
WINDOW_COUNT = 20000
FRAGMENT_BYTES = 64 * 1024
STAGES = {"query", "prepared", "applied", "failed", "declared"}
SESSION = ContextVar("usage_session", default=None)
TRUSTED = {}  # Same-process observations only. An imported claim is not attestation.


def diagnostic(e):
    return e.kind == "receipt" and e.data.get("purpose") == "usage-observation"


@lru_cache(maxsize=3)
def validator(name):
    from jsonschema import Draft202012Validator
    schema = json.loads((Path(__file__).resolve().parents[1]/"schemas"/(name + "-1.0.schema.json")).read_bytes())
    return Draft202012Validator(schema)


def validate(value, name):
    errors = sorted(validator(name).iter_errors(value), key=lambda e: str(e.path))
    if errors: raise ContractError("Invalid " + name + ": " + errors[0].message)
    if name == "usage-observation":
        for fragment in value["fragments"]: check_fragment(fragment)
    return value


def check_fragment(f, raw=None):
    if sum(k in f for k in ("text","text_ref","data_ref")) > 1: raise ContractError("Ambiguous inline/reference fragment")
    if f["end"] < f["start"]: raise ContractError("Invalid fragment interval")
    if f.get("unit") == "bytes" and (f["end"] - f["start"] != f["bytes"] or "text" in f or "text_ref" in f):
        raise ContractError("Invalid binary fragment interval/encoding")
    if "data_ref" in f and f.get("unit") != "bytes": raise ContractError("Binary reference needs byte units")
    ref = f.get("text_ref",f.get("data_ref"))
    if ref is not None and (ref["sha256"] != f["sha256"] or ref["bytes"] != f["bytes"]): raise ContractError("Usage fragment reference mismatch")
    if "text" in f: raw = f["text"].encode("utf-8")
    if raw is not None:
        if sha(raw) != f["sha256"] or len(raw) != f["bytes"]: raise ContractError("Fragment bytes mismatch")
        try: length = len(raw) if f.get("unit") == "bytes" else len(raw.decode("utf-8"))
        except UnicodeDecodeError as exc: raise ContractError("Invalid text fragment encoding") from exc
        if length != f["end"] - f["start"]: raise ContractError("Usage fragment interval mismatch")


def check_batch(observations):
    if not isinstance(observations, list) or len(observations) > BATCH_COUNT:
        raise ContractError("Usage batch exceeds 1000 observations; paginate")
    if len(canonical({"format":FORMAT,"observations":observations})) > BATCH_BYTES:
        raise ContractError("Usage batch exceeds 1 MiB; reduce the case or paginate")
    seen = {}
    for row in observations:
        validate(row, "usage-observation")
        key = row["observation_id"]
        if key in seen and seen[key] != fingerprint(row): raise ContractError("Observation ID collision")
        seen[key] = fingerprint(row)
    return observations


def runtime_info():
    base = Path(__file__).resolve().parents[1]
    manifest = base/".codex-plugin/plugin.json"
    return {"plugin_version": json.loads(manifest.read_bytes())["version"] if manifest.exists() else "unknown",
            "method_version": "3.1.0", "revision": sha(Path(__file__).read_bytes()),
            "revision_scope":"v3_usage.py bytes; content identity, not Git commit attestation",
            "components":{p:sha((base/"scripts"/p).read_bytes()) for p in ("v3_cli.py","v3_context.py","v3_storage.py","usage_findings.py","usage_report.py","usage_bundle.py")},
            "python": __import__("sys").version.split()[0]}


def logical(value):
    """Remove only transport tracing; contractual digests and inputs stay intact."""
    if isinstance(value, dict):
        return {k: copy.deepcopy(v) for k, v in value.items() if k not in {"usage", "usage_context", "diagnostic_overhead"}}
    return copy.deepcopy(value)


def fragments(result):
    if result.get("format")=="lks-sdd-operation-result/1":result=result.get("contract",{})
    rows, budget = [], BATCH_BYTES // 2
    for source in result.get("sources", []) + result.get("attachments", []):
        text = source.get("text")
        if not isinstance(text, str):
            if source.get("requires_observation") and source.get("sha256"):
                rows.append({"source":source["path"],"revision":source["sha256"],"locator":"asset","unit":"bytes", "start":0,
                             "end":source["bytes"],"sha256":source["sha256"],"bytes":source["bytes"],"gap":"Binary asset bytes must be conserved before changing the source"})
            if len(rows) >= 1000: break
            continue
        raw = text.encode("utf-8")
        identity = source.get("source", {})
        row = {"source": source.get("key") or source.get("path") or identity.get("path", "unknown"),
               "revision": identity.get("digest") or identity.get("sha256") or source.get("sha256") or sha(raw),
               "locator": "body", "start": 0, "end": len(text), "sha256": sha(raw), "bytes": len(raw)}
        if len(raw) <= FRAGMENT_BYTES and len(raw) <= budget:
            row["text"] = text; budget -= len(raw)
        else: row["gap"] = "Exact bytes exceed transient budget; attach source before exporting as ready"
        rows.append(row)
        if len(rows) >= 1000: break
    return rows


def observe(action, data, result, *, context=None, elapsed=None, stage=None, root=None, invocation_id=None):
    diagnostic_start = time.monotonic()
    context = context or {}
    tasks = context.get("tasks", data.get("tasks", [data["task"]] if data.get("task") else []))
    request = context.get("request", data.get("request"))
    gaps = list(context.get("gaps", []))
    if root is not None and (request or tasks):
        try:
            model = load(root).require_valid()
            if request: request = model.get(request, "request").uid
            tasks = [model.get(t,"task").uid for t in tasks]
            if request and any(model.get(t).data["request"] != request for t in tasks): raise ContractError("Usage task outside request")
        except (ContractError, TypeError, KeyError, ValueError):
            request, tasks = None, []
            gaps.append("Work binding could not be validated; input references retained as data only")
    run = context.get("run_id") or "provisional-" + str(uuid.uuid4())
    stage = stage or ("failed" if result.get("status") in {"blocked", "unsupported", "reconciliation-required"}
                      else "prepared" if "preview" in result else "query")
    raw = canonical(logical(result))
    row = {"format": FORMAT, "observation_id": str(uuid.uuid4()), "run_id": run,
           "invocation_id": invocation_id or str(uuid.uuid4()),
           "binding": {"request": request, "tasks": sorted(set(tasks)), "state": "linked" if request or tasks else "provisional"},
           "phase": context.get("phase", action), "operation": action, "stage": stage,
           "window_state": context.get("window_state", "blocked" if stage == "failed" else "in-progress" if request or tasks else "provisional"),
           "gaps": gaps,
           "origin": {"kind": "runtime-derived", "mechanism": "shared-api", "assurance": "same-process-observed"},
           "runtime": runtime_info(), "input": copy.deepcopy(logical(data)), "result_digest": sha(raw),
           "result": {k: copy.deepcopy(result[k]) for k in ("status", "cause", "causes", "next", "widened", "scope_provenance", "sufficiency", "selection_digest", "snapshot") if k in result},
           "fragments": fragments(result), "metrics": {
               "prepared_bytes": {"value": len(raw), "unit": "bytes", "method": "canonical JSON UTF-8", "coverage": "shared API result", "status": "measured"},
               "elapsed": {"value": elapsed, "unit": "seconds", "method": "monotonic same process", "coverage": "shared API call", "status": "measured" if elapsed is not None else "absent"},
               "billed_tokens": {"value": None, "unit": "tokens", "method": "host unavailable", "coverage": "absent", "status": "absent"}}}
    if result.get("format")=="lks-sdd-operation-result/1":
        literal=result.get("contract",{})
        row["result"].update({k:copy.deepcopy(literal[k]) for k in ("roots","widened","scope_provenance","sufficiency","selection_digest","snapshot") if k in literal})
    preview = result.get("preview", {})
    if preview.get("preview_hash"): row["preview_hash"] = preview["preview_hash"]
    if stage == "applied":
        row["application"] = {"status":result.get("status"),"receipt":result.get("receipt"),
                              "preview_hash":preview.get("preview_hash",result.get("preview_hash")),
                              "current_conformance":result.get("current_conformance","journal result only")}
    if stage == "failed":
        if len(raw) <= 128*1024:
            row["result"]["exact"] = logical(result)
            if not row["result"].get("cause") and not row["result"].get("causes"): row["result"]["causes"] = logical(result)
        else: row["result"]["gap"] = "Exact failure result exceeds transient budget; attach it before claiming readiness"
    if len(canonical(row)) > BATCH_BYTES // 2:
        row["input"] = {"digest": fingerprint(data), "gap": "Input too large; exact input required as attachment"}
        row["fragments"] = []
        row["result"] = {"status": result.get("status"), "gap": "Result exceeds observation budget; exact result required"}
    row["metrics"]["collection"] = {"value":time.monotonic()-diagnostic_start,"unit":"seconds","method":"monotonic same process",
                                    "coverage":"envelope preparation only; validation and conservation measured separately", "status":"measured"}
    validate(row, "usage-observation")
    TRUSTED[row["observation_id"]] = fingerprint(row)
    if len(TRUSTED) > BATCH_COUNT: TRUSTED.pop(next(iter(TRUSTED)))
    return row


def imported(row, *, external=False):
    row = copy.deepcopy(row)
    if not external and TRUSTED.get(row["observation_id"]) == fingerprint(row): return row
    if row["origin"].get("assurance") == "unverified-import" and row["origin"].get("kind") == "agent-declared": return row
    claimed = {k:row["origin"][k] for k in ("kind","mechanism","assurance")}
    row["origin"] = {"kind": "agent-declared", "mechanism": "imported-envelope", "assurance": "unverified-import", "claimed":claimed}
    for metric in row["metrics"].values():
        if metric["status"] == "measured": metric["claimed_status"] = "measured"; metric["status"] = "declared"
    return row


@contextmanager
def session(context, data):
    if not isinstance(context, dict): raise ContractError("usage_context must be an object")
    context = copy.deepcopy(context or {})
    check_batch(context.get("observations", []))
    value = {"context": context, "data": data, "consumed": False}
    token = SESSION.set(value)
    try: yield value
    finally: SESSION.reset(token)


def early(payload, action, data=None, *, context=None):
    """Dispatcher/runtime failures have the same exportable transient boundary."""
    result = dict(payload)
    failure = {"status":"blocked", "cause":str(payload.get("cause") or payload.get("error") or payload.get("errors") or "Early runtime failure")}
    row = observe(action, data or {}, failure, stage="failed", context=context)
    from usage_report import report
    value = report([row])
    result["usage"] = {"observations":[row], "summary":value["summary"], "prompt":value["prompt"]}
    return result


def catalog(model, *, run_id=None, request=None, task=None):
    from content_store import read_object
    rows, seen, declared_bytes = [], {}, 0
    receipts = [e for e in model.by_kind("receipt") if diagnostic(e)]
    # Budget before resolving references, not after allocation.
    bound_runs = {e.data["run_id"] for e in receipts if (not request or e.data.get("request") == request)
                  and (not task or task in e.data.get("tasks", []))}
    selected = [e for e in receipts if (not run_id or e.data.get("run_id") == run_id)
                and (not (request or task) or e.data["run_id"] in bound_runs)]
    if sum(e.data["count"] for e in selected) > WINDOW_COUNT:
        raise ContractError("Usage window exceeds 20000 observations; select a run")
    for e in selected:
        declared_bytes += e.data["observations_ref"]["bytes"]
        if declared_bytes > 64 * 1024 * 1024: raise ContractError("Usage window exceeds 64 MiB; select a run")
        value = json.loads(read_object(model.root, e.data["observations_ref"]))
        for row in value["observations"]:
            key = row["observation_id"]
            if key in seen and seen[key] != fingerprint(row): raise ContractError("Observation ID collision")
            if key not in seen: rows.append(row); seen[key] = fingerprint(row)
    return rows


def validate_receipt(model, e, *, objects=None):
    from content_store import object_path, read_object
    data = e.meta["data"]
    if type(data.get("count")) is not int or not 0 <= data["count"] <= BATCH_COUNT: raise ContractError("Invalid usage count")
    budget = getattr(model,"_usage_run_budget",{})
    model._usage_run_budget = budget
    ref = data.get("observations_ref")
    name = object_path(ref)
    batch_digest = ref["sha256"]
    if ref["bytes"] > BATCH_BYTES: raise ContractError("Usage object exceeds 1 MiB")
    count, size = budget.get(data.get("run_id"),(0,0))
    if count + data["count"] > WINDOW_COUNT or size + ref["bytes"] > 64*1024*1024: raise ContractError("Usage run exceeds aggregate budget")
    budget[data.get("run_id")] = (count + data["count"],size + ref["bytes"])
    raw = objects[name] if objects is not None and name in objects else read_object(model.root, ref)
    if sha(raw) != ref["sha256"] or len(raw) != ref["bytes"]: raise ContractError("Usage object integrity mismatch")
    value = json.loads(raw)
    if set(value) != {"format", "observations"} or value["format"] != FORMAT: raise ContractError("Unsupported usage object")
    check_batch(value["observations"])
    if data.get("observation_ids") != [r["observation_id"] for r in value["observations"]]: raise ContractError("Usage observation ID index mismatch")
    cache = getattr(model, "_usage_object_cache", {})
    model._usage_object_cache = cache
    for row in value["observations"]:
        for f in row["fragments"]:
            ref = f.get("text_ref",f.get("data_ref"))
            if ref is None: continue
            path = object_path(ref)
            if ref["sha256"] != f["sha256"] or ref["bytes"] != f["bytes"]:
                raise ContractError("Usage fragment reference mismatch")
            run_refs = getattr(model,"_usage_run_refs",{})
            model._usage_run_refs = run_refs
            refs = run_refs.setdefault(data["run_id"],{})
            if path not in refs and sum(refs.values()) + ref["bytes"] > 64*1024*1024: raise ContractError("Usage source material exceeds aggregate budget")
            refs[path] = ref["bytes"]
            if path not in cache:
                raw_fragment = objects[path] if objects is not None and path in objects else read_object(model.root,ref)
                if sha(raw_fragment) != ref["sha256"] or len(raw_fragment) != ref["bytes"]: raise ContractError("Usage fragment integrity mismatch")
                try: characters = len(raw_fragment.decode("utf-8"))
                except UnicodeDecodeError: characters = None
                cache[path] = (ref["bytes"],characters)
            elif cache[path][0] != ref["bytes"]: raise ContractError("Conflicting usage fragment size")
            length = cache[path][0 if f.get("unit") == "bytes" else 1]
            if length is None or length != f["end"] - f["start"]: raise ContractError("Usage fragment interval mismatch")
            model.hashes[path] = ref["sha256"]
    if data.get("count") != len(value["observations"]): raise ContractError("Usage count mismatch")
    if any(r["run_id"] != data.get("run_id") or r["binding"]["request"] != data.get("request")
           or r["binding"]["tasks"] != data.get("tasks") for r in value["observations"]): raise ContractError("Usage binding mismatch")
    model.hashes[name] = batch_digest


def additions(root, observations, actor=None, *, materials=None):
    """Idempotent append via the existing journal and immutable object store."""
    from content_store import prepare_object, read_object
    check_batch(observations)
    model = load(root).require_valid()
    if actor: model.get(actor, "member")
    existing = {r["observation_id"]: r for run in {r["run_id"] for r in observations} for r in catalog(model, run_id=run)}
    groups, seen, changes = {}, {}, {}
    def unpack(row):
        row = copy.deepcopy(row)
        for f in row["fragments"]:
            if "transient_gap" in f:
                f.pop("text_ref",None); f.pop("data_ref",None); f["gap"] = f.pop("transient_gap")
            elif "text_ref" in f and f["bytes"] <= FRAGMENT_BYTES: f["text"] = read_object(root,f.pop("text_ref")).decode("utf-8")
        return row
    def pack(row):
        row = copy.deepcopy(row)
        for f in row["fragments"]:
            if "text" in f:
                f["text_ref"] = prepare_object(root,f.pop("text").encode("utf-8"),changes)
            elif "text_ref" in f or "data_ref" in f:
                ref=f.get("text_ref",f.get("data_ref"))
                if materials is not None and f["sha256"] in materials:
                    raw=materials[f["sha256"]]; check_fragment(f,raw)
                    if prepare_object(root,raw,changes)!=ref: raise ContractError("Captured fragment reference mismatch")
                else: read_object(root,ref)
            elif f.get("gap"):
                try:
                    key = f["source"].split(":",1)[0]
                    e = model.elements.get(key)
                    if materials is not None and f["sha256"] in materials:
                        raw=materials[f["sha256"]]; check_fragment(f,raw)
                    elif e:
                        if e.digest() != f["revision"]: e = model.at(key,f["revision"])
                        raw = e.body.encode("utf-8")
                    elif f["source"].startswith("prose:") and model.hashes.get(f["source"][6:]) == f["revision"]:
                        raw = model.prose[f["source"][6:]].encode("utf-8")
                    else:
                        from v3_contract import read_bytes
                        raw = read_bytes(root,f["source"],limit=64*1024*1024)
                    if sha(raw) == f["sha256"] and len(raw) == f["bytes"]:
                        field = "data_ref" if f.get("unit") == "bytes" else "text_ref"
                        f[field] = prepare_object(root,raw,changes); f["transient_gap"] = f.pop("gap")
                except (ContractError,OSError,ValueError): pass  # Explicit missing bytes; never claim readiness.
        return row
    for original in observations:
        key = original["observation_id"]
        if key in seen and seen[key] != fingerprint(original): raise ContractError("Observation ID collision")
        seen[key] = fingerprint(original)
        if key in existing:
            old = existing[key]
            plain = unpack(old)
            if original not in (old,plain) and imported(original) not in (old,plain): raise ContractError("Observation ID collision")
            continue
        if any(key in e.data.get("observation_ids", []) and e.data["run_id"] != original["run_id"] for e in model.by_kind("receipt") if diagnostic(e)):
            raise ContractError("Observation ID collision across runs")
        row = pack(imported(original))
        binding = row["binding"]
        if binding["request"]: model.get(binding["request"], "request")
        for task in binding["tasks"]:
            t = model.get(task, "task")
            if binding["request"] and t.data["request"] != binding["request"]: raise ContractError("Usage task outside request")
        group = (row["run_id"], binding["request"], tuple(binding["tasks"]))
        groups.setdefault(group, {})[key] = row
    items = []
    for (run_id, request, tasks), values in groups.items():
        rows = list(values.values())
        ref = prepare_object(root, canonical({"format": FORMAT, "observations": rows}), changes)
        items.append(element("receipt", "Observaciones de uso del plugin", "Diagnóstico informativo conservado; no acredita calidad, aprobación ni aceptación.",
                             purpose="usage-observation", run_id=run_id, request=request, tasks=list(tasks),
                             actor=actor, count=len(rows), observation_ids=[r["observation_id"] for r in rows], observations_ref=ref))
        items[-1]["meta"].update(nature="fact", state="observed")
    return items, changes


def pending(root):
    value = SESSION.get()
    if not value or value["consumed"]: return [], {}
    value["consumed"] = True
    from v3_contract import INDEX, DOCS
    if value["context"].get("observations") and not (Path(root)/INDEX).exists() and not (Path(root)/DOCS).exists():
        value["deferred"] = True
        return [], {}
    return additions(root, value["context"].get("observations", []), value["data"].get("actor")) if value["context"].get("observations") else ([], {})


def record(root, data):
    from v3_storage import prepare
    items, changes = additions(root, data["observations"], data.get("actor"))
    if not items: return {"status": "already-recorded", "writes": []}
    return prepare(root, items, "usage-record", changes=changes)


def summary_metrics(rows):
    rows = list({r["observation_id"]:r for r in rows}.values())
    accumulated, intervals, binary = 0, {}, 0
    for r in rows:
        for f in r["fragments"]:
            if f.get("unit") == "bytes": binary += f["bytes"]; continue
            accumulated += f["end"] - f["start"]
            intervals.setdefault((f["source"], f["revision"]), []).append((f["start"], f["end"]))
    unique = 0
    for values in intervals.values():
        end = -1
        for a, b in sorted(values): unique += max(0, b - max(a, end)); end = max(end, b)
    return {"invocations": len({r.get("invocation_id",r["observation_id"]) for r in rows}), "observations":len(rows), "accumulated_characters": accumulated,
            "unique_characters_by_revision": unique, "method": "union of fragment intervals per source/revision; shared operations counted once",
            "referenced_attachment_bytes_accumulated":binary,
            "coverage": "conserved observations only; selection/preparation does not prove host reading", "billed_tokens": None}
