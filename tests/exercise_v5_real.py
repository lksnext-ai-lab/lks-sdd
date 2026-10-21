"""Controlled SAT snapshot migration. Never run against the active consumer.

The case-specific dispositions are reviewable migration inputs, not production
runtime special cases. Historical evidence remains historical; obsolete method
wrappers are retired and the existing CI route is converted to the v5 validator.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v5_core as core
import v5_migration as migration
import v5_distribution as distribution
from v5_legacy import Reader, paths

SNAPSHOT = "e55f87a122aa6e3595d8a26d2bb729dd867cad26"


def prepare_dispositions(root):
    tracked = migration.git(root, "ls-files", "-z", binary=True).decode().split("\0")
    dispositions = {}
    for name in tracked:
        path = root / name
        if not name or name.startswith(("docs/lks-sdd/", ".lks-sdd/", ".github/skills/")) or not path.is_file():
            continue
        if path.stat().st_size > 4 * 1024 * 1024:
            continue
        raw = path.read_bytes()
        try: text = raw.decode("utf-8")
        except UnicodeError: continue
        if "docs/lks-sdd" not in text and ".lks-sdd/runtime" not in text:
            continue
        if name.startswith(("output/", "backend/verification/", "functional-test-cases/evidence/", "docs/design/", "docs/runtime-owner-fix/")) or name == "docs/release-0.14.0-delivery.json":
            action = "retire" if name == "output/ci-permanent/run_sdd_cached.py" else "historical"
            dispositions[name] = {"action": action, "sha256": core.digest(raw),
                "reason": "Snapshot evidence of a prior execution, not an active runtime dependency" if action == "historical" else
                          "Obsolete temporary method wrapper; runtime cache it invokes is retired"}
    validator = '''"""Validate the pinned v5 capability/task contract in CI."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / '.lks-sdd/distribution-lock.json').read_bytes())
runtime = (root / lock['runtime']).resolve()
if not runtime.is_relative_to(root / '.lks-sdd/runtime'):
    raise SystemExit('Invalid pinned runtime path')
cli = runtime / 'scripts/lks_sdd.py'
for command in ('doctor', 'validate'):
    subprocess.run([sys.executable, '-B', str(cli), command, '--root', str(root)], check=True)
