"""Document-first retrieval over safe snapshots, not consumer state validation."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from itertools import combinations
import json
import posixpath
import re
import unicodedata
from urllib.parse import unquote

from contract_engine import (ContractEngineError, ProjectModel, ProjectRow, ProjectEdge,
                             _parse_frontmatter, _parse_markdown_tables, load_registry,
                             parse_reference_cell)
from query_sources import SourceReader, identity


ENTITY = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z]+)*-\d{3,}\b")
STOP = {"que", "como", "del", "las", "los", "una", "unos", "para", "por", "con", "sin",
        "sobre", "cual", "cuales", "esta", "este", "the", "and", "what", "how", "does",
        "explica", "explicame", "consulta", "requisitos", "especificacion", "especificaciones", "tareas",
        "requirements", "specification", "specifications", "tasks"}
GLOBAL = re.compile(r"(?i)(?:^|[/_.-])(?:constraints|security|glossary|reglas|restricciones|seguridad|glosario)(?:[/_.-]|$)")


def normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    # Keep the ASCII fast path in C; only non-ASCII marks need Unicode lookup.
    return re.sub(r"[^\x00-\x7f]", lambda m: "" if unicodedata.combining(m[0]) else m[0], folded)


def terms(topic: str) -> list[str]:
    return sorted({t for t in re.findall(r"[\w-]+", normalize(topic)) if len(t) > 2 and t not in STOP})


def without_fences(text: str) -> str:
    if "```" not in text and "~~~" not in text:
        return text
    output, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            output.append("")
        else:
            output.append("" if fence else line)
    return "\n".join(output)


def snapshot_model(reader: SourceReader, manifest: dict) -> tuple[ProjectModel, list[dict], list[dict], dict]:
    """Reuse contract types/parsers without build_project_model's broader I/O.

    This is a projection of snapshots, never a valid-contract assertion. A full
    validation remains the existing strict workflow and is not run by a question.
    """
    version = str(manifest.get("schema_version", "1.5"))
    if version == "2.0":
        from v2_query import snapshot_records
        return snapshot_records(reader, manifest)
    try:
        registry = load_registry(version)
    except ContractEngineError:
        registry = None
        reader.warnings.append("unsupported-schema-text-only")
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        artifacts = []
        reader.warnings.append("invalid-manifest-artifacts")
    indexed = {e["path"]: e for e in artifacts if isinstance(e, dict) and isinstance(e.get("path"), str)}
    rows, nodes, model_edges = {}, {}, []
    records, relations, definitions = [], [], defaultdict(list)
    for path, source in reader.sources.items():
        if source["kind"] != "document":
            continue
        text = without_fences(source["text"])
        metadata, body, start = {}, text, 1
        if text.startswith("---\n"):
            try:
                metadata, body, start = _parse_frontmatter(text)
            except ValueError:
                reader.exclude(path, "unparsed-frontmatter")
        artifact_id = str(metadata.get("artifact_id", indexed.get(path, {}).get("id", "")))
        artifact_type = str(metadata.get("artifact_type", ""))
        contract = registry.artifact_for(artifact_id, artifact_type) if registry else None
        for table in (_parse_markdown_tables(body, start) if "|" in body else ()):
            typed = contract.tables_by_headers.get(table.headers) if contract else None
            for line, cells in table.rows:
                if typed:
                    first = cells.get(typed.key_column, "") if typed.key_column else ""
                else:
                    first = next(iter(cells.values()), "") if normalize(table.headers[0]) in {"id", "identificador", "codigo"} else ""
                key = first.strip(" `") if ENTITY.fullmatch(first.strip(" `")) else None
                uid = f"{path}:{line}"
                state_column = typed.state_column if typed else next((h for h in cells if normalize(h) in {"estado", "status", "state"}), None)
                state = cells.get(state_column) if state_column else None
                if key:
                    definitions[key].append(uid)
                    records.append({"id": key, "source": path, "line": line, "cells": cells,
                                    "declared_state": state, "authority": "declared-not-validated",
                                    "nature": "documented", "typed": typed is not None})
                references = []
                if typed:
                    row = ProjectRow(uid, artifact_id, artifact_type, path, typed.table_id, line, cells, typed, key, state)
                    rows[uid] = row
                    if key:
                        nodes.setdefault(key, row)
                    for column, base_spec in typed.relations.items():
                        spec = replace(base_spec, targets=base_spec.targets_for(cells))
                        if typed.applicability and column == typed.applicability.references_column and cells.get(typed.applicability.applicability_column) != "applicable":
                            continue
                        parsed = parse_reference_cell(cells.get(column, ""), spec,
                                                      max_range_size=registry.max_range_size)
                        row.reference_results[column] = parsed
                        if not parsed.valid:
                            reader.exclude(path, "invalid-reference-cell")
                            continue
                        for target in parsed.references:
                            references.append((target, column))
                            if len(model_edges) < reader.limits.max_relations:
                                model_edges.append(ProjectEdge(uid, key, column, target, spec.active_input, spec.require_defined))
                else:
                    # A mention is not a dependency, ownership or approval relation.
                    for column, value in cells.items():
                        for target in sorted(set(ENTITY.findall(value)) - {key}):
                            references.append((target, column))
                if key:
                    candidates = ((key, target, column, "declared" if typed else "explicit-mention")
                                  for target, column in references)
                else:
                    # Coverage/traceability rows reference entities; they do not
                    # define duplicate requirements, tasks or increments.
                    candidates = ((left, right, lc + " / " + rc,
                                   "declared-co-reference" if typed else "explicit-mention")
                                  for (left, lc), (right, rc) in combinations(dict.fromkeys(references), 2) if left != right)
                for left, right, column, nature in candidates:
                    if len(relations) >= reader.limits.max_relations:
                        reader.exclude(path, "relation-count-limit")
                        break
                    relations.append({"source_id": left, "target_id": right, "relation": column,
                                      "nature": nature, "source": path, "line": line})
    duplicates = {key: paths for key, paths in definitions.items() if len(paths) > 1}
    model = ProjectModel(reader.root, version, manifest, registry, rows, nodes, tuple(model_edges), (), (),
                         tuple(reader.sources), {p: s["sha256"] for p, s in reader.sources.items()})
    return model, records, relations, duplicates


def collect_documents(reader: SourceReader, *, documents: tuple[str, ...] = ()) -> tuple[dict, list[str]]:
    manifest = {}
    index = reader.root / ".lks-sdd/project.json"
    if index.exists() or index.is_symlink():
        source = reader.read(".lks-sdd/project.json", "index")
        if source:
            try:
                value = json.loads(source["text"])
                if not isinstance(value, dict):
                    raise ValueError("Manifest must be an object")
                manifest = value
            except (ValueError, TypeError):
                reader.warnings.append("invalid-manifest-text-only")
    # Inventory discovery is independent of the manifest and is renewed each call.
    inventory = reader.inventory()
    ordered = list(documents)
    entries = manifest.get("artifacts", [])
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                ordered.append(entry["path"])
    ordered += inventory
    reader.read_documents(dict.fromkeys(ordered))
    return manifest, inventory


def document_context(reader: SourceReader, *, topic: str = "", entity: str | None = None,
                     documents: tuple[str, ...] = ()) -> dict:
    manifest, inventory = collect_documents(reader, documents=documents)
    model, records, relations, duplicates = snapshot_model(reader, manifest)
    words = terms(topic)
    selected, reasons = set(), defaultdict(list)
    def include(path, why):
        selected.add(path)
        if why not in reasons[path]:
            reasons[path].append(why)
    for path, source in reader.sources.items():
        if source["kind"] != "document":
            continue
        searchable = normalize(path + "\n" + source["text"]) if words else ""
        if path in documents:
            include(path, "explicit-document")
        if topic.strip() and not words and not entity and not documents:
            include(path, "documentary-overview-candidate")
        if entity and entity in ENTITY.findall(source["text"]):
            include(path, "entity-or-inverse-reference")
        if words and all(word in searchable for word in words):
            include(path, "topic-match-candidate")
    if not selected and words:
        for path, source in reader.sources.items():
            if source["kind"] == "document" and any(w in normalize(path + "\n" + source["text"]) for w in words):
                include(path, "partial-topic-match-candidate")
    selected_ids = {entity} if entity else set()
    if not entity:
        for row in records:
            if row["source"] in selected and (row["source"] in documents or
                    all(w in normalize(" ".join(row["cells"].values())) for w in words)):
                selected_ids.add(row["id"])
    expanded = False
    for _ in range(reader.limits.relation_depth):
        before = set(selected_ids)
        for relation in relations:
            if relation["source_id"] in before or relation["target_id"] in before:
                selected_ids.update((relation["source_id"], relation["target_id"]))
                include(relation["source"], "declared-relation-or-inverse")
        for row in records:
            if row["id"] in selected_ids:
                include(row["source"], "related-entity")
        if selected_ids == before:
            expanded = False
            break
        expanded = True
    if expanded:
        reader.warnings.append("relation-depth-limit")
    frontier = set(selected)
    for _ in range(reader.limits.relation_depth):
        following = set()
        for path in frontier:
            for angled, plain in re.findall(r'\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+)(?:\s+"[^"]*")?)\)', without_fences(reader.sources[path]["text"])):
                target = angled or plain
                target = unquote(target.split("#")[0])
                if not target or ":" in target or target.startswith(("/", "\\")):
                    continue
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
                linked = reader.lookup(resolved)
                if linked and linked["kind"] == "document" and linked["path"] not in selected:
                    following.add(linked["path"])
        for path in following:
            include(path, "explicit-document-link")
        frontier = following
        if not frontier:
            break
    if frontier:
        reader.warnings.append("document-link-depth-limit")
    if selected:
        for path, source in reader.sources.items():
            if source["kind"] == "document" and GLOBAL.search(path):
                include(path, "cross-cutting-rules-candidate")
    fragments, used = [], 0
    roots = {r["source"] for r in records if entity and r["id"] == entity}
    for path in sorted(selected, key=lambda p: (p not in documents, p not in roots, "topic-match-candidate" not in reasons[p], p)):
        source = reader.sources[path]
        text = source["text"]
        if used + len(text) > reader.limits.max_output_chars:
            reader.exclude(path, "output-limit-unread-fragment")
            continue
        used += len(text)
        fragments.append({"source": path, "line": 1, "end_line": max(1, source["line_count"]),
                          "text": text, "nature": "documented", "authority": "mixed-or-unknown",
                          "included_because": reasons[path]})
    emitted = {f["source"] for f in fragments}
    relevant_duplicates = {k: v for k, v in duplicates.items() if k in selected_ids}
    context_id = identity({"topic": topic, "entity": entity, "documents": list(documents),
                           "sources": dict(model.source_hashes),
                           "inventory": inventory, "revision": reader.revision(),
                           "limits": reader.limits.__dict__})
    return {"context_id": context_id, "fragments": fragments,
            "entities": [r for r in records if r["source"] in emitted and (not selected_ids or r["id"] in selected_ids)],
            "relations": [r for r in relations if r["source"] in emitted and
                          (r["source_id"] in selected_ids or r["target_id"] in selected_ids)],
            "duplicates": relevant_duplicates, "inventory": inventory,
            "indexed": bool(manifest), "contract_validation": "not-run",
            "output_chars": used}
