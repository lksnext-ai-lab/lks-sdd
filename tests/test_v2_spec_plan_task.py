"""Regression cases for the 2.1 SPEC → PLAN/TASK execution boundary."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from eval_support import V2_CLI, authorize_implementation, materialize_ready_project, run_json, tree_digest
from dual_distribution import SKILLS, project_files
from v2_authoring import author, edit_elements
from v2_contract import ContractError, canonical, load, make_element, render_block, render_document
from v2_features import decomposition
from v2_integration_guard import assess_strict
from v2_lifecycle import current_authorization, planning, start
from v2_method_upgrade import diagnose, upgrade


def revise(root, identifier, *, body=None, relations=None):
    model = load(root)
    element = model.elements[identifier]
    meta = dict(element.meta, revision=element.meta["revision"] + 1)
    if relations is not None:
        meta["relations"] = relations
    for relative, data in edit_elements(model, {identifier: meta},
                                        {identifier: body} if body else None).items():
        (root / relative).write_bytes(data)


def append(root, element):
    path = root / "docs/lks-sdd/04-delivery/fixture-task.md"
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\n" + render_block(element["meta"], element["body"]))


class SpecPlanTaskTests(unittest.TestCase):
    def test_both_project_hosts_receive_the_method_policy(self):
        plugin_root = Path(__file__).resolve().parents[1]
        core_paths = [".codex-plugin/plugin.json", "distribution/dual.json",
                      "distribution/host-copilot.md", "docs/V2-SPEC-PLAN-TASK.md"]
        core_paths.extend(f"skills/lks-sdd-{suffix}/SKILL.md" for suffix in SKILLS)
        core = {name: (plugin_root / name).read_bytes() for name in core_paths}
        files = project_files(core, "unit", "stable")
        lock = json.loads(files[".lks-sdd/distribution-lock.json"])
        self.assertEqual(lock["method_version"], "2.1.0")
        self.assertIn("2.0.0", lock["readable_method_versions"])
        for path in ("AGENTS.md", ".github/copilot-instructions.md"):
            content = files[path].decode("utf-8")
            self.assertIn("PLAN/TASK", content)
            self.assertIn("SPEC", content)

    def test_change_assessment_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-change-query")
            before = tree_digest(root)
            code, report = run_json(V2_CLI, "change", root, "--id", "PCH-001")
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "documented")
            self.assertEqual(report["plans"][0]["status"], "covered")
            self.assertEqual(before, tree_digest(root))

    def test_closed_task_scope_requires_new_task_or_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-closed-task")
            model = load(root)
            task = model.elements["TASK-001"]
            for relative, data in edit_elements(model, {"TASK-001": dict(task.meta, state="done")}).items():
                (root / relative).write_bytes(data)
            model = load(root)
            task = model.elements["TASK-001"]
            changes = edit_elements(model, {"TASK-001": dict(task.meta, revision=task.meta["revision"] + 1)},
                                    {"TASK-001": task.body + " A new material outcome."})
            with self.assertRaisesRegex(ContractError, "closed TASK"):
                author(model, {"documents": [{"path": task.path,
                                               "text": changes[task.path].decode("utf-8")}]})

    def test_incremental_deferral_keeps_full_plan_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-incremental")
            append(root, make_element("FR-002", "requirement", "Later result", "Later result.",
                                      state="confirmed", nature="decision", relations={"acceptance": ["AC-002"]}))
            append(root, make_element("AC-002", "acceptance", "Later result accepted", "Later result appears.",
                                      state="confirmed", nature="decision", relations={"requirements": ["FR-002"]}))
            revise(root, "FTR-001", relations={"requirements": ["FR-001", "FR-002"]})
            model = load(root)
            plan = model.elements["PLAN-001"]
            plan_meta = dict(plan.meta, revision=plan.meta["revision"] + 1,
                             planning_policy="incremental-authorized")
            for relative, data in edit_elements(model, {"PLAN-001": plan_meta}).items():
                (root / relative).write_bytes(data)
            request = make_element("PCH-002", "change", "Later request", "Deliver later result in a later slice.",
                                   state="confirmed", nature="decision", category="implementation-request",
                                   source_summary="Synthetic deferred decision", relations={"affects": ["FTR-001"]},
                                   points=[{"key": "LATER", "summary": "Later result",
                                            "requirements": ["FR-002"], "acceptance": ["AC-002"],
                                            "tests": [], "plans": ["PLAN-001"], "tasks": [],
                                            "disposition": "deferred", "decision_reason": "Independent later slice"}])
            relative = "docs/lks-sdd/00-control/changes/later-request.md"
            (root / relative).write_bytes(render_document("change", "Later request", [request]))
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"].append({"id": "PCH-002", "path": relative})
            manifest_path.write_bytes(canonical(manifest) + b"\n")
            assessment = planning(load(root), ["TASK-001"])
            self.assertEqual(assessment["status"], "ready", assessment["blockers"])
            self.assertEqual(assessment["full_plan"][0]["status"], "partial")
            revise(root, "FR-001", relations={"acceptance": ["AC-001"],
                                              "depends_on": ["FR-002"]})
            blocked = planning(load(root), ["TASK-001"])
            self.assertEqual(blocked["status"], "blocked")
            self.assertIn("deferred", " ".join(blocked["blockers"]))

    def test_confirmed_future_requirement_in_another_plan_preserves_slice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-second-plan")
            before = planning(load(root), ["TASK-001"])["fingerprint"]
            records = [
                make_element("FR-002", "requirement", "Second result", "Second result.",
                             state="confirmed", nature="decision", relations={"acceptance": ["AC-002"]}),
                make_element("AC-002", "acceptance", "Second result accepted", "Second result appears.",
                             state="confirmed", nature="decision", relations={"requirements": ["FR-002"]}),
                make_element("TST-002", "test", "Second result regression", "Positive, negative and regression.",
                             state="confirmed", nature="decision", cases=["positive", "negative", "regression"]),
                make_element("PLAN-002", "plan", "Second result plan", "Independent delivery plan.",
                             state="confirmed", nature="decision", planning_policy="complete",
                             relations={"requirements": ["FR-002"]}),
                make_element("TASK-002", "task", "Implement second result", "Independent implementation.",
                             state="ready", nature="decision", owner="fixture-owner", risk="low",
                             change_types=["evolution"], paths=["src/**"], gates=["GATE-UNIT"],
                             evidence_scopes=["component"],
                             relations={"plan": ["PLAN-002"], "implements": ["FTR-001"],
                                        "requirements": ["FR-002"], "acceptance": ["AC-002"],
                                        "tests": ["TST-002"], "bindings": ["BIND-001"]}),
            ]
            for record in records:
                append(root, record)
            revise(root, "FTR-001", relations={"requirements": ["FR-001", "FR-002"]})
            request = make_element("PCH-002", "change", "Second result request", "Deliver a second result.",
                                   state="confirmed", nature="decision", category="implementation-request",
                                   source_summary="Second synthetic request", relations={"affects": ["FTR-001"]},
                                   points=[{"key": "SECOND", "summary": "Second result",
                                            "requirements": ["FR-002"], "acceptance": ["AC-002"],
                                            "tests": ["TST-002"], "plans": ["PLAN-002"],
                                            "tasks": ["TASK-002"], "disposition": "planned"}])
            relative = "docs/lks-sdd/00-control/changes/second-request.md"
            (root / relative).write_bytes(render_document("change", "Second request", [request]))
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"].append({"id": "PCH-002", "path": relative})
            manifest_path.write_bytes(canonical(manifest) + b"\n")
            assessment = planning(load(root), ["TASK-001"])
            self.assertEqual(assessment["status"], "ready", assessment["blockers"])
            self.assertEqual(before, assessment["fingerprint"])
            other = planning(load(root), ["TASK-002"])
            self.assertEqual(other["status"], "ready", other["blockers"])

    def test_future_draft_requirement_does_not_block_current_slice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-future-draft")
            before = planning(load(root), ["TASK-001"])["fingerprint"]
            append(root, make_element("FR-002", "requirement", "Future result", "Future proposal.",
                                      state="draft", nature="proposal"))
            revise(root, "FTR-001", relations={"requirements": ["FR-001", "FR-002"]})
            assessment = planning(load(root), ["TASK-001"])
            self.assertEqual(assessment["status"], "ready")
            self.assertEqual(before, assessment["fingerprint"])

    def test_independent_task_in_same_plan_preserves_slice_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-independent")
            before = planning(load(root), ["TASK-001"])["fingerprint"]
            model = load(root)
            task = model.elements["TASK-001"]
            sibling = dict(task.meta, id="TASK-002", uid=str(uuid.uuid4()),
                           revision=1, title="Independent contributor")
            append(root, {"meta": sibling, "body": "Independent contribution."})
            model = load(root)
            request = model.elements["PCH-001"]
            request_meta = dict(request.meta, revision=request.meta["revision"] + 1)
            request_meta["points"] = [dict(request_meta["points"][0], tasks=["TASK-001", "TASK-002"])]
            for relative, data in edit_elements(model, {"PCH-001": request_meta}).items():
                (root / relative).write_bytes(data)
            self.assertEqual(before, planning(load(root), ["TASK-001"])["fingerprint"])

    def test_plan_rule_change_stales_authorization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-plan-change")
            authorize_implementation(root)
            before = planning(load(root), ["TASK-001"])["fingerprint"]
            revise(root, "PLAN-001", body="Independent rollback review is required.")
            self.assertNotEqual(before, planning(load(root), ["TASK-001"])["fingerprint"])
            with self.assertRaisesRegex(ContractError, "stale"):
                current_authorization(load(root), ["TASK-001"], "test")

    def test_new_spec_requirement_needs_plan_and_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-new-requirement")
            append(root, make_element("FR-002", "requirement", "Second result", "A second result is required.",
                                      state="confirmed", nature="decision", relations={"acceptance": ["AC-002"]}))
            append(root, make_element("AC-002", "acceptance", "Second result accepted", "The second result appears.",
                                      state="confirmed", nature="decision", relations={"requirements": ["FR-002"]}))
            revise(root, "FTR-001", relations={"requirements": ["FR-001", "FR-002"]})
            model = load(root)
            self.assertEqual(planning(model, ["TASK-001"])["status"], "blocked")
            self.assertEqual(decomposition(model, "PLAN-001")["status"], "incomplete")
            self.assertIn("FR-002", " ".join(planning(model, ["TASK-001"])["blockers"]))

    def test_new_acceptance_needs_task_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-new-acceptance")
            append(root, make_element("AC-002", "acceptance", "Reject invalid", "Invalid input is rejected.",
                                      state="confirmed", nature="decision", relations={"requirements": ["FR-001"]}))
            revise(root, "FR-001", relations={"acceptance": ["AC-001", "AC-002"]})
            model = load(root)
            self.assertEqual(planning(model, ["TASK-001"])["status"], "blocked")
            self.assertIn("AC-002", " ".join(planning(model, ["TASK-001"])["blockers"]))

    def test_strict_guard_requires_approved_auth_and_exec(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base"
            approved = root / "approved"
            candidate = root / "candidate"
            materialize_ready_project(base, "spt-guard")
            (base / "src").mkdir()
            (base / "src/ack.py").write_text("ACK = 1\n", encoding="utf-8")
            shutil.copytree(base, approved)
            shutil.copytree(base, candidate)
            (candidate / "src/ack.py").write_text("ACK = 2\n", encoding="utf-8")
            result = assess_strict(base, approved, candidate, ["TASK-001"], "test")
            self.assertEqual(result["status"], "blocked")
            self.assertIn("AUTH", " ".join(result["blockers"]))
            authorize_implementation(approved)
            plan = start(load(approved), ["TASK-001"], "test", actor="fixture-owner",
                         at="2026-09-22T10:00:00+00:00")
            start(load(approved), ["TASK-001"], "test", actor="fixture-owner",
                  at="2026-09-22T10:00:00+00:00", authorized_hash=plan["preview_hash"])
            shutil.rmtree(candidate)
            shutil.copytree(approved, candidate)
            (candidate / "src/ack.py").write_text("ACK = 2\n", encoding="utf-8")
            result = assess_strict(base, approved, candidate, ["TASK-001"], "test")
            self.assertEqual(result["status"], "structurally-compliant", result["blockers"])

    def test_method_upgrade_is_explicit_and_preserves_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            materialize_ready_project(root, "spt-upgrade")
            path = root / ".lks-sdd/project.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["method_version"] = "2.0.0"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            before = (root / "docs/lks-sdd/04-delivery/fixture-task.md").read_bytes()
            self.assertEqual(diagnose(root)["status"], "upgrade-available")
            plan = upgrade(root)
            self.assertEqual(load(root).manifest["method_version"], "2.0.0")
            upgrade(root, plan["preview_hash"])
            self.assertEqual(load(root).manifest["method_version"], "2.1.0")
            self.assertEqual(before, (root / "docs/lks-sdd/04-delivery/fixture-task.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
