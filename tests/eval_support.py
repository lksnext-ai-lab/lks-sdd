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
MIGRATE_SCRIPT = PLUGIN_ROOT / "scripts" / "migrate_project.py"
PLANNING_SCRIPT = PLUGIN_ROOT / "scripts" / "manage_planning.py"
CLIENT_VIEW_SCRIPT = PLUGIN_ROOT / "scripts" / "render_client_view.py"
VALIDATE_SPEC_SCRIPT = PLUGIN_ROOT / "scripts" / "validate_spec.py"
VALIDATE_SCRIPT = PLUGIN_ROOT / "scripts" / "validate_project.py"
TASK_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-define"
    / "assets"
    / "templates"
    / "04-delivery"
    / "task-detail.md"
)


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def run_json(
    script: Path, *args: str, expected_codes: set[int] | None = None
) -> tuple[int, dict[str, Any]]:
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
        raise AssertionError(
            f"Non-JSON output from {script.name}: {process.stdout}"
        ) from exc
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


def materialize_ready_increment(root: Path, *, confirm_plan: bool = True) -> None:
    docs = root / "docs" / "lks-sdd"
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "phase": "readiness",
            "gate": "G2",
            "active_increment": "INC-001",
            "active_plan": "PLAN-001",
            "active_task": None,
            "active_tasks": [],
            "delivery_governance": {
                "state": "confirmed",
                "model": "continuous-evolution",
                "decision": "ADR-002",
                "source": "docs/lks-sdd/04-delivery/delivery-governance.md",
                "active_change": "CHG-001",
                "review_due": "2026-11-19",
            },
            "version_control": {
                "type": "none",
                "origin": "none",
                "branching_model": "not-applicable",
                "main_branch": None,
                "integration_branch": None,
                "decision": "ADR-002",
            },
        }
    )
    if manifest.get("schema_version") == "1.4":
        manifest["task_tracking"].update(
            {
                "state": "confirmed",
                "mode": "repository-only",
                "provider": None,
                "decision": "ADR-900",
                "site": None,
                "project_key": None,
                "issue_type": None,
                "sync_policy": "not-required",
                "write_policy": "local-only",
                "projection_fingerprint": None,
                "sync_status": "not-required",
                "last_sync_on": None,
            }
        )
    manifest["technology"] = {
        "preferred_stack_assessed": True,
        "selected_profile": "API-FASTAPI-STATELESS-OCI",
        "selection_decision": "ADR-001",
        "profile_bindings": [
            {
                "binding_id": "BIND-001",
                "unit_id": "UNIT-001",
                "unit_path": ".",
                "profile_id": "API-FASTAPI-STATELESS-OCI",
                "profile_scope": "deployable",
                "selection_decision": "ADR-001",
                "lock_path": ".lks-sdd/profiles/BIND-001.lock.json",
                "state": "confirmed",
            }
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if manifest.get("schema_version") == "1.4":
        tracking_path = docs / "04-delivery" / "task-tracking.md"
        _replace_row(
            tracking_path,
            "TRK-001",
            "| TRK-001 | confirmed | repository-only | none | not-applicable | not-applicable | not-applicable | not-required | local-only | ADR-900 | 2026-08-19 |",
        )

    open_points = docs / "00-control" / "open-points.md"
    lines = [
        line
        for line in open_points.read_text(encoding="utf-8").splitlines()
        if "OPEN-001" not in line
    ]
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
        "| ADR-001 | confirmed | Select API-FASTAPI-STATELESS-OCI for UNIT-001. | FR-001 | Limited to INC-001 and BIND-001 |",
    )
    _append_row(
        docs / "03-solution" / "solution-overview.md",
        "| ID | State | Decision",
        "| ADR-002 | confirmed | Use continuous evolution, SemVer, immutable promotion and automated recovery for the synthetic fixture; version control is not applicable. | FR-001 | Governs CHG-001, PLAN-001 and ENV-001 |",
    )
    _append_row(
        docs / "03-solution" / "solution-overview.md",
        "| ID | State | Decision",
        "| ADR-900 | confirmed | Select repository-only task tracking mode. |  | Governs TRK-001 and requires no external tracker |",
    )
    _append_row(
        docs / "04-delivery" / "increments.md",
        "| ID | State | In scope",
        "| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | FR-001 | AC-001 | ADR-001 | TEST-001 |",
    )
    for domain, reason in (
        ("data", "The fixture does not persist domain data."),
        ("identity", "The synthetic fixture has no accounts."),
        ("security", "No protected boundary is introduced by this fixture."),
        ("privacy", "No personal data is processed by this fixture."),
        ("integrations", "The fixture calls no external system."),
    ):
        _append_row(
            docs / "04-delivery" / "increments.md",
            "| Increment | Domain | Applicability",
            f"| INC-001 | {domain} | not-applicable | none | {reason} |",
        )
    _append_row(
        docs / "04-delivery" / "increments.md",
        "| Increment | Interface applicability",
        "| INC-001 | not-applicable: API-only synthetic increment | not-applicable: no human-facing interface | none | not-applicable: no visual change | The fixture exercises a service acknowledgement without screens or interactions. |",
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
    _append_row(
        docs / "05-quality" / "test-strategy.md",
        "| Test | Level or type",
        "| TEST-001 | API integration | INC-001 acknowledgement | AC-001 | ENV-001 | pending: executed during G3 |",
    )
    _append_row(
        docs / "03-solution" / "architecture.md",
        "| Unit | State | Component",
        "| UNIT-001 | confirmed | Stateless acknowledgement API | Accept and acknowledge synthetic requests | OCI service boundary | HTTP/OpenAPI | none: stateless | FR-001 | BIND-001 |",
    )
    governance = docs / "04-delivery" / "delivery-governance.md"
    _replace_row(
        governance,
        "CHG-001",
        "| CHG-001 | confirmed | 2026-08-19 | continuous-evolution | SemVer with independently releasable increments | not-applicable: fixture has no VCS | Promote the same immutable digest | Automated deployment to confirmed environments | Roll back artifact then forward-fix | ADR-002 | Quarterly or on product, risk or platform change |",
    )
    _append_row(
        governance,
        "| ID | State | Role",
        "| ENV-001 | confirmed | CI verification | 1 | UNIT-001 | automated gate plus human release authority | environment variables without secrets | synthetic and ephemeral | structured logs and health | discard environment and restore prior artifact |",
    )
    plans = docs / "04-delivery" / "plans.md"
    _replace_row(
        plans,
        "PLAN-001",
        "| PLAN-001 | active | Synthetic continuous delivery | continuous-evolution | 0.x | Deliver INC-001 with verifiable evidence | INC-001 | not-applicable: initial plan | fixture-owner | 2026-11-19 |",
    )
    _replace_row(
        plans,
        "REL-001",
        "| REL-001 | active | 0.1.0 | PLAN-001 | 2026-08-19 | continuous stream | ENV-001 | TASK-001 | pending | pending | pending: G3/G4 not executed |",
    )
    planning = docs / "04-delivery" / "planning-coverage.md"
    _replace_row(
        planning,
        "REL-001",
        "| REL-001 | release | proposed | Deliver INC-001 with verifiable evidence | INC-001 | complete-before-implementation | not-applicable: method default | TASK-001 | scope, contract or dependency change |",
    )
    _append_row(
        planning,
        "| Target | Increment | Contract items",
        "| REL-001 | INC-001 | FR-001, AC-001, ADR-001, TEST-001 | TASK-001 | not-applicable: single-task release | Implement and jointly verify the complete synthetic increment | All active items are owned by the only executable task |",
    )
    tasks = docs / "04-delivery" / "tasks.md"
    _append_row(
        tasks,
        "| ID | Plan | Title",
        "| TASK-001 | PLAN-001 | Implement synthetic acknowledgement | REL-001 | INC-001 | UNIT-001 | BIND-001 | ready | on-track | 0 | not-applicable: no prerequisite task | none | fixture-owner | ./tasks/TASK-001.md | 2026-08-19 |",
    )
    task_directory = docs / "04-delivery" / "tasks"
    task_directory.mkdir(parents=True, exist_ok=True)
    task_text = TASK_TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{TASK_ID}}": "TASK-001",
        "{{TASK_TITLE}}": "Implement synthetic acknowledgement",
        "{{PLAN_ID}}": "PLAN-001",
        "{{RELEASE_ID}}": "REL-001",
        "{{INCREMENT_ID}}": "INC-001",
        "{{UNIT_ID}}": "UNIT-001",
        "{{BINDING_ID}}": "BIND-001",
        "{{PROJECT_ID}}": manifest["project_id"],
        "{{BASELINE_ID}}": manifest["baseline_id"],
        "{{DATE}}": "2026-08-19",
    }
    for marker, value in replacements.items():
        task_text = task_text.replace(marker, value)
    task_text = task_text.replace(
        "| pending | pending | pending | pending | pending | pending | pending | not-applicable |",
        "| Implement the confirmed acknowledgement behavior | UNIT-001 API behavior and tests | Reporting and administration | FR-001 | AC-001 | CAP-API-CONTRACT, CAP-OCI-RUNTIME | GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD | not-applicable |",
    ).replace(
        "| pending | pending | pending | pending-assignment | pending | pending | pending | pending | pending |",
        "| TEST-001 | ADR-001, ADR-002 and fixture constraints | not-applicable: no known synthetic risk | fixture-owner | Code and TEST-001 complete | AC-001 passed with required gates | EVID-001 tied to revision and artifact | TASK-001 performs joint release integration | not-applicable: single-task release |",
    ).replace(
        "| pending | pending | pending | pending | pending | pending |",
        "| Acknowledgement behavior and tests | pending | AC-001 | TEST-001 | EVID-001 | Single release deliverable |",
    ).replace(
        "| backlog | unknown | 0 | pending-assignment | pending | pending | pending | pending | pending | 2026-08-19 |",
        "| ready | on-track | 0 | fixture-owner | pending | pending | pending | pending | ENV-001 | 2026-08-19 |",
    ).replace(
        "| incomplete | none | none | none | pending | pending | complete task definition |",
        "| executable | none | none | none | pending | pending | begin TASK-001 after authorization |",
    )
    (task_directory / "TASK-001.md").write_text(
        task_text, encoding="utf-8", newline="\n"
    )
    _append_row(
        docs / "06-operation" / "deployment.md",
        "| Environment | State | Role",
        "| ENV-001 | confirmed | CI verification | UNIT-001 | immutable OCI digest | environment variables without secrets | replace and smoke | restore previous digest | health and structured logs | FR-001 |",
    )

    if not confirm_plan:
        return

    confirm_planning(root)


