"""Full-core development reproducibility and isolated pinned 1.5 -> 2.0 migration.

Does not install into a host, create commits, publish or attest a clean release.
"""
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_dual_distribution import collect_development
from build_candidate_package import EXCLUDED_PARTS, _package_integrity_bytes
from dual_distribution import artifacts, compact_distribution_core, digest, filesystem_root, project_files
from runtime_doctor import check
from validate_copilot_package import validate
from v2_contract import canonical, load
from v2_storage import recover


def command(script, *args, cwd):
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), *map(str, args), "--json"],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=180)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def write_tree(root, files):
    for relative, raw in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def run(baseline_commit=None):
    started = time.monotonic()
    core = collect_development(ROOT)
    source = "working-tree:" + digest(canonical({p: digest(b) for p, b in sorted(core.items())}))
    first = artifacts(core, source, "development-not-certified")
    second = artifacts(dict(reversed(list(core.items()))), source, "development-not-certified")
    assert first == second, "Two builds from the same source must have identical bytes"
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    native = validate(first[f"lks-sdd-copilot-plugin-v{version}.zip"])
    assert native["status"] == "valid", native
    if baseline_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", baseline_commit):
        raise ValueError("Baseline must be an explicit immutable 40-character commit ID")
    revision = baseline_commit or subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    archive = subprocess.run(["git", "archive", "--format=zip", revision], cwd=ROOT, capture_output=True, check=True).stdout
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        old_core = {name: bundle.read(name) for name in bundle.namelist() if not name.endswith("/")
                    and not EXCLUDED_PARTS.intersection(Path(name).parts)
                    and not name.startswith(("tests/reports/", "pilot/runs/", "site/"))}
    old_version = json.loads(old_core[".codex-plugin/plugin.json"])["version"]
    assert not old_version.startswith("2."), "Select an explicit 1.x baseline with --baseline-commit"
    old_core["package-integrity.json"] = _package_integrity_bytes(list(old_core.items()), old_version, revision)
    old_core = compact_distribution_core(old_core)
    target_core = compact_distribution_core(core)
    with tempfile.TemporaryDirectory(prefix="lks-v2-dist-") as directory:
        base = filesystem_root(Path(directory))
        consumer, target = base / "consumer", base / "target"
        old_files = project_files(old_core, revision, "historical-baseline-not-new-release")
        write_tree(consumer, old_files)
        write_tree(target, target_core)
        old_lock = json.loads(old_files[".lks-sdd/distribution-lock.json"])
        old_cli = consumer / old_lock["runtime"] / "scripts/lks_sdd.py"
        command(old_cli, "define", consumer, "--project-id", "synthetic-pinned-migration", cwd=consumer)
        before = (consumer / ".lks-sdd/project.json").read_bytes()
        assert json.loads(before)["schema_version"] == "1.5"
        assert check(consumer)["status"] == "valid"
        cli = ROOT / "scripts/lks_sdd.py"
        proposed = command(cli, "v2", "migration-preview", consumer, "--target-runtime", target, cwd=consumer)
        assert (consumer / ".lks-sdd/project.json").read_bytes() == before
        migrated = command(cli, "v2", "migrate", consumer, "--target-runtime", target,
                           "--apply", "--authorize", proposed["preview_hash"], cwd=consumer)
        assert migrated["status"] == "applied", migrated
        model = load(consumer)
        model.require_valid()
        assert model.manifest["schema_version"] == "2.0"
        assert not model.by_kind("feature") and not model.by_kind("authorization")
        assert check(consumer)["status"] == "valid", check(consumer)
        new_lock = json.loads((consumer / ".lks-sdd/distribution-lock.json").read_bytes())
        assert new_lock["runtime"] != old_lock["runtime"]
        for name, raw in old_files.items():
            if name.startswith(old_lock["runtime"] + "/"):
                assert (consumer / name).read_bytes() == raw, name
        new_cli = consumer / new_lock["runtime"] / "scripts/lks_sdd.py"
        validated = command(new_cli, "validate-project", consumer, cwd=consumer)
        assert validated.get("status") == "valid", validated
        queried = command(new_cli, "query", consumer, "--topic", "Proyecto", "--mode", "docs-only", cwd=consumer)
        assert queried.get("kind") == "query-context", queried
        assert queried["metrics"]["code_files_read"] == 0 and not queried.get("writes"), queried
        recover(consumer, proposed["preview_hash"], rollback=True, receipt=migrated["receipt"])
        assert (consumer / ".lks-sdd/project.json").read_bytes() == before
        assert (consumer / ".lks-sdd/distribution-lock.json").read_bytes() == old_files[".lks-sdd/distribution-lock.json"]
        assert check(consumer)["status"] == "valid", check(consumer)
    return {"kind": "development-distribution-smoke-not-release-attestation", "status": "passed",
        "source": source, "source_commit_baseline": revision, "version": version,
        "historical_runtime_version": old_version, "core_files": len(target_core),
        "reproducibility": "identical-bytes-two-builds", "artifacts": {p: digest(b) for p, b in first.items()},
        "pinned_migration": "passed", "rollback": "exact-original-bytes", "native_archive": "valid",
        "full_pinned_query": "passed", "query_metrics": queried["metrics"],
        "seconds": time.monotonic() - started, "active_installation": "not-performed",
        "host_acceptance": "not-run", "clean_release_attestation": "not-claimed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--baseline-commit", help="Immutable 1.x commit; defaults to HEAD while developing from 1.x")
    args = parser.parse_args()
    try:
        result = run(args.baseline_commit)
    except (ValueError, OSError, AssertionError, subprocess.SubprocessError) as exc:
        result = {"status": "failed", "error": str(exc), "host_acceptance": "not-run"}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
    print(output)
    raise SystemExit(0 if result["status"] == "passed" else 1)
