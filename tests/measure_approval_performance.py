"""Repeated isolated before/after measurements; synthetic data, no release gate.

Example: python -B -X utf8 tests/measure_approval_performance.py --output report.json
"""
import argparse
from collections import Counter
from contextlib import contextmanager, nullcontext
import ctypes
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from unittest.mock import patch

from approval_performance_support import ROOT, REFERENCE, runtime, synthetic, stable_generation, key, shared_inventory_history

PROGRESS = None


def isolation_audit():
    """Refuse ambiguous measurements instead of silently accepting another runner."""
    if sys.platform != "win32": return {"supported": False, "conflicting_pids": []}
    script = ("@(Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | "
              "Where-Object { $_.ProcessId -ne " + str(os.getpid()) +
              " -and $_.CommandLine -match 'measure_approval_performance[.]py|run_unit_tests[.]py|profile-rc2-load[.]py' } | "
              "Select-Object -ExpandProperty ProcessId) | ConvertTo-Json -Compress")
    done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                          capture_output=True, text=True, encoding="utf-8", check=True)
    pids = json.loads(done.stdout.strip() or "[]")
    if not isinstance(pids, list): pids = [pids]
    if pids: raise RuntimeError("Isolation check failed: another benchmark/test/profile process is active: " + str(pids))
    return {"supported": True, "conflicting_pids": []}


class _MemoryCounters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [(name, ctypes.c_size_t) for name in
        ("peak", "working", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile")]


def memory():
    if sys.platform == "win32":
        counters = _MemoryCounters(); counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess
        handle.restype = ctypes.c_void_p
        get = ctypes.windll.psapi.GetProcessMemoryInfo
        get.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        if not get(handle(), ctypes.byref(counters), counters.cb): raise OSError("Cannot measure process memory")
        return {"working_set_bytes": counters.working, "process_peak_bytes": counters.peak}
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"working_set_bytes": None, "process_peak_bytes": peak * (1 if sys.platform == "darwin" else 1024)}


@contextmanager
def counters():
    import v3_contract as contract, v3_approval as approval, v3_scope as scope, v3_migration as migration
    import v2_contract, source_inventory
    counts = Counter()
    def wrapped(name, function):
        def call(*args, **kwargs):
            counts[name] += 1
            return function(*args, **kwargs)
        return call
    original_get = contract.Model.get
    def get(model, *args, **kwargs):
        counts["identity_lookups"] += 1
        if not hasattr(model, "_index_identities"): counts["identity_linear_entries"] += len(model.elements)
        return original_get(model, *args, **kwargs)
    patches = [patch.object(contract.Model, "get", get),
               patch.object(approval._Descriptors, "__init__", wrapped("descriptor_reconstructions", approval._Descriptors.__init__)),
               patch.object(approval._Descriptors, "closure", wrapped("closure_traversals", approval._Descriptors.closure)),
               patch.object(contract.Element, "digest", wrapped("element_digests", contract.Element.digest)),
               patch.object(scope, "_memberships" if hasattr(scope, "_memberships") else "memberships",
                            wrapped("membership_traversals", getattr(scope, "_memberships", scope.memberships))),
               patch.object(migration.v2, "parse_document", wrapped("original_parses", migration.v2.parse_document)),
                patch.object(migration, "read_bytes", wrapped("original_route_reads", migration.read_bytes)),
                patch.object(v2_contract, "path_at", wrapped("shared_path_checks", v2_contract.path_at)),
                patch.object(source_inventory, "read", wrapped("physical_file_reads", source_inventory.read))]
    if hasattr(contract.Model, "_index_identities"):
        original_index = contract.Model._index_identities
        def index(model):
            if model._identities is None:
                counts["identity_index_builds"] += 1
                counts["identity_index_entries"] += len(model.elements)
            return original_index(model)
        patches.append(patch.object(contract.Model, "_index_identities", index))
    from contextlib import ExitStack
    with ExitStack() as stack:
        for item in patches: stack.enter_context(item)
        yield counts


class Measurements:
    def __init__(self): self.rows = []

    def run(self, label, callback):
        from v3_contract import fingerprint
        before = memory()
        observed = [before["working_set_bytes"] or 0]
        done = threading.Event()
        def sample_memory():
            while not done.wait(0.01):
                observed.append(memory()["working_set_bytes"] or 0)
        sampler = threading.Thread(target=sample_memory, daemon=True)
        sampler.start()
        with counters() as counts:
            cpu_start = time.process_time()
            start = time.perf_counter()
            try:
                value = callback()
            finally:
                elapsed = time.perf_counter() - start
                cpu_elapsed = time.process_time() - cpu_start
                done.set(); sampler.join()
        after = memory()
        observed.append(after["working_set_bytes"] or 0)
        self.rows.append({"operation": label, "seconds": elapsed, "memory_before": before, "memory_after": memory(),
                          "sampled_peak_working_set_bytes": max(observed) or None,
                          "process_peak_growth_bytes": max(0, after["process_peak_bytes"] - before["process_peak_bytes"]),
                          "cpu_seconds": cpu_elapsed, "counts": dict(counts), "semantic_digest": fingerprint(value)})
        if PROGRESS is not None:
            with PROGRESS.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"operation": label, "seconds": elapsed, "cpu_seconds": cpu_elapsed}) + "\n")
        return value


