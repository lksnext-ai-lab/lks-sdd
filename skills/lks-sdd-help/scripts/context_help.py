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

from validate_project import validate_project  # noqa: E402


def _option(action: str, effect: str) -> dict[str, Any]:
    return {"action": action, "effect": effect, "starts_action": False}


def _base_response(root: Path, status: str, meaning: str) -> dict[str, Any]:
    return {
        "status": status,
        "project_root": str(root),
        "where": {"route": None, "phase": None, "gate": None},
        "meaning": meaning,
        "resolved": [],
        "missing_or_limits": [],
        "options": [],
        "choice_prompt": "¿Qué opción quieres explorar? No se iniciará ninguna sin tu elección explícita.",
        "action_started": False,
    }


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
    readiness = manifest.get("readiness", {}).get("status", "not-assessed")
    active_increment = manifest.get("active_increment")
    response = _base_response(
        root,
        "context-available",
        "Los Markdown versionados son la fuente de verdad; project.json solo indexa su estado operativo.",
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
                "readiness": readiness,
            },
            "resolved": [
                f"El índice y {len(report.checked_files) - 1} artefactos Markdown superan la validación estructural.",
                f"La ruta registrada es {route} y la baseline es {manifest.get('baseline_id')}.",
            ],
        }
    )

    missing: list[str] = []
    blocker_ids = manifest.get("open_blockers", [])
    for blocker_id in blocker_ids:
        row = definitions.get(blocker_id, {})
        detail = row.get("Question") or row.get("Impact") or "bloqueo sin detalle"
        missing.append(f"{blocker_id}: {detail}")
    for item_id, row in definitions.items():
        if not item_id.startswith("OPEN-") or item_id in blocker_ids:
            continue
        if row.get("State") in {"open", "blocked"}:
            detail = row.get("Question") or row.get("Impact") or "pendiente sin detalle"
            missing.append(f"Pendiente no bloqueante {item_id}: {detail}")
    if active_increment is None:
        missing.append("No hay un incremento activo indexado.")
    if not manifest.get("technology", {}).get("preferred_stack_assessed", False):
        missing.append("Todavía no se ha evaluado el encaje de la pila preferente.")
    response["missing_or_limits"] = missing or ["No hay bloqueos ni límites estructurales indexados."]

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
                f"readiness={where.get('readiness', 'not-assessed')}"
            )
        print(f"Dónde estás: {location}")
        print(f"Qué significa: {state['meaning']}")
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
