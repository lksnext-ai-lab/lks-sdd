"""Measured v2 retrieval cost; does not measure or certify model/host behavior."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time
from unittest.mock import patch

from v2_fixture import project, element, write
from v2_contract import DOCS, render_document
from query_project import query
from build_dual_distribution import collect_development
from dual_distribution import compact_distribution_core, digest, json_bytes, project_files


def measure(count, repetitions, core=None):
    with tempfile.TemporaryDirectory(prefix="lks-v2-benchmark-") as directory:
        root = Path(directory)
        project(root)
        pinned_root = None
        if core:
            for name, raw in project_files(core, "development-benchmark", "development-not-certified").items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            lock = json.loads((root / ".lks-sdd/distribution-lock.json").read_bytes())
            pinned_root = root / lock["runtime"]
        initial = len(list((root / DOCS).rglob("*.md")))
        for i in range(count - initial):
            body = f"Función Dominio{i:04}. Solo se permite la operación confirmada.\n" + "Regla documentada de alcance local.\n" * 580
            write(root, DOCS + f"/02-specification/features/FTR-{i+1000:04}/specification.md",
                  render_document("feature", f"Dominio{i:04}", [element(f"FTR-{i+1000:04}", "feature", body)]))
        sizes = [p.stat().st_size for p in (root / DOCS).rglob("*.md")]
        durations, metrics = [], []
        for i in range(repetitions):
            begin = time.perf_counter()
            if pinned_root:
                # Same current source bytes, pointed at the complete temporary
                # packaged runtime; production still requires its exact CLI.
                with patch("query_project.PLUGIN_ROOT", pinned_root):
                    result = query(root, topic=f"Dominio{i:04}", mode="docs-only")
            else:
                result = query(root, topic=f"Dominio{i:04}", mode="docs-only")
            durations.append(time.perf_counter() - begin)
            metrics.append(result["metrics"])
            assert result["fragments"] and result["metrics"]["code_files_read"] == 0
            assert not result.get("writes")
        p95 = sorted(durations)[int(repetitions * .95 + .999) - 1]
        target = 2.0 if count == 100 else 5.0
        return {"documents": len(sizes), "bytes": sum(sizes), "queries": repetitions,
                "p95_seconds": p95, "target_p95_seconds": target, "passed": p95 <= target,
                "first_seconds": durations[0], "median_seconds": statistics.median(durations),
                "durations_seconds": durations, "last_metrics": metrics[-1], "persistent_cache": False,
                "runtime_mode": "full-pinned-integrity" if core else "unmanaged"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--pinned", action="store_true", help="Include fresh full packaged-runtime integrity in every query")
    args = parser.parse_args()
    if args.repetitions < 20:
        parser.error("At least twenty queries per sample")
    results = []
    core = compact_distribution_core(collect_development(Path(__file__).resolve().parents[1])) if args.pinned else None
    for count in (100, 1000):
        print(f"Measuring v2: {count} documents", file=sys.stderr, flush=True)
        results.append(measure(count, args.repetitions, core))
    value = {"python": sys.version, "platform": platform.platform(), "results": results,
             "host_acceptance": "not-run", "agent_total_latency": "not-run", "os_cache": "uncontrolled",
             "runtime_digest": digest(json_bytes({n: digest(b) for n, b in core.items()})) if core else None}
    output = json.dumps(value, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
    print(output)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
