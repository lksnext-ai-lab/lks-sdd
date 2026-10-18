"""Differential semantic checks for bounded store JSON inspection."""
import json
from pathlib import Path
import random
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from content_store import object_path, reference
from v2_contract import ContractError
from store_json_inspector import inspect


def original(raw, logical):
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return 0, 0
    if not isinstance(value, (dict, list)):
        return 0, 0
    stack = [value]
    nodes = refs = 0
    while stack:
        item = stack.pop()
        nodes += 1
        if isinstance(item, dict):
            if item.get("format") == "lks-sdd-object/1":
                object_path(item)
                if logical.get(item["sha256"]) != item["bytes"]:
                    raise ContractError("Unresolved or contradictory logical object reference")
                refs += 1
            else:
                stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return nodes, refs


class JsonInspectionTests(unittest.TestCase):
    def setUp(self):
        self.ref = reference(b"known")
        self.logical = {self.ref["sha256"]: self.ref["bytes"]}

    def check_equivalent(self, raw):
        try:
            expected = original(raw, self.logical)
        except ContractError:
            with self.assertRaises(ContractError):
                inspect(raw, self.logical)
        else:
            self.assertEqual(expected, inspect(raw, self.logical))

    def test_randomized_reference_semantics(self):
        rng = random.Random(40101)
        def value(depth):
            if depth == 0:
                return rng.choice([None, True, False, 1, -1, 4.5, "x", "é", "😀", "\\", self.ref])
            return rng.choice([value(0), [value(depth - 1) for _ in range(rng.randrange(5))],
                               {str(i) + "é": value(depth - 1) for i in range(rng.randrange(5))}])
        for _ in range(160):
            body = {"data": value(3)}
            for ascii_only in (True, False):
                self.check_equivalent(json.dumps(body, ensure_ascii=ascii_only).encode())

    def test_duplicate_keys_and_deferred_reference_validation(self):
        absent = {**self.ref, "sha256": "0" * 64}
        ref = json.dumps(absent)
        for key in ("é", "😀" + "x" * 300):
            literal, escaped = json.dumps(key, ensure_ascii=False), json.dumps(key, ensure_ascii=True)
            self.check_equivalent(("{" + literal + ":" + ref + "," + escaped + ":0}").encode())
            self.check_equivalent(("{" + literal + ":0," + escaped + ":" + ref + "}").encode())
        raw = json.dumps({"format":"lks-sdd-object/1", "sha256": self.ref["sha256"], "bytes":5})
        self.check_equivalent(raw.replace('"format"', '"bytes":false,"format"').encode())

    def test_exact_reference_types_and_escaped_ascii(self):
        for field, bad in (("sha256", "g" * 64), ("bytes", True), ("bytes", 5.0),
                           ("bytes", -1), ("bytes", "5"), ("extra", 0)):
            self.check_equivalent(json.dumps({**self.ref, field: bad}).encode())
        self.check_equivalent(json.dumps({"ref":self.ref}).replace("format", "\\u0066ormat").encode())

    def test_invalid_json_never_uses_partial_references(self):
        absent = json.dumps({**self.ref,"sha256":"0" * 64}).encode()
        for raw in (b'{"x":'+absent+b',', b'{"x":"\\'+"é".encode()+b'"}',
                    b'{"x":"\xff"}', b'{"x":"\x01"}', b'[true,]', b'{bad}', b'opaque'):
            self.check_equivalent(raw)

    def test_encodings_escapes_and_surrogates(self):
        for text in (json.dumps({"é":[self.ref,"😀","\\"]}, ensure_ascii=False),
                     r'{"\ud83d\ude00":1,"😀":2,"\ud800":0}',
                     '{"a":"' + "\ud800\udc00" + '"}'):
            for encoding in ("utf-8", "utf-16", "utf-32"):
                self.check_equivalent(text.encode(encoding, "surrogatepass"))

    def test_normalization_chunk_boundaries(self):
        for padding in range(65515, 65545):
            for tail in ('😀', '\\\\😀', '\\😀', 'é'):
                raw = ('{"padding":"' + 'x'*padding + tail + '"}').encode()
                self.check_equivalent(raw)

    def test_long_key_fingerprints_and_escape_boundaries(self):
        absent = json.dumps({**self.ref, "sha256":"0"*64})
        for padding in range(65500, 65542):
            for tail in ('😀', '\\😀', '"é', '\\'*8):
                key = 'x'*padding + tail + 'end'
                literal = json.dumps(key, ensure_ascii=False)
                escaped = json.dumps(key, ensure_ascii=True)
                raw = ('{' + literal + ':' + absent + ',' + escaped + ':0}').encode()
                self.check_equivalent(raw)

    def test_oversized_input_refused_before_decode(self):
        with patch('store_json_inspector.MAX_OBJECT_BYTES', 4):
            with self.assertRaisesRegex(ContractError, "object byte budget"):
                inspect(b'[0,0]', {})

    def test_work_node_deadline_and_recursion_refuse_explicitly(self):
        self.assertEqual((1,1), inspect(json.dumps(self.ref).encode(), self.logical, node_limit=1))
        self.assertEqual((3,2), inspect(json.dumps([self.ref,self.ref]).encode(), self.logical, node_limit=3))
        self.assertEqual((8,0), inspect(b'[0,0,0,0,0,0,0]', {}, node_limit=8))
        with self.assertRaisesRegex(ContractError, "budget"):
            inspect(b'[0,0,0,0,0,0,0,0]', {}, node_limit=8)
        with self.assertRaisesRegex(ContractError, "time budget"):
            inspect(b'{}', {}, deadline=time.monotonic() - 1)
        with patch('store_json_inspector.time.monotonic', side_effect=[0,2]):
            with self.assertRaisesRegex(ContractError, "time budget"):
                inspect(b'{}', {}, deadline=1)
        with self.assertRaisesRegex(ContractError, "recursion budget"):
            inspect(b'[' * 2000 + b'0' + b']' * 2000, {})


if __name__ == "__main__":
    unittest.main()
