#!/usr/bin/env python3
"""Verify that the configured GitHub distribution ref resolves to a release commit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "distribution-reference-observation-1.0"
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")


class DistributionReferenceError(Exception):
    """Expected error while validating a distribution reference."""


def _read_marketplace(path: Path) -> tuple[str, str]:
    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DistributionReferenceError(
            f"No se puede leer el catálogo de distribución: {exc}"
        ) from exc
    if not isinstance(marketplace, dict):
        raise DistributionReferenceError("El catálogo de distribución debe ser un objeto.")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        raise DistributionReferenceError("El catálogo de distribución no declara plugins.")
    matches = [
        plugin
        for plugin in plugins
        if isinstance(plugin, dict) and plugin.get("name") == "lks-sdd"
    ]
    if len(matches) != 1:
        raise DistributionReferenceError(
            f"Se esperaba una entrada lks-sdd; se encontraron {len(matches)}."
        )
    source = matches[0].get("source")
    if (
        not isinstance(source, dict)
        or source.get("source") != "github"
        or not isinstance(source.get("repo"), str)
        or not isinstance(source.get("ref"), str)
    ):
        raise DistributionReferenceError(
            "La entrada lks-sdd debe declarar una fuente GitHub con repo y ref."
        )
    repository = source["repo"]
    reference = source["ref"]
    if not REPOSITORY_RE.fullmatch(repository):
        raise DistributionReferenceError("El repositorio GitHub configurado no es válido.")
    if not REF_RE.fullmatch(reference):
        raise DistributionReferenceError("La referencia GitHub configurada no es válida.")
    return repository, reference


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
        raise DistributionReferenceError(
            f"No se puede consultar la referencia remota configurada: {detail}"
        )
    return completed.stdout


def _remote_refs(repository: str, reference: str) -> str:
    remote = f"https://github.com/{repository}.git"
    return _git(
        [
            "ls-remote",
            "--tags",
            "--heads",
            remote,
            f"refs/tags/{reference}*",
            f"refs/heads/{reference}",
        ]
    )


def _resolved_targets(output: str, reference: str) -> list[dict[str, str]]:
    direct_tag = f"refs/tags/{reference}"
    peeled_tag = f"{direct_tag}^{{}}"
    branch = f"refs/heads/{reference}"
    refs: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            raise DistributionReferenceError("git ls-remote devolvió una línea inválida.")
        commit, remote_ref = parts
        if not COMMIT_RE.fullmatch(commit):
            raise DistributionReferenceError("git ls-remote devolvió un commit inválido.")
        if remote_ref in {direct_tag, peeled_tag, branch}:
            refs[remote_ref] = commit.lower()

    targets: list[dict[str, str]] = []
    if peeled_tag in refs:
        targets.append({"kind": "tag", "commit": refs[peeled_tag]})
    elif direct_tag in refs:
        targets.append({"kind": "tag", "commit": refs[direct_tag]})
    if branch in refs:
        targets.append({"kind": "branch", "commit": refs[branch]})
    return targets


def build_report(
    marketplace_path: Path,
    source_commit: str,
    *,
    observed_at: str,
) -> dict[str, Any]:
    """Return a read-only observation of the configured distribution reference."""

    if not COMMIT_RE.fullmatch(source_commit):
        raise DistributionReferenceError("El commit de release debe ser un SHA válido.")
    repository, reference = _read_marketplace(marketplace_path)
    targets = _resolved_targets(_remote_refs(repository, reference), reference)
    expected_commit = source_commit.lower()
    status = (
        "passed"
        if len(targets) == 1 and targets[0]["commit"] == expected_commit
        else "failed"
    )
    if not targets:
        reason = "La referencia configurada no existe como etiqueta ni rama remota."
    elif len(targets) > 1:
        reason = "La referencia configurada es ambigua entre etiqueta y rama remotas."
    elif status == "failed":
        reason = "La referencia configurada no apunta al commit acreditado de la release."
    else:
        reason = ""
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "observed_at": observed_at,
        "configured_source": {
            "repository": repository,
            "reference": reference,
        },
        "source_commit": expected_commit,
        "resolved_targets": targets,
        "status": status,
        "reason": reason,
    }


def _default_source_commit() -> str:
    return _git(["rev-parse", "HEAD"]).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path | None, value: dict[str, Any]) -> None:
    if path is None:
        return
    output = path.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--marketplace",
        type=Path,
        default=PLUGIN_ROOT / ".github" / "plugin" / "marketplace.json",
    )
    parser.add_argument("--source-commit")
    parser.add_argument("--observed-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(
            args.marketplace,
            args.source_commit or _default_source_commit(),
            observed_at=args.observed_at or _utc_now(),
        )
    except DistributionReferenceError as exc:
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "error",
            "error": str(exc),
        }
        _write_json(args.output, report)
        print(json.dumps(report, ensure_ascii=False))
        return 2
    _write_json(args.output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
