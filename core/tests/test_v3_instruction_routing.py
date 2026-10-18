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
from v3_decision_profiles import ACTIONS, PROFILES, OPERATION_GUIDES, profiles, instruction_refs


class RoutingTests(unittest.TestCase):
    def test_every_public_action_has_a_route(self):
        self.assertEqual(set(CLI_ACTIONS), set(ACTIONS) & set(CLI_ACTIONS))
        self.assertEqual(18, len(PROFILES))
        for action in CLI_ACTIONS:
            selected = profiles(action, {"purpose": "proposal"})
            self.assertTrue(selected)
            refs = instruction_refs(selected, event=action)
            self.assertEqual(len(refs), len({r["path"] for r in refs}))
            self.assertEqual(len(refs), 2 + len({PROFILES[p][0] for p in selected} - {None}) + len(OPERATION_GUIDES.get(action, ())))

    def test_work_operation_routes_keep_authority_and_load_only_their_resources(self):
        from v3_presentation_guard import required
        for action in ('work-prepare', 'work-continue', 'work-record-results'):
            refs = {r['path'] for r in instruction_refs(profiles(action, {}), event=action)}
            self.assertFalse(required(action, {}))
            self.assertNotIn('docs/WORK-ACTIVITY.md', refs)
            if action == 'work-prepare':
                self.assertIn('docs/WORK-PREPARE.md', refs)
                self.assertNotIn('docs/WORK-OPERATIONS.md', refs)
            else:
                self.assertIn('docs/WORK-OPERATIONS.md', refs)
                self.assertNotIn('docs/WORK-PREPARE.md', refs)
        refs = {r['path'] for r in instruction_refs(profiles('work-record-results', {}), event='work-record-results')}
        self.assertIn('docs/decision-guides/verification.md', refs)
        self.assertEqual(['assignment'], profiles('resume', {'review': True}))
        self.assertEqual(['correction','verification'], profiles('resolve-defect', {}))

    def test_changed_event_and_operation_resource_reloads_exact_bytes(self):
        import shutil
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            for name in ('docs/V3-COMMON.md','docs/USER-DECISIONS.md','docs/WORK-OPERATIONS.md'):
                path = target/name; path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(root/name,path)
            first = instruction_refs(['information'],target,event='work-continue')
            path = target/'docs/WORK-OPERATIONS.md'; path.write_bytes(path.read_bytes()+b'\nChanged operation condition.\n')
            second = instruction_refs(['information'],target,event='work-continue')
            self.assertNotEqual(first[-1]['sha256'],second[-1]['sha256'])
            path.unlink()
            with self.assertRaises(ContractError): instruction_refs(['information'],target,event='work-continue')
            with self.assertRaises(ContractError): instruction_refs(['information'],target,event='unknown')
            self.assertEqual(2,len(instruction_refs(['information'],target,event='status')))

    def test_six_skills_keep_discovery_and_resolvable_local_references(self):
        import re
        import yaml
        root = Path(__file__).resolve().parents[1]
        entries = sorted((root/'skills').glob('lks-sdd-*/SKILL.md'))
        self.assertEqual(6,len(entries))
        descriptions = set()
        for entry in entries:
            meta = yaml.safe_load(entry.read_text(encoding='utf-8').split('---',2)[1])
            self.assertEqual(entry.parent.name,meta['name'])
            descriptions.add(meta['description'])
            policy = yaml.safe_load((entry.parent/'agents/openai.yaml').read_text(encoding='utf-8'))
            self.assertIs(True,policy['policy']['allow_implicit_invocation'])
            for path in (entry,entry.parent/'references/v3.md'):
                for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
                    if '://' in link: continue
                    target = (path.parent/link.split('#',1)[0]).resolve()
                    self.assertTrue(target.is_relative_to(root),link)
                    self.assertTrue(target.is_file(),(path,link))
        self.assertEqual(6,len(descriptions))

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
                    skill_paths = [f'skills/lks-sdd-{s}/{p}' for s in ('help','define','adopt-existing','assess-readiness','implement','verify')
                                   for p in ('SKILL.md','references/v3.md','agents/openai.yaml')]
                    for relative in ("scripts/v3_cli_presentation.py", "docs/CLI-PRESENTATION.md", "scripts/diagnostic_capture.py", "docs/DIAGNOSTIC-CAPTURE.md", "tests/test_diagnostic_capture.py", "tests/test_v4_cli_presentation.py", "docs/WORK-PREPARE.md", "docs/WORK-OPERATIONS.md", "docs/WORK-ACTIVITY.md", "docs/DOCUMENT-CONTEXT.md", "docs/V3-COMMON.md", *skill_paths):
                        self.assertEqual(core[relative], package.read(runtime + relative))
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
                minimal = subprocess.run([*command, "--view", "operational", "--json"],
                    capture_output=True, text=True, encoding="utf-8", timeout=60)
                self.assertEqual(0, minimal.returncode, minimal.stdout + minimal.stderr)
                operational = json.loads(minimal.stdout)
                usage = operational.pop("usage")
                self.assertEqual("lks-sdd-usage-view/1", usage["format"])
                self.assertNotIn("observations", usage)
                self.assertEqual({k:v for k,v in view.items() if k != "usage"}, operational)
                self.assertEqual([], list(project.iterdir()))
                capture = directory / (host + "-capture")
                recorded = subprocess.run([*command, "--view", "operational", "--capture-dir", str(capture)],
                    capture_output=True, text=True, encoding="utf-8", timeout=60)
                self.assertEqual(0, recorded.returncode, recorded.stdout + recorded.stderr)
                self.assertEqual("stored", json.loads(recorded.stdout)["diagnostic_capture"]["status"])
                inspected = subprocess.run([sys.executable, "-B", "-X", "utf8", str(target / "scripts/lks_sdd.py"), "usage-inspect", str(capture)],
                    capture_output=True, text=True, encoding="utf-8", timeout=60)
                self.assertEqual(0, inspected.returncode, inspected.stdout + inspected.stderr)
                self.assertEqual("stored", json.loads(inspected.stdout)["status"])
                self.assertEqual([], list(project.iterdir()))
                rendered.append(view)
            # Trace IDs/times describe distinct invocations; the decision itself
            # must remain identical across hosts, including its exact receipt.
            for value in rendered:
                usage = value.pop("usage")
                self.assertEqual("query",usage["observations"][0]["stage"])
                self.assertEqual("lks-sdd-usage/1",usage["observations"][0]["format"])
            self.assertEqual(rendered[0], rendered[1])


if __name__ == "__main__": unittest.main()
