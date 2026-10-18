"""One-off V4-02 observation of an unchanged runtime; synthetic consumers only.

This is a measurement aid, not a plugin entrypoint or a whole-task host benchmark.
Run against the extracted, hashed source archive described in BASELINE.md.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def files(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes())
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() or output == source or source in output.parents:
        raise ValueError("Use a new output directory outside the measured source")
    if not 1 <= args.samples <= 6:
        raise ValueError("Use one to six baseline samples; this is not a comparison")
    output.mkdir(parents=True)
    sys.path[:0] = [str(source / "scripts"), str(source / "tests")]
    from test_v31_review import IntegralTests
    from v3_current import require_current
    from v3_contract import load
    from v3_workflow import state
    from usage_bundle import fixture as context_fixture
    from v3_cli import execute

    case = IntegralTests(methodName="runTest")
    setup_start = time.perf_counter()
    case.setUp()
    records = []
    try:
        (case.root / "app.py").write_bytes(b"def greeting(): return 'Adios'\n")
        # Fixture setup, not a migration benchmark or a real consumer installation.
        # IntegralTests has current canonical configuration but deliberately no runtime.
        spec = importlib.util.spec_from_file_location("baseline_fixture_installer", source / "distribution/install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        install = installer.plan(args.runtime_bundle.resolve(), case.root, "copilot", contract_transition=("3.1", "3.1"))
        installer.apply(install, install["preview_hash"])
        case.close_proposal()
        case.create_plan()
        require_current(case.root, {"task": case.task})
        lock = json.loads((case.root / ".lks-sdd/distribution-lock.json").read_bytes())
        cli = case.root / lock["runtime"] / "scripts/lks_sdd.py"
        write(output / "synthetic-runtime-lock.json", lock)
        setup_seconds = time.perf_counter() - setup_start
        write(output / "fixture-identities.json", {"synthetic": True, "actor": case.actor,
              "request": case.req, "proposal": case.prop, "plan": case.plan_id, "task": case.task})
        write(output / "context-small.json", context_fixture(case.root, [case.task]))

        def call(label, action, data, flags=("--json", "--compact"), expected=0):
            number = len(records) + 1
            base = output / f"{number:02d}-{label}"
            request = {**data, "usage_context": {"run_id": "v4-02-baseline", "tasks": [case.task], "request": case.req}}
            write(base.with_suffix(".input.json"), request)
            before = files(case.root)
            start = time.perf_counter()
            result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(cli),
                "v3", action, str(case.root), "--input", str(base.with_suffix(".input.json")), *flags],
                capture_output=True, timeout=90)
            elapsed = time.perf_counter() - start
            base.with_suffix(".stdout.json").write_bytes(result.stdout)
            base.with_suffix(".stderr.txt").write_bytes(result.stderr)
            body = json.loads(result.stdout)
            queries = {"status", "interventions", "readiness", "context", "decision-view", "review"}
            changed = files(case.root) != before
            if action in queries and changed:
                raise AssertionError("Query mutated synthetic consumer: " + action)
            if result.returncode != expected:
                raise AssertionError(f"Unexpected exit {result.returncode}: {body.get('cause', body.get('status'))}")
            usage = body.get("usage")
            operational = {k: v for k, v in body.items() if k != "usage"}
            operational_raw = (json.dumps(operational, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            row = {"label": label, "action": action, "flags": list(flags), "exit": result.returncode,
                "stdout_bytes": len(result.stdout), "stdout_characters": len(result.stdout.decode("utf-8")),
                "stderr_bytes": len(result.stderr), "input_bytes": base.with_suffix(".input.json").stat().st_size,
                "operational_reserialized_bytes": len(operational_raw),
                "diagnostic_increment_bytes": len(result.stdout) - len(operational_raw) if usage else 0,
                "stdout_sha256": digest(result.stdout), "cli_wall_seconds": elapsed,
                "consumer_changed": changed, "status": body.get("status"),
                "transport": (usage or {}).get("transport"), "usage_present": bool(usage),
                "output_file_bytes": (output / "decision-export.json").stat().st_size
                    if "--output" in flags else 0}
            records.append(row)
            return body

        for sample in range(args.samples):
            call(f"small-context-{sample + 1}", "context", {"roots": [case.task]})
        for action, data in (("status", {"task": case.task}),
                             ("interventions", {"request": case.req, "actor": case.actor}),
                             ("readiness", {"task": case.task, "actor": case.actor, "action": "start"})):
            call("prepare-" + action, action, data)
        decision = {"event": "authorize-plan", "data": {"actor": case.actor, "plan": case.plan_id,
                    "statement": "Valido y autorizo el plan sintético exacto", "review_tasks": [case.task]}}
        for mode, flags in (("compact", ("--json", "--compact")),
                            ("details", ("--json", "--details")),
                            ("export-compact", ("--json", "--compact", "--output", str(output / "decision-export.json")))):
            call("decision-" + mode, "decision-view", decision, flags)

        prose = case.root / "docs/lks-sdd/legacy-unclassified.md"
        prose.write_text('---\nschema_version: "3.1"\n---\n\n# Fuente histórica sin clasificación\n' +
                         "Conservar las obligaciones desconocidas hasta revisar su aplicabilidad.\n" * 280,
                         encoding="utf-8")
        write(output / "context-large-unclassified.json", context_fixture(case.root, [case.task]))
        for sample in range(args.samples):
            call(f"large-context-{sample + 1}", "context", {"roots": [case.task]})
        prose_bytes = prose.stat().st_size
        prose.unlink()  # Only this synthetic input, restored before the lifecycle.

        call("invalid-root", "context", {"roots": ["00000000-0000-0000-0000-000000000000"]}, expected=2)
        call("start", "start", {"actor": case.actor, "task": case.task, "reason": "Inicio técnico autorizado del escenario"},
             ("--json", "--apply"))
        (case.root / "app.py").write_bytes(b"def greeting(): return 'Hola'\n")
        proof = subprocess.run([sys.executable, "-B", "-c", "import app; assert app.greeting() == 'Hola'; print('greeting: passed; expected Hola')"],
                               cwd=case.root, capture_output=True, timeout=30)
        if proof.returncode:
            raise AssertionError(proof.stderr.decode("utf-8"))
        artifact = "docs/lks-sdd/evidence/observed-test.txt"
        (case.root / artifact).parent.mkdir(parents=True, exist_ok=True)
        (case.root / artifact).write_bytes(proof.stdout)
        (output / "actual-test.stdout.txt").write_bytes(proof.stdout)
        call("implement", "implement", {"actor": case.actor, "task": case.task, "reason": "Código sintético comprobado"}, ("--json", "--apply"))
        call("record-evidence", "evidence", {"actor": case.actor, "task": case.task, "tests": ["greeting"],
             "outcome": "passed", "source": "automated", "artifact": artifact,
             "explanation": "Subproceso real sobre el código sintético exacto; no aceptación humana"}, ("--json", "--apply"))
        call("verify", "verify", {"actor": case.actor, "task": case.task, "reason": "Evidencia actual recuperable"}, ("--json", "--apply"))
        call("close", "close", {"actor": case.actor, "task": case.task, "reason": "Cierre técnico del caso sintético"}, ("--json", "--apply"))
        closed_state = state(load(case.root).require_valid(), load(case.root).get(case.task))

        # Establish compatibility constraints without changing runtime implementation.
        observed = execute("context", case.root, {"roots": [case.task]})["usage"]["observations"]
        (output / "import-probe.json").write_text(json.dumps(observed), encoding="utf-8")
        # A separate process must downgrade imported measured claims, as 3.4.3 does.
        import_check = subprocess.run([sys.executable, "-B", "-c",
            "import sys,json;sys.path.insert(0,sys.argv[1]);from v3_usage import imported;"
            "r=imported(json.load(open(sys.argv[2],encoding='utf-8'))[0]);"
            "print(json.dumps({'origin':r['origin'],'metric_statuses':{k:v['status'] for k,v in r['metrics'].items()}}))",
            str(source / "scripts"), str(output / "import-probe.json")], capture_output=True, timeout=30)
        if import_check.returncode:
            raise AssertionError(import_check.stderr.decode())
        imported = json.loads(import_check.stdout)
        write(output / "import-probe-result.json", imported)

        aggregates = {}
        for prefix in ("small-context-", "large-context-"):
            group = [r for r in records if r["label"].startswith(prefix)]
            aggregates[prefix.rstrip("-")] = {k: statistics.median(r[k] for r in group) for k in
                ("stdout_bytes", "stdout_characters", "diagnostic_increment_bytes", "cli_wall_seconds")}
        summary = {"scope": "unchanged 3.4.3 synthetic CLI reference, not a candidate comparison or human benchmark",
            "python": sys.version.split()[0], "platform": sys.platform, "samples": args.samples,
            "setup_seconds_excluded_from_cli": setup_seconds, "rows": records, "aggregates": aggregates,
            "unclassified_prose_bytes": prose_bytes, "final_synthetic_task_state": closed_state,
            "queries_mutated_consumer": any(r["consumer_changed"] for r in records if r["action"] in
                {"status", "interventions", "readiness", "context", "decision-view", "review"}),
            "imported_observation": imported,
            "host_tokens": None, "billed_cost": None, "human_active_minutes": None,
            "limitations": ["Three single-version samples are descriptive, not comparative performance proof",
                "Synthetic approvals are fixture mechanics, not real human approval or comprehension",
                "Raw CLI captured to files; full stdout was not delivered to the model",
                "Setup and extra presentation/export probes are not part of a minimal S1 flow",
                "No S1-S7 final host campaign and no 4.0 acceptance criteria executed"]}
        write(output / "measurement.json", summary)
        print(json.dumps({"output": str(output), "aggregates": aggregates, "operations": len(records),
              "closed_state": closed_state, "queries_mutated_consumer": summary["queries_mutated_consumer"],
              "import_assurance": imported["origin"]["assurance"]}, ensure_ascii=False))
    finally:
        case.doCleanups()


if __name__ == "__main__":
    main()
