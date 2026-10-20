"""Portable, versioned transport. Payloads are read one bounded object at a time."""
from collections.abc import MutableMapping, Mapping
import json
from pathlib import Path

from content_store import LIMIT, reference, object_path
from v2_contract import ContractError, canonical, path_at, read_bytes, sha
from path_utils import publish_new_file
from capacity import require

FORMAT = "lks-sdd-packet/1"
MAX_FILES = 100000
MAX_BYTES = 2 * 1024 * 1024 * 1024
MAX_DESCRIPTOR = 64 * 1024 * 1024


class Packet(dict):
    def __init__(self, value, base):
        super().__init__(value)
        self.base = Path(base).resolve()


class Spool(MutableMapping):
    def __init__(self, base):
        self.base = Path(base).resolve()
        self.base.mkdir(parents=True, exist_ok=False)
        self.refs = {}
        self.unique = {}
        self.total_bytes = 0

    def __len__(self): return len(self.refs)
    def __iter__(self): return iter(self.refs)
    def __delitem__(self, name): del self.refs[name]
    def __getitem__(self, name):
        ref = self.refs[name]
        return None if ref is None else payload_bytes(self.base, "objects", ref)

    def __setitem__(self, name, raw):
        from v2_contract import relative_parts
        relative_parts(name, package_data=True)
        require("packet_files", len(self.refs) + (name not in self.refs), MAX_FILES, "Packet file budget exceeded")
        if raw is None: self.refs[name] = None; return
        ref = reference(raw)
        digest = ref["sha256"]
        if digest not in self.unique:
            require("packet_bytes", self.total_bytes + len(raw), MAX_BYTES, "Packet byte budget exceeded")
            target = path_at(self.base, "objects/" + digest, missing=True, package_data=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            publish_new_file(target, raw, prefix=".packet-")
            self.unique[digest] = len(raw)
            self.total_bytes += len(raw)
        self.refs[name] = ref


def payload_bytes(base, folder, ref):
    object_path(ref)
    raw = read_bytes(base, folder + "/" + ref["sha256"], limit=LIMIT, package_data=True)
    if len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]: raise ContractError("Packet object altered")
    return raw


class Payload(Mapping):
    def __init__(self, packet):
        if not isinstance(packet, Packet): raise ContractError("Referenced packet needs its explicit file location")
        folder = packet.get("object_directory")
        if not isinstance(folder, str) or "/" in folder or folder in {"", ".", ".."}:
            raise ContractError("Invalid packet object directory")
        self.base, self.folder, self.refs = packet.base, folder, packet["payload"]
        if not isinstance(self.refs, dict): raise ContractError("Packet file budget exceeded")
        require("packet_files", len(self.refs), MAX_FILES, "Packet file budget exceeded")
        unique = {}
        for ref in self.refs.values():
            if ref is not None:
                object_path(ref)
                if ref["sha256"] in unique and unique[ref["sha256"]] != ref["bytes"]: raise ContractError("Conflicting packet size")
                unique[ref["sha256"]] = ref["bytes"]
        require("packet_bytes", sum(unique.values()), MAX_BYTES, "Packet byte budget exceeded")
    def __len__(self): return len(self.refs)
    def __iter__(self): return iter(self.refs)
    def __getitem__(self, name):
        ref = self.refs[name]
        return None if ref is None else payload_bytes(self.base, self.folder, ref)


class InlinePayload(Mapping):
    """Compatibility transport; decode one entry, without retaining all decoded bytes."""
    def __init__(self, packet):
        from v2_contract import relative_parts
        self.values = packet["payload"]
        if not isinstance(self.values, dict):
            raise ContractError("Packet file budget exceeded")
        require("packet_files", len(self.values), MAX_FILES, "Packet file budget exceeded")
        total = 0
        for name, raw in self.values.items():
            relative_parts(name, package_data=True)
            if raw is not None:
                if not isinstance(raw, str) or len(raw) > 4*((LIMIT+2)//3):
                    raise ContractError("Packet object budget exceeded")
                total += (len(raw)//4)*3 - (len(raw)-len(raw.rstrip("=")))
                require("packet_bytes", total, MAX_BYTES, "Inline packet byte budget exceeded")
    def __len__(self): return len(self.values)
    def __iter__(self): return iter(self.values)
    def __getitem__(self, name):
        import base64
        raw = self.values[name]
        if raw is None: return None
        decoded = base64.b64decode(raw, validate=True)
        if len(decoded) > LIMIT: raise ContractError("Packet object budget exceeded")
        return decoded


def finish(packet, spool):
    value = Packet({**packet, "format": FORMAT, "object_directory": "objects", "payload": spool.refs}, spool.base)
    raw = canonical(value)
    if len(raw) > MAX_DESCRIPTOR: raise ContractError("Packet descriptor budget exceeded")
    publish_new_file(spool.base/"packet.json", raw, prefix=".packet-")
    return value


def read(path, *, raw=None):
    path = Path(path).resolve()
    if raw is None: raw = read_bytes(path.parent, path.name, limit=MAX_DESCRIPTOR, package_data=True)
    if not isinstance(raw, bytes) or len(raw)>MAX_DESCRIPTOR: raise ContractError("Packet/input byte budget exceeded")
    value = json.loads(raw)
    if not isinstance(value, dict): raise ContractError("Packet/input object required")
    return Packet(value, path.parent) if value.get("format") == FORMAT else value


def persist(packet):
    from v2_storage import write_one
    if isinstance(packet, Packet):
        raw = canonical(packet)
        if len(raw) > MAX_DESCRIPTOR: raise ContractError("Packet descriptor budget exceeded")
        write_one(packet.base, "packet.json", raw)
    return packet


def save(packet, destination):
    """Keep the descriptor and every referenced byte together when output is relocated."""
    from v2_storage import write_one
    destination = Path(destination).resolve()
    folder = destination.name + ".objects"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists(): raise ContractError("Packet output already exists")
    refs, sizes, total = {}, {}, 0
    values = Payload(packet) if packet.get("format") == FORMAT else InlinePayload(packet)
    if (destination.parent/folder).exists(): raise ContractError("Packet object directory already exists")
    (destination.parent/folder).mkdir()
    for name, raw in values.items():
        if raw is None: refs[name] = None; continue
        ref = reference(raw); refs[name] = ref
        if ref["sha256"] not in sizes:
            sizes[ref["sha256"]] = ref["bytes"]
            total += ref["bytes"]
            require("packet_bytes", total, MAX_BYTES, "Packet byte budget exceeded")
            write_one(destination.parent, folder + "/" + ref["sha256"], raw)
    value = {**packet, "format": FORMAT, "object_directory": folder, "payload": refs}
    raw = canonical(value)
    if len(raw) > MAX_DESCRIPTOR or len(refs) > MAX_FILES: raise ContractError("Packet descriptor budget exceeded")
    publish_new_file(destination, raw, prefix=".packet-")
    return Packet(value, destination.parent)
