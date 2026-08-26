#!/usr/bin/env python3
"""Assess, confirm and authorize LKS-SDD 1.3/1.4 implementation planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from delivery_engine import delivery_readiness, parse_tables, validate_delivery_contract
from planning_engine import (
    AUTHORIZATION_HEADERS,
    PLANNING_TARGET_HEADERS,
    assess_authorization,
    assess_planning,
    expand_ids,
    next_tasks,
)
from validate_project import validate_project
from task_tracking_engine import assess_tracking


class PlanningCommandError(ValueError):
    """Expected planning command failure."""


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    try:
        original = path.read_bytes()
        value = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanningCommandError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict) or value.get("schema_version") not in {"1.3", "1.4", "1.5"}:
        raise PlanningCommandError(
            "La gestión integral de planificación requiere schema 1.3 o 1.4."
        )
    return path, value, original


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> str:
    expected = {
        "ART-PLANNING": "docs/lks-sdd/04-delivery/planning-coverage.md",
    }.get(artifact_id)
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            observed = str(item.get("path", ""))
            if expected is not None and observed != expected:
                raise PlanningCommandError(
                    f"{artifact_id} debe usar la ruta canónica {expected}."
                )
            return observed
    raise PlanningCommandError(f"Falta {artifact_id} en el índice.")


def _cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return [item.strip() for item in stripped[1:-1].split("|")]


def _replace_row(
    text: str, headers: tuple[str, ...], row_id: str, updates: dict[str, str]
) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        cursor = index + 2
        while cursor < len(lines):
            values = _cells(lines[cursor])
            if values is None:
                break
            if len(values) == len(headers) and values[0] == row_id:
                row = dict(zip(headers, values, strict=True))
                row.update(updates)
                lines[cursor] = "| " + " | ".join(row[item] for item in headers) + " |"
                return "\n".join(lines) + "\n"
            cursor += 1
    raise PlanningCommandError(f"No se encontró la fila {row_id}.")


def _append_row(text: str, headers: tuple[str, ...], values: list[str]) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _cells(line) != list(headers):
            continue
        cursor = index + 2
        while cursor < len(lines) and _cells(lines[cursor]) is not None:
            cursor += 1
        lines.insert(cursor, "| " + " | ".join(values) + " |")
        return "\n".join(lines) + "\n"
    raise PlanningCommandError(f"No se encontró la tabla {headers[0]}.")


def _frontmatter_update(text: str, change_date: str, *, confirmed: bool = False) -> str:
    updated, count = re.subn(
        r'^last_updated: "[0-9]{4}-[0-9]{2}-[0-9]{2}"$',
        f'last_updated: "{change_date}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise PlanningCommandError("No se pudo actualizar last_updated.")
    if confirmed:
        updated = re.sub(
            r"^status: (?:draft|proposed)$", "status: confirmed", updated,
            count=1, flags=re.MULTILINE,
        )
    return updated


def _safe_cell(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized or any(marker in normalized for marker in ("|", "\r", "\n")):
        raise PlanningCommandError(f"{label} es obligatorio y debe caber en una celda Markdown.")
    return normalized


def _change_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise PlanningCommandError("--date debe usar AAAA-MM-DD.") from exc


def _preview_hash(*values: bytes, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(hashlib.sha256(value).digest())
    digest.update(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def _apply_atomic(paths: list[Path], originals: list[bytes], replacements: list[bytes]) -> None:
    temporaries: list[Path] = []
    replaced = 0
    try:
        for path, content in zip(paths, replacements, strict=True):
            temporary = path.with_name(path.name + ".lks-sdd-planning.tmp")
            with temporary.open("xb") as stream:
                stream.write(content)
            temporaries.append(temporary)
        for path, original in zip(paths, originals, strict=True):
            if path.read_bytes() != original:
                raise PlanningCommandError(f"{path.name} cambió después del preview.")
        for path, temporary in zip(paths, temporaries, strict=True):
            os.replace(temporary, path)
            replaced += 1
    except (OSError, PlanningCommandError):
        for index in range(replaced):
            paths[index].write_bytes(originals[index])
        for temporary in temporaries[replaced:]:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise


def _confirm(
    root: Path, manifest: dict[str, Any], args: argparse.Namespace
) -> tuple[Path, bytes, bytes, dict[str, Any], dict[str, Any]]:
    if manifest.get("schema_version") in {"1.4", "1.5"}:
        from task_tracking_engine import validate_tracking_contract

        tracking = validate_tracking_contract(root, manifest)
        if tracking.get("mode") == "pending":
            raise PlanningCommandError(
                "Antes de confirmar la planificación debe elegir repository-only o jira-hybrid."
            )
        if tracking.get("errors"):
            raise PlanningCommandError(
                "El contrato de tracking debe ser válido antes de confirmar la "
                "planificación: " + "; ".join(tracking["errors"])
            )
        if tracking.get("binding", {}).get("State") != "confirmed":
            raise PlanningCommandError(
                "Antes de confirmar la planificación debe confirmar explícitamente "
                "repository-only o jira-hybrid mediante una decisión ADR."
            )
    planning = assess_planning(root, manifest, args.increment, release=args.release)
    remaining = [gap for gap in planning["gaps"] if gap.get("kind") != "human-confirmation"]
    incremental = planning.get("policy") == "incremental-authorized"
    confirmation_blocking_kinds = {
        "planning-target",
        "target-field",
        "target-scope",
        "incremental-decision",
        "migration-required",
        "index-target",
        "change-record-required",
    }
    confirmation_blockers = (
        [
            gap
            for gap in remaining
            if gap.get("kind") in confirmation_blocking_kinds
        ]
        if incremental
        else remaining
    )
    if incremental and not planning.get("tasks", {}).get("executable"):
        confirmation_blockers.append(
            {
                "kind": "executable-slice",
                "explanation": "La planificación incremental necesita al menos una tarea ejecutable antes de confirmarse.",
            }
        )
    if planning["integrity"] != "valid" or confirmation_blockers:
        raise PlanningCommandError(
            "La planificación no puede confirmarse: "
            + "; ".join(
                planning["integrity_errors"]
                + [
                    str(gap.get("explanation"))
                    for gap in confirmation_blockers
                ]
            )
        )
    change_date = _change_date(args.date)
    target_id = planning["target"]["id"]
    planning_path = root / _artifact_path(manifest, "ART-PLANNING")
    original = planning_path.read_bytes()
    text = original.decode("utf-8")
    updated = _replace_row(text, PLANNING_TARGET_HEADERS, target_id, {"State": "confirmed"})
    updated = _frontmatter_update(updated, change_date, confirmed=True)
    manifest_new = json.loads(json.dumps(manifest))
    target_type = planning["target"]["type"]
    target_rows = [
        row for actual, rows in parse_tables(updated)
        if actual == PLANNING_TARGET_HEADERS for row in rows if row.get("Target") == target_id
    ]
    target = target_rows[0]
    decision_ids, _ = expand_ids(target.get("Decision", ""))
    manifest_new["planning"].update({
        "target_type": target_type,
        "target_id": target_id,
        "policy": target["Planning policy"],
        "policy_decision": next((item for item in decision_ids if item.startswith("ADR-")), None),
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "confirmed_by_role": _safe_cell("--actor-role", args.actor_role),
        "confirmed_on": change_date,
        "last_change": max(
            (
                str(item["id"])
                for item in planning.get("change_impact", {}).get(
                    "applicable_confirmed_changes", []
                )
                if item.get("id")
            ),
            default=manifest_new["planning"].get("last_change"),
        ),
    })
    tracking_invalidated = False
    if manifest.get("schema_version") in {"1.4", "1.5"}:
        previous_planning = manifest.get("planning", {})
        fingerprints_changed = (
            previous_planning.get("specification_fingerprint")
            != planning["specification_fingerprint"]
            or previous_planning.get("planning_fingerprint")
            != planning["planning_fingerprint"]
        )
        tracking_index = manifest_new.get("task_tracking", {})
        if (
            fingerprints_changed
            and tracking_index.get("mode") == "jira-hybrid"
            and tracking_index.get("sync_status") == "in-sync"
        ):
            tracking_index["projection_fingerprint"] = None
            tracking_index["sync_status"] = "out-of-sync"
            tracking_invalidated = True
    payload = {
        "operation": "confirm-planning", "target": target_id,
        "actor_role": _safe_cell("--actor-role", args.actor_role),
        "date": change_date,
        "planning_policy": target["Planning policy"],
        "planning_status": "partial" if remaining else "complete",
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "tracking_invalidated": tracking_invalidated,
    }
    return planning_path, original, updated.encode("utf-8"), manifest_new, payload


def _authorize(
    root: Path, manifest: dict[str, Any], args: argparse.Namespace
) -> tuple[Path, bytes, bytes, dict[str, Any], dict[str, Any]]:
    planning = assess_planning(root, manifest, args.increment, release=args.release)
    if planning["integrity"] != "valid":
        raise PlanningCommandError("La planificación es inválida; no se puede autorizar.")
    if planning["status"] != "complete" and not planning["partial_implementation_policy_satisfied"]:
        raise PlanningCommandError(
            "La planificación no está completa y no existe una política incremental confirmada."
        )
    tasks = sorted(set(args.task or []))
    if not tasks:
        raise PlanningCommandError("Autorizar requiere al menos un --task TASK-###.")
    delivery = delivery_readiness(root, manifest, args.increment, task_ids=tasks)
    if delivery["status"] != "ready":
        raise PlanningCommandError("La porción seleccionada no está ready: " + "; ".join(delivery["blockers"]))
    if manifest.get("schema_version") in {"1.4", "1.5"}:
        tracking = assess_tracking(root, manifest, tasks)
        if tracking.get("blockers"):
            raise PlanningCommandError(
                "El tracking operativo no permite autorizar todavía: "
                + "; ".join(tracking["blockers"])
            )
    if not re.fullmatch(r"AUTH-[0-9]{3}", args.authorization_id):
        raise PlanningCommandError("--authorization-id debe usar AUTH-###.")
    if not re.fullmatch(r"ADR-[0-9]{3}", args.decision):
        raise PlanningCommandError("--decision debe usar una ADR-### confirmada.")
    if args.decision not in planning.get("confirmed_decisions", []):
        raise PlanningCommandError(
            "--decision debe referenciar una ADR-### confirmada, no una propuesta."
        )
    if any(item.get("authorization_id") == args.authorization_id for item in manifest.get("authorizations", [])):
        raise PlanningCommandError(f"Ya existe {args.authorization_id}.")
    change_date = _change_date(args.date)
    actor_role = _safe_cell("--actor-role", args.actor_role)
    constraints = _safe_cell("--constraints", args.constraints)
    target = planning["target"]
    release = target.get("release")
    if not release:
        raise PlanningCommandError("La autorización de implementación requiere una release explícita.")
    planning_path = root / _artifact_path(manifest, "ART-PLANNING")
    original = planning_path.read_bytes()
    updated = _append_row(
        original.decode("utf-8"), AUTHORIZATION_HEADERS,
        [
            args.authorization_id, "authorized", target["id"], args.increment,
            release, ", ".join(tasks), planning["specification_fingerprint"],
            planning["planning_fingerprint"], actor_role, change_date,
            args.decision, constraints,
        ],
    )
    updated = _frontmatter_update(updated, change_date)
    authorization = {
        "authorization_id": args.authorization_id,
        "state": "authorized",
        "target": target["id"],
        "increment": args.increment,
        "release": release,
        "task_ids": tasks,
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "authorized_by_role": actor_role,
        "authorized_on": change_date,
        "decision": args.decision,
        "constraints": constraints,
    }
    manifest_new = json.loads(json.dumps(manifest))
    manifest_new["authorizations"].append(authorization)
    payload = {"operation": "authorize-implementation", **authorization, "constraints": constraints}
    return planning_path, original, updated.encode("utf-8"), manifest_new, payload


def _transition_summary(
    command: str,
    *,
    preview: bool,
    payload: dict[str, Any],
    planning: dict[str, Any],
) -> dict[str, Any]:
    target = str(payload.get("target", planning.get("target", {}).get("id", "target")))
    all_tasks = list(planning.get("tasks", {}).get("all", []))
    selected = list(payload.get("task_ids", []))
    remaining = sorted(set(all_tasks) - set(selected)) if selected else all_tasks
    if command == "confirm":
        partial = payload.get("planning_status") == "partial"
        return {
            "where_we_are": (
                "planning-confirmation-preview"
                if preview
                else "planning-partial-confirmed"
                if partial
                else "planning-complete"
            ),
            "completed": [] if preview else [
                f"La planificación {'parcial' if partial else 'integral'} de {target} quedó confirmada y ligada a fingerprints."
            ],
            "in_progress": [],
            "pending": (
                [
                    f"{target} conserva huecos de cobertura; solo puede autorizarse una porción TASK explícita.",
                    f"Tareas pendientes de autorización de implementación: {', '.join(all_tasks) or 'ninguna definida'}.",
                ]
                if partial
                else [
                    f"Tareas pendientes de autorización de implementación: {', '.join(all_tasks) or 'ninguna definida'}."
                ]
            ),
            "blocked": [],
            "next_step": (
                "Revisar el preview y confirmar o corregir la descomposición."
                if preview
                else "Seleccionar y autorizar solo una porción ready, manteniendo visible la planificación parcial."
                if partial
                else "Seleccionar la porción inicial ready y registrar una autorización explícita."
            ),
            "human_decision": (
                "Confirmar o revisar la política y la descomposición mostradas."
                if preview
                else "Autorizar, diferir o limitar la porción inicial sin presentar la release como completamente planificada."
                if partial
                else "Autorizar, diferir o limitar la porción inicial."
            ),
        }
    authorization_id = str(payload.get("authorization_id", "AUTH pendiente"))
    return {
        "where_we_are": "implementation-authorization-preview" if preview else "implementation-authorized",
        "completed": [] if preview else [f"{authorization_id} autoriza: {', '.join(selected)}."],
        "in_progress": [],
        "pending": [f"Tareas del plan fuera de esta autorización: {', '.join(remaining)}."] if remaining else [],
        "blocked": [],
        "next_step": (
            "Revisar alcance, rol, decisión, restricciones y fingerprints antes de aplicar."
            if preview
            else "Iniciar únicamente las tareas autorizadas y crear EXEC/CKPT en el mismo apply."
        ),
        "human_decision": (
            "Confirmar o rechazar esta autorización delimitada."
            if preview
            else "Ninguna nueva; respetar los límites de la autorización registrada."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--release")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("assess", "next"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--json", action="store_true", dest="as_json")
    confirm = subparsers.add_parser("confirm")
    confirm.add_argument("--date", required=True)
    confirm.add_argument("--actor-role", required=True)
    authorize = subparsers.add_parser("authorize")
    authorize.add_argument("--authorization-id", required=True)
    authorize.add_argument("--task", action="append")
    authorize.add_argument("--date", required=True)
    authorize.add_argument("--actor-role", required=True)
    authorize.add_argument("--decision", required=True)
    authorize.add_argument("--constraints", required=True)
    for sub in (confirm, authorize):
        mode = sub.add_mutually_exclusive_group(required=True)
        mode.add_argument("--preview", action="store_true")
        mode.add_argument("--apply", action="store_true")
        sub.add_argument("--authorize", action="store_true")
        sub.add_argument("--preview-hash")
        sub.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    root = args.project_root.expanduser().resolve()
    try:
        manifest_path, manifest, manifest_original = _load_manifest(root)
        planning = assess_planning(root, manifest, args.increment, release=args.release)
        if args.command == "assess":
            result = planning
            code = 0 if planning["status"] == "complete" else 3
        elif args.command == "next":
            delivery = validate_delivery_contract(root, manifest)
            result = next_tasks(delivery, planning)
            result["planning_status"] = planning["status"]
            code = 0
        else:
            planning_path, planning_original, planning_new, manifest_new, payload = (
                _confirm(root, manifest, args)
                if args.command == "confirm"
                else _authorize(root, manifest, args)
            )
            manifest_new_bytes = (json.dumps(manifest_new, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            preview_hash = _preview_hash(
                planning_original, manifest_original, payload=payload
            )
            result = {
                "status": "preview" if args.preview else "applied",
                "changed": False, "preview_hash": preview_hash, **payload,
            }
            result["transition_summary"] = _transition_summary(
                args.command,
                preview=args.preview,
                payload=payload,
                planning=planning,
            )
            if args.preview:
                code = 0
            else:
                if not args.authorize or args.preview_hash != preview_hash:
                    raise PlanningCommandError(
                        "Aplicar requiere --authorize y el preview hash vigente."
                    )
                _apply_atomic(
                    [planning_path, manifest_path],
                    [planning_original, manifest_original],
                    [planning_new, manifest_new_bytes],
                )
                report, _, _ = validate_project(root)
                post = assess_planning(root, manifest_new, args.increment, release=args.release)
                authorization = (
                    assess_authorization(manifest_new, post, args.task or [])
                    if args.command == "authorize" else None
                )
                valid = report.valid and (
                    (
                        post["status"] == "complete"
                        or post.get("partial_implementation_policy_satisfied")
                        is True
                    )
                    if args.command == "confirm"
                    else authorization is not None
                    and authorization["status"] == "authorized"
                )
                if not valid:
                    _apply_atomic(
                        [planning_path, manifest_path],
                        [planning_new, manifest_new_bytes],
                        [planning_original, manifest_original],
                    )
                    raise PlanningCommandError(
                        "La operación se revirtió: " + "; ".join(report.errors + post["integrity_errors"])
                    )
                result.update({"status": "applied", "changed": True})
                code = 0
        if getattr(args, "as_json", False):
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(result.get("status", "ok"))
            if result.get("preview_hash"):
                print(f"preview_hash={result['preview_hash']}")
        return code
    except (OSError, PlanningCommandError, ValueError) as exc:
        print(json.dumps({"status": "error", "changed": False, "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
