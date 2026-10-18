#!/usr/bin/env python3
"""Check the project's exact shared runtime and host adapters without mutation."""
from __future__ import annotations

import argparse
import json
import hashlib
import os
import stat
from path_utils import file_attributes, filesystem_root
from pathlib import Path
import sys

from dual_distribution import BEGIN, END, digest, json_bytes, safe_name, filesystem_root


def _linked(path):
    # Observe once for both predicates; this is never a cache across paths.
    # On an observation error retain the former Path predicate behaviour.
    attributes = file_attributes(path)
    if attributes is not None:
        if not attributes & 0x400: return False
        return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
    try: info = path.lstat()
    except OSError:
        return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())
    return stat.S_ISLNK(info.st_mode) or (hasattr(path, "is_junction") and
                                         getattr(info, "st_reparse_tag", 0) == 0xA0000003)


def check(root: Path) -> dict:
    # Normalize once. Every descendant then has the Windows extended spelling;
    # _linked need not normalize thousands of already absolute paths again.
    root = filesystem_root(root, force_extended=True)
    lock_path = root / ".lks-sdd/distribution-lock.json"
    if not lock_path.exists():
        return {"status": "unmanaged", "errors": [], "runtime": None}
    errors = []
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock.get("schema_version") != "1.0" or lock.get("project_schema") not in {"1.5", "2.0", "3.0", "3.1"}:
            raise ValueError("Unsupported distribution contract")
        # Keep this diagnostic independent of the transaction engine it checks.
        # This metadata-only rule matches the core and offline installer.
        formats = lock.get("storage_formats", [])
        if not isinstance(formats, list): raise ValueError("Invalid runtime storage capabilities")
        pending = root / ".lks-sdd/transaction.json"
        if pending.exists():
            if _linked(pending) or pending.stat().st_size > 128*1024*1024:
                raise ValueError("Invalid or excessive pending journal")
            tag = json.loads(pending.read_bytes()).get("schema_version", "")
            if isinstance(tag, str) and tag.startswith("lks-sdd-store-maintenance/") and tag not in formats:
                raise ValueError("Pinned runtime cannot recover the pending maintenance format")
        if "lks-sdd-store-maintenance/2" in formats:
            required = {"scripts/" + name for name in ("store_compaction.py", "store_maintenance_batches.py", "store_json_inspector.py")}
            if not required <= set(lock.get("runtime_files", {})):
                raise ValueError("Incomplete pinned maintenance /2 recovery inventory")
        if "lks-sdd-object-zip/1" not in formats:
            folder = root / ".lks-sdd/objects/packs"
            cursor = folder
            while cursor != root:
                if _linked(cursor): raise ValueError("Unsafe object ZIP directory")
                cursor = cursor.parent
            if folder.exists():
                if not folder.is_dir(): raise ValueError("Invalid object ZIP directory")
                with os.scandir(folder) as entries:
                    if next(entries, None) is not None:
                        raise ValueError("Incompatible ZIP reader: restore a verified compatible store before changing the pin")
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
            if not path.is_relative_to(root):
                raise ValueError(f"Unsafe managed path: {relative}")
            # Walk the same ancestors once, without rebuilding every ancestor's
            # own parents to test containment. Every route still observes each
            # link freshly; no trust result survives another file or check.
            cursor = path
            while cursor != root:
                if _linked(cursor):
                    raise ValueError(f"Unsafe managed path: {relative}")
                cursor = cursor.parent
            if not path.is_file():
                errors.append(f"Missing: {relative}")
                continue
            if relative in {"AGENTS.md", ".github/copilot-instructions.md"}:
                data = path.read_bytes()
                text = data.decode("utf-8").replace("\r\n", "\n")
                if text.count(BEGIN) != 1 or text.count(END) != 1:
                    raise ValueError(f"Invalid instruction block: {relative}")
                data = (BEGIN + text.split(BEGIN)[1].split(END)[0] + END + "\n").encode("utf-8")
                actual = digest(data)
            else:
                observed = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(64*1024), b""): observed.update(block)
                actual = observed.hexdigest()
            if actual != expected:
                errors.append(f"Modified: {relative}")
        if digest(json_bytes(lock["runtime_files"])) != lock["runtime_digest"]:
            errors.append("Runtime inventory digest mismatch")
        manifest = json.loads((runtime / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        if manifest.get("version") != lock["version"]:
            errors.append("Runtime version mismatch")
        distribution = json.loads((runtime / "distribution/dual.json").read_text(encoding="utf-8"))
        if lock.get("storage_formats", []) != distribution.get("storage_formats", []):
            errors.append("Runtime storage capabilities mismatch")
        if lock.get("method_version", distribution.get("method_version")) != distribution.get("method_version"):
            errors.append("Runtime method declaration mismatch")
        project_index = root / ".lks-sdd/project.json"
        if project_index.is_file():
            project = json.loads(project_index.read_text(encoding="utf-8"))
            if project.get("schema_version") != lock["project_schema"]:
                errors.append("Project schema differs from its pinned distribution; use explicit migration/recovery")
            if project.get("schema_version") in {"2.0", "3.0", "3.1"} and project.get("method_version") not in lock.get(
                    "readable_method_versions", [distribution.get("method_version")]):
                errors.append("Project method is unsupported by its pinned runtime")
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
