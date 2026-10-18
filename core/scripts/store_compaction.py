"""Explicit /2 maintenance. One immutable scope, one shared owner, two authorities."""
from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import time
import zipfile

import object_zip as codec
import store_json_inspector as inspector
import store_maintenance as legacy
import store_maintenance_batches as planner
from path_utils import is_within_filesystem_path
from source_inventory import linked, signature
from v2_contract import ContractError, canonical, fingerprint, path_at, sha, _read_regular
from v2_storage import PENDING, ensure_idle

FORMAT = planner.FORMAT
TERMINAL = {"compacted", "retained-originals", "rejected-stale-preview"}
PHASES = {"owned", "preparing", "awaiting-removal-authorization", "removing"} | TERMINAL
MODULES = ("store_compaction.py", "store_maintenance_batches.py", "store_json_inspector.py",
           "store_maintenance.py", "v2_storage.py", "v3_storage.py", "path_utils.py", "source_inventory.py",
           "v3_cli.py", "lks_sdd.py", "runtime_doctor.py")


def _checkpoint(phase):
    """Local fault-injection seam; never introduces waits or model calls."""


def reader(root):
    pin = planner._pinned(root)
    lock = json.loads(_read_regular(root, legacy.PIN, limit=4 * 1024 * 1024))
    declaration = json.loads(_read_regular(root, lock["runtime"] + "/distribution/dual.json",
                                          limit=1024 * 1024, package_data=True))
    if FORMAT not in lock["storage_formats"] or FORMAT not in declaration.get("storage_formats", []):
        raise ContractError("Pinned runtime lacks verified maintenance /2 recovery; update explicitly before preparing /2")
    for module in MODULES:
        name = "scripts/" + module
        raw = _read_regular(root, lock["runtime"] + "/" + name, limit=4 * 1024 * 1024, package_data=True)
        if sha(raw) != lock["runtime_files"].get(name):
            raise ContractError("Pinned maintenance /2 recovery integrity mismatch: " + module)
    if planner._pinned(root) != pin:
        raise ContractError("Pinned maintenance runtime changed during validation")
    return pin


def _paths(root, manifest, key):
    destinations = manifest["destinations"]
    backup = planner._destination(root, destinations["backup_dir"])
    restore = planner._destination(root, destinations["restore"])
    stage = planner._destination(root, restore.with_name(restore.name + ".lks-stage-" + key[:16]))
    paths = (backup, restore, stage)
    for index, path in enumerate(paths):
        for other in paths[:index]:
            if is_within_filesystem_path(path, other) or is_within_filesystem_path(other, path):
                raise ContractError("Maintenance destinations overlap")
    return paths


def _limits():
    return {"object_bytes": planner.OBJECT_LIMIT, "objects": planner.OBJECT_COUNT,
            "batch_bytes": planner.BATCH_BYTES, "batch_objects": planner.BATCH_OBJECTS,
            "backup_bytes": planner.BACKUP_LIMIT, "manifest_bytes": planner.MANIFEST_LIMIT,
            "journal_bytes": planner.JOURNAL_LIMIT, "json_nodes_per_object": 1_000_000,
            "command_work_seconds": planner.WORK_SECONDS}


def _hash(value):
    return isinstance(value, str) and codec.HASH.fullmatch(value) is not None


def is_v2_input(value):
    return isinstance(value, dict) and isinstance(value.get("manifest"), dict) and value["manifest"].get("format") == FORMAT


def pending_v2(root, authorized=None):
    name = PENDING if path_at(root, PENDING, missing=True).exists() else _receipt(authorized) if _hash(authorized) else None
    if name is None or not path_at(root, name, missing=True).exists():
        return False
    return json.loads(_read_regular(root, name, limit=128 * 1024 * 1024)).get("schema_version") == FORMAT


def summary(manifest):
    rows = manifest["objects"]
    return {"format": manifest["format"], "objects": len(rows), "logical_bytes": sum(row["bytes"] for row in rows),
            "batches": len(manifest["batches"]),
            "eligible_loose_objects": sum(row["loose"] and row["bytes"] <= codec.TARGET for row in rows),
            "new_packs": sum(len(batch["packs"]) for batch in manifest["batches"]),
            "removal_authorization": manifest["removal_authorization"]}


