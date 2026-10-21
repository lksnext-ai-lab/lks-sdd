"""Experimental v5 vertical slice. Independent of every v2/v3/v4 runtime.

Markdown is authoritative. JSON front matter is deliberately provisional.
The local lock coordinates this runtime, not other editors or distributed clones.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import time
import uuid
import zipfile


class Conflict(ValueError):
    """A precondition changed; preserve the competing content."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def path_at(root, name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("Expected a relative portable path")
    parts = PurePosixPath(name).parts
    if not parts or PurePosixPath(name).is_absolute() or ".." in parts:
        raise ValueError("Path outside project")
    root = Path(root).resolve()
    path = root.joinpath(*parts)
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Links/junctions require reconciliation")
    if not path.resolve().is_relative_to(root):
        raise ValueError("Path outside project")
    return path


def read(root, name):
    path = path_at(root, name)
    return path.read_bytes() if path.is_file() else None


def document(meta, body):
    return ("---\n" + encode(meta) + "\n---\n\n" + body.strip() + "\n").encode("utf-8")


def parse(raw):
    if raw is None:
        raise ValueError("Missing document")
    match = re.fullmatch(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", raw.decode("utf-8-sig"), re.S)
    if not match:
        raise ValueError("Expected experimental v5 Markdown")
    meta = json.loads(match[1])
    if meta.get("format") != "sdd/5-prototype" or meta.get("kind") not in {"unit", "task", "plan"}:
        raise ValueError("Unsupported document")
    return meta, match[2].strip()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", value):
        raise ValueError("Invalid stable identifier")
    return value


def unit_path(unit):
    return "docs/sdd/especificaciones/" + identifier(unit) + ".md"


def task_path(task, part):
    return "docs/sdd/tareas/" + identifier(task) + "/" + part + ".md"


def current(root, name):
    raw = read(root, name)
    meta, body = parse(raw)
    return meta, body, digest(raw)


def context(root, task):
    """No historical/global enumeration; dependencies are explicit, never inferred."""
    names = [task_path(task, "tarea"), task_path(task, "plan")]
    task_meta, _, _ = current(root, names[0])
    pending = list(task_meta.get("units", []))
    seen = set()
    while pending:
        unit = pending.pop(0)
        if unit in seen:
            continue
        seen.add(unit)
        name = unit_path(unit)
        meta, _, _ = current(root, name)
        if meta.get("id") != unit or meta["kind"] != "unit":
            raise ValueError("Unit identity mismatch")
        names.append(name)
        pending.extend(meta.get("depends_on", []))
    names.extend(task_meta.get("policies", []))
    if read(root, "AGENTS.md") is not None:
        names.append("AGENTS.md")
    documents = {}
    for name in dict.fromkeys(names):
        raw = read(root, name)
        if raw is None:
            raise ValueError("Missing applicable source: " + name)
        documents[name] = raw.decode("utf-8")
    return {"documents": documents, "files_read": len(documents),
            "bytes": sum(len(x.encode("utf-8")) for x in documents.values()),
            "billed_tokens": None}


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".sdd-" + uuid.uuid4().hex)
    try:
        with tmp.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextlib.contextmanager
def locked(root):
    state = path_at(root, ".sdd-work")
    state.mkdir(exist_ok=True)
    marker = state / ".gitignore"
    if not marker.exists():
        atomic_write(marker, b"# v5 local recoverable work; never source of business truth\n*\n")
    lock_path = path_at(root, ".sdd-work/lock")
    with lock_path.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise Conflict("Another local operation is active") from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise Conflict("Another local operation is active") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def writable(name, migration=False):
    prefixes = ("docs/sdd/", ".sdd-work/tmp/")
    if migration:
        prefixes += ("docs/lks-sdd/",)
    if not name.startswith(prefixes):
        raise ValueError("Outside owned mutation scope: " + name)


