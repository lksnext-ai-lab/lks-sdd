"""Bounded review probes against synthetic projects; no consumer or runtime edits.

This is review evidence, not a new release gate or an implementation of the proposal.
Run with Python -B from the repository root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path[:0] = [str(repo / "scripts"), str(repo / "tests")]

    from eval_support import authorize_implementation, materialize_ready_project
    from v2_authoring import edit_elements
    from v2_contract import ContractError, execution_context, load, make_element, render_block
    from v2_features import decomposition
    from v2_integration_guard import assess
    from v2_lifecycle import current_authorization, planning

    results = []

    def revise(root: Path, identifier: str, *, body=None, relations=None) -> None:
        model = load(root)
        element = model.elements[identifier]
        meta = dict(element.meta, revision=element.meta["revision"] + 1)
        if relations is not None:
            meta["relations"] = relations
        bodies = {identifier: body} if body is not None else None
        for relative, data in edit_elements(model, {identifier: meta}, bodies).items():
            (root / relative).write_bytes(data)

    def append(root: Path, element: dict) -> None:
        path = root / "docs/lks-sdd/04-delivery/fixture-task.md"
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write("\n" + render_block(element["meta"], element["body"]))

    def confirmed(identifier, kind, title, **values):
        return make_element(identifier, kind, title, title,
                            state="confirmed", nature="decision", **values)

    with tempfile.TemporaryDirectory(prefix="lks-sdd-review-") as directory:
        base = Path(directory)

        # P01: plan text changes while TASK/specification stay byte-equivalent.
        root = base / "plan-change"
        materialize_ready_project(root, "probe-plan-change")
        authorize_implementation(root)
        before = execution_context(load(root), ["TASK-001"])["fingerprint"]
        revise(root, "PLAN-001", body="The delivery now requires an independent rollback review before execution.")
        model = load(root)
        model.require_valid()
        authorization = current_authorization(model, ["TASK-001"], "test")
        results.append({
            "id": "P01", "scenario": "Normative PLAN revision changes",
            "planning": planning(model, ["TASK-001"])["status"],
            "context_fingerprint_unchanged": before == execution_context(model, ["TASK-001"])["fingerprint"],
            "authorization": authorization["status"],
            "interpretation": "PLAN prose/revision is absent from the current execution fingerprint.",
        })

        # P02: a confirmed feature obligation is discoverable in context but unplanned.
        root = base / "new-obligation"
        materialize_ready_project(root, "probe-new-obligation")
        authorize_implementation(root)
        append(root, confirmed("FR-002", "requirement", "Acknowledge a second documented request type",
                               relations={"acceptance": ["AC-002"]}))
        append(root, confirmed("AC-002", "acceptance", "The second request type receives acknowledgement",
                               relations={"requirements": ["FR-002"]}))
        revise(root, "FTR-001", relations={"requirements": ["FR-001", "FR-002"]})
        model = load(root)
        model.require_valid()
        assessment = planning(model, ["TASK-001"])
        try:
            current_authorization(model, ["TASK-001"], "test")
            stale_auth_blocked = False
        except ContractError:
            stale_auth_blocked = True
        results.append({
            "id": "P02", "scenario": "Feature gains FR-002 without PLAN/TASK assignment",
            "planning": assessment["status"], "full_plan": assessment["full_plan"],
            "decomposition": decomposition(model, "PLAN-001")["status"],
            "new_requirement_in_context": any(e["meta"]["id"] == "FR-002" for e in assessment["context"]["elements"]),
            "previous_authorization_blocked": stale_auth_blocked,
            "interpretation": "Existing authority becomes stale, but a new readiness assessment still calls the old plan complete.",
        })

        # P03: direct FR ownership masks a missing acceptance criterion in the task.
        root = base / "acceptance-gap"
        materialize_ready_project(root, "probe-acceptance-gap")
        append(root, confirmed("AC-002", "acceptance", "Malformed requests must be rejected",
                               relations={"requirements": ["FR-001"]}))
        revise(root, "FR-001", relations={"acceptance": ["AC-001", "AC-002"]})
        model = load(root)
        model.require_valid()
        assessment = planning(model, ["TASK-001"])
        results.append({
            "id": "P03", "scenario": "An explicit TASK requirement has an uncovered acceptance criterion",
            "planning": assessment["status"],
            "decomposition": decomposition(model, "PLAN-001")["status"],
            "requirement_acceptance": sorted(model.elements["FR-001"].targets("acceptance")),
            "task_acceptance": sorted(model.elements["TASK-001"].targets("acceptance")),
            "interpretation": "Requirement ownership alone does not prove assignment of every acceptance obligation.",
        })

        # P04: the existing integration guard intentionally checks structural scope.
        root = base / "trusted"
        materialize_ready_project(root, "probe-structural-guard")
        (root / "src").mkdir(exist_ok=True)
        (root / "src/ack.py").write_text("ACK = 'documented'\n", encoding="utf-8")
        candidate = base / "candidate"
        shutil.copytree(root, candidate)
        (candidate / "src/ack.py").write_text("ACK = 'different behavior'\n", encoding="utf-8")
        guard = assess(root, candidate, ["TASK-001"])
        model = load(candidate)
        results.append({
            "id": "P04", "scenario": "Direct code edit inside TASK paths, without AUTH or EXEC",
            "guard_status": guard["status"], "changed": guard["changed"],
            "authorization_count": len(model.by_kind("authorization")),
            "execution_count": len(model.by_kind("execution")),
            "interpretation": "The structural guard alone is not a SPEC/PLAN/AUTH/execution compliance gate.",
        })

        # P05: preserve a working protection rather than claiming all gates fail.
        root = base / "task-change"
        materialize_ready_project(root, "probe-task-change")
        authorize_implementation(root)
        revise(root, "TASK-001", body="The implementation must satisfy an additional documented behavior.")
        model = load(root)
        try:
            current_authorization(model, ["TASK-001"], "test")
            blocked = False
        except ContractError:
            blocked = True
        results.append({
            "id": "P05", "scenario": "Normative TASK revision changes",
            "previous_authorization_blocked": blocked,
            "interpretation": "The existing TASK/specification fingerprint protection must be preserved.",
        })

        # P06: method version is already a strict compatibility boundary.
        root = base / "method-boundary"
        materialize_ready_project(root, "probe-method-boundary")
        manifest_path = root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["execution_policy"] = "spec-plan-task-v1"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        optional_policy_status = planning(load(root), ["TASK-001"])["status"]
        manifest["method_version"] = "2.1.0"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        try:
            load(root).require_valid()
            unknown_method_rejected = False
        except ContractError:
            unknown_method_rejected = True
        results.append({
            "id": "P06", "scenario": "Optional policy marker versus unknown method version",
            "optional_policy_marker_planning": optional_policy_status,
            "schema_version": manifest["schema_version"],
            "unknown_method_version": manifest["method_version"],
            "unknown_method_rejected": unknown_method_rejected,
            "interpretation": "Method 2.1.0 can provide an explicit compatibility boundary while retaining schema 2.0; an optional marker alone is ignored.",
        })

    sources = ["scripts/v2_contract.py", "scripts/v2_lifecycle.py", "scripts/v2_features.py",
               "scripts/v2_integration_guard.py", "scripts/v2_authoring.py", "scripts/v2_schema.py",
               "schemas/project-2.0.schema.json", "tests/eval_support.py"]
    report = {
        "kind": "synthetic-critical-review", "observed_at": datetime.now(timezone.utc).isoformat(),
        "plugin_version": json.loads((repo / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"],
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "python": platform.python_version(),
        "source_sha256": {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in sources},
        "scope": "Temporary synthetic projects only; no consumer repository, host conversation, CI or release tested.",
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": len(results), "results": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
