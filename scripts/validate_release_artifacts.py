#!/usr/bin/env python3
"""Validate the packaged assets that accompany release evidence."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import validate_copilot_package


REPORT_SCHEMA_VERSION = "release-package-validation-1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ReleasePackageValidationError(Exception):
    """Expected failure while validating release package artifacts."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ReleasePackageValidationError(f"No se puede leer {label}: {exc}") from exc


def _manifest(candidate: Path) -> tuple[dict[str, Any], bytes]:
    content = _read_bytes(candidate / "release-manifest.json", "release-manifest.json")
    try:
        value = json.loads(content)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleasePackageValidationError(
            f"release-manifest.json no contiene JSON válido: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ReleasePackageValidationError("release-manifest.json debe ser un objeto.")
    return value, content


def _artifact_bytes(
    candidate: Path, manifest: dict[str, Any], name: str
) -> tuple[bytes, dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ReleasePackageValidationError("El manifiesto no declara artefactos.")
    matches = [
        item
        for item in artifacts
        if isinstance(item, dict) and item.get("path") == name
    ]
    if len(matches) != 1:
        raise ReleasePackageValidationError(
            f"El manifiesto no acredita exactamente el artefacto {name}."
        )
    artifact = matches[0]
    digest = artifact.get("sha256")
    size = artifact.get("size")
    if (
        not isinstance(digest, str)
        or SHA256_RE.fullmatch(digest) is None
        or not isinstance(size, int)
        or size < 0
    ):
        raise ReleasePackageValidationError(
            f"El manifiesto contiene integridad inválida para {name}."
        )
    content = _read_bytes(candidate / name, name)
    if len(content) != size or _sha256(content) != digest:
        raise ReleasePackageValidationError(
            f"El artefacto {name} no coincide con su manifiesto."
        )
    return content, artifact


def _safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if (
        not name
        or path == PurePosixPath(".")
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in name
        or ":" in name
    ):
        raise ReleasePackageValidationError("El ZIP contiene una ruta insegura.")
    return path


def _validate_bundle(data: bytes, label: str) -> None:
    try:
        with tempfile.TemporaryDirectory(prefix="lks-sdd-release-package-") as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for info in archive.infolist():
                    if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ReleasePackageValidationError(
                            f"El ZIP {label} contiene una entrada no permitida."
                        )
                    path = _safe_member(info.filename)
                    destination = root.joinpath(*path.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(info))
            validators = list(root.rglob("validate_plugin_contract.py"))
            if len(validators) != 1:
                raise ReleasePackageValidationError(
                    f"El ZIP {label} no contiene una raíz de plugin única."
                )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-X",
                    "utf8",
                    str(validators[0]),
                    str(validators[0].parent.parent),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if completed.returncode != 0:
                raise ReleasePackageValidationError(
                    f"El ZIP {label} no valida su contrato: "
                    f"{(completed.stderr or completed.stdout).strip()}"
                )
    except (OSError, zipfile.BadZipFile) as exc:
        raise ReleasePackageValidationError(f"El ZIP {label} es inválido: {exc}") from exc


def validate_candidate(candidate: Path) -> dict[str, Any]:
    """Validate the exact assets produced for a release candidate."""

    manifest, manifest_bytes = _manifest(candidate)
    version = manifest.get("plugin_version")
    source_commit = manifest.get("source_commit")
    if not isinstance(version, str) or not version or not isinstance(source_commit, str):
        raise ReleasePackageValidationError(
            "El manifiesto no acredita versión y commit de la release."
        )
    copilot_name = f"lks-sdd-copilot-plugin-v{version}.zip"
    plugin_name = f"lks-sdd-plugin-v{version}.zip"
    marketplace_name = f"lks-sdd-marketplace-v{version}.zip"
    copilot_bytes, _ = _artifact_bytes(candidate, manifest, copilot_name)
    plugin_bytes, _ = _artifact_bytes(candidate, manifest, plugin_name)
    marketplace_bytes, _ = _artifact_bytes(candidate, manifest, marketplace_name)

    try:
        validate_copilot_package.validate(copilot_bytes)
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        raise ReleasePackageValidationError(
            f"El ZIP Copilot acreditado es inválido: {exc}"
        ) from exc
    _validate_bundle(plugin_bytes, "plugin")
    _validate_bundle(marketplace_bytes, "marketplace")
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "passed",
        "plugin_version": version,
        "source_commit": source_commit,
        "release_manifest_sha256": _sha256(manifest_bytes),
        "checks": [
            {"id": "copilot-package", "status": "passed"},
            {"id": "plugin-bundle", "status": "passed"},
            {"id": "marketplace-bundle", "status": "passed"},
        ],
    }


def validate_report(candidate: Path, report: dict[str, Any]) -> None:
    """Confirm a package-validation report binds to the candidate manifest."""

    manifest, manifest_bytes = _manifest(candidate)
    expected_checks = [
        {"id": "copilot-package", "status": "passed"},
        {"id": "plugin-bundle", "status": "passed"},
        {"id": "marketplace-bundle", "status": "passed"},
    ]
    if not isinstance(report, dict) or (
        report.get("schema_version") != REPORT_SCHEMA_VERSION
        or report.get("status") != "passed"
        or report.get("plugin_version") != manifest.get("plugin_version")
        or report.get("source_commit") != manifest.get("source_commit")
        or report.get("release_manifest_sha256") != _sha256(manifest_bytes)
        or report.get("checks") != expected_checks
    ):
        raise ReleasePackageValidationError(
            "La validación de paquetes no está vinculada al manifiesto de release."
        )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate_candidate(args.candidate.expanduser().resolve())
    except ReleasePackageValidationError as exc:
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "blocked",
            "error": str(exc),
        }
        _write_json(args.output.expanduser().resolve(), report)
        print(json.dumps(report, ensure_ascii=False))
        return 2
    _write_json(args.output.expanduser().resolve(), report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
