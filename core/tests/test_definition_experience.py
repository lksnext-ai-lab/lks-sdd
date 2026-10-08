from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from eval_support import V2_CLI, initialize, run_json, tree_digest


class DefinitionExperienceTests(unittest.TestCase):
    def test_initializer_creates_a_local_mandatory_technology_declaration(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            initialized = initialize(root, "definition-experience")

            declaration = (
                root / "docs/lks-sdd/03-solution/technology-declaration.md"
            ).read_text(encoding="utf-8")
            manifest = json.loads(
                (root / ".lks-sdd/project.json").read_text(encoding="utf-8")
            )

            self.assertEqual(initialized["status"], "applied")
            self.assertIn("Declaración tecnológica local", declaration)
            self.assertIn('"id":"TECH-001"', declaration)
            self.assertNotIn("profile", declaration.lower())
            self.assertNotIn("technology", manifest)
            self.assertIn(
                {"id": "TECH-001", "path": "docs/lks-sdd/03-solution/technology-declaration.md"},
                manifest["artifacts"],
            )

    def test_cli_preview_is_json_and_does_not_write(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            before = tree_digest(root)

            _, preview = run_json(
                V2_CLI,
                "init",
                str(root),
                "--name",
                "Preview project",
                "--project-id",
                "preview-project",
            )

            self.assertEqual(preview["status"], "preview")
            self.assertEqual(preview["operation"], "initialize-v2")
            self.assertIn(
                "docs/lks-sdd/03-solution/technology-declaration.md",
                preview["writes"],
            )
            self.assertEqual(before, tree_digest(root))

    def test_invalid_v2_index_is_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            initialize(root, "unsupported-schema")
            manifest_path = root / ".lks-sdd/project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["schema_version"] = "1.5"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            before = tree_digest(root)

            code, validation = run_json(
                V2_CLI, "validate", str(root), expected_codes={2}
            )

            self.assertEqual(code, 2)
            self.assertEqual(validation["status"], "blocked")
            self.assertEqual(before, tree_digest(root))


if __name__ == "__main__":
    unittest.main()
