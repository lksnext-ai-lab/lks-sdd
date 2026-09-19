"""Synthetic regression coverage for v2 inventories, task context and observers."""
from __future__ import annotations

import copy
import tempfile
import unittest
import uuid
from pathlib import Path

from eval_support import authorize_implementation, materialize_ready_project
from v2_authoring import edit_elements
from v2_contract import ContractError, DOCS, execution_context, load, render_document, sha
from v2_lifecycle import checkpoint, start, work_inventory
from v2_quality import obligations
from v2_storage import apply, preview
from v2_verification import close, evidence, verification_plan, verify


GATES = ("GATE-ALPHA", "GATE-BETA", "GATE-GAMMA")
PINNED_IMAGE = "registry.invalid/lks-observer@sha256:" + "a" * 64


def _apply(root: Path, changes: dict[str, bytes], operation: str) -> None:
    model = load(root)
    plan = preview(root, changes, sources=model.hashes, operation=operation)
    apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())


def _add_sibling(root: Path) -> None:
    model = load(root)
    source = model.elements["TASK-001"]
    sibling = dict(source.meta)
    sibling.update(
        id="TASK-002",
        uid=str(uuid.uuid4()),
        revision=1,
        state="ready",
        title="Independent synthetic sibling",
        gates=["GATE-UNRELATED"],
        evidence_scopes=["visual"],
        relations={relation: list(targets) for relation, targets in source.relations.items()},
    )
    path = DOCS + "/04-delivery/synthetic-sibling.md"
    _apply(
        root,
        {path: render_document("fixture-task", "Synthetic sibling", [{"meta": sibling, "body": source.body}])},
        "add-synthetic-sibling",
    )


def _add_release_relation(root: Path) -> None:
    model = load(root)
    task = model.elements["TASK-001"]
    task_value = dict(task.meta)
    task_value["revision"] += 1
    task_value["relations"] = {
        **{relation: list(targets) for relation, targets in task.relations.items()},
        "release": ["REL-001"],
    }
    release = {
        "id": "REL-001",
        "uid": str(uuid.uuid4()),
        "kind": "release",
        "title": "Synthetic administrative release",
        "revision": 1,
        "state": "confirmed",
        "nature": "decision",
        "relations": {"implements": ["TASK-001", "TASK-002"]},
    }
    _apply(
        root,
        {
            DOCS + "/04-delivery/synthetic-release.md": render_document(
                "fixture-release",
                "Synthetic administrative release",
                [{"meta": release, "body": "Administrative traceability only."}],
            ),
            **edit_elements(model, {"TASK-001": task_value}),
        },
        "add-synthetic-release-relation",
    )


def _configure_observers(
    root: Path,
    *,
    omitted_gate: str | None = None,
    invalid_hash_gate: str | None = None,
    missing_input_gate: str | None = None,
    out_of_scope_gate: str | None = None,
    invalid_command_gate: str | None = None,
    risk: str = "low",
) -> None:
    inputs = {}
    for gate in GATES:
        relative = "src/" + gate.lower() + "-observer.py"
        if gate != missing_input_gate:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("print('synthetic observer')\n", encoding="utf-8")
            inputs[gate] = sha(path.read_bytes())
        else:
            inputs[gate] = "b" * 64

    model = load(root)
    task = model.elements["TASK-001"]
    task_value = dict(task.meta)
    task_value.update(gates=list(GATES), evidence_scopes=["component"], risk=risk, revision=task.meta["revision"] + 1)

    observers = []
    for number, gate in enumerate(GATES, start=1):
        if gate == omitted_gate:
            continue
        relative = "src/" + gate.lower() + "-observer.py"
        observers.append(
            {
                "id": f"OBS-{number:03}",
                "gate_id": gate,
                "source": "approved-consumer",
                "image": PINNED_IMAGE,
                "command": ["python3", "\x00invalid"] if gate == invalid_command_gate else ["python3", relative],
                "inputs": [{"path": relative, "sha256": "0" * 64 if gate == invalid_hash_gate else inputs[gate]}],
                "timeout_seconds": 30,
                "requires_containers": True,
                "scopes": ["visual"] if gate == out_of_scope_gate else ["component"],
                "interfaces": [],
            }
        )
    declaration = model.elements["TECH-001"]
    technology = copy.deepcopy(declaration.meta["technology"])
    technology["variants"] = [
        {
            "id": "VAR-001",
            "state": "approved",
            "scope": ["TASK-001"],
            "environments": ["test"],
            "stages": ["development"],
            "observers": observers,
        }
    ]
    declaration_value = dict(
        declaration.meta,
        revision=declaration.meta["revision"] + 1,
        technology=technology,
    )
    _apply(
        root,
        edit_elements(model, {"TASK-001": task_value, "TECH-001": declaration_value}),
        "configure-approved-synthetic-observers",
    )


