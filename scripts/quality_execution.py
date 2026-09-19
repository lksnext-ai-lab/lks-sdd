#!/usr/bin/env python3
"""Shared deterministic test selection and managed subprocess execution."""

from __future__ import annotations

import fnmatch
import json
import os
import platform
import re
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SUITE_REGISTRY_PATH = PLUGIN_ROOT / "quality" / "test-suites.json"
IMPACT_MAP_PATH = PLUGIN_ROOT / "quality" / "test-impact-map.json"
PERFORMANCE_POLICY_PATH = PLUGIN_ROOT / "quality" / "performance-policy.json"
RELEASE_CORE_SELECTION_PATH = PLUGIN_ROOT / "quality" / "release-core-tests.json"


class QualityExecutionError(Exception):
    """Expected configuration or execution failure."""


@dataclass(frozen=True)
class ManagedCommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    termination: str
    process_cleanup: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QualityExecutionError(f"No se puede leer {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualityExecutionError(f"{path} debe contener un objeto JSON.")
    return value


def runner_fingerprint() -> dict[str, str]:
    """Return a non-personal comparison key for performance evidence."""

    return {
        "os": platform.system().lower(),
        "architecture": platform.machine().lower(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "implementation": platform.python_implementation().lower(),
        "runner_class": os.environ.get("LKS_SDD_RUNNER_CLASS", "local"),
    }


def discovered_test_modules(tests_root: Path | None = None) -> list[str]:
    root = tests_root or (PLUGIN_ROOT / "tests")
    return sorted(path.stem for path in root.glob("test_*.py") if path.is_file())


def load_suite_registry(
    path: Path = SUITE_REGISTRY_PATH,
    *,
    tests_root: Path | None = None,
) -> dict[str, Any]:
    registry = _load_object(path)
    if registry.get("schema_version") != "1.0":
        raise QualityExecutionError("El registro de suites debe usar schema_version 1.0.")
    tiers = registry.get("tiers")
    required_tiers = {"fast", "integration", "package", "profile"}
    if not isinstance(tiers, dict) or set(tiers) != required_tiers:
        raise QualityExecutionError(
            "El registro debe declarar fast, integration, package y profile."
        )
    release_only = registry.get("release_only_modules", {})
    if not isinstance(release_only, dict) or not all(
        isinstance(module, str)
        and module.startswith("test_")
        and isinstance(timeout, int)
        and timeout >= 1
        for module, timeout in release_only.items()
    ):
        raise QualityExecutionError(
            "release_only_modules debe declarar módulos y timeouts válidos."
        )
    assigned: dict[str, str] = {}
    for tier, config in tiers.items():
        if not isinstance(config, dict):
            raise QualityExecutionError(f"La suite {tier} debe ser un objeto.")
        timeout = config.get("module_timeout_seconds")
        max_workers = config.get("max_workers")
        modules = config.get("modules")
        if not isinstance(timeout, int) or timeout < 1:
            raise QualityExecutionError(f"La suite {tier} no declara un timeout válido.")
        if not isinstance(max_workers, int) or not 1 <= max_workers <= 8:
            raise QualityExecutionError(
                f"La suite {tier} no declara una concurrencia válida."
            )
        if not isinstance(modules, list) or not all(
            isinstance(module, str) and module.startswith("test_") for module in modules
        ):
            raise QualityExecutionError(f"La suite {tier} no declara módulos válidos.")
        if len(modules) != len(set(modules)):
            raise QualityExecutionError(f"La suite {tier} contiene módulos duplicados.")
        for module in modules:
            previous = assigned.setdefault(module, tier)
            if previous != tier:
                raise QualityExecutionError(
                    f"{module} está asignado a {previous} y {tier}."
                )
    discovered = set(discovered_test_modules(tests_root))
    configured = set(assigned)
    if discovered != configured:
        raise QualityExecutionError(
            "El registro de suites no cubre exactamente los tests: "
            f"missing={sorted(discovered - configured)}; "
            f"unknown={sorted(configured - discovered)}"
        )
    unknown_release_only = sorted(set(release_only) - configured)
    if unknown_release_only:
        raise QualityExecutionError(
            "release_only_modules contiene módulos no asignados: "
            f"{unknown_release_only}"
        )
    return registry


def load_release_core_selection(
    path: Path = RELEASE_CORE_SELECTION_PATH,
) -> dict[str, Any]:
    """Load the bounded stable-release test selection."""

    selection = _load_object(path)
    expected_keys = {
        "schema_version",
        "name",
        "max_tests",
        "selection_basis",
        "tests",
        "excluded_noncritical_cases",
    }
    if set(selection) != expected_keys or selection.get("schema_version") != "1.0":
        raise QualityExecutionError(
            "La selección release-core debe usar el contrato 1.0 completo."
        )
    if selection.get("name") != "release-core":
        raise QualityExecutionError("La selección debe llamarse release-core.")
    max_tests = selection.get("max_tests")
    if not isinstance(max_tests, int) or not 1 <= max_tests <= 50:
        raise QualityExecutionError(
            "release-core debe declarar un máximo entre 1 y 50 pruebas."
        )
    if not isinstance(selection.get("selection_basis"), str) or not selection[
        "selection_basis"
    ].strip():
        raise QualityExecutionError("release-core debe explicar su criterio de selección.")
    tests = selection.get("tests")
    if not isinstance(tests, list) or not tests or len(tests) > max_tests:
        raise QualityExecutionError(
            "release-core debe declarar entre una y max_tests pruebas."
        )
    case_ids: set[str] = set()
    selectors: set[str] = set()
    selector_pattern = re.compile(
        r"test_[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.test_[A-Za-z0-9_]+"
    )
    for entry in tests:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"case_id", "selector"}
            or not isinstance(entry.get("case_id"), str)
            or not re.fullmatch(r"FX-[0-9]{2}", entry["case_id"])
            or not isinstance(entry.get("selector"), str)
            or not selector_pattern.fullmatch(entry["selector"])
        ):
            raise QualityExecutionError(
                "Cada prueba release-core debe declarar case_id y selector válidos."
            )
        if entry["case_id"] in case_ids or entry["selector"] in selectors:
            raise QualityExecutionError(
                "release-core no puede repetir casos ni selectores."
            )
        case_ids.add(entry["case_id"])
        selectors.add(entry["selector"])
    excluded = selection.get("excluded_noncritical_cases")
    if not isinstance(excluded, list):
        raise QualityExecutionError(
            "release-core debe declarar los casos no críticos excluidos."
        )
    excluded_ids: set[str] = set()
    for entry in excluded:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"case_id", "selector", "rationale"}
            or not isinstance(entry.get("case_id"), str)
            or not re.fullmatch(r"FX-[0-9]{2}", entry["case_id"])
            or not isinstance(entry.get("selector"), str)
            or not selector_pattern.fullmatch(entry["selector"])
            or not isinstance(entry.get("rationale"), str)
            or not entry["rationale"].strip()
        ):
            raise QualityExecutionError(
                "Cada exclusión release-core debe declarar caso, selector y motivo."
            )
        if entry["case_id"] in case_ids or entry["case_id"] in excluded_ids:
            raise QualityExecutionError(
                "release-core no puede solapar pruebas y exclusiones."
            )
        excluded_ids.add(entry["case_id"])
    return selection


