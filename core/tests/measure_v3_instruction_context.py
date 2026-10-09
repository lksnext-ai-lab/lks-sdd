"""One-shot instruction measurement; no host telemetry or consumer mutations."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from v3_decision_profiles import PROFILES, profiles, instruction_refs
from v3_contract import sha

SCENARIOS = [
    ("consulta", "help", "status", {}),
    ("especificación", "define", "review", {}),
    ("plan y encargos", "define", "authorize-plan", {"review_tasks": ["synthetic-task"]}),
    ("relevo e inicio", "implement", "resume", {"offer": "synthetic-offer", "review": True}),
    ("integración y aceptación", "verify", "integrate", {"accept_result": True}),
    ("rechazo", "verify", "reject-result", {}),
    ("excepción", "implement", "exception", {}),
    ("migración", "adopt-existing", "migration-preview", {}),
    ("dirección visual", "define", "visual-choice", {}),
    ("aclaración", "define", "clarify", {}),
    ("corrección comprobada", "verify", "resolve-defect", {}),
    ("continuación tras compactación", "implement", "start", {}),
]


def count(root, paths):
    entries = []
    for name in dict.fromkeys(paths):
        data = (root / name).read_bytes(); text = data.decode("utf-8").replace("\r\n", "\n")
        entries.append({"path": name, "sha256": sha(data), "characters": len(text), "words": len(text.split())})
    return {"characters": sum(e["characters"] for e in entries), "reads": len(entries), "files": entries}


def measure(baseline=None):
    guides = ["docs/decision-guides/" + group + ".md" for group in sorted({p[0] for p in PROFILES.values()} - {None})]
    rows = []
    for name, skill, event, data in SCENARIOS:
        entry = ["skills/lks-sdd-" + skill + "/SKILL.md", "skills/lks-sdd-" + skill + "/references/v3.md"]
        selection = profiles(event, data)
        references = [r["path"] for r in instruction_refs(selection)]
        if event in {"status", "start"}: references = ["docs/V3-COMMON.md"]
        chosen = count(ROOT, entry + references)
        full = count(ROOT, entry + ["docs/V3-COMMON.md", "docs/USER-DECISIONS.md"] + guides)
        row = {"scenario": name, "event": event, "selected": chosen, "same_functionality_all_guides": full,
               "character_reduction_percent": round(100 * (1 - chosen["characters"] / full["characters"]), 2)}
        if baseline:
            row["previous_functionality"] = count(Path(baseline), entry + ["docs/V3-COMMON.md", "docs/V31-REVIEW.md"])
        rows.append(row)
    return {"measurement": "static-instruction-routes; UTF-8 normalized LF characters", "scenarios": rows,
            "billed_tokens": None, "observed_host_tokens": None, "whole_task_latency": None,
            "agent_error_reduction": "not-measured", "consumer_writes": [],
            "limitations": "Reading counts describe selected resources, not actual host/tool reads. Full-task and semantic observations are separate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path); parser.add_argument("--output", type=Path)
    args = parser.parse_args(); result = measure(args.baseline)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scenarios": len(result["scenarios"]), "reductions_percent": {r["scenario"]: r["character_reduction_percent"] for r in result["scenarios"]}, "billed_tokens": None}, ensure_ascii=False))
