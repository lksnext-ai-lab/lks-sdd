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
from v2_controls import accept_result, authorize_delivery, continue_with_reservations, correction
from v2_lifecycle import checkpoint, planning, start, work_inventory
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
    request = model.elements["PCH-001"]
    request_meta = dict(request.meta, revision=request.meta["revision"] + 1)
    request_meta["points"] = [dict(request_meta["points"][0], tasks=["TASK-001", "TASK-002"])]
    _apply(
        root,
        {path: render_document("fixture-task", "Synthetic sibling", [{"meta": sibling, "body": source.body}]),
         **edit_elements(model, {"PCH-001": request_meta})},
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


def _configure_reservation_policy(
    root: Path,
    *,
    environments: list[str] | None = None,
    gate_scopes: list[str] | None = None,
    statuses: list[str] | None = None,
) -> None:
    model = load(root)
    governance = model.elements["ADR-001"]
    value = dict(governance.meta)
    value["revision"] += 1
    value["verification_reservation_policy"] = {
        "rules": [
            {
                "id": "RES-POL-001",
                "environments": environments or ["test"],
                "stages": ["development"],
                "gate_scopes": gate_scopes or ["component"],
                "statuses": statuses or ["failed", "blocked", "not-run"],
            }
        ]
    }
    _apply(root, edit_elements(model, {"ADR-001": value}), "configure-synthetic-reservation-policy")


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


def _partially_failing_runner(executed: list[str], failed_gate: str):
    passing = _passing_runner(executed)

    def runner(root: Path, entry: dict):
        if entry["gate_id"] != failed_gate:
            return passing(root, entry)
        executed.append(entry["gate_id"])
        return {
            "gate_id": entry["gate_id"],
            "status": "failed",
            "scopes": entry["gate"]["scopes"],
            "interfaces": entry["gate"]["interfaces"],
            "observations": {"synthetic": False},
            "artifacts": [],
        }, {}

    return runner


def _blocked_runner(executed: list[str], blocked_gate: str, reason: str):
    passing = _passing_runner(executed)

    def runner(root: Path, entry: dict):
        if entry["gate_id"] != blocked_gate:
            return passing(root, entry)
        executed.append(entry["gate_id"])
        return {
            "gate_id": entry["gate_id"],
            "status": "blocked",
            "reason": reason,
            "scopes": entry["gate"]["scopes"],
            "interfaces": entry["gate"]["interfaces"],
            "observations": {},
            "artifacts": [],
        }, {}

    return runner


def _apply_close(root: Path, evidence_id: str, request: dict) -> dict:
    result = close(
        load(root),
        ["TASK-001"],
        evidence_id,
        actor="fixture-reviewer",
        at="2026-09-19T10:03:00+00:00",
        reason="Accept the bounded synthetic verification reservation.",
        reservation_request=request,
    )
    return close(
        load(root),
        ["TASK-001"],
        evidence_id,
        actor="fixture-reviewer",
        at="2026-09-19T10:03:00+00:00",
        reason="Accept the bounded synthetic verification reservation.",
        reservation_request=request,
        authorized_hash=result["preview_hash"],
    )


def _apply_reservation_acceptance(root: Path, evidence_id: str, request: dict) -> dict:
    result = accept_result(
        load(root),
        ["TASK-001"],
        evidence_id,
        actor="fixture-reviewer",
        at="2026-09-19T10:03:00+00:00",
        reason="Accept the bounded synthetic verification reservation.",
        reservation_request=request,
    )
    return accept_result(
        load(root),
        ["TASK-001"],
        evidence_id,
        actor="fixture-reviewer",
        at="2026-09-19T10:03:00+00:00",
        reason="Accept the bounded synthetic verification reservation.",
        reservation_request=request,
        authorized_hash=result["preview_hash"],
    )


def _apply_reservation_continuation(root: Path, task_ids: list[str], request: dict) -> dict:
    result = continue_with_reservations(
        load(root),
        task_ids,
        request,
        actor="fixture-reviewer",
        at="2026-09-19T10:05:00+00:00",
        reason="Continue bounded dependent work with declared inherited reservations.",
    )
    return continue_with_reservations(
        load(root),
        task_ids,
        request,
        actor="fixture-reviewer",
        at="2026-09-19T10:05:00+00:00",
        reason="Continue bounded dependent work with declared inherited reservations.",
        authorized_hash=result["preview_hash"],
    )


def _apply_replan(root: Path, task_ids: list[str]) -> dict:
    result = correction(
        load(root),
        task_ids,
        actor="fixture-owner",
        at="2026-09-19T10:05:00+00:00",
        reason="End the blocked synthetic execution and request a new decision.",
        replan=True,
    )
    return correction(
        load(root),
        task_ids,
        actor="fixture-owner",
        at="2026-09-19T10:05:00+00:00",
        reason="End the blocked synthetic execution and request a new decision.",
        replan=True,
        authorized_hash=result["preview_hash"],
    )


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

    def test_missing_or_invalid_observers_record_blocked_attempt_without_implicit_execution(self):
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
                result = verify(
                    load(root), ["TASK-001"], "test", "development", evidence_id="EVID-001", execute=True
                )
                recorded = evidence(load(root), "EVID-001")

                self.assertEqual(result["status"], "not-verified")
                self.assertTrue(result["blocked_preflight"])
                self.assertTrue(any(reason in blocker for blocker in plan["blockers"]))
                self.assertTrue((root / DOCS / "evidence" / "EVID-001.json").exists())
                self.assertEqual(recorded["classification"], "not-verified")
                self.assertTrue(recorded["blocked_preflight"])
                self.assertTrue(all(check["status"] in {"blocked", "not-run"} for check in recorded["checks"]))
                with self.assertRaisesRegex(ContractError, "Evidence does not close this exact authorized subject"):
                    close(
                        load(root),
                        ["TASK-001"],
                        "EVID-001",
                        actor="fixture-reviewer",
                        at="2026-09-19T10:02:00+00:00",
                        reason="An absent observer cannot be accepted as a reservation.",
                        reservation_request={
                            "decision": "accept-and-close-with-reservations",
                            "reservations": [{
                                "id": "RES-001",
                                "gate_id": "GATE-GAMMA",
                                "reason": "Synthetic missing observer.",
                                "follow_up": "Declare and run an approved observer.",
                            }],
                        },
                    )

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


class V2ReservationClosureTests(unittest.TestCase):
    def test_hard_preflight_block_has_a_user_authorized_replan_exit(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-replan-exit")
            _configure_observers(root, omitted_gate="GATE-GAMMA")
            _start_review(root)

            recorded = verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
            )
            replanned = _apply_replan(root, ["TASK-001"])
            model = load(root)

            self.assertEqual(recorded["status"], "not-verified")
            self.assertTrue(recorded["blocked_preflight"])
            self.assertTrue(replanned["writes"])
            self.assertEqual(model.elements["TASK-001"].meta["state"], "ready")
            self.assertEqual(model.elements["EXEC-001"].meta["state"], "cancelled")
            self.assertEqual(model.elements["AUTH-001"].meta["state"], "revoked")

    def test_partial_verification_records_actual_failure_and_closes_only_with_policy_bound_reservations(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-closure")
            _configure_observers(root)
            _configure_reservation_policy(root)
            _start_review(root)
            executed = []
            result = verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner(executed, "GATE-ALPHA"),
            )

            self.assertEqual(executed, list(GATES))
            self.assertEqual(result["status"], "not-verified")
            self.assertEqual(evidence(load(root), "EVID-001")["classification"], "not-verified")
            with self.assertRaisesRegex(ContractError, "reservation acceptance remains pending"):
                close(
                    load(root),
                    ["TASK-001"],
                    "EVID-001",
                    actor="fixture-reviewer",
                    at="2026-09-19T10:03:00+00:00",
                )

            request = {
                "decision": "accept-and-close-with-reservations",
                "reservations": [{
                    "id": "RES-001",
                    "gate_id": "GATE-ALPHA",
                    "reason": "The approved observer recorded a synthetic failure.",
                    "follow_up": "Correct the failure and rerun normal verification.",
                }],
            }
            applied = _apply_close(root, "EVID-001", request)
            model = load(root)
            receipt = next(entry for entry in model.by_kind("receipt")
                           if entry.meta.get("category") == "result-reservation-review")

            self.assertTrue(applied["writes"])
            self.assertEqual(model.elements["TASK-001"].meta["state"], "done-with-reservations")
            self.assertEqual(model.elements["TASK-001"].meta["health"], "accepted-with-reservations")
            self.assertEqual(evidence(model, "EVID-001")["classification"], "not-verified")
            self.assertEqual(receipt.meta["technical_classification"], "not-verified")
            self.assertEqual(receipt.meta["reservations"][0]["gate_id"], "GATE-ALPHA")
            self.assertEqual(receipt.meta["execution_id"], "EXEC-001")
            with self.assertRaisesRegex(ContractError, "requires a verified deployable artifact"):
                authorize_delivery(load(root), {
                    "actor": "fixture-delivery-owner",
                    "recorded_at": "2026-09-19T10:04:00+00:00",
                    "expires_at": "2026-09-19T11:04:00+00:00",
                    "environment": "ENV-001",
                    "version": "0.0.0-synthetic",
                    "artifact_digest": "a" * 64,
                    "evidence_id": "EVID-001",
                    "operation": "deployed",
                    "features": ["FTR-001"],
                    "reason": "A reserved result cannot promote delivery.",
                })
            self.assertEqual(close(
                model,
                ["TASK-001"],
                "EVID-001",
                actor="fixture-reviewer",
                at="2026-09-19T10:04:00+00:00",
            )["status"], "already-closed")

    def test_declared_reservation_classifies_evidence_without_changing_failed_check(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "declared-reservation")
            _configure_observers(root)
            _configure_reservation_policy(root)
            _start_review(root)
            executed = []
            request = {
                "reservations": [{
                    "id": "RES-001",
                    "gate_id": "GATE-ALPHA",
                    "reason": "The approved observer is intentionally deferred in this synthetic fixture.",
                    "follow_up": "Run the observer before delivery.",
                }],
            }

            result = verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner(executed, "GATE-ALPHA"),
                reservation_request=request,
            )
            recorded = evidence(load(root), "EVID-001")

            self.assertEqual(result["status"], "verified-with-reservations")
            self.assertEqual(recorded["classification"], "verified-with-reservations")
            self.assertEqual(next(check for check in recorded["checks"] if check["gate_id"] == "GATE-ALPHA")["status"], "failed")
            self.assertEqual(recorded["reservations"][0]["policy_rule_id"], "RES-POL-001")
            close_request = {"decision": "accept-and-close-with-reservations", **request}
            _apply_close(root, "EVID-001", close_request)
            self.assertEqual(load(root).elements["TASK-001"].meta["state"], "done-with-reservations")

    def test_reservation_acceptance_is_a_durable_step_before_later_close(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-acceptance")
            _configure_observers(root)
            _configure_reservation_policy(root)
            _start_review(root)
            request = {
                "decision": "accept-and-close-with-reservations",
                "reservations": [{
                    "id": "RES-001",
                    "gate_id": "GATE-ALPHA",
                    "reason": "Synthetic deferred failure.",
                    "follow_up": "Repeat full verification after correction.",
                }],
            }
            verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner([], "GATE-ALPHA"),
                reservation_request={"reservations": request["reservations"]},
            )

            accepted = _apply_reservation_acceptance(root, "EVID-001", request)
            pending_close = close(
                load(root),
                ["TASK-001"],
                "EVID-001",
                actor="fixture-reviewer",
                at="2026-09-19T10:04:00+00:00",
            )
            completed = close(
                load(root),
                ["TASK-001"],
                "EVID-001",
                actor="fixture-reviewer",
                at="2026-09-19T10:04:00+00:00",
                authorized_hash=pending_close["preview_hash"],
            )

            self.assertTrue(accepted["writes"])
            self.assertTrue(completed["writes"])
            self.assertEqual(load(root).elements["TASK-001"].meta["state"], "done-with-reservations")

    def test_reservation_hard_guards_reject_critical_scope_and_integrity_waivers(self):
        request = {
            "decision": "accept-and-close-with-reservations",
            "reservations": [{
                "id": "RES-001",
                "gate_id": "GATE-ALPHA",
                "reason": "Synthetic reservation request.",
                "follow_up": "Run complete verification.",
            }],
        }
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-scope-guard")
            _configure_observers(root)
            _configure_reservation_policy(root, gate_scopes=["contract"])
            _start_review(root)

            with self.assertRaisesRegex(ContractError, "No reservation policy permits this gate outcome"):
                verify(
                    load(root),
                    ["TASK-001"],
                    "test",
                    "development",
                    evidence_id="EVID-001",
                    execute=True,
                    runner=_partially_failing_runner([], "GATE-ALPHA"),
                    reservation_request={"reservations": request["reservations"]},
                )

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-critical-guard")
            _configure_observers(root)
            model = load(root)
            task = model.elements["TASK-001"]
            replacement = dict(task.meta, critical=True, revision=task.meta["revision"] + 1)
            _apply(root, edit_elements(model, {"TASK-001": replacement}), "mark-synthetic-task-critical")
            _configure_reservation_policy(root)
            _start_review(root)
            verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner([], "GATE-ALPHA"),
            )

            with self.assertRaisesRegex(ContractError, "Critical TASK verification cannot close with reservations"):
                close(
                    load(root),
                    ["TASK-001"],
                    "EVID-001",
                    actor="fixture-reviewer",
                    at="2026-09-19T10:03:00+00:00",
                    reason="Critical work cannot be waived.",
                    reservation_request=request,
                )

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-isolation-guard")
            _configure_observers(root)
            _configure_reservation_policy(root)
            _start_review(root)

            with self.assertRaisesRegex(ContractError, "observer integrity or isolation failure"):
                verify(
                    load(root),
                    ["TASK-001"],
                    "test",
                    "development",
                    evidence_id="EVID-001",
                    execute=True,
                    runner=_blocked_runner([], "GATE-ALPHA", "Observer output contract is malformed"),
                    reservation_request={"reservations": request["reservations"]},
                )
            self.assertFalse((root / DOCS / "evidence" / "EVID-001.json").exists())

    def test_reservations_do_not_bypass_policy_or_dependency_or_delivery_controls(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-guards")
            _add_sibling(root)
            _configure_observers(root)
            _configure_reservation_policy(root, environments=["preproduction"])
            model = load(root)
            sibling = model.elements["TASK-002"]
            sibling_value = dict(sibling.meta, revision=sibling.meta["revision"] + 1)
            sibling_value["relations"] = {
                **{relation: list(targets) for relation, targets in sibling.relations.items()},
                "depends_on": ["TASK-001"],
            }
            _apply(root, edit_elements(model, {"TASK-002": sibling_value}), "add-reservation-dependent-task")
            _start_review(root)
            executed = []
            verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner(executed, "GATE-ALPHA"),
            )
            unpermitted = {
                "decision": "accept-and-close-with-reservations",
                "reservations": [{
                    "id": "RES-001",
                    "gate_id": "GATE-ALPHA",
                    "reason": "Synthetic request without policy.",
                    "follow_up": "Run the observer.",
                }],
            }
            with self.assertRaisesRegex(ContractError, "No reservation policy permits this gate outcome"):
                close(
                    load(root),
                    ["TASK-001"],
                    "EVID-001",
                    actor="fixture-reviewer",
                    at="2026-09-19T10:03:00+00:00",
                    reason="Attempt to bypass the policy.",
                    reservation_request=unpermitted,
                )

        with tempfile.TemporaryDirectory(prefix="lks-sdd-v2-reservation-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "reservation-dependency")
            _add_sibling(root)
            _configure_observers(root)
            _configure_reservation_policy(root)
            model = load(root)
            sibling = model.elements["TASK-002"]
            sibling_value = dict(sibling.meta, revision=sibling.meta["revision"] + 1)
            sibling_value["relations"] = {
                **{relation: list(targets) for relation, targets in sibling.relations.items()},
                "depends_on": ["TASK-001"],
            }
            _apply(root, edit_elements(model, {"TASK-002": sibling_value}), "add-reservation-dependent-task")
            _start_review(root)
            verify(
                load(root),
                ["TASK-001"],
                "test",
                "development",
                evidence_id="EVID-001",
                execute=True,
                runner=_partially_failing_runner([], "GATE-ALPHA"),
            )
            _apply_close(root, "EVID-001", {
                "decision": "accept-and-close-with-reservations",
                "reservations": [{
                    "id": "RES-001",
                    "gate_id": "GATE-ALPHA",
                    "reason": "Synthetic accepted reservation.",
                    "follow_up": "Reverify before unblocking dependent work.",
                }],
            })

            assessment = planning(load(root), ["TASK-002"])

            self.assertEqual(load(root).elements["TASK-001"].meta["state"], "done-with-reservations")
            self.assertIn("Unfinished dependency: TASK-001", assessment["blockers"])
            continued = _apply_reservation_continuation(root, ["TASK-002"], {
                "decision": "continue-with-reservations",
                "dependency_task_ids": ["TASK-001"],
            })
            resumed = planning(load(root), ["TASK-002"])
            continuation = resumed["reservation_continuations"][0]

            self.assertTrue(continued["writes"])
            self.assertEqual(resumed["status"], "ready")
            self.assertEqual(continuation["dependency_task_id"], "TASK-001")
            self.assertEqual(continuation["task_id"], "TASK-002")
            model = load(root)
            dependency = model.elements["TASK-001"]
            replaced = dict(dependency.meta, revision=dependency.meta["revision"] + 1,
                            evidence_ids=[*dependency.meta["evidence_ids"], "EVID-002"])
            _apply(root, edit_elements(model, {"TASK-001": replaced}), "replace-terminal-reservation-evidence")

            stale = planning(load(root), ["TASK-002"])

            self.assertIn("Unfinished dependency: TASK-001", stale["blockers"])
            self.assertEqual(stale["reservation_continuations"], [])


if __name__ == "__main__":
    unittest.main()
