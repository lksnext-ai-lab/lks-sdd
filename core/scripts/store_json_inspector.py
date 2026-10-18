"""Bounded reference inspection using stdlib JSON grammar (validated in V401-01).

The projection is disposable analysis, never persisted as object content. Original
bytes remain canonical. No new JSON grammar, package, global decoder patch or OS
memory-policy change is introduced here.
"""
import codecs
from contextvars import ContextVar
import hashlib
import json
from json.decoder import JSONObject, JSONArray, scanstring
from json.scanner import py_make_scanner
import re
import sys
import time
from types import FunctionType

from content_store import object_path
from v2_contract import ContractError

TAG = "lks-sdd-object/1"
HASH = re.compile(r"[0-9a-f]{64}\Z")
SURROGATE = re.compile("[\ud800-\udfff]")
OTHER = object()
_ESCAPE_PREFIX = ContextVar("lks_sdd_v401_escape_prefix", default=0)
MAX_OBJECT_BYTES = 64 * 1024 * 1024


def _ascii_escape(error):
    # Preserve invalid escapes as invalid: '\\é' must not become valid '\\\\u00e9'.
    at = error.start - 1
    while at >= 0 and error.object[at] == "\\":
        at -= 1
    parity = (error.start - 1 - at) % 2
    if at < 0:
        parity ^= _ESCAPE_PREFIX.get()
    if parity:
        raise json.JSONDecodeError("Invalid escape before Unicode", error.object, error.start)
    end = min(error.end, error.start + 4096)
    return json.encoder.encode_basestring_ascii(error.object[error.start:end])[1:-1], end


codecs.register_error("lks_sdd_v401_probe_json_ascii", _ascii_escape)


def prepare(raw, *, deadline=None):
    """Normalize in bounded chunks. Caller releases raw before consuming result."""
    if len(raw) > MAX_OBJECT_BYTES:
        raise ContractError("JSON input exceeds object byte budget")
    encoding = json.detect_encoding(raw)
    decoder = codecs.getincrementaldecoder(encoding)(errors="surrogatepass")
    chunks = []
    parity = 0
    try:
        for offset in range(0, len(raw), 64 * 1024):
            if deadline is not None and time.monotonic() >= deadline:
                raise _BudgetExceeded("JSON inspection time budget exceeded")
            text = decoder.decode(raw[offset:offset + 64 * 1024],
                                  final=offset + 64 * 1024 >= len(raw))
            if SURROGATE.search(text):
                # Preserve nonstandard literal surrogate distinctions exactly.
                chunks.clear()
                return [raw.decode(encoding, "surrogatepass")]
            token = _ESCAPE_PREFIX.set(parity)
            try:
                encoded = text.encode("ascii", "lks_sdd_v401_probe_json_ascii")
            finally:
                _ESCAPE_PREFIX.reset(token)
            chunks.append(encoded.decode("ascii"))
            at = len(text) - 1
            while at >= 0 and text[at] == "\\":
                at -= 1
            tail = (len(text) - 1 - at) % 2
            parity = tail ^ parity if at < 0 else tail
        return chunks
    except _BudgetExceeded as exc:
        raise ContractError(str(exc)) from exc
    except (ValueError, UnicodeError):
        return None


class _Memo(dict):
    """Bound caching; long keys use the same SHA-256 trust model as the CAS."""
    def setdefault(self, key, default=None):
        if sys.getsizeof(key) > 160:
            digest = hashlib.sha256()
            for offset in range(0, len(key), 8192):
                digest.update(key[offset:offset + 8192].encode("utf-8", "surrogatepass"))
            return digest.digest()  # bytes cannot equal any actual short JSON key
        if len(self) < 4096:
            return super().setdefault(key, key)
        return key


class _BudgetExceeded(Exception):
    pass


def _unescaped_quote(source, start, stop):
    at = source.find('"', start, stop)
    while at >= 0:
        before = at - 1
        while before >= start and source[before] == "\\":
            before -= 1
        if (at - 1 - before) % 2 == 0:
            return at
        at = source.find('"', at + 1, stop)
    return -1


def _bounded_string(source, start, strict):
    """Let stdlib validate bounded string fragments; preserve long-key identity."""
    if _unescaped_quote(source, start, min(start + 1024, len(source))) >= 0:
        return scanstring(source, start, strict)
    digest = hashlib.sha256()
    at = start
    while at < len(source):
        stop = min(at + 64 * 1024, len(source))
        closing = _unescaped_quote(source, at, stop)
        if closing >= 0:
            value, end = scanstring(source[at:closing + 1], 0, strict)
            digest.update(value.encode("utf-8", "surrogatepass"))
            return digest.digest(), closing + 1
        # Cut only at complete escapes, preserving escaped surrogate pairs.
        slash = source.rfind("\\", at, stop)
        if slash >= at:
            before = slash - 1
            while before >= at and source[before] == "\\":
                before -= 1
            if (slash - before) % 2 == 1:
                if slash == stop - 1 or (source[slash + 1:slash + 2] == "u" and stop - slash < 6):
                    stop = slash
        high = stop - 6
        if high >= at and source[high:high + 2] == "\\u" and source[stop:stop + 2] == "\\u":
            before = high - 1
            while before >= at and source[before] == "\\":
                before -= 1
            try:
                paired = (high - 1 - before) % 2 == 0 and 0xD800 <= int(source[high + 2:stop],16) <= 0xDBFF and 0xDC00 <= int(source[stop + 2:stop + 6],16) <= 0xDFFF
            except ValueError:
                paired = False
            if paired:
                stop = high
        if stop <= at:
            raise json.JSONDecodeError("Incomplete JSON string escape", source, at)
        value, end = scanstring(source[at:stop] + '"', 0, strict)
        digest.update(value.encode("utf-8", "surrogatepass"))
        at = stop
    raise json.JSONDecodeError("Unterminated JSON string", source, start - 1)


