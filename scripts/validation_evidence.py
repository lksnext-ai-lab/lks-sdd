#!/usr/bin/env python3
"""Task-scoped visual evidence policy and deterministic management summaries.

The module adds derived views around the immutable EVID contract.  It never
rewrites an EVID document and its generated summaries live under the existing
administrative ``.lks-sdd/summaries`` exclusion.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

from evidence_contract import visual_gate_applicability


DEFAULT_VISUAL_POLICY = {"min_images": 1, "max_images": 5}
VISUAL_RESULTS = {"passed", "failed", "not-verified"}
VISUAL_TASK_RESULTS = VISUAL_RESULTS | {"not-applicable"}
MEANINGLESS = {"", "none", "pending", "not-run", "not-applicable", "unknown"}
AC_RE = re.compile(r"\bAC-[0-9]{3}\b")
UX_RE = re.compile(r"\bUX-[0-9]{3}\b")
VIS_RE = re.compile(r"\bVIS-[0-9]{3}\b")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


def _meaningful(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() not in MEANINGLESS


def _unique_strings(value: Any, pattern: re.Pattern[str] | None = None) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(set(value))
        and all(
            isinstance(item, str)
            and bool(item)
            and (pattern is None or pattern.fullmatch(item) is not None)
            for item in value
        )
    )


def task_contract_references(task_id: str, delivery: dict[str, Any]) -> dict[str, list[str]]:
    """Return the acceptance and UX/VIS references owned by one TASK."""

    details = delivery.get("task_details", {}).get(task_id, {})
    definitions = details.get("definition", [])
    row = definitions[0] if isinstance(definitions, list) and len(definitions) == 1 else {}
    serialized = " ".join(str(value) for value in row.values())
    return {
        "acceptance_ids": sorted(set(AC_RE.findall(str(row.get("Acceptance", ""))))),
        "ux_ids": sorted(set(UX_RE.findall(serialized))),
        "vis_ids": sorted(set(VIS_RE.findall(serialized))),
    }


def resolve_visual_policy(
    task_ids: Iterable[str], delivery: dict[str, Any]
) -> tuple[dict[str, dict[str, int]], list[str]]:
    """Use the documented global image bounds without technology-specific overrides."""
    return ({task_id: dict(DEFAULT_VISUAL_POLICY) for task_id in sorted(set(task_ids))}, [])

def validate_visual_review_v12(
    root: Path,
    value: Any,
    *,
    increment: str,
    task_ids: Iterable[str],
    delivery: dict[str, Any],
    policies: dict[str, dict[str, int]],
    expected_revision: dict[str, Any] | None,
    resolve_path: Callable[[str], tuple[Path | None, str | None]],
    image_signature: Callable[[Path], tuple[str | None, tuple[int, int] | None]],
) -> tuple[list[str], dict[str, Any] | None, list[str], list[str]]:
    """Validate the closed visual-review 1.2 contract.

    A semantically valid failed screenshot yields a failed outcome, rather
    than being rejected as malformed.  That preserves executed defect evidence
    while ensuring the parent EVID cannot be classified as verified.
    """

    root = root.resolve()
    errors: list[str] = []
    limitations: list[str] = []
    checked_files: list[str] = []
    required_top = {
        "schema_version", "increment", "status", "review_type", "reviewed_at",
        "reviewer", "revision", "task_reviews", "screenshots", "limitations",
    }
    if not isinstance(value, dict) or set(value) != required_top:
        return ["la evidencia visual no respeta el contrato cerrado 1.2"], None, [], []
    if value.get("schema_version") != "1.2":
        errors.append("schema_version debe ser 1.2")
    if value.get("increment") != increment:
        errors.append("increment no coincide")
    if value.get("status") not in VISUAL_RESULTS:
        errors.append("status visual inválido")
    if value.get("review_type") not in {"manual-browser", "automated-browser"}:
        errors.append("review_type debe ser manual-browser o automated-browser")
    if not _meaningful(value.get("reviewed_at")):
        errors.append("reviewed_at es obligatorio")
    reviewer = value.get("reviewer")
    if (
        not isinstance(reviewer, dict)
        or set(reviewer) != {"role", "alias"}
        or not _meaningful(reviewer.get("role"))
        or not _meaningful(reviewer.get("alias"))
    ):
        errors.append("reviewer debe declarar role y alias significativos")
    revision = value.get("revision")
    if not isinstance(revision, dict) or set(revision) != {
        "revision", "tree_id", "tree_sha256"
    }:
        errors.append("revision debe declarar revision, tree_id y tree_sha256")
        revision = {}
    elif not SHA_RE.fullmatch(str(revision.get("tree_sha256", ""))):
        errors.append("revision.tree_sha256 debe ser SHA-256")
    if expected_revision is not None:
        for field in ("revision", "tree_id", "tree_sha256"):
            if revision.get(field) != expected_revision.get(field):
                errors.append(f"revision.{field} no coincide con la revisión verificada")

    selected = sorted(set(task_ids))
    task_reviews = value.get("task_reviews")
    if not isinstance(task_reviews, list):
        errors.append("task_reviews debe ser una lista")
        task_reviews = []
    review_by_task: dict[str, dict[str, Any]] = {}
    for review in task_reviews:
        required = {
            "task_id", "status", "acceptance_ids", "ux_ids", "vis_ids",
            "screenshots", "not_applicable_reason",
        }
        if not isinstance(review, dict) or set(review) != required:
            errors.append("task_reviews contiene una fila inválida")
            continue
        task_id = str(review.get("task_id", ""))
        if task_id in review_by_task:
            errors.append(f"task_reviews duplica {task_id}")
            continue
        review_by_task[task_id] = review
        if review.get("status") not in VISUAL_TASK_RESULTS:
            errors.append(f"{task_id}: status visual inválido")
        if not _unique_strings(review.get("acceptance_ids"), AC_RE):
            errors.append(f"{task_id}: acceptance_ids inválidos")
        if not _unique_strings(review.get("ux_ids"), UX_RE):
            errors.append(f"{task_id}: ux_ids inválidos")
        if not _unique_strings(review.get("vis_ids"), VIS_RE):
            errors.append(f"{task_id}: vis_ids inválidos")
        if not _unique_strings(review.get("screenshots")):
            errors.append(f"{task_id}: screenshots inválidos")
    if set(review_by_task) != set(selected):
        errors.append("task_reviews debe cubrir exactamente el TASK slice")

    screenshots = value.get("screenshots")
    if not isinstance(screenshots, list):
        errors.append("screenshots debe ser una lista")
        screenshots = []
    shot_by_id: dict[str, dict[str, Any]] = {}
    digest_uses: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    screenshot_records: list[dict[str, Any]] = []
    shot_required = {
        "id", "task_ids", "acceptance_ids", "ux_ids", "vis_ids", "path", "sha256",
        "surface", "route", "prior_state", "interaction", "expected", "observed",
        "expectation_match", "theme", "viewport", "dimensions", "browser", "revision",
        "reviewed_at", "reviewer", "result", "limitations", "legibility",
        "duplicate_justification", "supersedes",
    }
    for shot in screenshots:
        if not isinstance(shot, dict) or set(shot) != shot_required:
            errors.append("screenshots contiene una fila inválida")
            continue
        shot_id = str(shot.get("id", ""))
        if not re.fullmatch(r"SHOT-[0-9]{3}", shot_id) or shot_id in shot_by_id:
            errors.append(f"ID de screenshot inválido o duplicado: {shot_id}")
            continue
        shot_by_id[shot_id] = shot
        for field, pattern in (
            ("task_ids", re.compile(r"TASK-[0-9]{3}")),
            ("acceptance_ids", AC_RE),
            ("ux_ids", UX_RE),
            ("vis_ids", VIS_RE),
        ):
            if not _unique_strings(shot.get(field), pattern):
                errors.append(f"{shot_id}: {field} inválidos")
        if not set(shot.get("task_ids", [])).issubset(selected):
            errors.append(f"{shot_id}: task_ids ajenos al TASK slice")
        for field in (
            "surface", "route", "prior_state", "interaction", "expected", "observed",
            "theme", "reviewed_at",
        ):
            if not _meaningful(shot.get(field)):
                errors.append(f"{shot_id}: {field} es obligatorio")
        if not str(shot.get("route", "")).startswith("/"):
            errors.append(f"{shot_id}: route debe ser una ruta de aplicación")
        if shot.get("result") not in VISUAL_RESULTS:
            errors.append(f"{shot_id}: result visual inválido")
        expectation_match = shot.get("expectation_match")
        if not isinstance(expectation_match, bool):
            errors.append(f"{shot_id}: expectation_match debe ser booleano")
        elif shot.get("result") == "passed" and not expectation_match:
            errors.append(f"{shot_id}: passed contradice el comportamiento observado")
        elif shot.get("result") in {"failed", "not-verified"} and expectation_match:
            errors.append(f"{shot_id}: un resultado no superado no puede declarar coincidencia")
        if shot.get("legibility") != "readable":
            errors.append(f"{shot_id}: la evidencia visual es ilegible")
        shot_limitations = shot.get("limitations")
        if not isinstance(shot_limitations, list) or not all(_meaningful(item) for item in shot_limitations):
            errors.append(f"{shot_id}: limitations debe contener textos significativos")
        else:
            limitations.extend(f"{shot_id}: {item}" for item in shot_limitations)
        if shot.get("reviewed_at") != value.get("reviewed_at") or shot.get("reviewer") != reviewer:
            errors.append(f"{shot_id}: fecha o revisor divergen de la revisión")
        if shot.get("revision") != revision:
            errors.append(f"{shot_id}: revisión o árbol divergen de la revisión")
        browser = shot.get("browser")
        if (
            not isinstance(browser, dict)
            or set(browser) != {"name", "version"}
            or not _meaningful(browser.get("name"))
            or not _meaningful(browser.get("version"))
        ):
            errors.append(f"{shot_id}: browser debe declarar name y version")
        viewport = shot.get("viewport")
        dimensions = shot.get("dimensions")
        if not isinstance(viewport, dict) or set(viewport) != {"width", "height", "dpr", "capture"}:
            errors.append(f"{shot_id}: viewport inválido")
            viewport = {}
        if not isinstance(dimensions, dict) or set(dimensions) != {"width", "height"}:
            errors.append(f"{shot_id}: dimensions inválidas")
            dimensions = {}

        path, path_error = resolve_path(str(shot.get("path", "")))
        if path_error or path is None or not path.is_file():
            errors.append(f"{shot_id}: archivo inexistente: {path_error or shot.get('path')}")
            continue
        actual_format, actual_dimensions = image_signature(path)
        if actual_format is None or actual_dimensions is None:
            errors.append(f"{shot_id}: firma PNG/JPEG inválida")
            continue
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        declared_sha = str(shot.get("sha256", "")).casefold()
        if not SHA_RE.fullmatch(declared_sha) or declared_sha != actual_sha:
            errors.append(f"{shot_id}: SHA-256 no coincide")
        if dimensions and actual_dimensions != (
            dimensions.get("width"), dimensions.get("height")
        ):
            errors.append(f"{shot_id}: dimensions no coinciden con el archivo")
        if viewport and dimensions:
            width, height, dpr = viewport.get("width"), viewport.get("height"), viewport.get("dpr")
            valid_viewport = (
                isinstance(width, int) and not isinstance(width, bool) and width > 0
                and isinstance(height, int) and not isinstance(height, bool) and height > 0
                and isinstance(dpr, (int, float)) and not isinstance(dpr, bool) and dpr > 0
            )
            if not valid_viewport:
                errors.append(f"{shot_id}: viewport contiene valores inválidos")
            elif viewport.get("capture") == "viewport" and actual_dimensions != (
                round(width * dpr), round(height * dpr)
            ):
                errors.append(f"{shot_id}: imagen incompatible con viewport, DPR y dimensiones")
            elif viewport.get("capture") == "full-page" and (
                actual_dimensions[0] != round(width * dpr)
                or actual_dimensions[1] < round(height * dpr)
            ):
                errors.append(f"{shot_id}: full-page incompatible con viewport, DPR y dimensiones")
            elif viewport.get("capture") not in {"viewport", "full-page"}:
                errors.append(f"{shot_id}: capture inválido")
        relative = path.relative_to(root).as_posix()
        checked_files.append(relative)
        supersedes = shot.get("supersedes")
        if supersedes is not None:
            if not isinstance(supersedes, dict) or set(supersedes) != {
                "evidence", "screenshot_id", "sha256"
            }:
                errors.append(f"{shot_id}: supersedes inválido")
            else:
                prior_path, prior_error = resolve_path(str(supersedes.get("evidence", "")))
                if prior_error or prior_path is None or not prior_path.is_file():
                    errors.append(f"{shot_id}: evidencia reemplazada inexistente")
                else:
                    try:
                        prior_value = json.loads(prior_path.read_text(encoding="utf-8"))
                    except (OSError, UnicodeError, json.JSONDecodeError):
                        prior_value = None
                    prior_shot = next(
                        (
                            item for item in prior_value.get("screenshots", [])
                            if isinstance(item, dict)
                            and item.get("id") == supersedes.get("screenshot_id")
                        ),
                        None,
                    ) if isinstance(prior_value, dict) else None
                    if prior_shot is None:
                        errors.append(f"{shot_id}: no existe la captura reemplazada")
                    else:
                        if prior_shot.get("sha256") != supersedes.get("sha256"):
                            errors.append(f"{shot_id}: el hash de la captura reemplazada no coincide")
                        if prior_shot.get("result") not in {"failed", "not-verified"}:
                            errors.append(f"{shot_id}: solo puede reemplazarse una captura fallida o no verificada")
                        semantic_fields = (
                            "task_ids", "acceptance_ids", "ux_ids", "vis_ids", "surface",
                            "route", "prior_state", "interaction", "theme", "viewport",
                        )
                        if any(prior_shot.get(field) != shot.get(field) for field in semantic_fields):
                            errors.append(f"{shot_id}: el reemplazo no representa el mismo estado semántico")
                        if prior_shot.get("sha256") == declared_sha:
                            errors.append(f"{shot_id}: el reemplazo debe materializar una nueva captura")
                    checked_files.append(prior_path.relative_to(root).as_posix())
        digest_uses[actual_sha].append(shot)
        screenshot_records.append(
            {
                "id": shot_id,
                "task_ids": sorted(shot.get("task_ids", [])),
                "path": relative,
                "sha256": actual_sha,
                "result": shot.get("result"),
            }
        )

    for digest, uses in digest_uses.items():
        if len(uses) <= 1:
            continue
        if not all(_meaningful(item.get("duplicate_justification")) for item in uses):
            ids = ", ".join(str(item.get("id")) for item in uses)
            errors.append(f"imágenes duplicadas sin justificación: {ids} ({digest[:12]})")

    used_shots: set[str] = set()
    task_results: list[str] = []
    for task_id in selected:
        review = review_by_task.get(task_id)
        if review is None:
            continue
        applicability = visual_gate_applicability([task_id], delivery)
        applicable = applicability.get("status") == "applicable"
        refs = task_contract_references(task_id, delivery)
        status = review.get("status")
        shot_ids = review.get("screenshots", [])
        if not applicable:
            if status != "not-applicable":
                errors.append(f"{task_id}: backend sin interfaz debe declarar not-applicable")
            reason = review.get("not_applicable_reason")
            if reason != applicability.get("reason"):
                errors.append(f"{task_id}: justificación not-applicable no es determinista")
            if shot_ids:
                errors.append(f"{task_id}: not-applicable no admite screenshots")
            task_results.append("not-applicable")
            continue
        if status == "not-applicable":
            errors.append(f"{task_id}: una TASK con UX/VIS o frontend no puede ser not-applicable")
            continue
        if review.get("not_applicable_reason") is not None:
            errors.append(f"{task_id}: una TASK aplicable no declara not_applicable_reason")
        policy = policies.get(task_id, DEFAULT_VISUAL_POLICY)
        count = len(set(shot_ids))
        if count < policy["min_images"]:
            errors.append(
                f"{task_id}: necesita al menos {policy['min_images']} imagen; recibió {count}"
            )
        if count > policy["max_images"]:
            errors.append(
                f"{task_id}: {count} imágenes exceden el máximo {policy['max_images']}; "
                "la TASK puede ser demasiado amplia: divídala o priorice la cobertura pendiente"
            )
        if not set(shot_ids).issubset(shot_by_id):
            errors.append(f"{task_id}: enlaza screenshots inexistentes")
        task_shots = [shot_by_id[item] for item in shot_ids if item in shot_by_id]
        if any(task_id not in item.get("task_ids", []) for item in task_shots):
            errors.append(f"{task_id}: una captura no conserva la TASK relacionada")
        used_shots.update(shot_ids)
        expected_acceptance = set(refs["acceptance_ids"])
        covered_acceptance = set(review.get("acceptance_ids", []))
        if not covered_acceptance or not covered_acceptance.issubset(expected_acceptance):
            errors.append(f"{task_id}: la revisión no enlaza aceptación aplicable")
        if not any(
            set(item.get("acceptance_ids", [])) & expected_acceptance
            and _meaningful(item.get("interaction"))
            for item in task_shots
        ):
            errors.append(f"{task_id}: capturas sin aceptación o interacción relacionada")
        for field in ("ux_ids", "vis_ids"):
            declared = set(review.get(field, []))
            expected = set(refs[field])
            if declared - expected:
                errors.append(f"{task_id}: {field} contiene referencias ajenas")
            if expected and declared != expected:
                errors.append(f"{task_id}: {field} no cubre las referencias TASK")
        shot_results = [item.get("result") for item in task_shots]
        derived_status = (
            "failed" if "failed" in shot_results else
            "not-verified" if "not-verified" in shot_results else "passed"
        )
        if status != derived_status:
            errors.append(f"{task_id}: status no coincide con el resultado de sus imágenes")
        task_results.append(derived_status)
    if set(shot_by_id) - used_shots:
        errors.append("hay screenshots que no demuestran ninguna TASK seleccionada")

    declared_limitations = value.get("limitations")
    if not isinstance(declared_limitations, list) or not all(_meaningful(item) for item in declared_limitations):
        errors.append("limitations debe ser una lista de textos significativos")
    else:
        limitations.extend(str(item) for item in declared_limitations)
    derived_overall = (
        "failed" if "failed" in task_results else
        "not-verified" if "not-verified" in task_results else "passed"
    )
    if value.get("status") != derived_overall:
        errors.append("status global no coincide con los resultados TASK")
    if errors:
        return list(dict.fromkeys(errors)), None, limitations, list(dict.fromkeys(checked_files))
    outcome = {
        "name": "visual-browser-review",
        "status": derived_overall,
        "schema_version": "1.2",
        "task_coverage": [
            {
                "task_id": task_id,
                "status": review_by_task[task_id]["status"],
                "image_count": len(set(review_by_task[task_id]["screenshots"])),
            }
            for task_id in selected
        ],
        "screenshots": sorted(screenshot_records, key=lambda item: item["id"]),
        "policy": {task_id: policies.get(task_id, DEFAULT_VISUAL_POLICY) for task_id in selected},
        "revision": revision,
    }
    return [], outcome, limitations, list(dict.fromkeys(checked_files))


def load_evidence_index(root: Path) -> dict[str, list[dict[str, Any]]]:
    """Read each immutable EVID at most once and index it by TASK."""

    result: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    evidence_root = root / "docs/lks-sdd/evidence"
    for path in sorted(evidence_root.glob("EVID-*.json")) if evidence_root.is_dir() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict) or value.get("evidence_id") != path.stem:
            continue
        value = {**value, "_path": path.relative_to(root).as_posix()}
        for task_id in value.get("task_ids", []):
            if isinstance(task_id, str):
                result[task_id].append(value)
    return dict(result)


def task_health(
    task_id: str,
    evidences: list[dict[str, Any]],
    active_findings: list[dict[str, str]],
    manifest_verification: dict[str, Any],
) -> dict[str, Any]:
    """Keep historical verification and present health as separate axes."""

    historical = [
        item for item in evidences
        if item.get("classification") in {"verified", "verified-with-reservations"}
    ]
    current_ids = set(manifest_verification.get("evidence_ids", []))
    current_verified = (
        task_id in manifest_verification.get("task_ids", [])
        and manifest_verification.get("status") == "verified"
        and bool(current_ids)
    )
    if historical and active_findings:
        current = "compromised"
        next_action = "Corregir los hallazgos abiertos y ejecutar una nueva verificación."
    elif historical and not current_verified:
        current = "pending-reverification"
        next_action = "Ejecutar la re-verificación gobernada del TASK slice."
    elif historical and current_verified:
        current = "healthy"
        next_action = "Mantener la evidencia y vigilar hallazgos posteriores."
    else:
        current = "not-verified"
        next_action = "Completar implementación y verificación."
    return {
        "historical_verification": "verified" if historical else "not-verified",
        "current_health": current,
        "open_findings": [item.get("ID") for item in active_findings if item.get("ID")],
        "pending_reverification": current in {"compromised", "pending-reverification"},
        "next_action": next_action,
    }


def derive_task_summaries(
    root: Path,
    manifest: dict[str, Any],
    delivery: dict[str, Any],
    *,
    evidence_index: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Generate every TASK card deterministically in one pass."""

    indexed = evidence_index if evidence_index is not None else load_evidence_index(root)
    summaries: dict[str, dict[str, Any]] = {}
    manifest_verification = manifest.get("verification", {})
    if not isinstance(manifest_verification, dict):
        manifest_verification = {}
    for task_id, task in sorted(delivery.get("tasks", {}).items()):
        details = delivery.get("task_details", {}).get(task_id, {})
        definition_rows = details.get("definition", [])
        definition = definition_rows[0] if len(definition_rows) == 1 else {}
        plan_rows = details.get("plan", [])
        plan = plan_rows[0] if len(plan_rows) == 1 else {}
        findings = [
            item for item in details.get("problems", details.get("issues", []))
            if item.get("State") == "active"
        ]
        evidence = indexed.get(task_id, [])
        latest = evidence[-1] if evidence else {}
        checks = [item for item in latest.get("checks", []) if isinstance(item, dict)]
        technical = [item for item in checks if item.get("name") != "visual-browser-review"]
        visual = next((item for item in checks if item.get("name") == "visual-browser-review"), None)
        visual_coverage: dict[str, Any]
        if isinstance(visual, dict):
            task_row = next(
                (item for item in visual.get("task_coverage", []) if item.get("task_id") == task_id),
                {},
            )
            visual_coverage = {
                "status": task_row.get("status", visual.get("status")),
                "images": int(task_row.get("image_count", len(visual.get("screenshots", [])))),
            }
        else:
            applicability = visual_gate_applicability([task_id], delivery)
            visual_coverage = {
                "status": "not-applicable" if applicability.get("status") == "not-applicable" else "not-verified",
                "images": 0,
                "reason": applicability.get("reason"),
            }
        health = task_health(task_id, evidence, findings, manifest_verification)
        passed = [item.get("name") for item in technical if item.get("status") == "passed"]
        not_passed = [item.get("name") for item in technical if item.get("status") != "passed"]
        summaries[task_id] = {
            "schema_version": "1.0",
            "kind": "derived-task-evidence-summary",
            "task_id": task_id,
            "objective": definition.get("Objective") or task.get("Title") or "pending",
            "code_state": task.get("Workflow state", "unknown"),
            "tests_executed": [
                {"name": item.get("name"), "status": item.get("status"), "command": item.get("command")}
                for item in technical
            ],
            "technical_result": latest.get("classification", "not-run"),
            "visual_coverage": visual_coverage,
            "behavior_demonstrated": sorted(str(item) for item in passed if item),
            "behavior_not_demonstrated": sorted(str(item) for item in not_passed if item),
            "findings": [
                {"id": item.get("ID"), "description": item.get("Description"), "impact": item.get("Impact")}
                for item in findings
            ],
            "limitations": list(latest.get("limitations", [])),
            "canonical_evidence": [item.get("evidence_id") for item in evidence],
            "verified_revision": latest.get("revision"),
            "next_action": health["next_action"],
            "health": health,
            "derived_from": {
                "task_detail": task.get("Detail"),
                "required_tests": plan.get("Tests"),
                "evidence": [item.get("_path") for item in evidence],
            },
        }
    return summaries


def summary_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


__all__ = [
    "DEFAULT_VISUAL_POLICY",
    "derive_task_summaries",
    "load_evidence_index",
    "resolve_visual_policy",
    "summary_bytes",
    "task_contract_references",
    "task_health",
    "validate_visual_review_v12",
]
