"""Check evidence integrity; does not rerun or improve frozen experimental outcomes."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parents[1]
ROOT = S.parents[2]
checks = []

def read(rel):
    return json.loads((S / rel).read_text(encoding="utf-8"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})

def hash_check(rel, expected):
    check("sha256:" + rel, digest(S / rel) == expected)

def main():
    design = read("code-experiment/design.json")
    hash_check("code-experiment/evaluate.py", design["frozen_oracle_sha256"])
    for filename, sha in design["frozen_inputs"].items():
        hash_check("code-experiment/" + filename, sha)
    revision = read("code-experiment/revision-design.json")
    for filename, sha in revision["prompts"].items():
        hash_check("code-experiment/" + filename, sha)
    expected = {"full": (121, 12), "direct_only": (101, 5),
                "compact_complete": (114, 11), "contract_preserved": (121, 12)}
    for variant, counts in expected.items():
        result = read("code-experiment/results-candidate-" + variant + ".json")
        hash_check("code-experiment/" + result["candidate"], result["candidate_sha256"])
        check("oracle-identical:" + variant, result["oracle_sha256"] == design["frozen_oracle_sha256"])
        check("observed-outcome:" + variant,
              (result["passed"], result["all_cases_passed"]) == counts and result["total"] == 121)
        check("assertion-totals:" + variant, sum(x["passed"] for x in result["results"]) == result["passed"])
    inputs = read("cases/inputs.json")
    gold = read("cases/oracle.json")
    check("36-distinct-input-cases", len(inputs) == len({x["id"] for x in inputs}) == 36)
    check("matching-oracle-ids", {x["id"] for x in inputs} == {x["id"] for x in gold})
    check("oracle-26-ready", sum(x["expected_status"] == "ready" for x in gold) == 26)
    for version, selector in [("v1", "selection_experiment.py"), ("v2", "selection_revision.py")]:
        freeze = read("selection-experiment/freeze-" + version + ".json")
        hash_check("tools/" + selector, freeze["selector_sha256"])
        hash_check("cases/inputs.json", freeze["inputs_sha256"])
        scored = read("selection-experiment/results-" + version + ".json")
        hash_check("cases/oracle.json", scored["oracle_sha256"])
    stress = read("selection-experiment/stress-results.json")
    check("180-stress-observations", len(stress["rows"]) == 180)
    probe = read("repo-probe/results.json")
    check("6-probe-cases", probe["case_count"] == len(probe["cases"]) == 6)
    check("probe-source-integrity", not probe["source_integrity"]["changed_paths"])
    posthoc = read("code-experiment/posthoc-results.json")
    for row in posthoc["rows"]:
        hash_check("code-experiment/" + row["candidate"], row["sha256"])
        check("posthoc-outcome:" + row["candidate"],
              sum(t["passed"] for t in row["tests"]) == (3 if row["candidate"] == "candidate-full.py" else 1))
    guard = read("selection-experiment/integrity-guard-tests.json")
    check("8-guard-checks", len(guard["tests"]) == 8 and all(t["passed"] for t in guard["tests"]))
    for path in sorted((S / "tools").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            valid = True
        except SyntaxError:
            valid = False
        check("syntax:" + path.name, valid)
    for filename in ["INFORME.md", "README.md"]:
        doc = (S / filename).read_text(encoding="utf-8")
        check("unicode:" + filename, "\ufffd" not in doc)
        for target in re.findall(r"\]\(([^)]+)\)", doc):
            if not target.startswith(("https://", "http://", "#")):
                check("link:" + filename + ":" + target, (S / target.split("#")[0]).exists())
    labels = ["targeted-native", "plugin-contract", "fixture-manifest", "plugin-ingestion",
              "reference-structure", "repo-probe-confirmed", "quick-adopt", "quick-define",
              "quick-help", "quick-implement", "quick-readiness", "quick-verify"]
    for label in labels:
        check("receipt:" + label, read("evidence/" + label + ".json")["exit_code"] == 0)
    baseline = read("evidence/baseline.json")
    changed = [p for p, sha in baseline["preexisting_changed_file_sha256"].items()
               if not (ROOT / p).is_file() or digest(ROOT / p) != sha]
    git_diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    result = {"status": "evidence-consistency-not-semantic-certification", "checks": checks,
              "passed": sum(x["passed"] for x in checks), "total": len(checks),
              "git_diff_check_exit": git_diff.returncode,
              "git_diff_check_output": git_diff.stdout + git_diff.stderr,
              "preexisting_files_changed_since_baseline": changed,
              "concurrent_changes_note": "Observed drift is not attributed to this study; no restoration or mutation is performed."}
    (S / "evidence" / "study-audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}, ensure_ascii=False))
    if not all(x["passed"] for x in checks):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
