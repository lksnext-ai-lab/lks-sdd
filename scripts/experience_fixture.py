#!/usr/bin/env python3
"""Create the generic representative 0.15.0 experience/benchmark fixture."""

from __future__ import annotations

import json
from pathlib import Path


def create_representative_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".lks-sdd").mkdir()
    docs = root / "docs/lks-sdd"
    tasks_dir = docs / "04-delivery/tasks"
    tasks_dir.mkdir(parents=True)
    (docs / "04-delivery/checkpoints").mkdir()
    (docs / "05-quality").mkdir()
    rows: list[str] = []
    states = ["in-review", "blocked", "done", "ready", "backlog"]
    for number in range(1, 14):
        task_id = f"TASK-{number:03d}"
        state = states[number - 1] if number <= len(states) else "backlog"
        rows.append(
            f"| {task_id} | PLAN-001 | Capability {number} | REL-001 | INC-001 | UNIT-{((number - 1) % 3) + 1:03d} | BIND-{((number - 1) % 3) + 1:03d} | {state} | "
            f"{'blocked' if state == 'blocked' else 'on-track'} | {100 if state == 'done' else 70 if state == 'in-review' else 0} | "
            f"{'not-applicable: first task' if number == 1 else f'TASK-{number-1:03d}'} | "
            f"{'PROB-001' if state == 'blocked' else 'none'} | fixture-owner | ./tasks/{task_id}.md | 2026-08-28 |"
        )
        issues = ""
        if number == 1:
            issues = (
                "| PROB-001 | active | Evidence recorder cannot persist the result | Verification cannot close | tool-owner | Fix recorder | pending |\n"
                "| PROB-002 | resolved | Historical parser defect | none | tool-owner | fixed | EVID-900 |\n"
                "| PROB-003 | active | Production promotion decision | production only | release-owner | decide before production | pending |\n"
            )
        detail = f"""---
artifact_id: ART-{task_id}
artifact_type: development-task
schema_version: \"1.5\"
method_version: \"1.5.0\"
created_with_plugin_version: \"0.15.0\"
project_id: representative-fixture
baseline_id: BL-0001
status: confirmed
---

# {task_id} · Capability {number}

| Objective | In scope | Out of scope | Requirements | Acceptance | Required capabilities | Technical gates | Dependencies |
|---|---|---|---|---|---|---|---|
| Deliver capability {number} | Generic local behavior | production | TR-{number:03d} | AC-{number:03d} | CAP-API-CONTRACT | GATE-API-TEST | not-applicable |

| Tests | Decisions and constraints | Risks and blockers | Responsible role | Review entry conditions | Definition of done | Required evidence | Integration points | Parallel constraints |
|---|---|---|---|---|---|---|---|---|
| TEST-{number:03d} | ADR-001 | none | fixture-owner | code complete | tests and evidence | EVID-{number:03d} | none | none |

| Deliverable | State | Acceptance | Tests | Evidence | Notes |
|---|---|---|---|---|---|
| Generic capability {number} | {'done' if state == 'done' else 'in-progress'} | AC-{number:03d} | TEST-{number:03d} | {'EVID-003' if state == 'done' else 'pending'} | generic |

| Workflow state | Health | Progress | Owner | Branch | Revision start | Revision verified | Build | Environment | Updated |
|---|---|---|---|---|---|---|---|---|---|
| {state} | on-track | 70 | fixture-owner | main | pending | pending | pending | local | 2026-08-28 |

| ID | State | Description | Impact | Owner | Resolution condition | Evidence |
|---|---|---|---|---|---|---|
{issues}
| Acceptance | Gate | Result | Evidence | Revision | Artifact digest | Environment |
|---|---|---|---|---|---|---|
| AC-{number:03d} | GATE-API-TEST | {'passed' if number == 1 else 'pending'} | {'EVID-001' if number == 1 else 'pending'} | pending | pending | local |

| Date | From | To | Reason | Actor or authority | Evidence |
|---|---|---|---|---|---|
| 2026-08-28 | ready | {state} | Synthetic fixture transition | fixture-owner | pending |
"""
        (tasks_dir / f"{task_id}.md").write_text(detail, encoding="utf-8", newline="\n")
    board = """---
artifact_id: ART-TASKS
artifact_type: development-task-board
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.15.0"
project_id: representative-fixture
baseline_id: BL-0001
status: confirmed
---

| ID | Plan | Title | Release | Increment | Unit | Profile binding | Workflow state | Health | Progress | Dependencies | Blockers | Owner | Detail | Updated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n"
    (docs / "04-delivery/tasks.md").write_text(board, encoding="utf-8", newline="\n")
    for number, state in ((1, "implementation-started"), (2, "blocked"), (3, "review-complete")):
        checkpoint = f"""---
artifact_id: ART-CKPT-{number:03d}
artifact_type: checkpoint
schema_version: "1.5"
method_version: "1.5.0"
created_with_plugin_version: "0.15.0"
project_id: representative-fixture
baseline_id: BL-0001
status: confirmed
---

# CKPT-{number:03d}

