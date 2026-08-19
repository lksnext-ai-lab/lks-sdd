"""Reusable deterministic fixture execution for tests and the eval harness."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = PLUGIN_ROOT / "tests" / "fixtures"
INIT_SCRIPT = PLUGIN_ROOT / "skills" / "lks-sdd-define" / "scripts" / "init_project.py"
READINESS_SCRIPT = PLUGIN_ROOT / "skills" / "lks-sdd-assess-readiness" / "scripts" / "assess_readiness.py"
HELP_SCRIPT = PLUGIN_ROOT / "skills" / "lks-sdd-help" / "scripts" / "context_help.py"
VALIDATE_SCRIPT = PLUGIN_ROOT / "scripts" / "validate_project.py"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def run_json(script: Path, *args: str, expected_codes: set[int] | None = None) -> tuple[int, dict[str, Any]]:
    process = subprocess.run(
        [sys.executable, "-X", "utf8", str(script), *map(str, args), "--json"],
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
            f"Unexpected exit {process.returncode} for {script.name}:\nstdout={process.stdout}\nstderr={process.stderr}"
        )
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Non-JSON output from {script.name}: {process.stdout}") from exc
    return process.returncode, payload


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def initialize(root: Path, project_id: str, dry_run: bool = False) -> dict[str, Any]:
    args = [str(root), "--project-id", project_id, "--date", "2026-08-19"]
    if dry_run:
        args.append("--dry-run")
    _, payload = run_json(INIT_SCRIPT, *args)
    return payload


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
    docs = root / "docs" / "lks-sdd"
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({"phase": "readiness", "gate": "G2", "active_increment": "INC-001", "open_blockers": []})
    manifest["technology"] = {
        "preferred_stack_assessed": True,
        "selected_profile": "STACK-REFERENCE",
        "selection_decision": "ADR-001",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    open_points = docs / "00-control" / "open-points.md"
    lines = [line for line in open_points.read_text(encoding="utf-8").splitlines() if "OPEN-001" not in line]
    open_points.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    _append_row(
        docs / "02-requirements" / "functional-requirements.md",
        "| ID | State | Statement",
        "| FR-001 | confirmed | A user can submit one synthetic request. | user-confirmed | must | AC-001 | INC-001 |",
    )
    _append_row(
        docs / "02-requirements" / "acceptance-criteria.md",
        "| ID | State | Condition",
        "| AC-001 | confirmed | Given valid synthetic data, the request is acknowledged. | FR-001 | none |",
    )
    _append_row(
        docs / "03-solution" / "solution-overview.md",
        "| ID | State | Decision",
        "| ADR-001 | decision | Select STACK-REFERENCE with a reversible web boundary derived from requirements. | FR-001 | Limited to INC-001 |",
    )
    _append_row(
        docs / "04-delivery" / "increments.md",
        "| ID | State | In scope",
        "| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | not-applicable: no persisted domain data | not-applicable: synthetic fixture has no accounts | not-applicable: no external systems | TEST-001 |",
    )
    _append_row(
        docs / "05-quality" / "quality-strategy.md",
        "| ID | State | Purpose",
        "| TEST-001 | planned | Verify acknowledgement for valid synthetic data | INC-001 | AC-001 |",
    )
    _append_row(
        docs / "05-quality" / "traceability.md",
        "| Requirement | Acceptance",
        "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
    )


def run_new_project(root: Path) -> dict[str, Any]:
    fixture = load_fixture("new-project.json")
    before = tree_digest(root)
    dry_run = initialize(root, fixture["project_id"], dry_run=True)
    after_dry_run = tree_digest(root)
    created = initialize(root, fixture["project_id"])
    _, validation = run_json(VALIDATE_SCRIPT, str(root))
    resumed = initialize(root, fixture["project_id"])
    materialize_ready_increment(root)
    _, ready = run_json(READINESS_SCRIPT, str(root), "--increment", "INC-001")
    passed = all(
        [
            before == after_dry_run,
            dry_run["changed"] is False,
            len(created["created"]) == 15,
            resumed["would_change"] is False,
            validation["valid"] is True,
            ready["status"] == "ready",
            ready["implementation_authorized"] is False,
        ]
    )
    return {"id": fixture["id"], "passed": passed, "details": {"ready": ready["status"]}}


def run_insufficient_information(root: Path) -> dict[str, Any]:
    fixture = load_fixture("insufficient-information.json")
    initialize(root, fixture["project_id"])
    before = tree_digest(root)
    code, result = run_json(
        READINESS_SCRIPT,
        str(root),
        "--increment",
        fixture["increment"],
        expected_codes={3},
    )
    after = tree_digest(root)
    passed = all(
        [
            code == 3,
            result["status"] == "blocked",
            bool(result["blockers"]),
            before == after,
            result["implementation_authorized"] is False,
        ]
    )
    return {"id": fixture["id"], "passed": passed, "details": {"blockers": result["blockers"]}}


def run_alternative_stack(root: Path) -> dict[str, Any]:
    fixture = load_fixture("alternative-stack.json")
    initialize(root, fixture["project_id"])
    materialize_ready_increment(root)
    docs = root / "docs" / "lks-sdd"
    proposal = fixture["proposal"]
    _append_row(
        docs / "03-solution" / "solution-overview.md",
        "| ID | State | Option",
        f"| {proposal['id']} | proposal | {proposal['title']} | {proposal['support_level']} | "
        f"{proposal['rationale']} | Requiere decisión explícita | Pila de referencia |",
    )
    _replace_row(
        docs / "04-delivery" / "increments.md",
        "INC-001",
        f"| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | "
        f"FR-001 | AC-001 | {proposal['id']} | not-applicable: no persisted domain data | "
        "not-applicable: synthetic fixture has no accounts | not-applicable: no external systems | TEST-001 |",
    )
    _replace_row(
        docs / "05-quality" / "traceability.md",
        "FR-001",
        f"| FR-001 | AC-001 | {proposal['id']} | INC-001 | TEST-001 | none |",
    )
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["technology"] = {
        "preferred_stack_assessed": True,
        "selected_profile": None,
        "selection_decision": None,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    before = tree_digest(root)
    code, result = run_json(
        READINESS_SCRIPT,
        str(root),
        "--increment",
        fixture["increment"],
        expected_codes={3},
    )
    after_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blocker = any(proposal["id"] in item and "proposal" in item for item in result["blockers"])
    solution_text = (docs / "03-solution" / "solution-overview.md").read_text(encoding="utf-8")
    passed = all(
        [
            code == 3,
            result["status"] == "blocked",
            blocker,
            after_manifest["technology"]["selected_profile"] is None,
            after_manifest["technology"]["selection_decision"] is None,
            f"| {proposal['id']} | proposal |" in solution_text,
            before == tree_digest(root),
            result["implementation_authorized"] is False,
        ]
    )
    return {"id": fixture["id"], "passed": passed, "details": {"blockers": result["blockers"]}}


def run_help(root: Path) -> dict[str, Any]:
    fixture = load_fixture("help.json")
    initialize(root, fixture["project_id"])
    before = tree_digest(root)
    _, result = run_json(HELP_SCRIPT, str(root))
    after = tree_digest(root)
    passed = all(
        [
            result["status"] == "context-available",
            result["project_id"] == fixture["project_id"],
            result["action_started"] is False,
            bool(result["resolved"]),
            bool(result["missing_or_limits"]),
            bool(result["options"]),
            all(option["starts_action"] is False for option in result["options"]),
            bool(result["choice_prompt"]),
            before == after,
        ]
    )
    return {"id": fixture["id"], "passed": passed, "details": {"options": result["options"]}}


def run_scoped_blocker(root: Path) -> dict[str, Any]:
    fixture = load_fixture("scoped-blocker.json")
    initialize(root, fixture["project_id"])
    materialize_ready_increment(root)
    _append_row(
        root / "docs" / "lks-sdd" / "04-delivery" / "increments.md",
        "| ID | State | In scope",
        f"| {fixture['other_increment']} | open | Trabajo futuro independiente | {fixture['increment']} | "
        "not-applicable | not-applicable | not-applicable | not-applicable: pending definition | "
        "not-applicable: pending definition | not-applicable: pending definition | not-applicable |",
    )
    _append_row(
        root / "docs" / "lks-sdd" / "00-control" / "open-points.md",
        "| ID | State | Question",
        f"| OPEN-002 | blocked | Falta una decisión de {fixture['other_increment']} | "
        f"No afecta a {fixture['increment']} | {fixture['other_increment']} | true |",
    )
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["open_blockers"] = ["OPEN-002"]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    before = tree_digest(root)
    _, result = run_json(READINESS_SCRIPT, str(root), "--increment", fixture["increment"])
    passed = all(
        [
            result["status"] == "ready-with-non-blocking-pending",
            any("OPEN-002" in item for item in result["non_blocking_pending"]),
            not result["blockers"],
            result["implementation_authorized"] is False,
            before == tree_digest(root),
        ]
    )
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {"status": result["status"], "pending": result["non_blocking_pending"]},
    }
