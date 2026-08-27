#!/usr/bin/env python3
"""Initialize the LKS-SDD documentation core for an authorized new project."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

PLUGIN_VERSION = "0.14.0"
METHOD_VERSION = "1.5.0"
SCHEMA_VERSION = "1.5"
BASELINE_ID = "BL-0001"
PROJECT_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cs",
    ".go",
    ".rb",
    ".php",
    ".vue",
    ".svelte",
    ".kt",
    ".rs",
}
CODE_MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
    "composer.json",
    "Dockerfile",
}
IGNORED_DIRS = {
    ".git",
    ".lks-sdd",
    "docs",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


ARTIFACTS = [
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


class InitializationError(Exception):
    """Expected, user-actionable initialization failure."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def contains_existing_application(root: Path) -> list[str]:
    indicators: list[str] = []
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = [
            name
            for name in dirs
            if name not in IGNORED_DIRS and not _is_link_like(current_path / name)
        ]
        for name in files:
            path = current_path / name
            if _is_link_like(path):
                continue
            relative = path.relative_to(root).as_posix()
            if name in CODE_MANIFESTS or path.suffix.lower() in CODE_EXTENSIONS:
                indicators.append(relative)
                if len(indicators) >= 8:
                    return indicators
    return indicators


def load_existing_manifest(root: Path, path: Path) -> dict | None:
    if not path.exists():
        return None
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if _is_link_like(current):
            raise InitializationError(
                "No se lee project.json a través de enlaces simbólicos o junctions."
            )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InitializationError(
            f"No se puede reanudar: project.json no es válido: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise InitializationError(
            "No se puede reanudar: project.json debe ser un objeto JSON."
        )
    return data


def render_template(
    template: Path, project_id: str, baseline_id: str, today: str
) -> str:
    content = template.read_text(encoding="utf-8")
    content = re.sub(
        r'^created_with_plugin_version: "[0-9A-Za-z.-]+"$',
        f'created_with_plugin_version: "{PLUGIN_VERSION}"',
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^schema_version: "[0-9.]+"$',
        f'schema_version: "{SCHEMA_VERSION}"',
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^method_version: "[0-9.]+"$',
        f'method_version: "{METHOD_VERSION}"',
        content,
        flags=re.MULTILINE,
    )
    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{BASELINE_ID}}": baseline_id,
        "{{DATE}}": today,
    }
    for token, value in replacements.items():
        content = content.replace(token, value)
    remaining = re.findall(r"\{\{[A-Z0-9_]+\}\}", content)
    if remaining:
        raise InitializationError(
            f"Tokens de plantilla sin resolver en {template.name}: {remaining}"
        )
    return content


def build_manifest(
    project_id: str, documentation_level: str, risk_profile: str, root: Path
) -> dict:
    return {
        "project_id": project_id,
        "route": "new",
        "method_version": METHOD_VERSION,
        "schema_version": SCHEMA_VERSION,
        "plugin_version": PLUGIN_VERSION,
        "documentation_level": documentation_level,
        "risk_profile": risk_profile,
        "phase": "definition",
        "gate": "G0",
        "baseline_id": BASELINE_ID,
        "canonical_docs": "docs/lks-sdd",
        "artifacts": [
            {"id": artifact_id, "path": f"docs/lks-sdd/{relative}", "required": True}
            for artifact_id, relative in ARTIFACTS
        ],
        "technology": {
            "preferred_stack_assessed": False,
            "selected_profile": None,
            "selection_decision": None,
            "profile_bindings": [],
        },
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
            "type": "git" if (root / ".git").exists() else "none",
            "origin": "none",
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
    }