def apply(root, changes, expected, *, migration=False, guards=(), interrupt_after=None):
    """All sources checked before writing. One transient journal, not one per phase."""
    with locked(root):
        journal = path_at(root, ".sdd-work/journal.json")
        if journal.exists():
            raise Conflict("Pending operation: resume it before another mutation")
        for name, value in expected.items():
            if digest(read(root, name)) != value:
                raise Conflict("Source changed: " + name)
        entries = {}
        for name, after in changes.items():
            writable(name, migration)
            if name not in expected:
                raise ValueError("Every target needs an explicit base")
            before = read(root, name)
            if before != after:
                entries[name] = {
                    "before": base64.b64encode(before).decode() if before is not None else None,
                    "after": base64.b64encode(after).decode() if after is not None else None}
        if not entries:
            return {"status": "unchanged", "files": 0}
        payload = {"format": "sdd/5-transaction", "migration": migration, "entries": entries, "guards": guards,
                   "reads": {k: v for k, v in expected.items() if k not in entries}}
        atomic_write(journal, encode(payload).encode())
        return _resume(root, payload, interrupt_after)


def _resume(root, payload, interrupt_after=None):
    if payload.get("format") != "sdd/5-transaction":
        raise ValueError("Unknown journal")
    entries = payload["entries"]
    decoded = {}
    for guard in payload.get("guards", []):
        task, _, _ = current(root, guard["task"])
        if input_fingerprint(root, guard["task"], task, guard["check"]) != guard["fingerprint"]:
            raise Conflict("Test inputs changed before completion/recovery")
    for name, hashes in payload["reads"].items():
        if digest(read(root, name)) != hashes:
            raise Conflict("Recovery source changed: " + name)
    for name, values in entries.items():
        writable(name, payload["migration"])
        before, after = (base64.b64decode(values[key], validate=True) if values[key] is not None else None
                         for key in ("before", "after"))
        if read(root, name) not in (before, after):
            raise Conflict("Recovery conflicts with later edits: " + name)
        decoded[name] = (before, after)
    for index, (name, (_, after)) in enumerate(decoded.items(), 1):
        path = path_at(root, name)
        if read(root, name) != after:
            if after is None:
                path.unlink()
            else:
                atomic_write(path, after)
        if interrupt_after == index:
            raise InterruptedError("Injected interruption; journal retained")
    path_at(root, ".sdd-work/journal.json").unlink()
    return {"status": "applied", "files": len(entries)}


def resume(root):
    with locked(root):
        raw = read(root, ".sdd-work/journal.json")
        if raw is None:
            return {"status": "unchanged", "files": 0}
        return _resume(root, json.loads(raw))


def require_authority(task, operation):
    authority = task.get("authority", {})
    if not authority.get("actor") or not authority.get("source") or operation not in authority.get("scope", []):
        raise ValueError("Recorded authority does not cover " + operation)


def input_fingerprint(root, task_name, task, check):
    """Explicit scope includes additions/deletions. No claim of inferred coverage."""
    if not check.get("inputs") or not check.get("environment") or not check.get("argv"):
        raise ValueError("Declare inputs, command and environment")
    files = {task_name: digest(read(root, task_name))}
    for name in task.get("policies", []):
        raw = read(root, name)
        if raw is None:
            raise ValueError("Missing policy")
        files[name] = digest(raw)
    if read(root, "AGENTS.md") is not None:
        files["AGENTS.md"] = digest(read(root, "AGENTS.md"))
    count = 0
    for pattern in check["inputs"]:
        path_at(root, pattern)
        for path in sorted(Path(root).glob(pattern)):
            name = path.relative_to(root).as_posix()
            path_at(root, name)
            if path.is_file():
                files[name] = digest(path.read_bytes())
                count += 1
    if not count:
        raise ValueError("No test input matched")
    value = {"files": files, "definition": check, "python": sys.version,
             "platform": platform.platform()}
    return digest(encode(value).encode())


def result_current(result, fingerprint, check):
    if not result or result.get("status") != "passed" or result.get("inputs") != fingerprint:
        return False
    age = time.time() - result["finished"]
    return 0 <= age <= check.get("max_age_seconds", float("inf"))


