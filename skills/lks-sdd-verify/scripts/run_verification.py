#!/usr/bin/env python3
"""Plan or execute locked multi-profile checks for one LKS-SDD increment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from contract_engine import (  # noqa: E402
    build_project_model,
    is_pending_traceability_evidence,
    resolve_active_increment,
)
from validate_project import (  # noqa: E402
    INTERFACE_CONTRACT_HEADERS,
    interface_applicability,
    parse_frontmatter,
    parse_markdown_table_blocks,
    table_rows_for_headers,
    v06_contract_applies,
    validate_project,
    validate_visual_review_evidence,
)
from validate_reference_profile import (  # noqa: E402
    PROFILE_ID,
    validate_consumer_profile_lock,
    validate_profile,
)
from delivery_engine import (  # noqa: E402
    load_delivery_evidence,
    repository_revision,
    validate_delivery_contract,
)
from planning_engine import assess_authorization, assess_planning  # noqa: E402
from profile_registry import load_profile_bundle  # noqa: E402

EVIDENCE_RE = re.compile(r"^EVID-[0-9]{3}$")


class VerificationError(Exception):
    """Expected verification failure."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _assert_safe_path(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"Ruta fuera del proyecto: {path}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if _is_link_like(current):
            raise VerificationError(
                f"No se escribe mediante symlinks o junctions: {relative.as_posix()}"
            )


def _commands(root: Path) -> list[dict[str, Any]]:
    npx = "npx.cmd" if os.name == "nt" else "npx"
    pnpm = [npx, "--yes", "pnpm@10.34.5"]
    return [
        {
            "name": "backend-lock",
            "cwd": root / "apps/backend",
            "command": ["uv", "sync", "--frozen"],
        },
        {
            "name": "backend-lint",
            "cwd": root / "apps/backend",
            "command": ["uv", "run", "ruff", "check", "."],
        },
        {
            "name": "backend-typecheck",
            "cwd": root / "apps/backend",
            "command": ["uv", "run", "mypy"],
        },
        {
            "name": "backend-tests",
            "cwd": root / "apps/backend",
            "command": ["uv", "run", "pytest"],
        },
        {
            "name": "backend-openapi",
            "cwd": root / "apps/backend",
            "command": [
                "uv",
                "run",
                "python",
                "-c",
                (
                    "import sys; sys.path.insert(0, 'src'); from lks_sdd_app.main import app; "
                    "assert app.openapi()['openapi'].startswith('3.1.')"
                ),
            ],
        },
        {
            "name": "frontend-lock",
            "cwd": root / "apps/frontend",
            "command": [*pnpm, "install", "--frozen-lockfile"],
        },
        {
            "name": "frontend-lint",
            "cwd": root / "apps/frontend",
            "command": [*pnpm, "lint"],
        },
        {
            "name": "frontend-typecheck",
            "cwd": root / "apps/frontend",
            "command": [*pnpm, "typecheck"],
        },
        {
            "name": "frontend-tests",
            "cwd": root / "apps/frontend",
            "command": [*pnpm, "test"],
        },
        {
            "name": "frontend-build",
            "cwd": root / "apps/frontend",
            "command": [*pnpm, "build"],
        },
    ]


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any], bytes]:
    path = root / ".lks-sdd" / "project.json"
    _assert_safe_path(root, path)
    try:
        original = path.read_bytes()
        value = json.loads(original.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"No se puede leer project.json: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError("project.json debe ser un objeto.")
    return path, value, original


def _implementation_gate(
    manifest: dict[str, Any], increment: str, *, planning: bool
) -> tuple[list[str], dict[str, Any]]:
    """Require an attributable implementation before planning or executing checks."""
    implementation = manifest.get("implementation")
    if not isinstance(implementation, dict):
        return ["Falta implementation en .lks-sdd/project.json."], {}

    blockers: list[str] = []
    implementation_increment = implementation.get("increment")
    implementation_status = implementation.get("status")
    implementation_profile = implementation.get("profile_id")
    selected_profile = manifest.get("technology", {}).get("selected_profile")

    if implementation_increment != increment:
        blockers.append(
            "implementation.increment no coincide con el incremento solicitado: "
            f"{implementation_increment!r} != {increment!r}."
        )

    allowed_statuses = {"in-progress", "completed"} if planning else {"completed"}
    if implementation_status not in allowed_statuses:
        if planning:
            blockers.append(
                "El plan de verificación requiere implementation.status "
                "in-progress o completed para el mismo incremento."
            )
        else:
            blockers.append(
                "Ejecutar checks o registrar evidencia requiere "
                "implementation.status=completed."
            )

    if not isinstance(implementation_profile, str) or not implementation_profile:
        blockers.append("Falta implementation.profile_id en project.json.")
    elif implementation_profile != selected_profile:
        blockers.append(
            "implementation.profile_id no coincide con "
            "technology.selected_profile: "
            f"{implementation_profile!r} != {selected_profile!r}."
        )

    return blockers, {
        "status": implementation_status,
        "increment": implementation_increment,
        "profile_id": implementation_profile,
    }


def _active_contract_snapshot(root: Path, increment: str) -> tuple[str, list[str]]:
    """Bind verification to the currently resolved active contract."""
    active = resolve_active_increment(build_project_model(root), increment)
    errors = [
        f"Contrato activo: {item.message}"
        for item in active.diagnostics
        if item.severity == "error"
    ]
    return active.fingerprint, errors


def _revalidate_evidence_gate(
    root: Path,
    increment: str,
    *,
    initial_manifest: bytes,
    initial_contract_fingerprint: str,
    initial_lock_details: dict[str, str | None],
) -> tuple[Path, dict[str, Any], bytes, dict[str, str | None]]:
    """Recheck every attributable input after checks and before any write."""
    manifest_path, current_manifest, current_manifest_bytes = _load_manifest(root)
    current_report, validated_manifest, _ = validate_project(root)
    blockers = [
        f"Contrato inválido tras ejecutar los checks: {error}"
        for error in current_report.errors
    ]

    try:
        manifest_still_current = manifest_path.read_bytes() == current_manifest_bytes
    except OSError as exc:
        raise VerificationError(
            f"No se puede confirmar project.json antes de registrar evidencia: {exc}"
        ) from exc
    if not manifest_still_current or validated_manifest != current_manifest:
        blockers.append(
            "project.json cambió mientras se revalidaba el registro de evidencia."
        )
    if current_manifest_bytes != initial_manifest:
        blockers.append("project.json cambió después de ejecutar los checks.")

    if current_manifest.get("active_increment") not in {None, increment}:
        blockers.append(
            f"Otro incremento está activo: {current_manifest.get('active_increment')}"
        )
    implementation_blockers, _ = _implementation_gate(
        current_manifest, increment, planning=False
    )
    blockers.extend(implementation_blockers)
    if current_manifest.get("technology", {}).get("selected_profile") != PROFILE_ID:
        blockers.append(
            "La verificación automatizada H0 requiere el perfil de referencia seleccionado."
        )
    blockers.extend(validate_profile(require_validated=True))

    lock_errors, current_lock_details = validate_consumer_profile_lock(root)
    blockers.extend(lock_errors)
    if current_lock_details != initial_lock_details:
        blockers.append("El lock H0 cambió después de ejecutar los checks.")

    current_contract_fingerprint, contract_errors = _active_contract_snapshot(
        root, increment
    )
    blockers.extend(contract_errors)
    if current_contract_fingerprint != initial_contract_fingerprint:
        blockers.append("El contrato activo cambió después de ejecutar los checks.")

    if blockers:
        raise VerificationError(
            "No se registra evidencia porque la puerta cambió tras ejecutar los checks: "
            + "; ".join(dict.fromkeys(blockers))
        )
    return (
        manifest_path,
        current_manifest,
        current_manifest_bytes,
        current_lock_details,
    )


def _interface_is_applicable(
    root: Path, manifest: dict[str, Any], increment: str
) -> bool:
    entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if item.get("id") == "ART-INCREMENTS"
        ),
        None,
    )
    if not isinstance(entry, dict):
        raise VerificationError("Falta ART-INCREMENTS para determinar la interfaz.")
    path = root / entry["path"]
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    if not v06_contract_applies(manifest, metadata):
        return False
    rows = table_rows_for_headers(
        parse_markdown_table_blocks(body), INTERFACE_CONTRACT_HEADERS
    )
    if rows is None:
        raise VerificationError("Falta la tabla de aplicabilidad de interfaz.")
    matching = [row for row in rows if row.get("Increment", "").strip() == increment]
    if len(matching) != 1:
        raise VerificationError(
            f"{increment} debe tener exactamente una fila de aplicabilidad de interfaz."
        )
    applicability, _ = interface_applicability(
        matching[0].get("Interface applicability", "")
    )
    return applicability == "applicable"


