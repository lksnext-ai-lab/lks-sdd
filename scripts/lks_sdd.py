#!/usr/bin/env python3
"""Stable command dispatcher for scripts bundled with the LKS-SDD plugin."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "help": "skills/lks-sdd-help/scripts/context_help.py",
    "define": "skills/lks-sdd-define/scripts/init_project.py",
    "adopt-inspect": "skills/lks-sdd-adopt-existing/scripts/inspect_repository.py",
    "adopt-validate": "skills/lks-sdd-adopt-existing/scripts/validate_adoption.py",
    "adopt-materialize": "skills/lks-sdd-adopt-existing/scripts/materialize_adoption.py",
    "assess-readiness": "skills/lks-sdd-assess-readiness/scripts/assess_readiness.py",
    "implement": "skills/lks-sdd-implement/scripts/prepare_increment.py",
    "verify": "skills/lks-sdd-verify/scripts/run_verification.py",
    "tasks": "scripts/manage_tasks.py",
    "planning": "scripts/manage_planning.py",
    "tracking": "scripts/manage_task_tracking.py",
    "continuity": "scripts/manage_continuity.py",
    "profiles": "scripts/validate_reference_profile.py",
    "validate-project": "scripts/validate_project.py",
    "validate-spec": "scripts/validate_spec.py",
    "traceability": "scripts/check_traceability.py",
    "client-view": "scripts/render_client_view.py",
    "status": "scripts/project_status.py",
    "work": "scripts/work_task.py",
    "doctor": "scripts/doctor_project.py",
}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="strict")
    parser = argparse.ArgumentParser(
        description=(
            "Punto de entrada portable. Use la ruta absoluta de este archivo desde "
            "la instalación del plugin y pase después los argumentos del comando."
        )
    )
    parser.add_argument("command", choices=tuple(COMMANDS))
    if len(sys.argv) == 1 or sys.argv[1] in {"-h", "--help"}:
        parser.print_help()
        return 0
    command = sys.argv[1]
    if command not in COMMANDS:
        parser.error(
            f"argument command: invalid choice: {command!r} "
            f"(choose from {', '.join(repr(item) for item in COMMANDS)})"
        )
    forwarded = sys.argv[2:]
    target = (PLUGIN_ROOT / COMMANDS[command]).resolve()
    try:
        target.relative_to(PLUGIN_ROOT)
    except ValueError:
        parser.error("El comando resuelto queda fuera del plugin.")
    if not target.is_file():
        parser.error(f"Falta el ejecutable empaquetado: {COMMANDS[command]}")
    original_argv = sys.argv
    original_path = list(sys.path)
    try:
        sys.argv = [str(target), *forwarded]
        sys.path.insert(0, str(target.parent))
        runpy.run_path(str(target), run_name="__main__")
    except SystemExit as exc:
        return int(exc.code or 0)
    finally:
        sys.argv = original_argv
        sys.path[:] = original_path
    return 0


if __name__ == "__main__":
    sys.exit(main())
