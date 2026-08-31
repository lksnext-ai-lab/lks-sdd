"""Regression of the two independent INT tables; all data is synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contract_engine import build_project_model, load_registry
from delivery_engine import (
    ARCHITECTURE_HEADERS, EXTERNAL_INTEGRATION_HEADERS,
    INTEGRATION_INTERFACE_HEADERS, validate_delivery_contract,
)


def table(headers, rows):
    return "\n".join("| " + " | ".join(row) + " |" for row in (headers, ["---"] * len(headers), *rows))


def materialize(root, tables, *, unit=False):
    path = "docs/lks-sdd/03-solution/integrations.md"
    artifacts = [{"id": "ART-INTEGRATIONS", "path": path, "required": False}]
    content = "---\nartifact_id: ART-INTEGRATIONS\nartifact_type: integrations\nschema_version: 1.5\n---\n\n" + "\n\n".join(tables)
    (root / path).parent.mkdir(parents=True)
    (root / path).write_text(content, encoding="utf-8")
    if unit:
        arch = "docs/lks-sdd/03-solution/architecture.md"
        artifacts.append({"id": "ART-ARCH", "path": arch, "required": True})
        (root / arch).write_text(table(ARCHITECTURE_HEADERS, [[
            "UNIT-001", "proposed", "API", "Receive external contracts", "backend",
            "INT-001", "synthetic", "FR-001", "pending",
        ]]), encoding="utf-8")
    manifest = {"schema_version": "1.5", "method_version": "1.5.0", "artifacts": artifacts}
    (root / ".lks-sdd").mkdir()
    (root / ".lks-sdd/project.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


EXTERNAL = ["INT-001", "proposed", "External mobile client", "Read synthetic data",
            "GET /items", "pending", "Fail closed", "FR-001"]
INTERNAL = ["INT-002", "proposed", "UNIT-001", "UNIT-002", "BIND-001, BIND-002",
            "HTTPS", "GET /items", "read", "contract,composition,user-flow",
            "delivery-owner", "TASK-001", "FR-001", "pending"]


class IntegrationTablesV018Tests(unittest.TestCase):
    def test_both_table_contracts_are_optional_in_15(self):
        contracts = load_registry("1.5").artifacts["ART-INTEGRATIONS"].tables
        self.assertEqual(len(contracts), 2)
        self.assertTrue(all(t.minimum_occurrences == 0 for t in contracts))

    def test_external_internal_both_and_not_applicable_round_trip(self):
        external = table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL])
        internal = table(INTEGRATION_INTERFACE_HEADERS, [INTERNAL])
        for tables, ids in [([], set()), ([external], {"INT-001"}),
                            ([internal], {"INT-002"}), ([external, internal], {"INT-001", "INT-002"})]:
            with self.subTest(ids=ids), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                materialize(root, tables)
                model = build_project_model(root)
                self.assertEqual({n for n in model.nodes if n.startswith("INT-")}, ids)
                self.assertFalse([d for d in model.diagnostics if d.location.artifact_id == "ART-INTEGRATIONS"
                                  and d.code.startswith("LKS-TABLE")])

    def test_duplicate_ids_across_tables_are_rejected_without_rewrite(self):
        internal = ["INT-001", *INTERNAL[1:]]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = materialize(root, [table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL]),
                                          table(INTEGRATION_INTERFACE_HEADERS, [internal])])
            path = root / manifest["artifacts"][0]["path"]
            before = path.read_bytes()
            model = build_project_model(root)
            self.assertIn("LKS-ID-DUPLICATE", [d.code for d in model.diagnostics])
            self.assertTrue(any("duplicado entre" in e for e in validate_delivery_contract(root, manifest)["errors"]))
            self.assertEqual(path.read_bytes(), before)

    def test_external_reference_does_not_require_fictional_internal_unit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = materialize(root, [table(EXTERNAL_INTEGRATION_HEADERS, [EXTERNAL])], unit=True)
            delivery = validate_delivery_contract(root, manifest)
            self.assertEqual(delivery["interfaces"], {})
            self.assertEqual(delivery["external_integrations"]["INT-001"]["State"], "proposed")
            self.assertFalse(any("contratos inexistentes" in e for e in delivery["errors"]))
            self.assertEqual(set(delivery["units"]), {"UNIT-001"})

    def test_duplicates_within_each_table_are_rejected(self):
        for headers, row in [(EXTERNAL_INTEGRATION_HEADERS, EXTERNAL), (INTEGRATION_INTERFACE_HEADERS, INTERNAL)]:
            with self.subTest(headers=headers), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = materialize(root, [table(headers, [row, row])])
                self.assertIn("LKS-ID-DUPLICATE", [d.code for d in build_project_model(root).diagnostics])
                self.assertTrue(any("duplicados" in e for e in validate_delivery_contract(root, manifest)["errors"]))


if __name__ == "__main__":
    unittest.main()