def calculation_worker(args):
    from v3_contract import load
    from v3_scope import memberships
    from v3_approval import descriptor, approved
    from v3_context import select
    from v3_evaluation import evaluation
    readings = Measurements()
    model, tech, prop, _ = synthetic(args.workspace / "current", args.size, args.technologies)
    readings.run("load", lambda: load(model.root).require_valid().index())
    readings.run("context", lambda: select(model, [prop.uid]))
    readings.run("identities", lambda: [model.get(value).uid for e in model.elements.values() for value in (e.uid, e.id)])
    readings.run("classification", lambda: {k: sorted(v) for k, v in memberships(model).items()})
    readings.run("dependencies", lambda: descriptor(model, [tech[0].uid]))
    def evaluate_all(current_model, entries):
        with evaluation(current_model) if not args.original else nullcontext():
            return [approved(current_model, [e.uid], "technology")["valid"] or approved(current_model, [e.uid])["valid"] for e in entries]
    readings.run("current-approvals", lambda: evaluate_all(model, tech))
    old, inherited, _, _ = synthetic(args.workspace / "historical", args.size, args.technologies, historical=True)
    readings.run("historical-approvals", lambda: evaluate_all(old, inherited))
    return {"rows": readings.rows, "elements": len(model.elements), "technologies": len(tech),
            "global_rules": len(model.by_kind("rule")), "historical_elements": len(old.elements)}


