#!/usr/bin/env python3
"""Validate, record, aggregate, and decide the privacy-safe LKS-SDD M5 pilot."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
PREVIOUS_CANDIDATE_VERSION = "0.14.2"
CONFIG_KEYS = {
    "schema_version",
    "pilot_id",
    "status",
    "duration_weeks",
    "projects",
    "participants",
    "roles",
    "support",
    "rollback",
    "privacy",
}
PROJECT_KEYS = {
    "code",
    "route",
    "environment",
    "data_classification",
    "authorization_confirmed",
}
ROLE_KEYS = {
    "method_owner",
    "product_owner",
    "maintainer",
    "security_reviewer",
    "quality_reviewer",
    "workspace_admin",
    "support_owner",
}
METRIC_KEYS = {
    "activation_correct",
    "baseline_minutes",
    "repeated_questions",
    "open_points",
    "incidents",
    "documentation_load",
    "manual_changes",
    "defects_before_codex",
    "defects_after_codex",
    "onboarding_completed",
    "sdd_comprehension",
    "utility",
    "clarity",
    "confidence",
    "reuse_intent",
    "document_quality",
}
OUTCOME_KEYS = {
    "route_completed",
    "resume_correct",
    "edits_preserved",
    "permission_failures",
    "build_passed",
    "tests_passed",
    "traceability_complete",
    "security_incidents",
}
ROUTES = {
    "greenfield-certified-profile",
    "adopt-existing",
    "candidate-or-external-profile",
    "reinforced-risk",
}
REQUIRED_ROUTES = {
    "greenfield-certified-profile",
    "adopt-existing",
    "candidate-or-external-profile",
}


class PilotError(Exception):
    """Expected, actionable pilot workflow failure."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"JSON ilegible {path}: {exc}") from exc


def _current_plugin_version() -> str:
    manifest = _load_json(MANIFEST_PATH)
    version = manifest.get("version") if isinstance(manifest, dict) else None
    if not isinstance(version, str) or not re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?",
        version,
    ):
        raise PilotError("El manifest del plugin no declara una versión SemVer válida.")
    return version


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PilotError(f"{label} debe ser un objeto JSON.")
    return value


def _is_alias(value: Any, prefix: str, digits: int = 3) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(rf"{re.escape(prefix)}-[0-9]{{{digits}}}", value)
    )


def _is_int(value: Any, minimum: int = 0, maximum: int | None = None) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= minimum
        and (maximum is None or value <= maximum)
    )


