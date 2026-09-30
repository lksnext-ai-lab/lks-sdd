"""Version 3 Markdown model. Indexes are derived; prose is part of the contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid

from v2_contract import ContractError, canonical, fingerprint, path_at, read_bytes, sha

VERSION, METHOD = "3.0", "3.0.0"
METHODS = {"3.0.0": "3.0", "3.1.0": "3.1"}
DOCS = "docs/lks-sdd"
HISTORY = DOCS + "/00-control/history"
INDEX = ".lks-sdd/project.json"
BLOCK = re.compile(r'^<!-- lks-sdd: (\{[^\r\n]*\}) -->\r?\n(.*?)^<!-- /lks-sdd -->[ \t]*\r?$', re.M | re.S)
KINDS = set("project policy member request proposal requirement acceptance rule constraint task plan test decision interface technology assignment handoff exception analysis execution checkpoint evidence problem migration adoption feature group increment release binding environment authorization applicability legacy receipt visual change".split())
EVENTS = set("decision assignment handoff exception analysis execution checkpoint evidence problem migration authorization receipt".split())
NORMATIVE = KINDS - EVENTS - {"legacy"}
STATES = set("draft proposed confirmed approved active effective superseded retired cancelled unknown conflict backlog ready in-progress in-review done done-with-reservations blocked paused completed revoked open resolved reconciliation-required observed transition".split())


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def uid(value):
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise ContractError("Identidad UUID no válida: " + str(value)) from exc
    return value


def element(kind, title, body, *, identifier=None, **data):
    if kind not in KINDS or not title.strip() or not isinstance(body, str):
        raise ContractError("Tipo, título y contenido son obligatorios")
    key = uid(identifier) if identifier else str(uuid.uuid4())
    return {"meta": {"uid": key, "id": kind.upper() + "-" + key[:8], "kind": kind,
                     "revision": 1, "title": title, "state": "draft", "nature": "proposal",
                     "relations": {}, "data": data}, "body": body}


def render(item, version=VERSION):
    # Body bytes, including line endings, are preserved. No semantic normalization.
    return (f'---\nschema_version: "{version}"\nartifact_type: "{item["meta"]["kind"]}"\n---\n\n'
            + "<!-- lks-sdd: " + canonical(item["meta"]).decode() + " -->\n"
            + item["body"] + "\n<!-- /lks-sdd -->\n").encode("utf-8")


def location(item):
    return DOCS + "/elements/" + uid(item["meta"]["uid"]) + ".md"


@dataclass
class Element:
    meta: dict
    body: str
    path: str
    line: int = 1

    @property
    def uid(self): return self.meta["uid"]
    @property
    def id(self): return self.meta["id"]
    @property
    def kind(self): return self.meta["kind"]
    @property
    def data(self): return self.meta["data"]
    @property
    def relations(self): return self.meta["relations"]
    @property
    def retired(self): return self.meta["state"] in {"retired", "cancelled", "superseded"}

    def item(self): return {"meta": self.meta, "body": self.body}

    def normative(self):
        meta = {k: v for k, v in self.meta.items() if k not in {"state", "nature", "progress", "updated_at", "id", "revision"}}
        return {"meta": meta, "body": self.body}

    def digest(self): return fingerprint(self.normative())

    def targets(self):
        return {x for values in self.relations.values() for x in values}

    def source(self):
        return {"uid": self.uid, "id": self.id, "path": self.path, "line": self.line,
                "revision": self.meta["revision"], "digest": self.digest()}


def parse(raw, path):
    text = raw.decode("utf-8")
    version_match = re.search(r'^schema_version: [\"\']?(3\.[01])[\"\']?\r?$', text, re.M)
    if not version_match:
        raise ContractError("Se esperaba Markdown 3.0/3.1: " + path)
    matches = list(BLOCK.finditer(text))
    if len(matches) != text.count("<!-- lks-sdd:") or len(matches) != text.count("<!-- /lks-sdd -->"):
        raise ContractError("Bloques incompletos: " + path)
    result = []
    from v3_schema import validate
    for match in matches:
        meta = json.loads(match[1])
        validate("element", meta, version_match[1])
        uid(meta["uid"])
        if meta["kind"] not in KINDS or meta["state"] not in STATES:
            raise ContractError("Tipo o estado desconocido: " + path)
        for values in meta["relations"].values():
            if len(values) != len(set(values)):
                raise ContractError("Relación duplicada: " + path)
            for value in values:
                for part in value.split("/"): uid(part)
                if len(value.split("/")) > 2: raise ContractError("Referencia cualificada inválida")
        # render adds one framing newline; don't trim normative whitespace.
        body = match[2][:-1] if match[2].endswith("\n") else match[2]
        result.append(Element(meta, body, path, text.count("\n", 0, match.start()) + 1))
    prose = BLOCK.sub("", text)
    prose = re.sub(r'\A---\r?\n.*?\r?\n---\r?\n', '', prose, count=1, flags=re.S).strip()
    return result, prose


def document_paths(root):
    base = path_at(root, DOCS, missing=True)
    result = []
    if not base.exists(): return result
    excluded = {HISTORY, DOCS + "/evidence", DOCS + "/00-control/migrations"}
    for directory, folders, files in os.walk(base, followlinks=False):
        parent = Path(directory)
        folders[:] = sorted(n for n in folders if (parent / n).relative_to(root).as_posix() not in excluded)
        for name in folders + files: path_at(root, (parent / name).relative_to(root).as_posix())
        result.extend((parent / n).relative_to(root).as_posix() for n in files if n.endswith(".md"))
        if len(result) > 10000: raise ContractError("Inventario demasiado amplio; delimite el ámbito")
    return sorted(result)


@dataclass
class Model:
    root: Path
    elements: dict = field(default_factory=dict)
    hashes: dict = field(default_factory=dict)
    prose: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def require_valid(self):
        if self.errors: raise ContractError("; ".join(self.errors[:20]))
        return self

    def get(self, identifier, kind=None):
        if isinstance(identifier, str) and "/" in identifier:
            project, identifier = identifier.split("/", 1)
            if project != self.project.uid: raise ContractError("La dependencia externa necesita un contrato recibido y comprobable")
        candidates = [e for e in self.elements.values() if e.uid == identifier or e.id == identifier]
        if len(candidates) != 1: raise ContractError("Identidad inexistente o alias ambiguo: " + str(identifier))
        found = candidates[0]
        if kind and found.kind != kind: raise ContractError("Tipo requerido: " + kind)
        return found

    def by_kind(self, kind): return [e for e in self.elements.values() if e.kind == kind]

    @property
    def project(self):
        values = self.by_kind("project")
        if len(values) != 1: raise ContractError("Debe existir un único proyecto canónico")
        return values[0]

    def snapshot(self): return fingerprint(self.hashes)

    def at(self, identifier, digest):
        current = self.get(identifier)
        if current.digest() == digest: return current
        path = HISTORY + "/" + current.uid + "/" + digest + ".md"
        raw = read_bytes(self.root, path)
        self.hashes[path] = sha(raw)
        values, _ = parse(raw, path)
        if len(values) != 1 or values[0].uid != current.uid or values[0].digest() != digest:
            raise ContractError("Snapshot aprobado no recuperable")
        return values[0]

    def index(self):
        method = self.project.data["method_version"]
        return {"schema_version": METHODS[method], "method_version": method, "project_id": self.project.uid,
                "elements": {e.uid: {"path": e.path, "id": e.id, "kind": e.kind} for e in self.elements.values()}}


def load(root):
    root = Path(root).resolve()
    model = Model(root)
    total = 0
    for path in document_paths(root):
        try:
            raw = read_bytes(root, path)
            total += len(raw)
            if total > 32*1024*1024: raise ContractError("Contrato activo excesivo; archive historia mediante revisión explícita")
            model.hashes[path] = sha(raw)
            values, prose = parse(raw, path)
            if prose: model.prose[path] = prose
            for e in values:
                if e.uid in model.elements: raise ContractError("Identidad duplicada: " + e.uid)
                model.elements[e.uid] = e
        except (ValueError, UnicodeError, KeyError) as exc: model.errors.append(str(exc))
    try:
        project = model.project
        if project.data.get("method_version") not in METHODS:
            raise ContractError("Método desconocido; conserve el origen sin convertir")
        for e in model.elements.values():
            for ref in e.targets():
                target = ref.split("/")
                if len(target) == 2 and target[0] != project.uid:
                    model.warnings.append("Dependencia entre proyectos requiere evidencia explícita: " + ref)
                elif target[-1] not in model.elements:
                    model.errors.append("Referencia no resuelta: " + ref)
        from v31_review import validate_model
        validate_model(model)
    except ContractError as exc: model.errors.append(str(exc))
    index = path_at(root, INDEX, missing=True)
    if index.exists():
        model.hashes[INDEX] = sha(read_bytes(root, INDEX))
        try:
            value = json.loads(read_bytes(root, INDEX))
            if value.get("schema_version") != METHODS.get(model.project.data.get("method_version")): model.errors.append("Índice de otro formato; migración incompleta")
            elif model.elements and value != model.index(): model.warnings.append("Índice desactualizado; reconstruible desde Markdown")
        except (ValueError, ContractError): model.warnings.append("Índice ilegible; reconstruible desde Markdown")
    return model
