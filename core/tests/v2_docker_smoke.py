"""Explicit isolated v2 variant run, evidence reuse and governed closure; no host pilot claim."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import time

from v2_fixture import write
from test_v2_project_variants import materialize
from project_variants import approval_preview, apply_approval
from v2_contract import load
from v2_lifecycle import authorize, start, checkpoint
from v2_verification import verify, close, evidence


def run():
    begun = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="lks-v2-docker-") as directory:
        root = Path(directory)
        materialize(root)
        at = datetime.now(timezone.utc).isoformat()
        expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        args = dict(actor="synthetic-owner", role="synthetic-owner", environment="ENV-001", approved_at=at,
                    expires_at=expires, reason="Explicit isolated v2 acceptance test")
        auth = authorize(load(root), ["TASK-001"], **args)
        authorize(load(root), ["TASK-001"], **args, authorized_hash=auth["preview_hash"])
        for stage in ("development", "integration"):
            decision = approval_preview(root, "VAR-001", "ENV-001", stage, actor="synthetic-owner",
                reason="Reviewed bounded fixture and isolated observer", risks="Untested behavior remains unverified",
                expires=(date.today() + timedelta(days=7)).isoformat())
            apply_approval(root, decision, decision["preview_hash"])
        args = dict(actor="synthetic-developer", at=at)
        plan = start(load(root), ["TASK-001"], "ENV-001", **args)
        start(load(root), ["TASK-001"], "ENV-001", **args, authorized_hash=plan["preview_hash"])
        args = dict(state="in-review", actor="synthetic-developer", at=at, summary="Fixture ready", next_action="Run actual observer")
        plan = checkpoint(load(root), **args)
        checkpoint(load(root), **args, authorized_hash=plan["preview_hash"])
        first = verify(load(root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-001", execute=True, containers=True)
        assert first["status"] == "verified-with-reservations", first
        old = evidence(load(root), "EVID-001")
        second = verify(load(root), ["TASK-001"], "ENV-001", "integration", evidence_id="EVID-002", execute=True)
        assert second["processes_executed"] == 0, second
        new = evidence(load(root), "EVID-002")
        assert old["build_id"] == new["build_id"], "Cache reuse must retain the same observed build identity"
        assert [c["observed_at"] for c in old["checks"]] == [c["observed_at"] for c in new["checks"]]
        args = dict(actor="synthetic-owner", at=datetime.now(timezone.utc).isoformat())
        plan = close(load(root), ["TASK-001"], "EVID-002", **args)
        close(load(root), ["TASK-001"], "EVID-002", **args, authorized_hash=plan["preview_hash"])
        assert load(root).elements["TASK-001"].meta["state"] == "done"
        return {"status": "passed", "actual_observer_processes": first["processes_executed"],
                "reused_processes": second["processes_executed"], "seconds": time.monotonic() - begun,
                "evidence": new, "host_acceptance": "not-run", "delivery": "not-assessed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    try:
        result = run()
    except (ValueError, OSError, AssertionError) as exc:
        result = {"status": "failed", "error": str(exc), "host_acceptance": "not-run"}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
    print(output)
    raise SystemExit(0 if result["status"] == "passed" else 1)
