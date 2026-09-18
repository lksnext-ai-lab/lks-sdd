"""Validate plan-to-code-to-test traceability without inventing semantic acceptance."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def audit(reports=()):
    matrix = json.loads((ROOT / "quality/v2-traceability.json").read_text(encoding="utf-8"))
    plan = (ROOT / "docs/plans/2026-09-18-lks-sdd-v2-coverage.md").read_text(encoding="utf-8")
    errors, observations, report_hashes = [], {}, {}
    for report in reports:
        raw = Path(report).read_bytes()
        value = json.loads(raw)
        report_hashes[Path(report).name] = hashlib.sha256(raw).hexdigest()
        for result in value.get("results", []):
            parts = result["id"].split(".")
            observations[parts[0] + "." + parts[-1]] = result["status"]
    expected_requirements = {f"R{i:03}" for i in range(1, 68)}
    expected_scenarios = {f"C{i:03}" for i in range(1, 61)}
    if {r["id"] for r in matrix["requirements"]} != expected_requirements or len(matrix["requirements"]) != 67:
        errors.append("Requirement inventory differs from the approved 67-item plan")
    if {c["id"] for c in matrix["scenarios"]} != expected_scenarios or len(matrix["scenarios"]) != 60:
        errors.append("Scenario inventory differs from the approved 60-family plan")
    tasks = set()
    for row in matrix["requirements"]:
        source = next((line for line in plan.splitlines() if line.startswith("| " + row["id"] + " |")), "")
        if set(re.findall(r"C\d{3}", source)) != set(row["scenarios"]):
            errors.append(row["id"] + ": scenario mapping drift")
        if set(re.findall(r"T\d{3}", source)) != {row["primary_task"], *row["contributors"]}:
            errors.append(row["id"] + ": task mapping drift")
        tasks.update([row["primary_task"], *row["contributors"]])
    if tasks != {f"T{i:03}" for i in range(1, 49)}:
        errors.append("Task inventory differs from the approved 48-item plan")
    source_hashes, tests = {}, {}
    scenarios = []
    for row in matrix["scenarios"]:
        for source in row["code"]:
            path = ROOT / source
            if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
                errors.append(row["id"] + ": missing implementation " + source)
            else:
                source_hashes[source] = hashlib.sha256(path.read_bytes()).hexdigest()
        states = {}
        for reference in row["tests"]:
            module, name = reference.split(".")
            path = ROOT / "tests" / (module + ".py")
            if module not in tests:
                tests[module] = {n.name for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))) if isinstance(n, ast.FunctionDef)}
            if name not in tests[module]:
                errors.append(row["id"] + ": missing test " + reference)
            states[reference] = observations.get(reference, "not-run")
        scenarios.append({"id": row["id"], "tests": states, "automatic_contract_checks":
            "passed" if states and set(states.values()) == {"passed"} else "incomplete",
            "semantic_or_host_acceptance": "not-run", "whole_family_acceptance": "not-claimed"})
    return {"kind": "development-traceability-audit-not-release-attestation", "status": "valid" if not errors else "invalid",
            "counts": {"requirements": len(matrix["requirements"]), "tasks": len(tasks), "scenario_families": len(scenarios)},
            "errors": errors, "source_hashes": source_hashes, "report_hashes": report_hashes, "scenarios": scenarios,
            "limitations": ["A named passing test does not prove all semantic obligations in a family",
                            "Real hosts, human comprehension, model cost and external enforcement remain separate"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="append", default=[], type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    value = audit(args.report)
    output = json.dumps(value, ensure_ascii=False, indent=2)
    if args.json_out:
        with args.json_out.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
    print(output)
    raise SystemExit(0 if value["status"] == "valid" else 1)