def _visual_applicability(
    root: Path,
    manifest: dict[str, Any],
    increment: str,
    task_ids: list[str],
    delivery: dict[str, Any],
) -> dict[str, Any]:
    """Derive visual review applicability from the exact selected TASK slice."""

    triggers: list[str] = []
    inspected: list[str] = []
    selected_releases = {
        delivery.get("tasks", {}).get(task_id, {}).get("Release")
        for task_id in task_ids
    }
    selected_releases.discard(None)
    release_scope = False
    if len(selected_releases) == 1:
        release_id = next(iter(selected_releases))
        release_tasks = {
            candidate_id
            for candidate_id, row in delivery.get("tasks", {}).items()
            if row.get("Release") == release_id
        }
        release_scope = bool(release_tasks) and set(task_ids) == release_tasks

    for task_id in sorted(task_ids):
        task = delivery.get("tasks", {}).get(task_id, {})
        details = delivery.get("task_details", {}).get(task_id, {})
        definition_rows = details.get("definition", [])
        definition = definition_rows[0] if len(definition_rows) == 1 else {}
        unit = delivery.get("units", {}).get(task.get("Unit"), {})
        binding = delivery.get("bindings", {}).get(task.get("Profile binding"), {})
        textual_fields = {
            "in-scope": definition.get("In scope", ""),
            "out-of-scope": definition.get("Out of scope", ""),
            "requirements": definition.get("Requirements", ""),
            "acceptance": definition.get("Acceptance", ""),
            "capabilities": definition.get("Required capabilities", ""),
            "gates": definition.get("Technical gates", ""),
            "unit": " ".join(
                str(unit.get(key, ""))
                for key in ("Component", "Responsibility", "Runtime boundary", "Interfaces")
            ),
        }
        joined = " ".join(textual_fields.values())
        refs = sorted(set(re.findall(r"\b(?:UX|VIS)-[0-9]{3}\b", joined)))
        if refs:
            triggers.append(f"{task_id}:refs={','.join(refs)}")
        contract_ids = re.findall(
            r"\b(?:CAP|GATE)-[A-Z0-9-]{3,80}\b",
            " ".join([textual_fields["capabilities"], textual_fields["gates"]]),
        )
        direct_frontend = sorted(
            {
                item
                for item in contract_ids
                if {"FRONTEND", "BROWSER", "UI"} & set(item.split("-"))
            }
        )
        if direct_frontend:
            triggers.append(
                f"{task_id}:frontend-contract={','.join(direct_frontend)}"
            )
        in_scope_text = textual_fields["in-scope"].casefold()
        backend_only = bool(
            re.search(
                r"\b(?:backend|api|worker|consumer|processor|database)\b",
                in_scope_text,
            )
        ) and not bool(
            re.search(
                r"\b(?:frontend|browser|interfaz|interface|ui|spa|screen)\b",
                in_scope_text,
            )
        )
        unit_text = textual_fields["unit"].casefold()
        if not backend_only and re.search(
            r"\b(?:frontend|browser|interfaz|interface|client-side|spa)\b", unit_text
        ):
            triggers.append(f"{task_id}:unit={task.get('Unit')}")
        profile_id = str(binding.get("profile_id", ""))
        if not backend_only and profile_id:
            bundle = load_profile_bundle(profile_id)
            roles = {
                str(item.get("role", "")).casefold()
                for item in bundle.profile.get("units", [])
                if isinstance(item, dict)
            }
            if "frontend" in roles and "backend" not in roles:
                triggers.append(f"{task_id}:profile={profile_id}")
        inspected.append(task_id)

    if triggers:
        return {
            "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
            "status": "applicable",
            "scope": "release" if release_scope else "task-slice",
            "task_ids": sorted(task_ids),
            "reason": "selected-task-interface-signals:" + ";".join(sorted(set(triggers))),
        }
    if release_scope and _interface_is_applicable(root, manifest, increment):
        return {
            "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
            "status": "applicable",
            "scope": "release",
            "task_ids": sorted(task_ids),
            "reason": f"release-{next(iter(selected_releases))}-delivers-interface",
        }
    return {
        "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
        "status": "not-applicable",
        "scope": "task-slice",
        "task_ids": sorted(task_ids),
        "reason": "selected-tasks-have-no-ux-vis-frontend-browser-or-interface-unit-signals:"
        + ",".join(inspected),
    }


def _binding_ids_for_tasks(
    task_ids: list[str], delivery: dict[str, Any]
) -> list[str]:
    return sorted(
        {
            str(delivery.get("tasks", {}).get(task_id, {}).get("Profile binding"))
            for task_id in task_ids
            if delivery.get("tasks", {}).get(task_id, {}).get("Profile binding")
        }
    )


def _resolve_visual_evidence_path(root: Path, requested: Path) -> Path:
    candidate = requested if requested.is_absolute() else root / requested
    try:
        relative = candidate.absolute().relative_to(root)
    except ValueError as exc:
        raise VerificationError("La evidencia visual debe estar dentro del proyecto.") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if _is_link_like(current):
            raise VerificationError(
                f"La evidencia visual usa un symlink o junction: {relative.as_posix()}"
            )
    resolved = candidate.resolve()
    try:
        resolved.relative_to((root / "docs/lks-sdd/evidence/visual").resolve())
    except ValueError as exc:
        raise VerificationError(
            "La evidencia visual debe estar bajo docs/lks-sdd/evidence/visual/."
        ) from exc
    return resolved


