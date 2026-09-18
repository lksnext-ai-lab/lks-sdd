"""Bounded baseline of existing sources; observations are not intended behavior."""
from __future__ import annotations

import uuid

from query_sources import SourceReader
from v2_contract import ContractError, DOCS, canonical, load, make_element, render_document
from v2_authoring import initialize
from v2_storage import apply, preview


def adopt(root, paths, *, name, description, authorized_hash=None):
    if not paths or not description.strip():
        raise ContractError("Bounded adoption needs explicit source paths and purpose")
    existing = load(root) if (root / ".lks-sdd/project.json").exists() else None
    if existing:
        existing.require_valid()
        changes = {".lks-sdd/project.json": canonical(existing.manifest)}
    else:
        _, changes = initialize(root, name or "Sistema existente")
    reader = SourceReader(root)
    observations = []
    for relative in paths:
        kind = "document" if relative.endswith((".md", ".txt", ".rst")) else "code"
        source = reader.read(relative, kind)
        if source is None:
            raise ContractError("Adoption source is unavailable or outside safe bounds: " + relative)
        observations.append(source)
    if reader.revalidate():
        raise ContractError("Sources changed during adoption preview")
    index = __import__("json").loads(changes[".lks-sdd/project.json"])
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, index["project_id"])
    from v2_lifecycle import next_id
    first = next_id(existing, "OBS") if existing else "OBS-001"
    first_number = int(first.split("-")[-1])
    elements = [make_element(first, "legacy", "Baseline acotada del sistema existente", description,
                            uid=str(uuid.uuid5(namespace, first)), state="unknown", nature="fact",
                            scope="unknown", critical=True, sources=[{"path": s["path"], "sha256": s["sha256"]} for s in observations])]
    for i, source in enumerate(observations, first_number + 1):
        identifier = f"OBS-{i:03}"
        elements.append(make_element(identifier, "legacy", source["path"],
            "Observación estática; no acredita intención, aceptación ni ejecución.\n\n```text\n" +
            source["text"].replace("```", "`` `") + "\n```",
            uid=str(uuid.uuid5(namespace, identifier)), state="unknown", nature="fact",
            source_path=source["path"], source_sha256=source["sha256"]))
    relative = DOCS + ("/01-context/adoptions/" + first + ".md" if existing else "/01-context/adopted-baseline.md")
    changes[relative] = render_document("baseline", "Sistema existente: ámbito inspeccionado", elements,
                                       preamble="Cobertura parcial. No se inventan funcionalidades, tareas históricas ni decisiones de negocio.")
    index["artifacts"].append({"path": relative})
    index["route"] = "adopt-existing"
    changes[".lks-sdd/project.json"] = canonical(index) + b"\n"
    sources = {**(existing.hashes if existing else {}), **{s["path"]: s["sha256"] for s in observations}}
    result = preview(root, changes, sources=sources, operation="adopt-bounded-v2")
    return apply(root, changes, result, authorized_hash, validator=lambda: load(root).require_valid()) if authorized_hash else result
