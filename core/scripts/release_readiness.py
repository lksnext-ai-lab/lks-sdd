#!/usr/bin/env python3
"""Check whether the current commit can enter the release gate without writing."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Preserve the read-only contract even when invoked without Python's -B option.
sys.dont_write_bytecode = True

import run_release_gate
import validate_plugin_contract


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "release-readiness-1.0"


class ReleaseReadinessError(Exception):
    """Expected error while gathering release-readiness evidence."""


def _git(arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ReleaseReadinessError(f"Git no pudo comprobar la release: {detail}")
    return completed.stdout.strip()


def _check(check_id: str, operation) -> dict[str, Any]:
    try:
        detail = operation()
    except (ReleaseReadinessError, run_release_gate.ReleaseGateError) as exc:
        return {"id": check_id, "status": "error", "detail": str(exc)}
    if isinstance(detail, str):
        return {"id": check_id, "status": "failed", "detail": detail}
    return {"id": check_id, "status": "passed", "detail": ""}


def _contract_check() -> str | None:
    errors = validate_plugin_contract.validate(PLUGIN_ROOT)
    if errors:
        return " | ".join(errors)
    return None


def _distribution_check(version: str) -> str | None:
    errors = validate_plugin_contract.validate_copilot_catalog(PLUGIN_ROOT, version)
    if errors:
        return " | ".join(errors)
    return None


def _worktree_check() -> str | None:
    if _git(["status", "--porcelain", "--untracked-files=all"]):
        return "El checkout debe estar limpio, incluidos archivos no versionados."
    return None


def _approval_check(version: str, channel: str) -> str | None:
    if channel == "candidate":
        return None
    run_release_gate._approved_release(
        PLUGIN_ROOT / "quality" / f"release-approval-v{version}.json",
        version,
    )
    return None


def _remote_checks(source_commit: str, version: str) -> tuple[str | None, str | None]:
    output = _git(
        [
            "ls-remote",
            "--heads",
            "--tags",
            "origin",
            "refs/heads/main",
            f"refs/tags/v{version}*",
        ]
    )
    main_ref = "refs/heads/main"
    tag_prefix = f"refs/tags/v{version}"
    main_commits: list[str] = []
    release_refs: list[str] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            raise ReleaseReadinessError("git ls-remote devolvió una línea inválida.")
        commit, remote_ref = parts
        if remote_ref == main_ref:
            main_commits.append(commit.lower())
        elif remote_ref == tag_prefix or remote_ref.startswith(f"{tag_prefix}^{{}}"):
            release_refs.append(remote_ref)
    if len(main_commits) != 1:
        source_failure = "No se pudo resolver de forma única origin/main."
    elif main_commits[0] != source_commit:
        source_failure = "HEAD no coincide con el commit actualmente integrado en origin/main."
    else:
        source_failure = None
    if release_refs:
        tag_failure = f"La etiqueta v{version} ya existe en remoto y no se puede reutilizar."
    else:
        tag_failure = None
    return source_failure, tag_failure


def build_report(channel: str) -> dict[str, Any]:
    """Evaluate only lightweight release preconditions for the current checkout."""

    checks: list[dict[str, Any]] = []
    try:
        version = run_release_gate._plugin_version()
        source_commit = _git(["rev-parse", "HEAD"]).lower()
    except (ReleaseReadinessError, run_release_gate.ReleaseGateError) as exc:
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "channel": channel,
            "readiness": "blocked",
            "checks": [{"id": "source-context", "status": "error", "detail": str(exc)}],
            "blockers": ["source-context"],
            "next_action": "Corrija el contexto Git o el manifest antes de reintentar.",
        }

    checks.append(_check("contract", _contract_check))
    checks.append(_check("distribution", lambda: _distribution_check(version)))
    checks.append(_check("worktree", _worktree_check))
    if channel == "stable":
        checks.append(_check("approval", lambda: _approval_check(version, channel)))
    else:
        checks.append(
            {
                "id": "approval",
                "status": "not-applicable",
                "detail": "El canal candidate no exige aprobación de release stable.",
            }
        )
    try:
        source_failure, tag_failure = _remote_checks(source_commit, version)
    except ReleaseReadinessError as exc:
        checks.extend(
            [
                {"id": "source", "status": "error", "detail": str(exc)},
                {"id": "release-tag", "status": "error", "detail": str(exc)},
            ]
        )
    else:
        checks.extend(
            [
                {
                    "id": "source",
                    "status": "failed" if source_failure else "passed",
                    "detail": source_failure or "",
                },
                {
                    "id": "release-tag",
                    "status": "failed" if tag_failure else "passed",
                    "detail": tag_failure or "",
                },
            ]
        )
    blockers = [check["id"] for check in checks if check["status"] in {"failed", "error"}]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "channel": channel,
        "version": version,
        "source_commit": source_commit,
        "checks": checks,
        "readiness": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "next_action": (
            "Ejecute el gate estable una vez sobre este SHA."
            if not blockers
            else "Corrija únicamente los bloqueos indicados y vuelva a ejecutar el preflight."
        ),
    }


def _write_report(path: Path, report: dict[str, Any]) -> None:
    output = path.expanduser().resolve()
    try:
        output.relative_to(PLUGIN_ROOT)
    except ValueError:
        pass
    else:
        raise ReleaseReadinessError(
            "--output debe estar fuera del repositorio para preservar el preflight de solo lectura."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("candidate", "stable"), default="stable")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(args.channel)
    try:
        if args.output is not None:
            _write_report(args.output, report)
    except ReleaseReadinessError as exc:
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA_VERSION,
                    "status": "error",
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["readiness"] == "ready":
        return 0
    if any(check["status"] == "error" for check in report["checks"]):
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
