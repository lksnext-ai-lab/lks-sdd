#!/usr/bin/env python3
"""Check semantic traceability between confirmed needs, acceptance, increments, tests, and evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from validate_project import (
    ID_RE,
    parse_frontmatter,
    parse_markdown_tables,
    validate_project,
)


def _ids(value: str, prefixes: set[str]) -> set[str]:
    return {
        item for item in ID_RE.findall(value or "") if item.split("-", 1)[0] in prefixes
    }


def check(root: Path, increment: str | None) -> tuple[int, dict[str, Any]]:
    report, manifest, definitions = validate_project(root)
    gaps = [f"Contrato inválido: {item}" for item in report.errors]
    if manifest is None or report.errors:
        return 2, {"valid": False, "increment": increment, "gaps": gaps, "checked": []}
    trace_entry = next(
        item for item in manifest["artifacts"] if item["id"] == "ART-TRACE"
    )
    metadata, body = parse_frontmatter(
        (root / trace_entry["path"]).read_text(encoding="utf-8")
    )
    del metadata
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
            requirement_id.split("-", 1)[0] not in {"FR", "NFR", "TR"}
            or item.get("State") != "confirmed"
        ):
            continue
        item_increments = _ids(item.get("Increment", ""), {"INC"})
        if increment and increment not in item_increments:
            continue
        checked.append(requirement_id)
        matching = [
            row
            for row in rows
            if requirement_id in _ids(row.get("Requirement", ""), {"FR", "NFR", "TR"})
        ]
        if increment:
            matching = [
                row
                for row in matching
                if increment in _ids(row.get("Increment", ""), {"INC"})
            ]
        if not matching:
            gaps.append(f"{requirement_id}: falta una fila de trazabilidad aplicable.")
            continue
        for label, column, prefixes in (
            ("aceptación", "Acceptance", {"AC"}),
            ("incremento", "Increment", {"INC"}),
            ("prueba", "Test", {"TEST"}),
        ):
            if not any(_ids(row.get(column, ""), prefixes) for row in matching):
                gaps.append(f"{requirement_id}: falta enlace de {label}.")
        linked_evidence = [
            (row, evidence_id)
            for row in matching
            for evidence_id in _ids(row.get("Evidence", ""), {"EVID"})
        ]
        if not linked_evidence:
            gaps.append(f"{requirement_id}: no existe evidencia ejecutada enlazada.")
            continue
        applicable_evidence = False
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
            if (
                evidence
                and evidence.get("increment") in row_increments
                and (increment is None or evidence.get("increment") == increment)
            ):
                applicable_evidence = True
                break
        if not applicable_evidence:
            gaps.append(
                f"{requirement_id}: la evidencia enlazada no corresponde al incremento."
            )
    if increment and increment not in definitions:
        gaps.append(f"El incremento {increment} no está definido.")
    result = {
        "valid": not gaps,
        "increment": increment,
        "checked": checked,
        "gaps": gaps,
        "limitations": [
            "La comprobación valida enlaces y estados; no juzga la suficiencia semántica de la evidencia."
        ],
    }
    return (0 if not gaps else 3), result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    code, result = check(args.project_root.expanduser().resolve(), args.increment)
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("VALID" if result["valid"] else "INCOMPLETE")
        for gap in result["gaps"]:
            print(f"GAP: {gap}")
    return code


if __name__ == "__main__":
    sys.exit(main())