def confirm_planning(root: Path, *, change_date: str = "2026-08-19") -> dict[str, Any]:
    """Persist the fixture's complete planning fingerprints after human review."""
    _, preview = run_json(
        PLANNING_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "confirm",
        "--date",
        change_date,
        "--actor-role",
        "fixture-authority",
        "--preview",
    )
    _, applied = run_json(
        PLANNING_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "confirm",
        "--date",
        change_date,
        "--actor-role",
        "fixture-authority",
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return applied


def confirm_planning_change(
    root: Path,
    *,
    change_id: str,
    affected_contract: str,
    affected_tasks: str,
    decision: str,
    reason: str,
    classification: str = "new-scope",
    change_date: str = "2026-08-20",
) -> dict[str, Any]:
    """Record an exact confirmed PCH before reconfirming a stale fixture plan."""
    code, planning = run_json(
        PLANNING_SCRIPT,
        str(root),
        "--increment",
        "INC-001",
        "assess",
        expected_codes={3},
    )
    if code != 3 or not planning["change_impact"]["requires_change_record"]:
        raise AssertionError("The fixture plan is not awaiting an exact PCH record.")
    previous = planning["stored_fingerprints"]["planning"]
    current = planning["planning_fingerprint"]
    if not previous or previous == current:
        raise AssertionError("The fixture PCH requires distinct planning fingerprints.")
    _append_row(
        root / "docs/lks-sdd/04-delivery/planning-coverage.md",
        "| ID | State | Classification",
        f"| {change_id} | confirmed | {classification} | {affected_contract} | "
        f"{affected_tasks} | {previous} | {current} | {decision} | {reason} |",
    )
    return confirm_planning(root, change_date=change_date)


def authorize_implementation(
    root: Path,
    *,
    task_ids: tuple[str, ...] = ("TASK-001",),
    authorization_id: str = "AUTH-001",
    decision: str = "ADR-002",
    change_date: str = "2026-08-19",
) -> dict[str, Any]:
    """Persist a human-role authorization for an already confirmed fixture plan."""
    common = [
        str(root),
        "--increment",
        "INC-001",
        "authorize",
        "--authorization-id",
        authorization_id,
    ]
    for task_id in task_ids:
        common.extend(["--task", task_id])
    common.extend(
        [
            "--date",
            change_date,
            "--actor-role",
            "fixture-authority",
            "--decision",
            decision,
            "--constraints",
            "Only the selected executable task definitions are authorized.",
        ]
    )
    _, preview = run_json(PLANNING_SCRIPT, *common, "--preview")
    _, applied = run_json(
        PLANNING_SCRIPT,
        *common,
        "--apply",
        "--authorize",
        "--preview-hash",
        preview["preview_hash"],
    )
    return applied


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
            len(created["created"]) == 23,
            resumed["would_change"] is False,
            validation["valid"] is True,
            ready["status"] == "ready-for-implementation-authorization",
            ready["implementation_authorized"] is False,
        ]
    )
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {"ready": ready["status"]},
    }


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
            result["status"] == "specification-blocked",
            bool(result["blockers"]),
            before == after,
            result["implementation_authorized"] is False,
        ]
    )
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {"blockers": result["blockers"]},
    }


