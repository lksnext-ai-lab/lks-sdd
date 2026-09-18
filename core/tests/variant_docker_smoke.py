"""Explicit Docker acceptance; never part of a read-only diagnostic or fast tier."""

from __future__ import annotations
import argparse
import json
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from variant_fixture import materialize
from project_variants import approval_preview, apply_approval
from variant_verification import verify
from variant_preparation import prepare
from work_task import _checkpoint
from validate_project import validate_project


def run() -> dict:
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="lks-variant-docker-") as folder:
        root = Path(folder).resolve()
        materialize(root, start_legacy=False)
        preview = approval_preview(
            root,
            "VAR-001",
            "ENV-001",
            "integration",
            actor="synthetic-owner",
            reason="Review synthetic variant and isolated observer for the API TASK",
            risks="Dependency compatibility outside selected tests remains a reservation",
            expires=(date.today() + timedelta(days=7)).isoformat(),
        )
        apply_approval(root, preview, preview["preview_hash"])
        initial = prepare(root, "VAR-001", stage="integration", actor="synthetic-owner")
        prepared = prepare(
            root,
            "VAR-001",
            stage="integration",
            actor="synthetic-owner",
            apply=True,
            preview_hash=initial["preview_hash"],
        )
        assert prepared["functional_files_written"] == [], prepared
        assert not (root / "pyproject.toml").exists(), (
            "Preparation copied the reference scaffold"
        )
        args = argparse.Namespace(
            actor="synthetic-owner",
            reason="Synthetic API implementation ready",
            completed="API and checks implemented",
            next_action="Verify selected API gates",
        )
        code, review = _checkpoint(root, "TASK-001", "in-review", args)
        assert code == 0, review
        first_started = time.monotonic()
        first = verify(
            root,
            "VAR-001",
            "ENV-001",
            "integration",
            execute=True,
            evidence_id="EVID-001",
        )
        first_seconds = time.monotonic() - first_started
        assert first["status"] == "verified-with-reservations", first
        repeat_started = time.monotonic()
        second = verify(
            root,
            "VAR-001",
            "ENV-001",
            "integration",
            execute=True,
            evidence_id="EVID-002",
        )
        repeat_seconds = time.monotonic() - repeat_started
        assert second["processes_executed"] == 0, second
        args.reason = "Close within approved scope with all TASK gates passed"
        code, closed = _checkpoint(root, "TASK-001", "completed", args)
        assert code == 0, closed
        report, manifest, _ = validate_project(root)
        assert report.valid, report.errors
        task = (
            manifest["task_summary"] if "task_summary" in manifest else closed["status"]
        )
        return {
            "status": "passed",
            "real_isolated_processes": first["processes_executed"],
            "repeat_processes": second["processes_executed"],
            "task": task,
            "task_checkpoint": closed["technical_reference"],
            "verification": first["status"],
            "delivery_readiness": first["delivery_readiness"],
            "project_valid": report.valid,
            "initial_verification_seconds": round(first_seconds, 3),
            "repeat_verification_seconds": round(repeat_seconds, 3),
            "approval_count": len(
                list(
                    (root / "docs/lks-sdd/02-design/technology-approvals").glob("*.md")
                )
            ),
            "seconds": round(time.monotonic() - started, 3),
        }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
