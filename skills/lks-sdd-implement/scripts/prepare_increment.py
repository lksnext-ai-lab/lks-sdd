#!/usr/bin/env python3
"""Plan or materialize one ready LKS-SDD task slice from locked profiles."""

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

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(
    0,
    str(
        PLUGIN_ROOT
        / "skills"
        / "lks-sdd-assess-readiness"
        / "scripts"
    ),
)

from assess_readiness import assess  # noqa: E402
from contract_engine import build_project_model, resolve_active_increment  # noqa: E402
from delivery_engine import (  # noqa: E402
    delivery_readiness,
    parse_tables,
    repository_revision,
    validate_delivery_contract,
)
from planning_engine import assess_authorization, assess_planning, next_tasks  # noqa: E402
from manage_tasks import (  # noqa: E402
    _append_table_row,
    _replace_frontmatter_date,
    _replace_table_row,
    _single_detail_row,
    TaskManagementError,
    TASK_DETAIL_HEADERS,
    TASK_DETAIL_HEADERS_V13,
    TASK_HEADERS,
)
from profile_registry import load_profile_bundle, profile_source_files  # noqa: E402
from validate_reference_profile import validate_profile  # noqa: E402
from validate_project import validate_project  # noqa: E402


class PreparationError(Exception):
    """Expected, actionable preparation failure."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _safe_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise PreparationError(f"La raíz no es una carpeta: {root}")
    return root


def _load_manifest(root: Path) -> tuple[dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if _is_link_like(current):
            raise PreparationError(
                "No se lee project.json mediante symlinks o junctions."
            )
    try:
        original = path.read_bytes()
        value = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreparationError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict):
        raise PreparationError("project.json debe ser un objeto.")
    return value, original


def _assert_safe_destination(root: Path, destination: Path) -> None:
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise PreparationError(
            f"Destino fuera de la raíz autorizada: {destination}"
        ) from exc
    current = destination
    while current != root:
        if _is_link_like(current):
            raise PreparationError(
                f"No se escribe mediante symlinks o junctions: {current}"
            )
        current = current.parent


def _source_entries(origin: Path, target: Path) -> list[tuple[Path, Path]]:
    if origin.is_file() and not origin.is_symlink():
        return [(origin, target)]
    if not origin.is_dir() or origin.is_symlink():
        raise PreparationError(f"Fuente de perfil ausente o enlazada: {origin}")
    return [
        (path, target / path.relative_to(origin))
        for path in profile_source_files(origin)
    ]


def _binding_contracts(
    manifest: dict[str, Any],
    delivery: dict[str, Any],
) -> list[dict[str, Any]]:
    technology = manifest.get("technology", {})
    if str(manifest.get("schema_version")) in {"1.2", "1.3", "1.4", "1.5"}:
        by_id = {
            item.get("binding_id"): item
            for item in technology.get("profile_bindings", [])
            if isinstance(item, dict)
        }
        return [
            by_id[binding_id]
            for binding_id in delivery.get("binding_ids", [])
            if binding_id in by_id
        ]
    selected = technology.get("selected_profile")
    if not isinstance(selected, str):
        return []
    return [
        {
            "binding_id": "BIND-000",
            "unit_id": "UNIT-000",
            "unit_path": ".",
            "profile_id": selected,
            "profile_scope": "system",
            "selection_decision": technology.get("selection_decision"),
            "lock_path": ".lks-sdd/profile.lock.json",
            "state": "confirmed",
        }
    ]


def _planned_files(
    root: Path,
    bindings: list[dict[str, Any]],
    *,
    mode: str = "new-project",
) -> tuple[
    list[tuple[Path, bytes]],
    list[str],
    list[str],
    list[dict[str, str]],
]:
    candidates: dict[Path, bytes] = {}
    preserved: list[str] = []
    manual_integrations: list[str] = []
    lock_details: list[dict[str, str]] = []
    for binding in bindings:
        binding_id = str(binding["binding_id"])
        profile_id = str(binding["profile_id"])
        unit_path = Path(str(binding.get("unit_path", ".")))
        if unit_path.is_absolute() or ".." in unit_path.parts:
            raise PreparationError(
                f"{binding_id}: unit_path no es seguro: {unit_path}"
            )
        bundle = load_profile_bundle(profile_id)
        if bundle.root is None:
            raise PreparationError(f"Perfil no resoluble: {profile_id}")
        if mode == "adoption":
            from adoption_preparation import adoption_resources
            try:
                candidates.update(adoption_resources(root, binding, bundle.driver))
            except ValueError as exc:
                raise PreparationError(str(exc)) from exc
        elif mode != "new-project":
            raise PreparationError("Modo de preparación desconocido.")
        for source in ([] if mode == "adoption" else bundle.driver["prepare"]["sources"]):
            target = Path(str(source["to"]))
            if target.is_absolute() or ".." in target.parts:
                raise PreparationError(
                    f"{binding_id}: destino de driver inseguro: {target}"
                )
            origin = (PLUGIN_ROOT / str(source["from"])).resolve()
            try:
                origin.relative_to(PLUGIN_ROOT.resolve())
            except ValueError as exc:
                raise PreparationError(
                    f"{binding_id}: fuente fuera del plugin."
                ) from exc
            destination_base = root / unit_path / target
            for file_path, destination in _source_entries(
                origin, destination_base
            ):
                _assert_safe_destination(root, destination)
                content = file_path.read_bytes()
                prior = candidates.get(destination)
                if prior is not None and prior != content:
                    raise PreparationError(
                        "Dos bindings o fuentes colisionan con contenido "
                        f"distinto en {destination.relative_to(root).as_posix()}."
                    )
                candidates[destination] = content

        descriptor_path = (
            root / ".lks-sdd" / "profiles" / f"{binding_id}.profile.json"
        )
        lock_path = root / str(binding["lock_path"])
        descriptor = (bundle.root / "technology-profile.yaml").read_bytes()
        lock = (bundle.root / "technology-profile.lock.json").read_bytes()
        candidates[descriptor_path] = descriptor
        candidates[lock_path] = lock
        if bundle.driver.get("variant"):
            import tempfile
            from technology_resolution import inspect_dependencies
            unit_root = root / unit_path
            # Inspect the exact prospective files, including preserved consumer
            # dependency inputs. Preview performs no installation or execution.
            with tempfile.TemporaryDirectory(prefix="lks-dependency-preview-") as temporary:
                prospective = Path(temporary)
                current = inspect_dependencies(unit_root)
                for relative in current["input_hashes"]:
                    target = prospective / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((unit_root / relative).read_bytes())
                for destination, content in candidates.items():
                    try:
                        relative = destination.relative_to(unit_root)
                    except ValueError:
                        continue
                    if relative.name not in __import__("technology_resolution").INPUT_NAMES:
                        continue
                    target = prospective / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                snapshot = inspect_dependencies(prospective)
            candidates[root / ".lks-sdd/profiles" / f"{binding_id}.resolution.json"] = (json.dumps(snapshot, sort_keys=True, indent=2) + "\n").encode()
        lock_details.append(
            {
                "binding_id": binding_id,
                "sha256": hashlib.sha256(lock).hexdigest(),
            }
        )

    planned: list[tuple[Path, bytes]] = []
    for destination, content in sorted(
        candidates.items(), key=lambda item: item[0].as_posix()
    ):
        _assert_safe_destination(root, destination)
        relative = destination.relative_to(root).as_posix()
        if destination.exists():
            if not destination.is_file():
                raise PreparationError(
                    f"Colisión con una ruta no regular: {relative}"
                )
            if destination.read_bytes() == content:
                preserved.append(relative)
                continue
            if destination.name == ".gitignore":
                manual_integrations.append(relative)
                continue
            raise PreparationError(
                f"Colisión; no se sobrescribirá {relative}."
            )
        planned.append((destination, content))
    return planned, preserved, manual_integrations, lock_details


def _preview_hash(
    root: Path,
    planned: list[tuple[Path, bytes]],
    manifest_before: bytes,
    input_fingerprint: str,
    task_ids: list[str],
    replacements: list[tuple[Path, bytes, bytes]],
) -> str:
    digest = hashlib.sha256()
    digest.update(b".lks-sdd/project.json\0")
    digest.update(hashlib.sha256(manifest_before).digest())
    digest.update(b"readiness-input-fingerprint\0")
    digest.update(input_fingerprint.encode("ascii"))
    for task_id in sorted(task_ids):
        digest.update(task_id.encode("ascii"))
        digest.update(b"\0")
    for destination, content in planned:
        digest.update(destination.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
    for destination, original, content in replacements:
        digest.update(destination.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0replace\0")
        digest.update(hashlib.sha256(original).digest())
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def _artifact_path(manifest: dict[str, Any], artifact_id: str) -> Path:
    expected = {
        "ART-TASKS": "docs/lks-sdd/04-delivery/tasks.md",
    }.get(artifact_id)
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            observed = str(item.get("path", ""))
            if expected is not None and observed != expected:
                raise PreparationError(
                    f"{artifact_id} debe usar la ruta canónica {expected}."
                )
            return Path(observed)
    raise PreparationError(f"Falta {artifact_id} en el índice.")


def _task_replacements(
    root: Path,
    manifest: dict[str, Any],
    task_ids: list[str],
    revision: dict[str, Any],
    transition_date: str,
    actor: str,
    continuity: dict[str, str] | None = None,
) -> list[tuple[Path, bytes, bytes]]:
    if not task_ids:
        return []
    try:
        normalized_date = date.fromisoformat(transition_date).isoformat()
    except ValueError as exc:
        raise PreparationError("--date debe usar AAAA-MM-DD.") from exc
    if not actor.strip() or any(marker in actor for marker in ("|", "\r", "\n")):
        raise PreparationError("--actor no puede estar vacío ni alterar tablas Markdown.")
    board_path = root / _artifact_path(manifest, "ART-TASKS")
    board_original = board_path.read_bytes()
    board_text = board_original.decode("utf-8")
    replacements: list[tuple[Path, bytes, bytes]] = []
    branch = str(revision.get("branch") or "not-applicable")
    revision_start = str(revision["revision"])
    for task_id in task_ids:
        detail_path = (
            root
            / "docs"
            / "lks-sdd"
            / "04-delivery"
            / "tasks"
            / f"{task_id}.md"
        )
        try:
            detail_original = detail_path.read_bytes()
            detail_text = detail_original.decode("utf-8")
            execution_headers = TASK_DETAIL_HEADERS["execution"]
            current = _single_detail_row(detail_text, execution_headers)
        except (OSError, UnicodeError, ValueError) as exc:
            raise PreparationError(f"No se puede preparar el seguimiento de {task_id}: {exc}") from exc
        if current.get("Workflow state") != "ready":
            raise PreparationError(
                f"{task_id} debe permanecer ready hasta aplicar el preview; "
                f"está {current.get('Workflow state')}."
            )
        board_text = _replace_table_row(
            board_text,
            TASK_HEADERS,
            task_id,
            {
                "Workflow state": "in-progress",
                "Health": current.get("Health", "unknown"),
                "Progress": current.get("Progress", "0"),
                "Blockers": "none",
                "Updated": normalized_date,
            },
        )
        detail_text = _replace_table_row(
            detail_text,
            execution_headers,
            "ready",
            {
                "Workflow state": "in-progress",
                "Health": current.get("Health", "unknown"),
                "Progress": current.get("Progress", "0"),
                "Branch": branch,
                "Revision start": revision_start,
                "Updated": normalized_date,
            },
        )
        detail_text = _append_table_row(
            detail_text,
            TASK_DETAIL_HEADERS["history"],
            [
                normalized_date,
                "ready",
                "in-progress",
                "Authorized implementation preparation applied",
                actor.strip(),
                "not-applicable",
            ],
        )
        if continuity is not None:
            continuity_headers = TASK_DETAIL_HEADERS_V13["continuity"]
            current_continuity = _single_detail_row(
                detail_text, continuity_headers
            )
            detail_text = _replace_table_row(
                detail_text,
                continuity_headers,
                current_continuity["Definition status"],
                {
                    "Current checkpoint": continuity["checkpoint"],
                    "Authorization": continuity["authorization"],
                    "Authorization scope": continuity["scope"],
                    "Specification fingerprint": continuity[
                        "specification_fingerprint"
                    ],
                    "Planning fingerprint": continuity[
                        "planning_fingerprint"
                    ],
                    "Next safe action": continuity["next_safe_action"],
                },
            )
        detail_text = _replace_frontmatter_date(detail_text, normalized_date)
        replacements.append(
            (detail_path, detail_original, detail_text.encode("utf-8"))
        )
    board_text = _replace_frontmatter_date(board_text, normalized_date)
    replacements.insert(
        0, (board_path, board_original, board_text.encode("utf-8"))
    )
    return replacements


def _current_input_fingerprint(root: Path, increment: str) -> str:
    model = build_project_model(root)
    return resolve_active_increment(model, increment).fingerprint


def _next_indexed_id(values: list[str], prefix: str) -> str:
    used = {
        int(match.group(1))
        for value in values
        if (match := re.fullmatch(rf"{re.escape(prefix)}-([0-9]{{3}})", value))
    }
    for number in range(1, 1000):
        if number not in used:
            return f"{prefix}-{number:03d}"
    raise PreparationError(f"Se agotó el espacio {prefix}-###.")


def _render_initial_checkpoint(
    root: Path,
    manifest: dict[str, Any],
    execution_id: str,
    checkpoint_id: str,
    task_ids: list[str],
    release_id: str,
    authorization_id: str,
    planning: dict[str, Any],
    revision_start: dict[str, Any],
    observed_revision: dict[str, Any],
    transition_date: str,
    actor: str,
    independent_ready: list[str],
    planned: list[tuple[Path, bytes]],
    replacements: list[tuple[Path, bytes, bytes]],
) -> bytes:
    template = (
        PLUGIN_ROOT
        / "skills/lks-sdd-define/assets/templates/04-delivery/checkpoint.md"
    ).read_text(encoding="utf-8")
    file_rows: list[str] = []
    task_label = task_ids[0] if len(task_ids) == 1 else ", ".join(task_ids)
    for path, content in planned:
        relative = path.relative_to(root).as_posix()
        file_rows.append(
            f"| {relative} | created | {hashlib.sha256(content).hexdigest()} | {task_label} | technical preparation |"
        )
    for path, _, content in replacements:
        relative = path.relative_to(root).as_posix()
        file_rows.append(
            f"| {relative} | updated | {hashlib.sha256(content).hexdigest()} | {task_label} | task tracking and continuity |"
        )
    deliverable_rows: list[str] = []
    check_rows: list[str] = []
    replacement_by_path = {path: content for path, _, content in replacements}
    for task_id in task_ids:
        detail_path = root / f"docs/lks-sdd/04-delivery/tasks/{task_id}.md"
        content = replacement_by_path.get(detail_path, detail_path.read_bytes())
        tables = parse_tables(content.decode("utf-8"))
        for headers, rows in tables:
            if headers == TASK_DETAIL_HEADERS_V13["deliverables"]:
                for row in rows:
                    deliverable_rows.append(
                        "| "
                        + " | ".join(
                            [
                                task_id,
                                row.get("Deliverable", "pending"),
                                row.get("State", "pending"),
                                row.get("Acceptance", "pending"),
                                row.get("Evidence", "pending"),
                                row.get("Notes", "pending"),
                            ]
                        )
                        + " |"
                    )
            if headers == TASK_DETAIL_HEADERS["definition"] and rows:
                acceptance = re.findall(
                    r"\bAC-[0-9]{3}\b", rows[0].get("Acceptance", "")
                ) or ["pending"]
                gates = re.findall(
                    r"\bGATE-[A-Z0-9-]{3,80}\b",
                    rows[0].get("Technical gates", ""),
                )
                tests = []
                for plan_headers, plan_rows in tables:
                    if plan_headers == TASK_DETAIL_HEADERS_V13["plan"] and plan_rows:
                        tests = re.findall(
                            r"\bTEST-[0-9]{3}\b", plan_rows[0].get("Tests", "")
                        )
                for contract_item, kind in [
                    *((item, "acceptance") for item in acceptance),
                    *((item, "test") for item in tests),
                    *((item, "gate") for item in gates),
                ]:
                    check_rows.append(
                        f"| {task_id} | {contract_item} | {kind} | not-run | pending | {observed_revision['revision']} | implementation not yet verified |"
                    )
    independent = sorted(set(independent_ready) - set(task_ids))
    values = {
        "{{CHECKPOINT_ID}}": checkpoint_id,
        "{{PROJECT_ID}}": str(manifest["project_id"]),
        "{{BASELINE_ID}}": str(manifest["baseline_id"]),
        "{{OWNER_ROLE}}": actor,
        "{{DATE}}": transition_date,
        "{{EXECUTION_ID}}": execution_id,
        "{{EXECUTION_STATE}}": "in-progress",
        "{{TASK_IDS}}": ", ".join(task_ids),
        "{{INCREMENT_ID}}": str(planning["target"]["increment"]),
        "{{RELEASE_ID}}": release_id,
        "{{AUTHORIZATION_ID}}": authorization_id,
        "{{BRANCH}}": str(revision_start.get("branch") or "not-applicable"),
        "{{REVISION_START}}": str(revision_start["revision"]),
        "{{LAST_REVISION}}": str(observed_revision["revision"]),
        "{{TREE_STATE}}": "dirty" if observed_revision["dirty"] else "clean",
        "{{SPECIFICATION_FINGERPRINT}}": str(
            planning["specification_fingerprint"]
        ),
        "{{PLANNING_FINGERPRINT}}": str(planning["planning_fingerprint"]),
        "{{FILE_ROWS}}": "\n".join(file_rows)
        or "| not-applicable | clean | not-applicable | not-applicable | no files prepared |",
        "{{DELIVERABLE_ROWS}}": "\n".join(deliverable_rows)
        or "| not-applicable | none | pending | pending | pending | no deliverable rows |",
        "{{CHECK_ROWS}}": "\n".join(check_rows)
        or "| not-applicable | pending | planned-check | not-run | pending | pending | no check mapped |",
        "{{ISSUE_ROWS}}": "| not-applicable | resolved | none | no blocker observed | not-applicable | not-applicable | not-applicable |",
        "{{COMPLETED}}": "technical preparation and transition to in-progress",
        "{{PARTIAL}}": "implementation not yet performed",
        "{{PENDING}}": "task deliverables, acceptance, tests and gates",
        "{{BLOCKED}}": "none observed",
        "{{NEXT_SAFE_ACTION}}": "implement only the authorized task definitions",
        "{{INDEPENDENT_TASKS}}": ", ".join(independent)
        if independent
        else "none observed",
        "{{RECONCILIATION}}": "no",
    }
    for token, value in values.items():
        template = template.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", template)
    if remaining:
        raise PreparationError(f"Tokens de checkpoint sin resolver: {remaining}")
    return template.encode("utf-8")


def _write_transaction(
    root: Path,
    manifest: dict[str, Any],
    original_manifest: bytes,
    planned: list[tuple[Path, bytes]],
    replacements: list[tuple[Path, bytes, bytes]],
) -> list[Path]:
    manifest_path = root / ".lks-sdd" / "project.json"
    created_files: list[Path] = []
    created_dirs: set[Path] = set()
    temporary: Path | None = None
    replacement_temporaries: list[Path] = []
    replaced: list[tuple[Path, bytes]] = []
    manifest_replaced = False
    try:
        for destination, original, _ in replacements:
            _assert_safe_destination(root, destination)
            if not destination.is_file() or destination.read_bytes() != original:
                raise PreparationError(
                    f"{destination.relative_to(root).as_posix()} cambió después del preview."
                )
        for destination, content in planned:
            _assert_safe_destination(root, destination)
            missing: list[Path] = []
            parent = destination.parent
            while parent != root and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.update(missing)
            with destination.open("xb") as stream:
                stream.write(content)
            created_files.append(destination)
        for destination, original, content in replacements:
            replacement = destination.with_name(
                destination.name + ".lks-sdd-prepare.tmp"
            )
            _assert_safe_destination(root, replacement)
            with replacement.open("xb") as stream:
                stream.write(content)
            replacement_temporaries.append(replacement)
            os.replace(replacement, destination)
            replacement_temporaries.remove(replacement)
            replaced.append((destination, original))
        if manifest_path.read_bytes() != original_manifest:
            raise PreparationError(
                "project.json cambió durante la materialización."
            )
        temporary = manifest_path.with_name("project.json.lks-sdd.tmp")
        _assert_safe_destination(root, temporary)
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
            )
        os.replace(temporary, manifest_path)
        temporary = None
        manifest_replaced = True
        report, _, _ = validate_project(root)
        if not report.valid:
            raise PreparationError(
                "La preparación produciría un contrato inválido: "
                + "; ".join(report.errors)
            )
        return created_files
    except (OSError, PreparationError) as exc:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        for replacement in replacement_temporaries:
            try:
                replacement.unlink()
            except OSError:
                pass
        if manifest_replaced:
            manifest_path.write_bytes(original_manifest)
        for destination, original in reversed(replaced):
            try:
                destination.write_bytes(original)
            except OSError:
                pass
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
        raise PreparationError(
            f"La materialización se revirtió: {exc}"
        ) from exc


def prepare(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = _safe_root(args.project_root)
    manifest, original_manifest = _load_manifest(root)
    requested_tasks = list(dict.fromkeys(args.task or []))
    readiness_code, readiness = assess(
        root, args.increment, task_ids=requested_tasks or None
    )
    blockers = list(readiness.get("blockers", []))
    if str(manifest.get("schema_version")) in {"1.2", "1.3", "1.4", "1.5"}:
        delivery = delivery_readiness(
            root,
            manifest,
            args.increment,
            task_ids=requested_tasks or None,
        )
    else:
        delivery = {
            "status": "not-applicable",
            "blockers": [],
            "task_ids": [],
            "binding_ids": [],
            "release_ids": [],
        }
    blockers.extend(delivery.get("blockers", []))
    planning = assess_planning(root, manifest, args.increment)
    authorization = assess_authorization(
        manifest, planning, delivery.get("task_ids", [])
    )
    if str(manifest.get("schema_version")) != "1.5":
        blockers.append(
            "La implementación de 0.15 requiere schema 1.5; el runtime no migra proyectos."
        )
    elif planning.get("status") != "complete" and not planning.get(
        "partial_implementation_policy_satisfied"
    ):
        blockers.append(
            "La planificación integral no está completa y no existe una política incremental humana confirmada."
        )
    if authorization.get("status") != "authorized":
        blockers.append(
            "Falta una autorización de implementación vigente y ligada a los fingerprints actuales."
        )
    bindings = _binding_contracts(manifest, delivery)
    if not bindings:
        blockers.append(
            "No existe un profile binding implementable para el alcance."
        )
    for binding in bindings:
        if binding.get("state") != "confirmed":
            blockers.append(
                f"{binding.get('binding_id')}: el binding no está confirmed."
            )
        if not binding.get("selection_decision"):
            blockers.append(
                f"{binding.get('binding_id')}: falta ADR de selección."
            )
        blockers.extend(
            validate_profile(
                str(binding.get("profile_id")), require_validated=True
            )
        )
    if manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption", {})
        if (
            adoption.get("status") != "materialized"
            or adoption.get("baseline_freshness") != "current"
        ):
            blockers.append(
                "La baseline adoptada debe estar materializada y vigente."
            )
    revision = repository_revision(root)
    if revision["kind"] == "git" and revision["dirty"]:
        blockers.append(
            "La implementación debe partir de una revisión Git limpia y "
            "atribuible; confirme primero los cambios de especificación."
        )
    if readiness_code != 0 or blockers:
        return 3, {
            "status": "blocked",
            "increment": args.increment,
            "task_ids": delivery.get("task_ids", []),
            "changed": False,
            "blockers": list(dict.fromkeys(blockers)),
        }

    planned, preserved, manual, locks = _planned_files(
        root, bindings, mode="adoption" if manifest.get("route") == "adopt-existing" else "new-project"
    )
    from composition_contract import resolve_compositions
    from delivery_engine import validate_delivery_contract
    compositions, composition_errors = resolve_compositions(root, validate_delivery_contract(root, manifest), delivery.get("task_ids", []))
    if composition_errors:
        raise PreparationError("; ".join(composition_errors))
    for composition in compositions:
        candidates = [(root / composition["path"], composition["content"].encode())]
        bundle = load_profile_bundle(composition["profile_id"])
        if bundle.driver.get("variant"):
            config = json.loads((bundle.root / "scaffold/profile-runtime.json").read_text())
            config["unit_paths"] = {p["role"]: p["unit_path"] for p in composition["material"]["participants"]}
            config_path = root / ".lks-sdd/verification/compositions" / (composition["profile_id"] + ".json")
            candidates.append((config_path, (json.dumps(config, sort_keys=True, indent=2) + "\n").encode()))
        for destination, content in candidates:
            _assert_safe_destination(root, destination)
            previous = next((value for path, value in planned if path == destination), None)
            if previous is not None:
                if previous != content:
                    raise PreparationError("Dos composiciones divergen en la misma ruta.")
                continue
            if destination.exists():
                if destination.read_bytes() != content:
                    raise PreparationError("La composición preparada ha cambiado; requiere reconciliación explícita.")
                preserved.append(destination.relative_to(root).as_posix())
            else:
                planned.append((destination, content))
    input_fingerprint = readiness.get("input_fingerprint")
    if not isinstance(input_fingerprint, str) or not re.fullmatch(
        r"[a-f0-9]{64}", input_fingerprint
    ):
        raise PreparationError(
            "Readiness no devolvió un fingerprint válido."
        )
    task_ids = list(delivery.get("task_ids", []))
    transition_date = getattr(args, "date", None) or date.today().isoformat()
    actor = getattr(args, "actor", None) or "codex"
    execution_id = _next_indexed_id(
        [
            str(item.get("execution_id"))
            for item in manifest.get("executions", [])
            if isinstance(item, dict)
        ],
        "EXEC",
    )
    checkpoint_folder = root / "docs/lks-sdd/04-delivery/checkpoints"
    checkpoint_id = _next_indexed_id(
        [
            *(
                [path.stem for path in checkpoint_folder.glob("CKPT-*.md")]
                if checkpoint_folder.is_dir()
                else []
            ),
            *[
                Path(str(item.get("latest_checkpoint"))).stem
                for item in manifest.get("executions", [])
                if isinstance(item, dict) and item.get("latest_checkpoint")
            ],
        ],
        "CKPT",
    )
    release_ids = list(delivery.get("release_ids", []))
    if len(release_ids) != 1:
        raise PreparationError(
            "La ejecución autorizada debe pertenecer a una única release."
        )
    release_id = release_ids[0]
    authorization_id = authorization.get("authorization_id")
    if not isinstance(authorization_id, str):
        raise PreparationError("No se resolvió AUTH-### para la ejecución.")
    continuity = {
        "checkpoint": f"../checkpoints/{checkpoint_id}.md",
        "authorization": authorization_id,
        "scope": ", ".join(task_ids),
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "next_safe_action": "implement only the authorized task definitions",
    }
    try:
        replacements = _task_replacements(
            root,
            manifest,
            task_ids,
            revision,
            transition_date,
            actor,
            continuity,
        )
    except TaskManagementError as exc:
        raise PreparationError(
            f"No se puede sincronizar el seguimiento TASK: {exc}"
        ) from exc
    anticipated_revision = repository_revision(
        root,
        overrides={
            path.relative_to(root).as_posix(): content
            for path, content in planned
        }
        | {
            path.relative_to(root).as_posix(): replacement
            for path, _, replacement in replacements
        },
    )
    if anticipated_revision["kind"] == "git" and (planned or replacements):
        anticipated_revision = {**anticipated_revision, "dirty": True}
    checkpoint_content = _render_initial_checkpoint(
        root,
        manifest,
        execution_id,
        checkpoint_id,
        task_ids,
        release_id,
        authorization_id,
        planning,
        revision,
        anticipated_revision,
        transition_date,
        actor,
        next_tasks(validate_delivery_contract(root, manifest), planning).get(
            "ready", []
        ),
        planned,
        replacements,
    )
    checkpoint_path = checkpoint_folder / f"{checkpoint_id}.md"
    _assert_safe_destination(root, checkpoint_path)
    if checkpoint_path.exists():
        raise PreparationError(f"Colisión de checkpoint: {checkpoint_id}.")
    planned.append((checkpoint_path, checkpoint_content))
    preview_hash = _preview_hash(
        root,
        planned,
        original_manifest,
        input_fingerprint,
        task_ids,
        replacements,
    )
    result = {
        "status": "dry-run" if args.dry_run else "prepared",
        "increment": args.increment,
        "task_ids": task_ids,
        "profile_bindings": [item["binding_id"] for item in bindings],
        "profiles": [item["profile_id"] for item in bindings],
        "changed": False,
        "preview_hash": preview_hash,
        "created": [
            path.relative_to(root).as_posix() for path, _ in planned
        ],
        "updated": [
            path.relative_to(root).as_posix() for path, _, _ in replacements
        ],
        "preserved": preserved,
        "manual_integrations": manual,
        "readiness": readiness["status"],
        "planning_completeness": planning["status"],
        "planning_integrity": planning["integrity"],
        "implementation_authorization": authorization,
        "execution_id": execution_id,
        "checkpoint": checkpoint_path.relative_to(root).as_posix(),
        "input_fingerprint": input_fingerprint,
        "revision_start": revision,
        "last_observed_revision": anticipated_revision,
        "locks": locks,
        "transition_summary": {
            "where_we_are": "task-start-preview",
            "completed": [
                f"Plan {planning['target']['id']} y {authorization_id} están vigentes para la porción seleccionada."
            ],
            "in_progress": [],
            "pending": [
                f"Crear {execution_id}, {checkpoint_id} y pasar a in-progress: {', '.join(task_ids)}."
            ],
            "blocked": [],
            "next_step": "Revisar todos los archivos y transiciones del preview antes del apply.",
            "human_decision": "Aplicar o rechazar el inicio de la porción ya autorizada.",
        },
    }
    if args.dry_run:
        return 0, result
    if not args.apply or not args.authorize:
        raise PreparationError(
            "Aplicar requiere --apply y --authorize tras revisar el dry-run."
        )
    if args.preview_hash != preview_hash:
        raise PreparationError(
            "El preview hash no coincide; repita el dry-run."
        )
    if _current_input_fingerprint(root, args.increment) != input_fingerprint:
        raise PreparationError(
            "La especificación cambió después del preview."
        )
    if (root / ".lks-sdd" / "project.json").read_bytes() != original_manifest:
        raise PreparationError(
            "project.json cambió después del preview."
        )

    manifest["phase"] = "implementation"
    manifest["gate"] = "G3"
    manifest["active_increment"] = args.increment
    if str(manifest.get("schema_version")) in {"1.2", "1.3", "1.4", "1.5"}:
        active_task_ids = set(task_ids)
        if str(manifest.get("schema_version")) in {"1.3", "1.4", "1.5"}:
            active_task_ids.update(manifest.get("active_tasks", []))
            manifest["active_tasks"] = sorted(active_task_ids)
        manifest["active_task"] = (
            next(iter(active_task_ids)) if len(active_task_ids) == 1 else None
        )
        if str(manifest.get("schema_version")) in {"1.3", "1.4", "1.5"}:
            changed_paths = [
                path.relative_to(root).as_posix() for path, _ in planned
            ] + [
                path.relative_to(root).as_posix()
                for path, _, _ in replacements
            ]
            manifest["executions"].append(
                {
                    "execution_id": execution_id,
                    "status": "in-progress",
                    "increment": args.increment,
                    "release": release_id,
                    "task_ids": task_ids,
                    "profile_bindings": [
                        str(item["binding_id"]) for item in bindings
                    ],
                    "locks": locks,
                    "branch": revision.get("branch"),
                    "revision_start": str(revision["revision"]),
                    "last_observed_revision": str(
                        anticipated_revision["revision"]
                    ),
                    "authorization_id": authorization_id,
                    "specification_fingerprint": planning[
                        "specification_fingerprint"
                    ],
                    "planning_fingerprint": planning["planning_fingerprint"],
                    "latest_checkpoint": checkpoint_path.relative_to(
                        root
                    ).as_posix(),
                    "changed_paths": changed_paths,
                    "evidence_ids": [],
                }
            )
        manifest["implementation"] = {
            "status": "in-progress",
            "increment": args.increment,
            "task_ids": task_ids,
            "profile_bindings": [
                str(item["binding_id"]) for item in bindings
            ],
            "branch": revision.get("branch"),
            "revision_start": str(revision["revision"]),
            "locks": locks,
            "changed_paths": [
                path.relative_to(root).as_posix() for path, _ in planned
            ]
            + [
                path.relative_to(root).as_posix()
                for path, _, _ in replacements
            ],
            "evidence_ids": [],
            "authorization_id": authorization_id,
            "specification_fingerprint": planning[
                "specification_fingerprint"
            ],
            "planning_fingerprint": planning["planning_fingerprint"],
            "latest_checkpoint": checkpoint_path.relative_to(root).as_posix(),
        }
    else:
        bundle = load_profile_bundle(str(bindings[0]["profile_id"]))
        manifest["implementation"] = {
            "status": "in-progress",
            "increment": args.increment,
            "profile_id": bindings[0]["profile_id"],
            "profile_version": bundle.profile.get("version"),
            "changed_paths": [
                path.relative_to(root).as_posix() for path, _ in planned
            ],
            "evidence_ids": [],
        }
    created = _write_transaction(
        root, manifest, original_manifest, planned, replacements
    )
    result.update(
        {
            "status": "prepared",
            "changed": True,
            "created": [
                path.relative_to(root).as_posix() for path in created
            ],
            "transition_summary": {
                "where_we_are": "implementation-in-progress",
                "completed": [
                    f"{execution_id} y el checkpoint inicial {checkpoint_id} quedaron registrados."
                ],
                "in_progress": task_ids,
                "pending": [
                    "Implementación, revisión, aceptación, gates y evidencia aún no demostrados."
                ],
                "blocked": [],
                "next_step": "Implementar únicamente la definición autorizada y actualizar el checkpoint antes de pausar.",
                "human_decision": "Ninguna nueva; conservar los límites del plan y la autorización vigentes.",
            },
        }
    )
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--task", action="append")
    parser.add_argument(
        "--date",
        help="Fecha AAAA-MM-DD para la transición TASK a in-progress.",
    )
    parser.add_argument(
        "--actor",
        help="Actor o autoridad que aplica la preparación autorizada.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        code, result = prepare(args)
    except PreparationError as exc:
        code, result = 2, {
            "status": "error",
            "changed": False,
            "error": str(exc),
        }
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        for blocker in result.get("blockers", []):
            print(f"BLOCKER: {blocker}")
        if result.get("preview_hash"):
            print(f"preview_hash={result['preview_hash']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
