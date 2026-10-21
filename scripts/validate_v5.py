"""Static validation of the actual curated v5 distribution and contract sources."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys

from v5_core import digest
from v5_distribution import SKILLS, RUNTIME, core_files, artifacts, inventory


def validate(root, canonical_hashes):
    errors = []
    root = Path(root)
    for name, expected in canonical_hashes.items():
        path = root / "specs/canonical" / name
        if not path.is_file() or digest(path.read_bytes()).upper() != expected:
            errors.append("Canonical source changed/missing: " + name)
    try:
        files = core_files(root)
        manifest = json.loads(files[".codex-plugin/plugin.json"])
        if manifest["name"] != "lks-sdd" or manifest["version"] != "5.0.0":
            errors.append("Unexpected plugin identity/version")
        dual = json.loads(files["distribution/dual.json"])
        if dual["project_schema"] != "5.0" or dual["hosts"] != ["codex", "copilot"]:
            errors.append("Distribution method/hosts mismatch")
        descriptions = set()
        for suffix in SKILLS:
            text = files[f"skills/lks-sdd-{suffix}/SKILL.md"].decode()
            description = re.search(r"^description: (.+)$", text, re.M)
            if not description or description[1] in descriptions or len(text) < 900:
                errors.append("Missing/full workflow or overlapping identical description: " + suffix)
            else:
                descriptions.add(description[1])
            if "docs/V5.md" not in text or "runtime" not in text:
                errors.append("Missing v5/runtime routing: " + suffix)
        for name, raw in files.items():
            if name.endswith(".py"):
                tree = ast.parse(raw, filename=name)
                for node in ast.walk(tree):
                    modules = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else (
                        [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
                    for module in modules:
                        if module not in sys.stdlib_module_names and module not in RUNTIME:
                            errors.append(f"Unshipped dependency {module}: {name}")
            if name.startswith(("scripts/v2", "scripts/v3", "scripts/v4")) or "/references/v3" in name:
                errors.append("Operational legacy dependency shipped: " + name)
        first, second = artifacts(files, "static-content", "local-preparation"), artifacts(files, "static-content", "local-preparation")
        if inventory(first) != inventory(second):
            errors.append("Non-reproducible dual distribution")
    except (ValueError, KeyError, OSError, SyntaxError) as exc:
        errors.append(str(exc))
    return errors
