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
from profile_registry import resolve_profile  # noqa: E402
from delivery_engine import delivery_readiness, validate_delivery_contract  # noqa: E402
from planning_engine import assess_authorization, assess_planning, next_tasks  # noqa: E402
from contract_engine import (  # noqa: E402
    RelationSpec,
    build_project_model,
    document_fingerprint,
    parse_reference_cell,
    resolve_active_increment,
)
from validate_reference_profile import (  # noqa: E402
    PROFILE_ID,
    validate_consumer_profile_lock,
    validate_profile,
)

DOMAIN_CONTRACT_HEADERS = (
    "Increment",
    "Domain",
    "Applicability",
    "References",
    "Reason",
)
DOMAIN_PREFIXES = {
    "data": {"DATA"},
    "identity": {"SEC"},
    "security": {"SEC"},
    "privacy": {"PRIV"},
    "integrations": {"INT"},
}


def _ids(value: str, prefixes: set[str] | None = None) -> list[str]:
    allowed = prefixes or {
        item.split("-", 1)[0] for item in ID_RE.findall(value or "")
    }
    if not allowed:
        return []
    relation = RelationSpec(
        column="runtime",
        targets=frozenset(allowed),
        minimum=0,
        maximum=None,
        active_input=False,
        require_defined=False,
        allow_empty=True,
        allow_applicability=frozenset({"pending", "not-applicable"}),
        allow_legacy_artifact_marker=True,
    )
    parsed = parse_reference_cell(value or "", relation, mode="compat")
    return list(parsed.references) if parsed.valid else []


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


def _assess_domains(
    root: Path,
    manifest: dict[str, Any],
    definitions: dict[str, dict[str, str]],
    increment_id: str,
    increment: dict[str, str],
    result: dict[str, Any],
) -> None:
    if manifest.get("schema_version") not in {"1.1", "1.2", "1.3"}:
        _domain_references(result, increment, definitions, "Data", "datos", {"DATA"})
        _domain_references(
            result,
            increment,
            definitions,
            "Identity",
            "identidad y privacidad",
            {"SEC", "PRIV"},
        )
        _domain_references(
            result,
            increment,
            definitions,
            "Integrations",
            "integraciones",
            {"INT"},
        )
        return

    body = _load_artifact_body(root, manifest, "ART-INCREMENTS")
    rows = table_rows_for_headers(
        parse_markdown_table_blocks(body), DOMAIN_CONTRACT_HEADERS
    )
    if rows is None:
        result["blockers"].append("Falta la tabla contractual de aplicabilidad por dominio.")
        return
    scoped = [
        row for row in rows if row.get("Increment", "").strip() == increment_id
    ]
    for domain, prefixes in DOMAIN_PREFIXES.items():
        matching = [
            row for row in scoped if row.get("Domain", "").strip().casefold() == domain
        ]
        if len(matching) != 1:
            result["blockers"].append(
                f"{increment_id} debe declarar exactamente una aplicabilidad para {domain}."
            )
            continue
        row = matching[0]
        applicability = row.get("Applicability", "").strip().casefold()
        reason = row.get("Reason", "").strip()
        references = _ids(row.get("References", ""), prefixes)
        if applicability == "pending":
            result["blockers"].append(
                f"{increment_id} mantiene pendiente la aplicabilidad de {domain}: {reason or 'sin motivo'}."
            )
            continue
        if applicability == "not-applicable":
            if references:
                result["blockers"].append(
                    f"{increment_id} declara {domain} no aplicable pero conserva referencias activas."
                )
            if not reason:
                result["blockers"].append(
                    f"La no aplicabilidad de {domain} requiere un motivo."
                )
            continue
        if applicability != "applicable":
            result["blockers"].append(
                f"{increment_id} usa una aplicabilidad inválida para {domain}: {applicability or 'vacía'}."
            )
            continue
        if not references:
            result["blockers"].append(
                f"{domain} applicable debe enlazar {sorted(prefixes)}."
            )
        for reference in references:
            _confirmed_reference(result, definitions, reference, domain)


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
            requirement_ids = _ids(
                item.get("Requirements", ""), {"FR", "NFR", "TR", "BR"}
            )
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


