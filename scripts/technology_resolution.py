"""Read-only consumer dependency diagnosis. Never runs a package manager."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LAYOUTS = {"flat": {"api": "backend", "frontend": "frontend"},
           "apps": {"api": "apps/backend", "frontend": "apps/frontend"}}
INPUT_NAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "pyproject.toml",
               "uv.lock", "requirements.txt", "requirements.lock", "requirements-dev.txt",
               ".python-version", ".node-version", "Dockerfile", "compose.yaml"}
EXACT = re.compile(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?")
PY_PIN = re.compile(r"^([a-zA-Z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;\\]+)")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    target = root / relative
    target.resolve().relative_to(root.resolve())
    current = root
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("linked input is not permitted")
    if target.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("dependency input exceeds diagnostic limit")
    return target


def inspect_dependencies(root: Path) -> dict[str, Any]:
    root = root.resolve()
    declared: dict[str, str] = {}
    resolved: dict[str, str] = {}
    runtime: dict[str, str] = {}
    tools: dict[str, str] = {}
    files: dict[str, str] = {}
    errors: list[str] = []
    locations = [".", "backend", "frontend", "database", "migration", "apps/backend", "apps/frontend", "apps/migration", "infra", "infra/compose", "infra/database"]
    def register(target, key, version):
        if key in target and target[key] != version:
            if target is runtime and (str(version).startswith(target[key] + ".") or target[key].startswith(str(version) + ".")):
                target[key] = max([target[key], str(version)], key=len)
                return
            if target is resolved:
                previous = target[key] if isinstance(target[key], list) else [target[key]]
                target[key] = sorted(set([*previous, str(version)]))
                return
            errors.append(f"conflicting versions for {key}")
        target[key] = str(version)
    for location in locations:
        for name in sorted(INPUT_NAMES):
            relative = (Path(location) / name).as_posix()
            if not (root / relative).exists():
                continue
            try:
                path = safe_file(root, relative)
                content = path.read_bytes()
                files[relative] = hashlib.sha256(content).hexdigest()
                text = content.decode("utf-8")
                if name == "package.json":
                    obj = json.loads(text)
                    for section in ("dependencies", "devDependencies", "optionalDependencies"):
                        for key, val in obj.get(section, {}).items():
                            register(declared, "npm:" + key, val)
                    if obj.get("packageManager"):
                        manager, _, version = obj["packageManager"].partition("@")
                        register(tools, manager, version)
                    for key, value in obj.get("engines", {}).items():
                        if key == "node":
                            register(declared, "runtime:node", value)
                elif name == "package-lock.json":
                    obj = json.loads(text)
                    for key, val in obj.get("packages", {}).items():
                        if key.startswith("node_modules/"):
                            register(resolved, "npm:" + key.rsplit("node_modules/", 1)[1], val.get("version", "unknown"))
                elif name == "pnpm-lock.yaml":
                    # Read package snapshot keys, not metadata-supplied commands.
                    for key, version in re.findall(r"^  '?([^\s'()]+)@(\d+\.\d+\.\d+[^\s:'()]*)[^:]*:\s*$", text, re.M):
                        register(resolved, "npm:" + key, version)
                elif name in {"pyproject.toml", "uv.lock"}:
                    obj = tomllib.loads(text)
                    if name == "uv.lock":
                        for item in obj.get("package", []):
                            if item.get("version") and item.get("source", {}).get("registry"):
                                register(resolved, "python:" + item["name"].lower().replace("_", "-"), item["version"])
                    else:
                        project = obj.get("project", {})
                        if project.get("requires-python"):
                            register(declared, "runtime:python", project["requires-python"])
                        deps = list(project.get("dependencies", []))
                        for group in obj.get("dependency-groups", {}).values():
                            deps.extend(d for d in group if isinstance(d, str))
                        for dep in deps:
                            match = PY_PIN.match(dep)
                            if match:
                                register(declared, "python:" + match[1].lower().replace("_", "-"), match[2])
                elif name.startswith("requirements"):
                    target = resolved if name == "requirements.lock" else declared
                    for line in text.splitlines():
                        match = PY_PIN.match(line.strip())
                        if match:
                            register(target, "python:" + match[1].lower().replace("_", "-"), match[2])
                elif name in {".python-version", ".node-version"}:
                    register(runtime, name[1:-8], text.strip())
                elif name in {"Dockerfile", "compose.yaml"}:
                    for tool, version in re.findall(r"\b(uv|pip|npm|pnpm)(?:==|@)(\d+\.\d+\.\d+)", text):
                        register(tools, tool, version)
                    for image, version, sha in re.findall(r"(?:FROM|image:)\s+(python|node|postgres):([\w.-]+)(?:@sha256:([a-f0-9]{64}))?", text):
                        match = re.match(r"\d+(?:\.\d+){0,2}", version)
                        if match:
                            register(runtime, "postgresql" if image == "postgres" else image, match[0])
                        if not sha:
                            errors.append(f"{relative}: unpinned {image} image")
            except (OSError, ValueError, TypeError, KeyError) as exc:
                errors.append(f"{relative}: unreadable or invalid {type(exc).__name__}")
    layouts = [key for key, paths in LAYOUTS.items() if all((root / p).is_dir() for p in paths.values())]
    result = {"schema_version": "1.0", "read_only": True, "declared": declared, "resolved": resolved,
            "runtime_declared": runtime, "runtime_verified": {}, "tools_declared": tools,
            "input_hashes": files, "dependency_fingerprint": digest(files), "layouts": layouts,
            "errors": sorted(set(errors))}
    from evidence_safety import sanitize
    clean, contamination = sanitize(result)
    if contamination:
        clean["errors"].append("sensitive dependency metadata was redacted; diagnosis is incomplete")
    return clean


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect local dependency declarations without executing them.")
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_dependencies(args.project_root), ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
