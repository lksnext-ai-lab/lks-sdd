"""Explicit authoring of human Markdown; derived catalogs never grant authority."""
from __future__ import annotations

import json
import posixpath
from pathlib import Path
import re
import uuid

from v2_contract import (ContractError, DOCS, HISTORY, DOMAINS, BLOCK, ID, VERSION, METHOD,
                         Model, OPERATIONAL, canonical, fingerprint, load, make_element, metadata,
                         parse_document, path_at, read_bytes, render_block, render_document, sha,
                         TECHNOLOGY_DECLARATION_PATH)
from v2_storage import apply, ensure_idle, preview, stage_contract


def initialize(root: Path, name: str, *, project_id: str | None = None) -> tuple[dict, dict]:
    ensure_idle(root)
    if path_at(root, ".lks-sdd/project.json", missing=True).exists():
        raise ContractError("Project already exists; initialization is not migration")
    if not name.strip() or "\n" in name:
        raise ContractError("A single-line project name is required")
    project_id = project_id or str(uuid.uuid5(uuid.NAMESPACE_URL, str(root.absolute()) + ":" + name))
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, project_id)
    def entity(identifier, kind, title, body, **kwargs):
        return make_element(identifier, kind, title, body,
                            uid=str(uuid.uuid5(namespace, identifier)), **kwargs)
    project = entity("PRJ-001", "project", name,
                     "La cobertura documentada es parcial. Defina el alcance del próximo cambio antes de planificar su implementación.",
                     coverage="partial")
    obligations = [entity(f"APP-{i:03}", "applicability", domain,
                          "Pendiente de determinar para el ámbito solicitado.",
                          domain=domain, applicability="unknown", scope="global", critical=True,
                          nature="unknown", state="unknown") for i, domain in enumerate(DOMAINS, 1)]
    project_path = DOCS + "/01-context/project.md"
    rules_path = DOCS + "/02-specification/shared/applicability.md"
    project_document = render_document("project", name, [project])
    technology = entity(
        "TECH-001", "technology", "Tecnología pendiente de confirmar",
        "No se presume una pila tecnológica. Registre observaciones locales y confirme una decisión antes de usarla para preparar trabajo.",
        state="unknown", nature="unknown", relations={}, technology={
            "subject": "project technology decision",
            "state": "unknown",
            "critical": True,
            "scope": ["global"],
            "evidence": [{
                "kind": "consumer-document",
                "path": project_path,
                "sha256": sha(project_document),
            }],
            "provenance": [],
        },
    )
    technology_document = render_document(
        "technology-declaration", "Declaración tecnológica local", [technology],
        preamble="La declaración es local al proyecto. Una observación o una propuesta no equivale a una selección confirmada.",
    )
    index = {"schema_version": VERSION, "method_version": METHOD, "project_id": project_id,
             "plugin_version": json.loads((Path(__file__).resolve().parents[1] / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"], "name": name, "artifacts": [
                 {"id": "PRJ-001", "path": project_path}, {"id": "APP-001", "path": rules_path},
                 {"id": "TECH-001", "path": TECHNOLOGY_DECLARATION_PATH}]}
    changes = {project_path: project_document,
               rules_path: render_document("applicability", "Aplicabilidad del cambio", obligations),
               TECHNOLOGY_DECLARATION_PATH: technology_document,
               ".lks-sdd/project.json": canonical(index) + b"\n"}
    return preview(root, changes, sources={}, operation="initialize-v2"), changes


def history_changes(model: Model) -> tuple[str, dict[str, bytes]]:
    revision = model.snapshot()
    prefix = HISTORY + "/" + revision[:16]
    files = {}
    mapping = {}
    for path in sorted(model.hashes):
        # Preserve the whole relative tree so links remain navigable inside the
        # snapshot, including assets outside docs/lks-sdd and the project index.
        destination = prefix + "/tree/" + path
        data = read_bytes(model.root, path, limit=16 * 1024 * 1024)
        existing = path_at(model.root, destination, missing=True)
        if existing.exists() and existing.read_bytes() != data:
            raise ContractError("Historical snapshot collision")
        files[destination] = data
        mapping[path] = {"path": destination, "sha256": sha(data)}
    files[prefix + "/snapshot.json"] = canonical({"schema_version": VERSION, "snapshot": revision,
                                                   "sources": mapping, "state": "historical"})
    return revision, files


def historical(root: Path, revision: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        raise ContractError("Exact historical snapshot hash required")
    name = HISTORY + "/" + revision[:16] + "/snapshot.json"
    result = json.loads(read_bytes(root, name))
    if result.get("snapshot") != revision:
        raise ContractError("Historical snapshot identity mismatch")
    documents = []
    for source, entry in result["sources"].items():
        data = read_bytes(root, entry["path"], limit=16 * 1024 * 1024)
        if sha(data) != entry["sha256"]:
            raise ContractError("Historical content altered: " + source)
        documents.append({"source": source, **entry,
                          "text": data.decode("utf-8") if source.endswith(".md") else None})
    return {"status": "available", "snapshot": revision, "documents": documents, "writes": []}


def edit_elements(model: Model, replacements: dict[str, dict], bodies: dict[str, str] | None = None) -> dict[str, bytes]:
    changes = {}
    bodies = bodies or {}
    for identifier, value in replacements.items():
        old = model.elements[identifier]
        if value["id"] != identifier or value["uid"] != old.meta["uid"]:
            raise ContractError("Identity cannot be rewritten")
        text = changes.get(old.path, model.documents[old.path].encode()).decode()
        def replacement(match):
            current = json.loads(match[1])
            return render_block(value, bodies.get(identifier, match[2])).rstrip() if current["id"] == identifier else match[0]
        changes[old.path] = BLOCK.sub(replacement, text).encode()
    return changes


def author(model: Model, request: dict) -> tuple[dict, dict]:
    """A reviewed request contains complete blocks, not inferred business intent."""
    model.require_valid()
    ensure_idle(model.root)
    documents = request.get("documents", [])
    if not documents or not isinstance(documents, list):
        raise ContractError("Authoring request needs documents")
    _, changes = history_changes(model)
    seen = set()
    for document in documents:
        relative, text = document["path"], document["text"]
        if not relative.startswith(DOCS + "/") or relative.startswith(HISTORY + "/") or not relative.endswith(".md"):
            raise ContractError("Authoring is limited to active Markdown documents")
        if relative in seen:
            raise ContractError("Duplicate document target")
        seen.add(relative)
        path_at(model.root, relative, missing=True)
        elements, _ = parse_document(text, relative)
        for element in elements:
            old = model.elements.get(element.id)
            if element.kind in OPERATIONAL and (not old or old.meta != element.meta or old.body != element.body):
                raise ContractError("Operational records require their dedicated transition command: " + element.id)
            if element.kind == "task" and element.meta["state"] in {"done", "in-progress", "in-review", "blocked"} and (not old or old.meta["state"] != element.meta["state"]):
                raise ContractError("Authoring cannot fabricate a TASK execution result")
            if old and (old.meta["uid"] != element.meta["uid"] or element.meta["revision"] < old.meta["revision"]):
                raise ContractError("Identity/revision conflict: " + element.id)
            if old and old.normative() != element.normative() and element.meta["revision"] <= old.meta["revision"]:
                raise ContractError("A normative change requires a new revision: " + element.id)
        changes[relative] = text.encode("utf-8")
    # No element may vanish implicitly. Cancellation/retirement preserves its ID.
    resulting = {i for i, e in model.elements.items() if e.path not in seen}
    for p in seen:
        resulting.update(e.id for e in parse_document(changes[p].decode(), p)[0])
    if set(model.elements) - resulting:
        raise ContractError("Removing elements requires a preserved historical identity; retire or cancel instead")
    moves = request.get("moves", [])
    if len({m["from"] for m in moves}) != len(moves) or len({m["to"] for m in moves}) != len(moves):
        raise ContractError("Move endpoints must be unique")
    for move in moves:
        source, destination = move["from"], move["to"]
        if source not in model.documents or destination not in seen or source in seen:
            raise ContractError("Move must explicitly supply destination and retain all identities")
        expected_ids = {e.id for e in model.elements.values() if e.path == source}
        destination_ids = {e.id for e in parse_document(changes[destination].decode(), destination)[0]}
        if not expected_ids <= destination_ids or destination in model.documents:
            raise ContractError("Move cannot drop identities or overwrite another existing document")
        changes[source] = None
    index = dict(model.manifest)
    index["artifacts"] = [{"path": p} for p in sorted((set(model.documents) | seen) -
                           {m["from"] for m in request.get("moves", [])})]
    changes[".lks-sdd/project.json"] = canonical(index) + b"\n"
    sources = stage_contract(model.root, changes, model.hashes)
    return preview(model.root, changes, sources=sources, operation="author-v2"), changes


def commit(model: Model, request: dict, authorized_hash: str) -> dict:
    plan, changes = author(model, request)
    return apply(model.root, changes, plan, authorized_hash, validator=lambda: load(model.root).require_valid())


def catalog(model: Model) -> dict:
    from v2_lifecycle import is_active_execution

    items = []
    versions, history_diagnostics = feature_versions(model)
    for element in model.by_kind("feature") + model.by_kind("group"):
        tasks = [t for t in model.by_kind("task") if element.id in t.targets("contributes_to", "implements")]
        incoming = [{"id": e.id, "definition_state": e.meta["state"], "effectivity": e.meta.get("replacement"), "source": e.source()}
                    for e in model.elements.values() if element.id in e.targets("replaces", "splits", "merges")]
        items.append({"id": element.id, "uid": element.meta["uid"], "title": element.meta["title"],
                      "kind": element.kind, "definition_state": element.meta["state"],
                      "revision": element.meta["revision"], "source": element.source(),
                      "parent": element.relations.get("parent", []),
                      "replacement": element.meta.get("replacement"), "successors": incoming,
                      "tasks": [{"id": t.id, "state": t.meta["state"], "health": t.meta.get("health", "unknown"),
                                 "evidence": t.meta.get("evidence_ids", []), "source": t.source()} for t in tasks],
                      "deployment": [{"id": r.id, "observation": r.meta, "source": r.source()} for r in model.by_kind("receipt")
                                     if r.meta.get("category") == "delivery-observation" and element.id in r.targets("affects")],
                      "maintained_versions": element.meta.get("maintained_versions", []),
                      "definitions": versions.get(element.meta["uid"], []),
                      "verification": "see-task-evidence-not-inferred"})
    executions = [{
        "id": execution.id,
        "state": execution.meta["state"],
        "active": is_active_execution(execution),
        "normative_tasks": sorted(execution.targets("implements")),
        "historical_antecedents": sorted(execution.targets("affects")),
        "source": execution.source(),
    } for execution in model.by_kind("execution")]
    return {"schema_version": VERSION, "kind": "derived-catalog", "snapshot": model.snapshot(),
            "coverage": "partial-unless-explicitly-documented", "features": sorted(items, key=lambda e: e["id"]),
            "executions": sorted(executions, key=lambda e: e["id"]),
            "diagnostics": [*model.errors, *history_diagnostics], "writes": []}


def feature_versions(model):
    """A light derived history, with exact sources; never retire current behavior."""
    from v2_contract import parse_document, fingerprint
    result, seen, diagnostics = {}, set(), []
    def add(entry, source, snapshot=None):
        signature = fingerprint(entry.normative())
        key = (entry.meta["uid"], signature)
        if key in seen:
            return
        seen.add(key)
        result.setdefault(entry.meta["uid"], []).append({"id": entry.id, "revision": entry.meta["revision"],
            "definition_state": entry.meta["state"], "normative_sha256": signature, "source": source,
            "snapshot": snapshot, "effectivity": entry.meta.get("replacement"),
            "maintained_versions": entry.meta.get("maintained_versions", []), "verification": "not-inferred"})
    for entry in model.by_kind("feature"):
        add(entry, entry.source())
    folder = path_at(model.root, HISTORY, missing=True)
    manifests = sorted(folder.glob("*/snapshot.json")) if folder.exists() else []
    if len(manifests) > 128:
        diagnostics.append("Historical catalog limited to 128 snapshots; use history with an exact snapshot for more")
    consumed = 0
    for path in manifests[:128]:
        try:
            summary = json.loads(read_bytes(model.root, path.relative_to(model.root).as_posix()))
            for original, ref in summary["sources"].items():
                if not original.endswith(".md") or "/features/" not in original:
                    continue
                raw = read_bytes(model.root, ref["path"])
                consumed += len(raw)
                if consumed > 16 * 1024 * 1024:
                    diagnostics.append("Historical catalog byte limit reached; expand by exact snapshot")
                    return result, diagnostics
                if sha(raw) != ref["sha256"]:
                    raise ContractError("Historical feature source changed")
                for entry in parse_document(raw.decode("utf-8"), ref["path"])[0]:
                    if entry.kind == "feature":
                        add(entry, entry.source(), summary["snapshot"])
        except (ContractError, OSError, ValueError, KeyError) as exc:
            diagnostics.append("Historical source unavailable: " + path.parent.name + ": " + str(exc))
    return result, diagnostics


def catalog_markdown(model: Model) -> str:
    result = catalog(model)
    rows = ['---', 'schema_version: "2.0"', 'artifact_type: "derived"', '---', '',
            '# Catálogo de funcionalidades', '',
            'Vista derivada. Cobertura parcial; los estados documentados no prueban despliegue.', '',
            '| Funcionalidad | Definición | Tareas | Evolución |', '|---|---|---|---|']
    origin = DOCS + "/02-specification/catalog.md"
    for item in result["features"]:
        link = posixpath.relpath(item["source"]["path"], posixpath.dirname(origin)) + "#" + item["id"].lower()
        title = item["title"].replace("|", "\\|").replace("\n", " ")
        tasks = ", ".join(t["id"] + ": " + t["state"] for t in item["tasks"]) or "No documentadas"
        evolution = ", ".join(s["id"] + " (" + (s["effectivity"] or {}).get("state", "no determinada") + ")" for s in item["successors"])
        rows.append(f'| [{item["id"]} · {title}](<{link}>) | {item["definition_state"]} · revisión {item["revision"]} | {tasks} | {evolution or "Sin sustitución documentada"} |')
    if result["executions"]:
        rows += ['', '## Historial operativo', '',
                 'Los registros `reconciliation-required` se conservan como antecedentes auditables y no autorizan trabajo v2.',
                 '', '| Ejecución | Estado | Ámbito normativo | Antecedentes históricos |',
                 '|---|---|---|---|']
        for execution in result["executions"]:
            normative = ", ".join(execution["normative_tasks"]) or "Ninguno"
            antecedents = ", ".join(execution["historical_antecedents"]) or "Ninguno"
            rows.append(f'| {execution["id"]} | {execution["state"]} | {normative} | {antecedents} |')
    rows += ['', 'Origen: snapshot `' + result["snapshot"] + '`.', '']
    return "\n".join(rows)


def export_catalog(model: Model, authorized_hash: str | None = None) -> dict:
    relative = DOCS + "/02-specification/catalog.md"
    if relative in model.documents and metadata(model.documents[relative]).get("artifact_type") != "derived":
        raise ContractError("Catalog path contains human canonical content; no overwrite")
    changes = {relative: catalog_markdown(model).encode()}
    plan = preview(model.root, changes, sources=model.hashes, operation="export-catalog")
    return apply(model.root, changes, plan, authorized_hash) if authorized_hash else plan
