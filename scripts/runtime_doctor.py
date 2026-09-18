#!/usr/bin/env python3
"""Check the project's exact shared runtime and host adapters without mutation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from dual_distribution import BEGIN, END, digest, json_bytes, safe_name, filesystem_root


def check(root: Path) -> dict:
    root = filesystem_root(root)
    lock_path = root / ".lks-sdd/distribution-lock.json"
    if not lock_path.exists():
        return {"status": "unmanaged", "errors": [], "runtime": None}
    errors = []
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock.get("schema_version") != "1.0" or lock.get("project_schema") not in {"1.5", "2.0"}:
            raise ValueError("Unsupported distribution contract")
        entrypoints = lock.get("entrypoints", "project")
        if entrypoints not in {"project", "plugin"}:
            raise ValueError("Unsupported entrypoints mode")
        if entrypoints == "plugin":
            for suffix in ("help", "define", "adopt-existing", "assess-readiness", "implement", "verify"):
                if (root / f".github/skills/lks-sdd-{suffix}/SKILL.md").exists():
                    errors.append(f"Duplicate project/plugin skill: lks-sdd-{suffix}")
        runtime_name = safe_name(lock["runtime"])
        if not runtime_name.startswith(".lks-sdd/runtime/"):
            raise ValueError("Runtime must be project-local")
        runtime = root / runtime_name
        if not isinstance(lock["runtime_files"], dict) or not lock["runtime_files"]:
            raise ValueError("Empty runtime inventory")
        for path in runtime.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                relative = path.relative_to(runtime).as_posix()
                if relative not in lock["runtime_files"]:
                    errors.append(f"Unexpected runtime file: {relative}")
        checks = {f"{runtime_name}/{p}": h for p, h in lock["runtime_files"].items()}
        checks.update(lock["managed_files"])
        for relative, expected in checks.items():
            path = root / safe_name(relative)
            links = [p for p in [path, *path.parents] if p != root and root in p.parents]
            if not path.resolve().is_relative_to(root) or any(
                p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in links
            ):
                raise ValueError(f"Unsafe managed path: {relative}")
            if not path.is_file():
                errors.append(f"Missing: {relative}")
                continue
            data = path.read_bytes()
            if relative in {"AGENTS.md", ".github/copilot-instructions.md"}:
                text = data.decode("utf-8").replace("\r\n", "\n")
                if text.count(BEGIN) != 1 or text.count(END) != 1:
                    raise ValueError(f"Invalid instruction block: {relative}")
                data = (BEGIN + text.split(BEGIN)[1].split(END)[0] + END + "\n").encode("utf-8")
            if digest(data) != expected:
                errors.append(f"Modified: {relative}")
        if digest(json_bytes(lock["runtime_files"])) != lock["runtime_digest"]:
            errors.append("Runtime inventory digest mismatch")
        manifest = json.loads((runtime / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        if manifest.get("version") != lock["version"]:
            errors.append("Runtime version mismatch")
        project_index = root / ".lks-sdd/project.json"
        if project_index.is_file() and json.loads(project_index.read_text(encoding="utf-8")).get("schema_version") != lock["project_schema"]:
            errors.append("Project schema differs from its pinned distribution; use explicit migration/recovery")
        return {"status": "valid" if not errors else "blocked", "errors": errors,
                "runtime": runtime_name, "version": lock["version"], "channel": lock["channel"]}
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return {"status": "blocked", "errors": [str(exc)], "runtime": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check(args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
