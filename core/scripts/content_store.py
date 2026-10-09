"""Versioned, bounded content references. Objects are data, never authority."""
from __future__ import annotations

import json
import re

from v2_contract import ContractError, canonical, path_at, read_bytes, relative_parts, sha
from path_utils import publish_new_file

OBJECTS = ".lks-sdd/objects/sha256/"
FORMAT = "lks-sdd-object/1"
LIMIT = 64 * 1024 * 1024


def reference(data: bytes) -> dict:
    if len(data) > LIMIT:
        raise ContractError("Content object exceeds byte budget")
    digest = sha(data)
    return {"format": FORMAT, "sha256": digest, "bytes": len(data)}


def object_path(ref: dict) -> str:
    if (not isinstance(ref, dict) or set(ref) != {"format", "sha256", "bytes"}
            or ref.get("format") != FORMAT or not isinstance(ref.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])
            or type(ref.get("bytes")) is not int or not 0 <= ref["bytes"] <= LIMIT):
        raise ContractError("Invalid or unsupported content reference")
    return OBJECTS + ref["sha256"]


def read_object(root, ref: dict) -> bytes:
    name = object_path(ref)
    raw = read_bytes(root, name, limit=ref["bytes"])
    if len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]:
        raise ContractError("Content object integrity mismatch: " + ref["sha256"])
    return raw


def prepare_object(root, raw: bytes, changes: dict) -> dict:
    """Prepare missing immutable objects without writing during a preview."""
    ref = reference(raw)
    name = object_path(ref)
    if name in changes:
        if changes[name] != raw:
            raise ContractError("Conflicting content object")
    elif path_at(root, name, missing=True).exists():
        read_object(root, ref)
    else:
        changes[name] = raw
    return ref


def publish_object(root, name: str, raw: bytes) -> None:
    """Publish complete bytes atomically without replacing an existing object.

    A competing writer may publish the same hash first. Verify its bytes; never
    repair/replace damaged content as a side effect of an unrelated transaction.
    """
    ref = reference(raw)
    if name != object_path(ref):
        raise ContractError("Content objects are immutable")
    path = path_at(root, name, missing=True)
    if path.exists():
        read_object(root, ref)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path_at(root, name, missing=True)
    try:
        publish_new_file(path, raw, prefix=".lks-object-")
    except FileExistsError:
        read_object(root, ref)


def validate_inventory(root, value: dict) -> dict:
    if not isinstance(value, dict) or len(value) > 50000:
        raise ContractError("Invalid or excessive technical inventory")
    for name, digest in value.items():
        relative_parts(name, package_data=True)
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ContractError("Invalid inventory digest")
    return value


def prepare_inventory(root, value: dict, changes: dict) -> dict:
    validate_inventory(root, value)
    raw = canonical({"format": "lks-sdd-inventory/1", "files": value})
    if len(raw) > 16 * 1024 * 1024:
        raise ContractError("Inventory object exceeds byte budget")
    return prepare_object(root, raw, changes)


def inventory(root, meta: dict, field: str, *, cache=None, objects=None) -> dict:
    """Read old inline maps and new references; refuse ambiguous representations."""
    ref_field = field + "_ref"
    if field in meta and ref_field in meta:
        raise ContractError("Ambiguous inline and referenced inventory: " + field)
    if ref_field not in meta:
        return validate_inventory(root, meta.get(field, {}))
    ref = meta[ref_field]
    name = object_path(ref)
    if ref["bytes"] > 16 * 1024 * 1024:
        raise ContractError("Inventory object exceeds byte budget")
    key = (name, ref["bytes"])
    if cache is not None and key in cache:
        return cache[key]
    if cache is not None and sum(k[1] for k in cache) + ref["bytes"] > 32 * 1024 * 1024:
        raise ContractError("Referenced inventory byte budget exceeded")
    try:
        if objects is not None and name in objects:
            raw = objects[name]
            if raw is None or len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]: raise ContractError("Overlay inventory integrity mismatch")
        else: raw = read_object(root, ref)
        value = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ContractError("Invalid inventory object") from exc
    if not isinstance(value, dict) or set(value) != {"format", "files"} or value["format"] != "lks-sdd-inventory/1":
        raise ContractError("Unsupported inventory object")
    result = validate_inventory(root, value["files"])
    if cache is not None:
        cache[key] = result
    return result


def validate_references(model, meta: dict, fields: tuple[str, ...], cache: dict, *, objects=None):
    for field in fields:
        if field + "_ref" not in meta and field not in meta:
            continue
        inventory(model.root, meta, field, cache=cache, objects=objects)
        if field + "_ref" in meta:
            ref = meta[field + "_ref"]
            model.hashes[object_path(ref)] = ref["sha256"]
