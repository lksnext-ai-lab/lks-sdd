#!/usr/bin/env python3
"""Plan or execute the locked H0 verification checks for one increment."""

from __future__ import annotations

import argparse
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

from validate_project import validate_project
from validate_reference_profile import PROFILE_ID, validate_profile

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
            and cells[5].lower() in {"none", "pending", "not-run"}
        ):
            cells[5] = evidence_id
            lines[index] = "| " + " | ".join(cells) + " |"
            updated = True
    if not updated:
        raise VerificationError(
            "No existe una fila de trazabilidad pendiente para el incremento."
        )
    return original, ("\n".join(lines) + "\n").encode("utf-8")


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = args.project_root.expanduser().resolve()
    if not root.is_dir():
        raise VerificationError(f"La raíz no es una carpeta: {root}")
    report, manifest, _ = validate_project(root)
    blockers = list(report.errors)
    if manifest is None:
        blockers.append("Falta el índice LKS-SDD.")
        manifest = {}
    if manifest.get("active_increment") not in {None, args.increment}:
        blockers.append(
            f"Otro incremento está activo: {manifest.get('active_increment')}"
        )
    if manifest.get("technology", {}).get("selected_profile") != PROFILE_ID:
        blockers.append(
            "La verificación automatizada H0 requiere el perfil de referencia seleccionado."
        )
    blockers.extend(validate_profile(require_validated=True))
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
    if blockers:
        return 3, {
            "classification": "not-verified",
            "increment": args.increment,
            "blockers": blockers,
            "checks": [],
        }
    if args.plan:
        return 0, {
            "classification": "not-run",
            "increment": args.increment,
            "checks": [{**item, "status": "not-run"} for item in plan],
            "limitations": ["No se ejecutó ninguna comprobación."],
        }
    if not args.execute or not args.authorize:
        raise VerificationError(
            "La ejecución requiere --execute y --authorize tras revisar el plan."
        )

    outcomes = [_execute_check(check) for check in checks]
    if args.containers and all(item["status"] == "passed" for item in outcomes):
        outcomes.extend(_container_checks(root))
    failures = [item for item in outcomes if item["status"] != "passed"]
    limitations: list[str] = []
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
        manifest_path, current_manifest, original_manifest = _load_manifest(root)
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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--containers", action="store_true")
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
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["classification"])
        for check in result.get("checks", []):
            print(f"{check.get('status', 'unknown').upper()}: {check['name']}")
        for limitation in result.get("limitations", []):
            print(f"LIMITATION: {limitation}")
    return code


if __name__ == "__main__":
    sys.exit(main())
