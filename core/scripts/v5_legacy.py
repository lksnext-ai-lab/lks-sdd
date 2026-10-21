"""Read-only conversion readers. Never import or execute an older runtime."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile
import uuid

from v5_core import Conflict, digest, file_digest, filesystem_root, path_at, read

SUPPORTED = {"1.5", "2.0", "3.0", "3.1"}
BLOCK = re.compile(r"^<!-- lks-sdd: (\{[^\r\n]*\}) -->\r?\n(.*?)^<!-- /lks-sdd -->[ \t]*\r?$", re.M | re.S)
ARCHIVE = ("docs/lks-sdd/00-control/history/", "docs/lks-sdd/00-control/migrations/", "docs/lks-sdd/evidence/")
EVENTS = {"decision", "authorization", "assignment", "handoff", "exception", "analysis", "execution",
          "checkpoint", "evidence", "problem", "migration", "receipt"}
TECHNICAL = {"baseline", "baseline_files", "source_hashes", "descriptor",
             "inventory", "capture", "fragments", "legacy", "preview"}


def paths(root, prefix):
    root = filesystem_root(root)
    base = path_at(root, prefix)
    if not base.exists():
        return []
    result = []
    def fail(exc):
        raise exc  # A partial inventory can never authorize retirement.
    for directory, folders, files in os.walk(base, followlinks=False, onerror=fail):
        relative = Path(directory).relative_to(Path(root).resolve()).as_posix()
        for item in folders + files:
            entry = Path(directory) / item
            if entry.is_symlink() or (hasattr(entry, "is_junction") and entry.is_junction()):
                raise ValueError("Links/junctions require reconciliation: " + str(entry))
        result.extend(relative + "/" + item for item in files)
        if len(result) > 200000:
            raise ValueError("Migration inventory exceeds 200000 files; split an explicit source scope")
    return sorted(result)


@dataclass
class Element:
    meta: dict
    body: str
    source: str
    schema: str

    @property
    def uid(self):
        return self.meta["uid"]

    @property
    def id(self):
        return self.meta["id"]

    @property
    def kind(self):
        return self.meta["kind"]

    @property
    def data(self):
        return self.meta.get("data", {}) if self.schema.startswith("3.") else {
            **self.meta, **self.meta.get("data", {})}

    @property
    def relations(self):
        return self.meta.get("relations", {})

    def normative_hash(self):
        omit = {"state", "nature", "progress", "updated_at", "id", "revision"}
        value = {"meta": {k: v for k, v in self.meta.items() if k not in omit}, "body": self.body}
        return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


class Reader:
    def __init__(self, root):
        self.root = filesystem_root(root)
        self.elements = {}
        self.prose = {}
        self.document_hashes = {}
        self.schemas = set()
        self._objects = None
        self._pack_hashes = {}
        self.inventory = paths(self.root, "docs/lks-sdd")
        active = [name for name in self.inventory if name.endswith(".md") and not name.startswith(ARCHIVE)]
        if not active:
            raise ValueError("No supported source documents")
        index_raw = read(self.root, ".lks-sdd/project.json")
        declared = None
        if index_raw:
            index = json.loads(index_raw)
            declared = str(index.get("schema_version", ""))
            if declared and declared not in SUPPORTED:
                raise ValueError("Unknown source format; no silent conversion: " + declared)
        total = 0
        for name in active:
            raw = read(self.root, name)
            total += len(raw)
            if total > 256 * 1024 * 1024:
                raise ValueError("Active conversion content exceeds 256 MiB")
            self.document_hashes[name] = digest(raw)
            text = raw.decode("utf-8-sig")
            version = re.search(r'^schema_version:\s*[\"\']?([0-9.]+)', text, re.M)
            schema = version[1] if version else declared or "1.5"
            if schema not in SUPPORTED:
                raise ValueError("Unsupported document version: " + name)
            self.schemas.add(schema)
            if schema == "1.5" and "<!-- lks-sdd:" not in text:
                text = self._tables(text, name)
            matches = list(BLOCK.finditer(text))
            if text.count("<!-- lks-sdd:") != len(matches) or text.count("<!-- /lks-sdd -->") != len(matches):
                raise ValueError("Malformed source blocks: " + name)
            for match in matches:
                meta = json.loads(match[1])
                for key in ("id", "uid", "kind"):
                    if not isinstance(meta.get(key), str) or not meta[key]:
                        raise ValueError("Missing source identity: " + name)
                if meta["uid"] in self.elements:
                    raise ValueError("Duplicate source identity; reconcile before migration: " + meta["id"])
                body = match[2][:-1] if match[2].endswith("\n") else match[2]
                self.elements[meta["uid"]] = Element(meta, body, name, schema)
            prose = BLOCK.sub("", text)
            prose = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", prose, count=1, flags=re.S).strip()
            if prose:
                self.prose[name] = prose
            if schema != "1.5" and not matches and not prose:
                raise ValueError("Empty structured source: " + name)
        if "1.5" in self.schemas:
            identities = {e.id: uid for uid, e in self.elements.items()}
            for e in self.elements.values():
                if e.schema == "1.5":
                    e.meta["relations"] = {"references": sorted({identities[x] for value in e.data.values()
                        for x in re.findall(r"\b[A-Z][A-Z0-9]*-[0-9]+\b", str(value)) if x in identities and x != e.id})}

    def _tables(self, text, name):
        """Read native 1.5 ID tables, retaining unclassified prose/tables verbatim."""
        kinds = {"FR": "requirement", "NFR": "constraint", "TR": "constraint", "AC": "acceptance",
                 "TASK": "task", "PLAN": "plan", "TEST": "test", "ADR": "decision", "INC": "increment",
                 "TECH": "technology", "ENV": "environment", "UI": "visual", "UX": "visual"}
        lines, columns, kept = text.splitlines(keepends=True), None, []
        for line in lines:
            cells = [v.strip() for v in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else []
            if cells and cells[0] == "ID" and "State" in cells:
                columns = cells
                kept.append(line)
            elif columns and cells and re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]+", cells[0]) and len(cells) == len(columns):
                data = dict(zip(columns, cells))
                ident = cells[0]
                uid = str(uuid.uuid5(uuid.NAMESPACE_URL, "lks-sdd/1.5/" + name + "#" + ident))
                if uid in self.elements:
                    raise ValueError("Duplicate native legacy row: " + ident)
                value = {"uid": uid, "id": ident, "kind": kinds.get(ident.split('-')[0], "legacy"),
                         "state": data["State"], "data": {**data, "owner": data.get("Owner", "source-owner-pending")}}
                body = "\n".join(k + ": " + v for k, v in data.items())
                self.elements[uid] = Element(value, body, name, "1.5")
            else:
                kept.append(line)
                if not cells:
                    columns = None
        return "".join(kept)

    def object(self, reference):
        if (not isinstance(reference, dict) or reference.get("format") != "lks-sdd-object/1" or
                not re.fullmatch(r"[a-f0-9]{64}", reference.get("sha256", "")) or
                type(reference.get("bytes")) is not int or not 0 <= reference["bytes"] <= 64 * 1024 * 1024):
            raise ValueError("Invalid legacy object reference")
        ident = reference["sha256"]
        raw = read(self.root, ".lks-sdd/objects/sha256/" + ident)
        if raw is None:
            if self._objects is None:
                self._objects = {}
                for name in paths(self.root, ".lks-sdd/objects/packs"):
                    if not name.endswith(".zip"):
                        raise ValueError("Unexpected pack member")
                    path = path_at(self.root, name)
                    if path.stat().st_size > 64 * 1024 * 1024:
                        raise ValueError("Oversized legacy pack")
                    self._pack_hashes[name] = file_digest(path)
                    with zipfile.ZipFile(path) as archive:
                        if len(archive.infolist()) > 8192:
                            raise ValueError("Oversized pack index")
                        for entry in archive.infolist():
                            if (not re.fullmatch(r"[a-f0-9]{64}", entry.filename) or entry.filename in self._objects or
                                    stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1 or
                                    entry.file_size > 64 * 1024 * 1024 or entry.compress_type != zipfile.ZIP_STORED):
                                raise ValueError("Unsafe or duplicate legacy ZIP member")
                            self._objects[entry.filename] = name
            name = self._objects.get(ident)
            if not name:
                raise ValueError("Missing legacy object: " + ident)
            path = path_at(self.root, name)
            if file_digest(path) != self._pack_hashes[name]:
                raise Conflict("Legacy object pack changed")
            with zipfile.ZipFile(path) as archive:
                raw = archive.read(ident)
        if len(raw) != reference["bytes"] or digest(raw) != ident:
            raise ValueError("Corrupt legacy object")
        return raw

    def payload(self, value):
        """Resolve a specifically requested object, not unrelated snapshot inventories."""
        if isinstance(value, dict) and value.get("format") == "lks-sdd-object/1":
            return self.object(value)
        raise ValueError("Expected an object reference")

    def approvals(self):
        events = [x for x in self.elements.values() if x.kind in {"decision", "authorization"}]
        revoked = {x.data.get("revokes") for x in events if x.data.get("outcome") == "revoked"}
        covered = {}
        for event in events:
            data = event.data
            if event.uid in revoked or data.get("historical_only") or data.get("outcome") != "approved":
                continue
            recorded = data.get("descriptor", {}).get("units", {})
            # Read-only conversion cannot revive a stale decision: every source
            # in its original descriptor must still exist with its recorded hash.
            if not recorded or any(key not in self.elements or self.elements[key].normative_hash() != value
                                   for key, value in recorded.items()):
                continue
            for target in data.get("approval_roots", recorded):
                covered.setdefault(target, []).append(event)
        return covered

    def summary(self):
        from collections import Counter
        return {"formats": sorted(self.schemas), "active_files": len(self.document_hashes),
                "active_bytes": sum(path_at(self.root, p).stat().st_size for p in self.document_hashes),
                "elements": len(self.elements), "kinds": dict(Counter(e.kind for e in self.elements.values())),
                "prose_sources": len(self.prose), "valid_current_decision_roots": len(self.approvals())}


def business_data(data):
    """Drop known technical copies, never unclassified business fields."""
    return {k: v for k, v in data.items() if k not in TECHNICAL and k.removesuffix("_ref") not in TECHNICAL}
