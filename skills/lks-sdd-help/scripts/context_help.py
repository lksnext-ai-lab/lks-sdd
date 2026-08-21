#!/usr/bin/env python3
"""Read an LKS-SDD project and explain its state without modifying it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_project import (  # noqa: E402
    parse_frontmatter,
    parse_markdown_table_blocks,
    validate_project,
)
from check_traceability import check as check_traceability  # noqa: E402


COVERAGE_HEADERS = (
    "Dimensión",
    "Estado",
    "Alcance",
    "Información disponible",
    "Falta profundizar",
    "Impacto",
)
STATUS_HEADERS = (
    "Ruta",
    "Fase",
    "Puerta",
    "Incremento activo",
    "Readiness",
    "Próximo paso",
)


def _option(action: str, effect: str) -> dict[str, Any]:
    return {"action": action, "effect": effect, "starts_action": False}


def _diagnostic_summary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for item in items:
        code = str(item.get("code", "LKS-UNKNOWN"))
        severity = str(item.get("severity", "error"))
        key = (severity, code)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"code": code, "severity": severity, "count": count}
        for (severity, code), count in sorted(counts.items())
    ]


def _base_response(root: Path, status: str, meaning: str) -> dict[str, Any]:
    return {
        "status": status,
        "project_root": str(root),
        "where": {"route": None, "phase": None, "gate": None},
        "meaning": meaning,
        "structural_validity": {
            "status": "not-assessed",
            "mode": "not-assessed",
            "checked_files": 0,
            "warnings": [],
            "diagnostic_summary": [],
            "meaning": "La validez estructural todavía no se ha evaluado.",
        },
        "definition_coverage": {
            "available": False,
            "source": "none",
            "items": [],
            "sufficient": [],
            "needs_depth": [],
            "unknown": [],
            "not_applicable": [],
            "invalid": [],
            "fallback_reason": "No hay una cobertura cualitativa disponible.",
        },
        "readiness_snapshot": {
            "status": "not-assessed",
            "source": "none",
            "revalidated": False,
            "meaning": "No hay un snapshot de readiness disponible.",
        },
        "readiness_preflight": {
            "status": "not-run",
            "increment": None,
            "gaps": [],
            "diagnostics": [],
            "meaning": "No hay un incremento activo sobre el que ejecutar el preflight.",
        },
        "blockers": [],
        "next_decision": None,
        "resolved": [],
        "missing_or_limits": [],
        "options": [],
        "choice_prompt": "¿Qué opción quieres explorar? No se iniciará ninguna sin tu elección explícita.",
        "action_started": False,
    }


def _coverage_state(value: str) -> tuple[str, str | None]:
    normalized = value.strip()
    if normalized in {"unknown", "partial", "sufficient"}:
        return normalized, None
    prefix = "not-applicable:"
    if normalized.startswith(prefix) and normalized[len(prefix) :].strip():
        return "not-applicable", normalized[len(prefix) :].strip()
    return "invalid", None


def _read_definition_status(
    root: Path, manifest: dict[str, Any]
) -> tuple[dict[str, Any], str | None]:
    coverage: dict[str, Any] = {
        "available": False,
        "source": "legacy-fallback",
        "items": [],
        "sufficient": [],
        "needs_depth": [],
        "unknown": [],
        "not_applicable": [],
        "invalid": [],
        "fallback_reason": (
            "ART-STATUS no contiene la tabla cualitativa; la validez estructural "
            "no permite inferir suficiencia semántica."
        ),
    }
    status_entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if isinstance(item, dict) and item.get("id") == "ART-STATUS"
        ),
        None,
    )
    if status_entry is None or not isinstance(status_entry.get("path"), str):
        return coverage, None

    status_path = root / status_entry["path"]
    try:
        text = status_path.read_text(encoding="utf-8")
        _, body = parse_frontmatter(text)
    except (OSError, UnicodeError, ValueError) as exc:
        coverage["fallback_reason"] = f"No se pudo leer ART-STATUS: {exc}"
        return coverage, None

    next_decision: str | None = None
    coverage_rows: list[dict[str, str]] | None = None
    for headers, rows in parse_markdown_table_blocks(body):
        if headers == STATUS_HEADERS and rows:
            next_decision = rows[0].get("Próximo paso", "").strip() or None
        if headers == COVERAGE_HEADERS:
            coverage_rows = rows

    if coverage_rows is None:
        return coverage, next_decision

    coverage["available"] = True
    coverage["source"] = "ART-STATUS"
    coverage["fallback_reason"] = None
    for row in coverage_rows:
        dimension = row.get("Dimensión", "").strip()
        state_value = row.get("Estado", "").strip()
        state, reason = _coverage_state(state_value)
        item = {
            "dimension": dimension,
            "state": state_value,
            "scope": row.get("Alcance", "").strip(),
            "information": row.get("Información disponible", "").strip(),
            "missing": row.get("Falta profundizar", "").strip(),
            "impact": row.get("Impacto", "").strip(),
        }
        coverage["items"].append(item)
        if not dimension or state == "invalid":
            coverage["invalid"].append(
                dimension or "Dimensión sin nombre"
            )
        elif state == "sufficient":
            coverage["sufficient"].append(dimension)
        elif state == "partial":
            coverage["needs_depth"].append(dimension)
        elif state == "unknown":
            coverage["unknown"].append(dimension)
        else:
            coverage["not_applicable"].append(
                f"{dimension}: {reason}"
            )
    return coverage, next_decision


def load_state(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    manifest_path = root / ".lks-sdd" / "project.json"
    if not manifest_path.is_file():
        response = _base_response(
            root,
            "not-initialized",
            "No existe un índice operativo LKS-SDD en esta raíz.",
        )
        response["missing_or_limits"] = [
            "No se puede determinar una fase, puerta o baseline LKS-SDD.",
            "La presencia de código debe comprobarse antes de elegir la ruta new.",
        ]
        response["options"] = [
            _option("Aprender el método", "Solo explica LKS-SDD; no crea archivos."),
            _option(
                "Definir una aplicación nueva",
                "Requiere confirmar que no existe una aplicación previa y autorizar la inicialización.",
            ),
            _option(
                "Preparar una adopción segura",
                "Permite iniciar el preflight estático de solo lectura con la skill de adopción; no materializa sin una autorización posterior.",
            ),
        ]
        return response

    report, manifest, definitions = validate_project(root)
    if manifest is None or not report.valid:
        response = _base_response(
            root,
            "invalid-project",
            "El estado no puede interpretarse con confianza porque el contrato LKS-SDD es inválido.",
        )
        response["missing_or_limits"] = report.errors or ["No se pudo leer el índice operativo."]
        response["structural_validity"] = {
            "status": "invalid",
            "mode": "compatibility" if manifest and manifest.get("schema_version") == "1.0" else "strict",
            "checked_files": len(report.checked_files),
            "warnings": list(dict.fromkeys(report.warnings)),
            "diagnostic_summary": _diagnostic_summary(report.diagnostics),
            "meaning": "El contrato estructural contiene errores; no se evalúa suficiencia semántica.",
        }
        response["options"] = [
            _option(
                "Revisar el contrato",
                "Explica los errores detectados sin corregir ni modificar el proyecto.",
            )
        ]
        return response

    route = manifest.get("route")
    phase = manifest.get("phase")
    gate = manifest.get("gate")
    persisted_readiness = manifest.get("readiness")
    readiness = (
        persisted_readiness.get("status", "not-assessed")
        if isinstance(persisted_readiness, dict)
        else "not-persisted"
    )
    active_increment = manifest.get("active_increment")
    schema_version = str(manifest.get("schema_version", ""))
    compatibility_mode = schema_version in {"1.0", "1.1"}
    definition_coverage, next_decision = _read_definition_status(root, manifest)
    response = _base_response(
        root,
        "context-available",
        "Los Markdown versionados son la fuente de verdad. La validez estructural y la suficiencia semántica se muestran por separado.",
    )
    response.update(
        {
            "project_id": manifest.get("project_id"),
            "where": {
                "route": route,
                "phase": phase,
                "gate": gate,
                "baseline_id": manifest.get("baseline_id"),
                "active_increment": active_increment,
                "active_plan": manifest.get("active_plan"),
                "active_task": manifest.get("active_task"),
                "delivery_model": manifest.get("delivery_governance", {}).get(
                    "model"
                ),
                "readiness": readiness,
            },
            "structural_validity": {
                "status": "valid",
                "mode": "compatibility" if compatibility_mode else "strict",
                "checked_files": max(len(report.checked_files) - 1, 0),
                "warnings": list(dict.fromkeys(report.warnings)),
                "diagnostic_summary": _diagnostic_summary(report.diagnostics),
                "meaning": (
                    f"El índice y los Markdown son válidos en compatibilidad {schema_version}; los avisos señalan diferencias con el contrato activo 1.2 y esto no demuestra suficiencia semántica."
                    if compatibility_mode
                    else "El índice y los Markdown cumplen el contrato estructural estricto; esto no demuestra que la definición sea suficiente."
                ),
            },
            "definition_coverage": definition_coverage,
            "readiness_snapshot": {
                "status": readiness,
                "source": (
                    ".lks-sdd/project.json"
                    if isinstance(persisted_readiness, dict)
                    else "derived-on-demand"
                ),
                "revalidated": False,
                "meaning": (
                    "Es un dato legado no revalidado; no actúa como puerta."
                    if isinstance(persisted_readiness, dict)
                    else "Los contratos 1.1 y 1.2 no persisten readiness: la puerta se calcula sobre los Markdown activos cuando se solicita."
                ),
            },
            "next_decision": next_decision,
            "resolved": [
                f"La ruta registrada es {route} y la baseline es {manifest.get('baseline_id')}.",
                f"La fase indexada es {phase} y la puerta indexada es {gate}.",
                (
                    f"Snapshot legado de readiness no revalidado: {readiness}."
                    if isinstance(persisted_readiness, dict)
                    else "Readiness no se persiste; se calcula bajo demanda."
                ),
            ],
        }
    )

    missing: list[str] = []
    blocking: list[str] = []
    active_blocking_ids: set[str] = set()
    blocker_ids = manifest.get("open_blockers", [])
    for blocker_id, row in definitions.items():
        if not blocker_id.startswith("OPEN-"):
            continue
        is_active = row.get("State") in {"open", "blocked"}
        is_blocking = (
            blocker_id in blocker_ids
            or row.get("Blocking", "").strip().casefold() == "true"
        )
        if not is_active or not is_blocking:
            continue
        detail = row.get("Question") or row.get("Impact") or "bloqueo sin detalle"
        blocker = f"{blocker_id}: {detail}"
        active_blocking_ids.add(blocker_id)
        blocking.append(blocker)
        missing.append(blocker)
    for item_id, row in definitions.items():
        if not item_id.startswith("OPEN-") or item_id in active_blocking_ids:
            continue
        if row.get("State") in {"open", "blocked"}:
            detail = row.get("Question") or row.get("Impact") or "pendiente sin detalle"
            missing.append(f"Pendiente no bloqueante {item_id}: {detail}")
    if active_increment is None:
        missing.append("No hay un incremento activo indexado.")
    if not manifest.get("technology", {}).get("preferred_stack_assessed", False):
        missing.append("Todavía no se ha evaluado el encaje de la pila preferente.")
    if not definition_coverage["available"]:
        missing.append(definition_coverage["fallback_reason"])
    elif definition_coverage["invalid"]:
        missing.append(
            "ART-STATUS contiene estados de cobertura no reconocidos en: "
            + ", ".join(definition_coverage["invalid"])
        )
    missing.extend(
        f"Aviso estructural: {warning}"
        for warning in dict.fromkeys(report.warnings)
    )
    response["blockers"] = blocking
    if response["next_decision"] is None:
        if blocking:
            response["next_decision"] = blocking[0]
        elif definition_coverage["needs_depth"]:
            response["next_decision"] = (
                "Profundizar " + definition_coverage["needs_depth"][0]
            )
        elif definition_coverage["unknown"]:
            response["next_decision"] = (
                "Aclarar " + definition_coverage["unknown"][0]
            )
    response["missing_or_limits"] = missing or ["No hay bloqueos ni límites estructurales indexados."]

    if active_increment:
        preflight_code, preflight = check_traceability(
            root, active_increment, "preimplementation"
        )
        response["readiness_preflight"] = {
            "status": "clear" if preflight_code == 0 else "incomplete",
            "increment": active_increment,
            "gaps": preflight.get("gaps", []),
            "diagnostics": preflight.get("diagnostics", []),
            "meaning": (
                "La cadena estructural previa a implementación está completa; esto no equivale a readiness ni autoriza implementar."
                if preflight_code == 0
                else "El preflight estructural detecta vacíos antes de ejecutar la evaluación completa de readiness."
            ),
        }

    options = [
        _option(
            "Continuar la definición",
            "Permite resolver puntos abiertos; cualquier edición requiere una petición operativa separada.",
        )
    ]
    if active_increment:
        options.append(
            _option(
                f"Evaluar readiness de {active_increment}",
                "Realiza una evaluación de solo lectura y no autoriza implementación.",
            )
        )
    if route == "adopt-existing" and manifest.get("adoption", {}).get("status") != "materialized":
        options = [
            _option("Mantener el repositorio sin cambios", "Conserva el estado actual y no inicia adopción."),
            _option(
                "Preparar el preflight de adopción",
                "Permite iniciar la inspección estática de solo lectura; la materialización requiere reconciliación, preview y autorización posterior.",
            ),
        ]
    options.append(_option("Seguir aprendiendo", "Amplía la explicación sin cambiar estado ni archivos."))
    response["options"] = options
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    state = load_state(args.project_root)
    if args.as_json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        where = state["where"]
        location = state["status"]
        if where.get("route"):
            location = (
                f"ruta={where['route']}, fase={where['phase']}, puerta={where['gate']}, "
                f"incremento={where.get('active_increment') or 'alcance de proyecto'}, "
                f"readiness_snapshot={where.get('readiness', 'not-assessed')}"
            )
        print(f"Dónde estás: {location}")
        print(f"Qué significa: {state['meaning']}")
        structural = state["structural_validity"]
        print(
            f"Validez estructural: {structural['status']}. "
            f"{structural['meaning']}"
        )
        coverage = state["definition_coverage"]
        print(
            "Estado de la definición: "
            f"fase={where.get('phase') or 'no determinada'}, "
            f"alcance={where.get('active_increment') or state.get('project_id') or 'proyecto'}"
        )
        if coverage["available"]:
            groups = (
                ("✓ sufficient — suficiente para avanzar", coverage["sufficient"]),
                ("△ partial — requiere profundización", coverage["needs_depth"]),
                ("○ unknown — aún desconocido", coverage["unknown"]),
                ("— not-applicable — no aplicable", coverage["not_applicable"]),
            )
            for label, values in groups:
                print(f"- {label}: {', '.join(values) if values else 'ninguno'}")
            if coverage["invalid"]:
                print(f"- Estados no reconocidos: {', '.join(coverage['invalid'])}")
        else:
            print(f"- Cobertura no disponible: {coverage['fallback_reason']}")
        print("⛔ blocked — bloqueos:")
        for item in state["blockers"] or ["No hay bloqueos indexados."]:
            print(f"- {item}")
        print(
            "→ Siguiente decisión: "
            + (state["next_decision"] or "No hay una siguiente decisión documentada.")
        )
        readiness_snapshot = state["readiness_snapshot"]
        print(
            "Snapshot de readiness: "
            f"{readiness_snapshot['status']}. "
            f"{readiness_snapshot['meaning']}"
        )
        preflight = state["readiness_preflight"]
        print(
            "Preflight estructural: "
            f"{preflight['status']}. {preflight['meaning']}"
        )
        for item in preflight["gaps"][:5]:
            print(f"- {item}")
        print("Puedes pedir el detalle completo por dimensión.")
        print("Qué está resuelto:")
        for item in state["resolved"] or ["No hay elementos confirmados por esta lectura."]:
            print(f"- {item}")
        print("Qué falta o limita:")
        for item in state["missing_or_limits"]:
            print(f"- {item}")
        print("Qué opciones tienes:")
        for option in state["options"]:
            print(f"- {option['action']}")
        print("Qué ocurriría con cada opción:")
        for option in state["options"]:
            print(f"- {option['action']}: {option['effect']}")
        print(f"Pregunta de elección: {state['choice_prompt']}")
        print("No se ha iniciado ninguna acción ni se ha modificado el proyecto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
