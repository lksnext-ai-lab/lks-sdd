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
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from validate_project import validate_project  # noqa: E402
from validate_reference_profile import PROFILE_ID, validate_profile  # noqa: E402


EVIDENCE_RE = re.compile(r"^EVID-[0-9]{3}$")


class VerificationError(Exception):
    """Expected verification failure."""


def _commands(root: Path) -> list[dict[str, Any]]:
    npx = "npx.cmd" if os.name == "nt" else "npx"
    pnpm = [npx, "--yes", "pnpm@10.34.5"]
    return [
        {"name": "backend-lock", "cwd": root / "apps/backend", "command": ["uv", "sync", "--frozen"]},
        {"name": "backend-lint", "cwd": root / "apps/backend", "command": ["uv", "run", "ruff", "check", "."]},
        {"name": "backend-typecheck", "cwd": root / "apps/backend", "command": ["uv", "run", "mypy"]},
        {"name": "backend-tests", "cwd": root / "apps/backend", "command": ["uv", "run", "pytest"]},
        {
            "name": "backend-openapi",
            "cwd": root / "apps/backend",
            "command": [
                "uv",
                "run",
                "python",
                "-c",
                "import sys; sys.path.insert(0, 'src'); from lks_sdd_app.main import app; "
                "assert app.openapi()['openapi'].startswith('3.1.')",
            ],
        },
        {"name": "frontend-lock", "cwd": root / "apps/frontend", "command": [*pnpm, "install", "--frozen-lockfile"]},
        {"name": "frontend-lint", "cwd": root / "apps/frontend", "command": [*pnpm, "lint"]},
        {"name": "frontend-typecheck", "cwd": root / "apps/frontend", "command": [*pnpm, "typecheck"]},
        {"name": "frontend-tests", "cwd": root / "apps/frontend", "command": [*pnpm, "test"]},
        {"name": "frontend-build", "cwd": root / "apps/frontend", "command": [*pnpm, "build"]},
    ]


def _load_manifest(root: Path) -> tuple[Path, dict[str, Any]]:
    path = root / ".lks-sdd" / "project.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"No se puede leer project.json: {exc}") from exc
    return path, value


def _execute_check(check: dict[str, Any]) -> dict[str, Any]:
    cwd = check["cwd"]
    if not cwd.is_dir():
        return {"name": check["name"], "status": "blocked", "reason": "working-directory-missing"}
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


def _update_traceability(path: Path, increment: str, evidence_id: str) -> bytes:
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines()
    updated = False
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[3] == increment and cells[5].lower() in {"none", "pending", "not-run"}:
            cells[5] = evidence_id
            lines[index] = "| " + " | ".join(cells) + " |"
            updated = True
    if not updated:
        raise VerificationError("No existe una fila de trazabilidad pendiente para el incremento.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return original


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
        blockers.append(f"Otro incremento está activo: {manifest.get('active_increment')}")
    if manifest.get("technology", {}).get("selected_profile") != PROFILE_ID:
        blockers.append("La verificación automatizada H0 requiere el perfil de referencia seleccionado.")
    blockers.extend(validate_profile(require_validated=True))
    checks = _commands(root)
    plan = [
        {"name": item["name"], "cwd": str(item["cwd"].relative_to(root)), "command": item["command"]}
        for item in checks
    ]
    if blockers:
        return 3, {"classification": "not-verified", "increment": args.increment, "blockers": blockers, "checks": []}
    if args.plan:
        return 0, {
            "classification": "not-run",
            "increment": args.increment,
            "checks": [{**item, "status": "not-run"} for item in plan],
            "limitations": ["No se ejecutó ninguna comprobación."],
        }
    if not args.execute or not args.authorize:
        raise VerificationError("La ejecución requiere --execute y --authorize tras revisar el plan.")

    outcomes = [_execute_check(check) for check in checks]
    failures = [item for item in outcomes if item["status"] != "passed"]
    limitations: list[str] = []
    if not args.containers:
        limitations.append("No se ejecutó la integración local con PostgreSQL y Keycloak.")
    if args.containers:
        limitations.append("La integración de contenedores debe verificarse mediante el plan del proyecto; el runner no la inicia automáticamente.")
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
        evidence_path = root / "docs" / "lks-sdd" / "evidence" / f"{args.record_evidence}.json"
        if evidence_path.exists():
            raise VerificationError(f"La evidencia ya existe: {evidence_path.relative_to(root)}")
        manifest_path, current_manifest = _load_manifest(root)
        trace_path = root / "docs" / "lks-sdd" / "05-quality" / "traceability.md"
        original_manifest = manifest_path.read_bytes()
        original_trace = trace_path.read_bytes()
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
        try:
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            with evidence_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(evidence, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            _update_traceability(trace_path, args.increment, args.record_evidence)
            current_manifest["phase"] = "verification"
            current_manifest["gate"] = "G4"
            current_manifest["verification"] = {
                "status": classification,
                "increment": args.increment,
                "evidence_ids": [args.record_evidence],
                "limitations": limitations,
            }
            temporary = manifest_path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(current_manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            os.replace(temporary, manifest_path)
        except (OSError, VerificationError) as exc:
            manifest_path.write_bytes(original_manifest)
            trace_path.write_bytes(original_trace)
            try:
                evidence_path.unlink()
            except OSError:
                pass
            raise VerificationError(f"Se revirtió el registro de evidencia: {exc}") from exc
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
        code, result = 2, {"classification": "not-verified", "error": str(exc), "checks": []}
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
