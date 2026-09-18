"""Temporary synthetic retrieval benchmark; not assistant latency or host acceptance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from query_project import query


def run(count: int, repetitions: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="lks-query-bench-") as directory:
        root = Path(directory)
        docs = root / "docs"
        docs.mkdir()
        for index in range(count):
            body = f"# Dominio{index:04}\n\nRegla particular del dominio.\n" + "Contexto documental de referencia.\n" * 620
            (docs / f"documento-{index:04}.md").write_text(body, encoding="utf-8")
        total = sum(p.stat().st_size for p in docs.iterdir())
        durations, metrics = [], []
        for index in range(repetitions):
            start = time.perf_counter()
            result = query(root, topic=f"Dominio{index % count:04}")
            durations.append(time.perf_counter() - start)
            metrics.append(result["metrics"])
            assert result["metrics"]["code_files_read"] == 0 and result["fragments"]
        ordered = sorted(durations)
        p95 = ordered[max(0, int(len(ordered) * .95 + .999) - 1)]
        target = 2.0 if count <= 100 else 5.0
        return {"documents": count, "bytes": total, "queries": repetitions,
                "first_seconds": round(durations[0], 4), "median_seconds": round(statistics.median(durations), 4),
                "p95_seconds": round(p95, 4), "max_seconds": round(max(durations), 4),
                "target_p95_seconds": target, "passed": p95 <= target,
                "durations_seconds": [round(value, 4) for value in durations],
                "phase_p95_seconds": {key: round(sorted(m[key] for m in metrics)[max(0, int(len(metrics) * .95 + .999) - 1)], 4)
                                      for key in ("runtime_seconds", "document_seconds", "code_seconds", "revalidation_seconds")},
                "last_metrics": metrics[-1], "cache": "no-persistent-cache; OS cache uncontrolled"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    if args.repetitions < 20:
        parser.error("At least 20 representative queries per size are required")
    results = []
    for count in (100, 1000):
        print(f"Benchmark {count} documents / {args.repetitions} queries", file=sys.stderr, flush=True)
        results.append(run(count, args.repetitions))
    payload = {"python": sys.version, "platform": platform.platform(), "results": results,
               "assistant_latency": "not-run", "human_acceptance": "not-run"}
    text = json.dumps(payload, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as stream:
            stream.write(text + "\n")
    print(text)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
