"""Shared fixture for callers that need a local, tracker-free v2 task scope."""

from __future__ import annotations

from pathlib import Path

from eval_support import (
    V2_CLI,
    authorize_implementation,
    materialize_ready_project,
    run_json,
)


def apply_preview(root: Path, command: str, *arguments: str) -> dict:
    """Apply an explicitly preview-bound v2 command without tracker assumptions."""
    _, preview = run_json(V2_CLI, command, str(root), *arguments)
    if not preview.get("preview_hash"):
        return preview
    _, applied = run_json(
        V2_CLI,
        command,
        str(root),
        *arguments,
        "--apply",
        "--authorize",
        preview["preview_hash"],
    )
    return applied


def prepare_started_project(
    root: Path, project_id: str = "local-task-scope"
) -> dict:
    """Materialize and authorize a generic local task; no Jira projection is created."""
    materialize_ready_project(root, project_id)
    authorization = authorize_implementation(root)
    _, status = run_json(
        V2_CLI,
        "status",
        str(root),
        "--task",
        "TASK-001",
        "--environment",
        "test",
    )
    return {"authorization": authorization, "status": status}
