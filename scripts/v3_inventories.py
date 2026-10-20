"""Technical representations only; canonical metadata and normative hashes stay intact."""
import copy

from content_store import inventory, prepare_inventory, validate_references
from v2_contract import ContractError, fingerprint, relative_parts

KINDS = {"execution", "checkpoint", "analysis", "evidence", "problem", "receipt", "decision", "migration"}
FIELDS = ("baseline", "baseline_files", "files", "source_hashes")
MAP_KINDS = {"execution", "checkpoint"}
SUBJECT_LIMIT = 20000


def subject(root, value, *, model=None, cache=None, objects=None):
    if not isinstance(value, dict) or set(value) not in ({"scope", "files", "digest"}, {"scope", "files_ref", "digest"}):
        raise ContractError("Invalid technical subject representation")
    scope = value["scope"]
    if not isinstance(scope, list) or scope != sorted(set(scope)):
        raise ContractError("Invalid subject scope")
    from capacity import require
    require("subject_entries", len(scope), SUBJECT_LIMIT, "Invalid subject scope")
    for path in scope: relative_parts(path)
    files = inventory(root, value, "files", cache=cache, objects=objects)
    # Keep one observable map per physical inventory, rather than wrapping a copy
    # for every resolved event. The weak parent links are attached by Element.
    from v3_contract import _observe
    files = _observe(files)
    if cache is not None and "files_ref" in value:
        from content_store import object_path
        ref = value["files_ref"]
        cache[(object_path(ref), ref["bytes"])] = files
    require("subject_entries", len(files), SUBJECT_LIMIT, "Subject inventory/digest mismatch")
    if fingerprint(files) != value["digest"]:
        raise ContractError("Subject inventory/digest mismatch")
    if model is not None:
        validate_references(model, value, ("files",), cache, objects=objects)
    return {"scope": scope, "files": files, "digest": value["digest"]}


def subjects(data):
    """Recognized event fields, including typed dependency artifacts. Never arbitrary JSON."""
    if "subject" in data and not (data.get("legacy") and not isinstance(data["subject"], dict)):
        yield data, "subject"
    dependencies = data.get("dependencies", {})
    if isinstance(dependencies, dict):
        for row in dependencies.values():
            if isinstance(row, dict) and isinstance(row.get("artifact"), dict):
                yield row, "artifact"


def externalize(root, kind, data, changes):
    if kind not in KINDS: return data
    result = copy.deepcopy(data)
    for field in FIELDS if kind in MAP_KINDS else ():
        if field in result and isinstance(result[field], dict):
            if field + "_ref" in result: raise ContractError("Ambiguous technical inventory")
            result[field + "_ref"] = prepare_inventory(root, result.pop(field), changes)
    for parent, field in subjects(result):
        value = parent[field]
        normalized = subject(root, value)
        parent[field] = {"scope": normalized["scope"], "digest": normalized["digest"],
                         "files_ref": prepare_inventory(root, normalized["files"], changes)}
    return result


def resolve(model, element, cache, *, objects=None):
    if element.kind not in KINDS: return
    raw = element.meta["data"]
    if element.kind == "receipt" and raw.get("purpose") == "usage-observation":
        from v3_usage import validate_receipt
        validate_receipt(model, element, objects=objects)
    if element.kind == "migration" and "inventory_ref" in raw:
        import json
        from content_store import read_object, object_path
        from source_inventory import MIGRATION_CATALOG_BYTES, MIGRATION_PATH_LIMIT
        ref = raw["inventory_ref"]
        if ref["bytes"] > MIGRATION_CATALOG_BYTES: raise ContractError("Migration inventory budget exceeded")
        value = json.loads(read_object(model.root, ref))
        if not isinstance(value, dict) or value.get("format") != "lks-sdd-migration-inventory/1" or not isinstance(value.get("entries"), list) or len(value["entries"]) > MIGRATION_PATH_LIMIT:
            raise ContractError("Invalid migration inventory")
        hashes = {row["path"]: row["sha256"] for row in value["entries"]}
        if len(hashes) != len(value["entries"]) or fingerprint(hashes) != raw["source"]["snapshot"]:
            raise ContractError("Migration source catalog altered")
        model.hashes[object_path(ref)] = ref["sha256"]
    if element.kind in MAP_KINDS: validate_references(model, raw, FIELDS, cache, objects=objects)
    result = copy.deepcopy(raw)
    for parent, field in subjects(result):
        parent[field] = subject(model.root, parent[field], model=model, cache=cache, objects=objects)
    element.resolved_data = result