Synthetic {state} checkpoint for the representative repository fixture.
"""
        (docs / "04-delivery/checkpoints" / f"CKPT-{number:03d}.md").write_text(
            checkpoint, encoding="utf-8", newline="\n"
        )
    relations = [
        f"| RELROW-{number:03d} | TR-{((number - 1) % 13) + 1:03d} | TASK-{((number - 1) % 13) + 1:03d} |"
        for number in range(1, 421)
    ]
    planning = "| Row | Contract | Task |\n|---|---|---|\n" + "\n".join(relations) + "\n"
    (docs / "04-delivery/planning-coverage.md").write_text(planning, encoding="utf-8", newline="\n")
    trace = "| Requirement | Acceptance | Decision | Increment | Test | Evidence |\n|---|---|---|---|---|---|\n| TR-001..TR-014 | AC-001 | ADR-001 | INC-001 | TEST-001 | pending |\n"
    (docs / "05-quality/traceability.md").write_text(trace, encoding="utf-8", newline="\n")
    fingerprint = "a" * 64
    manifest = {
        "project_id": "representative-fixture",
        "route": "new",
        "method_version": "1.5.0",
        "schema_version": "1.5",
        "plugin_version": "0.15.0",
        "phase": "implementation",
        "gate": "G3",
        "active_increment": "INC-001",
        "active_plan": "PLAN-001",
        "active_task": "TASK-001",
        "active_tasks": ["TASK-001"],
        "artifacts": [
            {"id": "ART-TASKS", "path": "docs/lks-sdd/04-delivery/tasks.md", "required": True},
            {"id": "ART-TRACE", "path": "docs/lks-sdd/05-quality/traceability.md", "required": True},
        ],
        "technology": {
            "selected_profile": None,
            "selection_decision": None,
            "profile_bindings": [
                {"binding_id": "BIND-001", "unit_id": "UNIT-001", "unit_path": "web", "profile_id": "WEB-REACT-VITE-STATIC", "profile_scope": "deployable", "selection_decision": "ADR-001", "lock_path": ".lks-sdd/profiles/BIND-001.lock.json", "state": "confirmed"},
                {"binding_id": "BIND-002", "unit_id": "UNIT-002", "unit_path": "api", "profile_id": "API-FASTAPI-STATELESS-OCI", "profile_scope": "deployable", "selection_decision": "ADR-001", "lock_path": ".lks-sdd/profiles/BIND-002.lock.json", "state": "confirmed"},
                {"binding_id": "BIND-003", "unit_id": "UNIT-003", "unit_path": "worker", "profile_id": "MSG-PYTHON-RABBITMQ-WORKER-OCI", "profile_scope": "deployable", "selection_decision": "ADR-001", "lock_path": ".lks-sdd/profiles/BIND-003.lock.json", "state": "confirmed"},
            ],
        },
        "planning": {"target_id": "REL-001", "specification_fingerprint": fingerprint, "planning_fingerprint": "b" * 64},
        "authorizations": [{
            "authorization_id": "AUTH-001", "state": "authorized", "target": "REL-001",
            "increment": "INC-001", "release": "REL-001", "task_ids": ["TASK-001"],
            "specification_fingerprint": fingerprint, "planning_fingerprint": "b" * 64,
            "authorized_by_role": "fixture-owner", "authorized_on": "2026-08-28",
            "decision": "ADR-001", "constraints": "local-only",
        }],
        "executions": [{
            "execution_id": "EXEC-001", "status": "in-review", "increment": "INC-001",
            "release": "REL-001", "task_ids": ["TASK-001"], "profile_bindings": [],
            "locks": [], "branch": "main", "revision_start": "c" * 40,
            "last_observed_revision": "c" * 40, "authorization_id": "AUTH-001",
            "specification_fingerprint": fingerprint, "planning_fingerprint": "b" * 64,
            "latest_checkpoint": "docs/lks-sdd/04-delivery/checkpoints/CKPT-001.md",
            "changed_paths": ["src/app.py", "tests/test_app.py"], "evidence_ids": [],
        }],
        "verification": {
            "verification_id": "VER-001", "status": "blocked", "task_ids": ["TASK-001"],
            "evidence_ids": ["EVID-001"], "completed_on": None,
        },
        "task_tracking": {"mode": "jira-hybrid", "reporting_scope": "milestone-reporting", "coordination_gate": "advisory", "sync_status": "in-sync"},
    }
    (root / ".lks-sdd/project.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    for relative, content in {
        "src/app.py": "def capability(): return 1\n",
        "tests/test_app.py": "def test_capability(): assert True\n",
        "migrations/001.sql": "select 1;\n",
        "config/runtime.json": "{}\n",
        "Dockerfile": "FROM scratch\n",
        "package-lock.json": "{}\n",
        ".lks-sdd/profiles/BIND-001.lock.json": "{}\n",
        ".lks-sdd/profiles/BIND-002.lock.json": "{}\n",
        ".lks-sdd/profiles/BIND-003.lock.json": "{}\n",
        "docs/lks-sdd/evidence/EVID-001.json": json.dumps({"evidence_id": "EVID-001", "status": "current", "checks": [{"name": "unit", "status": "passed", "command": "python -m unittest"}]}, indent=2) + "\n",
        "docs/lks-sdd/evidence/EVID-900.json": json.dumps({"evidence_id": "EVID-900", "status": "historical", "checks": [{"name": "legacy", "status": "passed", "command": "historical-only"}]}, indent=2) + "\n",
    }.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return root
