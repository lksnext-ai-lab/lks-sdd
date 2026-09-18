#!/usr/bin/env python3
"""Read-only project context for human-oriented, documentation-first answers."""
from __future__ import annotations

import sys
# Must precede every plugin import, also when the runtime lives in the consumer.
sys.dont_write_bytecode = True

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time

from query_sources import Limits, QueryError, SourceReader, check_query_runtime, redact
from query_context import ENTITY, document_context
from query_code import inspect_code
from query_render import diagram, markdown


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MODES = ("docs-first", "docs-only", "compare")
INTENTS = ("documented", "implementation", "normative", "impact")


def query(root: Path, *, topic: str = "", entity: str | None = None,
          documents: tuple[str, ...] = (), mode: str = "docs-first", intent: str = "documented",
          code_paths: tuple[str, ...] = (), gap: str | None = None,
          context_id: str | None = None, limits: Limits | None = None) -> dict:
    started = time.perf_counter()
    if mode not in MODES or intent not in INTENTS:
        raise QueryError("Modo o intención no admitidos.")
    if not (topic.strip() or entity or documents):
        raise QueryError("Indique un tema, entidad o documento.")
    if entity and not ENTITY.fullmatch(entity):
        raise QueryError("El selector de entidad no es un identificador completo.")
    if mode == "docs-only" and (code_paths or gap or context_id):
        raise QueryError("docs-only no permite ampliar al código.")
    if mode == "docs-first" and (code_paths or gap or context_id):
        if not (code_paths and gap and gap.strip() and context_id and intent in {"implementation", "impact"}):
            raise QueryError("La ampliación requiere carencia concreta, contexto documental vigente, rutas e intención de implementación/impacto.")
    reader = SourceReader(root, limits)
    phase = time.perf_counter()
    check_query_runtime(reader.root, PLUGIN_ROOT)
    reader.metrics["runtime_seconds"] = round(time.perf_counter() - phase, 6)
    revision = reader.revision()
    phase = time.perf_counter()
    context = document_context(reader, topic=topic, entity=entity, documents=documents)
    reader.metrics["document_seconds"] = round(time.perf_counter() - phase, 6)
    if context_id and context_id != context["context_id"]:
        raise QueryError("El contexto documental ha cambiado; vuelva a evaluar la carencia antes de leer código.")
    fragments = context["fragments"]
    dependencies = []
    gaps = ["La suficiencia y las contradicciones deben evaluarse para la pregunta; la recuperación no las certifica."]
    if not fragments:
        gaps.append("No se han localizado fragmentos suficientes. Esto no demuestra que la funcionalidad no exista.")
    if not context["indexed"]:
        gaps.append("Sin índice SDD utilizable: fuentes textuales; no se requiere adopción para consultar.")
    if intent == "normative":
        gaps.append("Una decisión de negocio ausente no puede deducirse de la implementación.")
    if mode == "compare" and not code_paths:
        gaps.append("Delimite las rutas de implementación que desea contrastar.")
    if context["duplicates"]:
        gaps.append("Hay identificadores definidos más de una vez; no se selecciona una definición como autoridad.")
    phase = time.perf_counter()
    if code_paths and not context["duplicates"]:
        extra, dependencies = inspect_code(reader, code_paths, topic,
                                          reader.limits.max_output_chars - context["output_chars"])
        fragments = fragments + extra
        if not extra:
            gaps.append("La inspección acotada no devolvió código pertinente; no prueba ausencia de implementación.")
        gaps.append("Código leído estáticamente: no ejecutado ni contrastado con producción. Dependencias dinámicas/externas no resueltas.")
    reader.metrics["code_seconds"] = round(time.perf_counter() - phase, 6)
    phase = time.perf_counter()
    changed = reader.revalidate()
    inventory_after = reader.inventory()
    if revision != reader.revision() or context["inventory"] != inventory_after:
        changed.append("inventory-or-revision")
    if changed:
        # Never return excerpts or links that combine different snapshots.
        fragments = []
        context["entities"], context["relations"] = [], []
        context["duplicates"] = {}
        context["inventory"] = inventory_after
        dependencies = []
        reader.warnings.append("sources-changed-repeat-query")
        gaps.append("Las fuentes cambiaron durante la consulta; se omiten los fragmentos y se requiere una nueva lectura.")
    reader.metrics["revalidation_seconds"] = round(time.perf_counter() - phase, 6)
    emitted = {f["source"] for f in fragments}
    safe_topic, _ = redact(topic)
    safe_gap, _ = redact(gap or "")
    unselected = [p for p in context["inventory"] if p not in emitted]
    if len(unselected) > reader.limits.max_index_items:
        reader.warnings.append("unselected-document-index-truncated")
    result = {
        "schema_version": "1.0", "kind": "query-context",
        "status": "needs-clarification" if context["duplicates"] or (mode == "compare" and not code_paths) else "partial",
        "request": {"topic": safe_topic, "entity": entity, "documents": list(documents), "mode": mode,
                    "intent": intent, "code_paths": list(code_paths), "gap": safe_gap or None},
        "context_id": context["context_id"], "revision": revision,
        "contract_validation": "not-run", "semantic_review": "required",
        "sources": [{k: v for k, v in s.items() if k != "text"} for p, s in reader.sources.items() if p in emitted],
        "fragments": fragments, "entities": context["entities"], "relations": context["relations"],
        "duplicates": context["duplicates"], "dependency_candidates": dependencies,
        "gaps": gaps, "warnings": sorted(set(reader.warnings)), "exclusions": reader.exclusions,
        "unselected_documents": unselected[:reader.limits.max_index_items],
        "limits": asdict(reader.limits), "metrics": reader.metrics,
        "diagram": None, "writes": [], "consumer_executions": [],
    }
    result["diagram"] = diagram(result)
    result["metrics"]["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--topic", default="")
    parser.add_argument("--entity")
    parser.add_argument("--document", action="append", default=[])
    parser.add_argument("--mode", choices=MODES, default="docs-first")
    parser.add_argument("--intent", choices=INTENTS, default="documented")
    parser.add_argument("--code-path", action="append", default=[])
    parser.add_argument("--gap", help="Carencia documental concreta, evaluada por el asistente")
    parser.add_argument("--context-id", help="Identidad devuelta por la lectura documental previa")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--file-links", action="store_true", help="Enlaces al archivo sin sufijo de línea")
    args = parser.parse_args()
    try:
        result = query(args.project_root, topic=args.topic, entity=args.entity, documents=tuple(args.document),
                       mode=args.mode, intent=args.intent, code_paths=tuple(args.code_path),
                       gap=args.gap, context_id=args.context_id)
    except (QueryError, OSError) as exc:
        result = {"schema_version": "1.0", "kind": "query-context", "status": "blocked",
                  "error": str(exc), "writes": [], "consumer_executions": []}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
          markdown(result, args.project_root, line_links=not args.file_links), end="\n" if args.json else "")
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
