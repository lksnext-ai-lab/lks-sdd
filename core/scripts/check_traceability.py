#!/usr/bin/env python3
"""Check traceability at the preimplementation or verification handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from contract_engine import (
    build_project_model,
    expand_reference_ids,
    is_pending_traceability_evidence,
    resolve_active_increment,
)
from validate_project import (
    parse_frontmatter,
    parse_markdown_tables,
    validate_project,
)
from delivery_engine import validate_delivery_contract
from evidence_contract import (
    integration_evidence_errors,
    integration_gate_applicability,
    selected_task_requirements,
)


def _ids(value: str, prefixes: set[str]) -> set[str]:
    return expand_reference_ids(value, prefixes)


def _resolved_phase(manifest: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested
    if manifest.get("phase") in {"verification", "operation"}:
        return "verification"
    verification = manifest.get("verification")
    if isinstance(verification, dict) and verification.get("status") != "not-run":
        return "verification"
    return "preimplementation"


def _integration_obligations_for_evidence(
    evidence: dict[str, Any], delivery: dict[str, Any]
) -> list[dict[str, Any]]:
    task_ids = evidence.get("task_ids")
    if isinstance(task_ids, list) and task_ids:
        return integration_gate_applicability(task_ids, delivery)
    historical_owners: set[str] = set()
    for interface in delivery.get("interfaces", {}).values():
        if interface.get("State", "").strip().casefold() == "confirmed":
            historical_owners.update(
                expand_reference_ids(interface.get("Verification task", ""), {"TASK"})
            )
    return integration_gate_applicability(sorted(historical_owners), delivery)


def _successful_evidence(
    evidence: dict[str, Any] | None,
    evidence_id: str,
    row_increments: set[str],
    scoped_increment: str | None,
    delivery: dict[str, Any],
) -> bool:
    """Accept only structured, applicable evidence whose checks all passed."""

    if not evidence or evidence.get("evidence_id") != evidence_id:
        return False
    evidence_increment = evidence.get("increment")
    if evidence_increment not in row_increments:
        return False
    if scoped_increment is not None and evidence_increment != scoped_increment:
        return False
    if evidence.get("classification") not in {
        "verified",
        "verified-with-reservations",
    }:
        return False
    checks = evidence.get("checks")
    checks_passed = (
        isinstance(checks, list)
        and bool(checks)
        and all(
            isinstance(item, dict) and item.get("status") == "passed"
            for item in checks
        )
    )
    if not checks_passed:
        return False
    obligations = _integration_obligations_for_evidence(evidence, delivery)
    return not integration_evidence_errors(evidence, obligations)


def _active_gap(item: dict[str, Any]) -> str:
    """Render one handoff diagnostic with enough relation context to act on it."""

    location = item.get("location", {})
    source = (
        location.get("source_id")
        or location.get("table_id")
        or location.get("path")
    )
    observed = item.get("observed")
    if isinstance(observed, dict):
        target = str(observed.get("id") or observed)
        state = observed.get("state")
        if state:
            target += f" ({state})"
    elif observed is not None:
        target = str(observed)
    else:
        target = None
    relation = ""
    column = location.get("column")
    if source and column and target:
        relation = f"{source} [{column}] -> {target}: "
    elif source and target and source != target:
        relation = f"{source} -> {target}: "
    elif target:
        relation = f"{target}: "
    elif source:
        relation = f"{source}: "
    remediation_value = item.get("remediation")
    remediation = f" Acción: {remediation_value}" if remediation_value else ""
    return f"[{item['code']}] {relation}{item['message']}{remediation}"


def _diagnostic_gap(item: dict[str, Any]) -> str:
    """Keep legacy trace gaps readable while exposing typed diagnostic codes."""

    code = str(item.get("code", "TRACE-UNKNOWN"))
    if code.startswith("LKS-ACTIVE-"):
        return _active_gap(item)
    element = item.get("element_id")
    prefix = f"{element}: " if element else ""
    return f"[{code}] {prefix}{item['message']}"


def _deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate exact structured diagnostics without merging distinct locations."""

    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def check(
    root: Path,
    increment: str | None,
    phase: str = "auto",
    *,
    task_ids: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    report, manifest, definitions = validate_project(root)
    diagnostics: list[dict[str, Any]] = []

    def gap(code: str, message: str, element_id: str | None = None) -> None:
        diagnostics.append(
            {
                "code": code,
                "severity": "error",
                "stage": "traceability",
                "message": message,
                "element_id": element_id,
            }
        )

    for item in report.errors:
        gap("TRACE-CONTRACT-INVALID", f"Contrato inválido: {item}")
    if manifest is None or report.errors:
        diagnostics = _deduplicate(diagnostics)
        return 2, {
            "valid": False,
            "phase": phase,
            "increment": increment,
            "gaps": [_diagnostic_gap(item) for item in diagnostics],
            "diagnostics": diagnostics,
            "checked": [],
        }

    resolved_phase = _resolved_phase(manifest, phase)
    scoped_requirements: set[str] | None = None
    delivery = validate_delivery_contract(root, manifest)
    if task_ids:
        unknown = sorted(set(task_ids) - set(delivery.get("tasks", {})))
        wrong_increment = sorted(
            task_id
            for task_id in task_ids
            if increment is not None
            and delivery.get("tasks", {}).get(task_id, {}).get("Increment") != increment
        )
        if unknown:
            gap("TRACE-TASK-UNDEFINED", "TASK no definida: " + ", ".join(unknown))
        if wrong_increment:
            gap("TRACE-TASK-SCOPE", "TASK fuera del incremento solicitado: " + ", ".join(wrong_increment))
        if not unknown and not wrong_increment:
            scoped_requirements = selected_task_requirements(task_ids, delivery)
            if not scoped_requirements:
                gap("TRACE-TASK-EMPTY", "El TASK slice no enlaza requisitos trazables.")
    if increment is not None:
        increment_definition = definitions.get(increment)
        if (
            increment_definition is None
            or not increment_definition.get("path", "").endswith("increments.md")
        ):
            gap(
                "TRACE-INCREMENT-UNDEFINED",
                f"El incremento {increment} no está definido.",
                increment,
            )

        active_contract = resolve_active_increment(
            build_project_model(root), increment
        )
        for item in active_contract.diagnostics:
            diagnostics.append(item.as_dict())

    trace_entry = next(
        item for item in manifest["artifacts"] if item["id"] == "ART-TRACE"
    )
    _, body = parse_frontmatter(
        (root / trace_entry["path"]).read_text(encoding="utf-8")
    )
    rows = [
        row
        for table in parse_markdown_tables(body)
        for row in table
        if "Requirement" in row
    ]
    checked: list[str] = []
    evidence_cache: dict[str, dict[str, Any] | None] = {}
    for requirement_id, item in definitions.items():
        if (
            requirement_id.split("-", 1)[0] not in {"FR", "NFR", "TR", "BR"}
            or item.get("State") != "confirmed"
        ):
            continue
        item_increments = _ids(item.get("Increment", ""), {"INC"})
        if increment and increment not in item_increments:
            continue
        if scoped_requirements is not None and requirement_id not in scoped_requirements:
            continue
        checked.append(requirement_id)
        matching = [
            row
            for row in rows
            if requirement_id
            in _ids(row.get("Requirement", ""), {"FR", "NFR", "TR", "BR"})
        ]
        if increment:
            matching = [
                row
                for row in matching
                if increment in _ids(row.get("Increment", ""), {"INC"})
            ]
        if not matching:
            gap(
                "TRACE-ROW-MISSING",
                f"{requirement_id}: falta una fila de trazabilidad aplicable.",
                requirement_id,
            )
            continue
        for code, label, column, prefixes in (
            ("TRACE-AC-MISSING", "aceptación", "Acceptance", {"AC"}),
            ("TRACE-INC-MISSING", "incremento", "Increment", {"INC"}),
            ("TRACE-TEST-MISSING", "prueba", "Test", {"TEST"}),
        ):
            if not any(_ids(row.get(column, ""), prefixes) for row in matching):
                gap(code, f"{requirement_id}: falta enlace de {label}.", requirement_id)

        decision_cells = [row.get("Decision", "").strip() for row in matching]
        has_decision = any(_ids(cell, {"ADR"}) for cell in decision_cells)
        has_reasoned_na = any(
            cell.casefold().startswith("not-applicable:")
            and bool(cell.partition(":")[2].strip())
            for cell in decision_cells
        )
        if not has_decision and not has_reasoned_na:
            gap(
                "TRACE-ADR-MISSING",
                f"{requirement_id}: falta decisión o justificación de no aplicabilidad.",
                requirement_id,
            )

        if resolved_phase == "preimplementation":
            continue
        linked_evidence = [
            (row, evidence_id)
            for row in matching
            for evidence_id in (
                set()
                if is_pending_traceability_evidence(row.get("Evidence", ""))
                else _ids(row.get("Evidence", ""), {"EVID"})
            )
        ]
        if not linked_evidence:
            gap(
                "TRACE-EVIDENCE-MISSING",
                f"{requirement_id}: no existe evidencia ejecutada enlazada.",
                requirement_id,
            )
            continue
        applicable_evidence = False
        unsuccessful_applicable_evidence = False
        reconciliation_applicable_evidence = False
        for row, evidence_id in linked_evidence:
            if evidence_id not in evidence_cache:
                path = root / "docs" / "lks-sdd" / "evidence" / f"{evidence_id}.json"
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    loaded = None
                evidence_cache[evidence_id] = (
                    loaded if isinstance(loaded, dict) else None
                )
            evidence = evidence_cache[evidence_id]
            row_increments = _ids(row.get("Increment", ""), {"INC"})
            evidence_increment = evidence.get("increment") if evidence else None
            same_scope = evidence_increment in row_increments and (
                increment is None or evidence_increment == increment
            )
            if same_scope and evidence:
                obligations = _integration_obligations_for_evidence(
                    evidence, delivery
                )
                reconciliation_applicable_evidence = (
                    reconciliation_applicable_evidence
                    or bool(integration_evidence_errors(evidence, obligations))
                )
            if same_scope and _successful_evidence(
                evidence, evidence_id, row_increments, increment, delivery
            ):
                applicable_evidence = True
                break
            if same_scope:
                unsuccessful_applicable_evidence = True
        if not applicable_evidence:
            if reconciliation_applicable_evidence:
                gap(
                    "TRACE-EVIDENCE-RECONCILIATION-REQUIRED",
                    f"{requirement_id}: reconciliation-required; la evidencia histórica "
                    "conserva valor de componente, pero no acredita la integración tipada.",
                    requirement_id,
                )
            elif unsuccessful_applicable_evidence:
                gap(
                    "TRACE-EVIDENCE-NOT-PASSED",
                    f"{requirement_id}: la evidencia enlazada no acredita checks ejecutados satisfactoriamente.",
                    requirement_id,
                )
            else:
                gap(
                    "TRACE-EVIDENCE-INAPPLICABLE",
                    f"{requirement_id}: la evidencia enlazada no corresponde al incremento.",
                    requirement_id,
                )

    if not checked:
        scope = f" para {increment}" if increment else ""
        gap(
            "TRACE-EMPTY-SCOPE",
            "No hay requisitos confirmados aplicables"
            f"{scope}; una comprobación vacía no puede considerarse válida.",
            increment,
        )

    diagnostics = _deduplicate(diagnostics)
    result = {
        "valid": not diagnostics,
        "phase": resolved_phase,
        "increment": increment,
        "task_ids": sorted(set(task_ids or [])),
        "checked": checked,
        "gaps": [_diagnostic_gap(item) for item in diagnostics],
        "diagnostics": diagnostics,
        "evidence_required": resolved_phase == "verification",
        "reconciliation_required": any(
            item.get("code") == "TRACE-EVIDENCE-RECONCILIATION-REQUIRED"
            for item in diagnostics
        ),
        "limitations": [
            "La comprobación exige scopes tipados suficientes; component y visual no acreditan composición, flujo ni persistencia."
        ],
    }
    return (0 if not diagnostics else 3), result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument(
        "--phase",
        choices=("auto", "preimplementation", "verification"),
        default="auto",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    code, result = check(
        args.project_root.expanduser().resolve(),
        args.increment,
        args.phase,
        task_ids=args.task or None,
    )
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("VALID" if result["valid"] else "INCOMPLETE")
        print(f"Phase: {result['phase']}")
        for item in result["gaps"]:
            print(f"GAP: {item}")
    return code


if __name__ == "__main__":
    sys.exit(main())
