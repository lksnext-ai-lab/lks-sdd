"""Finite routes, bounded resources and composed decisions."""
from pathlib import Path
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_v3_workflow import ProjectFixture  # configures the source runtime
from v3_contract import ContractError
from v3_cli import ACTIONS as CLI_ACTIONS
from v3_decision_profiles import ACTIONS, PROFILES, profiles, instruction_refs


class RoutingTests(unittest.TestCase):
    def test_every_public_action_has_a_route(self):
        self.assertEqual(set(CLI_ACTIONS), set(ACTIONS) & set(CLI_ACTIONS))
        self.assertEqual(18, len(PROFILES))
        for action in CLI_ACTIONS:
            selected = profiles(action, {"purpose": "proposal"})
            self.assertTrue(selected)
            refs = instruction_refs(selected)
            self.assertEqual(len(refs), len({r["path"] for r in refs}))
            self.assertEqual(len(refs), 2 + len({PROFILES[p][0] for p in selected} - {None}))

    def test_conditional_composition_and_deduplication(self):
        self.assertEqual(["planning", "assignment"], profiles("authorize-plan", {"review_tasks": ["task"]}))
        self.assertEqual(["integration", "acceptance"], profiles("integrate", {"accept_result": True}))
        self.assertEqual(3, len(instruction_refs(profiles("integrate", {"accept_result": True}))))
        self.assertEqual(["information"], profiles("start", {}))
        self.assertEqual(["assignment"], profiles("resume", {"offer": "offer"}))
        self.assertEqual(["correction", "verification"], profiles("resolve-defect", {}))

    def test_unknown_purpose_and_missing_runtime_do_not_succeed(self):
        with self.assertRaises(ContractError): profiles("approve", {})
        with self.assertRaises(ContractError): profiles("unknown", {})
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ContractError): instruction_refs(["specification"], temp)

    def test_negative_outcome_cannot_disguise_positive_actions(self):
        from v3_presentation_guard import required
        from v3_decision_presentation import normalize, decision_view
        for action in ("close-proposal", "resolve-comment", "review-exception", "approve", "integrate"):
            self.assertTrue(required(action, {"outcome": "changes-requested"}))
        self.assertFalse(required("review-proposal", {"outcome": "changes-requested"}))
        self.assertFalse(required("review-task", {"outcome": "changes-requested"}))
        self.assertNotEqual(normalize({"requirements": []}), normalize({}))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ContractError, "no admite outcome"):
                decision_view(temp, "close-proposal", {"outcome": "changes-requested"})

    def test_both_packages_execute_the_same_decision_view(self):
        from build_dual_distribution import collect_development
        from dual_distribution import artifacts
        root = Path(__file__).resolve().parents[1]
        core = collect_development(root)
        bundles = artifacts(core, "presentation-test", "development-unreleased")
        rendered = []
        with tempfile.TemporaryDirectory(prefix="lks-presentation-hosts-") as temp:
            directory = Path(temp)
            for host, prefix in (("codex", "lks-sdd-plugin-v"), ("copilot", "lks-sdd-copilot-v")):
                raw = next(raw for name, raw in bundles.items() if name.startswith(prefix))
                target = directory / host; target.mkdir()
                with zipfile.ZipFile(io.BytesIO(raw)) as package:
                    name = next(n for n in package.namelist() if n.endswith("/scripts/v3_decision_presentation.py"))
                    runtime = name.removesuffix("scripts/v3_decision_presentation.py")
                    for ref in instruction_refs(list(PROFILES)):
                        self.assertEqual(core[ref["path"]], package.read(runtime + ref["path"]))
                    for source in package.namelist():
                        if not source.startswith(runtime): continue
                        relative = source[len(runtime):]
                        path = target / relative
                        self.assertTrue(path.resolve().is_relative_to(target.resolve()))
                        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(package.read(source))
                project = directory / (host + "-project"); project.mkdir()
                payload = directory / (host + "-input.json")
                payload.write_text(json.dumps({"event": "identity", "data": {"actor_name": "Marta", "pending": "Confirmar quién solicita el cambio", "alternatives": ["Soy Marta", "Soy otra persona"]}}), encoding="utf-8")
                command = [sys.executable, "-B", "-X", "utf8", str(target / "scripts/lks_sdd.py"), "v3", "decision-view", str(project), "--input", str(payload)]
                result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                view = json.loads(result.stdout); self.assertTrue(view["complete"], view["issues"])
                self.assertNotIn("sources", view); self.assertEqual([], list(project.iterdir()))
                rendered.append(view)
            self.assertEqual(rendered[0], rendered[1])


if __name__ == "__main__": unittest.main()