'''
    for name, action, text, reason in (
        ("scripts/validate-lks-sdd-identities.py", "replace", validator,
         "CI validates current v5 integrity and document relations; no legacy method dependency remains"),
        ("scripts/test_lks_sdd_validation.py", "retire", None,
         "Tests exercise the retired identity-alias mechanism, not application behavior")):
        dispositions[name] = {"action": action, "sha256": core.digest((root / name).read_bytes()), "reason": reason}
        if text: dispositions[name]["text"] = text
    name = ".gitlab-ci.yml"
    raw = (root / name).read_bytes()
    text = raw.decode().replace('      python -m pip install --disable-pip-version-check -r "$task_runtime/requirements-runtime.txt"',
        '      python -B "$task_runtime/scripts/lks_sdd.py" doctor --root .')
    text = text.replace('    - python -B -m unittest discover -s scripts -p "test_lks_sdd_validation.py"\n', '')
    dispositions[name] = {"action": "replace", "sha256": core.digest(raw), "text": text,
        "reason": "v5 runtime is stdlib-only; keep the existing CI job and validate its current contract"}
    return dispositions


def run(root, report):
    root = root.resolve()
    allowed = (ROOT / "tests/reports/v5-full").resolve()
    if not root.is_relative_to(allowed) or migration.git(root, "rev-parse", "HEAD") != SNAPSHOT:
        raise ValueError("This experiment only accepts its controlled, exact snapshot clone")
    started = time.perf_counter()
    reader = Reader(root)
    ux_source = next(e for e in reader.elements.values() if e.kind == 'task' and e.id == 'TASK-UX-THEME-2026-001')
    ux_expected = {f'C{i}': value for i, value in enumerate(ux_source.data['acceptance'], 1)}
    source_docs = [name for name in reader.inventory if name.endswith('.md')]
    before = {"files": len(source_docs), "bytes": sum(core.path_at(root, name).stat().st_size for name in source_docs),
              "active_files": len(reader.document_hashes),
              "active_bytes": sum(core.path_at(root, name).stat().st_size for name in reader.document_hashes)}
    dispositions = prepare_dispositions(root)
    preview = migration.preview(root, dispositions=dispositions)
    prepared = time.perf_counter()
    result = migration.run(root, preview["preview_sha256"])
    applied = time.perf_counter()
    integrity = distribution.doctor(root)
    ci = subprocess.run([sys.executable, "-B", "scripts/validate-lks-sdd-identities.py"], cwd=root,
                        capture_output=True, text=True, timeout=120)
    if ci.returncode:
        raise ValueError("Converted CI validation failed: " + ci.stdout + ci.stderr)
    if (root / "docs/lks-sdd").exists():
        raise ValueError("Legacy document tree remains")
    if paths(root, migration.WORK) or core.read(root, migration.JOURNAL):
        raise ValueError("Migration staging was not removed")
    if not core.read(root, migration.REPORT):
        raise ValueError('Conversion report missing')
    lock = json.loads((root / ".lks-sdd/distribution-lock.json").read_bytes())
    runtimes = list((root / ".lks-sdd/runtime").iterdir())
    if len(runtimes) != 1 or runtimes[0] != root / lock["runtime"]:
        raise ValueError("An old runtime remains operational")
    timings = []
    for _ in range(30):
        start = time.perf_counter()
        context = core.context(root, "task-ux-theme-2026-001")
        timings.append(time.perf_counter() - start)
    docs = paths(root, 'docs/sdd')
    after = {"files": len(docs), "bytes": sum(core.path_at(root, name).stat().st_size for name in docs)}
    ux_task = core.current(root, core.task_path('task-ux-theme-2026-001', 'tarea'))[0]
    from collections import Counter
    plans = [core.parse(core.read(root, name))[0] for name in docs if name.endswith('/plan.md')]
    states = dict(Counter(plan['state'] for plan in plans))
    if (len(plans) != 76 or states.get('cerrado') != 43 or
            [plan['id'] for plan in plans if plan.get('blockers')] != ['task-012'] or
            core.unit_path('antecedentes') in context['documents']):
        raise ValueError('Migration introduced administrative work or unrelated historical context')
    if (not all(ux_task['criteria'].get(k) == v for k, v in ux_expected.items()) or
            'sonar' not in core.project_policy(root).get('required_checks', [])):
        raise ValueError('Converted UX criteria or mandatory quality policy missing')
    result = {"source_commit": SNAPSHOT, "copy": str(root), "preview": preview, "conversion": result,
        "integrity": integrity, "converted_ci_validator": "passed", "legacy_runtime": "absent",
        "conversion_report": migration.REPORT,
        "task_states": states, "task_plan_pairs": len(plans),
        "seconds": {"prepare_including_mapping": prepared - started, "apply": applied - prepared},
        "documentation": {"before": before, "after": after, "migration_backups": 0, "migration_staging_files": 0,
                          "ux_criteria": len(ux_task['criteria']), "literal_ux_criteria_preserved": len(ux_expected),
                          "linked_acceptance_criteria": len(ux_task['criteria']) - len(ux_expected),
                          "mandatory_controls": core.project_policy(root)},
        "context": {"task": "task-ux-theme-2026-001", "n": 30, "median": statistics.median(timings),
                    "p95_observed": sorted(timings)[28], "files": context["files_read"], "bytes": context["bytes"]},
        "consumer_acceptance": "not-run: controlled clone only", "app_regression": "not-run: migration does not change application behavior",
        "billed_tokens": None}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(core.encode(result), encoding="utf-8")
    print(core.encode(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=ROOT / "tests/reports/v5-full/real-results.json")
    args = parser.parse_args()
    run(args.root, args.report)
