#!/usr/bin/env python3
"""Verify that the Copilot Git ref contains the approved native plugin ZIP."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "distribution-reference-observation-1.1"
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")


class DistributionReferenceError(Exception):
    """Expected error while validating a distribution reference."""


def _read_marketplace(path: Path) -> tuple[str, str, str]:
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
    version = matches[0].get("version")
    if not REPOSITORY_RE.fullmatch(repository):
        raise DistributionReferenceError("El repositorio GitHub configurado no es válido.")
    if not REF_RE.fullmatch(reference):
        raise DistributionReferenceError("La referencia GitHub configurada no es válida.")
    if not isinstance(version, str) or reference != f"copilot-v{version}":
        raise DistributionReferenceError(
            "La referencia Copilot debe ser la etiqueta nativa de la versión declarada."
        )
    return repository, reference, version


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


def _native_package_inventory(path: Path, version: str) -> dict[str, str]:
    """Hash the files inside the one native plugin root, without extracting them."""

    try:
        with zipfile.ZipFile(path) as package:
            files: dict[str, str] = {}
            for entry in package.infolist():
                if entry.is_dir():
                    continue
                if not entry.filename.startswith("lks-sdd/"):
                    raise DistributionReferenceError("El ZIP Copilot contiene rutas fuera de lks-sdd/.")
                relative = entry.filename.removeprefix("lks-sdd/")
                if not relative or ".." in relative.split("/") or relative in files:
                    raise DistributionReferenceError("El ZIP Copilot contiene una ruta inválida o duplicada.")
                files[relative] = hashlib.sha256(package.read(entry)).hexdigest()
            manifest = json.loads(package.read("lks-sdd/plugin.json"))
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        raise DistributionReferenceError(f"El ZIP nativo Copilot no es legible: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != version:
        raise DistributionReferenceError("El ZIP nativo no declara la versión del catálogo.")
    if not files:
        raise DistributionReferenceError("El ZIP nativo Copilot está vacío.")
    return files


def _native_git_inventory(
    repository: str, reference: str, *, remote_override: str | None = None
) -> dict[str, str]:
    """Read an isolated fetch of the native tag; never alter the caller's checkout."""

    remote = remote_override or f"https://github.com/{repository}.git"
    with tempfile.TemporaryDirectory(prefix="lks-sdd-copilot-ref-") as temporary:
        commands = (
            ["git", "init", "--quiet", temporary],
            ["git", "-C", temporary, "fetch", "--quiet", "--no-tags", "--depth=1", remote, f"refs/tags/{reference}"],
            ["git", "-C", temporary, "archive", "--format=tar", "FETCH_HEAD"],
        )
        archive = b""
        for command in commands:
            completed = subprocess.run(command, capture_output=True, check=False)
            if completed.returncode != 0:
                raise DistributionReferenceError(
                    "No se pudo leer el árbol Git nativo: "
                    + completed.stderr.decode("utf-8", errors="replace").strip()
                )
            archive = completed.stdout
    files: dict[str, str] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tree:
            for entry in tree:
                if entry.isdir():
                    continue
                if not entry.isfile() or ".." in entry.name.split("/") or entry.name in files:
                    raise DistributionReferenceError("La etiqueta nativa contiene una ruta no regular o duplicada.")
                stream = tree.extractfile(entry)
                if stream is None:
                    raise DistributionReferenceError("No se pudo leer un archivo de la etiqueta nativa.")
                files[entry.name] = hashlib.sha256(stream.read()).hexdigest()
    except tarfile.TarError as exc:
        raise DistributionReferenceError(f"El árbol Git nativo no es legible: {exc}") from exc
    return files


def build_report(
    marketplace_path: Path,
    source_commit: str,
    native_package: Path,
    *,
    observed_at: str,
) -> dict[str, Any]:
    """Return a read-only observation of the configured distribution reference."""

    if not COMMIT_RE.fullmatch(source_commit):
        raise DistributionReferenceError("El commit de release debe ser un SHA válido.")
    repository, reference, version = _read_marketplace(marketplace_path)
    targets = _resolved_targets(_remote_refs(repository, reference), reference)
    expected_commit = source_commit.lower()
    native_files: dict[str, str] = {}
    tagged_files: dict[str, str] = {}
    if not targets:
        reason = "La referencia configurada no existe como etiqueta ni rama remota."
    elif len(targets) > 1:
        reason = "La referencia configurada es ambigua entre etiqueta y rama remotas."
    elif targets[0]["kind"] != "tag":
        reason = "La referencia Copilot debe ser una etiqueta inmutable."
    else:
        native_files = _native_package_inventory(native_package, version)
        tagged_files = _native_git_inventory(repository, reference)
        reason = (
            ""
            if tagged_files == native_files
            else "La etiqueta Copilot no coincide byte a byte con el ZIP nativo acreditado."
        )
    status = "passed" if not reason else "failed"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "observed_at": observed_at,
        "configured_source": {
            "repository": repository,
            "reference": reference,
        },
        "source_commit": expected_commit,
        "resolved_targets": targets,
        "native_package_files": len(native_files),
        "tagged_files": len(tagged_files),
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
    parser.add_argument("--native-package", type=Path, required=True)
    parser.add_argument("--observed-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(
            args.marketplace,
            args.source_commit or _default_source_commit(),
            args.native_package,
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
