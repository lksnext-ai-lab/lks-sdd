"""Informed revision generated only from prompt-contract_preserved.md."""

from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
from email.utils import parsedate_to_datetime
import hashlib
import heapq
import hmac
import json
import math
import re
from zoneinfo import ZoneInfo


def ledger_total(amounts):
    if not amounts:
        return "0.00"
    numbers = [Decimal(value) for value in amounts]
    precision = max(
        28,
        max(len(value.as_tuple().digits) + max(value.as_tuple().exponent, 0)
            for value in numbers) + len(str(len(numbers))) + 4,
    )
    with localcontext() as context:
        context.prec = precision
        total = sum(
            (value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
             for value in numbers),
            Decimal("0.00"),
        )
        return "0.00" if total == 0 else format(total, ".2f")


def local_day_ids(events, day, tz):
    target_day = date.fromisoformat(day)
    zone = ZoneInfo(tz)
    result = []
    for event in events:
        instant = datetime.fromisoformat(event["timestamp"])
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("timestamp must carry an offset")
        if instant.astimezone(zone).date() == target_day:
            result.append(deepcopy(event["id"]))
    return result


def fold_events(events):
    seen_events = {}
    seen_sequences = set()
    winners = {}
    for event in events:
        event_identity = (event["tenant"], event["event_id"])
        if event_identity in seen_events:
            if seen_events[event_identity] != event:
                raise ValueError("conflicting event identity")
            continue
        seen_events[event_identity] = event
        sequence_identity = (event["tenant"], event["key"], event["seq"])
        if sequence_identity in seen_sequences:
            raise ValueError("conflicting sequence")
        seen_sequences.add(sequence_identity)
        group = (event["tenant"], event["key"])
        if group not in winners or event["seq"] > winners[group]["seq"]:
            winners[group] = event
    return {group: deepcopy(event["value"])
            for group, event in winners.items() if not event["deleted"]}


def can_read(user, resource):
    if (user["disabled"]
            or user["tenant"] != resource["tenant"]
            or user["id"] in resource["denied_user_ids"]):
        return False
    return bool(
        "admin" in user["roles"]
        or resource["owner_id"] == user["id"]
        or resource["public"]
    )


def merge_patch(document, patch):
    if not isinstance(patch, dict):
        return deepcopy(patch)
    result = deepcopy(document) if isinstance(document, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge_patch(result.get(key), value)
    return result


def page_after(rows, cursor, limit):
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    if limit == 0:
        return []
    ordered = sorted(rows, key=lambda row: (row["ts"], row["id"]))
    selected = [row for row in ordered
                if cursor is None or (row["ts"], row["id"]) > cursor]
    return deepcopy(selected[:limit])


def retry_delay(value, now, cap):
    if value is None:
        return None
    value = value.strip()
    if re.fullmatch(r"[0-9]+", value):
        digits = value.lstrip("0") or "0"
        cap_text = str(cap)
        if len(digits) > len(cap_text):
            return cap
        return min(int(digits), cap)
    # A date must explicitly specify GMT; now is supplied as aware UTC.
    if not value.endswith(" GMT"):
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            return None
        seconds = math.ceil((parsed - now).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None
    return min(cap, max(0, seconds))


def csv_cell(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    trimmed = value.lstrip(" \t\r\n")
    if trimmed and trimmed[0] in "=+-@":
        return "'" + value
    return value


def migration_order(steps, applied):
    by_id = {}
    for step in steps:
        step_id = step["id"]
        if step_id in by_id:
            raise ValueError("duplicate migration ID")
        by_id[step_id] = step
    applied_ids = set(applied)
    known_ids = set(by_id)
    pending = known_ids - applied_ids
    predecessors = {}
    successors = {step_id: set() for step_id in pending}
    for step_id in pending:
        dependencies = set(by_id[step_id]["depends_on"])
        if dependencies - known_ids - applied_ids:
            raise ValueError("unknown migration dependency")
        predecessors[step_id] = dependencies & pending
        for dependency in predecessors[step_id]:
            successors[dependency].add(step_id)
    ready = [step_id for step_id in pending if not predecessors[step_id]]
    heapq.heapify(ready)
    result = []
    while ready:
        step_id = heapq.heappop(ready)
        result.append(step_id)
        for dependent in successors[step_id]:
            predecessors[dependent].remove(step_id)
            if not predecessors[dependent]:
                heapq.heappush(ready, dependent)
    if len(result) != len(pending):
        raise ValueError("migration dependency cycle")
    return result


def cache_key(tenant, user, scopes):
    return json.dumps(
        [tenant, user, sorted(set(scopes))],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def update_record(record, expected_version, changes):
    if expected_version != record["version"]:
        raise RuntimeError("version conflict")
    if {"id", "tenant", "version"}.intersection(changes):
        raise ValueError("immutable field in changes")
    result = deepcopy(record)
    if changes:
        result.update(deepcopy(changes))
        result["version"] = record["version"] + 1
    return result


def verify_signature(body, signature, timestamp, now, secret):
    if not re.fullmatch(r"[0-9]+", timestamp):
        return False
    if not re.fullmatch(r"sha256=[0-9a-f]{64}", signature):
        return False
    try:
        age = now - int(timestamp.lstrip("0") or "0")
    except (ValueError, OverflowError):
        return False
    if not -30 <= age <= 300:
        return False
    expected = "sha256=" + hmac.new(
        secret, timestamp.encode("ascii") + b"." + body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
