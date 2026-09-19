from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "tests"))

from eval_support import (  # noqa: E402
    IMPLEMENT_SCRIPT,
    authorize_implementation,
    materialize_ready_project,
    run_json,
)
from test_task_tracking_v14 import _configure, _manifest, _record  # noqa: E402


TRACKING_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_task_tracking.py"


def apply_preview(root: Path, command: str, *arguments: str) -> dict:
    _, preview = run_json(TRACKING_SCRIPT, command, str(root), *arguments)
    _, applied = run_json(
        TRACKING_SCRIPT,
        command,
        str(root),
        *arguments,
        "--apply",
        "--authorize",
        preview["mutation_hash"],
    )
    return applied


def prepare_started_project(root: Path, project_id: str = "jira-milestones") -> dict:
    materialize_ready_project(root, project_id)
    _configure(
        root,
        "jira-hybrid",
        decision="ADR-001",
        reporting_scope="milestone-reporting",
        coordination_gate="advisory",
    )
    from jira_reporting_engine import build_milestone_preview  # noqa: PLC0415
    from task_tracking_engine import build_projection_preview  # noqa: PLC0415

    projection = build_projection_preview(root, _manifest(root), ["TASK-001"])
    _record(
        root,
        projection,
        result="succeeded",
        external_id="10001",
        external_key="SYN-1",
    )
    authorize_implementation(root)
    _, preview = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--dry-run",
    )
    _, implementation = run_json(
        IMPLEMENT_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "--task",
        "TASK-001",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    assert implementation["execution_id"] == "EXEC-001"
    assert build_milestone_preview
    return implementation
