"""One bounded administrative journey on a disposable, pinned consumer.

Preparation creates the incident's open-work fixture; measurement performs the
native runtime cutover, cancellation, successor authorization and verified close.
No active plugin installation, host session, Git commit or publication is used.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reserve_full_journey(op):
    authorization = json.loads((op / "authorization.json").read_bytes())
    if authorization.get("full_journeys_started", 0) or authorization.get("actual_worker_starts", 0):
        raise RuntimeError("Journey reservation already consumed; no automatic retry, even before worker start")
    if not (op / "journey-admission.json").exists():
        raise RuntimeError("Admission must pass before launch")
    admission = json.loads((op / "journey-admission.json").read_bytes())
    runner_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if admission.get("status") != "admitted" or admission.get("execution_runner_sha256") != runner_digest:
        raise RuntimeError("Admission is invalid or belongs to another runner")
    authorization["full_journeys_started"] = 1
    write_json(op / "authorization.json", authorization)


def domain(core):
    sys.path[:0] = [str(core / "scripts"), str(ROOT / "tests")]
    # Fixtures must retain the frozen runtime, rather than importing source modules.
    import v3_contract
    return v3_contract


def invoke(phase, op, timeout=600):
    done = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                           "--operation", str(op), "--phase", phase], capture_output=True, timeout=timeout)
    (op / (phase + ".stdout")).write_bytes(done.stdout)
    (op / (phase + ".stderr")).write_bytes(done.stderr)
    if done.returncode:
        raise RuntimeError(phase + " failed; inspect " + str(op / (phase + ".stderr")))
    return json.loads(done.stdout)


def build(op):
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_dual_distribution import collect_development
    from build_candidate_package import _package_integrity_bytes
    from dual_distribution import compact_distribution_core, project_files, inventory, json_bytes, runtime_identity, zip_bytes
    raw = subprocess.run(["git", "archive", "--format=zip", "v3.4.3"], cwd=ROOT,
                         capture_output=True, check=True, timeout=60).stdout
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        old = {item.filename: archive.read(item) for item in archive.infolist() if not item.is_dir()}
    old["package-integrity.json"] = _package_integrity_bytes(list(old.items()), "3.4.3", "published-v3.4.3-fixture")
    binding = {}
    for name, files in [("reference", old), ("candidate", collect_development(ROOT))]:
        files = compact_distribution_core(files)
        core = op / (name + "-core"); core.mkdir()
        for relative, body in files.items():
            path = core / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(body)
        # Only the native consumer payload is needed, not five distribution ZIPs.
        bundle = op / (name + "-bundle"); (bundle / "payload").mkdir(parents=True)
        payload = zip_bytes(project_files(files, "v4-19-20-" + name, "development-unreleased"))
        (bundle / "payload/copilot.zip").write_bytes(payload)
        manifest = {"schema_version": "1.0", "version": "3.4.3",
                    "source": "v4-19-20-" + name, "channel": "development-unreleased",
                    "files": inventory({"payload/copilot.zip": payload}),
                    "runtime_digest": runtime_identity(files)}
        (bundle / "payload-manifest.json").write_bytes(json_bytes(manifest))
        binding[name] = {"runtime_digest": runtime_identity(files),
                         "git_module_sha256": hashlib.sha256(files["scripts/v3_git.py"]).hexdigest()}
    binding["runner_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(op / "binding.json", binding)
    return binding


def seed(op):
    core = op / "reference-core"; contract = domain(core)
    from presentation_test_support import present
    import test_v31_review as fixture
    from v3_authoring import author
    from v3_git import git, code_inventory
    from v3_workflow import state, transition
    from runtime_doctor import check
    case = fixture.IntegralTests("runTest"); case.setUp()
    root = op / "consumer"; shutil.copytree(case.root, root); case.root = root
    try:
        proposal = copy.deepcopy(contract.load(root).get(case.prop).item())
        proposal["meta"]["revision"] += 1
        proposal["meta"]["data"]["included"] = ["app.py", "support_a.py", "support_b.py"]
        fixture.commit_packet(root, author(root, case.actor, [proposal]))
        case.close_proposal(); case.create_plan()
        (root / "app.py").write_text("def greeting(): return 'Adios'\n", encoding="utf-8")
        spec = importlib.util.spec_from_file_location("synthetic_installer", core / "distribution/install.py")
        installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
        prepared = installer.plan(op / "reference-bundle", root, "copilot")
        # Seed fixture ownership, exactly as the existing compatibility fixture;
        # these are fixture bytes, never an installation into an active product.
        for entry in prepared["changes"]:
            path = root / entry["path"]
            if entry["content"] is None: path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(bytes.fromhex(entry["content"]))
        prior = len(code_inventory(root))
        for number in range(1178 - prior):
            path = root / "unrelated" / (str(number) + ".txt")
            path.parent.mkdir(exist_ok=True); path.write_bytes(b"pre-existing unchanged synthetic code input\n")
        case.advance("start")
        (root / "app.py").write_text("from support_a import text\ndef greeting(): return text()\n", encoding="utf-8")
        (root / "support_a.py").write_text("from support_b import WORD\ndef text(): return WORD\n", encoding="utf-8")
        (root / "support_b.py").write_text("WORD = 'Hola'\n", encoding="utf-8")
        successor = contract.element("task", "Continuidad autorizada del saludo",
            "Conservar el trabajo ya realizado y verificar las tres rutas expresamente cubiertas.",
            request=case.req, owner=case.actor, scope=["app.py", "support_a.py", "support_b.py"],
            acceptance=["Hola"], tests=["greeting"])
        successor["meta"]["relations"]["replaces"] = [case.task]
        plan = contract.element("plan", "Plan de continuidad administrativa",
            "Sustituir administrativamente el encargo estrecho y comprobar el resultado sin repetir la implementación.",
            request=case.req)
        plan["meta"]["relations"]["tasks"] = [successor["meta"]["uid"]]
        fixture.commit_packet(root, author(root, case.actor, [successor, plan]))
        # Verify the administrative packet is valid before increasing the census.
        present(transition, root, case.actor, case.task, "cancel", "Sustitución administrativa preparada; se conserva el trabajo")
        initial = contract.load(root).require_valid()
        old_lock = json.loads((root / ".lks-sdd/distribution-lock.json").read_bytes())
        original_decisions = {e.uid: e.digest() for e in initial.by_kind("authorization")}
        objects = root / ".lks-sdd/objects/sha256"; objects.mkdir(parents=True, exist_ok=True)
        count = sum(p.is_file() for p in objects.iterdir())
        for number in range(10157 - count):
            body = ("Preserved opaque synthetic historical object " + str(number)).encode()
            (objects / hashlib.sha256(body).hexdigest()).write_bytes(body)
        def paths(): return [p.decode() for p in git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0") if p]
        before = paths()
        internal = lambda p: p.startswith((".lks-sdd/", "docs/lks-sdd/"))
        missing = 18847 - sum(internal(p) for p in before)
        retained = root / ".lks-sdd/retained-fixture"; retained.mkdir()
        assert missing >= 0
        for number in range(missing): (retained / (str(number) + ".txt")).write_bytes(b"protected synthetic retained material\n")
        census = paths()
        assert len(census) == 20027, len(census)
        assert sum(internal(p) for p in census) == 18847
        documentary = initial.snapshot()
        try:
            present(transition, root, case.actor, case.task, "cancel", "Sustitución administrativa autorizada")
        except contract.ContractError as exc:
            assert "Inventario de código demasiado amplio" in str(exc), str(exc)
            observed_failure = str(exc)
        else: raise AssertionError("Published runtime must reproduce the inventory blocker")
        assert contract.load(root).snapshot() == documentary
        assert not (root / ".lks-sdd/transaction.json").exists()
        assert check(root)["status"] == "valid"
        scenario = {"actor": case.actor, "request": case.req, "proposal": case.prop,
                    "original": case.task, "successor": successor["meta"]["uid"], "plan": plan["meta"]["uid"],
                    "configuration": case.configuration, "initial_runtime": old_lock["runtime_digest"],
                    "original_decisions": original_decisions, "proposal_digest": initial.get(case.prop).digest(),
                    "initial_states": {"original": state(initial, initial.get(case.task)),
                                       "successor": state(initial, initial.get(successor["meta"]["uid"]))},
                    "git_paths": len(census), "internal_paths": 18847, "outside_paths": 1180,
                    "loose_objects": 10157, "reference_failure": observed_failure}
        write_json(op / "scenario.json", scenario)
        # One immutable reusable large fixture, not another full execution.
        with zipfile.ZipFile(op / "large-fixture.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for path in root.rglob("*"):
                if path.is_file(): archive.write(path, path.relative_to(root).as_posix())
        return scenario
    finally:
        case.doCleanups()


def execute(op):
    if sys.stdin.buffer.readline() != b"run\n": raise RuntimeError("Missing measurement start")
    authorization = json.loads((op / "authorization.json").read_bytes())
    assert authorization.get("actual_worker_starts", 0) == 0, "No automatic full rerun"
    authorization["actual_worker_starts"] = 1
    authorization["worker_started_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    write_json(op / "authorization.json", authorization)
    contract = domain(op / "candidate-core")
    from presentation_test_support import present
    from v3_current import upgrade
    from v3_storage import apply
    from runtime_doctor import check
    scenario = json.loads((op / "scenario.json").read_bytes()); root = op / "consumer"
    packet = present(upgrade, root, {"actor": scenario["actor"], "collaboration": scenario["configuration"],
        "statement": "Autorizo el cambio sintético de runtime conservando decisiones y trabajo abierto",
        "runtime_bundle": str(op / "candidate-bundle")})
    receipt = apply(root, packet, packet["preview"]["preview_hash"])
    lock = json.loads((root / ".lks-sdd/distribution-lock.json").read_bytes())
    binding = json.loads((op / "binding.json").read_bytes())
    assert lock["runtime_digest"] == binding["candidate"]["runtime_digest"]
    assert check(root)["status"] == "valid"
    write_json(op / "cutover.json", {"status": "valid", "runtime_digest": lock["runtime_digest"], "receipt": receipt})
    result = invoke("finish", op)
    result["runtime_digest"] = lock["runtime_digest"]
    return result


def finish(op):
    root = op / "consumer"; scenario = json.loads((op / "scenario.json").read_bytes())
    lock = json.loads((root / ".lks-sdd/distribution-lock.json").read_bytes())
    contract = domain(root / lock["runtime"])
    from presentation_test_support import present
    from v3_authoring import approve_and_authorize
    from v3_storage import apply
    from v3_verification import evidence
    from v3_workflow import state, transition
    from v3_git import code_inventory
    from v3_decision_presentation import decision_view
    actions = []
    def commit(name, packet):
        result = apply(root, packet, packet["preview"]["preview_hash"])
        actions.append(name); write_json(op / "actions.json", actions)
        return result
    def advance(task, action):
        return commit(action, present(transition, root, scenario["actor"], task, action,
            "Continuidad administrativa sintética; preservo especificación y trabajo ya acreditados"))
    cancellation = {"actor": scenario["actor"], "task": scenario["original"],
                    "reason": "Sustitución administrativa autorizada por la sucesora con alcance completo"}
    cancellation["presented"] = decision_view(root, "cancel", cancellation)["receipt"]
    write_json(op / "cancel-input.json", cancellation)
    cancelled = subprocess.run([sys.executable, "-B", str(root / lock["runtime"] / "scripts/lks_sdd.py"),
        "v3", "cancel", str(root), "--input", str(op / "cancel-input.json"),
        "--apply", "--view", "operational", "--json"], capture_output=True, timeout=180)
    (op / "cancel-cli.stdout").write_bytes(cancelled.stdout)
    (op / "cancel-cli.stderr").write_bytes(cancelled.stderr)
    if cancelled.returncode: raise RuntimeError("Native cancel CLI failed; inspect cancel-cli.stderr")
    actions.append("cancel-cli"); write_json(op / "actions.json", actions)
    commit("authorize-successor", present(approve_and_authorize, root, scenario["actor"], scenario["plan"],
        "Apruebo el alcance concreto de continuidad y autorizo su ejecución y revisión",
        review_tasks=[scenario["successor"]]))
    advance(scenario["successor"], "start")
    advance(scenario["successor"], "implement")
    code = "import runpy,inspect,json; f=runpy.run_path('app.py')['greeting']; assert f()=='Hola'; assert not inspect.signature(f).parameters; print(json.dumps({'greeting':'Hola','parameters':0,'passed':True}))"
    observed = subprocess.run([sys.executable, "-B", "-c", code], cwd=root, capture_output=True, timeout=30, check=True)
    artifact = "docs/lks-sdd/evidence/actual-greeting.json"
    path = root / artifact; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(observed.stdout)
    commit("record-proof", evidence(root, scenario["actor"], scenario["successor"], ["greeting"], "passed",
        "automated", artifact, "Resultado real de la función sin parámetros, sujeto completo de tres rutas"))
    advance(scenario["successor"], "verify")
    advance(scenario["successor"], "close")
    model = contract.load(root).require_valid()
    assert state(model, model.get(scenario["original"])) == "cancelled"
    assert state(model, model.get(scenario["successor"])) == "closed"
    assert model.get(scenario["proposal"]).digest() == scenario["proposal_digest"]
    assert all(model.get(uid).digest() == digest for uid, digest in scenario["original_decisions"].items())
    assert model.get(scenario["successor"]).relations["replaces"] == [scenario["original"]]
    assert not (root / ".lks-sdd/transaction.json").exists()
    return {"status": "passed", "original": "cancelled", "successor": "closed", "actions": actions,
            "unchanged_prior_decisions": len(scenario["original_decisions"]), "proposal_preserved": True,
            "eligible_code_paths": len(code_inventory(root)), "real_test": json.loads(observed.stdout),
            "loaded_git_module": str(sys.modules["v3_git"].__file__), "pending_journal": False,
            "native_cancel_cli_exit_code": cancelled.returncode,
            "integration": "not-run", "functional_acceptance": "not-run", "active_installation": False}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--operation", type=Path, required=True)
    parser.add_argument("--phase", choices=["prepare", "seed", "measure", "execute", "finish"], required=True)
    args = parser.parse_args(); op = args.operation.resolve()
    if args.phase == "prepare":
        build(op); result = invoke("seed", op)
    elif args.phase == "seed": result = seed(op)
    elif args.phase == "execute": result = execute(op)
    elif args.phase == "finish": result = finish(op)
    else:
        sys.path.insert(0, str(ROOT / "tests")); from performance_command import run
        reserve_full_journey(op)
        result, resources = run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                                 "--operation", str(op), "--phase", "execute"], ROOT, "V4-20", timeout=600,
                                 direct_worker=True)
        write_json(op / "journey-result.json", result); write_json(op / "journey-resources.json", resources)
        result = {"result": result, "resources": resources}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__": main()
