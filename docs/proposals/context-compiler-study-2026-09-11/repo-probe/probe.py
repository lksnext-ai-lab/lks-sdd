"""Read-only probe of actual LKS-SDD engines; fixture copies live only beside this script.

Run: python -B -X utf8 docs/proposals/context-compiler-study-2026-09-11/repo-probe/probe.py
No implementation, installation, commits, runtime edits or network operations.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
TEMP = OUT / "temporary"
TEMP.mkdir(exist_ok=True)
tempfile.tempdir = str(TEMP)
os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMP=str(TEMP), TEMP=str(TEMP))
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

from contract_engine import build_project_model, document_fingerprint, resolve_active_increment
from planning_engine import assess_planning
from test_contract_engine import ProjectModelTests
from eval_support import materialize_ready_project, _append_row, _replace_row
from test_planning_continuity_v13 import _build_parallel_complete_plan, _add_calculator_scope


class StudyDirectory:
    """Retained ordinary directory: Python 3.14 mkdtemp ACLs fail in this sandbox.

    Applied only in this probe process. No deletion or permissions changes.
    Existing fixture helpers use this same tempfile module object.
    """
    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        base = Path(dir) if dir else TEMP
        assert base.resolve().is_relative_to(OUT)
        path = base / ((prefix or "study-") + uuid.uuid4().hex[:10] + (suffix or ""))
        path.mkdir(parents=True)
        self.name = str(path)

    def __enter__(self):
        return self.name

    def __exit__(self, *args):
        return False

    def cleanup(self):
        pass


tempfile.TemporaryDirectory = StudyDirectory


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def measure(text):
    return {"characters": len(text), "utf8_bytes": len(text.encode("utf-8"))}


def fingerprint(root):
    model = build_project_model(root)
    active = resolve_active_increment(model, "INC-001")
    return {"document": document_fingerprint(model), "active": active.fingerprint,
            "model_valid": model.valid, "model_errors": sorted({d.code for d in model.diagnostics if d.severity == "error"}),
            "active_errors": sorted({d.code for d in active.diagnostics if d.severity == "error"})}


def source_inventory():
    paths = []
    for directory in ("tests", "scripts", "skills", "schemas", "profiles"):
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.is_relative_to(ROOT / "tests" / "reports") and p.suffix in {".py", ".json", ".md", ".png"})
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def visual(root):
    ProjectModelTests()._active_project(root)


def shared(root):
    visual(root)
    replacements = {
        "04-delivery/increments.md": ("| INC-001 | confirmed | feature | none | FR-001 | AC-001 | ADR-001 | TEST-001 |", "| INC-002 | confirmed | other | none | FR-001 | AC-002 | ADR-002 | TEST-002 |"),
        "02-requirements/acceptance-criteria.md": ("| AC-001 | confirmed | Feature works | FR-001 | none |", "| AC-002 | confirmed | Other feature works | FR-001 | none |"),
        "03-solution/solution-overview.md": ("| ADR-001 | confirmed | Use the selected design | FR-001 | bounded |", "| ADR-002 | confirmed | Use another design | FR-001 | other |"),
        "05-quality/quality-strategy.md": ("| TEST-001 | planned | Verify behavior | INC-001 | AC-001 |", "| TEST-002 | planned | Verify other behavior | INC-002 | AC-002 |"),
        "05-quality/traceability.md": ("| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |", "| FR-001 | AC-002 | ADR-002 | INC-002 | TEST-002 | foreign |"),
    }
    for relative, (old, additional) in replacements.items():
        path = root / "docs/lks-sdd" / relative
        text = path.read_text(encoding="utf-8")
        assert text.count(old) == 1
        save(path, text.replace(old, old + "\n" + additional))


def ready(root):
    materialize_ready_project(root, "probe-ready", confirm_plan=False)


def partial(root):
    materialize_ready_project(root, "probe-partial", confirm_plan=False)
    _add_calculator_scope(root)


def multi(root):
    materialize_ready_project(root, "probe-multi", confirm_plan=False)
    docs = root / "docs/lks-sdd"
    manifest_path = root / ".lks-sdd/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["active_task"] = None
    manifest["technology"]["selected_profile"] = None
    manifest["technology"]["selection_decision"] = None
    manifest["technology"]["profile_bindings"].append({"binding_id": "BIND-002", "unit_id": "UNIT-002", "unit_path": "web", "profile_id": "WEB-REACT-VITE-STATIC", "profile_scope": "deployable", "selection_decision": "ADR-003", "lock_path": ".lks-sdd/profiles/BIND-002.lock.json", "state": "confirmed"})
    save(manifest_path, manifest)
    _append_row(docs / "03-solution/solution-overview.md", "| ID | State | Decision", "| ADR-003 | confirmed | Select WEB-REACT-VITE-STATIC for UNIT-002 and BIND-002. | FR-001 | Limited to the static web deployable |")
    _append_row(docs / "03-solution/architecture.md", "| Unit | State | Component", "| UNIT-002 | confirmed | Static React web | Present the synthetic acknowledgement | Static browser deployable | HTTP to UNIT-001 | none: client state only | FR-001 | BIND-002 |")
    _append_row(docs / "04-delivery/tasks.md", "| ID | Plan | Title", "| TASK-002 | PLAN-001 | Implement synthetic web | REL-001 | INC-001 | UNIT-002 | BIND-002 | ready | on-track | 0 | not-applicable: no prerequisite task | none | fixture-owner | ./tasks/TASK-002.md | 2026-08-19 |")
    _replace_row(docs / "04-delivery/plans.md", "REL-001", "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001, TASK-002 | pending | pending | pending: G3/G4 not executed |")
    path = docs / "04-delivery/planning-coverage.md"
    save(path, path.read_text(encoding="utf-8").replace("| TASK-001 | not-applicable: single-task release | Implement and jointly verify the complete synthetic increment | All active items are owned by the only executable task |", "| TASK-001 | TASK-002 | Coordinate the API ownership with the web contribution | TASK-001 keeps primary ownership and TASK-002 provides the bound frontend contribution |"))
    text = (docs / "04-delivery/tasks/TASK-001.md").read_text(encoding="utf-8")
    for old, new in (("TASK-001", "TASK-002"), ("UNIT-001", "UNIT-002"), ("BIND-001", "BIND-002"), ("CAP-API-CONTRACT, CAP-OCI-RUNTIME", "CAP-FRONTEND-QUALITY, CAP-STATIC-BUNDLE"), ("GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD", "GATE-FRONTEND-TEST, GATE-FRONTEND-BUILD, GATE-BROWSER-SMOKE"), ("Implement synthetic acknowledgement", "Implement synthetic web")):
        text = text.replace(old, new)
    save(docs / "04-delivery/tasks/TASK-002.md", text)


def projection(rows):
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[(row.path, row.table_id)].append(row)
    parts = []
    for (path, table_id), items in sorted(grouped.items()):
        parts.extend([f"{path}#{table_id}", " | ".join(items[0].cells)])
        parts.extend(" | ".join(row.cells.values()) for row in sorted(items, key=lambda r: r.line))
    return "\n".join(parts) + "\n"


def outside_table_stats(text):
    lines = text.splitlines(keepends=True)
    front = False
    outside = []
    narrative = []
    for index, line in enumerate(lines):
        if index == 0 and line.strip() == "---":
            front = True
            continue
        if front:
            if line.strip() == "---": front = False
            continue
        if not line.lstrip().startswith("|"):
            outside.append(line)
            if line.strip() and not line.lstrip().startswith("#"):
                narrative.append(line)
    return {"non_table_body": measure("".join(outside)), "non_table_non_heading_nonblank": measure("".join(narrative))}


def inspect_case(root, name):
    model = build_project_model(root)
    active = resolve_active_increment(model, "INC-001")
    dest = OUT / "corpora" / name
    files = sorted({row["path"] for row in model.manifest.get("artifacts", []) if isinstance(row, dict) and isinstance(row.get("path"), str) and row["path"].endswith(".md") and (root / row["path"]).is_file()})
    texts = {relative: (root / relative).read_text(encoding="utf-8") for relative in files}
    concatenated = "\n".join(f"SOURCE {path}\n{text}" for path, text in texts.items())
    active_projection = projection(active.rows)
    save(dest / "indexed-documents.txt", concatenated)
    save(dest / "active-rows.txt", active_projection)
    save(dest / "all-model-rows.txt", projection(model.rows.values()))
    manifest = model.manifest
    try:
        planning = assess_planning(root, manifest, "INC-001")
        planning_result = {key: planning.get(key) for key in ("status", "integrity", "coverage", "tasks", "dependency_graph", "gaps", "integrity_errors", "specification_fingerprint", "planning_fingerprint")}
    except Exception as exc:
        planning_result = {"exception": f"{type(exc).__name__}: {exc}"}
    save(dest / "planning.json", planning_result)
    by_task = planning_result.get("coverage", {}).get("by_task", {}) if isinstance(planning_result.get("coverage"), dict) else {}
    task_metrics = {}
    for task, ids in by_task.items():
        # Deliberately only seeds, not a sufficient-context claim or closure.
        rows = [row for row in active.rows if row.key in set(ids) | {task} or row.artifact_id == "ART-" + task]
        payload = projection(rows)
        save(dest / f"{task}-seeds-only.txt", payload)
        task_metrics[task] = {"assigned_item_ids": ids, "rows": len(rows), "text": measure(payload), "sufficient_context": "not-assessed-seeds-only"}
    fr = model.nodes.get("FR-001")
    mutations = []
    if fr:
        path = root / fr.path
        original = path.read_bytes()
        baseline = fingerprint(root)
        additions = [
            ("normative_prose_outside_table", original.decode("utf-8") + "\n## Regla vinculante adicional para FR-001\nSolo un usuario autorizado puede ejecutar FR-001; una denegacion debe dejar los datos intactos.\n"),
            ("active_statement_cell", original.decode("utf-8").replace(fr.cells.get("Statement", ""), fr.cells.get("Statement", "") + " Solo un usuario autorizado puede ejecutarlo.", 1)),
        ]
        for mutation, changed_text in additions:
            save(path, changed_text)
            observed = fingerprint(root)
            mutations.append({"kind": mutation, "path": fr.path, "baseline": baseline, "observed": observed, "document_changed": observed["document"] != baseline["document"], "active_changed": observed["active"] != baseline["active"]})
            path.write_bytes(original)
        assert fingerprint(root) == baseline
    if active.assets:
        baseline = fingerprint(root)
        for owner in ("VIS-001", "VIS-003"):
            candidates = [asset for asset in model.assets if asset.owner_id == owner]
            if candidates:
                asset = candidates[0]
                path = root / asset.path
                original = path.read_bytes()
                path.write_bytes(original + b" probe-change")
                observed = fingerprint(root)
                mutations.append({"kind": "asset_bytes_" + owner, "path": asset.path, "baseline": baseline, "observed": observed, "document_changed": observed["document"] != baseline["document"], "active_changed": observed["active"] != baseline["active"]})
                path.write_bytes(original)
        assert fingerprint(root) == baseline
    save(dest / "mutations.json", mutations)
    return {"name": name, "indexed_md_files": len(files), "all_md_files": len(list(root.rglob("*.md"))), "indexed_source_text_without_labels": measure("".join(texts.values())), "indexed_corpus_with_labels": measure(concatenated), "outside_table_stats_per_file": {p: outside_table_stats(t) for p, t in texts.items()}, "model_rows": len(model.rows), "model_nodes": len(model.nodes), "active_rows": len(active.rows), "active_node_ids": list(active.node_ids), "active_projection": measure(active_projection), "tasks": task_metrics, "bindings": manifest.get("technology", {}).get("profile_bindings", []), "all_assets": [{"owner": a.owner_id, "state": a.state_class, "path": a.path} for a in model.assets], "active_assets": [a.owner_id for a in active.assets], "baseline": fingerprint(root), "planning_status": planning_result.get("status"), "planning_integrity": planning_result.get("integrity"), "mutation_observations": mutations, "corpus_directory": dest.relative_to(OUT).as_posix()}


def main():
    before = source_inventory()
    cases = [("visual_history", visual), ("shared_increment", shared), ("ready_single_task", ready), ("parallel_three_tasks", _build_parallel_complete_plan), ("calculator_partial", partial), ("two_profile_bindings", multi)]
    results = []
    for name, builder in cases:
        print(f"probe {name}", file=sys.stderr, flush=True)
        with tempfile.TemporaryDirectory(prefix=name + "-", dir=TEMP) as temporary:
            root = Path(temporary)
            try:
                builder(root)
                results.append(inspect_case(root, name))
            except Exception as exc:
                results.append({"name": name, "blocked": f"{type(exc).__name__}: {exc}"})
    after = source_inventory()
    changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
    result = {"script": "probe.py", "measurement": "Unicode characters and UTF-8 bytes; no token estimate", "classification": "synthetic-engine-study; not release or semantic acceptance", "case_count": len(results), "source_integrity": {"files_hashed": len(before), "changed_paths": changed}, "cases": results}
    save(OUT / "results.json", result)
    save(OUT / "source-hashes.json", before)
    print(json.dumps({"cases": [{"name": c["name"], "blocked": c.get("blocked"), "model_valid": c.get("baseline", {}).get("model_valid"), "rows": c.get("model_rows"), "active_rows": c.get("active_rows"), "planning": c.get("planning_status")} for c in results], "source_changes": changed}, ensure_ascii=False, indent=2))
    return 0 if all("blocked" not in c for c in results) and not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
