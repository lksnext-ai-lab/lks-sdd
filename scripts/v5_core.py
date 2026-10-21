"""LKS-SDD 5 document, execution and recoverable-write core.

Markdown is authoritative. JSON front matter is a small YAML-compatible metadata block.
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
import shutil
import stat
from datetime import datetime, timezone

FORMAT = "lks-sdd/5"
DELIVERY = ("implementation", "verification", "integration", "publication", "deployment", "acceptance")
STATES = {"definido", "preparado", "en-curso", "bloqueado", "cerrado", "cancelado"}


class Conflict(ValueError):
    """A precondition changed; preserve the competing content."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def filesystem_root(root):
    value = str(Path(root).resolve())
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\" + value[2:] if value.startswith("\\\\") else "\\\\?\\" + value
    return Path(value)


def path_at(root, name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("Expected a relative portable path")
    parts = PurePosixPath(name).parts
    if (not parts or PurePosixPath(name).is_absolute() or ".." in parts or any(p.endswith((" ", ".")) for p in parts)
            or any(re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", p) for p in parts)):
        raise ValueError("Path outside project")
    root = filesystem_root(root)
    path = root.joinpath(*parts)
    for part in (path, *path.parents):
        if part == root:
            break
        if any(c in str(part.relative_to(root)) for c in "*?["):
            continue  # Glob syntax is checked lexically; every actual match is checked below.
        try:
            attributes = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(attributes.st_mode) or getattr(attributes, "st_file_attributes", 0) & 0x400:
            raise ValueError("Links/junctions require reconciliation")
    return path


def read(root, name):
    path = path_at(root, name)
    if not path.is_file():
        return None
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Source exceeds 64 MiB; reference large evidence by hash")
    return path.read_bytes()


def file_digest(path):
    before = path.stat()
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise Conflict("Source changed while hashing: " + str(path))
    return value.hexdigest()


def document(meta, body):
    return ("---\n" + encode(meta) + "\n---\n\n" + body.strip() + "\n").encode("utf-8")


def parse(raw):
    if raw is None:
        raise ValueError("Missing document")
    match = re.fullmatch(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", raw.decode("utf-8-sig"), re.S)
    if not match:
        raise ValueError("Expected LKS-SDD 5 Markdown")
    meta = json.loads(match[1])
    if meta.get("format") != "lks-sdd/5" or meta.get("kind") not in {"unit", "task", "plan"}:
        raise ValueError("Unsupported document")
    identifier(meta.get("id"))
    if meta["kind"] == "plan" and meta.get("state") not in STATES:
        raise ValueError("Invalid work state")
    for key in ("units", "depends_on", "subtasks"):
        if key in meta:
            if not isinstance(meta[key], list) or len(meta[key]) != len(set(meta[key])):
                raise ValueError("Invalid/duplicate references: " + key)
            for item in meta[key]:
                identifier(item)
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
    if read(root, unit_path("proyecto")) is not None:
        names.append(unit_path("proyecto"))
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


_UNCONDITIONAL = object()


def atomic_write(path, raw, *, expected=_UNCONDITIONAL):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".sdd-" + uuid.uuid4().hex)
    try:
        with tmp.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if expected is not _UNCONDITIONAL:
            actual = file_digest(path) if path.is_file() else None
            if actual != expected:
                raise Conflict("Source changed before replacement: " + str(path))
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
        if journal.exists() or read(root, ".sdd-work/migration.json") is not None:
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
        payload = {"format": "lks-sdd/5-transaction", "migration": migration, "entries": entries, "guards": guards,
                   "reads": {k: v for k, v in expected.items() if k not in entries}}
        atomic_write(journal, encode(payload).encode())
        return _resume(root, payload, interrupt_after)


def _resume(root, payload, interrupt_after=None):
    if payload.get("format") != "lks-sdd/5-transaction":
        raise ValueError("Unknown journal")
    entries = payload["entries"]
    decoded = {}
    for name, values in entries.items():
        writable(name, payload["migration"])
        before, after = (base64.b64decode(values[key], validate=True) if values[key] is not None else None
                         for key in ("before", "after"))
        if read(root, name) not in (before, after):
            raise Conflict("Recovery conflicts with later edits: " + name)
        decoded[name] = (before, after)
    for guard in payload.get("guards", []):
        task, _, _ = current(root, guard["task"])
        if input_fingerprint(root, guard["task"], task, guard["check"],
                _before={name: before for name, (before, _) in decoded.items()}) != guard["fingerprint"]:
            raise Conflict("Test inputs changed before completion/recovery")
    for name, hashes in payload["reads"].items():
        if digest(read(root, name)) != hashes:
            raise Conflict("Recovery source changed: " + name)
    for index, (name, (before, after)) in enumerate(decoded.items(), 1):
        path = path_at(root, name)
        now = read(root, name)
        if now not in (before, after):
            raise Conflict("Concurrent edit before completion: " + name)
        if now != after:
            if after is None:
                if digest(read(root, name)) != digest(before):
                    raise Conflict("Concurrent edit before cleanup: " + name)
                path.unlink()
            else:
                atomic_write(path, after, expected=digest(before))
        if interrupt_after == index:
            raise InterruptedError("Injected interruption; journal retained")
    path_at(root, ".sdd-work/journal.json").unlink()
    for name, (_, after) in decoded.items():
        if after is None and name.startswith(".sdd-work/tmp/"):
            parent = path_at(root, name).parent
            boundary = path_at(root, ".sdd-work/tmp")
            while parent.is_relative_to(boundary):
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
    return {"status": "applied", "files": len(entries)}


def resume(root):
    with locked(root):
        raw = read(root, ".sdd-work/journal.json")
        if raw is None:
            return {"status": "unchanged", "files": 0}
        return _resume(root, json.loads(raw))


def scope_digest(task, body):
    # Decomposition does not change the approved functional scope of the parent.
    values = {k: v for k, v in task.items() if k not in {"authority", "provenance", "owner", "parent", "subtasks"}}
    return digest(document(values, body))


def test_scope(raw):
    task, body = parse(raw)
    administrative = {"authority", "provenance", "owner", "parent", "subtasks"}
    return digest(document({k: v for k, v in task.items() if k not in administrative}, body))


def require_authority(task, operation, body=None):
    authority = task.get("authority", {})
    if not authority.get("actor") or not authority.get("source") or operation not in authority.get("scope", []):
        raise ValueError("Recorded authority does not cover " + operation)
    if body is not None and authority.get("approved_scope") != scope_digest(task, body):
        raise ValueError("Authority does not cover the current task scope")
    if authority.get("expires") and datetime.fromisoformat(authority["expires"]) <= datetime.now(timezone.utc):
        raise ValueError("Authority expired")


def input_fingerprint(root, task_name, task, check, *, _before=None):
    """Explicit scope includes additions/deletions. No claim of inferred coverage."""
    root = filesystem_root(root)
    if not check.get("inputs") or not check.get("environment") or not (check.get("argv") or check.get("provider")):
        raise ValueError("Declare inputs, command and environment")
    files = {task_name: test_scope(read(root, task_name))}
    if read(root, unit_path("proyecto")) is not None:
        files[unit_path("proyecto")] = digest(read(root, unit_path("proyecto")))
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
                files[name] = file_digest(path)
                count += 1
    if not count:
        raise ValueError("No test input matched")
    # Recovery validates the original tested inputs after first proving every
    # transaction target is exactly its recorded before/after state. It must not
    # mistake its own completed specification write for a foreign input edit.
    for name, raw in (_before or {}).items():
        if name in files:
            if raw is None:
                files.pop(name)
            else:
                files[name] = digest(raw)
    files[task_name] = test_scope((_before or {}).get(task_name, read(root, task_name)))
    command = check.get("argv")
    if check.get("provider"):
        if not check.get("tool_version"):
            raise ValueError("External result requires a declared tool version")
        return digest(encode({"files": files, "definition": check}).encode())
    if not isinstance(command, list) or not command or any(not isinstance(x, str) for x in command):
        raise ValueError("Command must be an argument array; shell execution is unsupported")
    executable = shutil.which(command[0]) or command[0]
    tool = Path(executable)
    if not tool.is_file():
        raise ValueError("Executable unavailable")
    env = {name: os.environ.get(name) for name in check.get("environment_keys", [])}
    value = {"files": files, "definition": check, "python": sys.version,
             "platform": platform.platform(), "executable": file_digest(tool), "environment": env}
    return digest(encode(value).encode())


def result_current(result, fingerprint, check):
    if not result or result.get("status") != "passed" or result.get("inputs") != fingerprint:
        return False
    finished = result.get("finished")
    if finished is None:
        return "max_age_seconds" not in check  # Unknown age never satisfies a bounded freshness policy.
    age = time.time() - finished
    return 0 <= age <= check.get("max_age_seconds", float("inf"))


def check_task(root, task_id, check_id):
    if any(read(root, ".sdd-work/" + n) is not None for n in ("journal.json", "migration.json")):
        raise Conflict("Resume the pending operation before running another test")
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, task_body, task_hash = current(root, task_name)
    plan, body, plan_hash = current(root, plan_name)
    require_authority(task, "implement", task_body)
    definition = plan["checks"][check_id]
    if definition.get("provider"):
        raise ValueError("Import the original external result; do not synthesize a local pass")
    signature = input_fingerprint(root, task_name, task, definition)
    previous = plan.get("results", {}).get(check_id)
    if result_current(previous, signature, definition):
        return {"status": "reused", "check": check_id}
    old_log = previous.get('failure_log') if previous else None
    old_log_hash = plan.get('temporaries', {}).get(old_log)
    if old_log and (not old_log.startswith('.sdd-work/tmp/') or not old_log_hash or digest(read(root, old_log)) != old_log_hash):
        raise Conflict('Previous failure log has an unowned or changed value')
    start = time.perf_counter()
    import tempfile
    with tempfile.TemporaryFile() as output:
        try:
            run = subprocess.run(definition["argv"], cwd=root, stdout=output,
                                 stderr=subprocess.STDOUT, timeout=definition.get("timeout", 600), shell=False)
            code, status = run.returncode, "passed" if run.returncode == 0 else "failed"
        except (subprocess.TimeoutExpired, OSError):
            code, status = None, "blocked"
        output.seek(0)
        output_hash, output_bytes = hashlib.sha256(), 0
        tail = b""
        for chunk in iter(lambda: output.read(1024 * 1024), b""):
            output_hash.update(chunk)
            output_bytes += len(chunk)
            tail = (tail + chunk)[-65536:]
    if input_fingerprint(root, task_name, task, definition) != signature:
        raise Conflict("Test inputs changed during execution")
    result = {"status": status, "inputs": signature, "origin": "local-process",
              "exit_code": code, "finished": time.time(),
              "seconds": time.perf_counter() - start, "output_sha256": output_hash.hexdigest(),
              "output_bytes": output_bytes}
    changes, expected = {}, {task_name: task_hash, plan_name: plan_hash}
    if status != "passed":
        name = old_log or ".sdd-work/tmp/" + uuid.uuid4().hex + ".log"
        changes[name], expected[name] = tail, old_log_hash if old_log else None
        result["failure_log"] = name
        plan.setdefault("temporaries", {})[name] = digest(tail)
    elif old_log:
        changes[old_log], expected[old_log] = None, old_log_hash
        plan['temporaries'].pop(old_log)
    plan.setdefault("results", {})[check_id] = result
    plan["state"] = "en-curso"
    plan["next"] = "Resolver comprobación pendiente; continuar alcance independiente" if status != "passed" else "Consolidar cuando terminen las comprobaciones"
    changes[plan_name] = document(plan, body)
    apply(root, changes, expected, guards=[{"task": task_name, "check": definition, "fingerprint": signature}])
    return {"status": result["status"], "check": check_id, "seconds": result["seconds"]}


def artifact(root, name):
    path = path_at(root, name)
    if not path.is_file():
        raise ValueError("Missing artifact")
    media = "application/zip" if name.lower().endswith(".zip") else mimetypes.guess_type(name)[0]
    return {"path": name, "bytes": path.stat().st_size, "sha256": file_digest(path),
            "media_type": media or "application/octet-stream"}


def project_policy(root):
    raw = read(root, unit_path("proyecto"))
    return parse(raw)[0].get("policy", {}) if raw else {}


def required_checks(policy, task):
    """Apply declared path scopes; uncertain overlap never exempts a control."""
    def prefix(pattern):
        if not isinstance(pattern, str) or not pattern or pattern.startswith('/') or ':' in pattern or '\\' in pattern or '..' in pattern.split('/'):
            return ()  # Unknown scope must not silently remove a requirement.
        parts = pattern.split('/')
        result = []
        for part in parts:
            if part in ('', '.'): continue
            if any(c in part for c in '*?['): break
            result.append(part)
        return tuple(result)
    paths = task.get('paths')
    if not isinstance(paths, list) or not paths:
        return set(policy.get('required_checks', []))
    result = set()
    for name in policy.get('required_checks', []):
        scope = policy.get('check_scopes', {}).get(name)
        if not isinstance(scope, list) or not scope:
            result.add(name)
            continue
        if any(a[:min(len(a), len(b))] == b[:min(len(a), len(b))]
               for a in map(prefix, paths) for b in map(prefix, scope)):
            result.add(name)
    return result


def verify_coverage(root, task_id, task, plan, expected, guards, trail=()):
    """Resolve acceptance links, not duplicate children results into the parent."""
    if task_id in trail:
        raise ValueError("Cyclic criterion delegation")
    if project_policy(root).get("migration_pending"):
        raise ValueError("Resolve pending project controls before consolidation")
    required = required_checks(project_policy(root), task)
    checks = plan.get("checks", {})
    if required - set(checks) and not plan.get('criterion_links'):
        raise ValueError("Project requires checks: " + ", ".join(sorted(required - set(checks))))
    if not checks and not task.get("subtasks") and not plan.get("no_checks_reason"):
        raise ValueError("Declare pertinent checks; no automatic empty verification")
    dispositions = plan.get("criterion_dispositions", {})
    if any(not isinstance(reason, str) or not reason.strip() for reason in dispositions.values()):
        raise ValueError("Criterion dispositions require a reason")
    covered = {criterion for check in checks.values() for criterion in check.get("criteria", [])}
    covered.update(dispositions)
    verified_children = {}
    for criterion, links in plan.get("criterion_links", {}).items():
        if criterion not in task.get("criteria", {}) or not isinstance(links, list) or not links:
            raise ValueError("Invalid criterion delegation")
        for link in links:
            child = link.get("task")
            if child not in task.get("subtasks", []):
                raise ValueError("Criterion must reference a declared subtask")
            child_name, child_plan_name = task_path(child, "tarea"), task_path(child, "plan")
            child_task, _, task_hash = current(root, child_name)
            child_plan, _, plan_hash = current(root, child_plan_name)
            if child_task.get("parent") != task_id or link.get("criterion") not in child_task.get("criteria", {}):
                raise ValueError("Missing child criterion/parent relationship")
            if child_plan["state"] != "cerrado" or child_plan.get("verified_scope") != test_scope(read(root, child_name)):
                raise ValueError("Child verification no longer covers its scope")
            expected.update({child_name: task_hash, child_plan_name: plan_hash})
            if child not in verified_children:
                verified_children[child] = verify_coverage(root, child, child_task, child_plan, expected, guards, (*trail, task_id))
        covered.add(criterion)
    if task.get("criteria") and not plan.get("no_checks_reason") and set(task["criteria"]) - covered:
        raise ValueError("Acceptance criteria need explicit checks or reasoned dispositions")
    inherited = set()
    if verified_children and task.get('criteria') and set(task['criteria']) <= set(plan.get('criterion_links', {})):
        # Only complete explicit delegation can satisfy a parent's controls.
        # Every linked child must prove the same control, with current inputs.
        inherited = set.intersection(*verified_children.values())
    if required - (set(checks) | inherited):
        raise ValueError("Project requires checks: " + ", ".join(sorted(required - (set(checks) | inherited))))
    for name, definition in checks.items():
        task_name = task_path(task_id, "tarea")
        signature = input_fingerprint(root, task_name, task, definition)
        if not result_current(plan.get("results", {}).get(name), signature, definition):
            raise ValueError("Missing/current passing result: " + name)
        guards.append({"task": task_name, "check": definition, "fingerprint": signature})
    return set(checks) | inherited


def delivery_guards(root, task_id, task, body, plan, facts):
    if not set(facts) <= set(DELIVERY) or any(not isinstance(v, str) or not v.strip() for v in facts.values()):
        raise ValueError("Explicit delivery facts required")
    def positive(value):
        return not re.match(r"^(?:not-run|unknown|pending|not-applicable|n/a|pendiente|no ejecutado)(?:$|[ :.-])", value.strip(), re.I)
    external = {k: v for k, v in facts.items() if k in DELIVERY[2:] and positive(v)}
    if external:
        require_authority(task, "deliver", body)
    guards = []
    if "deployment" in external:
        for name in project_policy(root).get("deployment_checks", []):
            definition = plan.get("checks", {}).get(name)
            task_name = task_path(task_id, "tarea")
            if not definition:
                raise ValueError("Project requires current deployment check: " + name)
            fingerprint = input_fingerprint(root, task_name, task, definition)
            if not result_current(plan.get("results", {}).get(name), fingerprint, definition):
                raise ValueError("Project requires current deployment check: " + name)
            guards.append({"task": task_name, "check": definition, "fingerprint": fingerprint})
    return guards


def close(root, task_id, updates, facts=None, *, interrupt_after=None):
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, task_body, task_hash = current(root, task_name)
    plan, body, plan_hash = current(root, plan_name)
    require_authority(task, "consolidate", task_body)
    facts = {} if facts is None else facts
    if not isinstance(facts, dict) or not set(facts) <= set(DELIVERY) or any(not isinstance(v, str) or not v.strip() for v in facts.values()):
        raise ValueError("Explicit delivery facts required")
    facts = {**{k: 'unknown' for k in DELIVERY}, **plan.get('delivery', {}), **facts}
    if plan.get("state") == "cerrado":
        if facts != plan.get("delivery") or any(read(root, unit_path(k)) != v for k, v in updates.items()):
            raise Conflict("Closed task differs from requested result")
        return {"status": "unchanged", "files": 0}
    if plan.get("blockers"):
        raise ValueError("Resolve the affected blockers before consolidation")
    children = task.get("subtasks", [])
    for child in children:
        child_plan, _, _ = current(root, task_path(child, "plan"))
        if child_plan["state"] != "cerrado":
            raise ValueError("Subtask remains open: " + child)
    guards = []
    changes, expected = {}, {task_name: task_hash, plan_name: plan_hash}
    verify_coverage(root, task_id, task, plan, expected, guards)
    guards.extend(delivery_guards(root, task_id, task, task_body, plan, facts))
    expected[unit_path("proyecto")] = digest(read(root, unit_path("proyecto")))
    for child in children:
        name = task_path(child, "plan")
        expected[name] = digest(read(root, name))
    for unit, raw in updates.items():
        if unit not in task["units"]:
            raise ValueError("Unit outside task scope")
        name = unit_path(unit)
        meta, _ = parse(raw)
        if meta.get("id") != unit or meta["kind"] != "unit":
            raise ValueError("Invalid consolidated unit")
        for dependency in meta.get("depends_on", []):
            if dependency not in updates:
                dep_name = unit_path(dependency)
                current(root, dep_name)
                expected[dep_name] = digest(read(root, dep_name))
        changes[name], expected[name] = raw, plan["bases"][name]
    for name, old_hash in plan.get("temporaries", {}).items():
        if not name.startswith(".sdd-work/tmp/"):
            raise ValueError("Unowned cleanup target")
        changes[name], expected[name] = None, old_hash
    required = set(DELIVERY)
    if set(facts) != required or any(not isinstance(v, str) or not v.strip() for v in facts.values()):
        raise ValueError("Record six distinct delivery facts, including unknown/not-run")
    plan.update(state="cerrado", next="Sin ejecución pendiente en este alcance", delivery=facts,
                verified_scope=test_scope(read(root, task_name)),
                temporaries={}, bases={k: digest(v) for k, v in changes.items() if k.startswith("docs/sdd/especificaciones/")})
    changes[plan_name] = document(plan, body)
    return apply(root, changes, expected, guards=guards, interrupt_after=interrupt_after)


def authorize(root, task_id, actor, source, scope):
    """Record an actual decision supplied by the host, never authenticate its author."""
    if not actor.strip() or not source.strip() or not scope or not set(scope) <= {"implement", "consolidate", "deliver"}:
        raise ValueError("Explicit actor, decision source and bounded authority required")
    name = task_path(task_id, "tarea")
    task, body, before = current(root, name)
    task["authority"] = {"actor": actor, "source": source, "scope": sorted(set(scope)),
                         "approved_scope": scope_digest(task, body)}
    return apply(root, {name: document(task, body)}, {name: before})


def validate(root, task_id=None):
    """Whole-project validation is explicit; normal task context remains bounded."""
    root = filesystem_root(root)
    names = ([task_path(task_id, p) for p in ("tarea", "plan")] if task_id else
             sorted(p.relative_to(root).as_posix() for p in (root / "docs/sdd").rglob("*.md")))
    errors, identities = [], set()
    for name in names:
        try:
            data, _, _ = current(root, name)
            expected_name = unit_path(data["id"]) if data["kind"] == "unit" else task_path(data["id"], "tarea" if data["kind"] == "task" else "plan")
            if name != expected_name:
                raise ValueError("Identity does not match canonical path")
            key = (data["kind"], data["id"])
            if key in identities:
                raise ValueError("Duplicate document identity")
            identities.add(key)
            if data["kind"] == "task":
                context(root, data["id"])
                for child in data.get("subtasks", []):
                    child_data, _, _ = current(root, task_path(child, "tarea"))
                    if child_data.get("parent") != data["id"] or child == data["id"]:
                        raise ValueError("Subtask parent mismatch")
            elif data["kind"] == "plan":
                current(root, task_path(data["id"], "tarea"))
            elif data["kind"] == "unit":
                for dependency in data.get("depends_on", []):
                    current(root, unit_path(dependency))
        except (ValueError, KeyError, OSError) as exc:
            errors.append({"file": name, "error": str(exc)})
    if not names:
        errors.append({"file": "docs/sdd", "error": "No v5 documents"})
    return {"status": "passed" if not errors else "blocked", "documents": len(names), "errors": errors}


def status(root, task_id):
    task, _, _ = current(root, task_path(task_id, "tarea"))
    plan, _, _ = current(root, task_path(task_id, "plan"))
    return {"id": task_id, "owner": task.get("owner"), "state": plan["state"],
            "next": plan.get("next"), "blockers": plan.get("blockers", []),
            "delivery": plan.get("delivery", {k: "not-run" for k in DELIVERY}),
            "subtasks": [{"id": c, "state": current(root, task_path(c, "plan"))[0]["state"]}
                         for c in task.get("subtasks", [])]}


def prepare(root, task_id, title, request, criteria, units, owner, *, parent=None, paths=None):
    if not title.strip() or not request.strip() or not criteria or not owner.strip():
        raise ValueError("Need title, request, observable criteria and responsibility")
    for unit in units:
        current(root, unit_path(unit))
    task = {"format": FORMAT, "kind": "task", "id": identifier(task_id), "units": units, "owner": owner,
            "policies": [], "criteria": {f"C{i}": text for i, text in enumerate(criteria, 1)}}
    if paths is not None:
        if not isinstance(paths, list) or not paths:
            raise ValueError('Explicit paths must be a nonempty list')
        for name in paths: path_at(root, name)
        task['paths'] = paths
    if parent:
        task["parent"] = identifier(parent)
    plan = {"format": FORMAT, "kind": "plan", "id": task_id, "state": "definido",
            "next": "Preparar enfoque y comprobaciones proporcionales", "checks": {},
            "bases": {unit_path(u): digest(read(root, unit_path(u))) for u in units}}
    changes = {task_path(task_id, "tarea"): document(task, "# " + title + "\n\n" + request),
               task_path(task_id, "plan"): document(plan, "# Plan de " + title)}
    expected = {k: None for k in changes}
    if parent:
        name = task_path(parent, "tarea")
        data, body, before = current(root, name)
        data.setdefault("subtasks", []).append(task_id)
        changes[name], expected[name] = document(data, body), before
    return apply(root, changes, expected)


def delivery(root, task_id, facts):
    """Record results, not perform deployment or trigger an application suite."""
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, body, task_hash = current(root, task_name)
    plan, plan_body, before = current(root, plan_name)
    require_authority(task, "deliver" if "deliver" in task.get("authority", {}).get("scope", []) else "consolidate", body)
    guards = delivery_guards(root, task_id, task, body, plan, facts)
    plan.setdefault("delivery", {k: "not-run" for k in DELIVERY}).update(facts)
    return apply(root, {plan_name: document(plan, plan_body)}, {plan_name: before, task_name: task_hash,
        unit_path("proyecto"): digest(read(root, unit_path("proyecto")))}, guards=guards)