def check_task(root, task_id, check_id):
    if read(root, ".sdd-work/journal.json") is not None:
        raise Conflict("Resume the pending operation before running another test")
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, _, task_hash = current(root, task_name)
    plan, body, plan_hash = current(root, plan_name)
    require_authority(task, "implement")
    definition = plan["checks"][check_id]
    signature = input_fingerprint(root, task_name, task, definition)
    previous = plan.get("results", {}).get(check_id)
    if result_current(previous, signature, definition):
        return {"status": "reused", "check": check_id}
    start = time.perf_counter()
    run = subprocess.run(definition["argv"], cwd=root, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, timeout=definition.get("timeout", 60), shell=False)
    if input_fingerprint(root, task_name, task, definition) != signature:
        raise Conflict("Test inputs changed during execution")
    result = {"status": "passed" if run.returncode == 0 else "failed", "inputs": signature,
              "exit_code": run.returncode, "finished": time.time(),
              "seconds": time.perf_counter() - start, "output_sha256": digest(run.stdout),
              "output_bytes": len(run.stdout)}
    changes, expected = {}, {task_name: task_hash, plan_name: plan_hash}
    if run.returncode:
        name = ".sdd-work/tmp/" + uuid.uuid4().hex + ".log"
        changes[name], expected[name] = run.stdout, None
        result["failure_log"] = name
        plan.setdefault("temporaries", {})[name] = digest(run.stdout)
    plan.setdefault("results", {})[check_id] = result
    plan["state"] = "en-curso"
    plan["next"] = "Resolver fallo" if run.returncode else "Consolidar cuando terminen las comprobaciones"
    changes[plan_name] = document(plan, body)
    apply(root, changes, expected, guards=[{"task": task_name, "check": definition, "fingerprint": signature}])
    return {"status": result["status"], "check": check_id, "seconds": result["seconds"]}


def artifact(root, name):
    raw = read(root, name)
    if raw is None:
        raise ValueError("Missing artifact")
    media = "application/zip" if name.lower().endswith(".zip") else mimetypes.guess_type(name)[0]
    return {"path": name, "bytes": len(raw), "sha256": digest(raw),
            "media_type": media or "application/octet-stream"}


def close(root, task_id, updates, facts, *, interrupt_after=None):
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, _, task_hash = current(root, task_name)
    plan, body, plan_hash = current(root, plan_name)
    require_authority(task, "consolidate")
    if plan.get("state") == "cerrado":
        if facts != plan.get("delivery") or any(read(root, unit_path(k)) != v for k, v in updates.items()):
            raise Conflict("Closed task differs from requested result")
        return {"status": "unchanged", "files": 0}
    if plan.get("blockers"):
        raise ValueError("Resolve the affected blockers before consolidation")
    if not plan.get("checks"):
        raise ValueError("Declare pertinent checks; no automatic empty verification")
    guards = []
    for name, definition in plan["checks"].items():
        signature = input_fingerprint(root, task_name, task, definition)
        if not result_current(plan.get("results", {}).get(name), signature, definition):
            raise ValueError("Missing/current passing result: " + name)
        guards.append({"task": task_name, "check": definition, "fingerprint": signature})
    changes, expected = {}, {task_name: task_hash, plan_name: plan_hash}
    for unit, raw in updates.items():
        if unit not in task["units"]:
            raise ValueError("Unit outside task scope")
        name = unit_path(unit)
        meta, _ = parse(raw)
        if meta.get("id") != unit or meta["kind"] != "unit":
            raise ValueError("Invalid consolidated unit")
        changes[name], expected[name] = raw, plan["bases"][name]
    for name, old_hash in plan.get("temporaries", {}).items():
        if not name.startswith(".sdd-work/tmp/"):
            raise ValueError("Unowned cleanup target")
        changes[name], expected[name] = None, old_hash
    required = {"implementation", "verification", "integration", "publication", "deployment", "acceptance"}
    if set(facts) != required or any(not isinstance(v, str) or not v.strip() for v in facts.values()):
        raise ValueError("Record six distinct delivery facts, including unknown/not-run")
    plan.update(state="cerrado", next="Sin ejecución pendiente en este alcance", delivery=facts,
                temporaries={}, bases={k: digest(v) for k, v in changes.items() if k.startswith("docs/sdd/especificaciones/")})
    changes[plan_name] = document(plan, body)
    return apply(root, changes, expected, guards=guards, interrupt_after=interrupt_after)


LEGACY = re.compile(r"<!-- lks-sdd: (.*?) -->\s*(.*?)\s*<!-- /lks-sdd -->", re.S)


def legacy_read(raw):
    text = raw.decode("utf-8-sig")
    if not re.search(r'^schema_version: [\"\']?3\.1[\"\']?\r?$', text, re.M):
        raise ValueError("Prototype reader supports inline schema 3.1 only")
    matches = list(LEGACY.finditer(text))
    if not matches or len(matches) != text.count("<!-- lks-sdd:"):
        raise ValueError("Incomplete legacy blocks")
    return [(json.loads(m[1]), m[2]) for m in matches]


