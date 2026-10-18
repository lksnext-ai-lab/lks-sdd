"""Complete v2 states backed by immutable objects; legacy trees remain readable."""
from __future__ import annotations

import json
import ctypes
import re
import os
from pathlib import Path
import shutil
import tempfile
import sys

from content_store import prepare_object, read_object, object_path
from v2_contract import ContractError, HISTORY, READER, VERSION, _read_regular, canonical, fingerprint, path_at, read_bytes, relative_parts, sha
from object_zip import evaluated

FORMAT = "lks-sdd-history-cas/1"


def manifest_path(revision):
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ContractError("Exact historical snapshot hash required")
    return HISTORY + "/" + revision[:16] + "/snapshot.json"


def read_manifest(root, revision, *, raw=None):
    try:
        result = json.loads(read_bytes(root, manifest_path(revision)) if raw is None else raw)
        sources = result["sources"]
        if (result.get("schema_version") != VERSION or result.get("snapshot") != revision
                or result.get("state") != "historical" or not isinstance(sources, dict) or len(sources) > 10000):
            raise ContractError("Historical snapshot identity/inventory mismatch")
        storage = result.get("storage_format")
        if storage not in {None, FORMAT}:
            raise ContractError("Unsupported historical storage format")
        if result.get("reader", READER) != READER:
            raise ContractError("Unsupported historical reader")
        hashes = {}
        for source, entry in sources.items():
            relative_parts(source)
            expected_path = manifest_path(revision).rsplit("/", 1)[0] + "/tree/" + source
            if entry["path"] != expected_path or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                raise ContractError("Invalid historical source path/hash")
            if storage == FORMAT and entry["object"]["sha256"] != entry["sha256"]:
                raise ContractError("Historical object identity mismatch")
            if storage == FORMAT:
                object_path(entry["object"])
                if entry["object"]["bytes"] > 16 * 1024 * 1024:
                    raise ContractError("Historical object exceeds read budget")
            hashes[source] = entry["sha256"]
        if fingerprint({"reader": result.get("reader", READER), "sources": hashes}) != revision:
            raise ContractError("Historical manifest integrity mismatch")
        return result
    except (ValueError, KeyError, TypeError) as exc:
        raise ContractError("Invalid historical manifest: " + str(exc)) from exc


def source_bytes(root, manifest, source, *, limit=16 * 1024 * 1024):
    entry = manifest["sources"][source]
    if manifest.get("storage_format") == FORMAT and entry["object"]["bytes"] > limit:
        raise ContractError("Historical source exceeds read budget: " + source)
    raw = (read_object(root, entry["object"]) if manifest.get("storage_format") == FORMAT
           else _read_regular(root, entry["path"], limit=limit))
    if sha(raw) != entry["sha256"]:
        raise ContractError("Historical content altered: " + source)
    return raw


def _linked_manifest(root, relative):
    match = re.fullmatch(re.escape(HISTORY) + r"/([0-9a-f]{16})/tree/(.+)", relative)
    if not match:
        raise ContractError("Missing source: " + relative)
    prefix, source = match.groups()
    try:
        name = HISTORY + "/" + prefix + "/snapshot.json"
        raw = read_bytes(root, name)
        identity = json.loads(raw)["snapshot"]
        manifest_path(identity)
    except (ValueError, KeyError, TypeError) as exc:
        raise ContractError("Invalid historical link manifest") from exc
    if identity[:16] != prefix:
        raise ContractError("Historical link identity mismatch")
    manifest = read_manifest(root, identity, raw=raw)
    if source not in manifest["sources"]:
        raise ContractError("Unresolved historical link: " + relative)
    return name, raw, manifest, source


def virtual_source(root, relative, *, limit=16 * 1024 * 1024):
    """Resolve and verify CAS or legacy historical links against their manifest."""
    _, _, manifest, source = _linked_manifest(root, relative)
    return source_bytes(root, manifest, source, limit=limit)


