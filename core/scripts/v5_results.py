"""Import native test/CI results with explicit input and provenance binding."""
from __future__ import annotations
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from v5_core import (Conflict, apply, artifact, current, document, input_fingerprint,
                     read, require_authority, task_path)


def execution_time(value):
    if value is None:
        return None
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        result = float(value)
    else:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError("Execution time requires an explicit timezone")
        result = date.timestamp()
    if not 0 <= result <= time.time() + 1:
        raise ValueError("Invalid/future execution time")
    return result


def import_result(root, task_id, check_id, source, *, inputs, provider, run_id, finished_at=None):
    task_name, plan_name = task_path(task_id, "tarea"), task_path(task_id, "plan")
    task, task_body, task_hash = current(root, task_name)
    plan, body, before = current(root, plan_name)
    require_authority(task, "implement", task_body)
    check = plan["checks"][check_id]
    fingerprint = input_fingerprint(root, task_name, task, check)
    if inputs != fingerprint or provider != check.get("provider") or not run_id.strip():
        raise Conflict("Result is not bound to these inputs/provider/run")
    raw = read(root, source)
    evidence = artifact(root, source)
    native_finished = None
    if check.get("result_format") == "junit":
        if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
            raise ValueError("DTD/entity references unsupported")
        node = ET.fromstring(raw)
        if node.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Expected native JUnit result")
        cases = list(node.iter("testcase"))
        if not cases:
            raise ValueError("Empty test report is not a passing verification")
        status = "failed" if any(c.find("failure") is not None or c.find("error") is not None for c in cases) else (
            "blocked" if any(c.find("skipped") is not None for c in cases) else "passed")
        suites = list(node.iter("testsuite"))
        if suites and all(s.get("timestamp") for s in suites):
            native_finished = max(execution_time(s.get("timestamp")) + float(s.get("time", 0)) for s in suites)
    elif check.get("result_format") == "sonarqube":
        value = json.loads(raw)
        quality = value.get("projectStatus", {}).get("status")
        if quality not in {"OK", "ERROR", "NONE"}:
            raise ValueError("Missing native SonarQube projectStatus")
        status = {"OK": "passed", "ERROR": "failed", "NONE": "blocked"}[quality]
    elif check.get("result_format") == "gitlab":
        value = json.loads(raw)
        if str(value.get("id")) != run_id or value.get("sha") != check.get("commit"):
            raise ValueError("Pipeline identity/commit mismatch")
        status = {"success": "passed", "failed": "failed", "canceled": "blocked",
                  "skipped": "blocked", "manual": "blocked"}.get(value.get("status"))
        if not status:
            raise ValueError("Pipeline is not terminal; wait using the provider")
        native_finished = value.get("finished_at")
    else:
        raise ValueError("Supported formats: junit, sonarqube, gitlab")
    finished = execution_time(native_finished if native_finished is not None else finished_at)
    if finished is None and "max_age_seconds" in check:
        raise ValueError("A freshness policy requires the original execution time")
    previous = plan.get("results", {}).get(check_id)
    if previous and previous.get("inputs") == fingerprint and previous.get("run_id") == run_id and previous.get("evidence") == evidence:
        # An import cannot renew or reinterpret the age of the same execution.
        return {"status": "unchanged", "files": 0}
    plan.setdefault("results", {})[check_id] = {"status": status, "inputs": fingerprint,
        "origin": provider, "run_id": run_id, "finished": finished, "evidence": evidence,
        "provenance": "host-supplied native report; provider authenticity is a host responsibility"}
    return apply(root, {plan_name: document(plan, body)}, {plan_name: before,
        task_name: task_hash, source: evidence["sha256"]}, guards=[{
            "task": task_name, "check": check, "fingerprint": fingerprint}])


def wait_file(root, source, timeout=60, interval=1):
    """One bounded process, no model-driven polling loop. No state mutation."""
    if not 0 < timeout <= 3600 or not 0.1 <= interval <= 60:
        raise ValueError("Invalid wait bounds")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if read(root, source) is not None:
            return {"status": "available", "artifact": artifact(root, source)}
        time.sleep(min(interval, max(0, deadline - time.monotonic())))
        interval = min(interval * 1.5, 10)
    return {"status": "blocked", "reason": "External result unavailable", "retryable": True}
