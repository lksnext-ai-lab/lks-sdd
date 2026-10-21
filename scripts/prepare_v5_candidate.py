"""Prepare a reproducible local v5 build without commit, registry or installation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

from v5_core import atomic_write, digest, encode
from v5_distribution import artifacts, core_files, inventory


def prepare(root, output):
    from validate_plugin_contract import validate
    errors = validate(root)
    if errors:
        raise ValueError("Static contract failed: " + encode(errors))
    core = core_files(root)
    from build_candidate_package import SECRET_PATTERNS
    for name, raw in core.items():
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS):
            raise ValueError("Possible secret in curated source: " + name)
    source = "sha256:" + digest(encode(inventory(core)).encode())
    files = artifacts(core, source, "local-preparation")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        atomic_write(output / name, raw)
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    report = {"status": "prepared", "version": "5.0.0", "source_content": source, "base_commit": commit,
              "source_state": "local-worktree-not-a-stable-release", "files": inventory(files),
              "publication": "not-run", "installation": "not-run", "host_acceptance": "not-run"}
    atomic_write(output / "PREPARATION.json", encode(report).encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(encode(prepare(args.root, args.output or args.root / "dist/v5-prepared")))


if __name__ == "__main__":
    main()