def link_dependencies(root, relative):
    """Pin the exact metadata and object needed to resolve a historical link."""
    name, raw, manifest, source = _linked_manifest(root, relative)
    result = {name: sha(raw)}
    if manifest.get("storage_format") == FORMAT:
        ref = manifest["sources"][source]["object"]
        result[object_path(ref)] = ref["sha256"]
    return result


@evaluated
def history_changes(model):
    revision = model.snapshot()
    name = manifest_path(revision)
    if len(model.hashes) > 10000:
        raise ContractError("Historical source inventory exceeds bound")
    existing = read_manifest(model.root, revision) if path_at(model.root, name, missing=True).exists() else None
    changes, mapping = {}, {}
    for source, digest in sorted(model.hashes.items()):
        raw = read_bytes(model.root, source, limit=16 * 1024 * 1024)
        if sha(raw) != digest:
            raise ContractError("History source changed since load: " + source)
        if existing:
            source_bytes(model.root, existing, source)
            continue
        ref = prepare_object(model.root, raw, changes)
        mapping[source] = {"path": name.rsplit("/", 1)[0] + "/tree/" + source,
                           "sha256": digest, "object": ref}
    if existing:
        return revision, {}
    changes[name] = canonical({"schema_version": VERSION, "storage_format": FORMAT, "reader": READER,
                               "snapshot": revision, "sources": mapping, "state": "historical"})
    if len(changes[name]) > 4 * 1024 * 1024:
        raise ContractError("Historical manifest exceeds byte budget")
    return revision, changes


def historical(root, revision):
    manifest = read_manifest(root, revision)
    documents = []
    for source, entry in manifest["sources"].items():
        raw = source_bytes(root, manifest, source)
        documents.append({"source": source, **entry, "text": raw.decode("utf-8") if source.endswith(".md") else None})
    return {"status": "available", "snapshot": revision, "storage_format": manifest.get("storage_format", "tree/legacy"),
            "documents": documents, "writes": []}


@evaluated
def restore_changes(root, revision):
    """Build an exact isolated tree for inspection/export; never replace active docs."""
    manifest = read_manifest(root, revision)
    return {source: source_bytes(root, manifest, source) for source in manifest["sources"]}


def _publish_directory(stage, destination):
    """Atomically expose an export without replacing a competing destination."""
    if os.name == "nt":
        os.rename(stage, destination)
        return
    # POSIX rename silently replaces empty directories. Require a native
    # exclusive rename; unsupported systems/filesystems fail without a fallback.
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "linux" and hasattr(library, "renameat2"):
        function = library.renameat2
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        arguments = (-100, os.fsencode(stage), -100, os.fsencode(destination), 1)  # AT_FDCWD, RENAME_NOREPLACE
    elif sys.platform == "darwin" and hasattr(library, "renamex_np"):
        function = library.renamex_np
        function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        arguments = (os.fsencode(stage), os.fsencode(destination), 4)  # RENAME_EXCL
    else:
        raise ContractError("Atomic exclusive historical export is unavailable on this platform")
    function.restype = ctypes.c_int
    if function(*arguments) != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(destination))


@evaluated
def export_history(root, revision, destination):
    """Reconstruct byte-identical sources in a new directory outside the consumer."""
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if destination == root or root in destination.parents or destination in root.parents or destination.exists():
        raise ContractError("Historical export needs a new directory outside the consumer")
    manifest = read_manifest(root, revision)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".lks-history-export-", dir=destination.parent))
    try:
        from v2_storage import write_one
        for source in manifest["sources"]:
            write_one(stage, source, source_bytes(root, manifest, source))
        for source, entry in manifest["sources"].items():
            if sha(read_bytes(stage, source, limit=16 * 1024 * 1024)) != entry["sha256"]:
                raise ContractError("Historical export integrity mismatch")
        _publish_directory(stage, destination)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return {"status": "exported", "snapshot": revision, "destination": str(destination),
            "files": len(manifest["sources"]), "consumer_writes": []}
