#!/usr/bin/env python3
"""Read-only structural/integrity check of a native Copilot ZIP, not host acceptance."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys
import zipfile

from dual_distribution import SKILLS, digest, safe_name, runtime_identity


def unpack(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(item.file_size for item in archive.infolist()) > 1024 ** 3:
            raise ValueError("Archive exceeds the one-GiB validation budget")
        files, seen = {}, set()
        for item in archive.infolist():
            name = safe_name(item.filename)
            if name.casefold() in seen or item.is_dir() or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Duplicate, directory or linked archive entry")
            seen.add(name.casefold())
            files[name] = archive.read(item)
        return files


def validate(data):
    packed = unpack(data)
    if any(not name.startswith("lks-sdd/") for name in packed):
        raise ValueError("Expected one lks-sdd plugin root")
    files = {name[len("lks-sdd/"):]: value for name, value in packed.items()}
    manifest = json.loads(files["plugin.json"])
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json" or manifest.get("name") != "lks-sdd":
        raise ValueError("Unexpected native plugin manifest")
    expected_skills = {f"skills/lks-sdd-{suffix}/SKILL.md" for suffix in SKILLS}
    if {p for p in files if p.startswith("skills/") and p.endswith("/SKILL.md")} != expected_skills:
        raise ValueError("Expected exactly six native skills")
    if any(p.startswith(("hooks/", "agents/", "com.github.copilot/")) or p in {"mcp.json", ".mcp.json", "hooks.json"} for p in files):
        raise ValueError("Unrequested executable plugin components")
    core = {name[5:]: value for name, value in files.items() if name.startswith("core/")}
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    if manifest.get("version") != version:
        raise ValueError("Plugin/core version mismatch")
    for name in ("docs/LEARNING-GUIDE.md", "docs/COPILOT-PILOT.md", "docs/INSTALLATION.md"):
        if name not in core:
            raise ValueError(f"Missing shared documentation: {name}")
    for suffix in SKILLS:
        if f"skills/lks-sdd-{suffix}/SKILL.md" not in core:
            raise ValueError("Missing complete workflow")
    setup = json.loads(files["setup/payload-manifest.json"])
    for name, expected in setup["files"].items():
        if digest(files["setup/" + safe_name(name)]) != expected:
            raise ValueError(f"Setup integrity mismatch: {name}")
    project = unpack(files["setup/payload/copilot.zip"])
    lock = json.loads(project[".lks-sdd/distribution-lock.json"])
    if lock.get("entrypoints") != "plugin" or any(p.startswith(".github/skills/") for p in project):
        raise ValueError("Native setup must not duplicate project skills")
    if lock["version"] != version or lock["runtime_digest"] != runtime_identity(core):
        raise ValueError("Pinned core identity mismatch")
    runtime = safe_name(lock["runtime"])
    actual_core = {p[len(runtime) + 1:]: value for p, value in project.items() if p.startswith(runtime + "/")}
    if actual_core != core:
        raise ValueError("Bootstrap and native core bytes differ")
    return {"status": "valid", "version": version, "skills": 6,
            "runtime_digest": lock["runtime_digest"], "channel": setup["channel"],
            "host_acceptance": "not-run"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.package.read_bytes())
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
