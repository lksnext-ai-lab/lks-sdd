"""The public v5 interface. All mutating commands have explicit arguments."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import v5_core as core


def main(argv=None):
    parser = argparse.ArgumentParser(description="LKS-SDD 5: capabilities, task and one evolving plan")
    parser.add_argument("command", choices=["context", "status", "validate", "check", "fingerprint", "authorize",
        "prepare", "init", "close", "delivery", "resume", "doctor", "artifact", "import-result", "wait-result",
        "migration-preview", "migration-apply", "migration-resume", "discard-preview"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--task")
    parser.add_argument("--check")
    parser.add_argument("--source")
    parser.add_argument("--data", type=Path, help="JSON arguments; use - for stdin without a temporary argument file")
    parser.add_argument("--preview")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    command = args.command
    try:
        data = json.loads(sys.stdin.buffer.read() if str(args.data) == "-" else args.data.read_bytes()) if args.data else {}
        if command.startswith("migration-") or command == "discard-preview":
            import v5_migration as migration
            result = (migration.preview(root, **data) if command == "migration-preview" else
                      migration.discard_preview(root) if command == "discard-preview" else
                      migration.run(root, args.preview, resume=command == "migration-resume"))
        elif command == "doctor":
            from v5_distribution import doctor
            result = doctor(root)
        else:
            from v5_distribution import doctor
            binding = doctor(root)
            if binding.get("runtime") and core.filesystem_root(Path(__file__).resolve().parents[1]) != core.filesystem_root(root / binding["runtime"]):
                raise ValueError("Use the project's exact pinned CLI; do not substitute this installed core")
            if command == "context": result = core.context(root, args.task)
            elif command == "status": result = core.status(root, args.task)
            elif command == "validate": result = core.validate(root, args.task)
            elif command == "resume": result = core.resume(root)
            elif command == "check": result = core.check_task(root, args.task, args.check)
            elif command == "fingerprint":
                name = core.task_path(args.task, "tarea")
                task = core.current(root, name)[0]
                plan = core.current(root, core.task_path(args.task, "plan"))[0]
                result = {"inputs": core.input_fingerprint(root, name, task, plan["checks"][args.check])}
            elif command == "prepare": result = core.prepare(root, args.task, **data)
            elif command == "authorize": result = core.authorize(root, args.task, **data)
            elif command == "delivery": result = core.delivery(root, args.task, data)
            elif command == "artifact": result = core.artifact(root, args.source)
            elif command == "close":
                updates = {unit: core.read(root, name) for unit, name in data.get("updates", {}).items()}
                for unit, content in data.get("documents", {}).items():
                    if unit in updates or not isinstance(content, str):
                        raise ValueError("Supply one explicit source per consolidated unit")
                    updates[unit] = content.encode("utf-8")
                result = core.close(root, args.task, updates, data.get("facts"))
            elif command == "import-result":
                from v5_results import import_result
                result = import_result(root, args.task, args.check, args.source, **data)
            elif command == "wait-result":
                from v5_results import wait_file
                result = wait_file(root, args.source, **data)
            elif command == "init":
                if core.read(root, ".lks-sdd/project.json") or (root / "docs/lks-sdd").exists():
                    raise ValueError("Existing project requires migration/reconciliation, not initialization")
                if not data.get("project") or not isinstance(data.get("policy"), dict):
                    raise ValueError("Supply actual project context and policy; no preferred technology is assumed")
                name = core.unit_path("proyecto")
                result = core.apply(root, {name: core.document({"format": core.FORMAT,
                    "kind": "unit", "id": "proyecto", "depends_on": [], "policy": data["policy"]},
                    data["project"])}, {name: None})
        print(core.encode(result))
        return 0 if result.get("status") not in {"blocked", "failed"} else 2
    except (ValueError, OSError, KeyError) as exc:
        print(core.encode({"status": "blocked", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
