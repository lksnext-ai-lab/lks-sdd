"""Versioned Markdown contract. Read-only, bounded, no consumer code execution.

This model is derived, never persisted as a second source of requirements.
Historical v1 readers remain separate. JSON comments describe data, not commands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import unquote, urlsplit
import uuid

from query_sources import is_link, lexical_root, SECRET_NAME

VERSION = "2.0"
METHOD = "2.0.0"
READER = "lks-sdd-v2/1"
DOCS = "docs/lks-sdd"
HISTORY = DOCS + "/00-control/history"
KINDS = set("project feature group requirement acceptance rule constraint task increment plan release test decision interface binding environment authorization execution checkpoint problem change applicability legacy receipt visual".split())
RELATIONS = set("parent uses depends_on requirements acceptance tests contributes_to implements modifies replaces splits merges increment release plan bindings interfaces environments decision authorizes execution verifies sources affects".split())
OPERATIONAL = {"authorization", "execution", "checkpoint", "problem", "receipt"}
NON_NORMATIVE_BY_DEFAULT = {"legacy"}
ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z]+)*-\d{3,}")
BLOCK = re.compile(r"^<!-- lks-sdd: (\{[^\n]*\}) -->\s*\n(.*?)^<!-- /lks-sdd -->[ \t]*$", re.M | re.S)
LINK = re.compile(r"(?<!!)\[([^\]]+)\]\((?:<([^>]+)>|([^\s)]+))\)")
ASSET = re.compile(r"!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)")
ANCHOR = re.compile(r'<a\s+id=[\"\']([^\"\']+)[\"\']\s*></a>')
DOMAINS = ("ux", "data", "identity", "security", "privacy", "interfaces", "quality", "operation")
STATES = {"draft", "proposed", "confirmed", "approved", "active", "effective", "superseded", "retired", "cancelled", "unknown", "conflict", "backlog", "ready", "in-progress", "in-review", "done", "blocked", "paused", "completed", "revoked", "open", "resolved", "reconciliation-required"}


class ContractError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(value) -> str:
    return sha(canonical(value))


def path_at(root: Path, relative: str, *, missing: bool = False, package_data: bool = False) -> Path:
    if (not relative or "\\" in relative or ":" in relative or
            PurePosixPath(relative).is_absolute() or
            any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise ContractError("Unsafe project-relative path: " + relative)
    current = root
    parts = relative.split("/")
    for index, part in enumerate(parts):
        # Explicit package/scaffold operations may carry a placeholder template or
        # a named certification result. Ordinary document/code reads never opt in.
        benign_package_leaf = package_data and index == len(parts) - 1 and (
            part == ".env.example" or (part == "GATE-LOCAL-CREDENTIALS.json" and "certification-details" in parts))
        if part.casefold() == ".git" or (SECRET_NAME.search(part) and not benign_package_leaf):
            raise ContractError("Sensitive or Git path is not a contract input: " + relative)
        current /= part
        if os.path.lexists(current):
            if is_link(current):
                raise ContractError("Link/junction rejected: " + relative)
            if current.is_dir() and current != root and (current / ".git").exists():
                raise ContractError("Nested repository rejected: " + relative)
        elif not missing:
            raise ContractError("Missing source: " + relative)
    return current


def read_bytes(root: Path, relative: str, *, limit: int = 4 * 1024 * 1024, package_data: bool = False) -> bytes:
    path = path_at(root, relative, package_data=package_data)
    if not path.is_file() or path.stat().st_size > limit:
        raise ContractError("Not a bounded regular source: " + relative)
    data = path.read_bytes()
    if len(data) > limit:
        raise ContractError("Source exceeded read limit: " + relative)
    return data


def metadata(text: str) -> dict:
    from contract_engine import _parse_frontmatter
    if not text.startswith("---\n"):
        return {}
    try:
        return _parse_frontmatter(text)[0]
    except ValueError as exc:
        raise ContractError("Invalid document frontmatter") from exc


def make_element(identifier: str, kind: str, title: str, body: str, **values) -> dict:
    value = {"id": identifier, "uid": str(uuid.uuid4()), "kind": kind, "title": title,
             "revision": 1, "state": "draft", "nature": "proposal", "relations": {}}
    value.update(values)
    return {"meta": value, "body": body}


def render_block(meta: dict, body: str) -> str:
    anchor = '<a id="' + meta["id"].lower() + '"></a>'
    if anchor not in body:
        body = anchor + "\n\n## " + meta["id"] + " · " + meta["title"] + "\n\n" + body
    return "<!-- lks-sdd: " + canonical(meta).decode() + " -->\n" + body.strip() + "\n<!-- /lks-sdd -->\n"


def render_document(kind: str, title: str, elements: list[dict], *, preamble: str = "") -> bytes:
    return (f'---\nschema_version: "{VERSION}"\nartifact_type: "{kind}"\n---\n\n# {title}\n\n'
            + (preamble.strip() + "\n\n" if preamble.strip() else "")
            + "\n".join(render_block(e["meta"], e["body"]) for e in elements)).encode("utf-8")


@dataclass
class Element:
    meta: dict
    body: str
    path: str
    line: int

    @property
    def id(self):
        return self.meta["id"]

    @property
    def kind(self):
        return self.meta["kind"]

    @property
    def relations(self):
        return self.meta.get("relations", {})

    def targets(self, *relations) -> set[str]:
        return {target for relation, targets in self.relations.items()
                if not relations or relation in relations for target in targets}

    def normative(self) -> dict:
        meta = dict(self.meta)
        if self.kind in NON_NORMATIVE_BY_DEFAULT:
            return {"meta": {}, "body": ""}
        if self.kind == "task":
            for key in ("state", "health", "execution_id", "evidence_ids", "progress", "updated_at"):
                meta.pop(key, None)
        return {"meta": meta, "body": self.body}

    def source(self) -> dict:
        return {"path": self.path, "line": self.line, "anchor": self.id.lower(), "id": self.id}


def parse_document(text: str, path: str) -> tuple[list[Element], str]:
    text = text.replace("\r\n", "\n")
    frontmatter = metadata(text)
    if str(frontmatter.get("schema_version")) != VERSION:
        raise ContractError("Expected document contract 2.0: " + path)
    if frontmatter.get("artifact_type") == "derived":
        if "<!-- lks-sdd:" in text:
            raise ContractError("Derived view cannot define elements: " + path)
        return [], ""
    matches = list(BLOCK.finditer(text))
    if len(matches) != text.count("<!-- lks-sdd:") or len(matches) != text.count("<!-- /lks-sdd -->"):
        raise ContractError("Unclosed, nested or multiline metadata block: " + path)
    elements = []
    for match in matches:
        try:
            value = json.loads(match[1])
            from v2_schema import validate
            validate("element", value)
            if not isinstance(value, dict):
                raise ValueError("object required")
            if not ID.fullmatch(value.get("id", "")) or value.get("kind") not in KINDS:
                raise ValueError("invalid id/kind")
            if str(uuid.UUID(value["uid"])) != value["uid"]:
                raise ValueError("canonical UUID required")
            if type(value.get("revision")) is not int or value["revision"] < 1:
                raise ValueError("positive revision required")
            if value.get("state") not in STATES or value.get("nature") not in {"fact", "inference", "proposal", "decision", "unknown"}:
                raise ValueError("state/nature required")
            if not isinstance(value.get("title"), str) or not value["title"].strip():
                raise ValueError("title required")
            relations = value.get("relations")
            if not isinstance(relations, dict):
                raise ValueError("relations map required")
            for relation, targets in relations.items():
                if relation not in RELATIONS or not isinstance(targets, list) or len(targets) != len(set(targets)):
                    raise ValueError("invalid typed relation")
                if any(not isinstance(t, str) or not ID.fullmatch(t) for t in targets):
                    raise ValueError("invalid relation target")
            if len(relations.get("parent", [])) > 1:
                raise ValueError("only one principal parent")
            if value["id"].lower() not in ANCHOR.findall(match[2]):
                raise ValueError("stable anchor missing")
            if "replacement" in value:
                replacement = value["replacement"]
                if (replacement.get("mode") not in {"partial", "total"} or not replacement.get("effective")
                        or replacement.get("state") not in {"proposed", "approved", "effective"}
                        or (replacement["mode"] == "partial" and not replacement.get("residual_scope"))):
                    raise ValueError("replacement requires effectivity and residual scope")
            elements.append(Element(value, match[2].strip(), path, text.count("\n", 0, match.start()) + 1))
        except (ValueError, TypeError, KeyError) as exc:
            raise ContractError(f"Invalid block in {path}: {exc}") from exc
    return elements, BLOCK.sub("", text)


def document_paths(root: Path) -> list[str]:
    base = path_at(root, DOCS)
    paths = []
    count = 0
    for directory, folders, files in os.walk(base, followlinks=False):
        parent = Path(directory)
        folders[:] = sorted(d for d in folders if (parent / d).relative_to(root).as_posix() not in
                            {HISTORY, DOCS + "/evidence", DOCS + "/00-control/migrations"})
        for name in folders + files:
            count += 1
            if count > 50000:
                raise ContractError("Document inventory limit exceeded")
            path_at(root, (parent / name).relative_to(root).as_posix())
        paths.extend((parent / name).relative_to(root).as_posix() for name in sorted(files) if name.endswith(".md"))
    if len(paths) > 1500:
        raise ContractError("Document count limit exceeded")
    return sorted(paths)


@dataclass
class Model:
    root: Path
    manifest: dict
    elements: dict[str, Element] = field(default_factory=dict)
    documents: dict[str, str] = field(default_factory=dict)
    preambles: dict[str, str] = field(default_factory=dict)
    hashes: dict[str, str] = field(default_factory=dict)
    assets: dict[str, dict[str, str]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self):
        return not self.errors

    def require_valid(self):
        if self.errors:
            raise ContractError("; ".join(self.errors[:12]))

    def snapshot(self):
        return fingerprint({"reader": READER, "sources": self.hashes})

    def normative(self, identifiers: set[str]) -> dict:
        elements = [self.elements[i] for i in sorted(identifiers)]
        paths = {e.path for e in elements if e.kind not in OPERATIONAL}
        attachments = {}
        for path in sorted(paths):
            for asset, expected in self.assets.get(path, {}).items():
                if asset.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
                    raw = read_bytes(self.root, asset)
                    if sha(raw) != expected:
                        raise ContractError("Normative attachment changed during read: " + asset)
                    attachments[asset] = raw.decode("utf-8")
        return {"reader": READER, "project": self.manifest.get("project_id"),
                "elements": [e.normative() for e in elements
                             if e.kind not in OPERATIONAL and e.kind not in NON_NORMATIVE_BY_DEFAULT],
                "preambles": {p: self.preambles[p] for p in sorted(paths)},
                "assets": {p: self.assets.get(p, {}) for p in sorted(paths)},
                "text_attachments": attachments}

    def by_kind(self, kind):
        return [e for e in self.elements.values() if e.kind == kind]

    def revalidate(self):
        if document_paths(self.root) != sorted(self.documents):
            raise ContractError("Document inventory changed during read")
        for path, expected in self.hashes.items():
            if sha(read_bytes(self.root, path)) != expected:
                raise ContractError("Source changed during read: " + path)


def resolve_link(source: str, target: str) -> tuple[str, str]:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise ContractError("Not an internal source link")
    path = unquote(parsed.path)
    if path.startswith(("/", "\\")) or "\\" in path or ":" in path:
        raise ContractError("Unsafe link")
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), path)) if path else source
    if resolved.startswith("../") or resolved == "..":
        raise ContractError("Link escapes root")
    return resolved, unquote(parsed.fragment)


def load(root: Path) -> Model:
    root = lexical_root(root)
    from v2_storage import VALIDATING, ensure_idle
    if not VALIDATING.get():
        ensure_idle(root)
    raw = read_bytes(root, ".lks-sdd/project.json")
    manifest = json.loads(raw)
    from v2_schema import validate
    validate("project", manifest)
    if manifest.get("schema_version") != VERSION or manifest.get("method_version") != METHOD:
        raise ContractError("Unsupported project contract/method; no implicit conversion")
    if not manifest.get("project_id"):
        raise ContractError("Project identity required")
    model = Model(root, manifest, hashes={".lks-sdd/project.json": sha(raw)})
    uids = {}
    total = 0
    for relative in document_paths(root):
        raw = read_bytes(root, relative)
        total += len(raw)
        if total > 32 * 1024 * 1024:
            raise ContractError("Document byte budget exceeded")
        text = raw.decode("utf-8").replace("\r\n", "\n")
        model.documents[relative] = text
        model.hashes[relative] = sha(raw)
        if relative == DOCS + "/03-solution/technology-variants.md":
            from project_variants import read_markdown, validate_schema
            validate_schema(read_markdown(root, relative), "project-variants.schema.json")
            model.preambles[relative] = text
            continue
        if relative.startswith(DOCS + "/00-control/technology-approvals/"):
            from project_variants import read_markdown, digest
            approval = read_markdown(root, relative)
            if digest({k: v for k, v in approval.items() if k != "approval_id"}) != approval.get("approval_id"):
                model.errors.append("Technology approval integrity mismatch")
            model.preambles[relative] = ""
            continue
        try:
            elements, preamble = parse_document(text, relative)
            model.preambles[relative] = preamble
            for element in elements:
                if element.id in model.elements or element.meta["uid"] in uids:
                    model.errors.append("Identity/alias collision: " + element.id)
                    continue
                model.elements[element.id] = element
                uids[element.meta["uid"]] = element.id
        except ContractError as exc:
            model.errors.append(str(exc))
    for element in model.elements.values():
        for target in element.targets():
            if target not in model.elements:
                model.errors.append(f"Orphan relation {element.id} -> {target}")
        for target in element.targets("parent"):
            if target in model.elements and (element.kind not in {"feature", "group"} or model.elements[target].kind not in {"feature", "group"}):
                model.errors.append("Parent is a logical feature/group relation: " + element.id)
        for relation in ("replaces", "splits", "merges"):
            if element.targets(relation) and not element.meta.get("replacement"):
                model.errors.append("Evolution requires explicit effectivity/residual scope: " + element.id)
        if element.kind == "visual":
            for asset in element.meta.get("baseline_assets", []):
                try:
                    if not isinstance(asset, str) or not asset.startswith(DOCS + "/"):
                        raise ContractError("Visual baseline must be a canonical project asset")
                    data = read_bytes(root, asset, limit=16 * 1024 * 1024)
                    model.hashes[asset] = sha(data)
                    model.assets.setdefault(element.path, {})[asset] = sha(data)
                except (ContractError, OSError) as exc:
                    model.errors.append(f"{element.id}: invalid visual baseline: {exc}")
    for relation in ("parent", "depends_on"):
        visiting, done = set(), set()
        def visit(identifier):
            if identifier in visiting:
                raise ContractError("Cycle in " + relation + ": " + identifier)
            if identifier in done or identifier not in model.elements:
                return
            visiting.add(identifier)
            for target in model.elements[identifier].targets(relation):
                visit(target)
            visiting.remove(identifier)
            done.add(identifier)
        try:
            for identifier in model.elements:
                visit(identifier)
        except (ContractError, RecursionError) as exc:
            model.errors.append(str(exc))
    for relative, text in model.documents.items():
        if not model.preambles.get(relative):
            continue  # Derived views never influence contract fingerprints.
        for label, angled, plain in LINK.findall(text):
            target = angled or plain
            if urlsplit(target).scheme:
                continue
            try:
                destination, anchor = resolve_link(relative, target)
                target_path = path_at(root, destination)
                if target_path.is_dir():
                    if anchor or ID.search(label):
                        raise ContractError("Element link points to directory")
                    continue
                data = read_bytes(root, destination)
                if destination not in model.documents:
                    model.hashes[destination] = sha(data)
                    if not destination.startswith(DOCS + "/evidence/"):
                        model.assets.setdefault(relative, {})[destination] = sha(data)
                if destination.endswith(".md"):
                    target_text = data.decode("utf-8")
                    if anchor and anchor not in ANCHOR.findall(target_text):
                        raise ContractError("Missing explicit anchor: " + anchor)
                    for identifier in ID.findall(label):
                        element = model.elements.get(identifier)
                        if destination.startswith(HISTORY + "/"):
                            if identifier.lower() != anchor:
                                raise ContractError("Historical ID/anchor mismatch")
                        elif not element or element.path != destination or anchor != identifier.lower():
                            raise ContractError("Link label/target identity mismatch: " + identifier)
            except (ContractError, OSError, UnicodeError) as exc:
                model.errors.append(f"{relative}: {exc}")
        for angled, plain in ASSET.findall(text):
            try:
                destination, _ = resolve_link(relative, angled or plain)
                data = read_bytes(root, destination)
                model.assets.setdefault(relative, {})[destination] = sha(data)
                model.hashes[destination] = sha(data)
            except (ContractError, OSError) as exc:
                model.errors.append(f"{relative}: invalid asset: {exc}")
    model.revalidate()
    return model


def execution_context(model: Model, tasks: list[str]) -> dict:
    model.require_valid()
    if not tasks or len(tasks) != len(set(tasks)):
        raise ContractError("Select unique, nonempty TASK scope")
    for task in tasks:
        if task not in model.elements or model.elements[task].kind != "task":
            raise ContractError("Unknown TASK: " + task)
        if model.elements[task].meta["state"] in {"cancelled", "retired", "superseded"}:
            raise ContractError("Inactive TASK cannot be an execution root: " + task)
    selected = set(tasks)
    reasons = {t: ["selected-task"] for t in tasks}
    changed = True
    # Include complete relation closure and inverse contributors/consumers.
    while changed:
        before = set(selected)
        for identifier in tuple(selected):
            entry = model.elements[identifier]
            traversed = set(entry.relations) - {"parent"}
            if entry.kind in {"plan", "increment", "release"}:
                traversed -= {"requirements", "implements", "contributes_to"}
            for target in entry.targets(*traversed) if traversed else ():
                if (model.elements[target].kind not in OPERATIONAL
                        and model.elements[target].kind not in NON_NORMATIVE_BY_DEFAULT):
                    selected.add(target)
                    reasons.setdefault(target, []).append("relation:" + identifier)
        for e in model.elements.values():
            if e.kind in OPERATIONAL or e.kind in NON_NORMATIVE_BY_DEFAULT:
                continue
            # Migration-created unknown applicability is preserved as data, but
            # must not become a global v2 obligation before an explicit review.
            if (e.kind == "applicability" and e.meta.get("state") == "unknown"
                    and e.meta.get("migration")):
                continue
            if e.targets("contributes_to", "implements", "requirements", "uses", "interfaces") & selected:
                selected.add(e.id)
                reasons.setdefault(e.id, []).append("contributor-or-consumer")
            if e.kind in {"rule", "constraint", "applicability"} and e.meta.get("scope", "unknown") in {"global", "unknown"}:
                selected.add(e.id)
                reasons.setdefault(e.id, []).append("shared-or-uncertain-applicability")
            if e.kind == "decision" and e.meta.get("category") in {"delivery-governance", "tracking"}:
                selected.add(e.id)
                reasons.setdefault(e.id, []).append("governance-policy")
        changed = before != selected
    blockers = []
    for identifier in sorted(selected):
        e = model.elements[identifier]
        if e.kind in {"requirement", "acceptance", "rule", "constraint", "interface", "feature", "decision"}:
            if e.meta["state"] not in {"confirmed", "approved", "active", "effective"}:
                blockers.append("Unconfirmed obligation: " + identifier)
        if e.meta.get("scope") == "unknown" and e.meta.get("critical", True):
            blockers.append("Critical applicability unknown: " + identifier)
    applicability = {}
    for e in model.by_kind("applicability"):
        if e.id not in selected:
            continue
        domain = e.meta.get("domain")
        if domain in applicability:
            blockers.append("Conflicting/ambiguous applicability for domain: " + str(domain))
        applicability[domain] = e
    migration_unknown_domains = {
        e.meta.get("domain") for e in model.by_kind("applicability")
        if e.meta.get("state") == "unknown" and e.meta.get("migration")
    }
    for domain in DOMAINS:
        entry = applicability.get(domain)
        if domain in migration_unknown_domains:
            continue
        if not entry or entry.meta.get("applicability") not in {"applicable", "not-applicable"}:
            blockers.append("Applicability unresolved: " + domain)
        elif entry.meta["state"] not in {"confirmed", "approved"}:
            blockers.append("Applicability unconfirmed: " + domain)
        elif entry.meta["applicability"] == "not-applicable" and not entry.meta.get("reason"):
            blockers.append("Applicability exclusion needs reason: " + domain)
        elif entry.meta["applicability"] == "applicable" and not entry.targets("requirements"):
            blockers.append("Applicable domain has no documented obligations: " + domain)
    material = model.normative(selected)
    return {"schema_version": VERSION, "kind": "execution-context", "task_ids": tasks,
            "status": "blocked" if blockers else "sufficient", "blockers": sorted(set(blockers)),
            "fingerprint": fingerprint(material), "normative": material,
            "organizational_parents": [{"id": i, "source": model.elements[i].source(), "approval_inherited": False}
                                       for i in sorted({p for e in selected for p in model.elements[e].targets("parent")} - selected)],
            "elements": [{**e.normative(), "source": e.source(), "included_because": sorted(set(reasons.get(e.id, [])))}
                         for e in (model.elements[i] for i in sorted(selected))],
            "writes": [], "consumer_executions": [], "authorization": "not-assessed"}