def run_alternative_stack(root: Path) -> dict[str, Any]:
    fixture = load_fixture("alternative-stack.json")
    initialize(root, fixture["project_id"])
    materialize_ready_increment(root)
    docs = root / "docs" / "lks-sdd"
    proposal = fixture["proposal"]
    _append_row(
        docs / "03-solution" / "solution-overview.md",
        "| ID | State | Option",
        f"| {proposal['id']} | proposed | {proposal['title']} | {proposal['support_level']} | "
        f"{proposal['rationale']} | Requiere decisión explícita | Pila de referencia |",
    )
    _replace_row(
        docs / "04-delivery" / "increments.md",
        "INC-001",
        f"| INC-001 | confirmed | Submit and acknowledge one request | Reporting and administration | "
        f"FR-001 | AC-001 | {proposal['id']} | TEST-001 |",
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
        "profile_bindings": [
            {
                "binding_id": "BIND-001",
                "unit_id": "UNIT-001",
                "unit_path": ".",
                "profile_id": proposal["profile_id"],
                "profile_scope": "deployable",
                "selection_decision": proposal["id"],
                "lock_path": ".lks-sdd/profiles/BIND-001.lock.json",
                "state": "proposed",
            }
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    before = tree_digest(root)
    code, result = run_json(
        READINESS_SCRIPT,
        str(root),
        "--increment",
        fixture["increment"],
        expected_codes={3},
    )
    after_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    blocker = any(
        proposal["id"] in item and "proposed" in item for item in result["blockers"]
    )
    solution_text = (docs / "03-solution" / "solution-overview.md").read_text(
        encoding="utf-8"
    )
    passed = all(
        [
            code == 3,
            result["status"] == "specification-blocked",
            blocker,
            after_manifest["technology"]["selected_profile"] is None,
            after_manifest["technology"]["selection_decision"] is None,
            f"| {proposal['id']} | proposed |" in solution_text,
            before == tree_digest(root),
            result["implementation_authorized"] is False,
        ]
    )
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {"blockers": result["blockers"]},
    }


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
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {"options": result["options"]},
    }


