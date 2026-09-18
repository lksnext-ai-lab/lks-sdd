"""Single-submission implementation using only the supplied full context."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
from email.utils import parsedate_to_datetime
import hashlib
import heapq
import hmac
import json
import re
from zoneinfo import ZoneInfo


def ledger_total(amounts):
    values = [Decimal(value) for value in amounts]
    if not values:
        return "0.00"
    # Allow arbitrarily long ordinary finite amounts without default-precision loss.
    precision = max(
        28,
        max(max(len(value.as_tuple().digits), value.adjusted() + 3) for value in values)
        + len(str(len(values))) + 2,
    )
    with localcontext() as context:
        context.prec = precision
        cents = Decimal("0.01")
        total = sum((value.quantize(cents, rounding=ROUND_HALF_UP) for value in values), Decimal("0.00"))
        if total == 0:
            return "0.00"
        return format(total, ".2f")


def local_day_ids(events, day, tz):
    zone = ZoneInfo(tz)
    result = []
    for event in events:
        instant = datetime.fromisoformat(event["timestamp"])
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("timestamp must include an explicit offset")
        if instant.astimezone(zone).date().isoformat() == day:
            result.append(event["id"])
    return result


def fold_events(events):
    identities = {}
    sequences = {}
    latest = {}
    for event in events:
        identity = (event["tenant"], event["event_id"])
        if identity in identities:
            if identities[identity] != event:
                raise ValueError("conflicting event identity")
            continue
        identities[identity] = event
        key = (event["tenant"], event["key"])
        sequence_key = key + (event["seq"],)
        if sequence_key in sequences:
            raise ValueError("distinct events share a sequence")
        sequences[sequence_key] = event
        if key not in latest or event["seq"] > latest[key]["seq"]:
            latest[key] = event
    return {key: deepcopy(event["value"]) for key, event in latest.items() if not event["deleted"]}


def can_read(user, resource):
    if user["disabled"]:
        return False
    if user["tenant"] != resource["tenant"]:
        return False
    if user["id"] in resource["denied_user_ids"]:
        return False
    return bool("admin" in user["roles"] or resource["owner_id"] == user["id"] or resource["public"])


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
    selected = (row for row in rows if cursor is None or (row["ts"], row["id"]) > cursor)
    return deepcopy(sorted(selected, key=lambda row: (row["ts"], row["id"]))[:limit])


def retry_delay(value, now, cap):
    if value is None:
        return None
    text = value.strip()
    if re.fullmatch(r"[0-9]+", text):
        digits = text.lstrip("0") or "0"
        maximum = str(cap)
        if len(digits) > len(maximum) or (len(digits) == len(maximum) and digits > maximum):
            return cap
        return int(digits)
    # Accept HTTP's IMF-fixdate and obsolete RFC850 date with explicit GMT;
    # the timezone-free asctime variant is outside the required GMT contract.
    date_pattern = (
        r"(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), [0-9]{2} "
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]{4}"
        r"|(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), "
        r"[0-9]{2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-[0-9]{2})"
        r" [0-9]{2}:[0-9]{2}:[0-9]{2} GMT"
    )
    if not re.fullmatch(date_pattern, text):
        return None
    try:
        target = parsedate_to_datetime(text)
        difference = target - now
    except (ValueError, TypeError, OverflowError):
        return None
    # Integer timedelta arithmetic implements ceil without float rounding.
    seconds = difference.days * 86400 + difference.seconds
    if difference.microseconds:
        seconds += 1
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
        identity = step["id"]
        if identity in by_id:
            raise ValueError("duplicate migration id")
        by_id[identity] = step
    complete = set(applied)
    pending = set(by_id) - complete
    dependencies = {}
    successors = {identity: set() for identity in pending}
    for identity in pending:
        required = set(by_id[identity]["depends_on"]) - complete
        if required - set(by_id):
            raise ValueError("missing migration dependency")
        dependencies[identity] = required
        for dependency in required:
            successors[dependency].add(identity)
    available = [identity for identity in pending if not dependencies[identity]]
    heapq.heapify(available)
    result = []
    while available:
        identity = heapq.heappop(available)
        result.append(identity)
        for dependent in successors[identity]:
            dependencies[dependent].remove(identity)
            if not dependencies[dependent]:
                heapq.heappush(available, dependent)
    if len(result) != len(pending):
        raise ValueError("cycle among pending migrations")
    return result


def cache_key(tenant, user, scopes):
    return json.dumps([tenant, user, sorted(set(scopes))], ensure_ascii=False, separators=(",", ":"))


def update_record(record, expected_version, changes):
    if expected_version != record["version"]:
        raise RuntimeError("version conflict")
    if {"id", "tenant", "version"}.intersection(changes):
        raise ValueError("identity and version fields cannot be changed")
    result = deepcopy(record)
    if changes:
        result.update(deepcopy(changes))
        result["version"] += 1
    return result


def verify_signature(body, signature, timestamp, now, secret):
    if not re.fullmatch(r"[0-9]+", timestamp):
        return False
    if not re.fullmatch(r"sha256=[0-9a-f]{64}", signature):
        return False
    try:
        instant = int(timestamp.lstrip("0") or "0")
    except (ValueError, OverflowError):
        return False
    age = now - instant
    if age > 300 or age < -30:
        return False
    message = timestamp.encode("ascii") + b"." + body
    expected = "sha256=" + hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
