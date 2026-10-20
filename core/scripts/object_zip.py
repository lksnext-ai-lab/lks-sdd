"""Immutable ZIP support for logical CAS paths; indexes never grant authority."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import struct
import threading
import zipfile
import zlib

from v2_contract import ContractError

FORMAT = "lks-sdd-object-zip/1"
OBJECTS = ".lks-sdd/objects/sha256/"
PACKS = ".lks-sdd/objects/packs/"
HASH = re.compile(r"[0-9a-f]{64}")
MAX_PACK = 16 * 1024 * 1024
TARGET = 8 * 1024 * 1024
MAX_ENTRIES = 8192
MAX_INDEX = 1024 * 1024
MAX_INDEX_TOTAL = 16 * 1024 * 1024
MAX_PACKS = MAX_INDEX_TOTAL // 110  # At least one 110-byte directory record per pack.
_ACTIVE = ContextVar("lks_object_zip_indices", default=None)


def _sha(raw): return hashlib.sha256(raw).hexdigest()


def _owner():
    try: task = asyncio.current_task()
    except RuntimeError: task = None
    return threading.get_ident(), task


@contextmanager
def evaluation():
    active = _ACTIVE.get()
    if active is not None and active["owner"] == _owner():
        yield
        return
    active = {"owner": _owner(), "roots": {}, "bytes": 0}
    token = _ACTIVE.set(active)
    try: yield
    finally:
        active["roots"].clear(); active["owner"] = None
        _ACTIVE.reset(token)


def evaluated(function):
    @wraps(function)
    def call(*args, **kwargs):
        with evaluation(): return function(*args, **kwargs)
    return call


def invalidate(root):
    active = _ACTIVE.get()
    if active is not None and active["owner"] == _owner():
        old = active["roots"].pop(str(Path(root).resolve()), None)
        if old is not None: active["bytes"] -= old[1]


@contextmanager
def _opened(root, name, expected=None):
    from v2_contract import path_at
    from source_inventory import signature, linked
    path = path_at(root, name, package_data=True)
    observed = path.lstat()
    identity = signature(observed)
    if linked(observed) or not stat.S_ISREG(observed.st_mode) or observed.st_size > MAX_PACK:
        raise ContractError("Invalid or excessive object ZIP")
    if expected is not None and identity != expected:
        raise ContractError("Object ZIP changed during evaluation")
    with path.open("rb") as stream:
        if signature(os.fstat(stream.fileno())) != identity:
            raise ContractError("Object ZIP identity changed before reading")
        yield stream, observed.st_size, identity
        if signature(os.fstat(stream.fileno())) != identity or signature(path.lstat()) != identity:
            raise ContractError("Object ZIP changed during reading")


def _index(root, name, budget):
    # Reject excessive directory allocation and ZIP64 before ZipFile parses it.
    with _opened(root, name) as (stream, size, identity):
        if size < 22: raise ContractError("Invalid object ZIP footer")
        stream.seek(size - 22)
        footer = stream.read(22)
        if len(footer) != 22: raise ContractError("Truncated object ZIP footer")
        magic, disk, central_disk, count_disk, count, index_size, offset, comment = struct.unpack("<4s4H2LH", footer)
        if (magic != b"PK\x05\x06" or disk or central_disk or count_disk != count or comment
                or not 1 <= count <= MAX_ENTRIES or index_size > MAX_INDEX
                or offset + index_size != size - 22):
            raise ContractError("Invalid or excessive object ZIP index")
        if index_size > budget:
            from capacity import require, limit
            require("zip_index_bytes", limit("zip_index_bytes", MAX_INDEX_TOTAL) - budget + index_size,
                    MAX_INDEX_TOTAL, "Invalid or excessive object ZIP index")
        try:
            with zipfile.ZipFile(stream) as archive:
                entries = archive.infolist()
                if len(entries) != count or archive.start_dir != offset:
                    raise ContractError("Object ZIP directory mismatch")
                found = {}; end = 0
                for info in sorted(entries, key=lambda i: i.header_offset):
                    mode = info.external_attr >> 16
                    if (info.orig_filename != info.filename or not HASH.fullmatch(info.filename) or info.filename in found
                            or info.compress_type != zipfile.ZIP_STORED or info.flag_bits
                            or info.extract_version != 20
                            or info.extra or info.comment or info.create_system != 3
                            or stat.S_IFMT(mode) != stat.S_IFREG or info.file_size > TARGET
                            or info.file_size != info.compress_size or info.header_offset != end):
                        raise ContractError("Unsafe or contradictory object ZIP entry")
                    stream.seek(info.header_offset)
                    header = stream.read(30)
                    if len(header) != 30: raise ContractError("Truncated object ZIP header")
                    h = struct.unpack("<4s5H3L2H", header)
                    if (h[0] != b"PK\x03\x04" or h[1] != 20 or h[2] or h[3] or h[6] != info.CRC
                            or h[7] != info.file_size or h[8] != info.file_size or h[9] != 64 or h[10]
                            or stream.read(64) != info.filename.encode("ascii")):
                        raise ContractError("Object ZIP local header mismatch")
                    body_at = info.header_offset + 94
                    end = body_at + info.file_size
                    if end > offset: raise ContractError("Overlapping object ZIP ranges")
                    found[info.filename] = (name, identity, body_at, info.file_size, info.CRC)
                if end != offset: raise ContractError("Object ZIP contains unindexed bytes")
        except (zipfile.BadZipFile, ValueError, UnicodeError, struct.error) as exc:
            raise ContractError("Invalid object ZIP structure") from exc
        return found, index_size


def _locations(root, *, checkpoint=None):
    from v2_contract import path_at
    key = str(Path(root).resolve()); active = _ACTIVE.get()
    scoped = active is not None and active["owner"] == _owner()
    if scoped and key in active["roots"]: return active["roots"][key][0]
    from capacity import limit
    available = limit("zip_index_bytes", MAX_INDEX_TOTAL) - (active["bytes"] if scoped else 0)
    folder = path_at(root, PACKS.rstrip("/"), missing=True, package_data=True)
    locations = {}; total = 0
    if folder.exists():
        if not folder.is_dir(): raise ContractError("Object ZIP directory is not a directory")
        with os.scandir(folder) as entries:
            count = 0
            for entry in entries:
                if checkpoint is not None:
                    checkpoint()
                count += 1
                if count > MAX_PACKS:
                    from capacity import require
                    require("zip_index_bytes", count * 110, MAX_INDEX_TOTAL, "Object ZIP enumeration budget exceeded")
                if not re.fullmatch(r"[0-9a-f]{64}\.zip", entry.name):
                    raise ContractError("Unrecognized file in object ZIP directory")
                index, used = _index(root, PACKS + entry.name, available - total)
                total += used
                for digest, location in index.items():
                    others = locations.setdefault(digest, [])
                    if others and others[0][3] != location[3]:
                        raise ContractError("Contradictory object ZIP locations")
                    others.append(location)
    if scoped:
        active["roots"][key] = (locations, total); active["bytes"] += total
    return locations


def contains(root, name):
    from v2_contract import path_at
    digest = name[len(OBJECTS):]
    if not name.startswith(OBJECTS) or not HASH.fullmatch(digest):
        raise ContractError("Invalid logical object path")
    return path_at(root, name, missing=True).exists() or digest in _locations(root)


def _read_packed(root, digest, location, limit):
    pack, identity, offset, size, crc = location
    if size > limit: raise ContractError("Content object exceeds read budget")
    with _opened(root, pack, identity) as (stream, _, _):
        stream.seek(offset); raw = stream.read(size)
    if len(raw) != size or zlib.crc32(raw) != crc or _sha(raw) != digest:
        raise ContractError("Content object ZIP integrity mismatch")
    return raw


def read_logical(root, name, limit):
    from v2_contract import path_at, _read_regular
    digest = name[len(OBJECTS):]
    if not name.startswith(OBJECTS) or not HASH.fullmatch(digest):
        raise ContractError("Invalid logical object path")
    selected = None
    if path_at(root, name, missing=True).exists():
        selected = _read_regular(root, name, limit=limit)
        if _sha(selected) != digest: raise ContractError("Content object integrity mismatch")
    for location in _locations(root).get(digest, ()):
        raw = _read_packed(root, digest, location, limit)
        if selected is not None and selected != raw: raise ContractError("Contradictory object representations")
        selected = raw
    if selected is None: raise ContractError("Missing content object: " + digest)
    return selected


def supported(root):
    """An old pinned reader keeps writing its compatible loose representation."""
    from v2_contract import path_at, _read_regular
    name = ".lks-sdd/distribution-lock.json"
    if not path_at(root, name, missing=True).exists(): return True
    lock = json.loads(_read_regular(root, name, limit=4 * 1024 * 1024))
    if not isinstance(lock, dict) or not isinstance(lock.get("storage_formats", []), list):
        raise ContractError("Invalid pinned storage capabilities")
    if FORMAT not in lock.get("storage_formats", []):
        folder = path_at(root, PACKS.rstrip("/"), missing=True)
        if folder.exists():
            if not folder.is_dir(): raise ContractError("Invalid object ZIP directory")
            with os.scandir(folder) as entries:
                if next(entries, None) is not None:
                    raise ContractError("Pinned reader lacks ZIP capability; restore a compatible runtime before writing")
        return False
    runtime = lock.get("runtime")
    if (not isinstance(runtime, str) or not runtime.startswith(".lks-sdd/runtime/")
            or not isinstance(lock.get("runtime_files"), dict)):
        raise ContractError("Missing pinned ZIP reader inventory")
    declaration = json.loads(_read_regular(root, runtime + "/distribution/dual.json", limit=1024 * 1024, package_data=True))
    if declaration.get("storage_formats") != lock["storage_formats"]:
        raise ContractError("Pinned ZIP capability declaration mismatch")
    for module in ("object_zip.py", "v2_contract.py", "content_store.py", "v2_storage.py"):
        relative = "scripts/" + module
        raw = _read_regular(root, runtime + "/" + relative, limit=4 * 1024 * 1024, package_data=True)
        if _sha(raw) != lock["runtime_files"].get(relative):
            raise ContractError("Pinned ZIP reader integrity mismatch")
    return True


def encode(objects):
    if (not isinstance(objects, dict) or not 1 <= len(objects) <= MAX_ENTRIES
            or len(objects) * 110 > MAX_INDEX):
        raise ContractError("Object ZIP entry/index budget exceeded")
    total = 22
    for digest, body in objects.items():
        if (not isinstance(digest, str) or not HASH.fullmatch(digest) or not isinstance(body, bytes)
                or len(body) > TARGET or _sha(body) != digest):
            raise ContractError("Invalid object ZIP input")
        total += len(body) + 204
        if total > MAX_PACK: raise ContractError("Object ZIP byte budget exceeded")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        for digest, raw in sorted(objects.items()):
            info = zipfile.ZipInfo(digest, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3; info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, raw)
    raw = output.getvalue()
    if len(raw) > MAX_PACK: raise ContractError("Object ZIP byte budget exceeded")
    return raw


def stage_writer(root, writer):
    """Ephemeral validation uses the same logical bodies, grouped directly."""
    publisher = Publisher(root)
    def write(name, raw):
        if name.startswith(OBJECTS):
            if raw is None or name != OBJECTS + _sha(raw):
                raise ContractError("Staged content objects are immutable")
            publisher.add(raw)
        else: writer(root, name, raw)
    return write, publisher.flush


class Publisher:
    """Bounded streaming batches; no intermediate loose copy per fragment."""
    def __init__(self, root):
        self.root = root; self.enabled = supported(root)
        self.pending = {}; self.size = 22; self.seen = {}

    def add(self, raw):
        from content_store import reference, object_path, read_object, publish_object
        ref = reference(raw); digest = ref["sha256"]
        if digest in self.seen:
            if self.seen[digest] != len(raw): raise ContractError("Contradictory object sizes")
            return ref
        name = object_path(ref)
        if contains(self.root, name): read_object(self.root, ref)
        elif not self.enabled or len(raw) > TARGET:
            publish_object(self.root, name, raw)
        else:
            if self.size + len(raw) + 204 > TARGET or len(self.pending) >= MAX_ENTRIES:
                self.flush()
            self.pending[digest] = raw; self.size += len(raw) + 204
        self.seen[digest] = len(raw)
        return ref

    def flush(self):
        from content_store import publish_object
        from v2_contract import path_at, _read_regular
        from path_utils import publish_new_file
        if not self.pending: return
        if len(self.pending) == 1:
            digest, raw = next(iter(self.pending.items()))
            publish_object(self.root, OBJECTS + digest, raw)
        else:
            if not supported(self.root):
                raise ContractError("Pinned ZIP capability changed before publication")
            raw = encode(self.pending); digest = _sha(raw); name = PACKS + digest + ".zip"
            path = path_at(self.root, name, missing=True); path.parent.mkdir(parents=True, exist_ok=True)
            try: publish_new_file(path_at(self.root, name, missing=True), raw, prefix=".lks-pack-")
            except FileExistsError: pass
            # Keep the verified file identity across index and competitor checks,
            # not just during the full hash. A changed pack cannot inherit that
            # hash verdict and then supply unverified recovery bodies.
            with _opened(self.root, name) as (stream, size, _):
                if _sha(stream.read(size + 1)) != digest:
                    raise ContractError("Published object ZIP integrity mismatch")
                invalidate(self.root)
                locations = _locations(self.root)
                # The new pack was hashed completely; only competing bodies need
                # another read. Its identity is checked again when leaving scope.
                for object_digest, body in self.pending.items():
                    loose = OBJECTS + object_digest
                    if path_at(self.root, loose, missing=True).exists():
                        if _read_regular(self.root, loose, limit=len(body)) != body:
                            raise ContractError("Conflicting concurrent content object")
                    for location in locations.get(object_digest, ()):
                        if location[0] != name and _read_packed(self.root, object_digest, location, len(body)) != body:
                            raise ContractError("Conflicting concurrent packed content object")
                if not supported(self.root):
                    raise ContractError("Pinned ZIP capability changed during publication")
        self.pending.clear(); self.size = 22
