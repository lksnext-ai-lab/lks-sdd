"""Read-only package/source checks and documentary evidence for the local candidate.

Writes reports in this evidence directory; does not run or replace the release gate.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_dual_distribution import collect_development
from dual_distribution import artifacts, digest, runtime_identity
from validate_copilot_package import unpack, validate


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return result.stdout.strip()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("review_root", type=Path)
    args = parser.parse_args()
    review = args.review_root.resolve()
    bundle = review / "candidate-working-tree"
    core = collect_development(ROOT)
    manifest = read(bundle / "distribution-manifest.json")
    check(manifest["channel"] == "development-unreleased", "Unexpected channel")
    check(manifest["version"] == "3.3.0-rc.1", "Unexpected version")
    source = "working-tree:" + digest(json.dumps({k: digest(v) for k, v in core.items()}, sort_keys=True).encode())
    check(source == manifest["source"], "Working-tree source changed after the build")
    expected = artifacts(core, source, "development-unreleased")
    check(set(expected) == {p.name for p in bundle.iterdir()}, "Unexpected artifacts")
    for name, value in expected.items():
        check((bundle / name).read_bytes() == value, "Build reproduction mismatch: " + name)
    for line in (bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        sha, name = line.split(maxsplit=1)
        check(digest((bundle / name.strip()).read_bytes()) == sha, "Checksum mismatch: " + name)
    for name, sha in manifest["artifacts"].items():
        check(digest((bundle / name).read_bytes()) == sha, "Manifest mismatch: " + name)
    for path in bundle.glob("*.zip"):
        with zipfile.ZipFile(path) as archive:
            check(archive.testzip() is None, "Bad ZIP: " + path.name)
    version = manifest["version"]
    codex = unpack((bundle / f"lks-sdd-plugin-v{version}.zip").read_bytes())
    codex_core = {k[len("lks-sdd/"):]: v for k, v in codex.items()}
    native_bytes = (bundle / f"lks-sdd-copilot-plugin-v{version}.zip").read_bytes()
    native = unpack(native_bytes)
    native_core = {k[len("lks-sdd/core/"):]: v for k, v in native.items() if k.startswith("lks-sdd/core/")}
    marketplace = unpack((bundle / f"lks-sdd-marketplace-v{version}.zip").read_bytes())
    market_core = {k[len("plugins/lks-sdd/"):]: v for k, v in marketplace.items() if k.startswith("plugins/lks-sdd/")}
    check(core == codex_core == native_core == market_core, "Core byte parity failed")
    native_result = validate(native_bytes)
    check(runtime_identity(core) == manifest["runtime_digest"], "Runtime identity changed")
    static = {
        "plugin_contract": command(sys.executable, "-B", "-X", "utf8", "scripts/validate_plugin_contract.py", "."),
        "fixtures": command(sys.executable, "-B", "-X", "utf8", "scripts/validate_fixture_manifest.py"),
        "diff_check": command("git", "diff", "--check") or "passed",
    }
    check(not command("git", "status", "--porcelain", "--", "specs/canonical/"), "Canonical sources changed")
    initial = read(review / "technical-checks.json")
    windows = next(c for c in initial["checks"] if c["id"] == "windows-long-path-regression")
    smoke = read(review / "smoke-repeat.json")["check"]
    check(windows["status"] == smoke["status"] == "passed", "Required development checks not passed")
    unit_reports = []
    latest = {}
    for path in sorted(EVIDENCE.glob("*.json"), key=lambda p: (p.stat().st_mtime_ns, p.name)):
        value = read(path)
        if not isinstance(value.get("counts"), dict) or not isinstance(value.get("results"), list):
            continue
        unit_reports.append({"path": path.name, "sha256": digest(path.read_bytes()), "counts": value["counts"],
                             "duration_seconds": value.get("duration_seconds"), "passed": value.get("passed")})
        for row in value["results"]:
            latest[row["id"]] = {"id": row["id"], "status": row["status"], "report": path.name}
    check(latest and all(r["status"] == "passed" for r in latest.values()), "A latest focal test is not passed")
    readiness = read(review / "readiness-final.json")
    check(readiness["blockers"] == ["worktree"], "Unexpected candidate readiness blocker")
    counts = read(EVIDENCE / "storage-tests.json")["counts"]
    check(counts == {"total": 50, "passed": 50, "skipped": 0, "failed": 0}, "Storage regression incomplete")
    report = {
        "scope": "Technical preparation of uncommitted local candidate; not an official release gate or use acceptance",
        "version": version, "channel": manifest["channel"], "status": "prepared-development",
        "base_commit": command("git", "rev-parse", "HEAD"), "branch": command("git", "branch", "--show-current"),
        "source": source, "runtime_digest": manifest["runtime_digest"], "bundle": str(bundle),
        "artifact_sha256": {p.name: digest(p.read_bytes()) for p in sorted(bundle.iterdir())},
        "checks": {"byte_reproducibility": "passed", "checksums": "passed", "zip_integrity": "passed",
                   "source_codex_copilot_marketplace_parity": "passed", "canonical_sources_unchanged": "passed",
                   "source_files": len(core), "native_copilot": native_result, "static": static},
        "source_sha256": {k: digest(v) for k, v in core.items()},
        "test_evidence": {"reports": unit_reports, "latest_result_per_id": sorted(latest.values(), key=lambda x: x["id"]),
                          "source_attestation": "Historical working-tree runs; not a single immutable final-SHA gate",
                          "smoke": {k: v for k, v in smoke.items() if k not in {"_stdout", "_stderr"}},
                          "windows": {k: v for k, v in windows.items() if k not in {"_stdout", "_stderr"}},
                          "initial_timeout_preserved": str(review / "technical-checks.json"),
                          "smoke_repeat": str(review / "smoke-repeat.json"), "storage": counts},
        "official_readiness": readiness, "official_release_gate": "not-run; requires authorized clean commit",
        "human_review": "not-run", "host_acceptance": "not-run", "pilot": "not-run",
        "billed_tokens": "not-observed", "reliable_total_time_gain": "not-observed",
        "consumer_migration": "not-run", "publication": "not-run", "installation": "not-run",
    }
    write(EVIDENCE / "candidate-validation.json", report)
    documents = sorted(EVIDENCE.parent.glob("*.md"))
    issues, links = [], 0
    for path in documents:
        text = path.read_text(encoding="utf-8")
        for raw in re.findall(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)", text):
            target = raw[0] or raw[1]
            if target.startswith("#"):
                continue
            if re.match(r"^[A-Za-z]:[/\\]", target):
                linked = Path(unquote(target))
            elif urlsplit(target).scheme:
                continue
            else:
                linked = path.parent / unquote(urlsplit(target).path)
            links += 1
            # This report is emitted below; its own link is checked after writing.
            is_output = linked.resolve() == EVIDENCE / "global-review-validation-current.json"
            if not is_output and not linked.exists():
                issues.append({"source": path.name, "missing": str(linked)})
    json_paths = [p for p in sorted(EVIDENCE.glob("*.json")) if p.name != "global-review-validation-current.json"]
    for path in json_paths:
        read(path)
    python_paths = sorted(EVIDENCE.glob("*.py")) + [ROOT / "tests/test_v3_documentary_flow.py"]
    for path in python_paths:
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    integrity = {
        "scope": "Current documents and evidence integrity, not human acceptance or release gate",
        "checks": {"markdown": len(documents), "json": len(json_paths), "python": len(python_paths), "links": links},
        "issues": issues, "document_revisions": {"PROPOSAL.md": 6, "PLAN.md": 4},
        "document_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in documents},
        "candidate_validation_sha256": digest((EVIDENCE / "candidate-validation.json").read_bytes()),
        "prior_reports_preserved": True,
    }
    write(EVIDENCE / "global-review-validation-current.json", integrity)
    check((EVIDENCE / "global-review-validation-current.json").is_file(), "Missing integrity output")
    check(not issues, "Broken documentary links")
    print(json.dumps({"status": report["status"], "package_checks": "passed", "source_files": len(core),
                      "focal_unique_latest_passed": len(latest), "document_checks": integrity["checks"],
                      "official_release_gate": report["official_release_gate"]}, indent=2))


if __name__ == "__main__":
    main()
