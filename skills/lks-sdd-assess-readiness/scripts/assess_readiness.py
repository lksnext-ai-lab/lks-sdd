#!/usr/bin/env python3
"""Deterministically assess one LKS-SDD increment without modifying the project."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_project import (  # noqa: E402
    ID_RE,
    INTERFACE_CONTRACT_HEADERS,
    interface_applicability,
    parse_frontmatter,
    parse_markdown_table_blocks,
    parse_markdown_tables,
    table_rows_for_headers,
    v06_contract_applies,
    validate_project,
)
from validate_reference_profile import PROFILE_ID, validate_profile  # noqa: E402


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


def _input_fingerprint(root: Path, checked_files: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(set(checked_files)):
        path = root / relative
        if not path.is_file():
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _confirmed_reference(
    result: dict[str, Any],
    definitions: dict[str, dict[str, str]],
    item_id: str,
    label: str,
) -> dict[str, str]:
    item = definitions.get(item_id, {})
    if not item:
        result["blockers"].append(f"Referencia de {label} sin definición: {item_id}.")
    elif item.get("State") not in {"confirmed", "decision"}:
        result["blockers"].append(
            f"{item_id} afecta a {label} pero no está confirmado; estado: {item.get('State', 'absent')}."
        )
    return item


def _assess_visual_contract(
    root: Path,
    manifest: dict[str, Any],
    definitions: dict[str, dict[str, str]],
    increment_id: str,
    result: dict[str, Any],
) -> None:
    increment_entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if item.get("id") == "ART-INCREMENTS"
        ),
        None,
    )
    if not isinstance(increment_entry, dict):
        result["blockers"].append("Falta ART-INCREMENTS.")
        return
    increment_text = (root / increment_entry["path"]).read_text(encoding="utf-8")
    increment_metadata, body = parse_frontmatter(increment_text)
    if not v06_contract_applies(manifest, increment_metadata):
        result["interface_applicability"] = "legacy-not-enforced"
        return
    interface_rows = table_rows_for_headers(
        parse_markdown_table_blocks(body), INTERFACE_CONTRACT_HEADERS
    )
    if interface_rows is None:
        result["blockers"].append(
            "Falta la tabla contractual de aplicabilidad de interfaz."
        )
        return
    matching = [
        row for row in interface_rows if row.get("Increment", "").strip() == increment_id
    ]
    if len(matching) != 1:
        result["blockers"].append(
            f"{increment_id} debe tener exactamente una fila de aplicabilidad de interfaz."
        )
        return
    interface_row = matching[0]
    applicability, inline_reason = interface_applicability(
        interface_row.get("Interface applicability", "")
    )
    reason = interface_row.get("Reason", "").strip() or inline_reason or ""
    visual_mode = interface_row.get("Visual mode", "").strip().casefold()
    result["visual_mode"] = visual_mode or "invalid"
    result["interface_applicability"] = applicability or "invalid"
    if applicability == "pending":
        result["blockers"].append(
            f"{increment_id} mantiene pendiente la aplicabilidad de interfaz: {reason or 'sin motivo'}."
        )
        return
    if applicability == "not-applicable":
        if not reason:
            result["blockers"].append(
                f"{increment_id} declara interfaz no aplicable sin motivo."
            )
        return
    if applicability != "applicable":
        result["blockers"].append(
            f"{increment_id} no declara una aplicabilidad de interfaz válida."
        )
        return

    if not any(item.get("id") == "ART-UX" for item in manifest.get("artifacts", [])):
        result["blockers"].append(
            f"{increment_id} tiene interfaz, pero ART-UX no está materializado."
        )
        return

    ux_raw = interface_row.get("UX contract", "").strip()
    if _empty(ux_raw) or ux_raw.casefold() == "pending":
        result["blockers"].append(
            f"{increment_id} no tiene un contrato UX confirmado."
        )
        ux_ids: list[str] = []
    else:
        ux_ids = _ids(ux_raw, {"UX"})
        if not ux_ids and "ART-UX" in ux_raw:
            ux_ids = [
                item_id
                for item_id, item in definitions.items()
                if item_id.startswith("UX-")
                and increment_id in _ids(item.get("Increment", ""), {"INC"})
                and item.get("State") in {"confirmed", "decision"}
            ]
        if not ux_ids:
            result["blockers"].append(
                f"{increment_id} enlaza ART-UX, pero no contiene elementos UX confirmados para el incremento."
            )

    confirmed_ux: set[str] = set()
    confirmed_screens: set[str] = set()
    confirmed_flows: set[str] = set()
    confirmed_directions: set[str] = set()
    direction_decisions: set[str] = set()
    flow_covered_screens: set[str] = set()
    for ux_id in dict.fromkeys(ux_ids):
        item = _confirmed_reference(result, definitions, ux_id, "UX")
        if not item:
            continue
        if increment_id not in _ids(item.get("Increment", ""), {"INC"}):
            result["blockers"].append(f"{ux_id} no enlaza {increment_id}.")
        if item.get("State") in {"confirmed", "decision"}:
            confirmed_ux.add(ux_id)
        if "Screen" in item:
            confirmed_screens.add(ux_id)
            requirement_ids = _ids(item.get("Requirements", ""), {"FR", "NFR", "TR"})
            acceptance_ids = _ids(item.get("Acceptance", ""), {"AC"})
            if not requirement_ids:
                result["blockers"].append(f"{ux_id} no enlaza requisitos.")
            if not acceptance_ids:
                result["blockers"].append(f"{ux_id} no enlaza aceptación.")
            for reference in requirement_ids + acceptance_ids:
                _confirmed_reference(result, definitions, reference, "trazabilidad UX")
        elif "Flow or interaction" in item:
            confirmed_flows.add(ux_id)
            acceptance_ids = _ids(item.get("Acceptance", ""), {"AC"})
            if not acceptance_ids:
                result["blockers"].append(f"{ux_id} no enlaza aceptación.")
            for reference in acceptance_ids:
                _confirmed_reference(result, definitions, reference, "trazabilidad UX")
            linked_screens = _ids(item.get("Screens", ""), {"UX"})
            flow_covered_screens.update(linked_screens)
            if not linked_screens:
                result["blockers"].append(
                    f"{ux_id} no enlaza pantallas dentro del flujo."
                )
            for screen_id in linked_screens:
                screen = _confirmed_reference(
                    result, definitions, screen_id, "pantalla del flujo"
                )
                if screen and "Screen" not in screen:
                    result["blockers"].append(
                        f"{ux_id} enlaza {screen_id}, que no es una pantalla."
                    )
        elif "Aspect" in item:
            confirmed_directions.add(ux_id)
            decision_ids = _ids(item.get("Decision", ""), {"ADR"})
            direction_decisions.update(decision_ids)
            if not decision_ids:
                result["blockers"].append(
                    f"{ux_id} de dirección visual no enlaza una decisión."
                )
            for reference in decision_ids:
                _confirmed_reference(result, definitions, reference, "dirección visual")

    for label, items in (
        ("pantalla confirmada", confirmed_screens),
        ("flujo confirmado", confirmed_flows),
        ("dirección visual confirmada", confirmed_directions),
    ):
        if not items:
            result["blockers"].append(
                f"{increment_id} requiere al menos una {label} en ART-UX."
            )
    for screen_id in sorted(confirmed_screens - flow_covered_screens):
        result["blockers"].append(
            f"{screen_id} no está cubierta por un flujo incluido en el contrato UX de {increment_id}."
        )

    visual_raw = interface_row.get("Visual prototype", "").strip()
    lowered_visual = visual_raw.casefold()
    if visual_mode == "pending" or _empty(visual_raw) or lowered_visual == "pending":
        result["blockers"].append(
            f"{increment_id} mantiene pendiente el prototipo visual."
        )
        return
    if visual_mode == "none":
        _, separator, visual_reason = visual_raw.partition(":")
        none_disclosure = f"{visual_raw} {reason}".casefold()
        if (
            not lowered_visual.startswith("not-applicable:")
            or not separator
            or not visual_reason.strip()
            or not reason
        ):
            result["blockers"].append(
                f"{increment_id} declara ausencia de cambio visual sin un motivo delimitado."
            )
        if (
            _ids(reason, {"VIS"})
            or "reutil" in none_disclosure
            or "reuse" in none_disclosure
        ):
            result["blockers"].append(
                f"{increment_id} no puede ocultar una baseline reutilizada bajo Visual mode=none."
            )
        result["visual_prototypes"] = []
        return
    if visual_mode not in {"new", "material-change", "reuse"}:
        result["blockers"].append(
            f"{increment_id} no declara un Visual mode válido para una interfaz aplicable."
        )
        return

    visual_ids = _ids(visual_raw, {"VIS"})
    result["visual_prototypes"] = visual_ids
    if not visual_ids:
        result["blockers"].append(
            f"{increment_id} debe enlazar VIS-###, pending o not-applicable: motivo."
        )
        return
    increment_decisions = set(
        _ids(definitions.get(increment_id, {}).get("Decisions", ""), {"ADR"})
    )
    for visual_id in dict.fromkeys(visual_ids):
        item = _confirmed_reference(result, definitions, visual_id, "prototipo visual")
        if not item:
            continue
        if not item.get("_asset_path"):
            result["blockers"].append(
                f"{visual_id} no tiene un asset local íntegro validado."
            )
        if visual_mode != "reuse" and increment_id not in _ids(
            item.get("Increment", ""), {"INC"}
        ):
            result["blockers"].append(f"{visual_id} no enlaza {increment_id}.")
        linked_ux = set(_ids(item.get("Screens or flow", ""), {"UX"}))
        if not linked_ux:
            result["blockers"].append(
                f"{visual_id} no enlaza pantallas o flujos UX."
            )
        for ux_id in linked_ux:
            _confirmed_reference(result, definitions, ux_id, "prototipo visual")
        if (
            visual_mode != "reuse"
            and confirmed_ux
            and not linked_ux.intersection(confirmed_ux)
        ):
            result["blockers"].append(
                f"{visual_id} no cubre ningún elemento del contrato UX de {increment_id}."
            )
        if visual_mode == "reuse":
            visual_decisions = set(_ids(item.get("Decision", ""), {"ADR"}))
            shared = visual_decisions & direction_decisions & increment_decisions
            if not shared:
                result["blockers"].append(
                    f"{visual_id} reutilizado no comparte una ADR confirmada con la dirección visual y las decisiones de {increment_id}."
                )
    if visual_mode == "reuse" and not reason:
        result["blockers"].append(
            f"{increment_id} reutiliza una baseline visual sin delimitar el motivo."
        )


def assess(project_root: Path, increment_id: str) -> tuple[int, dict[str, Any]]:
    root = project_root.expanduser().resolve()
    first_report, _, _ = validate_project(root)
    first_checked = list(dict.fromkeys(first_report.checked_files))
    first_fingerprint = _input_fingerprint(root, first_checked)
    report, manifest, definitions = validate_project(root)
    checked_files = list(dict.fromkeys(report.checked_files))
    input_fingerprint = _input_fingerprint(root, checked_files)
    unstable_snapshot = (
        first_checked != checked_files or first_fingerprint != input_fingerprint
    )
    result: dict[str, Any] = {
        "increment": increment_id,
        "status": "blocked",
        "scope": increment_id,
        "blockers": [],
        "non_blocking_pending": [],
        "evidence_checked": checked_files,
        "checked_files": checked_files,
        "input_fingerprint": input_fingerprint,
        "limitations": [
            "La validación determinista no sustituye la revisión semántica de claridad, riesgo y suficiencia.",
            "Este resultado no autoriza implementación."
        ],
        "implementation_authorized": False,
    }
    if not re.fullmatch(r"INC-[0-9]{3}", increment_id):
        result["blockers"].append("El identificador debe usar el formato INC-###.")
        return 2, result
    if unstable_snapshot:
        result["blockers"].append(
            "Los Markdown o assets cambiaron durante la lectura inicial; repita readiness sobre una instantánea estable."
        )
    if not report.valid or manifest is None:
        result["blockers"].extend(f"Contrato inválido: {error}" for error in report.errors)
        return 2, result

    selected_profile = manifest.get("technology", {}).get("selected_profile")
    if selected_profile is None:
        result["blockers"].append("No hay un perfil tecnológico seleccionado mediante una decisión confirmada.")
    elif selected_profile != PROFILE_ID:
        result["blockers"].append(
            f"El perfil {selected_profile} no dispone de soporte H0 implementado; perfil disponible: {PROFILE_ID}."
        )
    else:
        result["blockers"].extend(
            f"Perfil tecnológico no apto: {error}" for error in validate_profile(require_validated=True)
        )

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

    _assess_visual_contract(root, manifest, definitions, increment_id, result)

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

    if not result["blockers"]:
        post_report, _, _ = validate_project(root)
        post_checked = list(dict.fromkeys(post_report.checked_files))
        post_fingerprint = _input_fingerprint(root, post_checked)
        if not post_report.valid:
            result["blockers"].extend(
                f"El contrato cambió durante readiness: {error}"
                for error in post_report.errors
            )
        elif post_fingerprint != result["input_fingerprint"]:
            result["blockers"].append(
                "Los Markdown o assets cambiaron durante la evaluación; repita readiness sobre una instantánea estable."
            )
        result["checked_files"] = post_checked
        result["evidence_checked"] = post_checked
        result["input_fingerprint"] = post_fingerprint

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