def modules_for_suite(
    suite: str,
    registry: dict[str, Any],
    *,
    include_release_only: bool = False,
) -> list[tuple[str, str, int]]:
    tiers = registry["tiers"]
    release_only = registry.get("release_only_modules", {})
    selected = (
        [suite]
        if suite != "all"
        else ["fast", "integration", "package", "profile"]
    )
    if any(tier not in tiers for tier in selected):
        raise QualityExecutionError(f"Suite no soportada: {suite}")
    return [
        (
            module,
            tier,
            int(release_only.get(module, tiers[tier]["module_timeout_seconds"])),
        )
        for tier in selected
        for module in tiers[tier]["modules"]
        if include_release_only or module not in release_only
    ]


def load_impact_map(path: Path = IMPACT_MAP_PATH) -> dict[str, Any]:
    value = _load_object(path)
    if value.get("schema_version") != "1.0":
        raise QualityExecutionError("El mapa de impacto debe usar schema_version 1.0.")
    if value.get("fallback_suite") != "integration":
        raise QualityExecutionError("El fallback del mapa de impacto debe ser integration.")
    rules = value.get("rules")
    if not isinstance(rules, list):
        raise QualityExecutionError("El mapa de impacto debe declarar rules.")
    known_modules = set(discovered_test_modules())
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"paths", "modules"}:
            raise QualityExecutionError("Cada regla de impacto debe declarar paths y modules.")
        paths = rule["paths"]
        modules = rule["modules"]
        if not isinstance(paths, list) or not paths or not all(
            isinstance(pattern, str) and pattern for pattern in paths
        ):
            raise QualityExecutionError("Una regla de impacto contiene paths inválidos.")
        if not isinstance(modules, list) or not modules or not set(modules) <= known_modules:
            raise QualityExecutionError("Una regla de impacto contiene módulos desconocidos.")
    return value


def impacted_modules(paths: list[str], impact_map: dict[str, Any]) -> dict[str, Any]:
    normalized = sorted({path.replace("\\", "/").lstrip("./") for path in paths if path})
    selected: set[str] = set()
    unmatched: list[str] = []
    for path in normalized:
        matches = [
            rule
            for rule in impact_map["rules"]
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule["paths"])
        ]
        if not matches:
            unmatched.append(path)
            continue
        for rule in matches:
            selected.update(rule["modules"])
    if unmatched:
        registry = load_suite_registry()
        selected.update(registry["tiers"][impact_map["fallback_suite"]]["modules"])
    return {
        "paths": normalized,
        "modules": sorted(selected),
        "fallback_applied": bool(unmatched),
        "unmatched_paths": unmatched,
    }