def _start_review(root: Path) -> None:
    authorize_implementation(root)
    started = start(
        load(root),
        ["TASK-001"],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
    )
    start(
        load(root),
        ["TASK-001"],
        "test",
        actor="fixture-owner",
        at="2026-09-19T10:00:00+00:00",
        authorized_hash=started["preview_hash"],
    )
    handoff = checkpoint(
        load(root),
        tasks=["TASK-001"],
        state="in-review",
        actor="fixture-owner",
        at="2026-09-19T10:01:00+00:00",
        summary="Synthetic implementation handoff.",
        next_action="Run approved synthetic observers.",
    )
    checkpoint(
        load(root),
        tasks=["TASK-001"],
        state="in-review",
        actor="fixture-owner",
        at="2026-09-19T10:01:00+00:00",
        summary="Synthetic implementation handoff.",
        next_action="Run approved synthetic observers.",
        authorized_hash=handoff["preview_hash"],
    )


def _passing_runner(executed: list[str]):
    def runner(_root: Path, entry: dict):
        executed.append(entry["gate_id"])
        artifact = ("evidence:" + entry["gate_id"]).encode()
        digest = sha(artifact)
        return {
            "gate_id": entry["gate_id"],
            "status": "passed",
            "scopes": entry["gate"]["scopes"],
            "interfaces": entry["gate"]["interfaces"],
            "observations": {"synthetic": True},
            "artifacts": [{"path": entry["gate_id"] + ".txt", "sha256": digest}],
        }, {digest: artifact}
    return runner


class V2InventoryPolicyTests(unittest.TestCase):
    def test_root_git_metadata_is_excluded_without_weakening_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-inventory-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "inventory-file")
            (root / ".git").write_text("gitdir: /synthetic/worktree/.git/worktrees/example\n", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "ordinary.py").write_text("value = 1\n", encoding="utf-8")
            (root / ".gitignore").write_text("cache/\n", encoding="utf-8")
            hashes = work_inventory(root)

            self.assertIn("src/ordinary.py", hashes)
            self.assertIn(".gitignore", hashes)
            self.assertNotIn(".git", hashes)

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-inventory-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "inventory-directory")
            (root / ".git").mkdir()
            (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

            self.assertNotIn(".git/HEAD", work_inventory(root))

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-inventory-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "inventory-nested")
            nested = root / "module"
            nested.mkdir()
            (nested / ".git").mkdir()

            with self.assertRaisesRegex(ContractError, "Nested repository"):
                work_inventory(root)


class V2TaskContextTests(unittest.TestCase):
    def test_single_task_excludes_sibling_gates_but_retains_global_obligations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-context-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "single-task-context")
            _add_sibling(root)

            context = execution_context(load(root), ["TASK-001"])
            selected = {item["meta"]["id"] for item in context["elements"]}
            quality = obligations(load(root), ["TASK-001"])

            self.assertIn("TASK-001", selected)
            self.assertNotIn("TASK-002", selected)
            self.assertIn("APP-001", selected)
            self.assertNotIn("GATE-UNRELATED", quality["gates"])

    def test_direct_dependency_is_normative_without_expanding_siblings(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-context-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "dependency-context")
            _add_sibling(root)
            model = load(root)
            task = model.elements["TASK-001"]
            replacement = dict(task.meta, revision=task.meta["revision"] + 1)
            replacement["relations"] = {
                **{relation: list(targets) for relation, targets in task.relations.items()},
                "depends_on": ["TASK-002"],
            }
            _apply(root, edit_elements(model, {"TASK-001": replacement}), "add-direct-dependency")

            context = execution_context(load(root), ["TASK-001"])
            dependent = next(item for item in context["elements"] if item["meta"]["id"] == "TASK-002")

            self.assertIn("direct-normative-dependency:TASK-001", dependent["included_because"])
            self.assertNotIn("GATE-UNRELATED", obligations(load(root), ["TASK-001"])["gates"])

    def test_release_traceability_does_not_expand_the_operational_subject(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-context-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "release-context")
            _add_sibling(root)
            _add_release_relation(root)

            one = execution_context(load(root), ["TASK-001"])
            both = execution_context(load(root), ["TASK-001", "TASK-002"])

            self.assertNotIn("TASK-002", {item["meta"]["id"] for item in one["elements"]})
            self.assertIn(
                {"task_id": "TASK-001", "relation": "release", "targets": ["REL-001"]},
                one["administrative_relations"],
            )
            self.assertEqual(
                {"TASK-001", "TASK-002"},
                {item["meta"]["id"] for item in both["elements"] if item["meta"]["kind"] == "task"},
            )