def validate_config(value: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _object(value, "La configuración")
    errors: list[str] = []
    blockers: list[str] = []
    if set(config) != CONFIG_KEYS:
        errors.append(f"Campos de configuración inválidos: {sorted(set(config) ^ CONFIG_KEYS)}")
    if config.get("schema_version") != "1.0":
        errors.append("schema_version debe ser 1.0.")
    if not isinstance(config.get("pilot_id"), str) or not re.fullmatch(
        r"pilot-[a-z0-9]+(?:-[a-z0-9]+)*", config.get("pilot_id", "")
    ):
        errors.append("pilot_id no respeta el contrato.")
    if config.get("status") not in {"prepared", "running", "closed", "withdrawn"}:
        errors.append("Estado de piloto inválido.")
    if not _is_int(config.get("duration_weeks"), 6, 8):
        errors.append("duration_weeks debe estar entre 6 y 8.")

    projects = config.get("projects")
    project_codes: set[str] = set()
    project_routes: set[str] = set()
    if not isinstance(projects, list):
        errors.append("projects debe ser una lista.")
        projects = []
    for project in projects:
        if not isinstance(project, dict) or set(project) != PROJECT_KEYS:
            errors.append("Proyecto de piloto con campos inválidos.")
            continue
        code = project.get("code")
        if not _is_alias(code, "PRJ"):
            errors.append(f"Código de proyecto inválido: {code!r}")
        elif code in project_codes:
            errors.append(f"Código de proyecto duplicado: {code}")
        else:
            project_codes.add(code)
        route = project.get("route")
        if route not in ROUTES:
            errors.append(f"Ruta de proyecto inválida: {route!r}")
        else:
            project_routes.add(route)
        if project.get("environment") not in {
            "synthetic",
            "sanitized-copy",
            "non-production",
        }:
            errors.append(f"Entorno no permitido en {code!r}.")
        if project.get("data_classification") not in {
            "synthetic",
            "sanitized-internal",
        }:
            errors.append(f"Clasificación de datos no permitida en {code!r}.")
        if project.get("authorization_confirmed") is not True:
            blockers.append(f"{code!r}: falta autorización confirmada.")
    if not 3 <= len(projects) <= 5:
        blockers.append("La muestra debe contener entre 3 y 5 proyectos.")
    missing_routes = sorted(REQUIRED_ROUTES - project_routes)
    if missing_routes:
        blockers.append(f"Faltan rutas obligatorias: {missing_routes}")

    participants = config.get("participants")
    participant_set: set[str] = set()
    if not isinstance(participants, list):
        errors.append("participants debe ser una lista.")
        participants = []
    for participant in participants:
        if not _is_alias(participant, "USR"):
            errors.append(f"Alias de participante inválido: {participant!r}")
        elif participant in participant_set:
            errors.append(f"Alias de participante duplicado: {participant}")
        else:
            participant_set.add(participant)
    if not 5 <= len(participants) <= 8:
        blockers.append("La muestra debe contener entre 5 y 8 participantes.")

    roles = config.get("roles")
    if not isinstance(roles, dict) or set(roles) != ROLE_KEYS:
        errors.append("La matriz de roles no respeta el contrato.")
        roles = {}
    for role in sorted(ROLE_KEYS):
        assigned = roles.get(role)
        if assigned is None:
            blockers.append(f"Falta asignar el rol {role}.")
        elif not _is_alias(assigned, "USR"):
            errors.append(f"Alias inválido para {role}: {assigned!r}")
        elif assigned not in participant_set:
            blockers.append(f"{role} debe referenciar un participante del piloto.")

    support = config.get("support")
    if not isinstance(support, dict) or set(support) != {
        "non_sensitive_url",
        "security_url",
    }:
        errors.append("support no respeta el contrato.")
        support = {}
    non_sensitive = support.get("non_sensitive_url")
    security = support.get("security_url")
    if not isinstance(non_sensitive, str) or not non_sensitive.startswith("https://"):
        errors.append("Falta una URL HTTPS de soporte no sensible.")
    if security is None:
        blockers.append("Falta el canal confidencial de seguridad.")
    elif not isinstance(security, str) or not security.startswith("https://"):
        errors.append("security_url debe ser una URL HTTPS.")

    rollback = config.get("rollback")
    if not isinstance(rollback, dict) or set(rollback) != {
        "previous_version",
        "candidate_version",
        "package_sha256",
        "procedure_confirmed",
    }:
        errors.append("rollback no respeta el contrato.")
        rollback = {}
    if rollback.get("previous_version") != PREVIOUS_CANDIDATE_VERSION:
        errors.append(
            f"La versión de rollback debe ser {PREVIOUS_CANDIDATE_VERSION}."
        )
    current_version = _current_plugin_version()
    if rollback.get("candidate_version") != current_version:
        errors.append(f"La versión candidate debe ser {current_version}.")
    package_hash = rollback.get("package_sha256")
    if package_hash is None:
        blockers.append("Falta el SHA-256 del paquete candidate.")
    elif not isinstance(package_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", package_hash):
        errors.append("package_sha256 no es válido.")
    if rollback.get("procedure_confirmed") is not True:
        blockers.append("El rollback debe estar confirmado antes de iniciar.")

    privacy = config.get("privacy")
    if not isinstance(privacy, dict) or set(privacy) != {
        "allow_client_content",
        "allow_secrets",
        "allow_personal_names",
        "retention_days",
    }:
        errors.append("privacy no respeta el contrato.")
        privacy = {}
    for field in ("allow_client_content", "allow_secrets", "allow_personal_names"):
        if privacy.get(field) is not False:
            errors.append(f"{field} debe permanecer false.")
    if not _is_int(privacy.get("retention_days"), 1, 365):
        errors.append("retention_days debe estar entre 1 y 365.")

    ready = not errors and not blockers
    report = {
        "status": "ready" if ready else "invalid" if errors else "blocked",
        "ready_to_start": ready,
        "project_count": len(projects),
        "participant_count": len(participants),
        "route_coverage": sorted(project_routes),
        "errors": sorted(errors),
        "blockers": sorted(blockers),
    }
    return config, report


def validate_observation(value: Any, config: dict[str, Any]) -> dict[str, Any]:
    observation = _object(value, "La observación")
    expected_keys = {
        "schema_version",
        "observation_id",
        "pilot_id",
        "project_code",
        "participant_code",
        "week",
        "route",
        "metrics",
        "outcomes",
    }
    if set(observation) != expected_keys:
        raise PilotError(
            f"Campos de observación inválidos: {sorted(set(observation) ^ expected_keys)}"
        )
    if observation.get("schema_version") != "1.0":
        raise PilotError("La observación debe usar schema_version 1.0.")
    if not _is_alias(observation.get("observation_id"), "OBS", 4):
        raise PilotError("observation_id debe usar OBS-0000.")
    if observation.get("pilot_id") != config.get("pilot_id"):
        raise PilotError("La observación pertenece a otro piloto.")
    projects = {project["code"]: project for project in config.get("projects", [])}
    project_code = observation.get("project_code")
    if project_code not in projects:
        raise PilotError("project_code no está autorizado por la configuración.")
    if observation.get("route") != projects[project_code]["route"]:
        raise PilotError("La ruta observada no coincide con la ruta configurada.")
    if observation.get("participant_code") not in set(config.get("participants", [])):
        raise PilotError("participant_code no está autorizado por la configuración.")
    if not _is_int(observation.get("week"), 0, config.get("duration_weeks", 0)):
        raise PilotError("La semana observada queda fuera del piloto.")
    metrics = observation.get("metrics")
    outcomes = observation.get("outcomes")
    if not isinstance(metrics, dict) or set(metrics) != METRIC_KEYS:
        raise PilotError("metrics no respeta el contrato cerrado.")
    if not isinstance(outcomes, dict) or set(outcomes) != OUTCOME_KEYS:
        raise PilotError("outcomes no respeta el contrato cerrado.")
    for field in ("activation_correct", "onboarding_completed", "reuse_intent"):
        if not isinstance(metrics.get(field), bool):
            raise PilotError(f"{field} debe ser booleano.")
    integer_ranges = {
        "baseline_minutes": (0, 10080),
        "repeated_questions": (0, None),
        "open_points": (0, None),
        "incidents": (0, None),
        "manual_changes": (0, None),
        "defects_before_codex": (0, None),
        "defects_after_codex": (0, None),
        "sdd_comprehension": (1, 5),
        "utility": (1, 5),
        "clarity": (1, 5),
        "confidence": (1, 5),
        "document_quality": (1, 5),
    }
    for field, (minimum, maximum) in integer_ranges.items():
        if not _is_int(metrics.get(field), minimum, maximum):
            raise PilotError(f"Métrica inválida: {field}")
    if metrics.get("documentation_load") not in {"low", "acceptable", "high"}:
        raise PilotError("documentation_load no es válido.")
    for field in ("route_completed", "resume_correct", "edits_preserved", "traceability_complete"):
        if not isinstance(outcomes.get(field), bool):
            raise PilotError(f"{field} debe ser booleano.")
    for field in ("permission_failures", "security_incidents"):
        if not _is_int(outcomes.get(field), 0):
            raise PilotError(f"{field} debe ser un entero no negativo.")
    for field in ("build_passed", "tests_passed"):
        if outcomes.get(field) is not None and not isinstance(outcomes.get(field), bool):
            raise PilotError(f"{field} debe ser booleano o null.")
    return observation


def _safe_external_directory(path: Path) -> Path:
    directory = path.expanduser().resolve()
    try:
        directory.relative_to(PLUGIN_ROOT)
    except ValueError:
        pass
    else:
        raise PilotError("Los datos del piloto deben almacenarse fuera del repositorio del plugin.")
    if not directory.is_dir():
        raise PilotError(f"El almacén externo no existe o no es carpeta: {directory}")
    current = directory
    while current.parent != current:
        if current.is_symlink() or (
            hasattr(current, "is_junction") and current.is_junction()
        ):
            raise PilotError("El almacén externo no puede usar symlinks o junctions.")
        current = current.parent
    return directory


def _atomic_write(path: Path, value: dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise PilotError(f"La salida ya existe: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _safe_external_output(path: Path) -> Path:
    destination = path.expanduser().resolve()
    _safe_external_directory(destination.parent)
    return destination


def record_observation(
    config: dict[str, Any], observation: dict[str, Any], store: Path
) -> dict[str, Any]:
    _, config_report = validate_config(config)
    if config.get("status") != "running" or not config_report["ready_to_start"]:
        raise PilotError("El piloto debe estar running y superar su puerta de inicio.")
    validated = validate_observation(observation, config)
    directory = _safe_external_directory(store)
    destination = directory / f"{validated['observation_id']}.json"
    encoded = json.dumps(validated, indent=2, ensure_ascii=False) + "\n"
    if destination.exists():
        if destination.read_text(encoding="utf-8") == encoded:
            return {
                "status": "unchanged",
                "changed": False,
                "observation_id": validated["observation_id"],
            }
        raise PilotError("El observation_id ya existe con contenido diferente.")
    _atomic_write(destination, validated)
    return {
        "status": "recorded",
        "changed": True,
        "observation_id": validated["observation_id"],
    }


def _rate(values: list[bool]) -> float | None:
    return round(sum(1 for value in values if value) / len(values), 6) if values else None


def _average(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


def summarize(config: dict[str, Any], store: Path) -> dict[str, Any]:
    _, config_report = validate_config(config)
    if config_report["errors"]:
        raise PilotError("La configuración es inválida y no puede resumirse.")
    if config.get("status") not in {"running", "closed", "withdrawn"}:
        raise PilotError("El piloto debe estar running, closed o withdrawn para resumirse.")
    directory = _safe_external_directory(store)
    observations = []
    for path in sorted(directory.glob("*.json")):
        if not re.fullmatch(r"OBS-[0-9]{4}\.json", path.name):
            raise PilotError(f"Archivo no permitido en el almacén de observaciones: {path.name}")
        observations.append(validate_observation(_load_json(path), config))
    projects = {item["project_code"] for item in observations}
    participants = {item["participant_code"] for item in observations}
    routes = {item["route"] for item in observations}
    completed_routes = {
        item["route"] for item in observations if item["outcomes"]["route_completed"]
    }
    build_values = [
        item["outcomes"]["build_passed"]
        for item in observations
        if item["outcomes"]["build_passed"] is not None
    ]
    test_values = [
        item["outcomes"]["tests_passed"]
        for item in observations
        if item["outcomes"]["tests_passed"] is not None
    ]
    metrics = {
        "activation_accuracy": _rate([item["metrics"]["activation_correct"] for item in observations]),
        "baseline_minutes_average": _average([item["metrics"]["baseline_minutes"] for item in observations]),
        "documentation_load_acceptable_rate": _rate([item["metrics"]["documentation_load"] in {"low", "acceptable"} for item in observations]),
        "document_quality_average": _average([item["metrics"]["document_quality"] for item in observations]),
        "onboarding_completion_rate": _rate([item["metrics"]["onboarding_completed"] for item in observations]),
        "sdd_comprehension_average": _average([item["metrics"]["sdd_comprehension"] for item in observations]),
        "utility_average": _average([item["metrics"]["utility"] for item in observations]),
        "clarity_average": _average([item["metrics"]["clarity"] for item in observations]),
        "confidence_average": _average([item["metrics"]["confidence"] for item in observations]),
        "reuse_intent_rate": _rate([item["metrics"]["reuse_intent"] for item in observations]),
        "resume_correct_rate": _rate([item["outcomes"]["resume_correct"] for item in observations]),
        "edits_preserved_rate": _rate([item["outcomes"]["edits_preserved"] for item in observations]),
        "traceability_complete_rate": _rate([item["outcomes"]["traceability_complete"] for item in observations]),
        "build_pass_rate": _rate(build_values),
        "tests_pass_rate": _rate(test_values),
        "permission_failures": sum(item["outcomes"]["permission_failures"] for item in observations),
        "security_incidents": sum(item["outcomes"]["security_incidents"] for item in observations),
        "defects_before_codex": sum(item["metrics"]["defects_before_codex"] for item in observations),
        "defects_after_codex": sum(item["metrics"]["defects_after_codex"] for item in observations),
    }
    sufficient = (
        len(projects) >= 3
        and len(participants) >= 5
        and REQUIRED_ROUTES.issubset(routes)
        and bool(observations)
    )
    return {
        "schema_version": "1.0",
        "pilot_id": config["pilot_id"],
        "observation_count": len(observations),
        "project_count": len(projects),
        "participant_count": len(participants),
        "route_coverage": sorted(routes),
        "completed_route_coverage": sorted(completed_routes),
        "sample_sufficient": sufficient,
        "metrics": metrics,
        "decision": {"status": "not-evaluated", "blockers": [], "conditions": []},
    }


def decide(
    config: dict[str, Any], summary: dict[str, Any], quality_report: dict[str, Any]
) -> dict[str, Any]:
    _, config_report = validate_config(config)
    if config_report["errors"]:
        raise PilotError("La configuración es inválida.")
    if summary.get("pilot_id") != config.get("pilot_id"):
        raise PilotError("El resumen pertenece a otro piloto.")
    if config.get("status") == "withdrawn":
        decision = {
            "status": "withdrawal",
            "blockers": ["El piloto está marcado como withdrawn."],
            "conditions": [],
        }
        return {**summary, "decision": decision}
    metrics = summary.get("metrics")
    if not isinstance(metrics, dict):
        raise PilotError("El resumen no contiene métricas agregadas.")
    quality_metrics = quality_report.get("metrics")
    quality_channels = quality_report.get("channels")
    if not isinstance(quality_metrics, dict) or not isinstance(quality_channels, dict):
        raise PilotError("El reporte de calidad no respeta el contrato M4.")
    blockers: list[str] = []
    conditions: list[str] = []
    if not summary.get("sample_sufficient"):
        blockers.append("La muestra observada no alcanza 3 proyectos, 5 participantes y las tres rutas obligatorias.")
    completed = set(summary.get("completed_route_coverage", []))
    for route in ("greenfield-certified-profile", "adopt-existing"):
        if route not in completed:
            blockers.append(f"La ruta {route} no está completada.")
    if metrics.get("security_incidents", 0) != 0:
        blockers.append("Existen incidencias de seguridad.")
    if metrics.get("permission_failures", 0) != 0:
        blockers.append("Existen fallos de permisos.")
    if quality_metrics.get("critical_failures") != 0:
        blockers.append("El harness M4 contiene fallos críticos.")
    if quality_metrics.get("profile_complete_gate") != 1:
        blockers.append("La cobertura técnica completa de perfiles activos no está verde.")
    document_quality = metrics.get("document_quality_average")
    if document_quality is None or document_quality < 4:
        blockers.append("La calidad documental media no alcanza 4 sobre 5.")
    load_rate = metrics.get("documentation_load_acceptable_rate")
    if load_rate is None or load_rate <= 0.5:
        blockers.append("La mayoría no considera aceptable la carga documental.")
    if not config_report["ready_to_start"]:
        blockers.extend(config_report["blockers"])
    for channel in ("activation", "document-review"):
        if quality_channels.get(channel, {}).get("status") != "passed":
            conditions.append(f"El canal de calidad {channel} debe quedar passed.")
    onboarding_rate = metrics.get("onboarding_completion_rate")
    if onboarding_rate is None or onboarding_rate < 0.8:
        conditions.append("El onboarding debe alcanzar al menos un 80 % de finalización.")
    comprehension = metrics.get("sdd_comprehension_average")
    if comprehension is None or comprehension < 4:
        conditions.append("La comprensión SDD media debe alcanzar 4 sobre 5.")
    if blockers:
        status = "no-go"
    elif conditions:
        status = "go-conditioned"
    else:
        status = "go"
    return {
        **summary,
        "decision": {
            "status": status,
            "blockers": sorted(set(blockers)),
            "conditions": sorted(set(conditions)),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate-config")
    validate_parser.add_argument("config", type=Path)
    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("config", type=Path)
    record_parser.add_argument("observation", type=Path)
    record_parser.add_argument("--store", type=Path, required=True)
    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("config", type=Path)
    summarize_parser.add_argument("--store", type=Path, required=True)
    summarize_parser.add_argument("--output", type=Path)
    summarize_parser.add_argument("--force", action="store_true")
    decide_parser = subparsers.add_parser("decide")
    decide_parser.add_argument("config", type=Path)
    decide_parser.add_argument("summary", type=Path)
    decide_parser.add_argument("quality_report", type=Path)
    decide_parser.add_argument("--output", type=Path)
    decide_parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        config, config_report = validate_config(_load_json(args.config))
        if args.command == "validate-config":
            result = config_report
            code = 0 if result["ready_to_start"] else 2 if result["errors"] else 3
        elif args.command == "record":
            result = record_observation(
                config, _load_json(args.observation), args.store
            )
            code = 0
        elif args.command == "summarize":
            result = summarize(config, args.store)
            if args.output:
                _atomic_write(_safe_external_output(args.output), result, args.force)
            code = 0
        else:
            result = decide(
                config,
                _object(_load_json(args.summary), "El resumen"),
                _object(_load_json(args.quality_report), "El reporte de calidad"),
            )
            if args.output:
                _atomic_write(_safe_external_output(args.output), result, args.force)
            code = 0 if result["decision"]["status"] == "go" else 3
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return code
    except (PilotError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