def load_performance_policy(path: Path = PERFORMANCE_POLICY_PATH) -> dict[str, Any]:
    value = _load_object(path)
    if value.get("schema_version") != "1.0":
        raise QualityExecutionError("La política de rendimiento debe usar schema_version 1.0.")
    budgets = value.get("budgets_seconds")
    required = {
        "fast",
        "integration",
        "package",
        "profile",
        "release-core",
        "candidate",
        "profile_execute",
    }
    if not isinstance(budgets, dict) or set(budgets) != required or not all(
        isinstance(budgets[name], int) and budgets[name] > 0 for name in required
    ):
        raise QualityExecutionError("La política no declara todos los presupuestos válidos.")
    baseline = value.get("baseline")
    if not isinstance(baseline, dict):
        raise QualityExecutionError("La política no declara una baseline.")
    return value


def performance_assessment(
    actual: dict[str, float],
    policy: dict[str, Any],
    fingerprint: dict[str, str],
) -> dict[str, Any]:
    budgets = policy["budgets_seconds"]
    baseline = policy["baseline"]
    comparable = fingerprint == baseline.get("runner_fingerprint")
    regressions: list[str] = []
    comparisons: list[dict[str, Any]] = []
    for tier in sorted(actual):
        duration = round(float(actual[tier]), 3)
        budget = budgets.get(tier)
        if isinstance(budget, (int, float)) and duration > budget:
            regressions.append(f"{tier}: {duration}s supera el límite absoluto de {budget}s")
        baseline_duration = baseline.get("durations_seconds", {}).get(tier)
        allowed = None
        regressed = False
        if comparable and isinstance(baseline_duration, (int, float)):
            allowed = round(
                baseline_duration
                + max(
                    baseline_duration * float(policy["relative_regression_limit"]),
                    float(policy["minimum_regression_seconds"]),
                ),
                3,
            )
            regressed = duration > allowed
            if regressed:
                regressions.append(
                    f"{tier}: {duration}s supera la baseline comparable permitida de {allowed}s"
                )
        comparisons.append(
            {
                "suite": tier,
                "actual_seconds": duration,
                "budget_seconds": budget,
                "baseline_seconds": baseline_duration if comparable else None,
                "allowed_seconds": allowed,
                "regressed": regressed,
            }
        )
    return {
        "status": "failed" if regressions else "passed",
        "baseline_version": baseline.get("version"),
        "baseline_comparable": comparable,
        "comparison_reason": "runner-fingerprint-match" if comparable else "runner-fingerprint-mismatch",
        "comparisons": comparisons,
        "regressions": regressions,
    }


def _terminate_process_tree(process: subprocess.Popen[str], grace_seconds: float) -> tuple[str, str]:
    if process.poll() is not None:
        return "already-exited", "confirmed"
    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=max(5.0, grace_seconds),
        )
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=grace_seconds)
        cleanup = "confirmed" if process.poll() is not None else "unconfirmed"
        return f"taskkill-exit-{completed.returncode}", cleanup
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=grace_seconds)
        return "process-group-terminated", "confirmed"
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=grace_seconds)
        return "process-group-killed", "confirmed"


def run_managed_command(
    command: list[str],
    *,
    cwd: Path = PLUGIN_ROOT,
    timeout: float,
    label: str,
    heartbeat_seconds: float = 30.0,
    grace_seconds: float = 5.0,
    progress_stream: TextIO | None = None,
    stream_stderr: bool = False,
) -> ManagedCommandResult:
    """Run one command with heartbeats and whole-process-tree timeout cleanup."""

    stream = progress_stream or sys.stderr
    started = time.monotonic()
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=None if stream_stderr else subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
        start_new_session=os.name != "nt",
    )
    print(f"START {label} pid={process.pid}", file=stream, flush=True)
    deadline = started + timeout
    timed_out = False
    termination = "normal"
    cleanup = "not-required"
    stdout = ""
    stderr = ""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            termination, cleanup = _terminate_process_tree(process, grace_seconds)
            stdout, stderr = process.communicate()
            stderr = stderr or ""
            break
        try:
            stdout, stderr = process.communicate(
                timeout=min(heartbeat_seconds, remaining)
            )
            stderr = stderr or ""
            break
        except subprocess.TimeoutExpired:
            elapsed = round(time.monotonic() - started, 1)
            print(f"HEARTBEAT {label} elapsed={elapsed}s", file=stream, flush=True)
    duration = round(time.monotonic() - started, 3)
    print(
        f"END {label} status={'timeout' if timed_out else process.returncode} duration={duration}s",
        file=stream,
        flush=True,
    )
    return ManagedCommandResult(
        returncode=None if timed_out else process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration,
        timed_out=timed_out,
        termination=termination,
        process_cleanup=cleanup,
    )