def run_scoped_blocker(root: Path) -> dict[str, Any]:
    fixture = load_fixture("scoped-blocker.json")
    initialize(root, fixture["project_id"])
    materialize_ready_increment(root)
    _append_row(
        root / "docs" / "lks-sdd" / "04-delivery" / "increments.md",
        "| ID | State | In scope",
        f"| {fixture['other_increment']} | draft | Trabajo futuro independiente | {fixture['increment']} | "
        "pending: definición futura | pending: definición futura | pending: definición futura | pending: definición futura |",
    )
    _append_row(
        root / "docs" / "lks-sdd" / "00-control" / "open-points.md",
        "| ID | State | Question",
        f"| OPEN-002 | blocked | Falta una decisión de {fixture['other_increment']} | "
        f"No afecta a {fixture['increment']} | {fixture['other_increment']} | true |",
    )
    before = tree_digest(root)
    _, result = run_json(
        READINESS_SCRIPT, str(root), "--increment", fixture["increment"]
    )
    passed = all(
        [
            result["status"] == "ready-for-implementation-authorization",
            any("OPEN-002" in item for item in result["non_blocking_pending"]),
            not result["blockers"],
            result["implementation_authorized"] is False,
            before == tree_digest(root),
        ]
    )
    return {
        "id": fixture["id"],
        "passed": passed,
        "details": {
            "status": result["status"],
            "pending": result["non_blocking_pending"],
        },
    }
