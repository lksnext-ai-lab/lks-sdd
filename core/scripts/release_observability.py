#!/usr/bin/env python3
"""Create a deterministic timing report from completed GitHub Actions metadata."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_SCHEMA_VERSION = "release-observability-1.1"
RELEASE_JOB_NAME = "release"
MEASURED_STEPS = {
    "dependencies": ("Install locked runtime dependencies",),
    "gate": ("Compact release gate",),
    "build": ("Build and validate release package",),
    # The Actions REST API reports `uses` steps by action, not YAML display name.
    "artifact_upload": (
        "Upload release evidence",
        "Run actions/upload-artifact@v4",
    ),
}
REUSE_STEPS = {
    "preflight_resolution": ("Resolve reusable stable preflight",),
    "preflight_verification": ("Verify reusable preflight evidence",),
}


class ReleaseObservabilityError(Exception):
    """Expected error while interpreting completed workflow metadata."""


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseObservabilityError(f"No se puede leer {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseObservabilityError(f"{label} debe ser un objeto JSON.")
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ReleaseObservabilityError(f"Falta la fecha {label}.")
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError as exc:
        raise ReleaseObservabilityError(f"La fecha {label} no es ISO-8601 válida.") from exc
    if parsed.tzinfo is None:
        raise ReleaseObservabilityError(f"La fecha {label} debe incluir zona horaria.")
    return parsed.astimezone(timezone.utc)


def _duration_seconds(start: datetime, end: datetime, label: str) -> float:
    seconds = round((end - start).total_seconds(), 3)
    if seconds < 0:
        raise ReleaseObservabilityError(f"La duración {label} no puede ser negativa.")
    return seconds


def _select_release_job(payload: dict[str, Any], job_name: str) -> dict[str, Any]:
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise ReleaseObservabilityError("La respuesta de jobs no contiene una lista.")
    matches = [job for job in jobs if isinstance(job, dict) and job.get("name") == job_name]
    if len(matches) != 1:
        raise ReleaseObservabilityError(
            f"Se esperaba exactamente un job {job_name!r}; se encontraron {len(matches)}."
        )
    return matches[0]


def _select_step(job: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    steps = job.get("steps")
    if not isinstance(steps, list):
        raise ReleaseObservabilityError("El job de release no contiene pasos.")
    matches = [
        step for step in steps if isinstance(step, dict) and step.get("name") in names
    ]
    if len(matches) != 1:
        expected = " o ".join(repr(name) for name in names)
        raise ReleaseObservabilityError(
            f"Se esperaba exactamente un paso {expected}; se encontraron {len(matches)}."
        )
    return matches[0]


def _step_duration(job: dict[str, Any], label: str, step_names: tuple[str, ...]) -> float:
    step = _select_step(job, step_names)
    step_name = step.get("name")
    if not isinstance(step_name, str):
        raise ReleaseObservabilityError("El paso de release no tiene un nombre válido.")
    return _duration_seconds(
        _timestamp(step.get("started_at"), f"paso {step_name} iniciado"),
        _timestamp(step.get("completed_at"), f"paso {step_name} completado"),
        label,
    )


def _has_step(job: dict[str, Any], names: tuple[str, ...]) -> bool:
    steps = job.get("steps")
    if not isinstance(steps, list):
        raise ReleaseObservabilityError("El job de release no contiene pasos.")
    return any(
        isinstance(step, dict) and step.get("name") in names
        for step in steps
    )


def build_report(
    workflow_run: dict[str, Any],
    workflow_jobs: dict[str, Any],
    *,
    release_job_name: str = RELEASE_JOB_NAME,
) -> dict[str, Any]:
    """Return timings for the completed release job without interpreting its result."""

    release_job = _select_release_job(workflow_jobs, release_job_name)
    created_at = _timestamp(workflow_run.get("created_at"), "workflow creado")
    started_at = _timestamp(workflow_run.get("run_started_at"), "workflow iniciado")
    updated_at = _timestamp(workflow_run.get("updated_at"), "workflow actualizado")
    job_started_at = _timestamp(release_job.get("started_at"), "job iniciado")
    job_completed_at = _timestamp(release_job.get("completed_at"), "job completado")
    run_id = workflow_run.get("id")
    attempt = workflow_run.get("run_attempt")
    source_commit = workflow_run.get("head_sha")
    source_ref = workflow_run.get("head_branch")
    if not isinstance(run_id, int) or run_id < 1:
        raise ReleaseObservabilityError("El workflow no declara un identificador válido.")
    if not isinstance(attempt, int) or attempt < 1:
        raise ReleaseObservabilityError("El workflow no declara un intento válido.")
    if not isinstance(source_commit, str) or not source_commit:
        raise ReleaseObservabilityError("El workflow no declara el commit de origen.")
    if not isinstance(source_ref, str) or not source_ref:
        raise ReleaseObservabilityError("El workflow no declara la referencia de origen.")

    common_timings = {
        "queue": _duration_seconds(created_at, started_at, "cola"),
        "workflow_execution": _duration_seconds(
            started_at, updated_at, "ejecución del workflow"
        ),
        "release_job": _duration_seconds(
            job_started_at, job_completed_at, "job de release"
        ),
        "dependencies": _step_duration(
            release_job, "dependencies", MEASURED_STEPS["dependencies"]
        ),
        "artifact_upload": _step_duration(
            release_job, "artifact_upload", MEASURED_STEPS["artifact_upload"]
        ),
    }
    rebuilt = _has_step(release_job, MEASURED_STEPS["gate"]) or _has_step(
        release_job, MEASURED_STEPS["build"]
    )
    if rebuilt:
        if not (
            _has_step(release_job, MEASURED_STEPS["gate"])
            and _has_step(release_job, MEASURED_STEPS["build"])
        ):
            raise ReleaseObservabilityError(
                "La revalidación de etiqueta debe incluir gate y build."
            )
        validation = {
            "mode": "revalidated",
            "tag_gate": "executed",
            "tag_build": "executed",
        }
        timings = {
            **common_timings,
            "gate": _step_duration(release_job, "gate", MEASURED_STEPS["gate"]),
            "build": _step_duration(release_job, "build", MEASURED_STEPS["build"]),
        }
    else:
        validation = {
            "mode": "reused-stable-preflight",
            "tag_gate": "not-run",
            "tag_build": "not-run",
        }
        timings = {
            **common_timings,
            **{
                label: _step_duration(release_job, label, step_names)
                for label, step_names in REUSE_STEPS.items()
            },
        }
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "workflow": {
            "run_id": run_id,
            "run_attempt": attempt,
            "source_commit": source_commit,
            "source_ref": source_ref,
            "job": release_job_name,
        },
        "validation": validation,
        "timings_seconds": timings,
        "unobserved": {
            "human_review": {
                "status": "not-observed",
                "reason": (
                    "El workflow actual no registra una decisión humana de "
                    "revisión o publicación."
                ),
            }
        },
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-run", type=Path, required=True)
    parser.add_argument("--workflow-jobs", type=Path, required=True)
    parser.add_argument("--job-name", default=RELEASE_JOB_NAME)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    try:
        report = build_report(
            _read_json(args.workflow_run, "los metadatos del workflow"),
            _read_json(args.workflow_jobs, "los metadatos de jobs"),
            release_job_name=args.job_name,
        )
    except ReleaseObservabilityError as exc:
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "error",
            "error": str(exc),
        }
        _write_json(output, report)
        print(json.dumps(report, ensure_ascii=False))
        return 2
    _write_json(output, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
