"""Plugin transaction state stays compact and recoverable."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from eval_support import authorize_implementation, initialize, materialize_ready_project
from v2_storage import recover


class V2StorageTests(unittest.TestCase):
    def test_completed_transactions_share_one_plugin_store(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-storage-") as directory:
            root = Path(directory)
            materialize_ready_project(root, "compact-storage")
            authorize_implementation(root)

            store_path = root / ".lks-sdd/transactions.json"
            store = json.loads(store_path.read_text(encoding="utf-8"))

            self.assertEqual(store["schema_version"], "2.0")
            self.assertGreaterEqual(len(store["transactions"]), 3)
            self.assertFalse((root / ".lks-sdd/transactions").exists())

    def test_completed_transaction_can_be_rolled_back_from_compact_store(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-storage-") as directory:
            root = Path(directory)
            result = initialize(root, "rollback-storage")

            outcome = recover(
                root,
                result["preview_hash"],
                rollback=True,
                receipt=result["receipt"],
            )

            self.assertEqual(outcome["receipt"], ".lks-sdd/transactions.json")
            self.assertFalse((root / ".lks-sdd/project.json").exists())
            self.assertTrue((root / ".lks-sdd/transactions.json").is_file())


if __name__ == "__main__":
    unittest.main()
