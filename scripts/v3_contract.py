"""Version 3 Markdown model. Indexes are derived; prose is part of the contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import uuid
import weakref

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
_QUERY_MODELS = ContextVar("lks_sdd_query_models", default=None)
_COPY_OBSERVERS = object()


@contextmanager
def query_evaluation():
    """Reuse a validated snapshot only during one read-only public operation."""
    if _QUERY_MODELS.get() is not None:
        yield
        return
    token = _QUERY_MODELS.set({})
    try:
        from object_zip import evaluation
        with evaluation(): yield
    finally:
        _QUERY_MODELS.reset(token)
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


@dataclass(init=False)
class Element:
    meta: dict
    body: str
    path: str
    line: int = 1
    resolved_data: dict | None = field(default=None, repr=False)
    _owners: object = field(default=None, init=False, repr=False, compare=False)

    def __init__(self, meta, body, path, line=1, resolved_data=None):
        # A fresh element has no model to invalidate. Reinitializing an attached
        # element still rejects active evaluations and preserves its owners.
        owners = getattr(self, "_owners", None)
        if owners is not None: self._identity_changed()
        object.__setattr__(self, "_owners", owners)
        object.__setattr__(self, "meta", _observe(meta, self._identity_changed))
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "line", line)
        object.__setattr__(self, "resolved_data", _observe(resolved_data, self._identity_changed))

    def __setattr__(self, name, value):
        if name in {"meta", "body", "path", "line", "resolved_data"}:
            self._identity_changed()
        if name == "meta":
            value = _observe(value, self._identity_changed)
        elif name == "resolved_data" and value is not None:
            value = _observe(value, self._identity_changed)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in {"meta", "body", "path", "line", "resolved_data"}:
            self._identity_changed()
        object.__delattr__(self, name)

    def _identity_changed(self):
        if getattr(self, "_owners", None) is not None: _notify_models(self._models())

    def _models(self):
        models = []
        owners = getattr(self, "_owners", None)
        for owner in tuple(owners.values()) if isinstance(owners, dict) else (owners,):
            model = owner() if owner is not None else None
            if model is not None and (model.elements.get(self.uid) is self or
                                      any(e is self for e in model.elements.values())):
                models.append(model)
        return models

    def _watch(self, model):
        owners = self._owners
        if owners is None or (not isinstance(owners, dict) and owners() is None):
            self._owners = weakref.ref(model)
        elif isinstance(owners, dict):
            self._owners = {k: ref for k, ref in owners.items() if ref() is not None}
            self._owners[id(model)] = weakref.ref(model)
        elif owners() is not model:
            self._owners = {id(owners()): owners, id(model): weakref.ref(model)}
        # A shallow Element copy shares these roots, but needs its own parent link.
        self.meta.watch(self._identity_changed)
        if self.resolved_data is not None: self.resolved_data.watch(self._identity_changed)

    def __deepcopy__(self, memo):
        import copy
        result = Element.__new__(Element)
        memo[id(self)] = result
        observed = memo.setdefault(_COPY_OBSERVERS, {})
        Element.__init__(result, _observe(copy.deepcopy(dict(self.meta), memo), memo=observed),
                         self.body, self.path, self.line,
                         _observe(copy.deepcopy(self.resolved_data, memo), memo=observed))
        return result

    @property
    def uid(self): return self.meta["uid"]
    @property
    def id(self): return self.meta["id"]
    @property
    def kind(self): return self.meta["kind"]
    @property
    def data(self): return self.resolved_data if self.resolved_data is not None else self.meta["data"]
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
    from v4_activity import checkpoint
    checkpoint()
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
        checkpoint()
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
    from path_utils import filesystem_root
    io_root = filesystem_root(root,force_extended=True)
    base = filesystem_root(path_at(root, DOCS, missing=True),force_extended=True)
    result = []
    if not base.exists(): return result
    excluded = {HISTORY, DOCS + "/evidence", DOCS + "/00-control/migrations"}
    for directory, folders, files in os.walk(base, followlinks=False):
        parent = Path(directory)
        folders[:] = sorted(n for n in folders if (parent / n).relative_to(io_root).as_posix() not in excluded)
        for name in folders + files: path_at(root, (parent / name).relative_to(io_root).as_posix())
        result.extend((parent / n).relative_to(io_root).as_posix() for n in files if n.endswith(".md"))
        if len(result) > 10000: raise ContractError("Inventario demasiado amplio; delimite el ámbito")
    return sorted(result)


def _notify_models(models):
    models = {id(model): model for model in models}.values()
    # Mark every affected model before raising: aliases may have active scopes
    # in several models, and catching the first error must not leave another valid.
    for model in models: model._revision += 1
    if any(model._evaluations for model in models):
        raise ContractError("El modelo cambió durante la evaluación; repita sobre una revisión inmutable")
    for model in models: model._invalidate_identities()


class _Observers:
    """Weak parent links allow shared inventories without copying their contents."""
    __slots__ = ()

    def watch(self, changed):
        if changed is None: return
        parent = changed.__self__
        parents = getattr(self, "_parents", None)
        if parents is None:
            self._parents = weakref.ref(parent)
        elif isinstance(parents, dict):
            parents[id(parent)] = weakref.ref(parent)
        elif parents() is not parent:
            previous = parents()
            self._parents = {id(parent): weakref.ref(parent)}
            if previous is not None: self._parents[id(previous)] = parents

    def changed(self):
        pending, seen, models = [self], set(), {}
        while pending:
            node = pending.pop()
            if id(node) in seen: continue
            seen.add(id(node))
            parents = getattr(node, "_parents", None)
            refs = tuple(parents.values()) if isinstance(parents, dict) else (parents,)
            for ref in refs:
                parent = ref() if ref is not None else None
                if parent is None: continue
                if isinstance(parent, dict): attached = any(v is node for v in parent.values())
                elif isinstance(parent, list): attached = any(v is node for v in parent)
                elif isinstance(parent, Element): attached = parent.meta is node or parent.resolved_data is node
                else: attached = any(getattr(parent, name, None) is node for name in ("elements", "prose", "errors", "warnings"))
                if attached:
                    if isinstance(parent, Element): models.update((id(m), m) for m in parent._models())
                    elif isinstance(parent, Model): models[id(parent)] = parent
                    else: pending.append(parent)
                elif isinstance(parents, dict): parents.pop(id(parent), None)
                else: node._parents = None
        _notify_models(models.values())


def _observe(value, changed=None, memo=None):
    """Own mutable JSON containers; preserve shared nodes within the input graph."""
    if isinstance(value, (_ObservedDict, _ObservedList)):
        value.watch(changed)
        return value
    if not isinstance(value, (dict, list)): return value
    memo = {} if memo is None else memo
    if id(value) in memo:
        result = memo[id(value)]
        result.watch(changed)
        return result
    return (_ObservedDict if isinstance(value, dict) else _ObservedList)(value, changed, memo=memo)


class _ObservedDict(dict, _Observers):
    """Notify before every normal edit, including edits through nested containers."""
    __slots__ = ("_parents", "_recursive", "__weakref__")
    def __init__(self, values, changed=None, *, memo=None, recursive=True):
        super().__init__()
        self.watch(changed)
        self._recursive = recursive
        memo = {} if memo is None else memo
        memo[id(values)] = self
        for key, value in values.items():
            dict.__setitem__(self, key, _observe(value, self.changed, memo) if recursive else value)

    def __setitem__(self, key, value):
        self.changed()
        super().__setitem__(key, _observe(value, self.changed) if self._recursive else value)

    def __delitem__(self, key):
        self.changed(); super().__delitem__(key)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items(): self[key] = value

    def clear(self):
        self.changed(); super().clear()

    def pop(self, *args):
        self.changed(); return super().pop(*args)

    def popitem(self):
        self.changed(); return super().popitem()

    def setdefault(self, key, default=None):
        if key not in self: self[key] = default
        return self[key]

    def __ior__(self, other):
        self.update(other); return self

    def __deepcopy__(self, memo):
        # A copied item is an independent draft, not an observer of its source.
        import copy
        return copy.deepcopy(dict(self), memo)

    def __copy__(self): return dict(self)

    @classmethod
    def fromkeys(cls, iterable, value=None): return dict.fromkeys(iterable, value)


class _ObservedList(list, _Observers):
    __slots__ = ("_parents", "__weakref__")
    def __init__(self, values, changed=None, *, memo=None):
        super().__init__()
        self.watch(changed)
        memo = {} if memo is None else memo
        memo[id(values)] = self
        list.extend(self, (_observe(value, self.changed, memo) for value in values))

    def __setitem__(self, key, value):
        self.changed()
        if isinstance(key, slice): value = [_observe(v, self.changed) for v in value]
        else: value = _observe(value, self.changed)
        super().__setitem__(key, value)

    def __delitem__(self, key): self.changed(); super().__delitem__(key)
    def append(self, value): self.changed(); super().append(_observe(value, self.changed))
    def extend(self, values):
        self.changed()
        super().extend([_observe(v, self.changed) for v in values])
    def insert(self, index, value): self.changed(); super().insert(index, _observe(value, self.changed))
    def pop(self, index=-1): self.changed(); return super().pop(index)
    def remove(self, value): self.changed(); super().remove(value)
    def clear(self): self.changed(); super().clear()
    def reverse(self): self.changed(); super().reverse()
    def sort(self, *args, **kwargs): self.changed(); super().sort(*args, **kwargs)
    def __iadd__(self, values): self.extend(values); return self
    def __imul__(self, count): self.changed(); super().__imul__(count); return self

    def __deepcopy__(self, memo):
        import copy
        return copy.deepcopy(list(self), memo)

    def __copy__(self): return list(self)


class _Elements(_ObservedDict):
    __slots__ = ()
    def __init__(self, values, model):
        super().__init__(values, model._semantic_changed, recursive=False)
        for entry in self.values(): entry._watch(model)

    def __setitem__(self, key, value):
        self.changed()
        parents = self._parents
        for ref in tuple(parents.values()) if isinstance(parents, dict) else (parents,):
            model = ref() if ref is not None else None
            if model is not None and model.elements is self: value._watch(model)
        dict.__setitem__(self, key, value)


@dataclass
class Model:
    root: Path
    elements: dict = field(default_factory=dict)
    hashes: dict = field(default_factory=dict)
    prose: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    _identities: dict | None = field(default=None, init=False, repr=False, compare=False)
    _kinds: dict | None = field(default=None, init=False, repr=False, compare=False)
    _revision: int = field(default=0, init=False, repr=False, compare=False)
    _evaluations: int = field(default=0, init=False, repr=False, compare=False)

    def __setattr__(self, name, value):
        if name in {"root", "elements", "prose", "errors", "warnings"}:
            self._semantic_changed()
        if name == "elements":
            if isinstance(value, _Elements):
                value.watch(self._semantic_changed)
                for entry in value.values(): entry._watch(self)
            else: value = _Elements(value, self)
        elif name in {"prose", "errors", "warnings"}:
            value = _observe(value, self._semantic_changed)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in {"root", "elements", "prose", "errors", "warnings"}:
            self._semantic_changed()
        object.__delattr__(self, name)

    def _semantic_changed(self):
        _notify_models([self])

    def __deepcopy__(self, memo):
        import copy
        result = Model.__new__(Model)
        memo[id(self)] = result
        Model.__init__(result, self.root, copy.deepcopy(dict(self.elements), memo),
                       copy.deepcopy(self.hashes, memo), copy.deepcopy(self.prose, memo),
                       copy.deepcopy(self.errors, memo), copy.deepcopy(self.warnings, memo))
        return result

    def __copy__(self):
        # Preserve ordinary shallow sharing, while binding every shared root and
        # element to both models. Evaluation state and identity indexes are local.
        result = Model.__new__(Model)
        result.__dict__.update(self.__dict__)
        result._evaluations = 0
        result._invalidate_identities()
        for name in ("elements", "prose", "errors", "warnings"):
            getattr(result, name).watch(result._semantic_changed)
        for entry in result.elements.values(): entry._watch(result)
        return result

    def _invalidate_identities(self):
        self._identities = self._kinds = None

    def _index_identities(self):
        if self._identities is not None: return
        identities, kinds = {}, {}
        for e in self.elements.values():
            for key in {e.uid, e.id}:
                previous = identities.get(key)
                identities[key] = e if previous is None else (*previous, e) if isinstance(previous, tuple) else (previous, e)
            kinds.setdefault(e.kind, []).append(e)
        self._kinds, self._identities = kinds, identities

    def require_valid(self):
        if self.errors: raise ContractError("; ".join(self.errors[:20]))
        return self

    def get(self, identifier, kind=None):
        if isinstance(identifier, str) and "/" in identifier:
            project, identifier = identifier.split("/", 1)
            if project != self.project.uid: raise ContractError("La dependencia externa necesita un contrato recibido y comprobable")
        self._index_identities()
        try: found = self._identities.get(identifier)
        except TypeError: found = None
        if found is None or isinstance(found, tuple): raise ContractError("Identidad inexistente o alias ambiguo: " + str(identifier))
        if kind and found.kind != kind: raise ContractError("Tipo requerido: " + kind)
        return found

    def by_kind(self, kind):
        self._index_identities()
        return list(self._kinds.get(kind, []))

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
        from v3_inventories import resolve
        resolve(self, values[0], {})
        return values[0]

    def index(self):
        method = self.project.data["method_version"]
        return {"schema_version": METHODS[method], "method_version": method, "project_id": self.project.uid,
                "elements": {e.uid: {"path": e.path, "id": e.id, "kind": e.kind} for e in self.elements.values()}}


def load(root):
    from object_zip import evaluation
    with evaluation(): return _load_snapshot(root)


def _load_snapshot(root):
    from v4_activity import checkpoint
    checkpoint()
    root = Path(root).resolve()
    cache = _QUERY_MODELS.get()
    if cache is not None and root in cache:
        return cache[root]
    model = _load(root)
    if cache is not None and not model.errors:
        cache[root] = model
    return model


def _load(root):
    from v3_evaluation import count
    count("model_loads")
    model = Model(root)
    from v2_storage import VALIDATING, PENDING
    if (root/PENDING).exists() and not VALIDATING.get():
        model.errors.append("Interrupted transaction: recover or rollback before normal operations")
        return model
    total = 0
    inventory_cache = {}
    elements = {}
    for path in document_paths(root):
        try:
            raw = read_bytes(root, path)
            total += len(raw)
            if total > 32*1024*1024: raise ContractError("Contrato activo excesivo; archive historia mediante revisión explícita")
            model.hashes[path] = sha(raw)
            values, prose = parse(raw, path)
            if prose: model.prose[path] = prose
            for e in values:
                if e.uid in elements: raise ContractError("Identidad duplicada: " + e.uid)
                elements[e.uid] = e
                from v3_inventories import resolve
                resolve(model, e, inventory_cache)
        except (ValueError, UnicodeError, KeyError) as exc: model.errors.append(str(exc))
    model.elements = elements
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
        from v3_scope import validate_prose_scope
        validate_prose_scope(model)
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
