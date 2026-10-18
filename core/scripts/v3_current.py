"""Public operating boundary: current method, explicit governance and pinned runtime."""
from v3_presentation_guard import reviewed
import copy
import importlib.util
import json
from pathlib import Path

from v2_contract import ContractError

FORMATS = ["lks-sdd-object/1", "lks-sdd-object-zip/1", "lks-sdd-inventory/1", "lks-sdd-state/1", "lks-sdd-packet/1", "lks-sdd-usage/1"]
READ_ONLY = set("decision-view validate status trace context readiness review interventions analysis-findings adopt-inspect migration-diagnose migration-continuation old-branch catalog history state-history usage-report usage-export".split())
READ_ONLY.add("work-prepare")
SPECIAL = {"init", "migration-preview", "configure-collaboration", "apply", "recover", "rollback"}


def require_requests(model, keys):
    from v31_review import policy_for
    for key in set(keys):
        request = model.get(key, "request")
        if not policy_for(model, request).data.get("collaboration") or not request.data.get("coordination"):
            raise ContractError("needs-migration: request configuration pending: " + request.uid)


def require_current(root, data=None):
    from v3_contract import load
    from v31_review import validate_config, policy_for
    from runtime_doctor import check
    from v2_storage import ensure_idle
    ensure_idle(root)
    from v3_cli import is_v3
    if not is_v3(root):
        raise ContractError("needs-migration: prepare migration-preview to method 3.1.0")
    model = load(root).require_valid()
    if model.project.data["method_version"] != "3.1.0":
        raise ContractError("needs-migration: prepare migration-preview to method 3.1.0")
    validate_config(policy_for(model).data.get("collaboration"))
    # Every request must have adopted its own policy/configuration before further work.
    selected = set()
    data = data or {}
    if data.get("request"): selected.add(model.get(data["request"], "request").uid)
    if data.get("task"): selected.add(model.get(data["task"], "task").data["request"])
    if data.get("plan"): selected.add(model.get(data["plan"], "plan").data["request"])
    for field in ("tasks", "requests", "units"):
        for key in data.get(field, []):
            entry = model.get(key)
            if entry.kind == "request": selected.add(entry.uid)
            elif entry.data.get("request"): selected.add(entry.data["request"])
    for field in ("problem", "correction"):
        if data.get(field):
            entry = model.get(data[field])
            if entry.data.get("request"): selected.add(entry.data["request"])
    for item in data.get("items", []):
        key = item.get("meta", {}).get("data", {}).get("request", item.get("data", {}).get("request"))
        if key in model.elements: selected.add(key)
    require_requests(model, selected)
    result = check(Path(root))
    if result["status"] != "valid":
        raise ContractError("needs-runtime-update: " + str(result["errors"]))
    lock = json.loads((Path(root)/".lks-sdd/distribution-lock.json").read_bytes())
    if lock["project_schema"] != "3.1" or not set(FORMATS) <= set(lock.get("storage_formats", [])):
        raise ContractError("needs-runtime-update: missing current storage capabilities")
    return model


def runtime_changes(root, bundle, origin=None):
    if not bundle: raise ContractError("Incluya runtime_bundle compatible para el corte completo")
    spec = importlib.util.spec_from_file_location("current_runtime_install", Path(__file__).resolve().parents[1]/"distribution/install.py")
    installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
    try:
        prepared = installer.plan(Path(bundle), Path(root), "copilot", contract_transition=(origin, "3.1") if origin else None,
                                  payload_limit=64*1024*1024)
    except ValueError as exc: raise ContractError(str(exc)) from exc
    changes = {e["path"]: bytes.fromhex(e["content"]) if e["content"] is not None else None for e in prepared["changes"]}
    raw = changes.get(".lks-sdd/distribution-lock.json")
    if raw is None:
        raw = (Path(root)/".lks-sdd/distribution-lock.json").read_bytes()
    lock = json.loads(raw)
    if lock.get("project_schema") != "3.1" or not set(FORMATS) <= set(lock.get("storage_formats", [])):
        raise ContractError("El bundle no acredita las capacidades actuales de almacenamiento")
    return changes


def declared_collaboration(value, owner, members):
    """Explicit symbolic declarations map to newly allocated UUIDs; no chosen people."""
    from v31_review import validate_config
    if not isinstance(value, dict): raise ContractError("Declare colaboración y personas del destino 3.1")
    value = copy.deepcopy(value)
    aliases = {"$owner": owner["meta"]["uid"]}
    for key, member in members:
        if not key or key in aliases: raise ContractError("Clave de miembro ausente o duplicada")
        aliases[key] = member["meta"]["uid"]
    roster = value.get("defaults", {})
    for field in ("responsible", "integration_validator", "functional_validator"):
        roster[field] = aliases.get(roster.get(field), roster.get(field))
    for reviewer in roster.get("reviewers", []):
        reviewer["member"] = aliases.get(reviewer.get("member"), reviewer.get("member"))
    validate_config(value)
    return value


@reviewed('migration-preview')
def upgrade(root, data):
    from v3_cli import is_v3
    if not is_v3(root):
        from v3_migration import preview
        return preview(root, data["actor_name"], data["profile"], data["controls"], data["statement"],
                       target=data["target"], runtime_bundle=data.get("runtime_bundle"), method="3.1.0",
                       collaboration=data.get("collaboration"), members=data.get("members"),
                       packet_directory=data.get("packet_directory"))
    from v3_contract import load
    from v31_review import configure
    model = load(root).require_valid()
    return configure(root, data["actor"], data["collaboration"], data["statement"],
                     requests=[r.uid for r in model.by_kind("request") if not r.retired],
                     runtime_bundle=data.get("runtime_bundle"), pin_runtime=True,
                     packet_directory=data.get("packet_directory"))


def diagnose(root, *, include_inventory=False):
    from v3_cli import is_v3
    from v2_storage import ensure_idle
    ensure_idle(root)
    if not is_v3(root):
        from v3_migration import diagnose as older
        result = older(root)
        if not include_inventory and "sources" in result:
            result["source_count"] = len(result.pop("sources"))
        return result
    from v3_contract import load
    from runtime_doctor import check
    model = load(root).require_valid()
    runtime = check(Path(root))
    try:
        require_current(root)
        status = "current"
    except ContractError:
        status = "needs-migration"
    return {"status": status, "format": model.index()["schema_version"], "method": model.project.data["method_version"],
            "runtime": runtime, "target": "3.1.0", "writes": [],
            "next": "Continue the selected authorized task" if status == "current" else "Prepare migration-preview with confirmed configuration and compatible runtime_bundle"}
