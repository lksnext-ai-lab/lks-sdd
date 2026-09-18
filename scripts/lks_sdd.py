#!/usr/bin/env python3
"""Stable command dispatcher for scripts bundled with the LKS-SDD plugin."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path
# A query may run from a consumer-local pinned runtime. Disable bytecode before
# importing any plugin module, not only after dispatching to query_project.
sys.dont_write_bytecode = True
from dual_distribution import filesystem_root


PLUGIN_ROOT = filesystem_root(Path(__file__).resolve().parents[1])
COMMANDS = {
    "v2": "scripts/v2_cli.py",
    "catalog": "scripts/v2_cli.py",
    "context": "scripts/v2_cli.py",
    "history": "scripts/v2_cli.py",
    "migrate": "scripts/v2_cli.py",
    "query": "scripts/query_project.py",
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
    "compatibility": "scripts/technology_resolution.py",
    "variants": "scripts/manage_project_variants.py",
    "profile-impact": "scripts/profile_impact.py",
    "validate-project": "scripts/validate_project.py",
    "validate-spec": "scripts/validate_spec.py",
    "traceability": "scripts/check_traceability.py",
    "client-view": "scripts/render_client_view.py",
    "status": "scripts/project_status.py",
    "work": "scripts/work_task.py",
    "doctor": "scripts/doctor_project.py",
    "runtime-doctor": "scripts/runtime_doctor.py",
    "visual-handoff": "scripts/manage_visual_handoff.py",
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
    # Legacy public work commands used action/root; accept both without ever
    # dispatching a v2 project into a writer for the table-based 1.5 contract.
    if command in {"work", "tasks", "planning", "continuity", "tracking"} and len(forwarded) > 1:
        from v2_cli import is_v2
        candidate = Path(forwarded[1])
        if not forwarded[0].startswith("-") and candidate.is_dir() and is_v2(candidate):
            forwarded = [forwarded[1], forwarded[0], *forwarded[2:]]
    # A shared project never silently runs a different global installation.
    migration_route = command == "migrate" or (command == "v2" and forwarded and forwarded[0] in {
        "migration-diagnose", "migration-preview", "migrate", "recover", "rollback"})
    if command not in {"runtime-doctor", "query"} and not migration_route:
        from runtime_doctor import check as check_runtime
        for argument in forwarded:
            if argument.startswith("-"):
                continue
            try:
                candidate = filesystem_root(Path(argument))
                locked = candidate.is_dir() and (candidate / ".lks-sdd/distribution-lock.json").is_file()
            except (OSError, ValueError):
                continue
            if not locked:
                continue
            runtime = check_runtime(candidate)
            if runtime["status"] == "blocked":
                print(json.dumps(runtime, ensure_ascii=False))
                return 2
            pinned = (candidate / runtime["runtime"]).resolve()
            if pinned != PLUGIN_ROOT:
                print(json.dumps({"status": "blocked", "error": "Use the exact project-pinned CLI and workflows",
                                  "cli": str(pinned / "scripts/lks_sdd.py")}, ensure_ascii=False))
                return 2
            break
    if command in {"catalog", "context", "history", "migrate"}:
        from v2_cli import main as v2_main
        return v2_main(forwarded, command=command)
    if command not in {"v2", "query", "variants", "profiles", "compatibility", "profile-impact", "runtime-doctor", "visual-handoff"} and forwarded and not forwarded[0].startswith("-"):
        from v2_cli import is_v2, main as v2_main
        project = Path(forwarded[0])
        if command == "define" and project.is_dir() and not (project / ".lks-sdd/project.json").exists():
            return v2_main(forwarded, command="init")
        if project.is_dir() and is_v2(project):
            route = {"validate-project": "validate", "validate-spec": "validate", "assess-readiness": "readiness",
                     "implement": "start", "verify": "verify", "status": "status", "doctor": "validate",
                     "help": "status", "client-view": "catalog", "define": "author", "traceability": "context"}
            if command in route:
                return v2_main(forwarded, command=route[command])
            if command in {"tasks", "work", "planning", "continuity", "tracking"}:
                action = forwarded[1] if len(forwarded) > 1 and not forwarded[1].startswith("-") else "status"
                action_route = {"status": "status", "board": "status", "assess": "readiness", "next": "readiness",
                                "authorize": "authorize", "start": "start", "resume": "resume", "checkpoint": "checkpoint",
                                "review": "checkpoint", "verify": "verify", "close": "close", "diff": "diff",
                                "prepare": "prepare", "problem": "problem", "correct": "correct", "replan": "replan", "revoke": "revoke"}
                if command == "tracking":
                    action_route = {a: "tracking-" + a for a in ("status", "project", "authorize", "result", "reconcile")}
                if action not in action_route:
                    print(json.dumps({"status": "blocked", "error": "Use the documented v2 command for this transition"}))
                    return 2
                arguments = [forwarded[0], *(forwarded[2:] if len(forwarded) > 1 and forwarded[1] == action else forwarded[1:])]
                if action == "review":
                    arguments += ["--state", "in-review"]
                return v2_main(arguments, command=action_route[action])
            if command not in {"query", "compatibility", "profiles", "profile-impact", "runtime-doctor", "visual-handoff"}:
                print(json.dumps({"status": "blocked", "error": "This legacy command does not write contract 2.0; use lks_sdd.py v2 --help"}))
                return 2
    if command == "verify" and "--variant" in forwarded:
        from manage_project_variants import forward_verify
        return forward_verify(forwarded)
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