def transport_guard(root, action, data, authorized, output):
    if output is None:
        return
    root, output = planner._absolute(root), planner._absolute(output)
    if action == "store-preview":
        destinations = [data.get("backup_dir", data.get("backup")), data.get("restore")]
    elif is_v2_input(data):
        destinations = list(_paths(root, data["manifest"], data.get("preview_hash", "")))
    elif action == "store-recover" and pending_v2(root, authorized):
        journal = _load(root, authorized, receipt=not path_at(root, PENDING, missing=True).exists())
        destinations = list(_paths(root, journal["manifest"], authorized))
    else:
        if action == "store-recover" and path_at(root, PENDING, missing=True).exists():
            pending = json.loads(_read_regular(root, PENDING, limit=128 * 1024 * 1024))
            if pending.get("schema_version") == legacy.FORMAT:
                data = pending["preview"]
        destinations = [data.get("backup", {}).get("path") if isinstance(data.get("backup"), dict) else data.get("backup"),
                        data.get("restore"), data.get("restore_stage")]
    for value in filter(None, destinations):
        destination = planner._destination(root, value)
        if is_within_filesystem_path(output, destination) or is_within_filesystem_path(destination, output):
            raise ContractError("Output must be separate from maintenance backup, restore and staging")


def validate(root, manifest, authorized):
    """Validate structure independently of a matching caller-supplied hash."""
    required = {"format", "operation", "consumer", "pin_sha256", "destinations", "objects", "existing_packs",
                "batches", "limits", "space_policy", "structured_references_checked", "removal_authorization"}
    if (not isinstance(manifest, dict) or set(manifest) != required or not _hash(authorized)
            or len(canonical(manifest)) > planner.MANIFEST_LIMIT or fingerprint(manifest) != authorized
            or manifest["format"] != FORMAT or manifest["operation"] != "physical-compaction"
            or not _hash(manifest["pin_sha256"]) or manifest["consumer"] != str(planner._absolute(root))
            or manifest["limits"] != _limits()
            or manifest["removal_authorization"] != "separate-exact-preview-hash-required"):
        raise ContractError("Invalid /2 manifest or exact maintenance authorization")
    rows = manifest["objects"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= planner.OBJECT_COUNT:
        raise ContractError("Invalid maintenance object table")
    previous = ""
    for row in rows:
        if (not isinstance(row, dict) or set(row) not in ({"sha256", "bytes", "loose"}, {"sha256", "bytes", "loose", "packed"})
                or not _hash(row.get("sha256")) or row["sha256"] <= previous
                or type(row.get("bytes")) is not int or not 0 <= row["bytes"] <= planner.OBJECT_LIMIT
                or type(row.get("loose")) is not bool or ("packed" in row and row["packed"] is not True)):
            raise ContractError("Invalid or unsorted maintenance object row")
        previous = row["sha256"]
    existing = manifest["existing_packs"]
    if (not isinstance(existing, dict) or len(existing) > codec.MAX_PACKS
            or any(not _hash(key) or type(size) is not int or not 0 < size <= codec.MAX_PACK for key, size in existing.items())):
        raise ContractError("Invalid pre-existing maintenance pack table")
    planned = manifest["batches"]
    ranges = list(planner._ranges(rows))
    if not isinstance(planned, list) or len(planned) != len(ranges):
        raise ContractError("Invalid maintenance batch coverage")
    pack_hashes = set(existing)
    for batch, (first, count) in zip(planned, ranges):
        logical_bytes = sum(row["bytes"] for row in rows[first:first + count])
        if (not isinstance(batch, dict) or set(batch) != {"first", "count", "logical_bytes", "backup", "packs"}
                or type(batch["first"]) is not int or type(batch["count"]) is not int
                or batch["first"] != first or batch["count"] != count or batch["logical_bytes"] != logical_bytes
                or not isinstance(batch["backup"], dict) or set(batch["backup"]) != {"sha256", "bytes"}
                or not _hash(batch["backup"]["sha256"])
                or batch["backup"]["bytes"] != logical_bytes + count * 204 + 22
                or batch["backup"]["bytes"] > planner.BACKUP_LIMIT):
            raise ContractError("Invalid maintenance batch or backup descriptor")
        groups = list(planner._pack_groups(rows, first, count))
        if not isinstance(batch["packs"], list) or len(batch["packs"]) != len(groups):
            raise ContractError("Invalid maintenance packed coverage")
        for pack, members in zip(batch["packs"], groups):
            if (not isinstance(pack, dict) or set(pack) != {"sha256", "bytes", "members"}
                    or not _hash(pack["sha256"]) or pack["sha256"] in pack_hashes
                    or pack["members"] != members or any(type(index) is not int for index in pack["members"])
                    or pack["bytes"] != sum(rows[index]["bytes"] + 204 for index in members) + 22
                    or pack["bytes"] > codec.MAX_PACK):
                raise ContractError("Invalid maintenance pack descriptor")
            pack_hashes.add(pack["sha256"])
    if (not isinstance(manifest["destinations"], dict) or set(manifest["destinations"]) != {"backup_dir", "restore"}
            or any(not isinstance(value, str) for value in manifest["destinations"].values())
            or type(manifest["structured_references_checked"]) is not int or manifest["structured_references_checked"] < 0):
        raise ContractError("Invalid maintenance destinations or reference count")
    backup, restore, _ = _paths(root, manifest, authorized)
    expected_space, _ = planner._space(root, backup, restore, rows, planned, admit=False)
    if manifest["space_policy"] != expected_space:
        raise ContractError("Maintenance space policy or destination volume changed")
    return manifest


def _receipt(key):
    return legacy.RECEIPTS + key + ".json"


def _temporary_directory(root, key):
    return path_at(root, legacy.RECEIPTS + ".tmp-" + key, missing=True)


def _journal_valid(root, journal, key):
    if (not isinstance(journal, dict) or set(journal) != {"schema_version", "manifest", "preview_hash", "phase", "removal_authorized", "progress"}
            or journal["schema_version"] != FORMAT or journal["preview_hash"] != key
            or journal["phase"] not in PHASES or type(journal["removal_authorized"]) is not bool):
        raise ContractError("Invalid maintenance /2 journal")
    validate(root, journal["manifest"], key)
    progress = journal["progress"]
    if (not isinstance(progress, dict) or set(progress) != {"prepared", "removed"}
            or any(type(value) is not int for value in progress.values())
            or not 0 <= progress["removed"] <= progress["prepared"] <= len(journal["manifest"]["batches"])):
        raise ContractError("Invalid maintenance progress")
    phase = journal["phase"]
    count = len(journal["manifest"]["batches"])
    if ((phase == "owned" and progress != {"prepared": 0, "removed": 0})
            or (phase in {"awaiting-removal-authorization", "removing", "compacted"} and progress["prepared"] != count)
            or (phase == "compacted" and progress["removed"] != count)
            or (phase not in {"removing", "compacted"} and (progress["removed"] or journal["removal_authorized"]))
            or (phase in {"removing", "compacted"} and not journal["removal_authorized"])):
        raise ContractError("Contradictory maintenance authority or phase")
    return journal


def _load(root, key, *, receipt=False):
    if not _hash(key):
        raise ContractError("Exact maintenance hash required")
    return _journal_valid(root, json.loads(_read_regular(root, _receipt(key) if receipt else PENDING,
                                                        limit=planner.JOURNAL_LIMIT)), key)


def _owned(root, journal):
    current = _read_regular(root, PENDING, limit=planner.JOURNAL_LIMIT)
    if current != canonical(journal):
        raise ContractError("Shared maintenance ownership changed")


def _next_states(current):
    """Recognize only exact uncommitted next-journal prefixes, never authority."""
    yield current
    phase = current["phase"]
    if phase in TERMINAL:
        return
    retained = copy.deepcopy(current)
    retained.update(phase="retained-originals", removal_authorized=False)
    retained["progress"]["removed"] = 0
    yield retained
    following = copy.deepcopy(current)
    if phase == "owned":
        following["phase"] = "preparing"
        yield following
        following = copy.deepcopy(current)
        following["phase"] = "rejected-stale-preview"
    elif phase == "preparing":
        if following["progress"]["prepared"] < len(current["manifest"]["batches"]):
            following["progress"]["prepared"] += 1
        else:
            following["phase"] = "awaiting-removal-authorization"
    elif phase == "awaiting-removal-authorization":
        following.update(phase="removing", removal_authorized=True)
    elif phase == "removing":
        if following["progress"]["removed"] < len(current["manifest"]["batches"]):
            following["progress"]["removed"] += 1
        else:
            following["phase"] = "compacted"
    yield following


def _atomic(path, raw, temporary, *, replace=False, candidates=(), existing_ok=True, before_publish=None):
    """Resume an operation-bound partial temporary; never replace foreign bytes."""
    path, temporary = planner._absolute(path), planner._absolute(temporary)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        if not existing_ok:
            raise FileExistsError(path)
        if _read_regular(path.parent, path.name, limit=len(raw)) != raw:
            raise ContractError("Maintenance destination conflict; foreign or damaged bytes preserved")
        if temporary.exists():
            part = _read_regular(temporary.parent, temporary.name, limit=max(len(raw), planner.JOURNAL_LIMIT))
            if not raw.startswith(part):
                raise ContractError("Conflicting maintenance temporary preserved")
            temporary.unlink()
        return
    if temporary.exists():
        part = _read_regular(temporary.parent, temporary.name, limit=max(len(raw), planner.JOURNAL_LIMIT))
        if not raw.startswith(part):
            if not any(canonical(candidate).startswith(part) for candidate in candidates):
                raise ContractError("Unrecognized maintenance temporary preserved")
            temporary.unlink()  # Recognized but uncommitted journal state grants no authority.
            part = b""
    else:
        part = b""
    mode = "ab" if temporary.exists() else "xb"
    with temporary.open(mode) as stream:
        _checkpoint("temporary-created")
        stream.write(memoryview(raw)[len(part):])
        stream.flush()
        os.fsync(stream.fileno())
    _checkpoint("temporary-fsynced")
    if before_publish is not None:
        before_publish()
    if replace:
        os.replace(temporary, path)
    elif os.name == "nt":
        os.rename(temporary, path)
    else:
        os.link(temporary, path)
        temporary.unlink()


def _save(root, current, following):
    _owned(root, current)
    _journal_valid(root, following, current["preview_hash"])
    raw = canonical(following)
    if len(raw) > planner.JOURNAL_LIMIT:
        raise ContractError("Maintenance /2 journal exceeds byte budget")
    _need(root, 2 * len(raw))
    temporary = _temporary_directory(root, current["preview_hash"]) / "transaction.json.tmp"
    _atomic(path_at(root, PENDING), raw, temporary, replace=True, candidates=_next_states(current),
            before_publish=lambda: _owned(root, current))
    current.clear()
    current.update(following)


def _advance(root, journal, *, phase=None, prepared=None, removed=None, removal_authorized=None):
    following = copy.deepcopy(journal)
    if phase is not None:
        following["phase"] = phase
    if prepared is not None:
        following["progress"]["prepared"] = prepared
    if removed is not None:
        following["progress"]["removed"] = removed
    if removal_authorized is not None:
        following["removal_authorized"] = removal_authorized
    _save(root, journal, following)


def _result(journal, status=None):
    manifest, key = journal["manifest"], journal["preview_hash"]
    terminal = journal["phase"] in TERMINAL
    return {"status": status or journal["phase"], "format": FORMAT, "preview_hash": key,
            "phase": journal["phase"], "progress": dict(journal["progress"]),
            "batches": len(manifest["batches"]), "pending": None if terminal else PENDING,
            "receipt": _receipt(key) if terminal else None, "removal_authorized": journal["removal_authorized"],
            "functional_authority": "unchanged", "next": "Inspect terminal receipt" if terminal else
            "Use store-recover with the same hash; removal requires separate exact authorization"}


@codec.evaluated
def preview(root, backup_dir, restore):
    deadline = time.monotonic() + planner.WORK_SECONDS
    root = planner._absolute(root)
    reader(root)
    result = planner._prepare(root, backup_dir, restore, deadline=deadline, guard=ensure_idle)
    validate(root, result["manifest"], result["preview_hash"])
    planner._budget(deadline)
    result["execution_enabled"] = True
    result["summary"] = summary(result["manifest"])
    return result


def status(root, authorized):
    root = planner._absolute(root)
    pending = path_at(root, PENDING, missing=True).exists()
    journal = _load(root, authorized, receipt=not pending)
    result = _result(journal)
    result.update(read_only=True, current_integrity="not-asserted-by-status")
    return result


def _need(path, amount):
    _, parent = planner._volume(path)
    if shutil.disk_usage(parent).free < amount:
        raise ContractError("Insufficient space for next maintenance write; pending state preserved")


def _batch_rows(manifest, batch):
    return manifest["objects"][batch["first"]:batch["first"] + batch["count"]]


def _backup_path(backup, number):
    return backup / f"batch-{number:04d}.zip"


def _directory(path, allowed, *, exact=False):
    path = planner._absolute(path)
    if not path.exists():
        return set()
    if not path.is_dir():
        raise ContractError("Maintenance directory conflicts with existing content")
    found = set()
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.name not in allowed:
                raise ContractError("Unknown maintenance directory content preserved: " + entry.name)
            info = Path(entry.path).lstat()
            if linked(info) or not stat.S_ISREG(info.st_mode):
                raise ContractError("Non-regular maintenance directory content preserved")
            found.add(entry.name)
    if exact and found != allowed:
        raise ContractError("Incomplete maintenance directory inventory")
    return found


def _destinations_state(root, journal):
    manifest, key = journal["manifest"], journal["preview_hash"]
    backup, restore, stage = _paths(root, manifest, key)
    names = {f"batch-{number:04d}.zip" for number in range(len(manifest["batches"]))} | {"manifest.json"}
    _directory(backup, names | {name + ".tmp" for name in names})
    if restore.exists() and stage.exists():
        raise ContractError("Both restore and staging exist; conflicting content preserved")
    digests = {row["sha256"] for row in manifest["objects"]}
    if restore.exists():
        _directory(restore, digests, exact=True)
    else:
        _directory(stage, digests | {digest + ".tmp" for digest in digests})
    temporary = _temporary_directory(root, key)
    owned = {pack["sha256"] + ".zip.tmp" for batch in manifest["batches"] for pack in batch["packs"]}
    _directory(temporary, owned | {"transaction.json.tmp", key + ".json.tmp"})
    return backup, restore, stage


def _pin(root, journal):
    _owned(root, journal)
    if reader(root) != journal["manifest"]["pin_sha256"]:
        raise ContractError("Pinned maintenance /2 runtime changed; restore exact pin before recovery")


def _scope(root, journal, deadline, *, require_originals=False):
    """One fresh scoped verification per invocation, never a store scan per batch."""
    _pin(root, journal)
    manifest = journal["manifest"]
    state = planner._catalog(root, deadline)
    for digest, size in manifest["existing_packs"].items():
        if state["existing_packs"].get(digest) != size:
            raise ContractError("Pre-existing maintenance ZIP missing or changed")
    complete = journal["progress"]["prepared"]
    for number, batch in enumerate(manifest["batches"]):
        for pack in batch["packs"]:
            present = state["existing_packs"].get(pack["sha256"])
            if (present is not None and present != pack["bytes"]) or (number < complete and present is None):
                raise ContractError("Prepared maintenance ZIP missing or changed")
    logical = {row["sha256"]: row["bytes"] for row in manifest["objects"]}
    for row in manifest["objects"]:
        digest = row["sha256"]
        if state["logical"].get(digest) != row["bytes"]:
            raise ContractError("Authorized logical maintenance object missing or changed")
        if (row["loose"] and digest not in state["physical"]["loose"] and
                (require_originals or row["bytes"] > codec.TARGET or not journal["removal_authorized"])):
            raise ContractError("Original missing before authorized maintenance withdrawal")
        raw = planner._read_object(root, digest, state, deadline)
        prepared = inspector.prepare(raw, deadline=deadline)
        del raw
        inspector.inspect_prepared(prepared, logical, deadline=deadline)
        del prepared
    if planner._physical(root, deadline) != state["physical"]:
        raise ContractError("Physical membership changed during recovery verification")
    _pin(root, journal)
    return state


def _backup_bodies(backup, number, manifest):
    batch = manifest["batches"][number]
    raw = _read_regular(backup, _backup_path(backup, number).name, limit=planner.BACKUP_LIMIT)
    if len(raw) != batch["backup"]["bytes"] or sha(raw) != batch["backup"]["sha256"]:
        raise ContractError("Maintenance backup batch integrity mismatch; damaged copy preserved")
    if len(raw) < 22:
        raise ContractError("Invalid maintenance backup footer")
    footer = struct.unpack("<4s4H2LH", raw[-22:])
    count = batch["count"]
    if (footer[:5] != (b"PK\x05\x06", 0, 0, count, count) or footer[5] != count * 110
            or footer[6] + footer[5] != len(raw) - 22 or footer[7]):
        raise ContractError("Invalid or excessive maintenance backup directory")
    rows = _batch_rows(manifest, batch)
    bodies = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if len(entries) != count or [entry.filename for entry in entries] != [row["sha256"] for row in rows]:
                raise ContractError("Maintenance backup batch membership mismatch")
            for entry, row in zip(entries, rows):
                if (entry.orig_filename != entry.filename or entry.file_size != row["bytes"]
                        or entry.compress_type != zipfile.ZIP_STORED or entry.flag_bits or entry.extra or entry.comment
                        or entry.create_system != 3 or stat.S_IFMT(entry.external_attr >> 16) != stat.S_IFREG):
                    raise ContractError("Invalid maintenance backup member")
                body = archive.read(entry)
                if sha(body) != row["sha256"]:
                    raise ContractError("Maintenance backup object integrity mismatch")
                bodies[row["sha256"]] = body
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ContractError("Invalid maintenance backup batch") from exc
    return bodies


def _verify_pack(root, pack):
    name = codec.PACKS + pack["sha256"] + ".zip"
    with codec._opened(root, name) as (stream, size, identity):
        if size != pack["bytes"] or sha(stream.read()) != pack["sha256"]:
            raise ContractError("Maintenance packed copy integrity mismatch")
    return identity


def _verify_bodies(root, manifest, batch, bodies, restore, deadline):
    for pack in batch["packs"]:
        _verify_pack(root, pack)
    for row in _batch_rows(manifest, batch):
        planner._budget(deadline)
        digest, expected = row["sha256"], bodies[row["sha256"]]
        if codec.read_logical(root, codec.OBJECTS + digest, planner.OBJECT_LIMIT) != expected:
            raise ContractError("Active object differs from verified backup")
        if _read_regular(restore, digest, limit=planner.OBJECT_LIMIT) != expected:
            raise ContractError("Restored object differs from verified backup")


def _verify_all(root, journal, deadline):
    backup, restore, stage = _destinations_state(root, journal)
    source = restore if restore.exists() else stage
    expected_manifest = canonical({"manifest": journal["manifest"], "preview_hash": journal["preview_hash"]})
    if _read_regular(backup, "manifest.json", limit=planner.MANIFEST_LIMIT + 1024) != expected_manifest:
        raise ContractError("External maintenance manifest integrity mismatch")
    for number, batch in enumerate(journal["manifest"]["batches"]):
        planner._budget(deadline)
        bodies = _backup_bodies(backup, number, journal["manifest"])
        _verify_bodies(root, journal["manifest"], batch, bodies, source, deadline)
        del bodies
    digests = {row["sha256"] for row in journal["manifest"]["objects"]}
    _directory(source, digests, exact=True)
    _pin(root, journal)
    return backup, restore, stage


def _prepare_batch(root, journal, number, state, destinations, deadline):
    manifest, key = journal["manifest"], journal["preview_hash"]
    batch = manifest["batches"][number]
    backup, restore, stage = destinations
    _pin(root, journal)
    path = _backup_path(backup, number)
    if not path.exists():
        bodies = {row["sha256"]: planner._read_object(root, row["sha256"], state, deadline)
                  for row in _batch_rows(manifest, batch)}
        raw = legacy._backup_bytes(bodies)
        del bodies
        if len(raw) != batch["backup"]["bytes"] or sha(raw) != batch["backup"]["sha256"]:
            raise ContractError("Reconstructed backup differs from authorized preview")
        _need(backup, len(raw))
        _atomic(path, raw, path.with_name(path.name + ".tmp"))
        del raw
    _checkpoint("after-backup")
    if path.with_name(path.name + ".tmp").exists():
        raw = _read_regular(backup, path.name, limit=planner.BACKUP_LIMIT)
        _atomic(path, raw, path.with_name(path.name + ".tmp"))
        del raw
    bodies = _backup_bodies(backup, number, manifest)
    for pack in batch["packs"]:
        planner._budget(deadline)
        name = codec.PACKS + pack["sha256"] + ".zip"
        path = path_at(root, name, missing=True)
        if not path.exists():
            raw = codec.encode({manifest["objects"][index]["sha256"]:
                                bodies[manifest["objects"][index]["sha256"]] for index in pack["members"]})
            if sha(raw) != pack["sha256"] or len(raw) != pack["bytes"]:
                raise ContractError("Reconstructed pack differs from authorized preview")
            _need(root, len(raw) + planner.JOURNAL_LIMIT)
            _atomic(path, raw, _temporary_directory(root, key) / (pack["sha256"] + ".zip.tmp"))
            del raw
        _verify_pack(root, pack)
        temporary = _temporary_directory(root, key) / (pack["sha256"] + ".zip.tmp")
        if temporary.exists():
            raw = _read_regular(root, name, limit=codec.MAX_PACK)
            _atomic(path, raw, temporary)
            del raw
    codec.invalidate(root)
    _checkpoint("after-publish")
    destination = restore if restore.exists() else stage
    _restore_batch(destination, bodies, deadline)
    _verify_bodies(root, manifest, batch, bodies, destination, deadline)
    del bodies
    _checkpoint("batch-verified-before-checkpoint")
    _advance(root, journal, prepared=number + 1)
    _checkpoint("batch-prepared")


def _restore_batch(destination, bodies, deadline):
    """Only verified backup bodies enter this writer; no consumer read fallback."""
    destination.mkdir(parents=True, exist_ok=True)
    for digest, raw in bodies.items():
        planner._budget(deadline)
        _need(destination, 0 if (destination / digest).exists() else len(raw))
        _atomic(destination / digest, raw, destination / (digest + ".tmp"))
        _checkpoint("during-restore")


def _finish_terminal(root, journal):
    key = journal["preview_hash"]
    _pin(root, journal)
    raw = canonical(journal)
    path = path_at(root, _receipt(key), missing=True)
    _need(root, len(raw))
    _checkpoint("before-receipt")
    temporary = _temporary_directory(root, key)
    _atomic(path, raw, temporary / (key + ".json.tmp"))
    _checkpoint("after-receipt")
    # Never delete unknown staging material; a retained-originals receipt may
    # explicitly preserve partial temporaries, which grant no recovery authority.
    leftovers = list(temporary.iterdir()) if temporary.exists() else []
    if not leftovers and temporary.exists():
        temporary.rmdir()
    _pin(root, journal)
    path_at(root, PENDING).unlink()
    codec.invalidate(root)
    result = _result(journal)
    if journal["phase"] == "retained-originals":
        result.update(backup_status="partial-or-unverified; inspect external destinations",
                      preserved_temporaries=len(leftovers))
    return result


def _remove(root, journal, deadline):
    manifest = journal["manifest"]
    backup, restore, _ = _paths(root, manifest, journal["preview_hash"])
    for number in range(journal["progress"]["removed"], len(manifest["batches"])):
        planner._budget(deadline)
        _pin(root, journal)
        batch = manifest["batches"][number]
        backup_path = _backup_path(backup, number)
        backup_identity = signature(backup_path.lstat())
        bodies = _backup_bodies(backup, number, manifest)
        if signature(backup_path.lstat()) != backup_identity:
            raise ContractError("Backup changed during withdrawal verification")
        _verify_bodies(root, manifest, batch, bodies, restore, deadline)
        for row in _batch_rows(manifest, batch):
            planner._budget(deadline)
            if not row["loose"] or row["bytes"] > codec.TARGET:
                continue
            digest, raw = row["sha256"], bodies[row["sha256"]]
            if signature(backup_path.lstat()) != backup_identity:
                raise ContractError("Verified backup changed before withdrawal")
            if _read_regular(restore, digest, limit=planner.OBJECT_LIMIT) != raw:
                raise ContractError("Restored copy changed before withdrawal")
            path = path_at(root, codec.OBJECTS + digest, missing=True)
            if path.exists() and _read_regular(root, codec.OBJECTS + digest, limit=planner.OBJECT_LIMIT) != raw:
                raise ContractError("Changed original preserved during maintenance withdrawal")
            copies = codec._locations(root).get(digest, ())
            if not copies or any(codec._read_packed(root, digest, copy, planner.OBJECT_LIMIT) != raw for copy in copies):
                raise ContractError("Fresh verified packed coverage required before withdrawal")
            # Recovery also verifies the backup/restoration of already absent
            # originals; absence after persisted authority is not a new deletion.
            if path.exists():
                path.unlink()
                _checkpoint("during-remove")
        del bodies
        _advance(root, journal, removed=number + 1)
        _checkpoint("batch-removed")
    _scope(root, journal, deadline)
    _verify_all(root, journal, deadline)
    _advance(root, journal, phase="compacted")
    return _finish_terminal(root, journal)


def _run(root, journal, deadline, *, remove=False, retain=False):
    if journal["phase"] in TERMINAL:
        if journal["phase"] == "compacted":
            _scope(root, journal, deadline)
            _verify_all(root, journal, deadline)
        elif journal["phase"] == "retained-originals":
            _scope(root, journal, deadline, require_originals=True)
            _paths(root, journal["manifest"], journal["preview_hash"])
        return _finish_terminal(root, journal)
    if retain:
        _scope(root, journal, deadline, require_originals=True)
        # External backup/staging conflicts do not require withdrawal or hold a
        # healthy active store hostage. Preserve them and certify only originals.
        _paths(root, journal["manifest"], journal["preview_hash"])
        _advance(root, journal, phase="retained-originals", removed=0, removal_authorized=False)
        return _finish_terminal(root, journal)
    verified_state = []
    if journal["phase"] == "owned":
        _checkpoint("before-revalidation")
        backup, restore, _ = _paths(root, journal["manifest"], journal["preview_hash"])
        try:
            fresh = planner._prepare(root, backup, restore, deadline=deadline,
                                     guard=lambda checked: _owned(checked, journal), state_sink=verified_state)
            if fresh["manifest"] != journal["manifest"]:
                raise ContractError("Maintenance preview is stale")
            del fresh
        except ContractError as exc:
            if time.monotonic() >= deadline:
                raise
            _advance(root, journal, phase="rejected-stale-preview")
            return {**_finish_terminal(root, journal), "cause": str(exc)}
        _advance(root, journal, phase="preparing")
        _checkpoint("revalidated")
    state = verified_state.pop() if verified_state else _scope(root, journal, deadline)
    destinations = _destinations_state(root, journal)
    if journal["phase"] == "preparing":
        backup, restore, stage = destinations
        descriptor = canonical({"manifest": journal["manifest"], "preview_hash": journal["preview_hash"]})
        _need(backup, len(descriptor))
        _atomic(backup / "manifest.json", descriptor, backup / "manifest.json.tmp")
        for number in range(journal["progress"]["prepared"]):
            planner._budget(deadline)
            bodies = _backup_bodies(backup, number, journal["manifest"])
            _verify_bodies(root, journal["manifest"], journal["manifest"]["batches"][number], bodies,
                           restore if restore.exists() else stage, deadline)
            del bodies
        for number in range(journal["progress"]["prepared"], len(journal["manifest"]["batches"])):
            _prepare_batch(root, journal, number, state, destinations, deadline)
        _verify_all(root, journal, deadline)
        if not restore.exists():
            from v2_history import _publish_directory
            _publish_directory(stage, restore)
        _checkpoint("restore-published-before-checkpoint")
        _advance(root, journal, phase="awaiting-removal-authorization")
        _checkpoint("awaiting-removal")
    if journal["phase"] == "awaiting-removal-authorization":
        if not remove:
            return _result(journal)
        _verify_all(root, journal, deadline)
        _advance(root, journal, phase="removing", removal_authorized=True)
        _checkpoint("removal-authorized")
    return _remove(root, journal, deadline)


def _resume(root, journal, deadline, **options):
    try:
        return _run(root, journal, deadline, **options)
    except ContractError as exc:
        if isinstance(exc, planner.BudgetExceeded) or str(exc) == "JSON inspection time budget exceeded":
            result = _result(journal, "paused")
            result["cause"] = str(exc)
            return result
        raise


@legacy._writer
@codec.evaluated
def apply(root, plan, authorized):
    deadline = time.monotonic() + planner.WORK_SECONDS
    root = planner._absolute(root)
    if not is_v2_input(plan) or plan.get("preview_hash") != authorized:
        raise ContractError("Input and exact authorized maintenance hash differ")
    manifest = plan["manifest"]
    validate(root, manifest, authorized)
    ensure_idle(root)
    if reader(root) != manifest["pin_sha256"]:
        raise ContractError("Pinned runtime differs from authorized maintenance preview")
    journal = {"schema_version": FORMAT, "manifest": manifest, "preview_hash": authorized,
               "phase": "owned", "removal_authorized": False, "progress": {"prepared": 0, "removed": 0}}
    raw = canonical(journal)
    if len(raw) > planner.JOURNAL_LIMIT:
        raise ContractError("Maintenance /2 journal exceeds byte budget")
    _need(root, 2 * len(raw))
    _checkpoint("before-own")
    try:
        _atomic(path_at(root, PENDING, missing=True), raw,
                _temporary_directory(root, authorized) / "transaction.json.tmp", existing_ok=False)
    except FileExistsError as exc:
        raise ContractError("Another transaction owns the shared pending slot") from exc
    _owned(root, journal)
    _checkpoint("after-own")
    return _resume(root, journal, deadline)


@legacy._writer
@codec.evaluated
def recover(root, authorized, *, remove_authorized=None, finalize_without_removal=False):
    deadline = time.monotonic() + planner.WORK_SECONDS
    root = planner._absolute(root)
    if remove_authorized is not None and remove_authorized != authorized:
        raise ContractError("Removal requires separate authorization of the exact preview hash")
    if finalize_without_removal and remove_authorized is not None:
        raise ContractError("Finalizing without removal cannot authorize removal")
    if not path_at(root, PENDING, missing=True).exists():
        journal = _load(root, authorized, receipt=True)
        if journal["phase"] not in TERMINAL:
            raise ContractError("Nonterminal maintenance receipt")
        return {**_result(journal), "previously_completed": True, "current_integrity": "not-asserted-by-historical-receipt"}
    journal = _load(root, authorized)
    if reader(root) != journal["manifest"]["pin_sha256"]:
        raise ContractError("Restore exact pinned /2 recovery runtime before resuming")
    return _resume(root, journal, deadline, remove=remove_authorized == authorized,
                   retain=finalize_without_removal)
