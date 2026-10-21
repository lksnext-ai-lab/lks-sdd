"""Reproducible runtime-only measurements; no billed-token or whole-agent claim."""
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import v5_core as core
from test_v5_core import fixture, put, update, FACTS


def summary(samples):
    ordered = sorted(samples)
    return {"n": len(samples), "median_seconds": statistics.median(samples),
            "maximum_seconds": max(samples), "samples_seconds": samples}


def measure():
    small, closing = [], []
    for _ in range(10):
        with tempfile.TemporaryDirectory(prefix="v5-measure-") as temporary:
            root = Path(temporary)
            start = time.perf_counter()
            fixture(root)
            core.check_task(root, "T-001", "C1")
            assert core.check_task(root, "T-001", "C1")["status"] == "reused"
            before_close = time.perf_counter()
            core.close(root, "T-001", update(root), FACTS)
            finish = time.perf_counter()
            small.append(finish - start)
            closing.append(finish - before_close)
    contexts = []
    with tempfile.TemporaryDirectory(prefix="v5-context-") as temporary:
        root = Path(temporary)
        fixture(root)
        for history in (10, 100, 1000):
            for index in range(history): put(root, f"history/task-{index}.md", "Unrelated historical source.\n" * 100)
            samples = []
            for _ in range(100):
                start = time.perf_counter()
                data = core.context(root, "T-001")
                samples.append(time.perf_counter() - start)
            contexts.append({"history_files": history, "files_read": data["files_read"], "bytes": data["bytes"],
                             "p95_observed_seconds": sorted(samples)[94], **summary(samples)})
    # Two consecutive UX-like lots in a controlled product fixture. Each lot has
    # six adjustments and a single pertinent combined test, then reuses that result.
    lots = []
    with tempfile.TemporaryDirectory(prefix="v5-lot-") as temporary:
        root = Path(temporary)
        for cycle in (1, 2):
            start = time.perf_counter()
            task_id = "UX-" + str(cycle)
            fixture(root, task_id)
            put(root, "product.py", "def normalized(value):\n    return value.strip()" + (".casefold()" if cycle == 2 else "") + "\n")
            put(root, "test_product.py", "from product import normalized\n" + "\n".join(
                f"assert normalized({value!r}) == {value.strip().casefold() if cycle == 2 else value.strip()!r}"
                for value in ("  Master ", " Company  ", "Contract", " SITE ", "", " Material ")) + "\n")
            core.check_task(root, task_id, "C1")
            assert core.check_task(root, task_id, "C1")["status"] == "reused"
            core.close(root, task_id, update(root, extra=f"Lot {cycle}: six normalized fields."), FACTS)
            lots.append({"cycle": cycle, "adjustments": 6, "executed_checks": 1, "reused_checks": 1,
                         "task_documents": 2, "seconds": time.perf_counter() - start})
    result = {"environment": {"python": sys.version, "platform": sys.platform},
              "small_flow": summary(small), "close": summary(closing), "contexts": contexts, "two_lots": lots,
              "billed_tokens": None, "cold_os_cache": "not-run", "whole_agent_overhead": "not-observed",
              "scope": "scripted runtime, known edits; not a replay of SAT's original delivery or proof of total savings"}
    output = ROOT / "tests/reports/v5-full/measurements.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(core.encode(result), encoding="utf-8")
    print(core.encode({"small": {k: v for k, v in result["small_flow"].items() if k != "samples_seconds"},
        "contexts": [{k: v for k, v in r.items() if k != "samples_seconds"} for r in contexts], "lots": lots}))


if __name__ == "__main__": measure()