class V2ApprovedObserverTests(unittest.TestCase):
    def test_approved_observers_materialize_exact_checks(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-observer-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "approved-observer-plan")
            _add_sibling(root)
            _add_release_relation(root)
            _configure_observers(root)
            _start_review(root)

            plan = verification_plan(load(root), ["TASK-001"], "test", "development")

            self.assertEqual(plan["status"], "planned")
            self.assertEqual(plan["task_ids"], ["TASK-001"])
            self.assertEqual([check["gate_id"] for check in plan["checks"]], list(GATES))
            self.assertEqual(plan["missing_critical_gates"], [])
            self.assertTrue(plan["allow_task_closure"])
            self.assertNotIn("GATE-UNRELATED", [check["gate_id"] for check in plan["checks"]])

    def test_approved_observers_materialize_execute_and_preserve_human_closure(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-observer-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "approved-observers")
            _add_sibling(root)
            _add_release_relation(root)
            _configure_observers(root, risk="high")
            (root / ".git").write_text("gitdir: /synthetic/worktree/.git/worktrees/example\n", encoding="utf-8")
            _start_review(root)

            plan = verification_plan(load(root), ["TASK-001"], "test", "development")
            self.assertEqual(plan["status"], "planned")
            self.assertEqual(plan["task_ids"], ["TASK-001"])
            self.assertEqual([check["gate_id"] for check in plan["checks"]], list(GATES))
            self.assertEqual(plan["missing_critical_gates"], [])
            self.assertTrue(plan["allow_task_closure"])
            self.assertTrue(all(check["requires_containers"] for check in plan["checks"]))
            self.assertNotIn(".git", plan["material"]["files"])
            self.assertFalse((root / DOCS / "evidence" / "EVID-001.json").exists())

            with self.assertRaisesRegex(ContractError, "--containers"):
                verify(load(root), ["TASK-001"], "test", "development", evidence_id="EVID-001", execute=True)

            executed = []
            result = verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_passing_runner(executed),
            )

            self.assertEqual(executed, list(GATES))
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["processes_executed"], 3)
            self.assertEqual(load(root).elements["TASK-001"].meta["state"], "in-review")
            self.assertEqual(evidence(load(root), "EVID-001")["classification"], "verified")
            self.assertEqual(
                sha((root / "src" / "gate-gamma-observer.py").read_bytes()),
                plan["checks"][-1]["input_hashes"]["src/gate-gamma-observer.py"],
            )
            with self.assertRaisesRegex(ContractError, "human/visual acceptance"):
                close(
                    load(root),
                    ["TASK-001"],
                    "EVID-001",
                    actor="fixture-reviewer",
                    at="2026-09-19T10:02:00+00:00",
                )

    def test_missing_or_invalid_observers_block_without_implicit_execution(self):
        cases = (
            ("missing", {"omitted_gate": "GATE-GAMMA"}, "No approved observer"),
            ("hash", {"invalid_hash_gate": "GATE-GAMMA"}, "input hash mismatch"),
            ("input", {"missing_input_gate": "GATE-GAMMA"}, "input is unsafe or unavailable"),
            ("scope", {"out_of_scope_gate": "GATE-GAMMA"}, "scopes outside"),
            ("command", {"invalid_command_gate": "GATE-GAMMA"}, "command is invalid"),
        )
        for name, options, reason in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="lks-sdd-v2-observer-") as directory:
                root = Path(directory)
                materialize_ready_project(root, "invalid-observer-" + name)
                _configure_observers(root, **options)
                _start_review(root)

                plan = verification_plan(load(root), ["TASK-001"], "test", "development")

                self.assertEqual(plan["status"], "blocked")
                self.assertIn("GATE-GAMMA", plan["missing_critical_gates"])
                self.assertEqual(
                    verify(load(root), ["TASK-001"], "test", "development", evidence_id="EVID-001", execute=True),
                    plan,
                )
                self.assertTrue(any(reason in blocker for blocker in plan["blockers"]))
                self.assertFalse((root / DOCS / "evidence" / "EVID-001.json").exists())

    def test_changed_approved_input_blocks_evidence_recording(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-observer-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "changed-observer-input")
            _configure_observers(root)
            _start_review(root)
            executed = []
            passing = _passing_runner(executed)

            def changed_input_runner(run_root: Path, entry: dict):
                if not executed:
                    (run_root / "src" / "gate-alpha-observer.py").write_text(
                        "print('changed after plan')\n", encoding="utf-8"
                    )
                return passing(run_root, entry)

            with self.assertRaisesRegex(ContractError, "input changed during execution"):
                verify(
                    load(root),
                    ["TASK-001"],
                    "test",
                    "development",
                    evidence_id="EVID-001",
                    execute=True,
                    runner=changed_input_runner,
                )
            self.assertEqual(executed, list(GATES))
            self.assertFalse((root / DOCS / "evidence" / "EVID-001.json").exists())


if __name__ == "__main__":
    unittest.main()
