"""Explicit physical compaction. Logical objects and business authority never change."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import zipfile
from contextlib import contextmanager
from functools import wraps

from v2_contract import ContractError, canonical, fingerprint, path_at, read_bytes, sha, _read_regular
from path_utils import filesystem_root, publish_new_file, is_within_filesystem_path
from v2_storage import PENDING, ensure_idle, write_one
import object_zip as codec

FORMAT = "lks-sdd-store-maintenance/1"
LIMIT = 64 * 1024 * 1024
COUNT = 50000
JOURNAL_LIMIT = 16 * 1024 * 1024
RECEIPTS = ".lks-sdd/maintenance/"
PIN = ".lks-sdd/distribution-lock.json"


@contextmanager
def _exclusive(root):
    """Serialize recovery of the SAME pending slot; OS releases on process death.

    This is not another pending journal. Business writers still exclusively own
    transaction.json and cannot start while a maintenance journal occupies it.
    """
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
        kernel.CreateMutexW.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        # Normalize 8.3 aliases AND extended prefixes to one pending path.
        from path_utils import _comparison_path
        name = 'Local\\LKS-SDD-store-' + sha(str(_comparison_path(Path(root))).casefold().encode())
        handle = kernel.CreateMutexW(None,False,name)
        if not handle: raise ContractError('Cannot acquire maintenance writer guard')
        acquired = kernel.WaitForSingleObject(handle,0) in (0,0x80)
        try:
            if not acquired: raise ContractError('Another recovery owns the shared pending slot')
            yield
        finally:
            if acquired: kernel.ReleaseMutex(handle)
            kernel.CloseHandle(handle)
    else:
        import fcntl
        lock = path_at(root,'.lks-sdd/transaction.lock',missing=True)
        lock.parent.mkdir(parents=True,exist_ok=True)
        with lock.open('a+b') as stream:
            try: fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as exc: raise ContractError('Another recovery owns the shared pending slot') from exc
            try: yield
            finally: fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def _writer(function):
    @wraps(function)
    def wrapped(root,*args,**kwargs):
        with _exclusive(root): return function(root,*args,**kwargs)
    return wrapped


def _external(root, value):
    """Reject links before resolving; neither backup nor restore lives in the repo."""
    from source_inventory import linked
    path = filesystem_root(Path(value), force_extended=True)
    for parent in [path, *path.parents]:
        if parent.exists() and linked(parent.lstat()):
            raise ContractError("Maintenance destination traverses a link")
    if is_within_filesystem_path(path, root) or is_within_filesystem_path(root, path):
        raise ContractError("Maintenance destination must be outside the consumer")
    return path


def _reader(root):
    if not path_at(root, PIN, missing=True).is_file() or not codec.supported(root):
        raise ContractError("Compaction requires a verified pinned ZIP reader")
    lock = json.loads(_read_regular(root, PIN, limit=4*1024*1024))
    runtime = lock["runtime"]
    name = "scripts/store_maintenance.py"
    raw = _read_regular(root, runtime + "/" + name, limit=4*1024*1024, package_data=True)
    declaration = json.loads(_read_regular(root, runtime + "/distribution/dual.json", limit=1024*1024, package_data=True))
    if (FORMAT not in lock["storage_formats"] or FORMAT not in declaration["storage_formats"]
            or sha(raw) != lock["runtime_files"].get(name)):
        raise ContractError("Pinned runtime lacks verified maintenance recovery")
    return sha(_read_regular(root, PIN, limit=4*1024*1024))


def _inventory(root):
    """One bounded physical inventory, including unreferenced but valid objects."""
    from source_inventory import linked
    codec.invalidate(root)
    locations = codec._locations(root)
    loose = {}; total = 0
    directory = path_at(root, codec.OBJECTS.rstrip('/'), missing=True)
    if directory.exists():
        if not directory.is_dir(): raise ContractError("Invalid loose object directory")
        with os.scandir(directory) as entries:
            for entry in entries:
                if len(loose) >= COUNT: raise ContractError("Maintenance object count exceeded")
                observed = entry.stat(follow_symlinks=False)
                if (not codec.HASH.fullmatch(entry.name) or linked(observed)
                        or not stat.S_ISREG(observed.st_mode) or observed.st_size > LIMIT):
                    raise ContractError("Unrecognized or protected loose object: " + entry.name)
                loose[entry.name] = observed.st_size
    all_objects = dict(loose)
    for digest, copies in locations.items(): all_objects.setdefault(digest, copies[0][3])
    if len(all_objects) > COUNT: raise ContractError("Maintenance object count exceeded")
    packs = {}
    for copies in locations.values():
        for name, *_ in copies: packs[name] = None
    for name in packs:
        raw = _read_regular(root, name, limit=codec.MAX_PACK)
        if sha(raw) != Path(name).stem: raise ContractError("Existing ZIP hash mismatch")
        packs[name] = sha(raw)
    bodies = {}; protected = {}; references = []; nodes = 0
    for digest, size in sorted(all_objects.items()):
        total += size
        if total > LIMIT:
            raise ContractError("Maintenance /1 logical byte budget exceeded; use store-preview with backup_dir for /2 after an explicit compatible runtime update")
        raw = codec.read_logical(root, codec.OBJECTS + digest, LIMIT)
        if len(raw) != size or sha(raw) != digest: raise ContractError("Object integrity mismatch")
        # Inspect structured objects once. Unknown formats remain byte-preserved.
        if raw.lstrip().startswith((b'{', b'[')):
            try: value = json.loads(raw)
            except (ValueError, UnicodeError, RecursionError): value = None
            stack = [value]
            while stack:
                item = stack.pop(); nodes += 1
                if nodes > 1000000: raise ContractError("Maintenance reference traversal budget exceeded")
                if isinstance(item, dict):
                    if item.get('format') == 'lks-sdd-object/1':
                        from content_store import object_path
                        object_path(item); references.append(item)
                    else: stack.extend(item.values())
                elif isinstance(item, list): stack.extend(item)
        if digest in loose:
            if size <= codec.TARGET: bodies[digest] = raw
            else: protected[digest] = {"bytes": size, "reason": "large-object-remains-loose"}
    for ref in references:
        if all_objects.get(ref['sha256']) != ref['bytes']:
            raise ContractError("Unresolved or contradictory logical object reference")
    return bodies, all_objects, packs, protected, len(references)


def _groups(bodies):
    batch = {}; size = 0
    for digest, raw in sorted(bodies.items()):
        if batch and (size + len(raw) + 204 > codec.TARGET or len(batch) == codec.MAX_ENTRIES):
            yield batch
            batch = {}; size = 0
        batch[digest] = raw; size += len(raw) + 204
    if batch: yield batch


def _backup_bytes(bodies):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for digest, raw in sorted(bodies.items()):
            info = zipfile.ZipInfo(digest, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3; info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, raw)
    return output.getvalue()


def _free(path, required):
    parent = path
    while not parent.exists():
        if parent.parent == parent: raise ContractError("Maintenance destination volume is unavailable")
        parent = parent.parent
    if shutil.disk_usage(parent).free < required:
        raise ContractError("Insufficient space for verified compaction and recovery")


@codec.evaluated
def preview(root, backup, restore):
    root = filesystem_root(root, force_extended=True)
    ensure_idle(root)
    pin = _reader(root)
    backup, restore = _external(root, backup), _external(root, restore)
    if (backup.exists() or restore.exists() or is_within_filesystem_path(backup, restore)
            or is_within_filesystem_path(restore, backup)):
        raise ContractError("Backup and restore require distinct new destinations")
    bodies, logical, packs, protected, references = _inventory(root)
    if not bodies: raise ContractError("No eligible loose objects to compact")
    targets = []
    for group in _groups(bodies):
        raw = codec.encode(group)
        targets.append({"path": codec.PACKS + sha(raw) + '.zip', "sha256": sha(raw),
                        "bytes": len(raw), "objects": list(group)})
    raw_backup = _backup_bytes(bodies)
    restore_stage = restore.with_name(restore.name + '.lks-stage-' + sha(raw_backup)[:16])
    if restore_stage.exists(): raise ContractError("Restore staging destination already exists")
    reserve = len(raw_backup) + sum(len(b) for b in bodies.values()) + sum(p['bytes'] for p in targets) + 16*1024*1024
    # Conservative per-volume admission: each volume must fit the complete bound.
    for path in (root, backup, restore): _free(path, reserve)
    data = {"format": FORMAT, "operation": "physical-compaction", "pin_sha256": pin,
            "originals": {k:len(v) for k,v in bodies.items()}, "logical_objects": logical,
            "existing_packs": packs, "protected": protected, "packs": targets,
            "structured_references_checked": references,
            "backup": {"path": str(backup), "sha256": sha(raw_backup), "bytes": len(raw_backup)},
            "restore": str(restore), "restore_stage": str(restore_stage), "required_free_bytes_per_volume": reserve,
            "removal_authorization": "separate-exact-preview-hash-required"}
    if len(canonical(data)) > JOURNAL_LIMIT//2: raise ContractError("Maintenance preview exceeds journal budget")
    return {**data, "preview_hash": fingerprint(data), "status": "preview", "consumer_writes": []}


def _validate(plan, authorized):
    if not isinstance(plan, dict): raise ContractError("Invalid maintenance preview")
    if len(canonical(plan)) > JOURNAL_LIMIT//2: raise ContractError("Maintenance preview exceeds budget")
    body = {k:v for k,v in plan.items() if k not in {'preview_hash','status','consumer_writes'}}
    if (plan.get('format') != FORMAT or not re.fullmatch(r'[0-9a-f]{64}', str(authorized))
            or plan.get('preview_hash') != authorized or fingerprint(body) != authorized):
        raise ContractError("Maintenance requires the exact authorized preview")
    originals = plan.get('originals', {})
    if (not isinstance(originals, dict) or not 1 <= len(originals) <= COUNT
            or any(not codec.HASH.fullmatch(k) or type(v) is not int or not 0 <= v <= codec.TARGET for k,v in originals.items())
            or sum(originals.values()) > LIMIT):
        raise ContractError("Invalid maintenance originals")
    members = []
    for pack in plan.get('packs', []):
        if (pack.get('path') != codec.PACKS + pack.get('sha256','') + '.zip'
                or not codec.HASH.fullmatch(pack.get('sha256',''))
                or not 0 < pack.get('bytes', 0) <= codec.MAX_PACK):
            raise ContractError("Invalid maintenance pack")
        members.extend(pack['objects'])
    if sorted(members) != sorted(originals) or len(members) != len(set(members)):
        raise ContractError("Maintenance pack coverage mismatch")
    backup = plan.get('backup', {})
    if (not codec.HASH.fullmatch(backup.get('sha256','')) or type(backup.get('bytes')) is not int
            or not 0 < backup['bytes'] <= LIMIT + COUNT*204 + 22):
        raise ContractError("Invalid maintenance backup bounds")


def _checkpoint(phase):
    """Failure-injection seam; production calls never introduce a delay."""


def _publish(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    try: publish_new_file(path, raw, prefix='.lks-maint-')
    except FileExistsError:
        if not path.is_file() or _read_regular(path.parent, path.name, limit=len(raw)) != raw:
            raise ContractError("Maintenance destination conflict")


def _backup(plan, root):
    path = _external(root, plan['backup']['path'])
    if not path.is_file() or path.stat().st_size != plan['backup']['bytes']:
        raise ContractError("Missing or changed maintenance backup")
    raw = _read_regular(path.parent, path.name, limit=LIMIT + COUNT*204 + 22)
    if sha(raw) != plan['backup']['sha256']: raise ContractError("Maintenance backup integrity mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) != len(plan['originals']) or {i.filename for i in entries} != set(plan['originals']):
            raise ContractError("Maintenance backup inventory mismatch")
        bodies = {}
        for entry in entries:
            if (entry.orig_filename != entry.filename or entry.compress_type != zipfile.ZIP_STORED
                    or entry.file_size != plan['originals'][entry.filename]):
                raise ContractError("Invalid maintenance backup entry")
            body = archive.read(entry)
            if sha(body) != entry.filename: raise ContractError("Maintenance backup object mismatch")
            bodies[entry.filename] = body
    return bodies


def _restore(plan, root, bodies):
    destination = _external(root, plan['restore'])
    if destination.exists():
        if not destination.is_dir(): raise ContractError("Restore destination conflict")
        found = {p.name for p in destination.iterdir()}
        if found != set(bodies): raise ContractError("Restore destination inventory conflict")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = _external(root, plan['restore_stage'])
        if stage.parent != destination.parent or stage == destination:
            raise ContractError("Invalid restore staging destination")
        stage.mkdir(exist_ok=True)
        if not stage.is_dir() or {p.name for p in stage.iterdir()} - set(bodies):
            raise ContractError("Unknown restore staging content preserved")
        for digest, raw in bodies.items():
            _publish(stage/digest, raw)
            _checkpoint('during-restore')
        for digest, raw in bodies.items():
            if _read_regular(stage,digest,limit=LIMIT) != raw:
                raise ContractError("Restore staging integrity mismatch")
        # The deterministic preview-bound staging directory also survives a crash.
        from v2_history import _publish_directory
        _publish_directory(stage, destination)
    for digest, raw in bodies.items():
        observed = _read_regular(destination, digest, limit=LIMIT)
        if observed != raw: raise ContractError("Restored original differs from backup")
    return destination


def _stable(root, plan):
    if _reader(root) != plan['pin_sha256']: raise ContractError("Pinned runtime changed since maintenance preview")
    for name, expected in plan['existing_packs'].items():
        if sha(_read_regular(root, name, limit=codec.MAX_PACK)) != expected:
            raise ContractError("Pre-existing pack changed")
    for digest, row in plan['protected'].items():
        if sha(_read_regular(root, codec.OBJECTS+digest, limit=LIMIT)) != digest:
            raise ContractError("Protected original changed")


def _journal(root, value):
    if len(canonical(value)) > JOURNAL_LIMIT: raise ContractError("Maintenance journal exceeds budget")
    write_one(root, PENDING, canonical(value))


def _finish(root, journal, *, remove):
    plan = journal['preview']; key = plan['preview_hash']
    _validate(plan, key); _stable(root, plan)
    backup_path = _external(root, plan['backup']['path'])
    if not backup_path.exists():
        bodies = {}
        for digest, size in plan['originals'].items():
            raw = _read_regular(root, codec.OBJECTS+digest, limit=LIMIT)
            if len(raw) != size or sha(raw) != digest: raise ContractError("Original changed before backup")
            bodies[digest] = raw
        raw = _backup_bytes(bodies)
        if sha(raw) != plan['backup']['sha256']: raise ContractError("Backup differs from preview")
        _publish(backup_path, raw)
    bodies = _backup(plan, root)
    _checkpoint('before-publish')
    for pack in plan['packs']:
        raw = codec.encode({digest:bodies[digest] for digest in pack['objects']})
        if len(raw) != pack['bytes'] or sha(raw) != pack['sha256']: raise ContractError("Pack differs from preview")
        _publish(path_at(root, pack['path'], missing=True), raw)
    codec.invalidate(root)
    _checkpoint('after-publish')
    # Verify fresh physical pack bytes and every logical copy before any removal.
    identities = {}
    for pack in plan['packs']:
        with codec._opened(root, pack['path']) as (stream, size, identity):
            if sha(stream.read()) != pack['sha256']:
                raise ContractError("Published maintenance ZIP changed")
            identities[pack['path']] = identity
    for digest, raw in bodies.items():
        if codec.read_logical(root, codec.OBJECTS+digest, LIMIT) != raw:
            raise ContractError("Compacted object differs from backup")
    _restore(plan, root, bodies)
    journal['phase'] = 'restored-and-verified'; _journal(root, journal)
    _checkpoint('before-remove')
    if not remove:
        return {"status":"awaiting-removal-authorization", "preview_hash":key, "backup":plan['backup'],
                "restored_objects":len(bodies), "pending":PENDING, "functional_authority":"unchanged"}
    _stable(root, plan)
    journal['removal_authorized'] = True; journal['phase'] = 'removing'; _journal(root, journal)
    for digest, raw in bodies.items():
        path = path_at(root, codec.OBJECTS+digest, missing=True)
        if path.exists():
            if _read_regular(root, codec.OBJECTS+digest, limit=LIMIT) != raw:
                raise ContractError("Changed original preserved during removal")
            # Fresh physical container and body immediately before this deletion.
            # Complete container hash was verified above in this evaluation.
            copies = codec._locations(root).get(digest, [])
            if (not copies or any(copy[0] in identities and copy[1] != identities[copy[0]] for copy in copies)
                    or any(codec._read_packed(root,digest,copy,LIMIT) != raw for copy in copies)):
                raise ContractError("Verified packed duplicate required before removal")
            path.unlink()
            _checkpoint('during-remove')
    journal['phase'] = 'completed'
    _checkpoint('before-receipt')
    receipt = RECEIPTS + key + '.json'
    _publish(path_at(root, receipt, missing=True), canonical(journal))
    _checkpoint('after-receipt')
    # The completed receipt is durable before releasing the shared writer slot.
    path_at(root, PENDING).unlink(); codec.invalidate(root)
    return {"status":"compacted", "preview_hash":key, "receipt":receipt,
            "originals_removed":len(bodies), "packs":len(plan['packs']), "functional_authority":"unchanged"}


@_writer
@codec.evaluated
def apply(root, plan, authorized):
    root = filesystem_root(root, force_extended=True)
    _validate(plan, authorized); ensure_idle(root)
    # Rebuild the exact preview before acquiring the common exclusive slot.
    if preview(root, plan['backup']['path'], plan['restore']) != plan:
        raise ContractError("Maintenance preview is stale")
    journal = {"schema_version":FORMAT, "preview":plan, "phase":"owned", "removal_authorized":False}
    path = path_at(root, PENDING, missing=True); path.parent.mkdir(parents=True, exist_ok=True)
    try: publish_new_file(path, canonical(journal), prefix='.lks-maint-owner-')
    except FileExistsError as exc: raise ContractError("Another transaction owns the shared slot") from exc
    return _finish(root, journal, remove=False)


@_writer
@codec.evaluated
def recover(root, authorized, *, remove_authorized=None):
    root = filesystem_root(root, force_extended=True)
    journal = json.loads(_read_regular(root, PENDING, limit=JOURNAL_LIMIT))
    if journal.get('schema_version') != FORMAT:
        raise ContractError("Use the business journal recovery for this pending operation")
    _validate(journal.get('preview'), authorized)
    if remove_authorized is not None and remove_authorized != authorized:
        raise ContractError("Removal needs separate authorization of the exact preview")
    # A completed removal authorization survives interruption, never a query.
    return _finish(root, journal, remove=journal.get('removal_authorized') is True or remove_authorized == authorized)
