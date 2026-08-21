#!/usr/bin/env python3
"""Run the declared technical gate for any LKS-SDD reference profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Any

from profile_registry import (
    PLUGIN_ROOT,
    capability_digest,
    certification_engine_sha256,
    composition_digest,
    load_catalog,
    load_profile_bundle,
    profile_source_files,
    sha256_file,
    sha256_prepare_sources,
)
from validate_reference_profile import PROFILE_ID, validate_profile


PYTHON_IMAGE = (
    "python:3.14.7-slim@sha256:"
    "ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
)
NODE_IMAGE = (
    "node:24.19.0-bookworm-slim@sha256:"
    "3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03"
)
PLAYWRIGHT_IMAGE = (
    "mcr.microsoft.com/playwright:v1.62.1-noble@sha256:"
    "dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e"
)


def _run(
    name: str,
    command: list[str],
    cwd: Path,
    results: list[dict[str, Any]],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> bool:
    started = time.monotonic()
    executable = list(command)
    if os.name == "nt" and executable:
        if executable[0] in {"npm", "npx"}:
            executable[0] += ".cmd"
    try:
        process = subprocess.run(
            executable,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        results.append(
            {
                "name": name,
                "status": "failed",
                "duration_seconds": round(time.monotonic() - started, 3),
                "error": str(exc),
                "command": command,
            }
        )
        return False
    results.append(
        {
            "name": name,
            "status": "passed" if process.returncode == 0 else "failed",
            "exit_code": process.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": command,
            "stdout_tail": process.stdout[-3000:],
            "stderr_tail": process.stderr[-3000:],
        }
    )
    return process.returncode == 0


def _materialize(profile_id: str, work: Path) -> None:
    bundle = load_profile_bundle(profile_id)
    if bundle.root is None:
        raise ValueError(f"Perfil no encontrado: {profile_id}")
    written: dict[Path, bytes] = {}
    for source in bundle.driver["prepare"]["sources"]:
        origin = (PLUGIN_ROOT / source["from"]).resolve()
        target = Path(source["to"])
        if target.is_absolute() or ".." in target.parts:
            raise ValueError(f"Destino de perfil inseguro: {source['to']}")
        destination_root = work / target
        if origin.is_file():
            entries = [(origin, Path(origin.name) if destination_root.is_dir() else Path("."))]
            if source["to"] != "." and destination_root.suffix:
                entries = [(origin, Path("."))]
        else:
            entries = [
                (path, path.relative_to(origin)) for path in profile_source_files(origin)
            ]
        for path, relative in entries:
            destination = (
                destination_root
                if relative == Path(".")
                else destination_root / relative
            )
            content = path.read_bytes()
            prior = written.get(destination)
            if prior is not None and prior != content:
                raise ValueError(
                    f"Fuentes del perfil colisionan en {destination.relative_to(work)}"
                )
            if destination.exists() and destination.read_bytes() != content:
                raise ValueError(
                    f"Fuentes del perfil divergen en {destination.relative_to(work)}"
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(content)
            written[destination] = content


def _docker_mount(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _dockerized(
    command: list[str], work: Path, cwd: Path, check_name: str
) -> list[str]:
    relative = cwd.relative_to(work).as_posix()
    shell_cwd = "/work" if relative == "." else f"/work/{relative}"
    first = command[0] if command else ""
    if first in {"npm", "npx", "npm.cmd", "npx.cmd"}:
        browser = any(
            token in check_name
            for token in ("browser", "accessibility", "hydration")
        )
        image = PLAYWRIGHT_IMAGE if browser else NODE_IMAGE
        script = f"cd {shlex.quote(shell_cwd)} && {shlex.join(command)}"
    else:
        image = PYTHON_IMAGE
        script = (
            "python -m pip install --disable-pip-version-check --quiet "
            "uv==0.12.5 && "
            f"cd {shlex.quote(shell_cwd)} && {shlex.join(command)}"
        )
    return [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{_docker_mount(work)}:/work",
        image,
        "sh",
        "-lc",
        script,
    ]


def _delivery_contract_check(work: Path) -> bool:
    candidates = [
        path
        for path in work.rglob("*")
        if path.is_file()
        and (
            "deploy" in path.parts
            or "delivery" in path.name.casefold()
            or path.name == "compose.yaml"
        )
    ]
    return bool(candidates)


def _compose_prefix(command: list[str]) -> list[str] | None:
    if len(command) < 2 or command[:2] != ["docker", "compose"]:
        return None
    prefix = ["docker", "compose"]
    if "-f" in command:
        index = command.index("-f")
        if index + 1 < len(command):
            prefix.extend(["-f", command[index + 1]])
    return prefix


def _compose_diagnostics(
    command: list[str], cwd: Path, results: list[dict[str, Any]], env: dict[str, str]
) -> None:
    prefix = _compose_prefix(command)
    if prefix is None:
        return
    _run(
        "compose-state",
        [*prefix, "ps", "--all"],
        cwd,
        results,
        env=env,
        timeout=60,
    )
    _run(
        "compose-logs",
        [*prefix, "logs", "--no-color", "--tail", "120"],
        cwd,
        results,
        env=env,
        timeout=60,
    )


def _compose_cleanup(
    work: Path,
    checks: list[dict[str, Any]],
    results: list[dict[str, Any]],
    env: dict[str, str],
) -> None:
    invocations: set[tuple[str, tuple[str, ...]]] = set()
    for check in checks:
        command = check.get("command", [])
        prefix = _compose_prefix(command)
        if prefix is None:
            continue
        invocations.add((str(check.get("cwd", ".")), tuple(prefix)))
    for declared_cwd, prefix in sorted(invocations):
        _run(
            "compose-cleanup",
            [*prefix, "down", "--volumes", "--remove-orphans"],
            work / declared_cwd,
            results,
            env=env,
            timeout=300,
        )


def _record_certification(profile_id: str, result: dict[str, Any]) -> Path:
    if not result.get("passed") or not result.get("complete_gate"):
        raise ValueError("Solo se registra una certificación completa y superada.")
    bundle = load_profile_bundle(profile_id)
    if bundle.root is None:
        raise ValueError(f"Perfil no encontrado: {profile_id}")
    catalog, errors = load_catalog()
    if errors:
        raise ValueError("; ".join(errors))
    capabilities = {
        item["id"]: item
        for item in catalog.get("capabilities", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    locked_capabilities = [
        {
            "id": capability_id,
            "version": capabilities[capability_id]["version"],
            "digest": capability_digest(capabilities[capability_id]),
        }
        for capability_id in sorted(bundle.profile["required_capabilities"])
    ]
    gate_ids = sorted(
        set(bundle.profile["gates"]["capability_gate_ids"])
        | {bundle.profile["gates"]["composition_gate_id"]}
    )
    profile_hash = sha256_file(bundle.root / "technology-profile.yaml")
    driver_hash = sha256_file(bundle.root / "profile-driver.json")
    scaffold_hash = sha256_prepare_sources(bundle.driver)
    composition_hash = composition_digest(
        profile_sha256=profile_hash,
        driver_sha256=driver_hash,
        scaffold_sha256=scaffold_hash,
        capabilities=locked_capabilities,
        gate_ids=gate_ids,
    )
    statuses = {
        item.get("gate_id"): item.get("status")
        for item in result.get("checks", [])
        if item.get("gate_id")
    }
    checks = [
        {"gate_id": gate_id, "status": str(statuses.get(gate_id, "not-run"))}
        for gate_id in gate_ids
    ]
    if any(item["status"] != "passed" for item in checks):
        raise ValueError("El resultado no contiene todos los gates required superados.")
    result_material = {
        "profile_id": profile_id,
        "profile_version": bundle.profile["version"],
        "runtime": result["runtime"],
        "containers_executed": result["containers_executed"],
        "complete_gate": result["complete_gate"],
        "passed": result["passed"],
        "checks": checks,
    }
    result_sha256 = hashlib.sha256(
        json.dumps(
            result_material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    evidence = {
        "schema_version": "1.0",
        "profile_id": profile_id,
        "profile_version": bundle.profile["version"],
        "certified_at": date.today().isoformat(),
        "runtime": "docker",
        "containers_executed": True,
        "complete_gate": True,
        "passed": True,
        "profile_sha256": profile_hash,
        "driver_sha256": driver_hash,
        "scaffold_sha256": scaffold_hash,
        "composition_digest": composition_hash,
        "certification_engine_sha256": certification_engine_sha256(),
        "checks": checks,
        "result_sha256": result_sha256,
        "command": (
            "python scripts/run_reference_profile_gate.py --profile "
            f"{profile_id} --runtime docker --containers --record-certification"
        ),
    }
    evidence_path = bundle.root / "certification-evidence.json"
    lock_path = bundle.root / "technology-profile.lock.json"
    evidence_original = evidence_path.read_bytes() if evidence_path.is_file() else None
    lock_original = lock_path.read_bytes() if lock_path.is_file() else None
    evidence_temp = evidence_path.with_name(evidence_path.name + ".tmp")
    lock_temp = lock_path.with_name(lock_path.name + ".tmp")
    try:
        evidence_temp.write_bytes(
            (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
        os.replace(evidence_temp, evidence_path)
        from update_profile_locks import build_lock

        lock = build_lock(profile_id)
        lock_temp.write_bytes(
            (json.dumps(lock, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
        os.replace(lock_temp, lock_path)
        validation_errors = validate_profile(
            profile_id,
            require_validated=bundle.profile.get("lifecycle") == "active",
        )
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
    except (OSError, ValueError):
        for path, original in (
            (evidence_path, evidence_original),
            (lock_path, lock_original),
        ):
            if original is None:
                try:
                    path.unlink()
                except OSError:
                    pass
            else:
                path.write_bytes(original)
        for temporary in (evidence_temp, lock_temp):
            try:
                temporary.unlink()
            except OSError:
                pass
        raise
    return evidence_path


def run_gate(
    profile_id: str, *, runtime: str, containers: bool
) -> tuple[int, dict[str, Any]]:
    results: list[dict[str, Any]] = []
    structural_errors = validate_profile(
        profile_id, require_validated=False
    )
    results.append(
        {
            "name": "profile-structure",
            "status": "passed" if not structural_errors else "failed",
            "errors": structural_errors,
        }
    )
    bundle = load_profile_bundle(profile_id)
    if structural_errors or bundle.root is None:
        return 2, {
            "profile_id": profile_id,
            "passed": False,
            "complete_gate": False,
            "runtime": runtime,
            "containers_executed": containers,
            "checks": results,
        }
    checks = bundle.driver["verify"]["checks"]
    required_container_checks = [
        item for item in checks if item.get("required") and item.get("requires_containers")
    ]
    skipped_required = False
    env = os.environ.copy()
    suffix = hashlib.sha256(profile_id.encode("ascii")).hexdigest()[:8]
    env["COMPOSE_PROJECT_NAME"] = f"lkssddgate{os.getpid()}{suffix}"
    with tempfile.TemporaryDirectory(
        prefix=f"lks-sdd-{profile_id.casefold()}-",
        ignore_cleanup_errors=True,
    ) as directory:
        work = Path(directory) / "reference-app"
        work.mkdir()
        try:
            _materialize(profile_id, work)
            for check in checks:
                name = str(check["name"])
                if check["kind"] == "delivery-evidence":
                    passed = _delivery_contract_check(work)
                    results.append(
                        {
                            "name": name,
                            "gate_id": check["id"],
                            "status": "passed" if passed else "failed",
                            "evidence": "packaged delivery contract",
                        }
                    )
                    if not passed and check["required"]:
                        break
                    continue
                if check["requires_containers"] and not containers:
                    results.append(
                        {
                            "name": name,
                            "gate_id": check["id"],
                            "status": "not-run",
                            "reason": "--containers was not supplied",
                        }
                    )
                    skipped_required = skipped_required or bool(check["required"])
                    continue
                declared_cwd = Path(check["cwd"])
                if declared_cwd.is_absolute() or ".." in declared_cwd.parts:
                    results.append(
                        {
                            "name": name,
                            "gate_id": check["id"],
                            "status": "failed",
                            "error": "cwd outside materialized profile",
                        }
                    )
                    break
                cwd = work / declared_cwd
                command = list(check["command"])
                if (
                    runtime == "docker"
                    and command[0] != "docker"
                    and check.get("execution_context", "runtime") != "host"
                ):
                    executable = _dockerized(command, work, cwd, name)
                    execution_cwd = work
                else:
                    executable = command
                    execution_cwd = cwd
                passed = _run(
                    name,
                    executable,
                    execution_cwd,
                    results,
                    env=env,
                    timeout=int(check["timeout_seconds"]),
                )
                results[-1]["gate_id"] = check["id"]
                results[-1]["required"] = bool(check["required"])
                if not passed:
                    _compose_diagnostics(command, cwd, results, env)
                    break
        except (OSError, ValueError) as exc:
            results.append(
                {"name": "materialization", "status": "failed", "error": str(exc)}
            )
        finally:
            if containers:
                _compose_cleanup(work, checks, results, env)

    failed = any(item["status"] == "failed" for item in results)
    passed = not failed and not skipped_required
    complete = (
        passed
        and runtime == "docker"
        and (containers or not required_container_checks)
    )
    return (0 if passed else 2), {
        "profile_id": profile_id,
        "lifecycle": bundle.profile.get("lifecycle"),
        "passed": passed,
        "complete_gate": complete,
        "runtime": runtime,
        "containers_executed": containers,
        "checks": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=PROFILE_ID)
    parser.add_argument("--runtime", choices=("local", "docker"), default="local")
    parser.add_argument("--containers", action="store_true")
    parser.add_argument("--record-certification", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    code, result = run_gate(
        args.profile, runtime=args.runtime, containers=args.containers
    )
    if args.record_certification:
        if args.runtime != "docker" or not args.containers:
            result.setdefault("errors", []).append(
                "--record-certification exige --runtime docker --containers."
            )
            code = 2
        elif code == 0:
            try:
                certification_path = _record_certification(args.profile, result)
                result["certification_recorded"] = True
                result["certification_path"] = certification_path.relative_to(
                    PLUGIN_ROOT
                ).as_posix()
            except (OSError, ValueError) as exc:
                result.setdefault("errors", []).append(str(exc))
                result["certification_recorded"] = False
                code = 2
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        print("PASSED" if result["passed"] else "FAILED")
        print(f"profile_id={result['profile_id']}")
        print(f"complete_gate={str(result['complete_gate']).lower()}")
        for check in result["checks"]:
            print(f"{check['status'].upper()}: {check['name']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