# Reuse the installed stdlib grammar with a local string callback. No global
# monkeypatch or copied object/array parser; Python-version compatibility is tested.
_OBJECT = FunctionType(JSONObject.__code__,
                       {**JSONObject.__globals__, "scanstring": _bounded_string},
                       "_bounded_stdlib_object", JSONObject.__defaults__)


class _Projection(json.JSONDecoder):
    def __init__(self, limit, deadline):
        self.work = 1  # root container
        self.limit = limit
        self.deadline = deadline
        super().__init__(object_hook=self._object_done,
                         parse_float=lambda _: OTHER, parse_constant=lambda _: OTHER)
        self.parse_string = self._string
        self.parse_object = self._object
        self.parse_array = self._array
        self.memo = _Memo()
        self.scan_once = py_make_scanner(self)

    @staticmethod
    def _string(source, end, strict):
        value, end = _bounded_string(source, end, strict)
        # Only these string values can influence recognition/validation of a ref.
        if value == TAG or (len(value) == 64 and HASH.fullmatch(value)):
            return value, end
        return OTHER, end

    def _scan(self, scanner, array=False):
        def value(source, at):
            self.work += 1
            if self.work > self.limit + 3:
                raise _BudgetExceeded("Per-object JSON decode work budget exceeded")
            if self.work % 4096 == 0 and self.deadline is not None and time.monotonic() >= self.deadline:
                raise _BudgetExceeded("JSON inspection time budget exceeded")
            result, end = scanner(source, at)
            if array and type(result) in (int, float):
                result = OTHER
            return result, end
        return value

    def _object(self, source, strict, scanner, hook, pairs_hook, memo=None):
        return _OBJECT(source, strict, self._scan(scanner), hook, pairs_hook, memo)

    def _array(self, source, scanner):
        return JSONArray(source, self._scan(scanner, array=True))

    def _object_done(self, value):
        if value.get("format") == TAG:
            try:
                object_path(value)
            except ContractError:
                pass  # Validate only after the complete JSON and last-key-wins.
            else:
                self.work -= 3  # reference metadata is one terminal logical node
        return value


def inspect(raw, logical, *, node_limit=1_000_000, deadline=None):
    """Small-input convenience; full objects use prepare/release/inspect_prepared."""
    return inspect_prepared(prepare(raw, deadline=deadline), logical,
                            node_limit=node_limit, deadline=deadline)


def inspect_prepared(chunks, logical, *, node_limit=1_000_000, deadline=None):
    """Consume disposable normalized chunks; original object bytes are not retained."""
    if deadline is not None and time.monotonic() >= deadline:
        raise ContractError("JSON inspection time budget exceeded")
    if chunks is None:
        return 0, 0
    try:
        source = "".join(chunks)
        chunks.clear()
        if deadline is not None and time.monotonic() >= deadline:
            raise _BudgetExceeded("JSON inspection time budget exceeded")
        if not source.lstrip().startswith(("{", "[")):
            return 0, 0
        decoder = _Projection(node_limit, deadline)
        value = decoder.decode(source)
        if decoder.work > node_limit:
            raise _BudgetExceeded("Per-object JSON decode work budget exceeded")
        del source
        if deadline is not None and time.monotonic() >= deadline:
            raise _BudgetExceeded("JSON inspection time budget exceeded")
    except _BudgetExceeded as exc:
        raise ContractError(str(exc)) from exc
    except RecursionError as exc:
        raise ContractError("JSON inspection recursion budget exceeded") from exc
    except (ValueError, UnicodeError):
        return 0, 0  # complete input is not JSON; preserve opaque bytes unchanged
    stack = [value]
    nodes = refs = 0
    while stack:
        item = stack.pop()
        nodes += 1
        if nodes > node_limit:
            raise ContractError("Per-object reference traversal budget exceeded")
        if nodes % 4096 == 0 and deadline is not None and time.monotonic() >= deadline:
            raise ContractError("JSON inspection time budget exceeded")
        if isinstance(item, dict):
            if item.get("format") == TAG:
                object_path(item)
                if logical.get(item["sha256"]) != item["bytes"]:
                    raise ContractError("Unresolved or contradictory logical object reference")
                refs += 1
            else:
                stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return nodes, refs