def initialize(args: argparse.Namespace) -> tuple[int, dict]:
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        raise InitializationError(
            f"La raíz del proyecto debe existir y ser una carpeta: {root}"
        )
    if len(args.project_id) < 3 or not PROJECT_ID_RE.fullmatch(args.project_id):
        raise InitializationError(
            "project_id debe usar minúsculas, números y guiones, con al menos tres caracteres."
        )
    try:
        date.fromisoformat(args.date)
    except ValueError as exc:
        raise InitializationError("--date debe usar el formato AAAA-MM-DD.") from exc

    manifest_path = root / ".lks-sdd" / "project.json"
    existing = load_existing_manifest(root, manifest_path)
    if existing is None:
        application_indicators = contains_existing_application(root)
        if application_indicators:
            return 3, {
                "status": "adopt-existing-required",
                "changed": False,
                "reason": "Se detectaron indicadores de una aplicación existente; la ruta new no puede escribir.",
                "indicators": application_indicators,
                "next_skill": "lks-sdd-adopt-existing",
                "next_skill_available": True,
            }
    else:
        if existing.get("route") != "new":
            raise InitializationError("El índice existente no pertenece a la ruta new.")
        if existing.get("project_id") != args.project_id:
            raise InitializationError(
                "El project_id solicitado no coincide con el índice existente."
            )

    template_root = Path(__file__).resolve().parents[1] / "assets" / "templates"
    planned: list[tuple[Path, str]] = []
    preserved: list[str] = []
    for _, relative in ARTIFACTS:
        destination = root / "docs" / "lks-sdd" / relative
        if destination.exists():
            if not destination.is_file():
                raise InitializationError(
                    f"Colisión: la ruta esperada no es un archivo: {destination}"
                )
            if existing is None:
                raise InitializationError(
                    "Colisión documental sin un índice LKS-SDD que permita reanudar; "
                    f"no se sobrescribió {destination}"
                )
            preserved.append(destination.relative_to(root).as_posix())
            continue
        template = template_root / relative
        if not template.is_file():
            raise InitializationError(f"Falta la plantilla empaquetada: {template}")
        planned.append(
            (
                destination,
                render_template(template, args.project_id, BASELINE_ID, args.date),
            )
        )

    if existing is None:
        planned.append(
            (
                manifest_path,
                json.dumps(
                    build_manifest(
                        args.project_id,
                        args.documentation_level,
                        args.risk_profile,
                        root,
                    ),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
            )
        )

    result = {
        "status": "dry-run" if args.dry_run else "initialized",
        "project_root": str(root),
        "changed": bool(planned) and not args.dry_run,
        "would_change": bool(planned),
        "created": [path.relative_to(root).as_posix() for path, _ in planned],
        "preserved": preserved,
        "route": "new",
        "code_generated": False,
    }
    if args.dry_run:
        return 0, result

    created_files: list[Path] = []
    created_directories: set[Path] = set()
    try:
        for destination, content in planned:
            missing_parents: list[Path] = []
            parent = destination.parent
            while parent != root and not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            destination.parent.mkdir(parents=True, exist_ok=True)
            created_directories.update(missing_parents)
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                created_files.append(destination)
                stream.write(content)
    except (FileExistsError, OSError) as exc:
        for created_file in reversed(created_files):
            try:
                created_file.unlink()
            except OSError:
                pass
        for created_directory in sorted(
            created_directories, key=lambda item: len(item.parts), reverse=True
        ):
            try:
                created_directory.rmdir()
            except OSError:
                pass
        raise InitializationError(
            f"La inicialización se revirtió tras una colisión o error de escritura en {destination}: {exc}"
        ) from exc
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
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
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        exit_code, result = initialize(args)
    except InitializationError as exc:
        exit_code, result = 2, {"status": "error", "changed": False, "error": str(exc)}

    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("status", "error"))
        if result.get("reason"):
            print(result["reason"])
        if result.get("error"):
            print(result["error"])
        for path in result.get("created", []):
            prefix = "would create" if args.dry_run else "created"
            print(f"{prefix}: {path}")
        if exit_code == 3:
            print(
                "Use lks-sdd-adopt-existing para iniciar el preflight de solo lectura."
            )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
