#!/usr/bin/env python3
"""Create a read-only, hash-bound plan for promoting tag evidence to a draft release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import validate_copilot_package
import release_notes


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA_VERSION = "draft-promotion-plan-1.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


class DraftPromotionError(Exception):
    """Expected error while validating release evidence for draft promotion."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise DraftPromotionError(f"No se puede leer {label}: {exc}") from exc


def _read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    content = _read_bytes(path, label)
    try:
        value = json.loads(content)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DraftPromotionError(f"{label} no contiene JSON válido: {exc}") from exc
    if not isinstance(value, dict):
        raise DraftPromotionError(f"{label} debe ser un objeto JSON.")
    return value, content


def _safe_artifact_path(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise DraftPromotionError("El manifiesto contiene un path de artefacto inválido.")
    path = PurePosixPath(value)
    if (
        path == PurePosixPath(".")
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or ":" in value
    ):
        raise DraftPromotionError("El manifiesto contiene un path de artefacto inseguro.")
    return value


def _manifest_artifacts(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise DraftPromotionError("El manifiesto no declara artefactos.")
    result: list[dict[str, Any]] = []
    paths: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise DraftPromotionError("El manifiesto contiene un artefacto inválido.")
        path = _safe_artifact_path(artifact.get("path"))
        digest = artifact.get("sha256")
        size = artifact.get("size")
        if (
            not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or not isinstance(size, int)
            or size < 0
            or path in paths
        ):
            raise DraftPromotionError("El manifiesto contiene integridad de artefacto inválida.")
        paths.add(path)
        result.append({"path": path, "sha256": digest, "size": size})
    return result


def _checksums(content: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise DraftPromotionError("SHA256SUMS no es UTF-8.") from exc
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise DraftPromotionError("SHA256SUMS contiene una línea inválida.")
        digest, path = match.groups()
        path = _safe_artifact_path(path)
        if path in result:
            raise DraftPromotionError("SHA256SUMS contiene paths duplicados.")
        result[path] = digest
    if not result:
        raise DraftPromotionError("SHA256SUMS está vacío.")
    return result


def _candidate_file(candidate: Path, relative: str) -> Path:
    return candidate.joinpath(*PurePosixPath(relative).parts)


def _validate_gate(
    gate: dict[str, Any], gate_bytes: bytes, manifest: dict[str, Any], *, source_commit: str
) -> str:
    version = manifest.get("plugin_version")
    source = gate.get("source")
    gate_status = gate.get("gate")
    quality = manifest.get("quality")
    if (
        not isinstance(version, str)
        or not isinstance(source, dict)
        or source.get("commit") != source_commit
        or source.get("tree_state") != "clean"
        or gate.get("plugin_version") != version
        or gate.get("channel") != "stable"
        or gate_status != {"status": "passed", "blockers": []}
        or not isinstance(quality, dict)
        or quality.get("gate") != "passed"
        or quality.get("channel") != "stable"
        or quality.get("report_sha256") != _sha256(gate_bytes)
    ):
        raise DraftPromotionError(
            "El gate de release no acredita una release stable para el SHA y manifiesto."
        )
    return version


def _validate_release_notes(
    manifest: dict[str, Any], version: str, changelog: bytes
) -> tuple[str, bytes]:
    relative = "CHANGELOG.md"
    source_files = manifest.get("source_files")
    if not isinstance(source_files, list):
        raise DraftPromotionError("El manifiesto no declara los ficheros fuente.")
    matches = [
        item
        for item in source_files
        if isinstance(item, dict) and item.get("path") == relative
    ]
    if len(matches) != 1:
        raise DraftPromotionError("El manifiesto no acredita CHANGELOG.md.")
    source = matches[0]
    if (
        source.get("sha256") != _sha256(changelog)
        or source.get("size") != len(changelog)
    ):
        raise DraftPromotionError(
            "CHANGELOG.md no coincide con los bytes acreditados por el manifiesto."
        )
    try:
        return relative, release_notes.extract(changelog, version)
    except release_notes.ReleaseNotesError as exc:
        raise DraftPromotionError(str(exc)) from exc


def build_plan(
    evidence: Path,
    tag: str,
    source_commit: str,
    changelog: Path,
) -> dict[str, Any]:
    """Validate exact tag evidence and return the immutable draft asset plan."""

    if not COMMIT_RE.fullmatch(source_commit):
        raise DraftPromotionError("El commit de origen debe ser un SHA válido.")
    gate, gate_bytes = _read_json(evidence / "release-gate.json", "release-gate.json")
    candidate = evidence / "candidate"
    manifest, manifest_bytes = _read_json(
        candidate / "release-manifest.json", "release-manifest.json"
    )
    if manifest.get("source_commit") != source_commit:
        raise DraftPromotionError("El manifiesto no está vinculado al SHA de la etiqueta.")
    version = _validate_gate(gate, gate_bytes, manifest, source_commit=source_commit)
    if tag != f"v{version}":
        raise DraftPromotionError("La etiqueta no coincide con la versión acreditada.")

    artifacts = _manifest_artifacts(manifest)
    expected_checksums = {
        **{artifact["path"]: artifact["sha256"] for artifact in artifacts},
        "release-manifest.json": _sha256(manifest_bytes),
    }
    checksums_bytes = _read_bytes(candidate / "SHA256SUMS", "SHA256SUMS")
    actual_checksums = _checksums(checksums_bytes)
    if actual_checksums != expected_checksums:
        raise DraftPromotionError("SHA256SUMS no coincide exactamente con el manifiesto.")

    for artifact in artifacts:
        content = _read_bytes(
            _candidate_file(candidate, artifact["path"]), artifact["path"]
        )
        if len(content) != artifact["size"] or _sha256(content) != artifact["sha256"]:
            raise DraftPromotionError(
                f"El artefacto {artifact['path']} no coincide con su manifiesto."
            )

    quality_report = _read_bytes(candidate / "quality-report.json", "quality-report.json")
    if quality_report != gate_bytes:
        raise DraftPromotionError(
            "quality-report.json no coincide con el gate de la ejecución de etiqueta."
        )
    copilot_name = f"lks-sdd-copilot-plugin-v{version}.zip"
    copilot = next((item for item in artifacts if item["path"] == copilot_name), None)
    if copilot is None:
        raise DraftPromotionError("El manifiesto no contiene el ZIP Copilot acreditado.")
    try:
        validate_copilot_package.validate(
            _candidate_file(candidate, copilot_name).read_bytes()
        )
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
        raise DraftPromotionError(f"El ZIP Copilot acreditado es inválido: {exc}") from exc

    release_note_path, release_note = _validate_release_notes(
        manifest, version, _read_bytes(changelog, "CHANGELOG.md")
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "tag": tag,
        "plugin_version": version,
        "source_commit": source_commit,
        "title": f"LKS-SDD {version}",
        "release_notes": {
            "source_path": release_note_path,
            "sha256": _sha256(release_note),
            "size": len(release_note),
        },
        "assets": artifacts
        + [
            {
                "path": "release-manifest.json",
                "sha256": _sha256(manifest_bytes),
                "size": len(manifest_bytes),
            },
            {
                "path": "SHA256SUMS",
                "sha256": _sha256(checksums_bytes),
                "size": len(checksums_bytes),
            },
        ],
    }


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    output = path.expanduser().resolve()
    try:
        output.relative_to(PLUGIN_ROOT)
    except ValueError:
        pass
    else:
        raise DraftPromotionError(
            "--output debe estar fuera del repositorio para preservar la verificación de solo lectura."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_release_notes(path: Path, changelog: Path, version: str) -> None:
    output = path.expanduser().resolve()
    try:
        output.relative_to(PLUGIN_ROOT)
    except ValueError:
        pass
    else:
        raise DraftPromotionError(
            "--release-notes-output debe estar fuera del repositorio para preservar la verificación de solo lectura."
        )
    notes = release_notes.extract(
        _read_bytes(changelog, "CHANGELOG.md"),
        version,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(notes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--changelog", type=Path, required=True)
    parser.add_argument("--release-notes-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = build_plan(
            args.evidence.expanduser().resolve(),
            args.tag,
            args.source_commit.lower(),
            args.changelog.expanduser().resolve(),
        )
        _write_plan(args.output, plan)
        _write_release_notes(
            args.release_notes_output,
            args.changelog.expanduser().resolve(),
            plan["plugin_version"],
        )
    except DraftPromotionError as exc:
        print(
            json.dumps(
                {
                    "schema_version": REPORT_SCHEMA_VERSION,
                    "status": "blocked",
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
