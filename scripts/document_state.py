"""Exact independent documentary states, including resources, without full tree copies."""
import json
import re
from pathlib import Path

from content_store import prepare_object, object_path, read_object
from v2_contract import ContractError, canonical, fingerprint, read_bytes, relative_parts, sha
from object_zip import evaluated

FORMAT = "lks-sdd-state/1"
PREFIX = "docs/lks-sdd/00-control/history/states/"
LINK = re.compile(re.escape(PREFIX) + r"([0-9a-f]{64})/tree/(.+)")
MAX_FILES = 100000
MAX_MANIFEST = 32 * 1024 * 1024


def bucket(path): return f"{int(sha(path.encode())[:2], 16) % 64:02x}"


def name(identity):
    if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{64}", identity): raise ContractError("Exact state hash required")
    return PREFIX + identity + "/state.json"


@evaluated
def prepare(root, sources, changes):
    from capacity import require
    require("state_files", len(sources), MAX_FILES, "State file budget exceeded")
    entries = {}
    for path, digest in sorted(sources.items()):
        raw = read_bytes(root, path, limit=64*1024*1024, package_data=True)
        if sha(raw) != digest: raise ContractError("State source changed: " + path)
        entries[path] = prepare_object(root, raw, changes)
    identity = fingerprint(entries)
    require("state_manifest_bytes", len(canonical(entries)), MAX_MANIFEST, "State manifest budget exceeded")
    grouped = {}
    for path, ref in entries.items(): grouped.setdefault(bucket(path), {})[path] = ref
    parts, part_bytes = {}, 0
    for key, files in sorted(grouped.items()):
        raw = canonical({"format": "lks-sdd-state-part/1", "files": files})
        part_bytes += len(raw)
        require("state_manifest_bytes", part_bytes, MAX_MANIFEST, "State parts byte budget exceeded")
        parts[key] = prepare_object(root, raw, changes)
    value = canonical({"format": FORMAT, "identity": identity, "parts": parts})
    target = name(identity)
    existing = Path(root)/target
    if existing.exists():
        if manifest(root, identity)["files"] != entries: raise ContractError("Contradictory documentary state")
    else: changes[target] = value
    return identity


@evaluated
def manifest(root, identity):
    try:
        return _manifest(root, identity)
    except (ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise ContractError("Invalid documentary state manifest") from exc


def _manifest(root, identity):
    from capacity import require
    from v2_contract import path_at
    path = path_at(root, name(identity))
    maximum = require("state_manifest_bytes", path.stat().st_size, MAX_MANIFEST, "State manifest budget exceeded")
    value = json.loads(read_bytes(root, name(identity), limit=maximum))
    if not isinstance(value, dict) or set(value) not in ({"format", "identity", "files"}, {"format", "identity", "parts"}):
        raise ContractError("Invalid documentary state manifest")
    entries = value.get("files")
    if "parts" in value:
        if "files" in value or not isinstance(value["parts"], dict) or len(value["parts"]) > 64:
            raise ContractError("Ambiguous/invalid state parts")
        refs = value["parts"]
        for key, ref in refs.items():
            if key not in {f"{i:02x}" for i in range(64)}: raise ContractError("Invalid state part key")
            object_path(ref)
        require("state_manifest_bytes", sum(ref["bytes"] for ref in refs.values()), MAX_MANIFEST, "State parts byte budget exceeded")
        entries = {}
        for key, ref in refs.items():
            part = json.loads(read_object(root, ref))
            if set(part) != {"format", "files"} or part["format"] != "lks-sdd-state-part/1" or not isinstance(part["files"], dict):
                raise ContractError("Invalid state part")
            for path, content in part["files"].items():
                if path in entries or bucket(path) != key: raise ContractError("State part collision")
                entries[path] = content
                require("state_files", len(entries), MAX_FILES, "State file budget exceeded")
    if value.get("format") != FORMAT or value.get("identity") != identity or not isinstance(entries, dict):
        raise ContractError("Invalid documentary state")
    require("state_files", len(entries), MAX_FILES, "State file budget exceeded")
    for path, ref in entries.items():
        relative_parts(path, package_data=True); object_path(ref)
    if fingerprint(entries) != identity: raise ContractError("Documentary state altered")
    return {"format": FORMAT, "identity": identity, "files": entries, "parts": value.get("parts", {})}


def linked(root, path, limit):
    from capacity import require
    match = LINK.fullmatch(path)
    if not match: raise ContractError("Invalid historical state link")
    identity, source = match.groups()
    value = manifest(root, identity)
    if source not in value["files"]: raise ContractError("Unresolved historical state link")
    ref = value["files"][source]
    if ref["bytes"] > limit:
        if limit != 4 * 1024 * 1024: raise ContractError("Historical state source exceeds budget")
        require("source_bytes", ref["bytes"], limit, "Historical state source exceeds budget")
    return read_object(root, ref)


def dependencies(root, path):
    identity, source = LINK.fullmatch(path).groups()
    ref = manifest(root, identity)["files"][source]
    result = {name(identity): sha(read_bytes(root, name(identity), limit=MAX_MANIFEST)), object_path(ref): ref["sha256"]}
    for part in manifest(root, identity)["parts"].values(): result[object_path(part)] = part["sha256"]
    return result


@evaluated
def export(root, identity, destination):
    import tempfile
    import shutil
    from v2_history import _publish_directory
    from v2_storage import write_one
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination.exists() or destination == root or root in destination.parents or destination in root.parents:
        raise ContractError("Export needs a new directory outside the consumer")
    value = manifest(root, identity)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".state-export-", dir=destination.parent))
    try:
        for path, ref in value["files"].items(): write_one(stage, path, read_object(root, ref))
        _publish_directory(stage, destination)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return {"state": identity, "destination": str(destination), "files": len(value["files"])}
