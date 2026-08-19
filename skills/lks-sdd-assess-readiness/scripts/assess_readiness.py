#!/usr/bin/env python3
"""Deterministically assess one LKS-SDD increment without modifying the project."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_project import ID_RE, parse_frontmatter, parse_markdown_tables, validate_project  # noqa: E402


def _ids(value: str, prefixes: set[str] | None = None) -> list[str]:
    found = ID_RE.findall(value or "")
    if prefixes is None:
        return found
    return [item for item in found if item.split("-", 1)[0] in prefixes]


def _empty(value: str) -> bool:
    return not value.strip() or value.strip().lower() in {"none", "unknown", "open", "n/a"}


def _domain_references(
    result: dict[str, Any],
    increment: dict[str, str],
    definitions: dict[str, dict[str, str]],
    column: str,
    label: str,
    prefixes: set[str],
) -> None:
    raw = increment.get(column, "").strip()
    if _empty(raw):
        result["blockers"].append(f"El incremento no define la aplicabilidad de {label}.")
        return
    if raw.lower().startswith("not-applicable"):
        _, separator, reason = raw.partition(":")
        if not separator or not reason.strip():
            result["blockers"].append(f"La no aplicabilidad de {label} requiere un motivo.")
        return
    item_ids = _ids(raw, prefixes)
    if not item_ids:
        result["blockers"].append(f"{label} debe enlazar IDs válidos o justificar not-applicable.")
        return
    for item_id in item_ids:
        item = definitions.get(item_id)
        if item is None:
            result["blockers"].append(f"Referencia de {label} sin definición: {item_id}.")
        elif item.get("State") not in {"confirmed", "decision"}:
            result["blockers"].append(
                f"{item_id} afecta a {label} pero no está confirmado; estado: {item.get('State', 'absent')}."
            )


def _load_artifact_body(root: Path, manifest: dict[str, Any], artifact_id: str) -> str:
    entry = next((item for item in manifest["artifacts"] if item.get("id") == artifact_id), None)
    if not entry:
        return ""
    text = (root / entry["path"]).read_text(encoding="utf-8")
    _, body = parse_frontmatter(text)
    return body


def _rows(body: str) -> list[dict[str, str]]:
    return [row for table in parse_markdown_tables(body) for row in table]


def assess(project_root: Path, increment_id: str) -> tuple[int, dict[str, Any]]:
    root = project_root.expanduser().resolve()
    report, manifest, definitions = validate_project(root)
    result: dict[str, Any] = {
        "increment": increment_id,
        "status": "blocked",
        "scope": increment_id,
        "blockers": [],
        "non_blocking_pending": [],
        "evidence_checked": list(report.checked_files),
        "limitations": [
            "La validación determinista no sustituye la revisión semántica de claridad, riesgo y suficiencia.",
            "Este resultado no autoriza implementación."
        ],
        "implementation_authorized": False,
    }
    if not re.fullmatch(r"INC-[0-9]{3}", increment_id):
        result["blockers"].append("El identificador debe usar el formato INC-###.")
        return 2, result
    if not report.valid or manifest is None:
        result["blockers"].extend(f"Contrato inválido: {error}" for error in report.errors)
        return 2, result

    increment = definitions.get(increment_id)
    if increment is None or increment.get("path", "").endswith("increments.md") is False:
        result["blockers"].append(f"El incremento {increment_id} no está definido en ART-INCREMENTS.")
        return 3, result
    if increment.get("State") != "confirmed":
        result["blockers"].append(f"{increment_id} debe estar confirmed; estado actual: {increment.get('State', 'absent')}.")
    if _empty(increment.get("In scope", "")):
        result["blockers"].append(f"{increment_id} no declara alcance incluido.")
    if _empty(increment.get("Out of scope", "")):
        result["blockers"].append(f"{increment_id} no declara alcance excluido.")

    requirement_ids = _ids(increment.get("Requirements", ""), {"FR", "NFR", "TR"})
    acceptance_ids = _ids(increment.get("Acceptance", ""), {"AC"})
    decisions_raw = increment.get("Decisions", "").strip()
    decision_ids = _ids(decisions_raw, {"ADR"})
    test_ids = _ids(increment.get("Tests", ""), {"TEST"})
    if not requirement_ids:
        result["blockers"].append(f"{increment_id} no enlaza requisitos.")
    if not acceptance_ids:
        result["blockers"].append(f"{increment_id} no enlaza criterios de aceptación.")
    if not decision_ids:
        if decisions_raw.lower().startswith("not-applicable"):
            _, separator, reason = decisions_raw.partition(":")
            if not separator or not reason.strip():
                result["blockers"].append(
                    f"{increment_id} declara decisiones no aplicables sin indicar el motivo."
                )
        else:
            result["blockers"].append(f"{increment_id} no enlaza decisiones ni justifica not-applicable.")
    if not test_ids:
        result["blockers"].append(f"{increment_id} no enlaza pruebas previstas.")

    _domain_references(result, increment, definitions, "Data", "datos", {"DATA"})
    _domain_references(result, increment, definitions, "Identity", "identidad y privacidad", {"SEC", "PRIV"})
    _domain_references(result, increment, definitions, "Integrations", "integraciones", {"INT"})

    expected_states = {
        **{item: {"confirmed"} for item in requirement_ids + acceptance_ids},
        **{item: {"decision", "confirmed"} for item in decision_ids},
        **{item: {"planned", "confirmed"} for item in test_ids},
    }
    for item_id, states in expected_states.items():
        item = definitions.get(item_id)
        if item is None:
            result["blockers"].append(f"Referencia requerida sin definición: {item_id}.")
        elif item.get("State") not in states:
            result["blockers"].append(
                f"{item_id} tiene estado {item.get('State', 'absent')}; se esperaba {sorted(states)}."
            )

    for requirement_id in requirement_ids:
        item = definitions.get(requirement_id, {})
        linked = set(_ids(item.get("Acceptance", ""), {"AC"}))
        if not linked.intersection(acceptance_ids):
            result["blockers"].append(
                f"{requirement_id} no enlaza un criterio de aceptación incluido en {increment_id}."
            )

    for acceptance_id in acceptance_ids:
        item = definitions.get(acceptance_id, {})
        linked = set(_ids(item.get("Requirement", ""), {"FR", "NFR", "TR"}))
        if not linked.intersection(requirement_ids):
            result["blockers"].append(
                f"{acceptance_id} no enlaza un requisito incluido en {increment_id}."
            )

    for decision_id in decision_ids:
        item = definitions.get(decision_id, {})
        linked = set(_ids(item.get("Requirements", ""), {"FR", "NFR", "TR"}))
        if not linked.intersection(requirement_ids):
            result["blockers"].append(
                f"{decision_id} no enlaza un requisito incluido en {increment_id}."
            )

    for test_id in test_ids:
        item = definitions.get(test_id, {})
        linked_increments = set(_ids(item.get("Increment", ""), {"INC"}))
        linked_acceptance = set(_ids(item.get("Acceptance", ""), {"AC"}))
        if increment_id not in linked_increments:
            result["blockers"].append(f"{test_id} no enlaza {increment_id}.")
        if not linked_acceptance.intersection(acceptance_ids):
            result["blockers"].append(
                f"{test_id} no enlaza un criterio de aceptación incluido en {increment_id}."
            )

    trace_rows = _rows(_load_artifact_body(root, manifest, "ART-TRACE"))
    for requirement_id in requirement_ids:
        matching = [
            row for row in trace_rows
            if requirement_id in _ids(row.get("Requirement", ""), {"FR", "NFR", "TR"})
            and increment_id in _ids(row.get("Increment", ""), {"INC"})
        ]
        if not matching:
            result["blockers"].append(
                f"Falta una fila de trazabilidad para {requirement_id} y {increment_id}."
            )
            continue
        if not any(set(_ids(row.get("Acceptance", ""), {"AC"})).intersection(acceptance_ids) for row in matching):
            result["blockers"].append(f"La trazabilidad de {requirement_id} no incluye aceptación.")
        if decision_ids and not any(
            set(_ids(row.get("Decision", ""), {"ADR"})).intersection(decision_ids) for row in matching
        ):
            result["blockers"].append(f"La trazabilidad de {requirement_id} no incluye decisión.")
        if not any(set(_ids(row.get("Test", ""), {"TEST"})).intersection(test_ids) for row in matching):
            result["blockers"].append(f"La trazabilidad de {requirement_id} no incluye prueba.")

    open_rows = _rows(_load_artifact_body(root, manifest, "ART-OPEN"))
    for row in open_rows:
        if row.get("State") not in {"open", "blocked"}:
            continue
        scope = row.get("Scope", "")
        message = f"{row.get('ID', 'OPEN')}: {row.get('Question', 'punto abierto')}"
        blocking = (
            row.get("ID") in manifest.get("open_blockers", [])
            or row.get("Blocking", "").strip().lower() == "true"
        )
        if blocking and scope in {"project", increment_id}:
            if message not in result["blockers"]:
                result["blockers"].append(message)
        else:
            if message not in result["non_blocking_pending"]:
                result["non_blocking_pending"].append(message)

    if manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption", {})
        if adoption.get("status") != "materialized":
            result["blockers"].append("La baseline de adopción no está materialized.")
        if adoption.get("baseline_freshness") != "current":
            result["blockers"].append("La baseline de adopción no está vigente.")

    if manifest.get("active_increment") not in {None, increment_id}:
        result["blockers"].append(
            f"El índice declara otro incremento activo: {manifest.get('active_increment')}."
        )

    if result["blockers"]:
        result["status"] = "blocked"
        return 3, result
    if result["non_blocking_pending"]:
        result["status"] = "ready-with-non-blocking-pending"
    else:
        result["status"] = "ready"
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    exit_code, result = assess(args.project_root, args.increment)
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        for blocker in result["blockers"]:
            print(f"BLOCKER: {blocker}")
        for pending in result["non_blocking_pending"]:
            print(f"PENDING: {pending}")
        print("La evaluación no autoriza implementación.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