def workflow_worker(args):
    import copy
    import shutil
    from test_v31_review import IntegralTests
    from test_v3_workflow import git
    from presentation_test_support import present
    from v3_contract import element, load, render, location, BLOCK
    from v3_workflow import transition, state
    from v3_verification import evidence, integrate, accept
    from v3_storage import apply
    fixture = IntegralTests(methodName="runTest")
    fixture.setUp()
    readings = Measurements()
    try:
        model = load(fixture.root)
        proposal = copy.deepcopy(model.get(fixture.prop).item())
        technologies = []
        for i in range(args.technologies):
            technologies.append(element("technology", "Synthetic technology " + str(i), "Literal synthetic technology decision " + str(i),
                                        identifier=key("workflow-technology-" + str(i)), request=fixture.req))
        extras = technologies + [element("rule", "Global rule " + str(i), "Complete synthetic global rule " + str(i),
                                        identifier=key("workflow-rule-" + str(i)), **{"global": True}) for i in range(min(24, args.size // 20))]
        for i in range(max(0, args.size - len(model.elements) - len(extras))):
            extras.append(element("feature", "Stable feature " + str(i), "Complete literal stable feature " + str(i),
                                  identifier=key("workflow-feature-" + str(i)), request=fixture.req))
        proposal["meta"]["revision"] += 1
        proposal["meta"]["relations"]["technology"] = [e["meta"]["uid"] for e in technologies]
        # Keep the large literal contract in one canonical multi-block Markdown.
        # Calculations separately measure the one-file-per-element layout. The
        # public path still loads/validates every element and all guards/sources.
        raw = b'---\nschema_version: "3.1"\nartifact_type: "specification"\n---\n\n'
        raw += b"\n".join(BLOCK.search(render(item, "3.1").decode())[0].encode() for item in extras)
        (fixture.root / "docs/lks-sdd/synthetic-volume.md").write_bytes(raw)
        (fixture.root / location(proposal)).write_bytes(render(proposal, "3.1"))
        fixture.close_proposal(); fixture.create_plan()
        trusted = args.workspace / "trusted"
        shutil.copytree(fixture.root, trusted)
        git(trusted, "symbolic-ref", "HEAD", "refs/heads/main")
        def operation(label, callback):
            packet = readings.run(label + ":prepare", callback)
            readings.run(label + ":apply", lambda: apply(fixture.root, packet, packet["preview"]["preview_hash"]))
        operation("start", lambda: present(transition, fixture.root, fixture.actor, fixture.task, "start", "Measured synthetic start"))
        (fixture.root / "app.py").write_bytes(b"def greeting(): return 'Hola'\n")
        operation("implement", lambda: present(transition, fixture.root, fixture.actor, fixture.task, "implement", "Measured synthetic implementation"))
        artifact = fixture.root / "docs/lks-sdd/evidence/input.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True); artifact.write_bytes(b"greeting passed: Hola\n")
        operation("evidence", lambda: evidence(fixture.root, fixture.actor, fixture.task, ["greeting"], "passed", "automated",
                   artifact.relative_to(fixture.root).as_posix(), "Measured synthetic proof"))
        for action in ("verify", "close"):
            operation(action, lambda action=action: present(transition, fixture.root, fixture.actor, fixture.task, action, "Measured synthetic " + action))
        operation("integrate", lambda: present(integrate, fixture.root, fixture.actor, fixture.req, trusted, "Explicit measured integration"))
        operation("accept", lambda: present(accept, fixture.root, fixture.actor, fixture.req, "Explicit measured functional acceptance"))
        final = load(fixture.root).require_valid()
        return {"rows": readings.rows, "elements": len(final.elements), "technologies": args.technologies,
                "final_state": state(final, final.get(fixture.task))}
    finally: fixture.doCleanups()


def shared_inventory_worker(args):
    from v3_contract import load
    from v3_approval import descriptor
    readings = Measurements()
    model, technologies, _, _ = synthetic(args.workspace / "shared", args.size, args.technologies)
    ref = shared_inventory_history(model)
    def reload():
        nonlocal model
        model = load(model.root).require_valid()
        return model.index()
    readings.run("shared-inventory:load", reload)
    for attempt in range(3):
        readings.run("shared-inventory:descriptor-" + str(attempt), lambda: descriptor(model, [technologies[0].uid]))
    return {"rows": readings.rows, "elements": len(model.elements), "technologies": len(technologies),
            "events": 80, "inventory_files": 6000, "unique_inventory_bytes": ref["bytes"],
            "resolved_inventory_objects": len({id(e.data["subject"]["files"]) for e in model.by_kind("execution")})}


def worker(args):
    global PROGRESS
    PROGRESS = args.progress
    from hashlib import sha256
    binding = json.loads((REFERENCE / "manifest.json").read_bytes())["files"] if args.original else {
        name: sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() for name in
        [*json.loads((REFERENCE / "manifest.json").read_bytes())["files"], "v3_evaluation.py"]}
    with runtime(args.original):
        stable_generation()
        # Same absolute fixture/staging roots in both subprocesses. This also makes
        # hashes of trusted-root guards comparable, without deleting relevant fields.
        sequence = iter(range(1000000))
        names = ("approval%09d" % i for i in sequence)
        tempfile.tempdir = str(args.workspace)
        tempfile._get_candidate_names = lambda: names
        result = {"calculations": calculation_worker, "workflow": workflow_worker,
                  "shared-inventories": shared_inventory_worker}[args.worker](args)
        result["source_binding"] = binding
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(args):
    samples, comparisons = [], []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".progress.jsonl").write_text("", encoding="utf-8")
    for size_text in args.sizes:
        size, technologies = map(int, size_text.split(":"))
        for phase in args.phases:
            for repetition in range(args.repetitions):
                pair = []
                with tempfile.TemporaryDirectory(prefix="approval-measure-") as parent:
                    order = (True, False) if args.order == "reference-first" or repetition % 2 == 0 else (False, True)
                    for original in order:
                        if args.cooldown: time.sleep(args.cooldown)
                        workspace = Path(parent) / "workspace"; workspace.mkdir()
                        output = Path(parent) / "sample.json"
                        command = [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker", phase,
                                   "--workspace", str(workspace), "--size", str(size), "--technologies", str(technologies), "--output", str(output),
                                   "--progress", str(args.output.with_suffix(".progress.jsonl").resolve())]
                        if original: command.append("--original")
                        audit_before = isolation_audit()
                        started = time.perf_counter()
                        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=args.timeout,
                                              env={**os.environ, "PYTHONHASHSEED": "0"})
                        worker_elapsed = time.perf_counter() - started
                        if done.returncode: raise RuntimeError(done.stderr[-10000:])
                        result = json.loads(output.read_bytes())
                        audit_after = isolation_audit()
                        sample = {"size": size, "technologies": technologies, "phase": phase, "repetition": repetition,
                                  "runtime": "3.4.2-reference" if original else "candidate", "worker_seconds": worker_elapsed,
                                  "isolation_audits": {"before": audit_before, "after": audit_after}, **result}
                        samples.append(sample); pair.append(sample)
                        # This is an owned, synthetic workspace under the verified temporary parent.
                        import shutil
                        if workspace.resolve().parent != Path(parent).resolve(): raise RuntimeError("Workspace escaped its temporary parent")
                        shutil.rmtree(workspace)
                        print(json.dumps({k: sample[k] for k in ("size", "phase", "repetition", "runtime", "worker_seconds")}), flush=True)
                equal = [r["semantic_digest"] for r in pair[0]["rows"]] == [r["semantic_digest"] for r in pair[1]["rows"]]
                comparisons.append({"size": size, "phase": phase, "repetition": repetition, "equivalent": equal})
                save(args, samples, comparisons)
                if not equal: raise AssertionError("Differential result differs; samples preserved in " + str(args.output))


def save(args, samples, comparisons):
    summaries = []
    for size in sorted({s["size"] for s in samples}):
        for phase in args.phases:
            rows = [s for s in samples if s["size"] == size and s["phase"] == phase]
            operations = sorted({r["operation"] for s in rows for r in s["rows"]})
            for operation in operations:
                entry = {"size": size, "phase": phase, "operation": operation}
                for runtime_name in ("3.4.2-reference", "candidate"):
                    values = [r["seconds"] for s in rows if s["runtime"] == runtime_name for r in s["rows"] if r["operation"] == operation]
                    measurements = [r for s in rows if s["runtime"] == runtime_name for r in s["rows"] if r["operation"] == operation]
                    if values:
                        entry[runtime_name] = {"samples": len(values), "median_seconds": statistics.median(values), "min_seconds": min(values), "max_seconds": max(values),
                                               "median_cpu_seconds": statistics.median(r["cpu_seconds"] for r in measurements),
                                               "max_process_peak_bytes": max(r["memory_after"]["process_peak_bytes"] for r in measurements),
                                               "max_sampled_working_set_bytes": max((r["sampled_peak_working_set_bytes"] or 0) for r in measurements),
                                               "max_process_peak_growth_bytes": max(r["process_peak_growth_bytes"] for r in measurements)}
                if "candidate" in entry and "3.4.2-reference" in entry:
                    entry["median_speedup"] = entry["3.4.2-reference"]["median_seconds"] / entry["candidate"]["median_seconds"]
                summaries.append(entry)
    manifest = json.loads((REFERENCE / "manifest.json").read_bytes())
    from hashlib import sha256
    source_files = {p.name: sha256(p.read_bytes()).hexdigest() for p in (ROOT / "scripts").glob("v3*.py")}
    report = {"format": "lks-sdd-approval-measurement/1", "reference": manifest, "candidate_source_files": source_files,
              "environment": {"python": sys.version, "platform": platform.platform()}, "repetitions": args.repetitions,
              "method": {"timer": "perf_counter; instrumentation enabled equally on both runtimes; cold subprocess per sample",
                         "order": args.order,
                         "cooldown_seconds_between_workers": args.cooldown,
                         "isolation_audit": "Windows CIM inventory before and after every worker; concurrent test/benchmark/profile runners abort the measurement",
                         "memory": "working set before/after plus 10ms sampled working-set peak; cumulative process peak and its growth per operation; samples may miss shorter spikes; not an allocation profiler",
                         "identity_entries": "counted from executed full-scan/index-build length, not an estimated complexity ratio",
                         "fixture": "calculations: up to 24 shared global rules in a chain, 5/15/35 technologies, remaining canonical features, one file per element; workflow: up to 24 independent global rules and the additional elements packed in one multi-block canonical Markdown; all literal context retained",
                         "equivalence": "PYTHONHASHSEED=0, seeded generated UUIDs/fixed generation timestamp; same absolute fixture and trusted roots; all result fields hashed canonically",
                         "scope": "public library prepare and apply with real Git, guards, staging and recoverable journal; no assistant/host token measurement",
                         "billed_tokens": None}, "comparisons": comparisons, "summaries": summaries, "samples": samples}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sizes", nargs="+", default=["100:5", "500:15", "1500:35"])
    parser.add_argument("--phases", nargs="+", choices=["calculations", "workflow", "shared-inventories"], default=["calculations", "workflow"])
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--cooldown", type=float, default=10, help="Idle seconds before cold worker processes; excluded from timings")
    parser.add_argument("--order", choices=["alternating", "reference-first"], default="alternating")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--worker", choices=["calculations", "workflow", "shared-inventories"])
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--size", type=int)
    parser.add_argument("--technologies", type=int)
    parser.add_argument("--original", action="store_true")
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args()
    worker(args) if args.worker else main(args)
