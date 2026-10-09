"""The same v3.1 contract against frozen/current libraries; synthetic temporary data only."""
import copy
import ctypes
import json
from pathlib import Path
import statistics
import sys
import time
import uuid


def scenario(args):
    sys.path.insert(0, str(Path(args.runtime)/"scripts"))
    import v3_contract
    sequence = iter(range(1000000))
    uuid.uuid4 = lambda: uuid.uuid5(uuid.NAMESPACE_OID, "v3-efficiency-" + str(next(sequence)))
    # Additional operational receipts must not shift canonical fixture identities.
    element_counts = {}
    original_element = v3_contract.element
    def stable_element(kind, title, body, **data):
        if data.get("identifier") is None:
            if kind in v3_contract.NORMATIVE:
                # A read-only presentation may construct a discarded draft policy.
                # Bind the actual canonical identity to its complete fixture content.
                key = json.dumps([kind, title, body, data], sort_keys=True)
            else:
                number = element_counts.get(kind, 0); element_counts[kind] = number+1
                key = f"{kind}-{number}"
            data["identifier"] = str(uuid.uuid5(uuid.NAMESPACE_OID, "v3-efficiency-" + key))
        return original_element(kind, title, body, **data)
    v3_contract.element = stable_element
    v3_contract.now = lambda: "2026-01-01T00:00:00+00:00"
    from presentation_test_support import present
    from test_v31_review import IntegralTests
    from test_v3_workflow import commit_packet
    from v3_authoring import author, approve_and_authorize
    from v3_lifecycle import checkpoint
    from v3_storage import apply
    from v3_contract import DOCS, NORMATIVE, element, render, load, sha, fingerprint, canonical, document_paths
    fixture = IntegralTests(methodName="runTest")
    fixture.setUp()
    root = fixture.root
    operations, loads = [], []

    def metrics(paths):
        count, size, unique = 0, 0, set()
        for path in paths:
            if path.is_file():
                raw = path.read_bytes(); count += 1; size += len(raw); unique.add(sha(raw))
        return {"files": count, "bytes": size, "unique_contents": len(unique)}

    def stored(): return metrics([*(root/DOCS).rglob("*"), *(root/".lks-sdd").rglob("*")])

    def operation(label, callback, *, counted=False):
        start = time.perf_counter(); packet = callback(); prepared = time.perf_counter()-start
        full_bytes = len(canonical(packet))
        shown_bytes = len(canonical({"preview_hash": packet["preview"]["preview_hash"], "summary": packet["summary"]}))
        start = time.perf_counter(); apply(root, packet, packet["preview"]["preview_hash"]); applied = time.perf_counter()-start
        operations.append({"operation": label, "archival_comparison": counted, "prepare_seconds": prepared, "apply_seconds": applied,
                           "full_packet_json_bytes": full_bytes, "compact_preview_bytes": shown_bytes})

    try:
        for i in range(args.code_files):
            name = root/("src/" + "component-"*5 + f"{i:05}.py")
            name.parent.mkdir(parents=True, exist_ok=True); name.write_bytes(f"value = {i}\n".encode())
        (root/"app.py").write_bytes(b"def greeting(): return 'Hola'\n")
        proposal = copy.deepcopy(load(root).get(fixture.prop).item())
        proposal["meta"]["revision"] += 1; proposal["meta"]["data"]["included"] = ["src", "app.py"]
        commit_packet(root, present(author, root, fixture.actor, [proposal]))
        # The reported incident copied many unchanged, unrelated functional sources.
        # Keep every source canonical and globally validated, without inventing 800
        # additional obligations for the measured small task. Global closure work is
        # exercised separately by test_global_approval_checks_all_content_without_quadratic_digest_work.
        for i in range(args.documents):
            item = element("feature", f"Stable source {i}", "Literal stable functional source " + str(i) + ": " + "unchanged "*20,
                           request=fixture.req)
            item["meta"].update(state="confirmed", nature="decision")
            path = root/DOCS/"elements"/(item["meta"]["uid"] + ".md")
            path.write_bytes(render(item, "3.1"))
        for i in range(args.resources):
            path = root/DOCS/"assets"/f"resource-{i:04}.bin"
            path.parent.mkdir(parents=True, exist_ok=True)
            seed = ("stable API/image resource " + str(i%5)).encode()
            path.write_bytes((seed*((args.resource_bytes//len(seed))+1))[:args.resource_bytes])
        fixture.close_proposal(); fixture.create_plan()
        task = copy.deepcopy(load(root).get(fixture.task).item())
        task["meta"]["revision"] += 1; task["meta"]["data"]["scope"] = ["src", "app.py"]
        commit_packet(root, present(author, root, fixture.actor, [task]))
        commit_packet(root, present(approve_and_authorize, root, fixture.actor, fixture.plan_id, "Explicit measured scope and authority", review_tasks=[fixture.task]))
        initial = stored()
        item = element("feature", "Measured changing source", "Literal initial feature", request=fixture.req)
        operation("author-initial", lambda: present(author, root, fixture.actor, [item]), counted=True)
        from v3_workflow import transition
        operation("start", lambda: transition(root, fixture.actor, fixture.task, "start", "Explicit measured execution"))
        for i in range(args.rounds):
            for step in ("before", "after"):
                changed = copy.deepcopy(load(root).get(item["meta"]["uid"]).item())
                changed["meta"]["revision"] += 1; changed["body"] = f"Literal source revision {i}/{step}"
                operation("author-" + step, lambda: present(author, root, fixture.actor, [changed]), counted=True)
                if step == "before":
                    for j in range(args.checkpoints):
                        operation("checkpoint", lambda j=j: checkpoint(root, fixture.actor, fixture.task, f"Distinct observation {i}/{j}", ["Continue current authorized task"]))
                    operation("correction-observation", lambda: checkpoint(root, fixture.actor, fixture.task, f"Distinct correction fact {i}", ["Retain full contract"], classification="correction"), counted=True)
                    plan = copy.deepcopy(load(root).get(fixture.plan_id).item()); plan["meta"]["revision"] += 1
                    plan["body"] += f"\nExplicit revised sequencing {i}; preserve task scope."
                    operation("author-replan", lambda: present(author, root, fixture.actor, [plan]), counted=True)
                    operation("authorize-replan", lambda: present(approve_and_authorize, root, fixture.actor, fixture.plan_id,
                              "Explicitly approve and authorize this exact revised plan", review_tasks=[fixture.task]))
            start = time.perf_counter(); load(root).require_valid(); loads.append(time.perf_counter()-start)
        final = stored(); model = load(root).require_valid()
        active = metrics(root/p for p in document_paths(root))
        history = metrics((root/(DOCS+"/00-control/history")).rglob("*"))
        normalized = {e.uid: e.normative() for e in model.elements.values() if e.kind in NORMATIVE}
        normalized_digest = fingerprint(normalized)
        reference_hashes = {e.meta["data"]["subject"]["files_ref"]["sha256"] for e in model.elements.values()
                            if isinstance(e.meta["data"].get("subject"), dict) and "files_ref" in e.meta["data"]["subject"]}
        peak = None
        if sys.platform == "win32":
            class Counters(ctypes.Structure):
                _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [(n, ctypes.c_size_t) for n in
                    ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
            counters = Counters(); counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess
            handle.restype = ctypes.c_void_p
            get = ctypes.windll.psapi.GetProcessMemoryInfo
            get.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            if get(handle(), ctypes.byref(counters), counters.cb): peak = counters.PeakWorkingSetSize
        return {"format": "3.1", "normative_digest": normalized_digest, "archival_operations": sum(o["archival_comparison"] for o in operations),
                "operation_count": len(operations), "initial_storage": initial, "final_storage": final,
                "growth": {k: final[k]-initial[k] for k in final}, "active_markdown": active, "history_tree": history,
                "shared_subject_inventory_hashes": sorted(reference_hashes), "load_seconds": loads, "load_median_seconds": statistics.median(loads),
                "peak_working_set_bytes": peak, "operations": operations, "prepare_total_seconds": sum(o["prepare_seconds"] for o in operations),
                "apply_total_seconds": sum(o["apply_seconds"] for o in operations), "billed_tokens": None}
    finally: fixture.doCleanups()


def migration_cost():
    """One small explicit cutover, including runtime and recoverable interruption."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
    from test_v3_efficiency import EfficiencyTests
    from v3_migration import source_model
    from v3_cli import execute
    from v3_contract import element, document_paths, load, canonical
    from v3_storage import prepare, apply, recover
    from v2_contract import document_paths as old_paths
    test = EfficiencyTests(methodName="runTest")
    EfficiencyTests.setUpClass()
    test.setUp()
    try:
        test.old()
        root = test.root
        old_bytes = sum((root/p).stat().st_size for p in old_paths(root))
        readings = {}
        for normalized in (False, True):
            values = []
            for _ in range(3):
                start = time.perf_counter(); model = source_model(root, normalize=normalized)
                values.append(time.perf_counter()-start)
                if normalized: model.inventory_temporary.cleanup()
            readings["normalized" if normalized else "normal"] = {"seconds": values, "median_seconds": statistics.median(values)}
        start = time.perf_counter(); diagnostic = execute("migration-diagnose", root, {})
        diagnose_seconds = time.perf_counter()-start
        start = time.perf_counter(); packet = test.migration(packet_directory=str(Path(test.temp.name)/"cutover"))
        prepare_seconds = time.perf_counter()-start
        descriptor_bytes = len(canonical(packet))
        start = time.perf_counter(); apply(root, packet, packet["preview"]["preview_hash"], current=True)
        apply_seconds = time.perf_counter()-start
        packet = prepare(root, [element("receipt", "Observed recovery", "Distinct synthetic interruption and recovered result")], "measured-recovery")
        start = time.perf_counter()
        try: apply(root, packet, packet["preview"]["preview_hash"], current=True, interrupt_after=2)
        except InterruptedError: pass
        else: raise AssertionError("Expected a recoverable interruption")
        interrupted_seconds = time.perf_counter()-start
        start = time.perf_counter(); recover(root, packet["preview"]["preview_hash"])
        recovery_seconds = time.perf_counter()-start
        load(root).require_valid()
        lock = json.loads((root/".lks-sdd/distribution-lock.json").read_bytes())
        return {"source": "synthetic initialized v2.3.1, without existing lock/history/tasks", "repetitions": 3,
                "runtime_digest": lock["runtime_digest"], "source_active_markdown_bytes": old_bytes,
                "target_active_markdown_bytes": sum((root/p).stat().st_size for p in document_paths(root)),
                "source_load": readings, "diagnose_seconds": diagnose_seconds,
                "diagnostic_bytes": len(canonical(diagnostic)), "descriptor_bytes": descriptor_bytes,
                "prepare_seconds": prepare_seconds, "apply_seconds": apply_seconds,
                "interrupted_apply_seconds": interrupted_seconds, "recovery_seconds": recovery_seconds,
                "runtime_bytes": sum((root/lock["runtime"]/p).stat().st_size for p in lock["runtime_files"]),
                "limitations": ["Single small cutover; does not extrapolate large migration latency", "Generated runtime in temporary fixture only; no consumer or personal installation", "Recovery timing is storage recovery, not renewal of task authority"]}
    finally:
        test.doCleanups(); EfficiencyTests.tearDownClass()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Measure small current-method migration and recovery; temporary fixtures only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = migration_cost()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
