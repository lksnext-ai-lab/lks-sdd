#!/usr/bin/env python3
"""Materialize an authorized adoption baseline using additive documentation only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from adoption_common import (
    AdoptionError,
    compare_baseline,
    is_link_like,
    load_json_object,
    safe_root,
)
from validate_adoption import validate

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_project import validate_project  # noqa: E402

PLUGIN_VERSION = "2.1.3"
METHOD_VERSION = "1.5.0"
SCHEMA_VERSION = "1.5"
BASELINE_ID = "BL-0001"
PROJECT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUS_SUMMARY_HEADERS = (
    "Ruta",
    "Fase",
    "Puerta",
    "Incremento activo",
    "Readiness",
    "Próximo paso",
)
CORE_ARTIFACTS = [
    ("ART-STATUS", "00-control/project-status.md"),
    ("ART-SCOPE", "00-control/scope-register.md"),
    ("ART-OPEN", "00-control/open-points.md"),
    ("ART-BRIEF", "01-context/product-brief.md"),
    ("ART-CONSTRAINTS", "01-context/constraints.md"),
    ("ART-FR", "02-requirements/functional-requirements.md"),
    ("ART-NFR", "02-requirements/non-functional-requirements.md"),
    ("ART-TR", "02-requirements/technical-requirements.md"),
    ("ART-AC", "02-requirements/acceptance-criteria.md"),
    ("ART-SOLUTION", "03-solution/solution-overview.md"),
    ("ART-ARCH", "03-solution/architecture.md"),
    ("ART-INCREMENTS", "04-delivery/increments.md"),
    ("ART-GOVERNANCE", "04-delivery/delivery-governance.md"),
    ("ART-PLANS", "04-delivery/plans.md"),
    ("ART-TASKS", "04-delivery/tasks.md"),
    ("ART-PLANNING", "04-delivery/planning-coverage.md"),
    ("ART-TRACKING", "04-delivery/task-tracking.md"),
    ("ART-RISK", "04-delivery/risks-dependencies.md"),
    ("ART-QUALITY", "05-quality/quality-strategy.md"),
    ("ART-TEST-STRATEGY", "05-quality/test-strategy.md"),
    ("ART-TRACE", "05-quality/traceability.md"),
    ("ART-DEPLOYMENT", "06-operation/deployment.md"),
]
ADOPTION_ARTIFACTS = [
    ("ART-ADOPT-SCOPE", "07-adoption/inspection-scope.md", "inspection-scope.md"),
    (
        "ART-ADOPT-INVENTORY",
        "07-adoption/repository-inventory.md",
        "repository-inventory.md",
    ),
    (
        "ART-ADOPT-ARCHITECTURE",
        "07-adoption/observed-architecture.md",
        "observed-architecture.md",
    ),
    ("ART-ADOPT-BEHAVIOR", "07-adoption/observed-behavior.md", "observed-behavior.md"),
    ("ART-ADOPT-GAPS", "07-adoption/gaps-and-unknowns.md", "gaps-and-unknowns.md"),
    ("ART-ADOPT-RECONCILIATION", "07-adoption/reconciliation.md", "reconciliation.md"),
    ("ART-ADOPT-STRATEGY", "07-adoption/adoption-strategy.md", "adoption-strategy.md"),
    ("ART-ADOPT-BASELINE", "07-adoption/baseline-record.md", "baseline-record.md"),
]


def _one_line(value: Any) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _items(values: list[Any], empty: str) -> str:
    clean = [_one_line(item) for item in values if str(item).strip()]
    return "; ".join(clean) if clean else empty


def _contradictions(values: list[dict[str, Any]]) -> str:
    if not values:
        return "- Ninguna contradicción registrada."
    return "\n".join(
        f"- Estado `{item['state']}`: {_one_line(item['statement'])}. Resolución: {_one_line(item['resolution'])}."
        for item in values
    )


def _unknowns(values: list[dict[str, Any]]) -> str:
    if not values:
        return "- Ningún desconocido registrado."
    return "\n".join(
        f"- {_one_line(item['statement'])} (no bloqueante)." for item in values
    )


def _render(text: str, replacements: dict[str, str]) -> str:
    for token, value in replacements.items():
        text = text.replace("{{" + token + "}}", value)
    remaining = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text)))
    if remaining:
        raise AdoptionError(f"Tokens de plantilla sin resolver: {remaining}")
    return text


def _markdown_cells(line: str) -> tuple[str, ...] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return tuple(cell.strip() for cell in stripped[1:-1].split("|"))


def _rewrite_status_summary(text: str) -> str:
    """Render the adoption state from the table contract, not template wording."""

    lines = text.splitlines(keepends=True)
    matches: list[tuple[int, int]] = []
    for index in range(len(lines) - 2):
        if _markdown_cells(lines[index]) != STATUS_SUMMARY_HEADERS:
            continue
        separator = _markdown_cells(lines[index + 1])
        if separator is None or len(separator) != len(STATUS_SUMMARY_HEADERS) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separator
        ):
            raise AdoptionError(
                "ART-STATUS contiene una tabla resumen con separador inválido."
            )
        row_indexes: list[int] = []
        row_index = index + 2
        while row_index < len(lines) and _markdown_cells(lines[row_index]) is not None:
            row_indexes.append(row_index)
            row_index += 1
        if len(row_indexes) != 1:
            raise AdoptionError(
                "ART-STATUS debe contener exactamente una fila de estado del proyecto."
            )
        matches.append((index, row_indexes[0]))
    if len(matches) != 1:
        raise AdoptionError(
            "ART-STATUS debe contener exactamente una tabla resumen contractual."
        )

    _, row_index = matches[0]
    newline = (
        "\r\n"
        if lines[row_index].endswith("\r\n")
        else "\n"
        if lines[row_index].endswith("\n")
        else ""
    )
    values = (
        "adopt-existing",
        "adoption",
        "G5",
        "none",
        "not-assessed",
        "Continuar la definición incremental desde la baseline adoptada",
    )
    lines[row_index] = "| " + " | ".join(values) + " |" + newline
    return "".join(lines)


def _render_core(
    relative: str, project_id: str, today: str, intent: dict[str, Any]
) -> str:
    template = (
        PLUGIN_ROOT / "skills" / "lks-sdd-define" / "assets" / "templates" / relative
    )
    text = template.read_text(encoding="utf-8")
    text = re.sub(
        r'^created_with_plugin_version: "[0-9A-Za-z.-]+"$',
        f'created_with_plugin_version: "{PLUGIN_VERSION}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^schema_version: "[0-9.]+"$',
        f'schema_version: "{SCHEMA_VERSION}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r'^method_version: "[0-9.]+"$',
        f'method_version: "{METHOD_VERSION}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    text = _render(
        text, {"PROJECT_ID": project_id, "BASELINE_ID": BASELINE_ID, "DATE": today}
    )
    if relative == "00-control/project-status.md":
        text = _rewrite_status_summary(text).replace(
            "La inicialización no confirma decisiones ni autoriza generación de código.",
            "La baseline adoptada no homologa la aplicación ni autoriza cambios funcionales.",
        )
    elif relative == "00-control/open-points.md":
        text = (
            "\n".join(line for line in text.splitlines() if "OPEN-001" not in line)
            + "\n"
        )
    elif relative == "01-context/product-brief.md":
        body = (
            "# Brief de producto\n\n"
            "## Propósito confirmado\n\n"
            f"{_one_line(intent['purpose'])}\n\n"
            "## Comportamiento deseado confirmado\n\n"
            f"{_one_line(intent['desired_behavior'])}\n\n"
            "## Prioridades confirmadas\n\n"
            + "\n".join(f"- {_one_line(item)}" for item in intent["priorities"])
            + "\n"
        )
        frontmatter, _, _ = text.partition("---\n\n")
        text = frontmatter + "---\n\n" + body
        text = text.replace("status: draft", "status: confirmed", 1)
    return text


def _build_manifest(
    project_id: str,
    documentation_level: str,
    risk_profile: str,
    report: dict[str, Any],
    decision: dict[str, Any],
    report_hash: str,
    decision_hash: str,
    today: str,
) -> dict[str, Any]:
    git = report["baseline"]["git"]
    artifacts = [
        {"id": artifact_id, "path": f"docs/lks-sdd/{relative}", "required": True}
        for artifact_id, relative in CORE_ARTIFACTS
    ] + [
        {"id": artifact_id, "path": f"docs/lks-sdd/{relative}", "required": True}
        for artifact_id, relative, _ in ADOPTION_ARTIFACTS
    ]
    return {
        "project_id": project_id,
        "route": "adopt-existing",
        "method_version": METHOD_VERSION,
        "schema_version": SCHEMA_VERSION,
        "plugin_version": PLUGIN_VERSION,
        "documentation_level": documentation_level,
        "risk_profile": risk_profile,
        "phase": "adoption",
        "gate": "G5",
        "baseline_id": BASELINE_ID,
        "canonical_docs": "docs/lks-sdd",
        "artifacts": artifacts,
        "active_increment": None,
        "active_plan": "PLAN-001",
        "active_task": None,
        "active_tasks": [],
        "delivery_governance": {
            "state": "proposed",
            "model": None,
            "decision": None,
            "source": "docs/lks-sdd/04-delivery/delivery-governance.md",
            "active_change": "CHG-001",
            "review_due": None,
        },
        "version_control": {
            "type": git["type"],
            "origin": git["origin"],
            "branching_model": None,
            "main_branch": None,
            "integration_branch": None,
            "decision": None,
        },
        "planning": {
            "source": "docs/lks-sdd/04-delivery/planning-coverage.md",
            "target_type": "release",
            "target_id": "REL-001",
            "policy": "complete-before-implementation",
            "policy_decision": None,
            "specification_fingerprint": None,
            "planning_fingerprint": None,
            "confirmed_by_role": None,
            "confirmed_on": None,
            "last_change": None,
        },
        "task_tracking": {
            "source": "docs/lks-sdd/04-delivery/task-tracking.md",
            "binding_id": "TRK-001",
            "state": "proposed",
            "mode": "pending",
            "provider": None,
            "decision": None,
            "site": None,
            "project_key": None,
            "issue_type": None,
            "sync_policy": "pending",
            "write_policy": "pending",
            "reporting_scope": "pending",
            "coordination_gate": "pending",
            "reporting_status": "decision-required",
            "last_reported_on": None,
            "projection_fingerprint": None,
            "sync_status": "decision-required",
            "last_sync_on": None,
        },
        "authorizations": [],
        "executions": [],
        "last_verified_revision": None,
        "adoption": {
            "status": "materialized",
            "strategy": decision["strategy"],
            "baseline_freshness": "current",
            "report_sha256": report_hash,
            "decision_sha256": decision_hash,
            "inventory_fingerprint": report["baseline"]["inventory_fingerprint"],
            "expected_revision": git["revision"],
            "materialized_at": today,
            "write_scope": [".lks-sdd/", "docs/lks-sdd/"],
        },
    }


def _preview_hash(root: Path, planned: list[tuple[Path, str]]) -> str:
    digest = hashlib.sha256()
    for destination, content in sorted(planned, key=lambda item: str(item[0])):
        digest.update(destination.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content.encode("utf-8")).digest())
    return digest.hexdigest()


def _assert_destination(root: Path, destination: Path) -> None:
    try:
        relative = destination.relative_to(root)
    except ValueError as exc:
        raise AdoptionError("Destino documental fuera de la raíz confirmada.") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if is_link_like(current):
            raise AdoptionError(
                f"No se escribe a través de enlaces simbólicos o junctions: {relative.as_posix()}"
            )


def materialize(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = safe_root(args.project_root)
    if len(args.project_id) < 3 or not PROJECT_ID_RE.fullmatch(args.project_id):
        raise AdoptionError(
            "project_id debe usar minúsculas, números y guiones, con al menos tres caracteres."
        )
    try:
        date.fromisoformat(args.date)
    except ValueError as exc:
        raise AdoptionError("--date debe usar AAAA-MM-DD.") from exc
    validation_code, validation = validate(root, args.report, args.decision)
    if validation_code != 0:
        return 3, {**validation, "changed": False}
    report = load_json_object(args.report.expanduser().resolve(), "el informe")
    decision = load_json_object(args.decision.expanduser().resolve(), "la decisión")
    report_hash = validation["report_sha256"]
    decision_hash = validation["decision_sha256"]
    manifest_path = root / ".lks-sdd" / "project.json"
    _assert_destination(root, manifest_path)
    if manifest_path.is_file():
        existing = load_json_object(manifest_path, "project.json")
        adoption = existing.get("adoption", {})
        if (
            existing.get("route") == "adopt-existing"
            and existing.get("project_id") == args.project_id
            and adoption.get("status") == "materialized"
            and adoption.get("report_sha256") == report_hash
            and adoption.get("decision_sha256") == decision_hash
        ):
            current, _ = compare_baseline(root, report)
            if not current:
                return 3, {
                    "status": "stale",
                    "changed": False,
                    "blockers": ["La baseline materializada ya no está vigente."],
                }
            return 0, {
                "status": "already-materialized",
                "changed": False,
                "preview_hash": None,
                "created": [],
                "preserved": [".lks-sdd/project.json"],
            }
        raise AdoptionError(
            "Ya existe un índice LKS-SDD distinto; no se sobrescribirá."
        )

    intent = decision["confirmed_intent"]
    reconciliation = decision["reconciliation"]
    git = report["baseline"]["git"]
    inventory = report["inventory"]
    replacements = {
        "PROJECT_ID": args.project_id,
        "BASELINE_ID": BASELINE_ID,
        "DATE": args.date,
        "ROOT_LABEL": root.name,
        "SCOPE": _one_line(report["preflight"]["scope"]),
        "PRODUCTION_STATE": report["preflight"]["production_state"],
        "EXCLUSIONS": _items(
            report["preflight"].get("exclusions", []), "ninguna declarada"
        ),
        "FILES_INVENTORIED": str(report["coverage"]["files_inventoried"]),
        "TRUNCATED": str(report["coverage"]["truncated"]).lower(),
        "MANIFESTS": _items(inventory.get("manifest_paths", []), "ninguno observado"),
        "SOURCE_EXTENSIONS": _items(
            inventory.get("source_extensions", []), "ninguna observada"
        ),
        "SENSITIVE_COUNT": str(report["coverage"]["sensitive_files_excluded"]),
        "PURPOSE": _one_line(intent["purpose"]),
        "DESIRED_BEHAVIOR": _one_line(intent["desired_behavior"]),
        "PRIORITIES": _items(intent["priorities"], "ninguna"),
        "CONTRADICTIONS": _contradictions(reconciliation["contradictions"]),
        "UNKNOWNS": _unknowns(reconciliation["unknowns"]),
        "LIMITATIONS": "\n".join(
            f"- {_one_line(item)}" for item in report["limitations"]
        ),
        "REPORT_SHA256": report_hash,
        "DECISION_SHA256": decision_hash,
        "MATCHES": _items(reconciliation.get("matches", []), "ninguna registrada"),
        "CONTRADICTIONS_SUMMARY": str(len(reconciliation["contradictions"])),
        "UNKNOWNS_SUMMARY": str(len(reconciliation["unknowns"])),
        "STRATEGY": decision["strategy"],
        "CONFIRMATION_REFERENCE": _one_line(
            decision["authorization"]["confirmation_reference"]
        ),
        "REVISION": git["revision"] or "none",
        "BRANCH": git["branch"] or "none",
        "DIRTY_STATE": "dirty-inventoried" if git["dirty"] else "clean",
        "INVENTORY_FINGERPRINT": report["baseline"]["inventory_fingerprint"],
    }
    planned: list[tuple[Path, str]] = []
    for _, relative in CORE_ARTIFACTS:
        planned.append(
            (
                root / "docs" / "lks-sdd" / relative,
                _render_core(relative, args.project_id, args.date, intent),
            )
        )
    template_root = (
        Path(__file__).resolve().parents[1] / "assets" / "current-state-templates"
    )
    for _, relative, template_name in ADOPTION_ARTIFACTS:
        planned.append(
            (
                root / "docs" / "lks-sdd" / relative,
                _render(
                    (template_root / template_name).read_text(encoding="utf-8"),
                    replacements,
                ),
            )
        )
    manifest = _build_manifest(
        args.project_id,
        args.documentation_level,
        args.risk_profile,
        report,
        decision,
        report_hash,
        decision_hash,
        args.date,
    )
    planned.append(
        (manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    )
    for destination, _ in planned:
        _assert_destination(root, destination)
    collisions = [
        path.relative_to(root).as_posix() for path, _ in planned if path.exists()
    ]
    if collisions:
        raise AdoptionError(
            f"Colisiones documentales; no se sobrescribirá: {collisions}"
        )
    preview_hash = _preview_hash(root, planned)
    result = {
        "status": "dry-run" if args.dry_run else "materialized",
        "changed": False,
        "preview_hash": preview_hash,
        "created": [path.relative_to(root).as_posix() for path, _ in planned],
        "write_scope": [".lks-sdd/", "docs/lks-sdd/"],
        "code_changed": False,
        "baseline_freshness": "current",
    }
    if args.dry_run:
        return 0, result
    if not args.apply or not args.authorize:
        raise AdoptionError(
            "Aplicar requiere --apply y --authorize después de revisar el dry-run."
        )
    if args.preview_hash != preview_hash:
        raise AdoptionError("El preview hash no coincide; repita el dry-run.")
    unchanged, _ = compare_baseline(root, report)
    if not unchanged:
        return 3, {
            "status": "stale",
            "changed": False,
            "blockers": ["La baseline cambió después del preview."],
        }

    created_files: list[Path] = []
    created_dirs: set[Path] = set()
    try:
        for destination, content in planned:
            missing: list[Path] = []
            parent = destination.parent
            while parent != root and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.update(missing)
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            created_files.append(destination)
        validation_report, _, _ = validate_project(root)
        if not validation_report.valid:
            raise AdoptionError(
                "La baseline materializada no valida: "
                + "; ".join(validation_report.errors)
            )
    except (AdoptionError, OSError) as exc:
        for path in reversed(created_files):
            try:
                path.unlink()
            except OSError:
                pass
        for directory in sorted(
            created_dirs, key=lambda item: len(item.parts), reverse=True
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise AdoptionError(f"La materialización se revirtió: {exc}") from exc
    result.update({"status": "materialized", "changed": True})
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument(
        "--documentation-level",
        choices=("compact", "standard", "extended"),
        default="standard",
    )
    parser.add_argument(
        "--risk-profile",
        choices=("P0", "P1", "P2", "undetermined"),
        default="undetermined",
    )
    parser.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        code, result = materialize(args)
    except AdoptionError as exc:
        code, result = 2, {"status": "error", "changed": False, "error": str(exc)}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        if result.get("preview_hash"):
            print(f"preview_hash={result['preview_hash']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
