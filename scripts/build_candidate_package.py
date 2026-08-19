#!/usr/bin/env python3
"""Build deterministic LKS-SDD plugin and development-marketplace candidate bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.5.0"
MARKETPLACE_TEMPLATE = PLUGIN_ROOT / "distribution" / "marketplace.template.json"
EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules",
    "dist",
    "pilot-data",
}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
)


class PackageError(Exception):
    """Expected, actionable packaging failure."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageError(f"JSON ilegible {path}: {exc}") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_output(path: Path) -> Path:
    output = path.expanduser().resolve()
    try:
        output.relative_to(PLUGIN_ROOT)
    except ValueError:
        pass
    else:
        raise PackageError("El paquete debe generarse fuera del repositorio fuente.")
    if output.exists():
        raise PackageError(f"La salida ya existe y no se sobrescribirá: {output}")
    current = output.parent
    while current.parent != current:
        if current.is_symlink() or (
            hasattr(current, "is_junction") and current.is_junction()
        ):
            raise PackageError("La salida no puede atravesar symlinks o junctions.")
        current = current.parent
    return output


def validate_marketplace(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"name", "interface", "plugins"}:
        raise PackageError("La plantilla de marketplace no respeta el contrato raíz.")
    if value.get("name") != "lks-sdd-development":
        raise PackageError("El marketplace de desarrollo debe llamarse lks-sdd-development.")
    interface = value.get("interface")
    if not isinstance(interface, dict) or interface.get("displayName") != "LKS-SDD Development":
        raise PackageError("Falta el displayName del marketplace.")
    plugins = value.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise PackageError("El marketplace debe contener exactamente LKS-SDD.")
    plugin = plugins[0]
    expected = {
        "name": "lks-sdd",
        "source": {"source": "local", "path": "./plugins/lks-sdd"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    if plugin != expected:
        raise PackageError("La entrada del marketplace no coincide con el contrato de Codex.")
    return value


def collect_source_files(root: Path = PLUGIN_ROOT) -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for current, directory_names, file_names in os.walk(root, topdown=True):
        current_path = Path(current)
        retained_directories = []
        for name in sorted(directory_names):
            path = current_path / name
            relative = path.relative_to(root)
            excluded = EXCLUDED_PARTS.intersection(relative.parts) or relative.parts[:2] in {
                ("tests", "reports"),
                ("pilot", "runs"),
            }
            if excluded:
                continue
            if path.is_symlink() or (
                hasattr(path, "is_junction") and path.is_junction()
            ):
                raise PackageError(f"No se empaquetan enlaces: {relative}")
            retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in sorted(file_names):
            path = current_path / name
            relative = path.relative_to(root)
            if EXCLUDED_PARTS.intersection(relative.parts) or relative.parts[:2] in {
                ("tests", "reports"),
                ("pilot", "runs"),
            }:
                continue
            if path.is_symlink() or (
                hasattr(path, "is_junction") and path.is_junction()
            ):
                raise PackageError(f"No se empaquetan enlaces: {relative}")
            if path.suffix in {".pyc", ".pyo"}:
                continue
            content = path.read_bytes()
            for pattern in SECRET_PATTERNS:
                if pattern.search(content):
                    raise PackageError(
                        f"Posible secreto o clave privada en {relative.as_posix()}; paquete bloqueado."
                    )
            files.append((relative.as_posix(), content))
    files.sort(key=lambda item: item[0])
    required = {
        ".codex-plugin/plugin.json",
        "README.md",
        "SECURITY.md",
        "SUPPORT.md",
        "distribution/marketplace.template.json",
    }
    present = {relative for relative, _ in files}
    missing = sorted(required - present)
    if missing:
        raise PackageError(f"Faltan archivos obligatorios del paquete: {missing}")
    return files


def _zip_bytes(
    entries: list[tuple[str, bytes]], timestamp: tuple[int, int, int, int, int, int]
) -> bytes:
    handle, temporary_name = tempfile.mkstemp(prefix="lks-sdd-package-", suffix=".zip")
    os.close(handle)
    try:
        with zipfile.ZipFile(
            temporary_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for name, content in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=timestamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        return Path(temporary_name).read_bytes()
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def build(output: Path, build_date: str, source_commit: str) -> dict[str, Any]:
    try:
        parsed_date = date.fromisoformat(build_date)
    except ValueError as exc:
        raise PackageError("--date debe usar YYYY-MM-DD.") from exc
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
        raise PackageError("--source-commit debe ser un commit Git completo de 40 caracteres.")
    manifest = _load_json(PLUGIN_ROOT / ".codex-plugin" / "plugin.json")
    if not isinstance(manifest, dict) or manifest.get("version") != EXPECTED_VERSION:
        raise PackageError(f"El manifest debe declarar {EXPECTED_VERSION} antes de empaquetar.")
    marketplace = validate_marketplace(_load_json(MARKETPLACE_TEMPLATE))
    files = collect_source_files()
    output = _safe_output(output)
    timestamp = (parsed_date.year, parsed_date.month, parsed_date.day, 0, 0, 0)
    plugin_entries = [(f"lks-sdd/{relative}", content) for relative, content in files]
    marketplace_bytes = (
        json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    marketplace_entries = [
        (".agents/plugins/marketplace.json", marketplace_bytes),
        *[(f"plugins/lks-sdd/{relative}", content) for relative, content in files],
    ]
    plugin_zip = _zip_bytes(plugin_entries, timestamp)
    marketplace_zip = _zip_bytes(marketplace_entries, timestamp)
    plugin_name = f"lks-sdd-plugin-v{EXPECTED_VERSION}.zip"
    marketplace_name = f"lks-sdd-marketplace-v{EXPECTED_VERSION}.zip"
    release_manifest = {
        "schema_version": "1.0",
        "plugin_version": EXPECTED_VERSION,
        "source_commit": source_commit,
        "built_on": build_date,
        "source_file_count": len(files),
        "source_files": [
            {"path": relative, "sha256": _sha256(content), "size": len(content)}
            for relative, content in files
        ],
        "artifacts": [
            {"path": plugin_name, "sha256": _sha256(plugin_zip), "size": len(plugin_zip)},
            {
                "path": marketplace_name,
                "sha256": _sha256(marketplace_zip),
                "size": len(marketplace_zip),
            },
        ],
        "marketplace": marketplace,
    }
    output.mkdir(parents=True)
    (output / plugin_name).write_bytes(plugin_zip)
    (output / marketplace_name).write_bytes(marketplace_zip)
    manifest_bytes = (
        json.dumps(release_manifest, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    (output / "release-manifest.json").write_bytes(manifest_bytes)
    checksums = "\n".join(
        f"{artifact['sha256']}  {artifact['path']}"
        for artifact in release_manifest["artifacts"]
    ) + "\n"
    (output / "SHA256SUMS").write_text(checksums, encoding="utf-8", newline="\n")
    return {
        "status": "built",
        "plugin_version": EXPECTED_VERSION,
        "output": str(output),
        "source_file_count": len(files),
        "artifacts": release_manifest["artifacts"],
        "manifest_sha256": _sha256(manifest_bytes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date", default=date.today().isoformat(), dest="build_date")
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    try:
        result = build(args.output, args.build_date, args.source_commit)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (PackageError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
