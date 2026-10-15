"""Validate final source bindings and combine independently measured pairs."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def combine(calculation_reports, workflows, binding):
    calculations = calculation_reports[0]
    samples = [sample for report in calculation_reports for sample in report["samples"]]
    for repetition, report in workflows:
        for sample in report["samples"]:
            samples.append({**sample, "repetition": repetition})
    expected = {(size, phase, repetition, runtime) for size in (100, 500, 1500)
                for phase in ("calculations", "workflow") for repetition in range(3)
                for runtime in ("3.4.2-reference", "candidate")}
    actual = {(s["size"], s["phase"], s["repetition"], s["runtime"]) for s in samples}
    if actual != expected or len(samples) != len(expected): raise ValueError("Incomplete or duplicate sample matrix")
    for name, digest in binding["files"].items():
        if sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() != digest: raise ValueError("Source changed: " + name)
    for name, digest in binding.get("measurement_files", {}).items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != digest: raise ValueError("Measurement tool changed: " + name)
    for sample in samples:
        expected_binding = binding["files"] if sample["runtime"] == "candidate" else calculations["reference"]["files"]
        if sample.get("source_binding") != expected_binding: raise ValueError("Sample belongs to a different source revision")
    pairs = defaultdict(dict)
    for sample in samples: pairs[sample["size"], sample["phase"], sample["repetition"]][sample["runtime"]] = sample
    comparisons = []
    for (size, phase, repetition), pair in sorted(pairs.items()):
        old, new = pair["3.4.2-reference"], pair["candidate"]
        if [(r["operation"], r["semantic_digest"]) for r in old["rows"]] != [(r["operation"], r["semantic_digest"]) for r in new["rows"]]:
            raise ValueError("Results differ for " + str((size, phase, repetition)))
        comparisons.append({"size": size, "phase": phase, "repetition": repetition, "equivalent": True})
    summaries = []
    for size in (100, 500, 1500):
        for phase in ("calculations", "workflow"):
            selected = [s for s in samples if s["size"] == size and s["phase"] == phase]
            operations = sorted({r["operation"] for s in selected for r in s["rows"]})
            if len(operations) != (7 if phase == "calculations" else 14): raise ValueError("Missing operation")
            for operation in operations:
                row = {"size": size, "phase": phase, "operation": operation}
                for runtime in ("3.4.2-reference", "candidate"):
                    readings = [r for s in selected if s["runtime"] == runtime for r in s["rows"] if r["operation"] == operation]
                    times = [r["seconds"] for r in readings]
                    row[runtime] = {"samples": len(times), "median_seconds": statistics.median(times), "min_seconds": min(times), "max_seconds": max(times),
                                    "median_cpu_seconds": statistics.median(r["cpu_seconds"] for r in readings),
                                    "max_process_peak_bytes": max(r["memory_after"]["process_peak_bytes"] for r in readings),
                                    "counts": {key: [r["counts"].get(key, 0) for r in readings] for key in sorted({k for r in readings for k in r["counts"]})}}
                old, new = row["3.4.2-reference"], row["candidate"]
                row["median_speedup"] = old["median_seconds"] / new["median_seconds"]
                row["wall_ranges_separate"] = new["max_seconds"] < old["min_seconds"]
                summaries.append(row)
    return {"format": "lks-sdd-approval-measurement/1", "reference": calculations["reference"], "candidate_source_binding": binding,
            "environment": calculations["environment"], "repetitions": 3,
            "method": {**calculations["method"], "public_runners": "nine independent size/repetition pair runners and three calculation size runners in parallel; original then candidate within each pair; shared machine wall times",
                       "cpu": "process_time in each worker; Windows process clock has coarse resolution for very small operations",
                       "causal_attribution": "public wall-time ratios are descriptive under changing shared load, not established causal speedups; use CPU and deterministic traversal counts, plus the separate isolated alternating-order calculation run",
                       "selection": "only samples bound to the final six core modules; earlier development iterations excluded",
                       "not_measured": ["assistant billed tokens", "real consumer latency", "CLI process startup and host conversation", "human acceptance"]},
            "comparisons": comparisons, "summaries": summaries, "samples": sorted(samples, key=lambda s: (s["size"], s["phase"], s["repetition"], s["runtime"]))}


def combine_isolated(main, shared, binding):
    """Require the complete isolated rc.2 matrix and exact immutable sources."""
    samples = main["samples"] + shared["samples"]
    repetitions = main["repetitions"]
    if repetitions < 4 or repetitions % 2: raise ValueError("Expected at least four balanced isolated pairs")
    if shared["repetitions"] != repetitions: raise ValueError("Repetition count differs")
    expected = {(size, phase, rep, runtime) for size in (100, 500, 1500)
                for phase in ("calculations", "workflow") for rep in range(repetitions)
                for runtime in ("3.4.2-reference", "candidate")}
    expected |= {(1500, "shared-inventories", rep, runtime) for rep in range(repetitions)
                 for runtime in ("3.4.2-reference", "candidate")}
    actual = {(s["size"], s["phase"], s["repetition"], s["runtime"]) for s in samples}
    if actual != expected or len(samples) != len(expected): raise ValueError("Incomplete isolated matrix")
    for name, digest in binding["files"].items():
        if sha256((ROOT / "scripts" / name).read_bytes()).hexdigest() != digest: raise ValueError("Source changed: " + name)
    for report in (main, shared):
        if report["method"]["order"] != "alternating": raise ValueError("Expected alternating isolated order")
        if report["method"].get("cooldown_seconds_between_workers", 0) < 10: raise ValueError("Missing between-process idle period")
        if report["reference"] != main["reference"]: raise ValueError("Reference changed")
    groups = defaultdict(list)
    pairs = defaultdict(dict)
    for sample in samples:
        expected_binding = binding["files"] if sample["runtime"] == "candidate" else main["reference"]["files"]
        if sample.get("source_binding") != expected_binding: raise ValueError("Sample source changed")
        for stage in ("before", "after"):
            audit = sample.get("isolation_audits", {}).get(stage, {})
            if not audit.get("supported") or audit.get("conflicting_pids") != []: raise ValueError("Missing clean isolation audit")
        groups[sample["size"], sample["phase"]].append(sample)
        pairs[sample["size"], sample["phase"], sample["repetition"]][sample["runtime"]] = sample
    comparisons, summaries, operations = [], [], []
    for (size, phase, rep), pair in sorted(pairs.items()):
        old, new = pair["3.4.2-reference"], pair["candidate"]
        expected_rows = {"calculations": 7, "workflow": 14, "shared-inventories": 4}[phase]
        if len(old["rows"]) != expected_rows: raise ValueError("Missing operation")
        if [(r["operation"], r["semantic_digest"]) for r in old["rows"]] != [(r["operation"], r["semantic_digest"]) for r in new["rows"]]:
            raise ValueError("Result differs: " + str((size, phase, rep)))
        for field in ("elements", "technologies", "final_state", "resolved_inventory_objects"):
            if old.get(field) != new.get(field): raise ValueError("Fixture differs: " + field)
        comparisons.append({"size": size, "phase": phase, "repetition": rep, "equivalent": True})
    def metrics(readings):
        return {"samples": len(readings), **{key: statistics.median(r[field] for r in readings)
                for key, field in (("median_seconds", "seconds"), ("median_cpu_seconds", "cpu_seconds"))},
                "min_seconds": min(r["seconds"] for r in readings), "max_seconds": max(r["seconds"] for r in readings),
                "min_cpu_seconds": min(r["cpu_seconds"] for r in readings), "max_cpu_seconds": max(r["cpu_seconds"] for r in readings),
                "max_process_peak_bytes": max(r["memory_after"]["process_peak_bytes"] for r in readings),
                "max_sampled_working_set_bytes": max(r["sampled_peak_working_set_bytes"] or 0 for r in readings),
                "max_process_peak_growth_bytes": max(r["process_peak_growth_bytes"] for r in readings)}
    for (size, phase), group in sorted(groups.items()):
        labels = sorted({r["operation"] for s in group for r in s["rows"]})
        for label in labels:
            row = {"size": size, "phase": phase, "operation": label}
            for runtime in ("3.4.2-reference", "candidate"):
                readings = [r for s in group if s["runtime"] == runtime for r in s["rows"] if r["operation"] == label]
                row[runtime] = {**metrics(readings), "counts": {k: [r["counts"].get(k, 0) for r in readings]
                    for k in sorted({k for r in readings for k in r["counts"]})}}
            summaries.append(row)
        if phase == "workflow":
            for operation in ("start", "implement", "evidence", "verify", "close", "integrate", "accept"):
                row = {"size": size, "operation": operation}
                for runtime in ("3.4.2-reference", "candidate"):
                    totals = [{field: sum(r[field] for r in s["rows"] if r["operation"].startswith(operation + ":"))
                               for field in ("seconds", "cpu_seconds")} for s in group if s["runtime"] == runtime]
                    row[runtime] = {"median_seconds": statistics.median(v["seconds"] for v in totals),
                                    "median_cpu_seconds": statistics.median(v["cpu_seconds"] for v in totals), "samples": len(totals)}
                operations.append(row)
    return {"format": "lks-sdd-approval-isolated/2", "reference": main["reference"], "candidate_source_binding": binding,
            "environment": main["environment"], "method": {**main["method"], "public_runners": "one sequential driver; no other test or benchmark runner from this task active",
                "selection": str(len(samples)) + " samples bound to seven candidate modules and six frozen original modules",
                "not_measured": ["CLI process startup and runtime-doctor", "assistant tokens", "real consumer latency", "human acceptance"]},
            "comparisons": comparisons, "summaries": summaries, "complete_public_operations": operations, "samples": samples}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / "docs/plans/approval-performance/evidence")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--isolated", action="store_true")
    args = parser.parse_args()
    def read(name): return json.loads((args.directory / name).read_bytes())
    if args.isolated:
        report = combine_isolated(read("rc2-isolated.json"), read("rc2-shared-inventories.json"), read("rc2-source-binding.json"))
    else:
        report = combine([read(f"calculations-final-{size}.json") for size in (100, 500, 1500)],
                         [(repetition, read(f"workflow-final-{size}-{repetition}.json")) for size in (100, 500, 1500) for repetition in range(3)],
                         read("source-binding.json"))
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(report["comparisons"]), "rows": sum(len(s["rows"]) for s in report["samples"]), "equivalent": True}))
