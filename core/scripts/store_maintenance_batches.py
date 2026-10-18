"""Read-only /2 inventory and deterministic manifest; execution is not enabled here.

The legacy /1 writer deliberately does not accept this manifest. A /2-capable
pinned recoverer and ownership/revalidation are required before physical effects.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import time

import object_zip as codec
import store_json_inspector as inspector
import store_maintenance as legacy
from path_utils import filesystem_root, is_within_filesystem_path, _comparison_path
from source_inventory import linked, signature
from v2_contract import ContractError, canonical, path_at, sha, _read_regular
from v2_storage import ensure_idle

FORMAT = "lks-sdd-store-maintenance/2"
OBJECT_LIMIT = BATCH_BYTES = 64 * 1024 * 1024
BATCH_OBJECTS = 4096
OBJECT_COUNT = 50_000
BACKUP_LIMIT = 66 * 1024 * 1024
MANIFEST_LIMIT = 12 * 1024 * 1024
JOURNAL_LIMIT = 16 * 1024 * 1024
WORK_SECONDS = 600
SPACE_POLICY = "full-logical-backup-and-restore-plus-new-packs-and-atomic-overhead/1"


class BudgetExceeded(ContractError):
    pass


def _budget(deadline):
    if time.monotonic() >= deadline:
        raise BudgetExceeded("Complete maintenance preview exceeds command time budget")


def _checkpoint(phase):
    """Fault-injection boundary; no side effects or external callbacks."""


def _pinned(root):
    before = _read_regular(root, legacy.PIN, limit=4 * 1024 * 1024)
    digest = legacy._reader(root)
    after = _read_regular(root, legacy.PIN, limit=4 * 1024 * 1024)
    if before != after or sha(before) != digest:
        raise ContractError("Pinned reader changed during maintenance validation")
    return digest


def _absolute(value):
    """Expand existing 8.3 ancestors even when the final destination is new."""
    path = filesystem_root(value, force_extended=True)
    for ancestor in [path, *path.parents]:
        try:
            info = ancestor.lstat()
        except FileNotFoundError:
            continue
        except NotADirectoryError as exc:
            raise ContractError("Maintenance destination traverses a non-directory") from exc
        if linked(info) or (ancestor != path and not stat.S_ISDIR(info.st_mode)):
            raise ContractError("Maintenance destination traverses a link or non-directory")
    existing, tail = path, []
    while not existing.exists():
        if existing.parent == existing:
            raise ContractError("Maintenance destination volume is unavailable")
        tail.append(existing.name)
        existing = existing.parent
    normalized = _comparison_path(existing) if os.name == "nt" else existing.absolute()
    for name in reversed(tail):
        normalized /= name
    return filesystem_root(normalized, force_extended=True)


def _destination(root, value):
    return legacy._external(root, _absolute(value))


def _destinations(backup, restore, stage=None):
    paths = [backup, restore] + ([stage] if stage is not None else [])
    for index, path in enumerate(paths):
        if os.path.lexists(path):
            raise ContractError("Maintenance destinations must be new")
        for other in paths[:index]:
            if is_within_filesystem_path(path, other) or is_within_filesystem_path(other, path):
                raise ContractError("Maintenance destinations must be distinct and non-overlapping")


def _physical(root, deadline):
    """Bounded physical membership and native identities, without body allocation."""
    result = {"loose": {}, "packs": {}, "directories": {}}
    container = path_at(root, ".lks-sdd/objects", missing=True)
    if container.exists():
        info = container.lstat()
        if linked(info) or not stat.S_ISDIR(info.st_mode):
            raise ContractError("Invalid maintenance object container")
        result["directories"]["container"] = signature(info)
        with os.scandir(container) as entries:
            for entry in entries:
                _budget(deadline)
                if entry.name not in {"sha256", "packs"}:
                    raise ContractError("Unrecognized path in maintenance object container")
    else:
        result["directories"]["container"] = None
    for kind, relative, maximum in (("loose", codec.OBJECTS, OBJECT_COUNT),
                                    ("packs", codec.PACKS, codec.MAX_PACKS)):
        _budget(deadline)
        directory = path_at(root, relative.rstrip("/"), missing=True)
        try:
            observed = directory.lstat()
        except FileNotFoundError:
            result["directories"][kind] = None
            continue
        if linked(observed) or not stat.S_ISDIR(observed.st_mode):
            raise ContractError("Invalid maintenance object directory")
        result["directories"][kind] = signature(observed)
        found = result[kind]
        with os.scandir(directory) as entries:
            for entry in entries:
                _budget(deadline)
                if len(found) >= maximum:
                    raise ContractError("Maintenance physical enumeration budget exceeded")
                # Windows DirEntry.stat may omit native file IDs (st_ino/dev).
                # Compare the same fresh lstat representation used by readers.
                info = Path(entry.path).lstat()
                digest = entry.name[:-4] if kind == "packs" and entry.name.endswith(".zip") else entry.name
                valid_name = codec.HASH.fullmatch(digest) and (kind == "loose" or entry.name == digest + ".zip")
                if (not valid_name or linked(info) or not stat.S_ISREG(info.st_mode)
                        or info.st_size > (OBJECT_LIMIT if kind == "loose" else codec.MAX_PACK)):
                    raise ContractError("Unrecognized or excessive maintenance object: " + entry.name)
                found[entry.name] = signature(info)
        if signature(directory.lstat()) != result["directories"][kind]:
            raise ContractError("Object directory changed during maintenance enumeration")
    if container.exists() and signature(container.lstat()) != result["directories"]["container"]:
        raise ContractError("Object container changed during maintenance enumeration")
    return result


def _identity(root, name, expected):
    if signature(path_at(root, name).lstat()) != expected:
        raise ContractError("Physical object changed during maintenance preview")


def _read_object(root, digest, state, deadline):
    _budget(deadline)
    loose = state["physical"]["loose"].get(digest)
    if loose is not None:
        _identity(root, codec.OBJECTS + digest, loose)
    # read_logical freshly verifies every physical representation, including
    # redundant packed copies. Evaluation caches only their bounded indexes.
    raw = codec.read_logical(root, codec.OBJECTS + digest, OBJECT_LIMIT)
    if len(raw) != state["logical"][digest] or sha(raw) != digest:
        raise ContractError("Logical object integrity mismatch")
    if loose is not None:
        _identity(root, codec.OBJECTS + digest, loose)
    _budget(deadline)
    return raw


def _catalog(root, deadline):
    physical = _physical(root, deadline)
    codec.invalidate(root)
    locations = codec._locations(root, checkpoint=lambda: _budget(deadline))
    _budget(deadline)
    logical = {digest: identity[3] for digest, identity in physical["loose"].items()}
    indexed_packs = set()
    for digest, copies in locations.items():
        _budget(deadline)
        for name, identity, _, size, _ in copies:
            if identity != physical["packs"].get(Path(name).name):
                raise ContractError("Object ZIP changed during maintenance inventory")
            if digest in logical and logical[digest] != size:
                raise ContractError("Contradictory physical object sizes")
            logical[digest] = size
            indexed_packs.add(Path(name).name)
        if len(logical) > OBJECT_COUNT:
            raise ContractError("Maintenance logical object count exceeded")
    if indexed_packs != set(physical["packs"]):
        raise ContractError("Incomplete maintenance ZIP inventory")
    packs = {}
    for filename, identity in sorted(physical["packs"].items()):
        _budget(deadline)
        name = codec.PACKS + filename
        _identity(root, name, identity)
        raw = _read_regular(root, name, limit=codec.MAX_PACK)
        if sha(raw) != filename[:-4]:
            raise ContractError("Existing ZIP hash mismatch")
        packs[filename[:-4]] = len(raw)
        del raw
        _identity(root, name, identity)
    state = {"physical": physical, "logical": logical, "locations": locations,
             "existing_packs": packs, "structured_nodes_checked": 0,
             "structured_references_checked": 0}
    return state


def _inventory(root, deadline):
    state = _catalog(root, deadline)
    logical = state["logical"]
    for digest in sorted(logical):
        raw = _read_object(root, digest, state, deadline)
        prepared = inspector.prepare(raw, deadline=deadline)
        del raw  # Required before joining Unicode normalization chunks.
        nodes, references = inspector.inspect_prepared(prepared, logical, deadline=deadline)
        del prepared
        state["structured_nodes_checked"] += nodes
        state["structured_references_checked"] += references
    _checkpoint("inventory-verified")
    return state


def _ranges(rows):
    first = size = count = 0
    for index, row in enumerate(rows):
        if row["bytes"] > BATCH_BYTES:
            raise ContractError("Individual object cannot fit a maintenance batch")
        if count and (size + row["bytes"] > BATCH_BYTES or count >= BATCH_OBJECTS):
            yield first, count
            first, size, count = index, 0, 0
        size += row["bytes"]
        count += 1
    if count:
        yield first, count


def _pack_groups(rows, first, count):
    members = []
    size = 22
    for index in range(first, first + count):
        row = rows[index]
        if not row["loose"] or row["bytes"] > codec.TARGET or row.get("packed"):
            continue
        if members and (size + row["bytes"] + 204 > codec.TARGET or len(members) >= codec.MAX_ENTRIES):
            yield members
            members, size = [], 22
        members.append(index)
        size += row["bytes"] + 204
    if members:
        yield members


def _batches(root, rows, state, deadline):
    batches = []
    for first, count in _ranges(rows):
        _budget(deadline)
        bodies = {rows[index]["sha256"]: _read_object(root, rows[index]["sha256"], state, deadline)
                  for index in range(first, first + count)}
        raw = legacy._backup_bytes(bodies)
        if len(raw) > BACKUP_LIMIT:
            raise ContractError("Maintenance backup batch exceeds physical byte budget")
        batch = {"first": first, "count": count,
                 "logical_bytes": sum(len(body) for body in bodies.values()),
                 "backup": {"sha256": sha(raw), "bytes": len(raw)}, "packs": []}
        del raw
        for members in _pack_groups(rows, first, count):
            _budget(deadline)
            raw = codec.encode({rows[index]["sha256"]: bodies[rows[index]["sha256"]] for index in members})
            batch["packs"].append({"sha256": sha(raw), "bytes": len(raw), "members": members})
            del raw
        del bodies
        batches.append(batch)
        _checkpoint("batch-described")
    return batches


def _volume(path):
    parent = path
    while not parent.exists():
        if parent.parent == parent:
            raise ContractError("Maintenance destination volume is unavailable")
        parent = parent.parent
    # st_dev identifies mounted volumes, including mounts below a drive root.
    return str(parent.stat().st_dev), parent


def _space(root, backup, restore, rows, batches, *, admit=True):
    pack_bytes = sum(pack["bytes"] for batch in batches for pack in batch["packs"])
    largest_pack = max((pack["bytes"] for batch in batches for pack in batch["packs"]), default=0)
    backup_bytes = sum(batch["backup"]["bytes"] for batch in batches)
    largest_backup = max((batch["backup"]["bytes"] for batch in batches), default=0)
    components = {
        "consumer": pack_bytes + 3 * JOURNAL_LIMIT + largest_pack,
        "backup_dir": backup_bytes + MANIFEST_LIMIT + largest_backup,
        # Restore staging becomes the destination by rename; do not count twice.
        "restore": sum(row["bytes"] for row in rows),
    }
    paths = {"consumer": root, "backup_dir": backup, "restore": restore}
    volumes, observations = {}, []
    for label, path in paths.items():
        device, parent = _volume(path)
        volume = volumes.setdefault(device, {"device": device, "required_bytes": 0, "destinations": []})
        volume["required_bytes"] += components[label]
        volume["destinations"].append(label)
    for device, volume in sorted(volumes.items()):
        _, parent = _volume(paths[volume["destinations"][0]])
        free = shutil.disk_usage(parent).free
        if admit and free < volume["required_bytes"]:
            raise ContractError("Insufficient space for full maintenance backup, restore and atomic overhead")
        observations.append({"device": device, "free_bytes": free})
    return {"rule": SPACE_POLICY, "components": components, "volumes": list(sorted(volumes.values(), key=lambda v: v["device"]))}, observations


def _stable(root, state, pin, deadline, guard=ensure_idle):
    _budget(deadline)
    guard(root)
    if _pinned(root) != pin:
        raise ContractError("Pinned reader changed during maintenance preview")
    if _physical(root, deadline) != state["physical"]:
        raise ContractError("Physical membership or identity changed during maintenance preview")
    _budget(deadline)


@codec.evaluated
def preview(root, backup_dir, restore):
    """Prepare a complete immutable /2 manifest without writing any destination.

    This component checks the existing pinned ZIP reader. The public /2 command
    must additionally require a verified /2 recoverer before accepting authority.
    """
    return _prepare(root, backup_dir, restore, deadline=time.monotonic() + WORK_SECONDS, guard=ensure_idle)


def _prepare(root, backup_dir, restore, *, deadline, guard, state_sink=None):
    """Internal reconstruction; mutators supply an independently verified owner."""
    root = _absolute(root)
    if not root.is_dir():
        raise ContractError("Maintenance consumer must be an existing directory")
    guard(root)
    pin = _pinned(root)
    backup, restore = _destination(root, backup_dir), _destination(root, restore)
    _destinations(backup, restore)
    state = _inventory(root, deadline)
    rows = []
    eligible = 0
    for digest, size in sorted(state["logical"].items()):
        row = {"sha256": digest, "bytes": size, "loose": digest in state["physical"]["loose"]}
        if digest in state["locations"]:
            row["packed"] = True
        rows.append(row)
        eligible += bool(row["loose"] and size <= codec.TARGET)
    if not eligible:
        raise ContractError("No eligible loose objects to compact")
    batches = _batches(root, rows, state, deadline)
    space, observed_space = _space(root, backup, restore, rows, batches)
    manifest = {"format": FORMAT, "operation": "physical-compaction", "consumer": str(root),
                "pin_sha256": pin, "destinations": {"backup_dir": str(backup), "restore": str(restore)},
                "objects": rows, "existing_packs": state["existing_packs"], "batches": batches,
                "limits": {"object_bytes": OBJECT_LIMIT, "objects": OBJECT_COUNT, "batch_bytes": BATCH_BYTES,
                           "batch_objects": BATCH_OBJECTS, "backup_bytes": BACKUP_LIMIT,
                           "manifest_bytes": MANIFEST_LIMIT, "journal_bytes": JOURNAL_LIMIT,
                           "json_nodes_per_object": 1_000_000, "command_work_seconds": WORK_SECONDS},
                "space_policy": space,
                "structured_references_checked": state["structured_references_checked"],
                "removal_authorization": "separate-exact-preview-hash-required"}
    raw = canonical(manifest)
    if len(raw) > MANIFEST_LIMIT:
        raise ContractError("Complete maintenance manifest exceeds byte budget")
    key = sha(raw)
    del raw
    stage = restore.with_name(restore.name + ".lks-stage-" + key[:16])
    _checkpoint("before-final-validation")
    # Repeat destination/link and volume/admission checks after all preparation.
    for path in (backup, restore, stage):
        if _destination(root, path) != path:
            raise ContractError("Maintenance destinations changed during preview")
    _destinations(backup, restore, stage)
    current_space, observed_space = _space(root, backup, restore, rows, batches)
    if current_space != space:
        raise ContractError("Maintenance destination volumes changed during preview")
    _stable(root, state, pin, deadline, guard)
    if state_sink is not None:
        state_sink.append(state)
    return {"manifest": manifest, "preview_hash": key, "status": "preview",
            "restore_stage": str(stage), "observed_space": observed_space, "consumer_writes": [],
            "structured_nodes_checked": state["structured_nodes_checked"],
            "execution_enabled": False}
