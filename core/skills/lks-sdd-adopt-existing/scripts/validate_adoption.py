#!/usr/bin/env python3
"""Validate adoption evidence, reconciliation, authorization, and baseline freshness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from adoption_common import (
    DECISION_KIND,
    REPORT_KIND,
    REPORT_VERSION,
    AdoptionError,
    compare_baseline,
    load_json_object,
    safe_root,
    sha256_file,
)

STRATEGIES = {"documentation", "progressive-normalization", "planned-modernization"}
WRITE_SCOPE = {".lks-sdd/", "docs/lks-sdd/"}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(
    project_root: Path, report_path: Path, decision_path: Path
) -> tuple[int, dict[str, Any]]:
    root = safe_root(project_root)
    report_file = report_path.expanduser().resolve()
    decision_file = decision_path.expanduser().resolve()
    report = load_json_object(report_file, "el informe de inventario")
    decision = load_json_object(decision_file, "la decisión de adopción")
    blockers: list[str] = []
    warnings: list[str] = []

    if (
        report.get("kind") != REPORT_KIND
        or report.get("contract_version") != REPORT_VERSION
    ):
        blockers.append("El informe no usa el contrato de inventario soportado.")
    preflight = report.get("preflight")
    if not isinstance(preflight, dict):
        blockers.append("El informe no contiene un preflight válido.")
        preflight = {}
    recorded_root = preflight.get("root")
    try:
        same_root = Path(str(recorded_root)).resolve() == root
    except OSError:
        same_root = False
    if not same_root:
        blockers.append(
            "La raíz actual no coincide con la raíz confirmada en el preflight."
        )
    if preflight.get("permissions") != "read-only":
        blockers.append("El preflight no acredita permisos de solo lectura.")
    proof = report.get("read_only_proof")
    if not isinstance(proof, dict):
        blockers.append("El informe no contiene una prueba de solo lectura válida.")
        proof = {}
    if proof.get("unchanged") is not True or proof.get("before") != proof.get("after"):
        blockers.append(
            "La inspección no demuestra un estado idéntico antes y después."
        )
    coverage = report.get("coverage")
    if not isinstance(coverage, dict):
        blockers.append("El informe no contiene una cobertura válida.")
        coverage = {}
    if (
        type(coverage.get("files_inventoried")) is not int
        or coverage.get("files_inventoried", 0) < 1
    ):
        blockers.append("El inventario no contiene archivos dentro del alcance.")
    if (
        type(coverage.get("sensitive_files_excluded")) is not int
        or coverage.get("sensitive_files_excluded", -1) < 0
        or type(coverage.get("truncated")) is not bool
    ):
        blockers.append("La cobertura del inventario está incompleta.")
    inventory = report.get("inventory")
    if not isinstance(inventory, dict) or not all(
        isinstance(inventory.get(field), list)
        for field in (
            "files",
            "sensitive_indicators",
            "symlinks_excluded",
            "submodules_excluded",
            "manifest_paths",
            "source_extensions",
        )
    ):
        blockers.append("El informe no contiene un inventario válido.")
    limitations = report.get("limitations")
    if not isinstance(limitations, list) or not all(
        _non_empty_string(item) for item in limitations
    ):
        blockers.append("El informe no declara limitaciones válidas.")

    report_hash = sha256_file(report_file)
    if (
        decision.get("kind") != DECISION_KIND
        or decision.get("contract_version") != REPORT_VERSION
    ):
        blockers.append("La decisión no usa el contrato de adopción soportado.")
    if decision.get("report_sha256") != report_hash:
        blockers.append(
            "La decisión no confirma exactamente este informe de inventario."
        )
    if decision.get("scope_confirmed") is not True:
        blockers.append("El alcance y sus exclusiones no están confirmados.")
    if decision.get("coverage_confirmed") is not True:
        blockers.append("La cobertura y sus limitaciones no están confirmadas.")
    write_scope = decision.get("write_scope")
    if (
        not isinstance(write_scope, list)
        or len(write_scope) != len(WRITE_SCOPE)
        or not all(isinstance(item, str) for item in write_scope)
        or set(write_scope) != WRITE_SCOPE
    ):
        blockers.append(
            "El alcance de escritura debe limitarse a .lks-sdd/ y docs/lks-sdd/."
        )
    if decision.get("strategy") not in STRATEGIES:
        blockers.append("La estrategia de adopción no pertenece al catálogo permitido.")
    intent = decision.get("confirmed_intent")
    if not isinstance(intent, dict):
        blockers.append("La decisión no contiene una intención confirmada válida.")
        intent = {}
    if not all(
        _non_empty_string(intent.get(field))
        for field in ("purpose", "desired_behavior")
    ):
        blockers.append("Faltan propósito o comportamiento deseado confirmados.")
    priorities = intent.get("priorities")
    if (
        not isinstance(priorities, list)
        or not priorities
        or not all(_non_empty_string(item) for item in priorities)
    ):
        blockers.append("Debe existir al menos una prioridad confirmada.")

    reconciliation = decision.get("reconciliation")
    if not isinstance(reconciliation, dict):
        blockers.append("La decisión no contiene una reconciliación válida.")
        reconciliation = {}
    contradictions = reconciliation.get("contradictions", [])
    unknowns = reconciliation.get("unknowns", [])
    matches = reconciliation.get("matches", [])
    if not isinstance(matches, list) or not all(
        _non_empty_string(item) for item in matches
    ):
        blockers.append("Las coincidencias de reconciliación deben ser una lista.")
    if not isinstance(contradictions, list) or not isinstance(unknowns, list):
        blockers.append(
            "La reconciliación debe declarar listas de contradicciones y desconocidos."
        )
    else:
        for index, item in enumerate(contradictions, 1):
            if not isinstance(item, dict) or not _non_empty_string(
                item.get("statement")
            ):
                blockers.append(f"Contradicción {index} incompleta.")
                continue
            if item.get("state") not in {
                "resolved",
                "deferred",
            } or not _non_empty_string(item.get("resolution")):
                blockers.append(
                    f"Contradicción {index} sin resolución o aplazamiento explícito."
                )
            if item.get("blocking") is True:
                blockers.append(
                    f"Contradicción {index} continúa bloqueando la materialización."
                )
        for index, item in enumerate(unknowns, 1):
            if not isinstance(item, dict) or not _non_empty_string(
                item.get("statement")
            ):
                blockers.append(f"Desconocido {index} incompleto.")
                continue
            if item.get("blocking") is True:
                blockers.append(
                    f"Desconocido {index} continúa bloqueando la materialización."
                )
    authorization = decision.get("authorization")
    if not isinstance(authorization, dict):
        blockers.append("La decisión no contiene una autorización válida.")
        authorization = {}
    if authorization.get("materialize") is not True:
        blockers.append("La decisión no autoriza la materialización documental.")
    try:
        date.fromisoformat(str(authorization.get("confirmed_at")))
    except ValueError:
        blockers.append(
            "La autorización debe registrar confirmed_at en formato AAAA-MM-DD."
        )
    if not _non_empty_string(authorization.get("confirmation_reference")):
        blockers.append(
            "La autorización requiere una referencia de confirmación trazable."
        )

    baseline_matches = False
    current: dict[str, Any] = {}
    try:
        baseline_matches, current = compare_baseline(root, report)
    except AdoptionError as exc:
        blockers.append(str(exc))
    if not baseline_matches:
        blockers.append(
            "La baseline está stale: cambió la revisión, el estado Git o el sistema de archivos inventariado."
        )
    if coverage.get("truncated") is True:
        warnings.append(
            "La baseline confirmada tiene cobertura parcial por límite de archivos."
        )

    blockers = list(dict.fromkeys(blockers))
    status = (
        "ready-for-materialization"
        if not blockers
        else "stale"
        if not baseline_matches
        else "blocked"
    )
    return (0 if not blockers else 3), {
        "status": status,
        "baseline_freshness": "current" if baseline_matches else "stale",
        "report_sha256": report_hash,
        "decision_sha256": sha256_file(decision_file),
        "strategy": decision.get("strategy"),
        "blockers": blockers,
        "warnings": warnings,
        "current_baseline": current,
        "changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        code, result = validate(args.project_root, args.report, args.decision)
    except AdoptionError as exc:
        code, result = 2, {"status": "error", "changed": False, "error": str(exc)}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        for blocker in result.get("blockers", []):
            print(f"BLOCKER: {blocker}")
    return code


if __name__ == "__main__":
    sys.exit(main())
