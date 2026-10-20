"""Explicit, operation-scoped resource consent. Never grants business authority."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
import base64
import copy
import json
import math
import hashlib
import os

from v2_contract import ContractError, canonical, fingerprint, read_bytes
from path_utils import same_filesystem_path, is_within_filesystem_path

REQUEST = "lks-sdd-capacity-request/1"
ACTIVE = ContextVar("lks_sdd_capacity", default=None)
MiB = 1024 * 1024
# These are processing budgets, not permission, integrity or representation checks.
DEFAULTS = {
    "source_bytes": 4 * MiB, "document_bytes": 32 * MiB,
    "document_files": 10000, "source_files": 250000, "source_scan_bytes": 16 * 1024 * MiB,
    "code_files": 20000, "git_paths": 200000, "git_stdout_bytes": 16 * MiB, "git_seconds": 60,
    "inventory_entries": 50000, "subject_entries": 20000,
    "state_files": 100000, "state_manifest_bytes": 32 * MiB,
    "zip_index_bytes": 16 * MiB,
    "packet_files": 100000, "packet_bytes": 2 * 1024 * MiB,
    "usage_batch_bytes": MiB, "usage_batch_count": 1000,
    "usage_window_count": 20000, "usage_window_bytes": 64 * MiB, "usage_material_bytes": 64 * MiB,
}
# Existing on-disk object/packet representations remain bounded and compatible.
CEILINGS = {"source_bytes": 64 * MiB, "state_manifest_bytes": 64 * MiB,
            "usage_batch_bytes": 64 * MiB}


class CapacityRequired(RuntimeError):
    def __init__(self, message, request):
        super().__init__(message)
        self.request = request


def _generation(root):
    """Bind fresh invocations to the official transaction generation, in a stream."""
    from v2_storage import TRANSACTION_STORE
    from v2_contract import path_at
    from source_inventory import signature, linked
    path = path_at(Path(root), TRANSACTION_STORE, missing=True)
    if not path.exists(): return None
    observed = path.lstat()
    if linked(observed) or not path.is_file() or observed.st_size > 128 * MiB:
        raise ContractError("Invalid transaction generation for capacity consent")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if signature(os.fstat(stream.fileno())) != signature(observed):
            raise ContractError("Transaction generation changed before capacity consent")
        while chunk := stream.read(MiB): digest.update(chunk)
        if signature(os.fstat(stream.fileno())) != signature(observed) or signature(path.lstat()) != signature(observed):
            raise ContractError("Transaction generation changed during capacity consent")
    return digest.hexdigest()


def _intent(action, data, authorization=None, root=None):
    if not isinstance(data, dict): raise ContractError("Capacity operation input must be an object")
    if action == "decision-view":
        action, data = data.get("event"), data.get("data", {})
    if not isinstance(data, dict): raise ContractError("Capacity operation data must be an object")
    clean = {k: v for k, v in data.items() if k not in {"presented", "usage_context"}}
    intent = fingerprint({"data": clean, "authorization": authorization})
    return action, fingerprint({"intent": intent, "generation": _generation(root)}) if root is not None else intent


def _check(approval, root, operation=None, intent=None):
    if (not isinstance(approval, dict) or set(approval) != {"request", "approved", "statement"}
            or approval["approved"] is not True or not isinstance(approval["statement"], str)
            or not approval["statement"].strip() or len(approval["statement"]) > 4096):
        raise ContractError("Capacity consent needs an explicit approved user response")
    request = approval["request"]
    if (not isinstance(request, dict) or set(request) != {
            "format", "project", "operation", "intent_sha256", "limits", "reached", "request_sha256"}
            or request["format"] != REQUEST or not isinstance(request["project"], str)
            or not same_filesystem_path(request["project"], root)
            or request["request_sha256"] != fingerprint({k: v for k, v in request.items() if k != "request_sha256"})
            or not isinstance(request["limits"], dict) or set(request["limits"]) != set(DEFAULTS)
            or not isinstance(request["operation"], str)
            or not isinstance(request["intent_sha256"], str) or len(request["intent_sha256"]) != 64):
        raise ContractError("Capacity request altered or belongs to another project")
    for name, value in request["limits"].items():
        if (type(value) is not int or value < DEFAULTS[name]
                or value > CEILINGS.get(name, 2**53 - 1)):
            raise ContractError("Invalid or incompatible capacity allowance: " + name)
    reached = request["reached"]
    if (not isinstance(reached, dict) or set(reached) != {"resource", "observed", "normal"}
            or reached["resource"] not in DEFAULTS
            or any(type(reached[k]) is not int or reached[k] < 0 for k in ("observed", "normal"))
            or reached["normal"] == 0 or reached["observed"] <= reached["normal"]
            or reached["observed"] > request["limits"][reached["resource"]]):
        raise ContractError("Invalid reached capacity description")
    if operation is not None and (operation != request["operation"] or intent != request["intent_sha256"]):
        raise ContractError("Capacity consent is stale for this operation or its inputs")
    return copy.deepcopy(approval)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ContractError("Duplicate field in capacity consent: " + key)
        result[key] = value
    return result


@contextmanager
def session(root, action, data=None, *, approval=None, approval_path=None, authorization=None):
    value = {"root": str(Path(root).resolve()), "action": action, "authorization": authorization,
             "approval_path": approval_path, "supplied": approval, "approval": None, "intent": None}
    token = ACTIVE.set(value)
    try:
        if data is not None: bind(data)
        yield
    finally:
        ACTIVE.reset(token)


def bind(data):
    value = ACTIVE.get()
    if value is None: return
    operation, intent = _intent(value["action"], data, value["authorization"])
    value.update(operation=operation, intent=intent, base_intent=intent, generation_bound=False)
    value["maintenance_v1"] = (value["action"] == "store-preview" and "backup" in data or
                               value["action"] == "store-compact" and (not isinstance(data.get("manifest"), dict) or
                               data["manifest"].get("format") != "lks-sdd-store-maintenance/2"))
    approval = value["supplied"]
    if value["approval_path"]:
        path = Path(value["approval_path"]).absolute()
        root = Path(value["root"])
        if is_within_filesystem_path(path, root):
            raise ContractError("Keep capacity consent outside the consumer")
        approval = json.loads(read_bytes(path.parent, path.name, limit=64 * 1024, package_data=True), object_pairs_hook=_unique)
    if approval is not None:
        value["intent"] = fingerprint({"intent": intent, "generation": _generation(value["root"])})
        value["generation_bound"] = True
        value["approval"] = _check(approval, value["root"], operation, value["intent"])


def limit(name, normal):
    value = ACTIVE.get()
    if value and value.get("maintenance_v1"): return normal
    approval = value.get("approval") if value else None
    if not approval: return normal
    return max(normal, approval["request"]["limits"][name], value.get("extra_limits", {}).get(name, 0))


def require(name, observed, normal, message):
    allowed = limit(name, normal)
    if observed <= allowed: return allowed
    if name not in DEFAULTS: raise ContractError(message)
    ceiling = CEILINGS.get(name)
    if ceiling is not None and observed > ceiling:
        raise ContractError(f"{message}; {observed} exceeds compatible format capacity {ceiling}; "
                            "no resource approval can change this representation")
    value = ACTIVE.get()
    if value is None:
        raise ContractError(message)
    if value.get("maintenance_v1"):
        raise ContractError(message + "; maintenance /1 retains compatible bounds; use explicit /2 backup_dir preparation for new maintenance")
    if not value.get("generation_bound"):
        value["intent"] = fingerprint({"intent": value["base_intent"], "generation": _generation(value["root"])})
        value["generation_bound"] = True
    # A single bounded envelope anticipates the other layers of this operation.
    factor = max(2, 2 ** math.ceil(math.log2(max(observed / max(normal, 1), 1))))
    limits = {key: min(max(limit(key, base), base * factor), CEILINGS.get(key, 2**53 - 1))
              for key, base in DEFAULTS.items()}
    limits["source_bytes"] = 64 * MiB
    limits[name] = max(limits[name], observed)
    request = {"format": REQUEST, "project": value["root"] if value else None,
               "operation": value.get("operation", value["action"]) if value else None,
               "intent_sha256": value["intent"] if value else None, "limits": limits,
               "reached": {"resource": name, "observed": observed, "normal": normal}}
    request["request_sha256"] = fingerprint(request)
    raise CapacityRequired(message, request)


def consent():
    value = ACTIVE.get()
    return copy.deepcopy(value["approval"]) if value and value.get("approval") else None


def legacy_maintenance():
    value = ACTIVE.get()
    if value is not None: value["maintenance_v1"] = True


def compatible(root):
    """An expanded write needs a pinned recoverer that actually carries this policy."""
    from v2_contract import path_at, sha
    pin = path_at(Path(root), ".lks-sdd/distribution-lock.json", missing=True)
    if not pin.exists(): return  # Legacy/library recovery has no current runtime pin.
    lock = json.loads(read_bytes(root, ".lks-sdd/distribution-lock.json"))
    name = "scripts/capacity.py"
    expected = lock.get("runtime_files", {}).get(name)
    if not expected or sha(Path(__file__).read_bytes()) != expected:
        raise ContractError("Capacity consent requires a compatible 4.0.3 pinned recoverer; prepare an explicit runtime update")
    if sha(read_bytes(root, lock["runtime"] + "/" + name, package_data=True)) != expected:
        raise ContractError("Pinned capacity recoverer integrity mismatch")


def reissue(request, action, data, authorized=None):
    result = copy.deepcopy(request)
    result["operation"], result["intent_sha256"] = _intent(action, data, authorized, result["project"])
    result["request_sha256"] = fingerprint({k: v for k, v in result.items() if k != "request_sha256"})
    return result


def _preview(preview, authorized):
    fields = ("operation", "sources", "before", "after", "document_inventory")
    if (not isinstance(preview, dict) or preview.get("preview_hash") != authorized
            or fingerprint({k: preview[k] for k in fields}) != authorized):
        raise ContractError("Capacity recovery requires the exact authorized preview")
    operation = preview["operation"]
    if not operation.startswith("v3:"): return None
    guards = json.loads(base64.b64decode(operation.rsplit(":", 1)[-1], validate=True))
    return guards.get("capacity")


@contextmanager
def recorded(root, approval):
    if approval is None:
        yield
        return
    checked = _check(approval, root)
    outer = ACTIVE.get()
    extra = {}
    if outer and outer.get("approval"):
        if not same_filesystem_path(outer["root"], root):
            raise ContractError("Capacity consent belongs to another project")
        # A separately approved apply/recovery extension can enlarge capacity,
        # but never removes the original transaction's business checks.
        extra = {k: max(v, outer.get("extra_limits", {}).get(k, 0))
                 for k, v in outer["approval"]["request"]["limits"].items()}
    token = ACTIVE.set({"root": str(Path(root).resolve()), "approval": checked, "extra_limits": extra,
                        "action": checked["request"]["operation"], "operation": checked["request"]["operation"],
                        "intent": checked["request"]["intent_sha256"], "generation_bound": True})
    try: yield
    finally: ACTIVE.reset(token)


def for_recovery(request, authorized):
    return reissue(request, "recover", {}, authorized)


@contextmanager
def maintenance_recorded(root, manifest, authorized):
    approval = manifest.get("capacity") if isinstance(manifest, dict) else None
    if approval is not None:
        if fingerprint(manifest) != authorized: raise ContractError("Capacity maintenance preview altered")
        compatible(root)
    with recorded(root, approval): yield


def maintenance_applying(function):
    @wraps(function)
    def run(root, plan, authorized, *args, **kwargs):
        manifest = plan.get("manifest", {})
        with maintenance_recorded(root, manifest, authorized):
            return function(root, plan, authorized, *args, **kwargs)
    return run


def maintenance_recovering(function):
    @wraps(function)
    def run(root, authorized, *args, **kwargs):
        from store_compaction import _load
        from v2_storage import PENDING
        journal = _load(root, authorized, receipt=not (Path(root)/PENDING).exists())
        with maintenance_recorded(root, journal["manifest"], authorized):
            return function(root, authorized, *args, **kwargs)
    return run


def applying(function):
    @wraps(function)
    def run(root, packet, authorized_hash, *args, **kwargs):
        approval = packet.get("guards", {}).get("capacity") if isinstance(packet, dict) else None
        if approval is not None:
            verified = _preview(packet["preview"], authorized_hash)
            if verified != approval: raise ContractError("Capacity guards altered")
        with recorded(root, approval): return function(root, packet, authorized_hash, *args, **kwargs)
    return run


def recovering(function):
    @wraps(function)
    def run(root, authorized_hash, *args, **kwargs):
        from v2_storage import _load_transaction
        receipt = kwargs.get("receipt")
        approval = None
        try:
            journal, _ = _load_transaction(Path(root), authorized_hash, receipt)
        except (ContractError, FileNotFoundError):
            # Maintenance has its own versioned journal/authority dispatcher.
            pass
        else:
            approval = _preview(journal["preview"], authorized_hash)
        with recorded(root, approval): return function(root, authorized_hash, *args, **kwargs)
    return run
