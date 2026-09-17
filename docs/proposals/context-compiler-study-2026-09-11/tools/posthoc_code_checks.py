"""New counterexamples after peer review; preserve the frozen 121-check oracle."""
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
EXPERIMENT = STUDY / "code-experiment"
NOW = datetime(2026, 9, 11, 12, 0, 0, 500000, tzinfo=timezone.utc)
VALUES = [
    ("valid-date", "Fri, 11 Sep 2026 12:00:02 GMT", 2),
    ("trailing-junk", "Fri, 11 Sep 2026 12:00:02 GMT junk GMT", None),
    ("duplicated-zone", "Fri, 11 Sep 2026 12:00:02 GMT GMT", None),
]

def main():
    rows = []
    for path in sorted(EXPERIMENT.glob("candidate-*.py")):
        spec = importlib.util.spec_from_file_location("candidate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests = []
        for name, value, expected in VALUES:
            try:
                actual = module.retry_delay(value, NOW, 100)
                tests.append({"name": name, "value": value, "expected": expected,
                              "actual": actual, "passed": actual == expected})
            except Exception as exc:
                tests.append({"name": name, "passed": False,
                              "exception": type(exc).__name__})
        rows.append({"candidate": path.name,
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "tests": tests})
    result = {"status": "posthoc-new-tests-not-part-of-frozen-oracle",
              "limitation": "Three targeted cases of one function, selected after review; not an independent benchmark.",
              "rows": rows}
    (EXPERIMENT / "posthoc-results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({r["candidate"]: sum(t["passed"] for t in r["tests"]) for r in rows}))

if __name__ == "__main__":
    main()
