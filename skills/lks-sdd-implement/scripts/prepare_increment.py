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
from delivery_engine import delivery_readiness, repository_revision  # noqa: E402
from manage_tasks import (  # noqa: E402
    _append_table_row,
    _replace_frontmatter_date,
    _replace_table_row,
    _single_detail_row,
    TaskManagementError,
    TASK_DETAIL_HEADERS,
    TASK_HEADERS,
)
from profile_registry import load_profile_bundle, profile_source_files  # noqa: E402
from validate_reference_profile import validate_profile  # noqa: E402


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
    if str(manifest.get("schema_version")) == "1.2":
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
        for source in bundle.driver["prepare"]["sources"]:
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
    for item in manifest.get("artifacts", []):
        if isinstance(item, dict) and item.get("id") == artifact_id:
            return Path(str(item["path"]))
    raise PreparationError(f"Falta {artifact_id} en el índice.")


def _task_replacements(
    root: Path,
    manifest: dict[str, Any],
    task_ids: list[str],
    revision: dict[str, Any],
    transition_date: str,
    actor: str,
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
                "Health": "on-track",
                "Progress": str(
                    max(1, min(int(current.get("Progress", "0")), 99))
                ),
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
                "Health": "on-track",
                "Progress": str(
                    max(1, min(int(current.get("Progress", "0")), 99))
                ),
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
    if str(manifest.get("schema_version")) == "1.2":
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

    planned, preserved, manual, locks = _planned_files(root, bindings)
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
    try:
        replacements = _task_replacements(
            root, manifest, task_ids, revision, transition_date, actor
        )
    except TaskManagementError as exc:
        raise PreparationError(
            f"No se puede sincronizar el seguimiento TASK: {exc}"
        ) from exc
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
        "input_fingerprint": input_fingerprint,
        "revision_start": revision,
        "locks": locks,
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
    if str(manifest.get("schema_version")) == "1.2":
        manifest["active_task"] = task_ids[0] if len(task_ids) == 1 else None
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
