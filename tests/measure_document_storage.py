"""Reproducible before/after development experiment; generates no committed fixtures.

Run from the source checkout with --output outside it. The baseline is an explicit
Git revision (default HEAD), copied into a temporary runtime without installation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def scenario(args):
    sys.path.insert(0, str(ROOT / "tests"))
    from eval_support import materialize_ready_project, authorize_implementation
    sys.path.insert(0, str(Path(args.runtime) / "scripts"))
    from v2_authoring import author, edit_elements
    from v2_contract import DOCS, load, make_element, read_bytes, render_document, sha
    from v2_controls import correction
    from v2_lifecycle import checkpoint, report_problem, start
    from v2_storage import apply, write_one
    with tempfile.TemporaryDirectory(prefix="lks-storage-scenario-") as directory:
        root = Path(directory)
        materialize_ready_project(root, "measured-synthetic")
        for i in range(args.code_files): write_one(root, f"src/stable/module-{i:05}.txt", f"code {i}\n".encode())
        links = []
        for i in range(args.resources):
            name = DOCS + f"/02-specification/features/assets/resource-{i:04}.bin"
            raw = (hashlib.sha256(str(i).encode()).digest() * ((args.resource_bytes + 31)//32))[:args.resource_bytes]
            write_one(root, name, raw)
            links.append(f"![resource {i}](assets/resource-{i:04}.bin)")
        feature_path = DOCS + "/02-specification/features/measured.md"
        entry = make_element("FTR-999", "feature", "Stable contract", "Literal stable behavior.", state="confirmed")
        request = {"documents": [{"path": feature_path, "text": render_document("feature", "Measured", [entry], preamble="\n".join(links)).decode()}]}
        for i in range(args.documents):
            request["documents"].append({"path": DOCS + f"/01-context/stable-{i:04}.md", "text": render_document("context", str(i), [], preamble=(f"Literal stable document {i}. " * 80)).decode()})
        archives, loads = [], []
        def author_write(request):
            model = load(root)
            begin = time.perf_counter()
            plan, changes = author(model, request)
            prepared = time.perf_counter() - begin
            begin = time.perf_counter()
            apply(root, changes, plan, plan["preview_hash"], validator=lambda: load(root).require_valid())
            archives.append({"operation": "author", "prepare_seconds": prepared, "apply_seconds": time.perf_counter() - begin})
        def transition(function, *pos, **kw):
            model = load(root)
            begin = time.perf_counter()
            plan = function(model, *pos, **kw)
            prepared = time.perf_counter() - begin
            begin = time.perf_counter()
            result = function(load(root), *pos, authorized_hash=plan["preview_hash"], **kw)
            if function == correction:
                archives.append({"operation": "replan" if kw.get("replan") else "correct", "prepare_seconds": prepared, "apply_seconds": time.perf_counter() - begin})
            return result
        author_write(request)
        for i in range(args.rounds):
            for step in ("before", "after"):
                if step == "before":
                    authorize_implementation(root)
                    transition(start, ["TASK-001"], "test", actor="fixture-owner", at="2026-01-02T00:00:00+00:00", technology=lambda *_: {"status": "documented"})
                    for j in range(args.checkpoints):
                        transition(checkpoint, tasks=["TASK-001"], state="paused", actor="fixture-owner", at=f"2026-01-02T00:{i:02}:{j:02}+00:00", summary=f"Observed checkpoint {i}/{j}", next_action="Resume authorized work")
                    transition(report_problem, ["TASK-001"], description=f"Observed problem {i}", actor="fixture-owner", at="2026-01-02T00:10:00+00:00")
                    transition(correction, ["TASK-001"], actor="fixture-owner", reason="Correct observed problem", at="2026-01-02T00:11:00+00:00")
                    transition(correction, ["TASK-001"], actor="fixture-owner", reason="Explicit replan", at="2026-01-02T00:12:00+00:00", replan=True)
                model = load(root)
                item = model.elements["FTR-999"]
                revised = edit_elements(model, {item.id: dict(item.meta, revision=item.meta["revision"]+1)}, {item.id: f"Literal revision {i}/{step}."})
                author_write({"documents": [{"path": feature_path, "text": revised[feature_path].decode()}]})
            begin = time.perf_counter(); load(root).require_valid(); loads.append(time.perf_counter()-begin)
        def metrics(paths):
            files = [p for p in paths if p.is_file()]
            sizes, hashes = [], set()
            for p in files:
                raw = p.read_bytes(); sizes.append(len(raw)); hashes.add(sha(raw))
            return {"files": len(files), "unique_contents": len(hashes), "bytes": sum(sizes)}
        history = root / (DOCS + "/00-control/history")
        active = [root/p for p in load(root).documents]
        retained = list(history.rglob("*")) + list((root/".lks-sdd/objects").rglob("*"))
        retained += [root/".lks-sdd/transactions.json"]
        return {"snapshot_count": len(list(history.glob("*/snapshot.json"))), "history_tree": metrics(history.rglob("*")),
                "history_and_recovery": metrics(retained), "active_markdown": metrics(active),
                "load_seconds": loads, "load_median_seconds": statistics.median(loads), "archive_operations": archives,
                "archive_prepare_total_seconds": sum(x["prepare_seconds"] for x in archives),
                "archive_apply_total_seconds": sum(x["apply_seconds"] for x in archives)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline", default="HEAD")
    parser.add_argument("--reuse-baseline-result", type=Path, help="Reuse a completed v3 baseline with the same scenario, configuration and normative contract")
    parser.add_argument("--format", choices=("v2", "v3"), default="v2")
    parser.add_argument("--runtime", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--trace-after", type=int, default=0, help=argparse.SUPPRESS)
    parser.add_argument("--documents", type=int, default=12)
    parser.add_argument("--resources", type=int, default=20)
    parser.add_argument("--resource-bytes", type=int, default=4096)
    parser.add_argument("--code-files", type=int, default=30)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--checkpoints", type=int, default=2)
    args = parser.parse_args()
    if any(getattr(args, k) < 1 for k in ("documents", "resources", "resource_bytes", "code_files", "rounds", "checkpoints")):
        parser.error("Fixture parameters must be positive")
    if args.runtime:
        if args.trace_after:
            import faulthandler
            faulthandler.dump_traceback_later(args.trace_after, repeat=True)
        if args.format == "v3":
            from measure_v3_efficiency import scenario as current_scenario
            print(json.dumps(current_scenario(args)))
        else: print(json.dumps(scenario(args)))
        return
    if not args.output: parser.error("--output is required")
    baseline = subprocess.check_output(["git", "rev-parse", args.baseline + "^{commit}"], cwd=ROOT, text=True).strip()
    reused, reuse_binding = None, None
    if args.reuse_baseline_result:
        if args.format != "v3": parser.error("Baseline reuse is supported only for the exact v3 comparison")
        raw = args.reuse_baseline_result.read_bytes()
        if len(raw) > 16*1024*1024: parser.error("Baseline evidence exceeds budget")
        prior = json.loads(raw)
        resolved = subprocess.check_output(["git", "rev-parse", prior["baseline_commit"] + "^{commit}"], cwd=ROOT, text=True).strip()
        configuration = {k: getattr(args, k) for k in ("documents", "resources", "resource_bytes", "code_files", "rounds", "checkpoints")}
        generators = ("tests/measure_v3_efficiency.py", "tests/presentation_test_support.py")
        if (prior["format"] != "v3" or resolved != baseline or prior["configuration"] != configuration
                or any(prior["after_source_hashes"].get(n) != hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in generators)):
            parser.error("Baseline source, configuration or scenario differs")
        reused = prior["results"]["before"]
        reuse_binding = {"evidence_sha256": hashlib.sha256(raw).hexdigest(), "resolved_commit": resolved,
                         "generator_hashes": {n: prior["after_source_hashes"][n] for n in generators},
                         "fixture_source_hashes": {n: prior["after_source_hashes"][n] for n in ("tests/test_v31_review.py", "tests/test_v3_workflow.py")},
                         "limitation": "Baseline timings were recorded earlier; final comparison must retain the complete normative digest and operation counts"}
    with tempfile.TemporaryDirectory(prefix="lks-storage-baseline-") as directory, tempfile.TemporaryDirectory(prefix="lks-storage-source-") as after_directory:
        old = Path(directory)
        after = Path(after_directory)
        names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", baseline, "scripts", "schemas", ".codex-plugin", "distribution"], cwd=ROOT, text=True).splitlines()
        for name in names:
            target = old/name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(["git", "show", baseline + ":" + name], cwd=ROOT))
        # Bind measurements to immutable temporary inputs, not to a moving checkout.
        names = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "scripts", "schemas", ".codex-plugin", "distribution"], cwd=ROOT).decode("utf-8").split("\0")
        names = sorted(set(filter(None, names)) | {"tests/measure_document_storage.py", "tests/measure_v3_efficiency.py", "tests/eval_support.py", "tests/test_v31_review.py", "tests/test_v3_workflow.py"})
        if (ROOT/"tests/presentation_test_support.py").exists(): names.append("tests/presentation_test_support.py")
        # Current decision guards resolve instruction resources from their own
        # frozen runtime, never from the live checkout or an installed plugin.
        for name in ("docs/V3-COMMON.md", "docs/USER-DECISIONS.md"):
            if (ROOT/name).exists(): names.append(name)
        names += [p.relative_to(ROOT).as_posix() for p in (ROOT/"docs/decision-guides").glob("*.md")]
        sources = {}
        for name in names:
            raw = (ROOT/name).read_bytes()
            target = after/name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            sources[name] = hashlib.sha256(raw).hexdigest()
        if any(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != digest for name, digest in sources.items()):
            raise RuntimeError("Checkout changed while freezing the measurement runtime")
        results = {}
        for label, runtime in (("before", old), ("after", after)):
            if label == "before" and reused is not None:
                results[label] = reused
                print("before reused (source-bound evidence)", flush=True)
                continue
            command = [sys.executable, "-B", "-X", "utf8", str(after/"tests/measure_document_storage.py"), "--runtime", str(runtime)]
            command += ["--format", args.format]
            for key in ("documents", "resources", "resource_bytes", "code_files", "rounds", "checkpoints"):
                command += ["--"+key.replace("_", "-"), str(getattr(args, key))]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            if result.returncode:
                raise RuntimeError(label + " scenario failed:\n" + result.stderr)
            results[label] = json.loads(result.stdout)
            print(label + " completed", flush=True)
        if args.format == "v3" and results["before"]["normative_digest"] != results["after"]["normative_digest"]:
            raise RuntimeError("The compared normative contracts differ; reject the measurement")
        if args.format == "v3" and any(results["before"][k] != results["after"][k] for k in ("operation_count", "archival_operations")):
            raise RuntimeError("The compared operation scopes differ; reject the measurement")
    evidence = {"baseline_commit": baseline, "format": args.format, "after_source_hashes": sources, "configuration": {k: getattr(args, k) for k in ("documents", "resources", "resource_bytes", "code_files", "rounds", "checkpoints")},
                "results": results, "limitations": ["Synthetic local Windows experiment; timings include filesystem, fsync and staging costs", "No host acceptance or consumer migration executed", "Logical byte counts exclude filesystem allocation and Git object sharing"]}
    if reuse_binding: evidence["baseline_reuse"] = reuse_binding
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "baseline_commit": baseline, "format": args.format,
                      "results": {label: {k: v for k, v in result.items() if k not in
                                   {"operations", "archive_operations", "shared_subject_inventory_hashes"}}
                                  for label, result in results.items()}}, ensure_ascii=False))


if __name__ == "__main__": main()
