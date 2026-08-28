#!/usr/bin/env python3
"""Fast installation and compatibility diagnostics for normal project work."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from experience_engine import ExperienceError, PLUGIN_VERSION, _read_json, _safe_project_root, Metrics


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    ".codex-plugin/plugin.json",
    "scripts/lks_sdd.py",
    "scripts/project_status.py",
    "scripts/work_task.py",
    "scripts/experience_engine.py",
    "skills/lks-sdd-help/SKILL.md",
    "skills/lks-sdd-define/SKILL.md",
    "skills/lks-sdd-adopt-existing/SKILL.md",
    "skills/lks-sdd-assess-readiness/SKILL.md",
    "skills/lks-sdd-implement/SKILL.md",
    "skills/lks-sdd-verify/SKILL.md",
)
SUPPORTED_PROJECT_SCHEMA = "1.5"
SUPPORTED_METHOD_VERSION = "1.5.0"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_integrity(metrics: Metrics) -> dict[str, Any]:
    """Verify the package manifest, or the required source set in development."""

    manifest_path = PLUGIN_ROOT / "package-integrity.json"
    if not manifest_path.is_file():
        missing = [item for item in REQUIRED if not (PLUGIN_ROOT / item).is_file()]
        return {
            "status": "development-source" if not missing else "invalid",
            "manifest_present": False,
            "verified_files": len(REQUIRED) - len(missing),
            "missing": missing,
            "mismatched": [],
        }
    integrity = _read_json(manifest_path, metrics)
    files = integrity.get("files")
    if (
        integrity.get("schema_version") != "1.0"
        or integrity.get("plugin_version") != PLUGIN_VERSION
        or not isinstance(files, list)
    ):
        return {
            "status": "invalid",
            "manifest_present": True,
            "verified_files": 0,
            "missing": [],
            "mismatched": ["package-integrity.json"],
        }
    missing: list[str] = []
    mismatched: list[str] = []
    verified = 0
    for item in files:
        if not isinstance(item, dict):
            mismatched.append("package-integrity.json:entry")
            continue
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            mismatched.append("package-integrity.json:entry")
            continue
        candidate = (PLUGIN_ROOT / relative).resolve()
        try:
            candidate.relative_to(PLUGIN_ROOT)
        except ValueError:
            mismatched.append(relative)
            continue
        if not candidate.is_file():
            missing.append(relative)
        elif _sha256(candidate) != expected:
            mismatched.append(relative)
        else:
            verified += 1
    return {
        "status": "verified" if not missing and not mismatched else "invalid",
        "manifest_present": True,
        "verified_files": verified,
        "missing": missing,
        "mismatched": mismatched,
    }


def quick_doctor(project_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    metrics = Metrics()
    root = _safe_project_root(project_root)
    plugin = _read_json(PLUGIN_ROOT / ".codex-plugin/plugin.json", metrics)
    manifest = _read_json(root / ".lks-sdd/project.json", metrics)
    missing = [item for item in REQUIRED if not (PLUGIN_ROOT / item).is_file()]
    integrity = _package_integrity(metrics)
    version_ok = plugin.get("version") == PLUGIN_VERSION
    schema = str(manifest.get("schema_version", ""))
    method = str(manifest.get("method_version", ""))
    compatible = schema == SUPPORTED_PROJECT_SCHEMA and method == SUPPORTED_METHOD_VERSION
    bindings = [
        item for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict) and item.get("state") == "confirmed"
    ]
    docker_required = False
    drivers: list[str] = []
    for binding in bindings:
        driver = PLUGIN_ROOT / "profiles" / str(binding.get("profile_id")) / "profile-driver.json"
        if not driver.is_file():
            continue
        value = _read_json(driver, metrics)
        drivers.append(driver.relative_to(PLUGIN_ROOT).as_posix())
        docker_required = docker_required or any(
            isinstance(check, dict) and check.get("required") is True and check.get("requires_containers") is True
            for check in value.get("verify", {}).get("checks", [])
        )
    docker_available = shutil.which("docker") is not None if docker_required else None
    tracking = manifest.get("task_tracking") if isinstance(manifest.get("task_tracking"), dict) else {}
    jira_required = (
        tracking.get("mode") == "jira-hybrid"
        and tracking.get("coordination_gate") == "required-before-execution"
        and tracking.get("sync_status") not in {"in-sync", "not-required"}
    )
    errors = []
    if not version_ok:
        errors.append("La versión del manifiesto del plugin no coincide con el runtime.")
    if missing:
        errors.append("Faltan scripts o skills requeridos.")
    if integrity["status"] == "invalid":
        errors.append("La integridad criptográfica del paquete no es válida.")
    if not compatible:
        errors.append(
            "Contrato de proyecto no soportado: "
            f"schema {schema or 'ausente'} / método {method or 'ausente'}; "
            "v0.15 requiere schema 1.5 y método 1.5.0."
        )
    if docker_required and not docker_available:
        errors.append("Docker es requerido por el perfil aplicable y no está disponible.")
    metrics.project_parse_ms = (time.perf_counter() - started) * 1000
    return {
        "status": "operational" if not errors else "blocked",
        "plugin_version": plugin.get("version"),
        "package_integrity": integrity,
        "project_compatible": compatible,
        "schema_version": schema,
        "method_version": method,
        "materialized_with_plugin_version": manifest.get("plugin_version"),
        "runtime": {"python": sys.version.split()[0], "compatible": sys.version_info >= (3, 10)},
        "docker": {
            "required": docker_required,
            "available": docker_available,
            "summary": "disponible" if docker_required and docker_available else "no necesario" if not docker_required else "no disponible",
        },
        "jira": {
            "required_for_current_operation": jira_required,
            "summary": "necesario para la operación actual" if jira_required else "no necesario para la operación actual",
        },
        "required_files": {"count": len(REQUIRED), "missing": missing},
        "profile_drivers": drivers,
        "errors": errors,
        "instrumentation": metrics.payload(),
        "internal_plugin_suite_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--quick", action="store_true", required=True)
    parser.add_argument("--view", choices=("management", "developer", "audit"), default="management")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        result = quick_doctor(args.project_root)
        if args.as_json or args.view == "audit":
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif result["status"] == "operational":
            print(
                f"LKS-SDD {result['plugin_version']} operativo. Proyecto compatible. "
                f"Docker {result['docker']['summary']}. Jira {result['jira']['summary']}."
            )
        else:
            print("LKS-SDD bloqueado: " + " ".join(result["errors"]))
        return 0 if result["status"] == "operational" else 3
    except ExperienceError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