def _visual_evidence_check(
    root: Path,
    increment: str,
    evidence_path: Path | None,
    manifest: dict[str, Any] | None = None,
    definitions: dict[str, dict[str, str]] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    if evidence_path is None:
        return (
            {
                "name": "visual-browser-review",
                "status": "not-run",
                "reason": "manual-browser-evidence-missing",
            },
            [],
        )
    if manifest is None or definitions is None:
        report, loaded_manifest, loaded_definitions = validate_project(root)
        if not report.valid or loaded_manifest is None:
            raise VerificationError(
                "El contrato del proyecto no es válido para revisar evidencia visual."
            )
        manifest = loaded_manifest
        definitions = loaded_definitions
    errors, outcome, limitations, checked_files = validate_visual_review_evidence(
        root,
        manifest,
        definitions,
        increment,
        evidence_path,
        require_fresh=True,
    )
    if errors or outcome is None:
        raise VerificationError("Evidencia visual inválida: " + "; ".join(errors))
    outcome["checked_files"] = checked_files
    return outcome, limitations


def _execute_check(check: dict[str, Any]) -> dict[str, Any]:
    cwd = check["cwd"]
    if not cwd.is_dir():
        return {
            "name": check["name"],
            "status": "blocked",
            "reason": "working-directory-missing",
        }
    started = time.monotonic()
    try:
        process = subprocess.run(
            check["command"],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
            check=False,
        )
    except FileNotFoundError:
        return {"name": check["name"], "status": "not-run", "reason": "tool-not-found"}
    except subprocess.TimeoutExpired:
        return {"name": check["name"], "status": "failed", "reason": "timeout"}
    return {
        "name": check["name"],
        "status": "passed" if process.returncode == 0 else "failed",
        "exit_code": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def _wait_http(name: str, url: str, timeout: int = 180) -> dict[str, Any]:
    started = time.monotonic()
    last_error = ""
    while time.monotonic() - started < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 400:
                    return {
                        "name": name,
                        "status": "passed",
                        "duration_seconds": round(time.monotonic() - started, 3),
                    }
        except (OSError, urllib.error.URLError) as exc:
            last_error = type(exc).__name__
        time.sleep(2)
    return {"name": name, "status": "failed", "reason": last_error or "timeout"}


def _container_checks(root: Path) -> list[dict[str, Any]]:
    compose = root / "infra" / "compose" / "compose.yaml"
    if not compose.is_file():
        return [
            {
                "name": "container-integration",
                "status": "blocked",
                "reason": "compose-file-missing",
            }
        ]
    project = f"lks-sdd-verify-{os.getpid()}"
    env = os.environ.copy()
    env.update(
        {
            "POSTGRES_USER": "lks_sdd_verify",
            "POSTGRES_PASSWORD": "synthetic-verification-password",
            "KEYCLOAK_ADMIN": "lks_sdd_verify_admin",
            "KEYCLOAK_ADMIN_PASSWORD": "synthetic-verification-admin-password",
            "LKS_SDD_KEYCLOAK_PORT": env.get("LKS_SDD_KEYCLOAK_PORT", "18080"),
            "LKS_SDD_BACKEND_PORT": env.get("LKS_SDD_BACKEND_PORT", "18000"),
            "LKS_SDD_FRONTEND_PORT": env.get("LKS_SDD_FRONTEND_PORT", "15173"),
        }
    )
    base = ["docker", "compose", "-p", project, "-f", str(compose)]
    outcomes: list[dict[str, Any]] = []
    config = {
        "name": "compose-config",
        "cwd": root,
        "command": [*base, "config", "--quiet"],
    }
    start = {
        "name": "compose-build-and-start",
        "cwd": root,
        "command": [*base, "up", "--detach", "--build"],
    }
    try:
        outcomes.append(_execute_check_with_env(config, env, timeout=120))
        if outcomes[-1]["status"] != "passed":
            return outcomes
        outcomes.append(_execute_check_with_env(start, env, timeout=1200))
        if outcomes[-1]["status"] != "passed":
            return outcomes
        outcomes.extend(
            [
                _wait_http(
                    "backend-health",
                    f"http://127.0.0.1:{env['LKS_SDD_BACKEND_PORT']}/health",
                ),
                _wait_http(
                    "frontend-smoke",
                    f"http://127.0.0.1:{env['LKS_SDD_FRONTEND_PORT']}/",
                ),
                _wait_http(
                    "keycloak-oidc-discovery",
                    f"http://127.0.0.1:{env['LKS_SDD_KEYCLOAK_PORT']}/realms/lks-sdd/.well-known/openid-configuration",
                ),
            ]
        )
        return outcomes
    finally:
        cleanup = {
            "name": "compose-cleanup",
            "cwd": root,
            "command": [*base, "down", "--volumes", "--remove-orphans"],
        }
        outcomes.append(_execute_check_with_env(cleanup, env, timeout=180))


def _execute_check_with_env(
    check: dict[str, Any], env: dict[str, str], timeout: int
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        process = subprocess.run(
            check["command"],
            cwd=check["cwd"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"name": check["name"], "status": "not-run", "reason": "tool-not-found"}
    except subprocess.TimeoutExpired:
        return {"name": check["name"], "status": "failed", "reason": "timeout"}
    return {
        "name": check["name"],
        "status": "passed" if process.returncode == 0 else "failed",
        "exit_code": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def _updated_traceability(
    path: Path, increment: str, evidence_id: str
) -> tuple[bytes, bytes]:
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines()
    updated = False
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if (
            len(cells) == 6
            and cells[3] == increment
            and is_pending_traceability_evidence(cells[5])
        ):
            cells[5] = evidence_id
            lines[index] = "| " + " | ".join(cells) + " |"
            updated = True
    if not updated:
        raise VerificationError(
            "No existe una fila de trazabilidad pendiente para el incremento."
        )
    return original, ("\n".join(lines) + "\n").encode("utf-8")


def _profile_command(
    root: Path,
    binding: dict[str, Any],
    check: dict[str, Any],
) -> dict[str, Any]:
    unit = Path(str(binding.get("unit_path", ".")))
    relative_cwd = Path(str(check["cwd"]))
    if (
        unit.is_absolute()
        or relative_cwd.is_absolute()
        or ".." in unit.parts
        or ".." in relative_cwd.parts
    ):
        raise VerificationError(
            f"{binding.get('binding_id')}: cwd inseguro en el driver."
        )
    command = list(check["command"])
    if os.name == "nt" and command and command[0] in {"npm", "npx"}:
        command[0] += ".cmd"
    return {
        "name": f"{binding['binding_id']}:{check['name']}",
        "gate_id": check["id"],
        "binding_id": binding["binding_id"],
        "cwd": root / unit / relative_cwd,
        "command": command,
        "timeout_seconds": check["timeout_seconds"],
        "requires_containers": check["requires_containers"],
        "required": check["required"],
    }


def _execute_profile_command(
    check: dict[str, Any], env: dict[str, str]
) -> dict[str, Any]:
    if not check["cwd"].is_dir():
        return {
            "name": check["name"],
            "gate_id": check["gate_id"],
            "binding_id": check["binding_id"],
            "status": "blocked",
            "reason": "working-directory-missing",
        }
    started = time.monotonic()
    try:
        process = subprocess.run(
            check["command"],
            cwd=check["cwd"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(check["timeout_seconds"]),
            check=False,
        )
    except FileNotFoundError:
        status, reason = "not-run", "tool-not-found"
        return {
            "name": check["name"],
            "gate_id": check["gate_id"],
            "binding_id": check["binding_id"],
            "status": status,
            "reason": reason,
        }
    except subprocess.TimeoutExpired:
        return {
            "name": check["name"],
            "gate_id": check["gate_id"],
            "binding_id": check["binding_id"],
            "status": "failed",
            "reason": "timeout",
        }
    return {
        "name": check["name"],
        "gate_id": check["gate_id"],
        "binding_id": check["binding_id"],
        "status": "passed" if process.returncode == 0 else "failed",
        "exit_code": process.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": process.stdout[-2000:],
        "stderr_tail": process.stderr[-2000:],
    }


def _cleanup_profile_compositions(
    root: Path,
    checks: list[dict[str, Any]],
    env: dict[str, str],
) -> list[dict[str, Any]]:
    prefixes: set[tuple[str, tuple[str, ...]]] = set()
    for check in checks:
        command = check["command"]
        normalized = [
            item[:-4] if index == 0 and item.endswith(".cmd") else item
            for index, item in enumerate(command)
        ]
        if normalized[:2] != ["docker", "compose"]:
            continue
        prefix = ["docker", "compose"]
        if "-f" in normalized:
            index = normalized.index("-f")
            if index + 1 < len(normalized):
                prefix.extend(["-f", normalized[index + 1]])
        prefixes.add((str(check["cwd"]), tuple(prefix)))
    outcomes: list[dict[str, Any]] = []
    for cwd_text, prefix in sorted(prefixes):
        outcomes.append(
            _execute_check_with_env(
                {
                    "name": "compose-cleanup",
                    "cwd": Path(cwd_text),
                    "command": [
                        *prefix,
                        "down",
                        "--volumes",
                        "--remove-orphans",
                    ],
                },
                env,
                timeout=300,
            )
        )
    return outcomes


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    ignored = {
        ".git",
        ".lks-sdd",
        ".venv",
        "node_modules",
        "coverage",
        "test-results",
        "playwright-report",
    }
    ignored_relative = {"docs/lks-sdd"}
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    entries: list[Path] = []
    for current, directories, files in os.walk(path, topdown=True):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in ignored
            and (current_path / directory).relative_to(path).as_posix()
            not in ignored_relative
            and not (current_path / directory).is_symlink()
        )
        entries.extend(
            current_path / filename
            for filename in sorted(files)
            if filename not in ignored
            and not (current_path / filename).is_symlink()
        )
    for item in sorted(entries, key=lambda value: value.relative_to(path).as_posix()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(item.read_bytes()).digest())
    return digest.hexdigest()


def _artifact_digests(
    root: Path,
    bindings: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> list[str]:
    values: list[str] = []
    for binding in bindings:
        unit_root = root / str(binding.get("unit_path", "."))
        candidates = [
            unit_root / "dist",
            unit_root / ".next" / "standalone",
            unit_root / "build",
        ]
        selected = next((item for item in candidates if item.exists()), None)
        if selected is None:
            selected = unit_root
        values.append(f"sha256:{_tree_digest(selected)}")
    image_tags: set[str] = set()
    for check in checks:
        command = check["command"]
        for marker in ("--tag", "-t"):
            if marker in command:
                index = command.index(marker)
                if index + 1 < len(command):
                    image_tags.add(command[index + 1])
    for tag in sorted(image_tags):
        process = subprocess.run(
            ["docker", "image", "inspect", tag, "--format", "{{.Id}}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        value = process.stdout.strip()
        if process.returncode == 0 and re.fullmatch(
            r"sha256:[a-f0-9]{64}", value
        ):
            values.append(value)
    return list(dict.fromkeys(values))


def _canonical_hash_payload(value: Any) -> bytes:
    """Serialize hash material with deterministic mapping and collection order."""

    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {key: normalize(item[key]) for key in sorted(item)}
        if isinstance(item, (list, tuple, set)):
            normalized = [normalize(child) for child in item]
            return sorted(
                normalized,
                key=lambda child: json.dumps(
                    child, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ),
            )
        if isinstance(item, Path):
            return item.as_posix()
        return item

    return json.dumps(
        normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _build_identity_material(
    revision: dict[str, Any],
    lock_details: list[dict[str, str | None]],
    bindings: list[dict[str, Any]],
    artifact_digests: list[str],
) -> dict[str, Any]:
    """Select only stable build inputs; execution diagnostics are deliberately absent."""

    stable_locks = [
        {
            key: value
            for key, value in details.items()
            if key in {"binding_id", "profile_id", "profile_version", "sha256"}
        }
        for details in lock_details
    ]
    stable_bindings = []
    for binding in bindings:
        profile_id = str(binding.get("profile_id", ""))
        bundle = load_profile_bundle(profile_id)
        stable_bindings.append(
            {
                "binding_id": binding.get("binding_id"),
                "unit_id": binding.get("unit_id"),
                "unit_path": str(binding.get("unit_path", ".")).replace("\\", "/"),
                "profile_id": profile_id,
                "profile_version": bundle.profile.get("version"),
                "profile_scope": binding.get("profile_scope"),
                "selection_decision": binding.get("selection_decision"),
            }
        )
    return {
        "identity_contract": "lks-sdd-build-1.0",
        "revision": revision.get("revision"),
        "tree_id": revision.get("tree_id"),
        "tree_sha256": revision.get("tree_sha256"),
        "locks": stable_locks,
        "profile_bindings": stable_bindings,
        "artifact_digests": sorted(set(artifact_digests)),
    }


def _verification_run_id(outcomes: list[dict[str, Any]], compose_project: str) -> str:
    material = {
        "identity_contract": "lks-sdd-verification-run-1.0",
        "time_ns": time.time_ns(),
        "pid": os.getpid(),
        "compose_project": compose_project,
        "outcomes": outcomes,
    }
    return "run-sha256:" + hashlib.sha256(_canonical_hash_payload(material)).hexdigest()


def _build_id(build_material: dict[str, Any]) -> str:
    return "build-sha256:" + hashlib.sha256(
        _canonical_hash_payload(build_material)
    ).hexdigest()


def _has_unallowed_dirty_paths(
    revision: dict[str, Any], allowed_relative_paths: set[str]
) -> bool:
    if revision.get("kind") != "git" or not revision.get("dirty"):
        return False
    return bool(set(revision.get("dirty_paths", [])) - allowed_relative_paths)


def _delivery_template(
    *,
    release: str,
    environment: str,
    revision: dict[str, Any],
    build_id: str,
    artifact_digests: list[str],
    technical_run_id: str,
) -> dict[str, Any]:
    pending_check = {
        "status": "pending",
        "recorded_at": "pending",
        "reference": "pending: replace with immutable evidence reference",
    }
    return {
        "schema_version": "1.1",
        "evidence_state": "draft",
        "technical_run_id": technical_run_id,
        "release": release,
        "environment": environment,
        "revision": revision["revision"],
        "tree_id": revision["tree_id"],
        "tree_sha256": revision["tree_sha256"],
        "build_id": build_id,
        "artifact_digests": sorted(set(artifact_digests)),
        "promotion": dict(pending_check),
        "smoke": dict(pending_check),
        "observability": dict(pending_check),
        "recovery": dict(pending_check),
        "authorization": {
            **pending_check,
            "authority": "pending: record the exact release authority",
        },
    }


def _materialize_delivery_template(root: Path, requested: Path, value: dict[str, Any]) -> str:
    candidate = requested if requested.is_absolute() else root / requested
    _assert_safe_path(root, candidate)
    relative = candidate.absolute().relative_to(root).as_posix()
    if not re.fullmatch(r"docs/lks-sdd/evidence/delivery/[A-Za-z0-9._-]+\.json", relative):
        raise VerificationError(
            "La plantilla G4 debe estar bajo docs/lks-sdd/evidence/delivery/ y usar .json."
        )
    if candidate.exists():
        raise VerificationError(f"La plantilla G4 ya existe: {relative}.")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    _assert_safe_path(root, candidate.parent)
    content = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        with candidate.open("xb") as stream:
            stream.write(content)
    except OSError as exc:
        raise VerificationError(f"No se puede materializar la plantilla G4: {exc}") from exc
    return relative


def _run_v12(
    args: argparse.Namespace,
    root: Path,
    report: Any,
    manifest: dict[str, Any],
    definitions: dict[str, dict[str, str]],
) -> tuple[int, dict[str, Any]]:
    # `run()` is also a supported internal test/integration seam.  Keep newly
    # added CLI options backwards-compatible for callers that construct an
    # argparse.Namespace directly instead of going through `main()`.
    for name, default in (
        ("task", None),
        ("execution_id", None),
        ("environment", "not-applicable"),
        ("delivery_evidence", None),
        ("materialize_delivery_template", None),
    ):
        if not hasattr(args, name):
            setattr(args, name, default)
    blockers = list(report.errors)
    if not re.fullmatch(r"(?:ENV-[0-9]{3}|not-applicable)", args.environment):
        blockers.append(
            "--environment debe usar ENV-### o not-applicable."
        )
    manifest_path, loaded_manifest, initial_manifest = _load_manifest(root)
    if loaded_manifest != manifest:
        blockers.append("project.json cambió durante la validación inicial.")
    projected_implementation = manifest.get("implementation", {})
    implementation = projected_implementation
    selected_execution: dict[str, Any] | None = None
    requested_tasks = list(dict.fromkeys(args.task or []))
    if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
        executions = [
            item
            for item in manifest.get("executions", [])
            if isinstance(item, dict) and item.get("increment") == args.increment
        ]
        if args.execution_id is not None:
            if not re.fullmatch(r"EXEC-[0-9]{3}", args.execution_id):
                blockers.append("--execution-id debe usar EXEC-###.")
                executions = []
            else:
                executions = [
                    item
                    for item in executions
                    if item.get("execution_id") == args.execution_id
                ]
        elif requested_tasks:
            executions = [
                item
                for item in executions
                if set(requested_tasks) <= set(item.get("task_ids", []))
            ]
        else:
            projected_tasks = set(projected_implementation.get("task_ids", []))
            executions = [
                item
                for item in executions
                if set(item.get("task_ids", [])) == projected_tasks
            ]
        if len(executions) != 1:
            blockers.append(
                "La verificación 1.3 necesita una única EXEC-###; use "
                "--execution-id cuando la selección sea ambigua."
            )
        else:
            selected_execution = executions[0]
            # Without an explicit execution/task selector, `implementation`
            # remains the canonical compatibility projection of the current
            # slice.  An EXEC snapshot identifies and attributes that slice,
            # but must not hide a later change to its current status, bindings
            # or locks.  Explicit historical/parallel selections instead use
            # the immutable execution context.
            if args.execution_id is not None or requested_tasks:
                execution_status = selected_execution.get("status")
                implementation = {
                    "status": (
                        "completed"
                        if execution_status in {"in-review", "completed"}
                        else "in-progress"
                        if execution_status == "in-progress"
                        else "blocked"
                    ),
                    "increment": selected_execution.get("increment"),
                    "task_ids": selected_execution.get("task_ids", []),
                    "profile_bindings": selected_execution.get(
                        "profile_bindings", []
                    ),
                    "locks": selected_execution.get("locks", []),
                    "branch": selected_execution.get("branch"),
                    "revision_start": selected_execution.get("revision_start"),
                    "changed_paths": selected_execution.get("changed_paths", []),
                    "evidence_ids": selected_execution.get("evidence_ids", []),
                }
    if implementation.get("increment") != args.increment:
        blockers.append(
            "implementation.increment no coincide con el solicitado."
        )
    allowed_status = {"in-progress", "completed"} if args.plan else {"completed"}
    if implementation.get("status") not in allowed_status:
        blockers.append(
            "La verificación requiere implementation.status=completed; "
            "el plan admite además in-progress."
        )
    task_ids = list(implementation.get("task_ids", []))
    if requested_tasks:
        missing = sorted(set(requested_tasks) - set(task_ids))
        if missing:
            blockers.append(
                f"Las tareas no pertenecen a la implementación: {missing}."
            )
        else:
            task_ids = requested_tasks
    planning_state: dict[str, Any] | None = None
    authorization_state: dict[str, Any] | None = None
    if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
        planning_state = assess_planning(root, manifest, args.increment)
        authorization_state = assess_authorization(
            manifest, planning_state, task_ids
        )
        if planning_state.get("status") == "stale" or planning_state.get(
            "integrity"
        ) != "valid":
            blockers.append(
                "La planificación cambió o es inválida; reconcilie antes de verificar."
            )
        if authorization_state.get("status") != "authorized":
            blockers.append(
                "La verificación no conserva una autorización vigente para las tareas."
            )
    delivery = validate_delivery_contract(root, manifest)
    blockers.extend(delivery["errors"])
    for task_id in task_ids:
        state = delivery["tasks"].get(task_id, {}).get("Workflow state")
        if state not in {"in-progress", "in-review", "done"}:
            blockers.append(
                f"{task_id} debe estar in-progress, in-review o done; está {state}."
            )

    bindings_by_id = {
        item.get("binding_id"): item
        for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict)
    }
    bindings: list[dict[str, Any]] = []
    lock_details: list[dict[str, str | None]] = []
    implementation_locks = {
        item.get("binding_id"): item.get("sha256")
        for item in implementation.get("locks", [])
        if isinstance(item, dict)
    }
    selected_binding_ids = _binding_ids_for_tasks(task_ids, delivery)
    execution_binding_ids = set(implementation.get("profile_bindings", []))
    for binding_id in sorted(execution_binding_ids):
        if binding_id not in bindings_by_id:
            blockers.append(f"Binding de implementación inexistente: {binding_id}.")
    missing_selected_bindings = sorted(set(selected_binding_ids) - execution_binding_ids)
    if missing_selected_bindings:
        blockers.append(
            "Los bindings de las tareas seleccionadas no pertenecen a la ejecución: "
            + ", ".join(missing_selected_bindings)
            + "."
        )
    for binding_id in selected_binding_ids:
        binding = bindings_by_id.get(binding_id)
        if binding is None:
            blockers.append(f"Binding de implementación inexistente: {binding_id}.")
            continue
        bindings.append(binding)
        profile_id = str(binding.get("profile_id"))
        blockers.extend(
            validate_profile(profile_id, require_validated=True)
        )
        lock_errors, details = validate_consumer_profile_lock(
            root,
            profile_id=profile_id,
            binding_id=binding_id,
            required=True,
        )
        blockers.extend(lock_errors)
        if implementation_locks.get(binding_id) != details.get("sha256"):
            blockers.append(
                f"{binding_id}: el lock no coincide con implementation.locks."
            )
        lock_details.append(details)
    if not bindings:
        blockers.append("No hay bindings verificables en implementation.")

    initial_contract_fingerprint, contract_errors = _active_contract_snapshot(
        root, args.increment
    )
    blockers.extend(contract_errors)
    revision_before = repository_revision(root)
    allowed_dirty_paths: set[str] = set()
    if args.delivery_evidence is not None:
        candidate = args.delivery_evidence if args.delivery_evidence.is_absolute() else root / args.delivery_evidence
        try:
            allowed_dirty_paths.add(candidate.absolute().relative_to(root).as_posix())
        except ValueError:
            pass
    if not args.plan and _has_unallowed_dirty_paths(revision_before, allowed_dirty_paths):
        blockers.append(
            "No se puede atribuir verificación a un Git con cambios sin confirmar."
        )

    profile_checks: list[dict[str, Any]] = []
    for binding in bindings:
        bundle = load_profile_bundle(str(binding["profile_id"]))
        for check in bundle.driver.get("verify", {}).get("checks", []):
            if check.get("kind") != "command" or check.get("phase") == "G4":
                continue
            profile_checks.append(
                _profile_command(root, binding, check)
            )
    plan = [
        {
            "name": item["name"],
            "gate_id": item["gate_id"],
            "binding_id": item["binding_id"],
            "cwd": str(item["cwd"].relative_to(root)),
            "command": item["command"],
            "required": item["required"],
            "requires_containers": item["requires_containers"],
        }
        for item in profile_checks
    ]
    visual_applicability: dict[str, Any] = {
        "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
        "status": "not-assessed",
        "scope": "task-slice",
        "task_ids": sorted(task_ids),
        "reason": "verification-contract-invalid",
    }
    visual_required = False
    if not blockers:
        visual_applicability = _visual_applicability(
            root, manifest, args.increment, task_ids, delivery
        )
        visual_required = visual_applicability["status"] == "applicable"
    if args.visual_evidence is not None and not visual_required:
        blockers.append(
            "Se aportó evidencia visual para un incremento sin interfaz applicable."
        )
    if visual_required:
        plan.append(
            {
                "name": "visual-browser-review",
                "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
                "binding_id": None,
                "binding_ids": [item["binding_id"] for item in bindings],
                "scope": "cross-cutting",
                "cwd": ".",
                "command": ["manual-browser-review", "--evidence", "<local-json>"],
                "required": True,
                "requires_containers": False,
            }
        )
    if blockers:
        return 3, {
            "classification": "not-verified",
            "increment": args.increment,
            "task_ids": task_ids,
            "blockers": list(dict.fromkeys(blockers)),
            "checks": [],
            "execution_ready": False,
            "profile_locks": lock_details,
            "execution_id": (
                selected_execution.get("execution_id")
                if selected_execution is not None
                else None
            ),
            "planning": planning_state,
            "implementation_authorization": authorization_state,
            "gate_applicability": [visual_applicability],
        }
    if args.plan:
        execution_ready = implementation.get("status") == "completed"
        limitations = ["No se ejecutó ninguna comprobación."]
        if not execution_ready:
            limitations.append(
                "El plan anticipa los checks, pero ejecutarlos o registrar evidencia "
                "requiere implementation.status=completed."
            )
        return 0, {
            "classification": "not-run",
            "increment": args.increment,
            "task_ids": task_ids,
            "checks": [
                {**item, "status": "not-run"} for item in plan
            ],
            "limitations": limitations,
            "execution_ready": execution_ready,
            "profile_locks": lock_details,
            "revision": revision_before,
            "execution_id": (
                selected_execution.get("execution_id")
                if selected_execution is not None
                else None
            ),
            "planning": planning_state,
            "implementation_authorization": authorization_state,
            "gate_applicability": [visual_applicability],
        }
    if not args.execute or not args.authorize:
        raise VerificationError(
            "La ejecución requiere --execute y --authorize tras revisar el plan."
        )

    env = os.environ.copy()
    env["COMPOSE_PROJECT_NAME"] = f"lkssddverify{os.getpid()}"
    outcomes: list[dict[str, Any]] = []
    try:
        for check in profile_checks:
            if check["requires_containers"] and not args.containers:
                outcomes.append(
                    {
                        "name": check["name"],
                        "gate_id": check["gate_id"],
                        "binding_id": check["binding_id"],
                        "status": "not-run",
                        "reason": "container-authorization-missing",
                    }
                )
                continue
            outcomes.append(_execute_profile_command(check, env))
    finally:
        if args.containers:
            outcomes.extend(
                _cleanup_profile_compositions(root, profile_checks, env)
            )

    limitations: list[str] = []
    if visual_required:
        visual, visual_limitations = _visual_evidence_check(
            root,
            args.increment,
            args.visual_evidence,
            manifest,
            definitions,
        )
        visual["gate_id"] = "GATE-VISUAL-BROWSER-REVIEW"
        outcomes.append(visual)
        limitations.extend(visual_limitations)
    delivery_value: dict[str, Any] | None = None
    if args.delivery_evidence is not None:
        candidate = (
            args.delivery_evidence
            if args.delivery_evidence.is_absolute()
            else root / args.delivery_evidence
        )
        _assert_safe_path(root, candidate)
        if not candidate.is_file():
            raise VerificationError(
                "--delivery-evidence debe ser un archivo del proyecto."
            )
        delivery_value, delivery_errors = load_delivery_evidence(candidate)
        selected_releases = {
            delivery["tasks"][task_id].get("Release")
            for task_id in task_ids
            if task_id in delivery["tasks"]
        }
        declared_release = delivery_value.get("release")
        if selected_releases != {declared_release}:
            delivery_errors.append(
                "delivery.release no coincide de forma unívoca con las tareas verificadas."
            )
        release_row = delivery["releases"].get(str(declared_release))
        if release_row is None:
            delivery_errors.append("delivery.release no existe en ART-PLANS.")
        else:
            release_environments = set(
                re.findall(r"\bENV-[0-9]{3}\b", release_row.get("Environments", ""))
            )
            if delivery_value.get("environment") not in release_environments:
                delivery_errors.append(
                    "delivery.environment no pertenece a la release declarada."
                )
        environment_row = delivery["environments"].get(
            str(delivery_value.get("environment"))
        )
        if environment_row is None or environment_row.get("State") != "confirmed":
            delivery_errors.append(
                "delivery.environment debe existir y estar confirmed."
            )
        outcomes.append(
            {
                "name": "delivery-evidence",
                "gate_id": "GATE-DELIVERY-EVIDENCE",
                "status": "passed" if not delivery_errors else "failed",
                "errors": delivery_errors,
            }
        )
    else:
        limitations.append(
            "G4 de promoción/despliegue no se evaluó; no se aportó --delivery-evidence."
        )
    required_failures = [
        item
        for item in outcomes
        if item.get("status") != "passed"
        and item.get("name") != "compose-cleanup"
    ]
    revision_after = repository_revision(root)
    current_contract, current_contract_errors = _active_contract_snapshot(
        root, args.increment
    )
    if current_contract_errors or current_contract != initial_contract_fingerprint:
        required_failures.append(
            {"name": "contract-stability", "status": "failed"}
        )
    if (
        revision_after["revision"] != revision_before["revision"]
        or revision_after["tree"] != revision_before["tree"]
        or (
            revision_after["kind"] == "git"
            and _has_unallowed_dirty_paths(revision_after, allowed_dirty_paths)
        )
    ):
        required_failures.append(
            {"name": "revision-stability", "status": "failed"}
        )
    if required_failures:
        classification = "not-verified"
    elif limitations:
        classification = "verified-with-reservations"
    else:
        classification = "verified"
    artifact_digests = _artifact_digests(
        root, bindings, profile_checks
    )
    tree_id = str(revision_after["tree_id"])
    tree_sha256 = str(revision_after["tree_sha256"])
    build_material = _build_identity_material(
        revision_after, lock_details, bindings, artifact_digests
    )
    build_id = _build_id(build_material)
    verification_run_id = _verification_run_id(outcomes, env["COMPOSE_PROJECT_NAME"])
    if delivery_value is not None:
        delivery_mismatches: list[str] = []
        if delivery_value.get("revision") != revision_after["revision"]:
            delivery_mismatches.append(
                "delivery.revision no coincide con la revisión verificada"
            )
        if delivery_value.get("tree_id") != tree_id:
            delivery_mismatches.append(
                "delivery.tree_id no coincide con el árbol verificado"
            )
        if delivery_value.get("schema_version") == "1.1" and delivery_value.get(
            "tree_sha256"
        ) != tree_sha256:
            delivery_mismatches.append(
                "delivery.tree_sha256 no coincide con el árbol verificado"
            )
        if delivery_value.get("build_id") != build_id:
            delivery_mismatches.append(
                "delivery.build_id no coincide con el build verificado"
            )
        if set(delivery_value.get("artifact_digests", [])) != set(
            artifact_digests
        ):
            delivery_mismatches.append(
                "delivery.artifact_digests no coincide con los artefactos verificados"
            )
        if delivery_mismatches:
            classification = "not-verified"
            for outcome in outcomes:
                if outcome.get("gate_id") == "GATE-DELIVERY-EVIDENCE":
                    outcome["status"] = "failed"
                    outcome.setdefault("errors", []).extend(
                        delivery_mismatches
                    )
    environment = (
        str(delivery_value["environment"])
        if delivery_value is not None and delivery_value.get("environment")
        else args.environment
    )
    result: dict[str, Any] = {
        "classification": classification,
        "increment": args.increment,
        "task_ids": task_ids,
        "checks": outcomes,
        "limitations": limitations,
        "evidence_recorded": False,
        "profile_locks": lock_details,
        "revision": revision_after,
        "tree_id": tree_id,
        "tree_sha256": tree_sha256,
        "build_id": build_id,
        "build_identity_material": build_material,
        "verification_run_id": verification_run_id,
        "artifact_digests": artifact_digests,
        "environment": environment,
        "planning": planning_state,
        "implementation_authorization": authorization_state,
        "gate_applicability": [visual_applicability],
        "execution_id": (
            selected_execution.get("execution_id")
            if selected_execution is not None
            else None
        ),
    }
    if args.materialize_delivery_template is not None:
        if delivery_value is not None:
            raise VerificationError(
                "No combine --materialize-delivery-template con --delivery-evidence."
            )
        if classification == "not-verified":
            raise VerificationError(
                "No se materializa G4 porque la verificación técnica no está superada."
            )
        if not re.fullmatch(r"ENV-[0-9]{3}", args.environment):
            raise VerificationError(
                "Materializar G4 requiere --environment ENV-###."
            )
        release_ids = {
            delivery["tasks"][task_id].get("Release")
            for task_id in task_ids
            if task_id in delivery["tasks"]
        }
        if len(release_ids) != 1:
            raise VerificationError("La plantilla G4 requiere una única REL-###.")
        result["delivery_template"] = _materialize_delivery_template(
            root,
            args.materialize_delivery_template,
            _delivery_template(
                release=str(next(iter(release_ids))),
                environment=args.environment,
                revision=revision_after,
                build_id=build_id,
                artifact_digests=artifact_digests,
                technical_run_id=verification_run_id,
            ),
        )
    if not args.record_evidence:
        return (0 if classification != "not-verified" else 3), result
    if not EVIDENCE_RE.fullmatch(args.record_evidence):
        raise VerificationError("--record-evidence debe usar EVID-###.")
    if manifest_path.read_bytes() != initial_manifest:
        raise VerificationError(
            "project.json cambió después de ejecutar los checks."
        )
    evidence_path = (
        root
        / "docs"
        / "lks-sdd"
        / "evidence"
        / f"{args.record_evidence}.json"
    )
    if evidence_path.exists():
        raise VerificationError(f"La evidencia ya existe: {evidence_path}.")
    trace_path = root / "docs/lks-sdd/05-quality/traceability.md"
    trace_original, trace_new = _updated_traceability(
        trace_path, args.increment, args.record_evidence
    )
    selected_profile = manifest.get("technology", {}).get("selected_profile")
    profile_versions = {
        item.get("profile_id"): item.get("profile_version")
        for item in build_material.get("profile_bindings", [])
        if isinstance(item, dict)
    }
    evidence = {
        "schema_version": "1.2",
        "evidence_id": args.record_evidence,
        **(
            {"execution_id": selected_execution["execution_id"]}
            if selected_execution is not None
            else {}
        ),
        "increment": args.increment,
        "profile_id": selected_profile,
        "profile_version": profile_versions.get(selected_profile),
        "task_ids": task_ids,
        "profile_bindings": [
            item["binding_id"] for item in bindings
        ],
        "profile_locks": lock_details,
        "revision": revision_after["revision"],
        "branch": revision_after.get("branch"),
        "tree_id": tree_id,
        "tree_sha256": tree_sha256,
        "build_id": build_id,
        "verification_run_id": verification_run_id,
        "build_identity_material": build_material,
        "artifact_digests": artifact_digests,
        "environment": environment,
        "classification": classification,
        "gate_ids": sorted(
            {item["gate_id"] for item in outcomes if item.get("gate_id")}
        ),
        "checks": outcomes,
        "gate_applicability": [visual_applicability],
        "limitations": limitations,
    }
    manifest_new = json.loads(json.dumps(manifest))
    manifest_new["phase"] = "verification"
    manifest_new["gate"] = "G4"
    manifest_new["last_verified_revision"] = str(
        revision_after["revision"]
    )
    manifest_new["verification"] = {
        "status": classification,
        **(
            {"execution_id": selected_execution["execution_id"]}
            if selected_execution is not None
            else {}
        ),
        "increment": args.increment,
        "task_ids": task_ids,
        "revision": str(revision_after["revision"]),
        "tree_id": tree_id,
        "tree_sha256": tree_sha256,
        "build_id": build_id,
        "artifact_digests": artifact_digests,
        "environment": environment,
        "gate_ids": evidence["gate_ids"],
        "evidence_ids": [args.record_evidence],
        "limitations": limitations,
    }
    if manifest.get("schema_version") in {"1.3", "1.4", "1.5"}:
        for execution in manifest_new.get("executions", []):
            if not isinstance(execution, dict):
                continue
            if (
                selected_execution is not None
                and execution.get("execution_id")
                == selected_execution.get("execution_id")
            ):
                execution["last_observed_revision"] = str(
                    revision_after["revision"]
                )
                execution["evidence_ids"] = sorted(
                    set(execution.get("evidence_ids", []))
                    | {args.record_evidence}
                )
    if delivery_value is not None and not any(
        item.get("status") == "failed"
        for item in outcomes
        if item.get("gate_id") == "GATE-DELIVERY-EVIDENCE"
    ):
        manifest_new["last_delivery"] = {
            "release": delivery_value["release"],
            "environment": delivery_value["environment"],
            "revision": delivery_value["revision"],
            "tree_id": delivery_value["tree_id"],
            "build_id": delivery_value["build_id"],
            "artifact_digests": delivery_value["artifact_digests"],
            "status": "verified",
            "evidence_ids": [args.record_evidence],
        }
    manifest_new_bytes = (
        json.dumps(manifest_new, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    evidence_bytes = (
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    temp_trace = trace_path.with_name(trace_path.name + ".lks-sdd.tmp")
    temp_manifest = manifest_path.with_name(
        manifest_path.name + ".lks-sdd.tmp"
    )
    try:
        with evidence_path.open("xb") as stream:
            stream.write(evidence_bytes)
        with temp_trace.open("xb") as stream:
            stream.write(trace_new)
        with temp_manifest.open("xb") as stream:
            stream.write(manifest_new_bytes)
        if (
            trace_path.read_bytes() != trace_original
            or manifest_path.read_bytes() != initial_manifest
        ):
            raise VerificationError(
                "Las entradas cambiaron antes de registrar evidencia."
            )
        os.replace(temp_trace, trace_path)
        os.replace(temp_manifest, manifest_path)
    except (OSError, VerificationError):
        if evidence_path.exists():
            evidence_path.unlink()
        for temporary in (temp_trace, temp_manifest):
            if temporary.exists():
                temporary.unlink()
        if trace_path.read_bytes() != trace_original:
            trace_path.write_bytes(trace_original)
        if manifest_path.read_bytes() != initial_manifest:
            manifest_path.write_bytes(initial_manifest)
        raise
    result["evidence_recorded"] = True
    result["evidence_id"] = args.record_evidence
    return (0 if classification != "not-verified" else 3), result


def _transition_summary(result: dict[str, Any]) -> dict[str, Any]:
    classification = str(result.get("classification", "not-verified"))
    checks = [item for item in result.get("checks", []) if isinstance(item, dict)]
    completed = [
        str(item.get("name")) for item in checks if item.get("status") == "passed"
    ]
    pending = [
        str(item.get("name"))
        for item in checks
        if item.get("status") in {"not-run", "skipped"}
    ]
    blocked = list(result.get("blockers", []))
    blocked.extend(
        str(item.get("name"))
        for item in checks
        if item.get("status") in {"failed", "blocked"}
    )
    if result.get("error"):
        blocked.append(str(result["error"]))
    planning = result.get("planning")
    planning_incomplete = isinstance(planning, dict) and (
        planning.get("status") != "complete"
        or planning.get("integrity") != "valid"
    )
    if planning_incomplete:
        pending.append(
            f"planificación {planning.get('status', 'not-assessed')}/"
            f"{planning.get('integrity', 'not-assessed')}"
        )
        unassigned = planning.get("coverage", {}).get("unassigned_items", [])
        if unassigned:
            pending.append("contrato sin tarea: " + ", ".join(unassigned))
    if classification == "verified" and planning_incomplete:
        next_step = (
            "Conservar la evidencia de la porción y completar o reconciliar la "
            "planificación antes de verificar conjuntamente o promover la release completa."
        )
        human_decision = (
            "Confirmar la planificación restante; la verificación de esta porción no "
            "autoriza ni completa la release."
        )
    elif classification == "verified":
        next_step = "Revisar la evidencia conjunta y solicitar por separado la promoción o entrega del artefacto exacto."
        human_decision = "Autorizar, diferir o rechazar la promoción del artefacto verificado."
    elif classification == "verified-with-reservations":
        next_step = "Resolver o aceptar explícitamente las reservas antes de cualquier promoción."
        human_decision = "Aceptar las limitaciones documentadas o exigir nueva verificación."
    elif classification == "not-run":
        next_step = "Revisar el plan y ejecutar los gates solo con implementación completa y autorización vigente."
        human_decision = "Autorizar o diferir la ejecución de la verificación."
    else:
        next_step = "Resolver checks fallidos, bloqueados o ausentes y repetir la verificación; no promover."
        human_decision = "Decidir corrección, bloqueo o replanificación según la evidencia observada."
    return {
        "where_we_are": f"verification-{classification}",
        "completed": completed,
        "in_progress": [],
        "pending": pending,
        "blocked": list(dict.fromkeys(blocked)),
        "next_step": next_step,
        "human_decision": human_decision,
    }


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        raise VerificationError(f"La raíz no es una carpeta: {root}")
    report, manifest, definitions = validate_project(root)
    blockers = list(report.errors)
    if manifest is None:
        blockers.append("Falta el índice LKS-SDD.")
        manifest = {}
    if manifest.get("schema_version") in {"1.2", "1.3", "1.4", "1.5"}:
        return _run_v12(
            args, root, report, manifest, definitions
        )
    initial_manifest = b""
    if manifest:
        _, loaded_manifest, initial_manifest = _load_manifest(root)
        if loaded_manifest != manifest:
            blockers.append(
                "project.json cambió durante la validación inicial; repita la verificación."
            )
    if manifest.get("active_increment") not in {None, args.increment}:
        blockers.append(
            f"Otro incremento está activo: {manifest.get('active_increment')}"
        )
    implementation_blockers, implementation_details = _implementation_gate(
        manifest, args.increment, planning=args.plan
    )
    blockers.extend(implementation_blockers)
    if manifest.get("technology", {}).get("selected_profile") != PROFILE_ID:
        blockers.append(
            "La verificación automatizada H0 requiere el perfil de referencia seleccionado."
        )
    blockers.extend(validate_profile(require_validated=True))
    lock_errors, lock_details = validate_consumer_profile_lock(root)
    blockers.extend(lock_errors)
    initial_contract_fingerprint = ""
    if manifest and not blockers:
        initial_contract_fingerprint, contract_errors = _active_contract_snapshot(
            root, args.increment
        )
        blockers.extend(contract_errors)
    visual_review_required = False
    if manifest and not blockers:
        visual_review_required = _interface_is_applicable(
            root, manifest, args.increment
        )
    if args.visual_evidence is not None and not visual_review_required:
        blockers.append(
            "Se aportó evidencia visual para un incremento cuya interfaz no está marcada applicable."
        )
    checks = _commands(root)
    plan = [
        {
            "name": item["name"],
            "cwd": str(item["cwd"].relative_to(root)),
            "command": item["command"],
        }
        for item in checks
    ]
    if args.containers:
        plan.extend(
            {
                "name": name,
                "cwd": ".",
                "command": ["docker", "compose", "<managed-by-runner>"],
            }
            for name in (
                "compose-config",
                "compose-build-and-start",
                "backend-health",
                "frontend-smoke",
                "keycloak-oidc-discovery",
                "compose-cleanup",
            )
        )
    if visual_review_required:
        plan.append(
            {
                "name": "visual-browser-review",
                "cwd": ".",
                "command": ["manual-browser-review", "--evidence", "<local-json>"],
            }
        )
    if blockers:
        return 3, {
            "classification": "not-verified",
            "increment": args.increment,
            "blockers": blockers,
            "checks": [],
            "execution_ready": False,
            "implementation": implementation_details,
            "profile_lock": lock_details,
        }
    if args.plan:
        execution_ready = implementation_details.get("status") == "completed"
        limitations = ["No se ejecutó ninguna comprobación."]
        if not execution_ready:
            limitations.append(
                "El plan anticipa los checks, pero ejecutarlos o registrar evidencia "
                "requiere implementation.status=completed."
            )
        return 0, {
            "classification": "not-run",
            "increment": args.increment,
            "checks": [{**item, "status": "not-run"} for item in plan],
            "limitations": limitations,
            "execution_ready": execution_ready,
            "implementation": implementation_details,
            "profile_lock": lock_details,
        }
    if not args.execute or not args.authorize:
        raise VerificationError(
            "La ejecución requiere --execute y --authorize tras revisar el plan."
        )

    outcomes = [_execute_check(check) for check in checks]
    if args.containers and all(item["status"] == "passed" for item in outcomes):
        outcomes.extend(_container_checks(root))
    limitations: list[str] = []
    if visual_review_required:
        visual_outcome, visual_limitations = _visual_evidence_check(
            root, args.increment, args.visual_evidence, manifest, definitions
        )
        outcomes.append(visual_outcome)
        limitations.extend(visual_limitations)
    failures = [item for item in outcomes if item["status"] != "passed"]
    if not args.containers:
        limitations.append(
            "No se ejecutó la integración local con PostgreSQL y Keycloak."
        )
    if not args.record_evidence:
        limitations.append(
            "El resultado no se registró como evidencia canónica enlazada."
        )
    if failures:
        classification = "not-verified"
    elif limitations:
        classification = "verified-with-reservations"
    else:
        classification = "verified"

    result: dict[str, Any] = {
        "classification": classification,
        "increment": args.increment,
        "checks": outcomes,
        "limitations": limitations,
        "evidence_recorded": False,
        "profile_lock": lock_details,
    }
    if args.record_evidence:
        if not EVIDENCE_RE.fullmatch(args.record_evidence):
            raise VerificationError("--record-evidence debe usar EVID-###.")
        evidence_path = (
            root / "docs" / "lks-sdd" / "evidence" / f"{args.record_evidence}.json"
        )
        if evidence_path.exists():
            raise VerificationError(
                f"La evidencia ya existe: {evidence_path.relative_to(root)}"
            )
        (
            manifest_path,
            current_manifest,
            original_manifest,
            lock_details,
        ) = _revalidate_evidence_gate(
            root,
            args.increment,
            initial_manifest=initial_manifest,
            initial_contract_fingerprint=initial_contract_fingerprint,
            initial_lock_details=lock_details,
        )
        result["profile_lock"] = lock_details
        trace_path = root / "docs" / "lks-sdd" / "05-quality" / "traceability.md"
        _assert_safe_path(root, trace_path)
        original_trace, updated_trace = _updated_traceability(
            trace_path, args.increment, args.record_evidence
        )
        evidence = {
            "evidence_id": args.record_evidence,
            "increment": args.increment,
            "profile_id": PROFILE_ID,
            "profile_version": "1.0.0-candidate.1",
            "revision": current_manifest.get("last_verified_revision"),
            "classification": classification,
            "checks": outcomes,
            "limitations": limitations,
        }
        evidence_parent_created = False
        evidence_created = False
        trace_replaced = False
        manifest_replaced = False
        trace_temporary = trace_path.with_name(
            trace_path.name + ".lks-sdd-evidence.tmp"
        )
        manifest_temporary = manifest_path.with_name(
            manifest_path.name + ".lks-sdd-evidence.tmp"
        )
        _assert_safe_path(root, evidence_path)
        _assert_safe_path(root, trace_temporary)
        _assert_safe_path(root, manifest_temporary)
        try:
            evidence_parent_created = not evidence_path.parent.exists()
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            with evidence_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(evidence, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            evidence_created = True
            current_manifest["phase"] = "verification"
            current_manifest["gate"] = "G4"
            current_manifest["verification"] = {
                "status": classification,
                "increment": args.increment,
                "evidence_ids": [args.record_evidence],
                "limitations": limitations,
            }
            with trace_temporary.open("xb") as stream:
                stream.write(updated_trace)
            with manifest_temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(
                    json.dumps(current_manifest, indent=2, ensure_ascii=False) + "\n"
                )
            if trace_path.read_bytes() != original_trace:
                raise VerificationError(
                    "La trazabilidad cambió durante el registro de evidencia."
                )
            if manifest_path.read_bytes() != original_manifest:
                raise VerificationError(
                    "project.json cambió durante el registro de evidencia."
                )
            os.replace(trace_temporary, trace_path)
            trace_replaced = True
            os.replace(manifest_temporary, manifest_path)
            manifest_replaced = True
            updated_report, _, _ = validate_project(root)
            if not updated_report.valid:
                raise VerificationError(
                    "El proyecto no valida después de registrar la evidencia: "
                    + "; ".join(updated_report.errors)
                )
        except (OSError, VerificationError) as exc:
            if manifest_replaced:
                manifest_path.write_bytes(original_manifest)
            if trace_replaced:
                trace_path.write_bytes(original_trace)
            for temporary in (trace_temporary, manifest_temporary):
                try:
                    temporary.unlink()
                except OSError:
                    pass
            if evidence_created:
                try:
                    evidence_path.unlink()
                except OSError:
                    pass
            if evidence_parent_created:
                try:
                    evidence_path.parent.rmdir()
                except OSError:
                    pass
            raise VerificationError(
                f"Se revirtió el registro de evidencia: {exc}"
            ) from exc
        result["evidence_recorded"] = True
        result["evidence_path"] = evidence_path.relative_to(root).as_posix()
    return (0 if classification != "not-verified" else 3), result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--task", action="append")
    parser.add_argument(
        "--execution-id",
        help="EXEC-### exacta; obligatoria cuando varias ejecuciones incluyen la misma selección.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--containers", action="store_true")
    parser.add_argument(
        "--environment",
        default="not-applicable",
        help="ENV-### verificado o not-applicable para verificación local.",
    )
    parser.add_argument(
        "--delivery-evidence",
        type=Path,
        help="JSON G4 con promoción, despliegue, smoke, observabilidad y recovery.",
    )
    parser.add_argument(
        "--materialize-delivery-template",
        type=Path,
        help=(
            "Crea tras G3 una plantilla G4 1.1 ligada al build bajo "
            "docs/lks-sdd/evidence/delivery/, sin declarar sus checks como passed."
        ),
    )
    parser.add_argument(
        "--visual-evidence",
        type=Path,
        help=(
            "JSON local de revisión manual/browser bajo "
            "docs/lks-sdd/evidence/visual/ para incrementos con interfaz."
        ),
    )
    parser.add_argument("--record-evidence")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        code, result = run(args)
    except VerificationError as exc:
        code, result = (
            2,
            {"classification": "not-verified", "error": str(exc), "checks": []},
        )
    result["transition_summary"] = _transition_summary(result)
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print(result["classification"])
        for check in result.get("checks", []):
            print(f"{check.get('status', 'unknown').upper()}: {check['name']}")
        for limitation in result.get("limitations", []):
            print(f"LIMITATION: {limitation}")
    return code


if __name__ == "__main__":
    sys.exit(main())
