"""Small, deterministic helpers shared by the remaining v2 unit tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
V2_CLI = SCRIPTS_ROOT / "v2_cli.py"
INIT_SCRIPT = PLUGIN_ROOT / "skills" / "lks-sdd-define" / "scripts" / "init_project.py"
READINESS_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-assess-readiness"
    / "scripts"
    / "assess_readiness.py"
)
HELP_SCRIPT = PLUGIN_ROOT / "skills" / "lks-sdd-help" / "scripts" / "context_help.py"
IMPLEMENT_SCRIPT = (
    PLUGIN_ROOT / "skills" / "lks-sdd-implement" / "scripts" / "prepare_increment.py"
)
VERIFY_SCRIPT = (
    PLUGIN_ROOT / "skills" / "lks-sdd-verify" / "scripts" / "run_verification.py"
)
INSPECT_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-adopt-existing"
    / "scripts"
    / "inspect_repository.py"
)
VALIDATE_ADOPTION_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-adopt-existing"
    / "scripts"
    / "validate_adoption.py"
)
MATERIALIZE_ADOPTION_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-adopt-existing"
    / "scripts"
    / "materialize_adoption.py"
)
PLANNING_SCRIPT = SCRIPTS_ROOT / "manage_planning.py"
CLIENT_VIEW_SCRIPT = SCRIPTS_ROOT / "render_client_view.py"
VALIDATE_SPEC_SCRIPT = SCRIPTS_ROOT / "validate_spec.py"
VALIDATE_SCRIPT = SCRIPTS_ROOT / "validate_project.py"
TASK_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-define"
    / "assets"
    / "templates"
    / "04-delivery"
    / "task-detail.md"
)

if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


def run_json(
    script: Path, *args: str, expected_codes: set[int] | None = None
) -> tuple[int, dict[str, Any]]:
    """Run a JSON command and fail with its complete diagnostics on an unexpected exit."""
    command = [sys.executable, "-B", "-X", "utf8", str(script), *map(str, args)]
    if "--json" not in command:
        command.append("--json")
    process = subprocess.run(
        command,
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    allowed = expected_codes or {0}
    if process.returncode not in allowed:
        raise AssertionError(
            f"Unexpected exit {process.returncode} for {script.name}:\n"
            f"stdout={process.stdout}\nstderr={process.stderr}"
        )
    try:
        return process.returncode, json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Non-JSON output from {script.name}: {process.stdout}"
        ) from exc


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _apply(root: Path, changes: dict[str, bytes | None], preview: dict[str, Any]) -> dict:
    from v2_contract import load
    from v2_storage import apply

    return apply(
        root,
        changes,
        preview,
        preview["preview_hash"],
        validator=lambda: load(root).require_valid(),
    )


def initialize(root: Path, project_id: str, dry_run: bool = False) -> dict[str, Any]:
    """Initialize a v2 project with its mandatory local technology declaration."""
    from v2_authoring import initialize as initialize_v2

    preview, changes = initialize_v2(root, project_id, project_id=project_id)
    if dry_run:
        return {**preview, "changed": False}
    result = _apply(root, changes, preview)
    return {**preview, **result, "project_root": str(root.resolve())}


def _append_row(path: Path, header_prefix: str, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines[:-1]):
        if line.startswith(header_prefix) and lines[index + 1].startswith("|---"):
            lines.insert(index + 2, row)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            return
    raise AssertionError(f"Table not found in {path}: {header_prefix}")


def _replace_row(path: Path, row_id: str, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = f"| {row_id} |"
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = row
            path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            return
    raise AssertionError(f"Row not found in {path}: {row_id}")


def materialize_ready_increment(root: Path) -> None:
    """Add a complete synthetic v2 task slice using generic local bindings only."""
    from v2_authoring import edit_elements
    from v2_contract import DOCS, canonical, load, make_element, render_document
    from v2_lifecycle import planning
    from v2_storage import preview

    model = load(root)
    replacements = {}
    for applicability in model.by_kind("applicability"):
        value = dict(applicability.meta)
        value.update(
            state="confirmed",
            nature="decision",
            applicability="not-applicable",
            reason="The synthetic unit fixture does not exercise this domain.",
            revision=value["revision"] + 1,
        )
        replacements[applicability.id] = value

    technology = model.elements["TECH-001"]
    technology_value = dict(technology.meta)
    technology_value["technology"] = dict(
        technology_value["technology"],
        state="confirmed",
        value="Synthetic documented technology",
    )
    technology_value.update(state="confirmed", nature="decision", revision=technology_value["revision"] + 1)
    replacements[technology.id] = technology_value

    fixture_path = DOCS + "/04-delivery/fixture-task.md"
    records = [
        make_element(
            "FTR-001",
            "feature",
            "Synthetic acknowledgement",
            "A bounded acknowledgement capability for lifecycle tests.",
            state="confirmed",
            nature="decision",
        ),
        make_element(
            "FR-001",
            "requirement",
            "Acknowledge a request",
            "The fixture acknowledges a valid synthetic request.",
            state="confirmed",
            nature="decision",
            relations={"acceptance": ["AC-001"]},
        ),
        make_element(
            "AC-001",
            "acceptance",
            "Acknowledgement is returned",
            "A valid request receives the documented acknowledgement.",
            state="confirmed",
            nature="decision",
            relations={"requirements": ["FR-001"]},
        ),
        make_element(
            "TST-001",
            "test",
            "Acknowledgement coverage",
            "Positive, negative and regression coverage are declared explicitly.",
            state="confirmed",
            nature="decision",
            cases=["positive", "negative", "regression"],
        ),
        make_element(
            "BIND-001",
            "binding",
            "Synthetic local binding",
            "A generic local relation for the bounded fixture.",
            state="confirmed",
            nature="decision",
            unit_id="UNIT-001",
            unit_path="src",
        ),
        make_element(
            "PLAN-001",
            "plan",
            "Synthetic delivery plan",
            "One complete task delivers the scoped requirement.",
            state="confirmed",
            nature="decision",
            planning_policy="complete",
            relations={"requirements": ["FR-001"]},
        ),
        make_element(
            "ADR-001",
            "decision",
            "Fixture delivery governance",
            "The fixture records delivery governance without selecting a global technology preset.",
            state="confirmed",
            nature="decision",
            category="delivery-governance",
            delivery_model="continuous",
            versioning="semantic",
            branching="trunk",
            ci="required",
            recovery="rollback",
            review_policy="peer-review",
            tracking="repository-only",
        ),
        make_element(
            "TASK-001",
            "task",
            "Implement acknowledgement",
            "Implement the bounded synthetic acknowledgement behavior.",
            state="ready",
            nature="decision",
            owner="fixture-owner",
            risk="low",
            change_types=["evolution"],
            paths=["src/**"],
            gates=["GATE-UNIT"],
            evidence_scopes=["component"],
            relations={
                "plan": ["PLAN-001"],
                "implements": ["FTR-001"],
                "requirements": ["FR-001"],
                "acceptance": ["AC-001"],
                "tests": ["TST-001"],
                "bindings": ["BIND-001"],
            },
        ),
    ]

    changes = edit_elements(model, replacements)
    changes[fixture_path] = render_document("fixture-task", "Synthetic task fixture", records)
    index = dict(model.manifest)
    index["artifacts"] = [
        *model.manifest["artifacts"],
        {"id": "TASK-001", "path": fixture_path},
    ]
    changes[".lks-sdd/project.json"] = canonical(index) + b"\n"
    plan = preview(root, changes, sources=model.hashes, operation="materialize-test-task")
    _apply(root, changes, plan)
    assessment = planning(load(root), ["TASK-001"])
    if assessment["status"] != "ready":
        raise AssertionError(f"Synthetic fixture is not ready: {assessment['blockers']}")


def materialize_ready_project(root: Path, project_id: str) -> None:
    """Create a complete project fixture with a generic binding and local declaration."""
    initialize(root, project_id)
    materialize_ready_increment(root)


def update_technology_declaration(
    root: Path, *, value: str, state: str = "confirmed"
) -> None:
    """Apply a local technology-declaration change through the v2 contract."""
    from v2_authoring import edit_elements
    from v2_contract import load
    from v2_storage import preview

    model = load(root)
    declaration = model.elements["TECH-001"]
    technology = dict(declaration.meta["technology"])
    technology["state"] = state
    if state == "unknown":
        technology.pop("value", None)
    else:
        technology["value"] = value
    replacement = dict(
        declaration.meta,
        state=state,
        nature="unknown" if state == "unknown" else "decision",
        revision=declaration.meta["revision"] + 1,
        technology=technology,
    )
    changes = edit_elements(model, {declaration.id: replacement})
    plan = preview(
        root,
        changes,
        sources=model.hashes,
        operation="update-test-technology-declaration",
    )
    _apply(root, changes, plan)


def authorize_implementation(
    root: Path,
    *,
    task_ids: tuple[str, ...] = ("TASK-001",),
    environment: str = "test",
) -> dict[str, Any]:
    """Persist a preview-bound v2 authorization for the selected synthetic tasks."""
    from v2_contract import load
    from v2_lifecycle import authorize

    model = load(root)
    preview = authorize(
        model,
        list(task_ids),
        actor="fixture-authority",
        role="test-authority",
        environment=environment,
        approved_at="2026-01-01T00:00:00+00:00",
        expires_at="2030-01-01T00:00:00+00:00",
        reason="Authorize the bounded synthetic fixture.",
    )
    return authorize(
        load(root),
        list(task_ids),
        actor="fixture-authority",
        role="test-authority",
        environment=environment,
        approved_at="2026-01-01T00:00:00+00:00",
        expires_at="2030-01-01T00:00:00+00:00",
        reason="Authorize the bounded synthetic fixture.",
        authorized_hash=preview["preview_hash"],
    )
