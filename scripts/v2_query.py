"""Read-only projection of v2 snapshots and a source-linked human fallback."""
from __future__ import annotations

from collections import defaultdict
import html
import re

from contract_engine import ProjectModel
from v2_contract import ContractError, parse_document, metadata


def snapshot_records(reader, manifest):
    from v2_storage import ensure_idle
    ensure_idle(reader.root)
    records, relations, definitions = [], [], defaultdict(list)
    for path, source in reader.sources.items():
        if source["kind"] != "document" or str(metadata(source["text"]).get("schema_version")) != "2.0":
            continue
        try:
            elements, _ = parse_document(source["text"], path)
        except ContractError:
            reader.exclude(path, "invalid-v2-document-text-preserved")
            continue
        for e in elements:
            definitions[e.id].append(f"{path}:{e.line}")
            records.append({"id": e.id, "source": path, "line": e.line,
                            "cells": {"Título": e.meta["title"], "Contenido": e.body},
                            "declared_state": e.meta["state"], "nature": e.meta["nature"],
                            "authority": "declared-not-validated", "typed": True,
                            "contract_version": "2.0", "element_kind": e.kind})
            for relation, targets in e.relations.items():
                for target in targets:
                    if len(relations) >= reader.limits.max_relations:
                        reader.exclude(path, "relation-count-limit")
                        break
                    relations.append({"source_id": e.id, "target_id": target, "relation": relation,
                                      "nature": "declared", "source": path, "line": e.line})
    model = ProjectModel(reader.root, "2.0", manifest, None, {}, {}, (), (), (),
                         tuple(reader.sources), {p: s["sha256"] for p, s in reader.sources.items()})
    return model, records, relations, {k: v for k, v in definitions.items() if len(v) > 1}


def prose(text):
    # Untrusted HTML never renders; no raw metadata, scripts, image loads or commands.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r'<a\s+id=[^>]+></a>', "", text)
    text = re.sub(r"^#{1,6}\s+[^\n]*\n", "", text, count=1, flags=re.M)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"[Material visual: \1; consultar fuente]", text)
    text = re.sub(r"<[^>]+>", lambda m: html.escape(m[0]), text)
    return text.strip()


def human_markdown(result, root, *, line_links=True):
    from query_render import source_link, label
    title = result["request"].get("topic") or result["request"].get("entity") or "Proyecto"
    lines = ["## " + label(title), "", "Síntesis documental. Los estados citados no acreditan despliegue ni aceptación por sí solos.", ""]
    groups = [("Funcionalidad y alcance", {"feature", "group", "increment", "project"}),
              ("Requisitos y criterios de aceptación", {"requirement", "acceptance", "rule", "constraint"}),
              ("Decisiones e información relacionada", {"decision", "interface", "binding", "environment", "change", "applicability", "legacy"})]
    rows = result["entities"]
    emitted = set()
    for heading, kinds in groups:
        selected = [r for r in rows if r.get("element_kind") in kinds]
        if not selected:
            continue
        lines += ["### " + heading, ""]
        for row in selected:
            emitted.add(row["source"])
            lines += ["**" + label(row["id"] + " · " + row["cells"]["Título"]) + "**",
                      "", prose(row["cells"]["Contenido"]), "",
                      "Estado documentado: " + label(row["declared_state"]) + ". Naturaleza: " + label(row["nature"]) + ". " +
                      source_link(root, row["source"], row["line"], line_links=line_links), ""]
    tasks = [r for r in rows if r.get("element_kind") == "task"]
    if tasks:
        lines += ["### Tareas involucradas", "", "| Tarea | Estado documentado | Fuente |", "|---|---|---|"]
        for task in tasks:
            emitted.add(task["source"])
            lines.append("| " + label(task["id"] + " · " + task["cells"]["Título"]) + " | " + label(task["declared_state"]) + " | " + source_link(root, task["source"], task["line"], line_links=line_links) + " |")
        lines.append("")
    other = [r for r in rows if r.get("element_kind") in {"test", "plan", "release", "execution", "checkpoint", "authorization", "problem"}]
    if other:
        lines += ["### Planificación, pruebas y seguimiento", ""]
        for row in other:
            emitted.add(row["source"])
            lines.append("- " + label(row["id"] + " · " + row["cells"]["Título"]) + " (" + label(row["declared_state"]) + "): " + source_link(root, row["source"], row["line"], line_links=line_links))
        lines.append("")
    # Do not silently drop document preambles/exceptions from the human response.
    notes = []
    for fragment in result["fragments"]:
        if fragment["nature"] != "documented":
            continue
        text = fragment["text"]
        if str(metadata(text).get("schema_version")) == "2.0":
            try:
                _, outside = parse_document(text, fragment["source"])
                outside = re.sub(r"\A---\n.*?\n---\n", "", outside, flags=re.S)
                outside = prose(outside)
            except ContractError:
                outside = "Formato no interpretado; consulte la fuente para revisar sus obligaciones."
        else:
            outside = prose(text)
        if outside:
            notes.append((outside, fragment))
    if notes:
        lines += ["### Notas documentadas y límites de interpretación", ""]
        for note, fragment in notes:
            lines += [note, "", source_link(root, fragment["source"], fragment["line"], line_links=line_links), ""]
    code = [f for f in result["fragments"] if f["nature"] != "documented"]
    if code:
        lines += ["### Observación estática de implementación", "", "El código no sustituye una decisión de negocio ni demuestra ejecución real.", ""]
        for fragment in code:
            lines += [source_link(root, fragment["source"], fragment["line"], line_links=line_links), ""]
    if result["relations"]:
        lines += ["### Relaciones relevantes", ""]
        for relation in result["relations"]:
            lines.append("- " + label(f'{relation["source_id"]} → {relation["target_id"]}: {relation["relation"]}') + ". " + source_link(root, relation["source"], relation["line"], line_links=line_links))
        lines.append("")
    if result.get("diagram"):
        lines += ["```mermaid", result["diagram"], "```", ""]
    if result["gaps"] or result["warnings"]:
        lines += ["### Pendientes y alcance de la consulta", ""]
        lines += ["- " + label(s) for s in result["gaps"] + result["warnings"]]
    return "\n".join(lines).rstrip() + "\n"
