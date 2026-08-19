#!/usr/bin/env python3
"""Run the reproducible technical gate for the LKS-SDD H0 scaffold."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from validate_reference_profile import PROFILE_ROOT, validate_profile


PYTHON_IMAGE = "python:3.14.7-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
NODE_IMAGE = "node:24.19.0-alpine@sha256:d32cdf619f63fe0471182d08996dd516c6275bb5fd31ae06e55a570bd9e1ad43"


def _run(
    name: str,
    command: list[str],
    cwd: Path,
    results: list[dict[str, Any]],
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> bool:
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        results.append(
            {
                "name": name,
                "status": "failed",
                "duration_seconds": round(time.monotonic() - started, 3),
                "error": str(exc),
                "command": command[0],
            }
        )
        return False
    results.append(
        {
            "name": name,
            "status": "passed" if process.returncode == 0 else "failed",
            "exit_code": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": process.stdout[-2000:],
            "stderr_tail": process.stderr[-2000:],
        }
    )
    return process.returncode == 0


def _docker_mount(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _wait_http(name: str, url: str, results: list[dict[str, Any]], timeout: int = 180) -> bool:
    started = time.monotonic()
    last_error = ""
    while time.monotonic() - started < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 400:
                    results.append(
                        {
                            "name": name,
                            "status": "passed",
                            "duration_seconds": round(time.monotonic() - started, 3),
                            "url": url,
                        }
                    )
                    return True
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        time.sleep(2)
    results.append(
        {
            "name": name,
            "status": "failed",
            "duration_seconds": round(time.monotonic() - started, 3),
            "url": url,
            "error": last_error or "timeout",
        }
    )
    return False


def _run_local(work: Path, results: list[dict[str, Any]]) -> bool:
    backend = work / "apps" / "backend"
    frontend = work / "apps" / "frontend"
    npx = "npx.cmd" if os.name == "nt" else "npx"
    checks = [
        ("backend-sync", ["uv", "sync", "--frozen"], backend),
        ("backend-lint", ["uv", "run", "ruff", "check", "."], backend),
        ("backend-typecheck", ["uv", "run", "mypy"], backend),
        ("backend-tests", ["uv", "run", "pytest"], backend),
        (
            "backend-openapi",
            [
                "uv",
                "run",
                "python",
                "-c",
                "import sys; sys.path.insert(0, 'src'); from lks_sdd_app.main import app; "
                "assert app.openapi()['openapi'].startswith('3.1.')",
            ],
            backend,
        ),
        ("frontend-install", [npx, "--yes", "pnpm@10.34.5", "install", "--frozen-lockfile"], frontend),
        ("frontend-lint", [npx, "--yes", "pnpm@10.34.5", "lint"], frontend),
        ("frontend-typecheck", [npx, "--yes", "pnpm@10.34.5", "typecheck"], frontend),
        ("frontend-tests", [npx, "--yes", "pnpm@10.34.5", "test"], frontend),
        ("frontend-build", [npx, "--yes", "pnpm@10.34.5", "build"], frontend),
    ]
    return all(_run(name, command, cwd, results) for name, command, cwd in checks)


def _run_docker(work: Path, results: list[dict[str, Any]]) -> bool:
    mount = _docker_mount(work)
    backend_script = (
        "python -m pip install --no-cache-dir uv==0.12.3 && "
        "cd /work/apps/backend && uv sync --frozen && uv run ruff check . && "
        "uv run mypy && uv run pytest && "
        "uv run python -c \"import sys; sys.path.insert(0, 'src'); from lks_sdd_app.main import app; "
        "assert app.openapi()['openapi'].startswith('3.1.')\""
    )
    frontend_script = (
        "npm install --global pnpm@10.34.5 && cd /work/apps/frontend && "
        "pnpm install --frozen-lockfile && pnpm lint && pnpm typecheck && pnpm test && pnpm build"
    )
    backend_ok = _run(
        "backend-gate-python-3.14.7",
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{mount}:/work",
            "--mount",
            "type=volume,destination=/work/apps/backend/.venv",
            PYTHON_IMAGE,
            "sh",
            "-lc",
            backend_script,
        ],
        work,
        results,
        timeout=900,
    )
    frontend_ok = _run(
        "frontend-gate-node-24.19.0",
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{mount}:/work",
            "--mount",
            "type=volume,destination=/work/apps/frontend/node_modules",
            NODE_IMAGE,
            "sh",
            "-lc",
            frontend_script,
        ],
        work,
        results,
        timeout=900,
    )
    return backend_ok and frontend_ok


def _run_compose(work: Path, results: list[dict[str, Any]]) -> bool:
    compose_file = work / "infra" / "compose" / "compose.yaml"
    project = f"lks-sdd-gate-{os.getpid()}"
    env = os.environ.copy()
    env.update(
        {
            "POSTGRES_USER": "lks_sdd_gate",
            "POSTGRES_PASSWORD": "synthetic-gate-password",
            "KEYCLOAK_ADMIN": "lks_sdd_gate_admin",
            "KEYCLOAK_ADMIN_PASSWORD": "synthetic-gate-admin-password",
            "LKS_SDD_KEYCLOAK_PORT": "18080",
            "LKS_SDD_BACKEND_PORT": "18000",
            "LKS_SDD_FRONTEND_PORT": "15173",
        }
    )
    base = ["docker", "compose", "-p", project, "-f", str(compose_file)]
    try:
        if not _run("compose-config", [*base, "config", "--quiet"], work, results, env=env):
            return False
        if not _run("compose-build-and-start", [*base, "up", "--detach", "--build"], work, results, env=env, timeout=1200):
            return False
        checks = [
            _wait_http("backend-health", "http://127.0.0.1:18000/health", results),
            _wait_http("frontend-smoke", "http://127.0.0.1:15173/", results),
            _wait_http(
                "keycloak-oidc-discovery",
                "http://127.0.0.1:18080/realms/lks-sdd/.well-known/openid-configuration",
                results,
            ),
        ]
        return all(checks)
    finally:
        _run("compose-cleanup", [*base, "down", "--volumes", "--remove-orphans"], work, results, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("local", "docker"), default="local")
    parser.add_argument("--containers", action="store_true", help="Run PostgreSQL, Keycloak, API, and frontend integration.")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    structural_errors = validate_profile(require_validated=False)
    results.append(
        {
            "name": "profile-structure",
            "status": "passed" if not structural_errors else "failed",
            "errors": structural_errors,
        }
    )
    passed = not structural_errors
    with tempfile.TemporaryDirectory(
        prefix="lks-sdd-profile-gate-", ignore_cleanup_errors=True
    ) as directory:
        work = Path(directory) / "reference-app"
        shutil.copytree(
            PROFILE_ROOT / "scaffold",
            work,
            ignore=shutil.ignore_patterns(
                ".venv",
                "node_modules",
                "dist",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "*.pyc",
                "*.tsbuildinfo",
            ),
        )
        if passed:
            passed = _run_docker(work, results) if args.runtime == "docker" else _run_local(work, results)
        if passed and args.containers:
            passed = _run_compose(work, results)

    complete = passed and args.runtime == "docker" and args.containers
    result = {
        "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
        "passed": passed,
        "complete_gate": complete,
        "runtime": args.runtime,
        "containers_executed": args.containers,
        "checks": results,
    }
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print("PASSED" if passed else "FAILED")
        print(f"complete_gate={str(complete).lower()}")
        for check in results:
            print(f"{check['status'].upper()}: {check['name']}")
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
