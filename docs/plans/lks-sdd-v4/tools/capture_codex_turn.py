"""Read numeric Codex usage for one completed turn; no transcript export.

V4-02 measurement aid only. The local log shape is observed, not a stable public
API. Missing fields, conflicting duplicates or incomplete accounting are errors.
"""
import argparse
import hashlib
import json
from pathlib import Path


FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
          "output_tokens", "reasoning_output_tokens", "total_tokens")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() == args.log.resolve():
        raise ValueError("Choose a new output file distinct from the source log")
    snapshot = args.log.read_bytes()
    observations, contexts, boundaries = {}, [], {}
    latest_counter = None
    duplicates = 0
    for line in snapshot.splitlines():
        row = json.loads(line)
        payload = row.get("payload", {})
        if payload.get("turn_id") != args.turn_id:
            continue
        if row.get("type") == "turn_context":
            contexts.append({key: payload.get(key) for key in ("model", "effort")})
        if row.get("type") == "event_msg" and payload.get("type") in {"task_started", "task_complete"}:
            boundaries[payload["type"]] = {key: payload.get(key) for key in
                ("started_at", "completed_at", "duration_ms")}
        if row.get("type") != "token_usage_record":
            continue
        response = payload["response_id"]
        usage = payload["usage"]
        if any(type(usage.get(key)) is not int or usage[key] < 0 for key in FIELDS):
            raise ValueError("Absent, invalid or changed token categories")
        if usage["input_tokens"] + usage["output_tokens"] != usage["total_tokens"]:
            raise ValueError("Unexpected total-token accounting")
        if usage["cached_input_tokens"] > usage["input_tokens"] or usage["reasoning_output_tokens"] > usage["output_tokens"]:
            raise ValueError("Unexpected subset accounting")
        if response in observations:
            if observations[response] != usage:
                raise ValueError("Conflicting duplicate response; investigate instead of summing")
            duplicates += 1
        observations[response] = usage
        latest_counter = payload["turn_token_usage"]
    if not observations or not contexts or not {"task_started", "task_complete"} <= boundaries.keys():
        raise ValueError("Missing usage, model context, or completed-turn boundaries")
    totals = {key: sum(value[key] for value in observations.values()) for key in FIELDS}
    if totals != {key: latest_counter[key] for key in FIELDS}:
        raise ValueError("Response sum does not match final turn counter")
    models = sorted({value["model"] for value in contexts})
    efforts = sorted({value["effort"] for value in contexts})
    if len(models) != 1 or len(efforts) != 1 or not models[0] or not efforts[0]:
        raise ValueError("Model/configuration unavailable or changed within turn")
    selected = json.dumps(observations, sort_keys=True, separators=(",", ":")).encode()
    result = {"scope": "completed Codex turn; not automatically one functional scenario",
        "turn_id": args.turn_id, "status": "validated-closed-turn-attribution",
        "model": models[0], "effort": efforts[0], "boundaries": boundaries,
        "unique_responses": len(observations), "duplicates_not_counted_twice": duplicates,
        "usage": totals, "sum_matches_final_turn_counter": True,
        "selected_usage_sha256": hashlib.sha256(selected).hexdigest(),
        "source_snapshot_sha256": hashlib.sha256(snapshot).hexdigest(),
        "transcript_exported": False, "functional_scenario_tokens": None, "invoice_cost": None,
        "limitations": ["Observed internal log format; recheck availability before each campaign",
            "Cached input and reasoning output are subsets, not extra tokens to add",
            "Turn wall time is not human active time",
            "A case spanning multiple turns needs an explicit manifest of completed turn IDs",
            "Whole-scenario comparison still needs equivalent initial context and case boundaries"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"status": result["status"], "unique_responses": len(observations),
        "sum_matches_final_turn_counter": True, "transcript_exported": False,
        "functional_scenario_tokens": None, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