def migration_preview(root, sources, targets, *, resolution, recovery_reference):
    """One reviewed semantic mapping. No automatic inference of functional truth.

    Prototype handles explicit inline 3.1 documents only. Full-project retirement,
    packed objects, runtime replacement and global reference rewriting are pending.
    """
    if not sources or not recovery_reference:
        raise ValueError("Explicit source set and recovery reference required")
    expected, ids = {}, set()
    for name in sources:
        if not name.startswith("docs/lks-sdd/"):
            raise ValueError("Only explicitly owned legacy documents")
        raw = read(root, name)
        if raw is None:
            raise ValueError("Missing conversion source")
        expected[name] = digest(raw)
        for meta, _ in legacy_read(raw):
            if meta["uid"] in ids:
                raise ValueError("Duplicate/conflicting legacy identity")
            ids.add(meta["uid"])
    if set(resolution) != ids or any(not str(v).strip() for v in resolution.values()):
        raise ValueError("Unresolved source meaning; preserve its source")
    changes = {}
    for name, raw in targets.items():
        if not name.startswith("docs/sdd/"):
            raise ValueError("Conversion target outside v5")
        parse(raw)
        expected[name] = digest(read(root, name))
        if expected[name] is not None:
            raise Conflict("Reconcile existing v5 documents before conversion")
        changes[name] = raw
    for name in sources:
        changes[name] = None
    for name, raw in targets.items():
        meta, _ = parse(raw)
        if meta["kind"] == "task":
            if task_path(meta["id"], "plan") not in targets:
                raise ValueError("Migrated task requires its single plan")
            for unit in meta.get("units", []):
                target = targets.get(unit_path(unit), read(root, unit_path(unit)))
                if target is None:
                    raise ValueError("Missing migrated unit")
        if meta["kind"] == "plan" and task_path(meta["id"], "tarea") not in targets:
            raise ValueError("Orphan migrated plan")
    serial = {"sources": expected, "targets": {k: digest(v) for k, v in changes.items()},
              "resolution": resolution, "recovery": recovery_reference}
    return {"preview": digest(encode(serial).encode()), "expected": expected, "changes": changes,
            "resolution": resolution, "recovery": recovery_reference,
            "summary": {"source_files": len(sources), "target_files": len(targets),
                        "source_elements": len(ids), "recovery": recovery_reference}}


def migrate(root, preview, authorized_preview, *, interrupt_after=None):
    serial = {"sources": preview["expected"],
              "targets": {k: digest(v) for k, v in preview["changes"].items()},
              "resolution": preview["resolution"], "recovery": preview["recovery"]}
    if authorized_preview != preview["preview"] or digest(encode(serial).encode()) != authorized_preview:
        raise ValueError("Authorization must cover the displayed conversion")
    # Prototype requires an existing, exact, bounded recovery ZIP. It never treats
    # an unverified label or a partial Git commit as a recoverable preimage.
    recovery = preview["recovery"]
    if not isinstance(recovery, dict) or recovery.get("kind") != "zip" or not recovery.get("expires"):
        raise ValueError("Verified recovery ZIP and explicit expiry required")
    recovery_path = path_at(root, recovery["path"])
    if digest(recovery_path.read_bytes()) != recovery["sha256"]:
        raise ValueError("Recovery archive changed")
    with zipfile.ZipFile(recovery_path) as archive:
        for name, target in preview["changes"].items():
            if target is None and digest(archive.read(name)) != preview["expected"][name]:
                raise ValueError("Recovery does not cover source: " + name)
    return apply(root, preview["changes"], preview["expected"], migration=True,
                 interrupt_after=interrupt_after)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("context", "check", "close"):
        command = sub.add_parser(action)
        command.add_argument("task")
        if action == "check":
            command.add_argument("check")
        if action == "close":
            command.add_argument("--unit", action="append", default=[], help="ID=relative-draft.md")
            command.add_argument("--facts", required=True, help="JSON with six distinct delivery facts")
    sub.add_parser("resume")
    args = parser.parse_args(argv)
    if args.action == "context":
        result = context(args.root, args.task)
    elif args.action == "check":
        result = check_task(args.root, args.task, args.check)
    elif args.action == "close":
        updates = {k: read(args.root, v) for k, v in (x.split("=", 1) for x in args.unit)}
        result = close(args.root, args.task, updates, json.loads(args.facts))
    else:
        result = resume(args.root)
    print(encode(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(encode({"status": "blocked", "reason": str(exc)}))
        sys.exit(2)