def _finalize_result(result: dict[str, Any]) -> dict[str, Any]:
    """Expose orthogonal phase outcomes and one unambiguous next action."""
    specification_blockers = list(dict.fromkeys(result.get("blockers", [])))
    pending = list(dict.fromkeys(result.get("non_blocking_pending", [])))
    specification_status = (
        "blocked"
        if specification_blockers
        else "ready-with-non-blocking-pending"
        if pending
        else "ready"
    )
    result["specification_readiness"] = {
        "status": specification_status,
        "blockers": specification_blockers,
        "non_blocking_pending": pending,
    }
    automation = result.get("automation_support", {})
    automation_blockers = list(dict.fromkeys(automation.get("blockers", [])))
    combined = specification_blockers + [
        f"Soporte de automatización: {item}" for item in automation_blockers
    ]
    result["blockers"] = list(dict.fromkeys(combined))
    result["non_blocking_pending"] = pending
    delivery = result.get("delivery_readiness", {})
    planning = result.get("planning_completeness", {})
    authorization = result.get("implementation_authorization", {})
    manifest_phase = result.pop("_manifest_phase", {})
    implementation = manifest_phase.get("implementation", "not-started")
    verification = manifest_phase.get("verification", "not-run")
    delivery_state = manifest_phase.get("delivery", "not-started")
    result["phase_states"] = {
        "specification": specification_status,
        "architecture_and_automation": automation.get("status", "not-assessed"),
        "planning_completeness": planning.get("status", "not-assessed"),
        "planning_integrity": planning.get("integrity", "not-assessed"),
        "selected_portion": delivery.get("status", "not-assessed"),
        "implementation": implementation,
        "verification": verification,
        "delivery": delivery_state,
    }
    if specification_blockers:
        action = "specification-blocked"
        recommendation = "Resolver los bloqueos de especificación del alcance evaluado."
    elif automation_blockers:
        action = "automation-blocked"
        recommendation = "Resolver el soporte de automatización o cambiar una decisión técnica confirmada."
    elif planning.get("integrity") == "invalid":
        action = "replanning-required"
        recommendation = "Corregir incoherencias de cobertura o dependencias antes de implementar."
    elif planning.get("status") == "stale":
        action = "reconciliation-required"
        recommendation = "Reconciliar el cambio y volver a confirmar los fingerprints de planificación."
    elif planning.get("status") != "complete" and not planning.get(
        "partial_implementation_policy_satisfied"
    ):
        action = "planning-required"
        recommendation = "Completar y validar la planificación antes de iniciar la implementación."
    elif delivery.get("status") != "ready":
        action = "selected-portion-blocked"
        recommendation = "Seleccionar o completar una tarea ready con todas sus dependencias done."
    elif authorization.get("status") != "authorized":
        action = "ready-for-implementation-authorization"
        recommendation = "Revisar el plan y registrar una autorización humana delimitada por tareas y fingerprints."
    else:
        action = "ready-to-implement"
        recommendation = "Iniciar o reanudar las tareas autorizadas y mantener su checkpoint."
    result["status"] = action
    result["recommended_next_step"] = recommendation
    result["implementation_authorized"] = authorization.get("status") == "authorized"
    decision = (
        "Confirmar la descomposición integral; alternativamente autorizar planificación incremental con una ADR explícita, o pausar con checkpoint."
        if action == "planning-required"
        else "Autorizar o no la implementación de la porción indicada."
        if action == "ready-for-implementation-authorization"
        else "Resolver la reconciliación o replanificación propuesta."
        if action in {"reconciliation-required", "replanning-required"}
        else "Ninguna decisión humana nueva; conservar los límites de la autorización vigente."
        if action == "ready-to-implement"
        else "Resolver los bloqueos indicados."
    )
    result["human_decision_required"] = decision
    result["transition_summary"] = {
        "where_we_are": action,
        "completed": result.pop("_completed_summary", []),
        "in_progress": manifest_phase.get("active_tasks", []),
        "pending": planning.get("gaps", []),
        "blocked": list(dict.fromkeys(
            specification_blockers
            + automation_blockers
            + delivery.get("blockers", [])
            + planning.get("integrity_errors", [])
        )),
        "next_step": recommendation,
        "human_decision": decision,
    }
    return result


