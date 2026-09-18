"""First delivery based only on prompt-direct_only.md; standard library only.

Underspecified choices are documented beside their implementations. No tests
or other contract variants were consulted before this delivery.
"""

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from email.utils import parsedate_to_datetime
import hashlib
import heapq
import hmac
import json
import math
import re
from zoneinfo import ZoneInfo


def ledger_total(amounts):
    # Assumption: round only the final sum, using decimal half-even rounding.
    values = [Decimal(amount) for amount in amounts]
    precision = max(
        28,
        sum(len(value.as_tuple().digits) + abs(value.as_tuple().exponent)
            for value in values) + 8,
    )
    with localcontext() as context:
        context.prec = precision
        total = sum(values, Decimal(0)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
    if total == 0:
        total = Decimal("0.00")
    return format(total, ".2f")


def local_day_ids(events, day, tz):
    target_day = date.fromisoformat(day)
    zone = ZoneInfo(tz)
    result = []
    for event in events:
        instant = datetime.fromisoformat(event["timestamp"])
        # An instant must include an offset; never use the host's local zone.
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("An event timestamp must include a UTC offset")
        if instant.astimezone(zone).date() == target_day:
            result.append(event["id"])
    return result


def fold_events(events):
    # Assumptions: event ids are unique within a tenant; first delivery wins
    # for duplicates. Highest seq wins per key; input order breaks seq ties.
    seen = set()
    latest = {}
    for index, event in enumerate(events):
        event_identity = (event["tenant"], event["event_id"])
        if event_identity in seen:
            continue
        seen.add(event_identity)
        key = (event["tenant"], event["key"])
        rank = (event["seq"], index)
        previous = latest.get(key)
        if previous is None or rank > previous[0]:
            latest[key] = (rank, event)
    return {
        key: deepcopy(event["value"])
        for key, (_, event) in latest.items()
        if not event["deleted"]
    }


def can_read(user, resource):
    # Conservative policy assumption: disablement, tenant isolation and an
    # explicit denial override public visibility, ownership and tenant admin.
    if user["disabled"]:
        return False
    if user["tenant"] != resource["tenant"]:
        return False
    if user["id"] in resource["denied_user_ids"]:
        return False
    return bool(
        resource["public"]
        or user["id"] == resource["owner_id"]
        or "admin" in user["roles"]
    )


def merge_patch(document, patch):
    # JSON Merge Patch: a non-object patch replaces the entire target.
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
    # Assumptions: ascending (ts,id), exclusive cursor, nonpositive limit
    # produces an empty page. Return copied rows without sorting the input.
    if limit <= 0:
        return []
    ordered = sorted(rows, key=lambda row: (row["ts"], row["id"]))
    boundary = tuple(cursor) if cursor is not None else None
    selected = [
        row for row in ordered
        if boundary is None or (row["ts"], row["id"]) > boundary
    ]
    return deepcopy(selected[:limit])


def retry_delay(value, now, cap):
    # Retry-After accepts integer delta-seconds or an HTTP date. Invalid and
    # absent values yield zero. Round future fractional seconds upward.
    if value is None:
        return 0
    raw = value.strip()
    if re.fullmatch(r"[0-9]+", raw):
        normalized = raw.lstrip("0") or "0"
        cap_text = str(cap)
        if len(normalized) > len(cap_text):
            return cap
        return min(int(normalized), cap)
    try:
        deadline = parsedate_to_datetime(raw)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        seconds = math.ceil((deadline - now).total_seconds())
    except (ValueError, TypeError, OverflowError, IndexError):
        return 0
    return min(cap, max(0, seconds))


def csv_cell(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)
    # Preserve numeric input types. For text, an apostrophe disarms formula
    # markers, including markers concealed behind leading whitespace.
    significant = value.lstrip()
    if (
        significant.startswith(("=", "+", "-", "@"))
        or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


def migration_order(steps, applied):
    # Assumptions: ties follow input order; applied ids satisfy dependencies.
    # Duplicate ids, unresolved dependencies and pending cycles are errors.
    by_id = {}
    position = {}
    for index, step in enumerate(steps):
        identity = step["id"]
        if identity in by_id:
            raise ValueError("Duplicate migration id")
        by_id[identity] = step
        position[identity] = index
    already_applied = set(applied)
    pending = set(by_id) - already_applied
    remaining = {}
    followers = {identity: set() for identity in pending}
    for identity in pending:
        dependencies = set(by_id[identity]["depends_on"])
        unknown = dependencies - set(by_id) - already_applied
        if unknown:
            raise ValueError("Unknown migration dependency")
        dependencies -= already_applied
        remaining[identity] = len(dependencies)
        for dependency in dependencies:
            followers[dependency].add(identity)
    ready = [
        (position[identity], identity)
        for identity in pending if remaining[identity] == 0
    ]
    heapq.heapify(ready)
    result = []
    while ready:
        _, identity = heapq.heappop(ready)
        result.append(identity)
        for follower in followers[identity]:
            remaining[follower] -= 1
            if remaining[follower] == 0:
                heapq.heappush(ready, (position[follower], follower))
    if len(result) != len(pending):
        raise ValueError("Cyclic migration dependencies")
    return result


def cache_key(tenant, user, scopes):
    # Assumption: scopes form an unordered permission set. JSON framing
    # preserves string boundaries even when identifiers contain delimiters.
    return json.dumps(
        [tenant, user, sorted(set(scopes))],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def update_record(record, expected_version, changes):
    # Conservative assumption: id, tenant and version cannot be overwritten
    # through changes. Version conflicts and forbidden changes raise ValueError.
    if record["version"] != expected_version:
        raise ValueError("Version conflict")
    if {"id", "tenant", "version"}.intersection(changes):
        raise ValueError("Changes include a protected field")
    result = deepcopy(record)
    result.update(deepcopy(changes))
    result["version"] = record["version"] + 1
    return result


def verify_signature(body, signature, timestamp, now, secret):
    # Assumptions where the prompt gives no wire protocol: sign the ASCII
    # timestamp, a dot and raw body; accept a hex digest optionally prefixed
    # by sha256=; permit at most 300 seconds of skew in either direction.
    if not re.fullmatch(r"[0-9]+", timestamp):
        return False
    try:
        signed_at = int(timestamp)
    except ValueError:
        return False
    if abs(now - signed_at) > 300:
        return False
    encoded = signature[7:] if signature.startswith("sha256=") else signature
    if not re.fullmatch(r"[0-9a-fA-F]{64}", encoded):
        return False
    supplied_digest = bytes.fromhex(encoded)
    expected_digest = hmac.new(
        secret,
        timestamp.encode("ascii") + b"." + body,
        hashlib.sha256,
    ).digest()
    return hmac.compare_digest(expected_digest, supplied_digest)
