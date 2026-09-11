#!/usr/bin/env python3
"""Build explicitly diagnostic dual packages from reviewed working-tree files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from dual_distribution import artifacts, digest, safe_name
from build_candidate_package import SECRET_PATTERNS, EXCLUDED_PARTS, _package_integrity_bytes

ROOT = Path(__file__).resolve().parents[1]


def collect_development(root):
    tracked = subprocess.run(["git", "ls-files", "-z", "--cached"], cwd=root,
                             capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    extra = json.loads((root / "distribution/dual.json").read_text(encoding="utf-8"))["additional_files"]
    files = {}
    for name in sorted(set(filter(None, tracked)) | set(extra)):
        safe_name(name)
        path = root / name
        if EXCLUDED_PARTS.intersection(path.relative_to(root).parts) or name.startswith(("tests/reports/", "pilot/runs/", "site/")):
            continue
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or unsafe source: {name}")
        content = path.read_bytes()
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            raise ValueError(f"Possible secret: {name}")
        # Respect repository LF policy for deterministic builds across Windows checkouts.
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2", ".zip"}:
            try:
                content = content.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
            except UnicodeError:
                pass
        files[name] = content
    version = json.loads(files[".codex-plugin/plugin.json"])["version"]
    files["package-integrity.json"] = _package_integrity_bytes(list(files.items()), version, "development-working-tree")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development", action="store_true", required=True,
                        help="Explicitly not a release attestation; clean release builder remains mandatory")
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        if output.exists():
            raise ValueError("Output must not already exist; no overwrite is supported")
        if output == ROOT or not output.parent.is_dir():
            raise ValueError("Choose a new directory under an existing output parent")
        core = collect_development(ROOT)
        source = "working-tree:" + digest(json.dumps({k: digest(v) for k, v in core.items()}, sort_keys=True).encode())
        result = artifacts(core, source, "development-not-certified")
        output.mkdir()
        for name, data in result.items():
            (output / name).write_bytes(data)
        print(json.dumps({"status": "built-development", "output": str(output),
                          "artifacts": list(result), "host_acceptance": "not-run"}, indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