def assess(
    project_root: Path,
    increment_id: str,
    task_ids: list[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    root = project_root.expanduser().resolve()
    first_report, _, _ = validate_project(root)
    first_model = build_project_model(root)
    first_document_fingerprint = document_fingerprint(first_model)
    report, manifest, definitions = validate_project(root)
    model = build_project_model(root)
    active_contract = resolve_active_increment(model, increment_id)
    current_document_fingerprint = document_fingerprint(model)
    checked_files = list(active_contract.checked_files)
    input_fingerprint = active_contract.fingerprint
    unstable_snapshot = first_document_fingerprint != current_document_fingerprint
    result: dict[str, Any] = {
        "increment": increment_id,
        "status": "blocked",
        "specification_readiness": {
            "status": "blocked",
            "blockers": [],
            "non_blocking_pending": [],
        },
        "automation_support": {
            "status": "not-assessed",
            "blockers": [],
        },
        "scope": increment_id,
        "blockers": [],
        "non_blocking_pending": [],
        "evidence_checked": checked_files,
        "checked_files": checked_files,
        "structural_checked_files": list(dict.fromkeys(report.checked_files)),
        "input_fingerprint": input_fingerprint,
        "active_contract_fingerprint": input_fingerprint,
        "profile_lock": {
            "path": ".lks-sdd/profile.lock.json",
            "sha256": active_contract.project.get("profile_lock_sha256"),
        },
        "document_fingerprint": current_document_fingerprint,
        "diagnostics": [item.as_dict() for item in active_contract.diagnostics],
        "limitations": [
            "La validación determinista no sustituye la revisión semántica de claridad, riesgo y suficiencia.",
            "Este resultado no autoriza implementación."
        ],
        "implementation_authorized": False,
        "_manifest_phase": {},
        "_completed_summary": [],
    }
    if not re.fullmatch(r"INC-[0-9]{3}", increment_id):
        result["blockers"].append("El identificador debe usar el formato INC-###.")
        return 2, _finalize_result(result)
    if unstable_snapshot:
        result["blockers"].append(
            "Los Markdown o assets cambiaron durante la lectura inicial; repita readiness sobre una instantánea estable."
        )
    if not report.valid or manifest is None:
        result["diagnostics"] = list(report.diagnostics)
        result["blockers"].extend(f"Contrato inválido: {error}" for error in report.errors)
        return 2, _finalize_result(result)
    result["blockers"].extend(
        f"Contrato activo: {item.message}"
        for item in active_contract.diagnostics
        if item.severity == "error"
    )

    prefix_counts: dict[str, int] = {}
    for item_id in active_contract.node_ids:
        prefix = item_id.split("-", 1)[0]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    result["_completed_summary"] = [
        f"Alcance activo de {increment_id} resuelto desde Markdown canónico.",
        (
            f"Requisitos activos: {sum(prefix_counts.get(prefix, 0) for prefix in ('FR', 'NFR', 'TR', 'BR'))}; "
            f"criterios de aceptación: {prefix_counts.get('AC', 0)}; pruebas planificadas: {prefix_counts.get('TEST', 0)}."
        ),
        f"Decisiones activas trazadas: {prefix_counts.get('ADR', 0)}.",
    ]
    executions = [
        item for item in manifest.get("executions", []) if isinstance(item, dict)
    ]
    active_execution_states = sorted(
        {
            str(item.get("status"))
            for item in executions
            if item.get("status")
            in {"in-progress", "in-review", "paused", "blocked"}
        }
    )
    terminal_execution_states = sorted(
        {str(item.get("status")) for item in executions}
    )
    legacy_implementation = manifest.get("implementation", {})
    implementation_state: Any = (
        active_execution_states[0]
        if len(active_execution_states) == 1
        else "mixed-active"
        if active_execution_states
        else terminal_execution_states[0]
        if len(terminal_execution_states) == 1
        else "mixed-terminal"
        if terminal_execution_states
        else legacy_implementation.get("status", "not-started")
        if isinstance(legacy_implementation, dict)
        else "not-started"
    )
    verification = manifest.get("verification", {})
    last_delivery = manifest.get("last_delivery", {})
    result["_manifest_phase"] = {
        "implementation": implementation_state,
        "verification": verification.get("status", "not-run") if isinstance(verification, dict) else "not-run",
        "delivery": last_delivery.get("status", "not-started") if isinstance(last_delivery, dict) else "not-started",
        "active_tasks": list(manifest.get("active_tasks", [])) if isinstance(manifest.get("active_tasks", []), list) else [],
    }

    if str(manifest.get("schema_version")) in {"1.2", "1.3"}:
        delivery = delivery_readiness(
            root, manifest, increment_id, task_ids=task_ids
        )
        result["delivery_readiness"] = delivery
        result["selected_portion_readiness"] = delivery
        result["non_blocking_pending"].extend(delivery["warnings"])
        planning = assess_planning(root, manifest, increment_id)
        result["planning_completeness"] = planning
        result["implementation_authorization"] = assess_authorization(
            manifest, planning, delivery.get("task_ids", [])
        )
        delivery_contract = validate_delivery_contract(root, manifest)
        result["next_tasks"] = next_tasks(delivery_contract, planning)
        result["_completed_summary"].extend(
            [
                f"Unidades desplegables registradas: {len(delivery_contract.get('units', {}))}; bindings tecnológicos: {len(delivery_contract.get('bindings', {}))}.",
                "Gobierno, release, tablero y detalles TASK se evaluaron como dimensiones separadas.",
            ]
        )
        bindings = {
            item.get("binding_id"): item
            for item in manifest.get("technology", {}).get(
                "profile_bindings", []
            )
            if isinstance(item, dict)
        }
        binding_results: list[dict[str, Any]] = []
        automation_errors: list[str] = []
        for binding_id in delivery.get("binding_ids", []):
            binding = bindings.get(binding_id, {})
            profile_id = binding.get("profile_id")
            if not isinstance(profile_id, str):
                automation_errors.append(
                    f"{binding_id}: falta un profile_id resoluble."
                )
                continue
            support = resolve_profile(profile_id)
            profile_errors = list(support.errors)
            profile_errors.extend(
                validate_profile(profile_id, require_validated=True)
            )
            lock_errors, lock_details = validate_consumer_profile_lock(
                root,
                profile_id=profile_id,
                binding_id=binding_id,
                required=False,
            )
            profile_errors.extend(lock_errors)
            profile_errors = list(dict.fromkeys(profile_errors))
            binding_supported = support.implementable and not profile_errors
            binding_results.append(
                {
                    "binding_id": binding_id,
                    "unit_id": binding.get("unit_id"),
                    **support.as_dict(),
                    "status": (
                        "supported" if binding_supported else "unsupported"
                    ),
                    "lock": lock_details,
                    "blockers": profile_errors,
                }
            )
            automation_errors.extend(
                f"{binding_id}/{profile_id}: {item}"
                for item in profile_errors
            )
        if not delivery.get("binding_ids"):
            automation_errors.append(
                "El incremento no resuelve ningún profile binding confirmado."
            )
        supported = bool(binding_results) and all(
            item["status"] == "supported" for item in binding_results
        )
        result["profile_locks"] = [
            item["lock"] for item in binding_results
        ]
        result["automation_support"] = {
            "status": "supported" if supported else "unsupported",
            "bindings": binding_results,
            "blockers": list(dict.fromkeys(automation_errors)),
        }
    else:
        result["selected_portion_readiness"] = {
            "status": "not-applicable",
            "blockers": [],
            "task_ids": [],
        }
        result["planning_completeness"] = {
            "status": "not-applicable",
            "integrity": "not-assessed",
            "gaps": [{
                "kind": "migration-required",
                "items": ["schema 1.2 or 1.3"],
                "explanation": "La completitud de planificación requiere migrar el contrato de entrega.",
            }],
            "integrity_errors": [],
        }
        result["implementation_authorization"] = {
            "status": "required", "authorization_id": None, "task_ids": []
        }
        selected_profile = manifest.get("technology", {}).get(
            "selected_profile"
        )
        if selected_profile is None:
            result["automation_support"] = {
                "status": "selection-required",
                "profile_id": None,
                "blockers": [
                    "No hay un perfil tecnológico seleccionado mediante una decisión confirmada."
                ],
            }
        else:
            support = resolve_profile(selected_profile)
            automation_errors = list(support.errors)
            if selected_profile == PROFILE_ID:
                automation_errors.extend(
                    validate_profile(require_validated=True)
                )
                lock_errors, lock_details = validate_consumer_profile_lock(
                    root, required=False
                )
                automation_errors.extend(lock_errors)
                lock_details["fingerprint_sha256"] = (
                    active_contract.project.get("profile_lock_sha256")
                )
                result["profile_lock"] = lock_details
            automation_errors = list(dict.fromkeys(automation_errors))
            supported = support.implementable and not automation_errors
            result["automation_support"] = {
                **support.as_dict(),
                "status": "supported" if supported else "unsupported",
                "blockers": automation_errors
                or (
                    []
                    if supported
                    else [
                        f"El perfil {selected_profile} es documentable, "
                        "pero no dispone de automatización validada."
                    ]
                ),
            }

    increment = definitions.get(increment_id)
    if increment is None or increment.get("path", "").endswith("increments.md") is False:
        result["blockers"].append(f"El incremento {increment_id} no está definido en ART-INCREMENTS.")
        return 3, _finalize_result(result)
    if increment.get("State") != "confirmed":
        result["blockers"].append(f"{increment_id} debe estar confirmed; estado actual: {increment.get('State', 'absent')}.")
    if _empty(increment.get("In scope", "")):
        result["blockers"].append(f"{increment_id} no declara alcance incluido.")
    if _empty(increment.get("Out of scope", "")):
        result["blockers"].append(f"{increment_id} no declara alcance excluido.")
    if (
        increment.get("State") == "confirmed"
        and not _empty(increment.get("In scope", ""))
        and not _empty(increment.get("Out of scope", ""))
    ):
        result["_completed_summary"][0] = (
            f"Alcance confirmado de {increment_id}: {increment['In scope']}. "
            f"Fuera de alcance: {increment['Out of scope']}."
        )

    _assess_visual_contract(root, manifest, definitions, increment_id, result)
    result["_completed_summary"].append(
        "UX e interfaz evaluadas: "
        f"aplicabilidad={result.get('interface_applicability', 'legacy')}; "
        f"modo visual={result.get('visual_mode', 'legacy')}; "
        f"elementos UX activos={prefix_counts.get('UX', 0)}; "
        f"baselines visuales activas={prefix_counts.get('VIS', 0)}."
    )

    requirement_ids = _ids(
        increment.get("Requirements", ""), {"FR", "NFR", "TR", "BR"}
    )
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

    _assess_domains(
        root, manifest, definitions, increment_id, increment, result
    )
    if manifest.get("schema_version") in {"1.1", "1.2", "1.3"}:
        domain_body = _load_artifact_body(root, manifest, "ART-INCREMENTS")
        domain_rows = table_rows_for_headers(
            parse_markdown_table_blocks(domain_body), DOMAIN_CONTRACT_HEADERS
        ) or []
        domain_states = {
            row.get("Domain", "").strip().casefold(): row.get(
                "Applicability", "unknown"
            ).strip().casefold()
            for row in domain_rows
            if row.get("Increment", "").strip() == increment_id
        }
        result["_completed_summary"].append(
            "Datos, identidad, seguridad, privacidad e integraciones evaluados: "
            + "; ".join(
                f"{domain}={domain_states.get(domain, 'missing')}"
                for domain in DOMAIN_PREFIXES
            )
            + "."
        )

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
        linked = set(
            _ids(item.get("Requirement", ""), {"FR", "NFR", "TR", "BR"})
        )
        if not linked.intersection(requirement_ids):
            result["blockers"].append(
                f"{acceptance_id} no enlaza un requisito incluido en {increment_id}."
            )

    for decision_id in decision_ids:
        item = definitions.get(decision_id, {})
        linked = set(
            _ids(item.get("Requirements", ""), {"FR", "NFR", "TR", "BR"})
        )
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
            if requirement_id
            in _ids(row.get("Requirement", ""), {"FR", "NFR", "TR", "BR"})
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
    scoped_open_points: list[str] = []
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
            scoped_open_points.append(row.get("ID", "OPEN"))
            if message not in result["blockers"]:
                result["blockers"].append(message)
        else:
            if message not in result["non_blocking_pending"]:
                result["non_blocking_pending"].append(message)
    if not scoped_open_points:
        result["_completed_summary"].append(
            "No quedan bloqueos ni puntos abiertos bloqueantes para el alcance evaluado; "
            "cualquier pendiente no bloqueante permanece visible por separado."
        )

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
        post_model = build_project_model(root)
        post_active = resolve_active_increment(post_model, increment_id)
        post_checked = list(post_active.checked_files)
        post_fingerprint = post_active.fingerprint
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
        result["active_contract_fingerprint"] = post_fingerprint
        result["document_fingerprint"] = document_fingerprint(post_model)
        result["structural_checked_files"] = list(
            dict.fromkeys(post_report.checked_files)
        )

    _finalize_result(result)
    return (
        0
        if result["status"]
        in {"ready-for-implementation-authorization", "ready-to-implement"}
        else 3,
        result,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    parser.add_argument(
        "--task",
        action="append",
        help="TASK-### selected for portion readiness; repeat for multiple tasks.",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    exit_code, result = assess(args.project_root, args.increment, args.task)
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
