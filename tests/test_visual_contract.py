from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from eval_support import (
    IMPLEMENT_SCRIPT,
    READINESS_SCRIPT,
    VERIFY_SCRIPT,
    _append_row,
    initialize,
    materialize_ready_increment,
    run_json,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = PLUGIN_ROOT / "scripts" / "validate_project.py"
UX_TEMPLATE = (
    PLUGIN_ROOT
    / "skills"
    / "lks-sdd-define"
    / "assets"
    / "templates"
    / "03-solution"
    / "ux-accessibility.md"
)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
ALT_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNg+A8AAQIBAEK+vGgAAAAASUVORK5CYII="
)


def _load_verification_module():
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_visual_verification", VERIFY_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_validator_module():
    scripts_root = str(PLUGIN_ROOT / "scripts")
    added_to_path = scripts_root not in sys.path
    if added_to_path:
        sys.path.insert(0, scripts_root)
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_project_validator", VALIDATE_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if added_to_path:
            sys.path.remove(scripts_root)
    return module


def _load_readiness_module():
    spec = importlib.util.spec_from_file_location(
        "lks_sdd_readiness", READINESS_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VisualContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lks-sdd-visual-")
        self.root = Path(self.temporary.name)
        initialize(self.root, "visual-contract")
        materialize_ready_increment(self.root)
        self.docs = self.root / "docs" / "lks-sdd"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _replace_interface_row(self, row: str) -> None:
        path = self.docs / "04-delivery" / "increments.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        header = "| Increment | Interface applicability | UX contract | Visual mode | Visual prototype | Reason |"
        index = lines.index(header)
        row_index = index + 2
        self.assertTrue(lines[row_index].startswith("| INC-001 |"))
        lines[row_index] = row
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def _materialize_profile_lock(self, implementation_status: str = "in-progress") -> None:
        packaged = (
            PLUGIN_ROOT
            / "profiles"
            / "WEB-FASTAPI-REACT-KEYCLOAK-PG"
            / "technology-profile.lock.json"
        )
        (self.root / ".lks-sdd/profile.lock.json").write_bytes(
            packaged.read_bytes()
        )
        manifest_path = self.root / ".lks-sdd/project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["implementation"] = {
            "status": implementation_status,
            "increment": "INC-001",
            "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
            "profile_version": "1.0.0-candidate.1",
            "changed_paths": [],
            "evidence_ids": [],
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _materialize_visual_contract(self, state: str = "confirmed") -> tuple[Path, str]:
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        content = UX_TEMPLATE.read_text(encoding="utf-8")
        content = content.replace(
            'created_with_plugin_version: "0.1.0"',
            'created_with_plugin_version: "0.6.0"',
        )
        content = content.replace("{{PROJECT_ID}}", "visual-contract")
        content = content.replace("{{BASELINE_ID}}", "BL-0001")
        content = content.replace("{{DATE}}", "2026-08-20")
        ux_path.write_text(content, encoding="utf-8", newline="\n")

        manifest_path = self.root / ".lks-sdd" / "project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["artifacts"].append(
            {
                "id": "ART-UX",
                "path": "docs/lks-sdd/03-solution/ux-accessibility.md",
                "required": True,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        _append_row(
            ux_path,
            "| ID | State | Screen",
            "| UX-001 | confirmed | Request screen | Submit one request | synthetic user | Request fields and acknowledgement | Submit | FR-001 | AC-001 | INC-001 |",
        )
        _append_row(
            ux_path,
            "| Screen | Entry and exit",
            "| UX-001 | Entry from the synthetic start route; exit after acknowledgement | Request fields first, acknowledgement second | Cancel request | not-applicable: one synthetic role | Desktop reference with narrow responsive stacking | Labelled fields, keyboard order and announced feedback | not-applicable: synthetic copy is fixed |",
        )
        _append_row(
            ux_path,
            "| Screen | Loading | Empty",
            "| UX-001 | Disable submit and expose progress | Show an empty request form | Preserve fields and show recoverable error | not-applicable: one synthetic role | Show acknowledgement next to the request | Restore fields after interruption |",
        )
        _append_row(
            ux_path,
            "| ID | State | Flow or interaction",
            "| UX-002 | confirmed | Submit and acknowledge | synthetic user | UX-001 | Valid submit | Submit and show acknowledgement | Show recoverable validation error | not-applicable: no destructive action | Keyboard focus returns to feedback | AC-001 | INC-001 |",
        )
        _append_row(
            ux_path,
            "| ID | State | Aspect",
            "| UX-003 | confirmed | Visual hierarchy | One primary action and restrained feedback | Keeps the synthetic flow legible | Reference profile components | user-confirmed; role=synthetic-reviewer; date=2026-08-20; ref=ADR-001 | ADR-001 | INC-001 |",
        )
        asset = self.docs / "03-solution" / "ui-prototypes" / "VIS-001.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(PNG_BYTES)
        digest = hashlib.sha256(PNG_BYTES).hexdigest()
        human_validation = (
            "user-confirmed; role=synthetic-reviewer; date=2026-08-20; ref=ADR-001"
            if state == "confirmed"
            else "pending"
        )
        _append_row(
            ux_path,
            "| ID | State | Asset",
            f"| VIS-001 | {state} | ![Request screen](ui-prototypes/VIS-001.png) | PNG | 1440x900 | UX-001, UX-002 | FR-001 | ImageGen synthetic fixture | 2026-08-20 | synthetic UI brief | {digest} | {human_validation} | Hierarchy, density and primary-action treatment | Static image does not prove responsive behavior or accessibility | ADR-001 | INC-001 |",
        )
        self._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | new | VIS-001 | New user-facing screen and interaction |"
        )
        return asset, digest

    def test_confirmed_visual_contract_is_ready_and_fingerprinted(self):
        asset, _ = self._materialize_visual_contract()
        _, validation = run_json(VALIDATE_SCRIPT, str(self.root))
        _, readiness = run_json(
            READINESS_SCRIPT, str(self.root), "--increment", "INC-001"
        )
        self.assertTrue(validation["valid"])
        self.assertEqual(readiness["status"], "ready")
        self.assertEqual(readiness["interface_applicability"], "applicable")
        self.assertEqual(readiness["visual_prototypes"], ["VIS-001"])
        self.assertIn(asset.relative_to(self.root).as_posix(), readiness["checked_files"])
        self.assertRegex(readiness["input_fingerprint"], r"^[a-f0-9]{64}$")

    def test_missing_visual_asset_invalidates_project(self):
        asset, _ = self._materialize_visual_contract()
        asset.unlink()
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("falta el asset" in item for item in result["errors"]))

    def test_corrupt_visual_asset_invalidates_project(self):
        asset, _ = self._materialize_visual_contract()
        asset.write_bytes(b"not-a-real-png")
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("firma PNG/JPEG inválida" in item for item in result["errors"]))

    def test_png_without_idat_is_rejected_even_with_valid_chunk_crcs(self):
        asset, old_digest = self._materialize_visual_contract()
        fake_png = PNG_BYTES[:33] + PNG_BYTES[-12:]
        asset.write_bytes(fake_png)
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        ux_path.write_text(
            ux_path.read_text(encoding="utf-8").replace(
                old_digest, hashlib.sha256(fake_png).hexdigest()
            ),
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("firma PNG/JPEG inválida" in item for item in result["errors"]))

    def test_jpeg_with_empty_tables_and_incomplete_frame_is_rejected(self):
        fake = (
            b"\xff\xd8"
            + b"\xff\xdb\x00\x02"
            + b"\xff\xc4\x00\x02"
            + b"\xff\xc0\x00\x08\x08\x00\x01\x00\x01\x01"
            + b"\xff\xda\x00\x06\x01\x00\x00\x00"
            + b"\x01"
            + b"\xff\xd9"
        )
        path = self.root / "fake.jpg"
        path.write_bytes(fake)
        validator = _load_validator_module()
        self.assertEqual(validator._image_signature(path), (None, None))

    def test_readiness_uses_the_snapshot_after_a_mid_read_mutation(self):
        module = _load_readiness_module()
        increments = self.docs / "04-delivery" / "increments.md"
        original_fingerprint = module.document_fingerprint
        calls = 0

        def mutate_then_fingerprint(model) -> str:
            nonlocal calls
            if calls == 0:
                increments.write_text(
                    increments.read_text(encoding="utf-8").replace(
                        "| INC-001 | confirmed |",
                        "| INC-001 | proposed |",
                        1,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
            calls += 1
            return original_fingerprint(model)

        with mock.patch.object(
            module, "document_fingerprint", side_effect=mutate_then_fingerprint
        ):
            code, result = module.assess(self.root, "INC-001")
        self.assertEqual(code, 3)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("debe estar confirmed" in item for item in result["blockers"]))

    def test_implementation_fingerprint_covers_undeclared_files_in_source_tree(self):
        app_root = self.root / "apps"
        app_root.mkdir(parents=True, exist_ok=True)
        declared = app_root / "a.txt"
        omitted = app_root / "b.txt"
        declared.write_text("declared\n", encoding="utf-8")
        omitted.write_text("first\n", encoding="utf-8")
        manifest = json.loads(
            (self.root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
        )
        manifest["implementation"] = {
            "status": "completed",
            "increment": "INC-001",
            "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
            "profile_version": "1.0.0-candidate.1",
            "changed_paths": ["apps/a.txt"],
            "evidence_ids": [],
        }
        validator = _load_validator_module()
        before, _, errors = validator.implementation_fingerprint(
            self.root, manifest, "INC-001"
        )
        self.assertEqual(errors, [])
        omitted.write_text("materially changed\n", encoding="utf-8")
        after, _, errors = validator.implementation_fingerprint(
            self.root, manifest, "INC-001"
        )
        self.assertEqual(errors, [])
        self.assertNotEqual(before, after)

    def test_verified_interface_evidence_requires_visual_review_check(self):
        self._materialize_visual_contract()
        evidence = self.docs / "evidence" / "EVID-999.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps(
                {
                    "evidence_id": "EVID-999",
                    "increment": "INC-001",
                    "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
                    "profile_version": "1.0.0-candidate.1",
                    "revision": None,
                    "classification": "verified",
                    "checks": [{"name": "backend-tests", "status": "passed"}],
                    "limitations": [],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        trace = self.docs / "05-quality" / "traceability.md"
        trace.write_text(
            trace.read_text(encoding="utf-8").replace(
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | EVID-999 |",
            ),
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={2}
        )
        self.assertEqual(code, 2)
        self.assertTrue(
            any(
                "requiere exactamente un check visual-browser-review" in item
                for item in result["errors"]
            )
        )

    def test_v06_project_cannot_downgrade_increment_contract_to_legacy(self):
        increments = self.docs / "04-delivery" / "increments.md"
        manifest = json.loads(
            (self.root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
        )
        increments.write_text(
            increments.read_text(encoding="utf-8").replace(
                f'created_with_plugin_version: "{manifest["plugin_version"]}"',
                'created_with_plugin_version: "0.5.0"',
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )
        code, validation = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={2}
        )
        self.assertEqual(code, 2)
        self.assertTrue(
            any("no puede rebajarse" in item for item in validation["errors"])
        )
        code, readiness = run_json(
            READINESS_SCRIPT,
            str(self.root),
            "--increment",
            "INC-001",
            expected_codes={2},
        )
        self.assertEqual(code, 2)
        self.assertNotEqual(
            readiness.get("interface_applicability"), "legacy-not-enforced"
        )

    def test_confirmed_screen_requires_detail_and_states(self):
        self._materialize_visual_contract()
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        lines = [
            line
            for line in ux_path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("| UX-001 | Entry from the synthetic start route")
        ]
        ux_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(
            any("requiere exactamente una fila de detalle" in item for item in result["errors"])
        )

    def test_confirmed_visual_direction_requires_structured_human_validation(self):
        self._materialize_visual_contract()
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        ux_path.write_text(
            ux_path.read_text(encoding="utf-8").replace(
                "user-confirmed; role=synthetic-reviewer; date=2026-08-20; ref=ADR-001",
                "user-confirmed: synthetic review",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(
            any("UX-003 confirmed requiere validación humana" in item for item in result["errors"])
        )

    def test_reused_visual_baseline_requires_explicit_mode_reference_and_reason(self):
        self._materialize_visual_contract()
        self._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | reuse | VIS-001 | Reuse the confirmed hierarchy and component treatment without visual changes |"
        )
        _, readiness = run_json(
            READINESS_SCRIPT, str(self.root), "--increment", "INC-001"
        )
        self.assertEqual(readiness["status"], "ready")
        self.assertEqual(readiness["visual_mode"], "reuse")

        self._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | reuse | not-applicable: reuse baseline | Reuse the confirmed hierarchy |"
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("debe enlazar una baseline VIS-###" in item for item in result["errors"]))

    def test_interface_change_without_visual_change_uses_none_but_still_reviews_browser(self):
        asset, _ = self._materialize_visual_contract()
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        lines = [
            line
            for line in ux_path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("| VIS-001 |")
        ]
        ux_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        asset.unlink()
        self._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | none | not-applicable: behavior changes but composition and visual direction do not | No screen, pattern or visual treatment changes |"
        )
        _, readiness = run_json(
            READINESS_SCRIPT, str(self.root), "--increment", "INC-001"
        )
        self.assertEqual(readiness["status"], "ready")
        self.assertEqual(readiness["visual_mode"], "none")
        self.assertEqual(readiness["visual_prototypes"], [])
        self._materialize_profile_lock()
        _, plan = run_json(
            VERIFY_SCRIPT, str(self.root), "--increment", "INC-001", "--plan"
        )
        self.assertTrue(
            any(item["name"] == "visual-browser-review" for item in plan["checks"])
        )

    def test_visual_asset_hash_must_match(self):
        _, digest = self._materialize_visual_contract()
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        ux_path.write_text(
            ux_path.read_text(encoding="utf-8").replace(digest, "0" * 64),
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("SHA-256 no coincide" in item for item in result["errors"]))

    def test_visual_asset_must_remain_in_canonical_directory(self):
        asset, _ = self._materialize_visual_contract()
        outside = self.docs / "03-solution" / "outside.png"
        outside.write_bytes(asset.read_bytes())
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        ux_path.write_text(
            ux_path.read_text(encoding="utf-8").replace(
                "ui-prototypes/VIS-001.png", "outside.png"
            ),
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("debe estar bajo" in item for item in result["errors"]))

    def test_visual_asset_symlink_is_rejected_when_supported(self):
        asset, digest = self._materialize_visual_contract()
        target = asset.with_name("target.png")
        target.write_bytes(PNG_BYTES)
        asset.unlink()
        try:
            asset.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlink no disponible en este entorno: {exc}")
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest)
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("enlace simbólico" in item for item in result["errors"]))

    def test_proposal_visual_does_not_satisfy_readiness(self):
        self._materialize_visual_contract(state="proposed")
        _, validation = run_json(VALIDATE_SCRIPT, str(self.root))
        code, readiness = run_json(
            READINESS_SCRIPT,
            str(self.root),
            "--increment",
            "INC-001",
            expected_codes={3},
        )
        self.assertTrue(validation["valid"])
        self.assertEqual(code, 3)
        self.assertTrue(
            any("VIS-001" in item and "no está confirmado" in item for item in readiness["blockers"])
        )

    def test_interface_not_applicable_with_reason_preserves_readiness(self):
        _, readiness = run_json(
            READINESS_SCRIPT, str(self.root), "--increment", "INC-001"
        )
        self.assertEqual(readiness["status"], "ready")
        self.assertEqual(readiness["interface_applicability"], "not-applicable")

    def test_global_maturity_percentage_is_rejected(self):
        status = self.docs / "00-control" / "project-status.md"
        status.write_text(
            status.read_text(encoding="utf-8") + "\nCobertura global de definición: 80 %\n",
            encoding="utf-8",
            newline="\n",
        )
        code, result = run_json(VALIDATE_SCRIPT, str(self.root), expected_codes={2})
        self.assertEqual(code, 2)
        self.assertTrue(any("porcentaje global" in item for item in result["errors"]))

    def test_visual_asset_change_invalidates_implementation_preview(self):
        asset, old_digest = self._materialize_visual_contract()
        _, preview = run_json(
            IMPLEMENT_SCRIPT,
            str(self.root),
            "--increment",
            "INC-001",
            "--dry-run",
        )
        asset.write_bytes(ALT_PNG_BYTES)
        new_digest = hashlib.sha256(ALT_PNG_BYTES).hexdigest()
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        ux_path.write_text(
            ux_path.read_text(encoding="utf-8").replace(old_digest, new_digest),
            encoding="utf-8",
            newline="\n",
        )
        _, readiness = run_json(
            READINESS_SCRIPT, str(self.root), "--increment", "INC-001"
        )
        self.assertEqual(readiness["status"], "ready")
        code, result = run_json(
            IMPLEMENT_SCRIPT,
            str(self.root),
            "--increment",
            "INC-001",
            "--apply",
            "--authorize",
            "--preview-hash",
            preview["preview_hash"],
            expected_codes={2},
        )
        self.assertEqual(code, 2)
        self.assertIn("preview hash", result["error"])
        self.assertFalse((self.root / "apps").exists())

    def test_frontend_verification_cannot_pass_without_manual_visual_evidence(self):
        self._materialize_visual_contract()
        self._materialize_profile_lock(implementation_status="completed")
        _, plan = run_json(
            VERIFY_SCRIPT, str(self.root), "--increment", "INC-001", "--plan"
        )
        self.assertTrue(
            any(item["name"] == "visual-browser-review" for item in plan["checks"])
        )

        module = _load_verification_module()
        args = argparse.Namespace(
            project_root=self.root,
            increment="INC-001",
            plan=False,
            execute=True,
            authorize=True,
            containers=False,
            record_evidence=None,
            visual_evidence=None,
        )
        with mock.patch.object(
            module,
            "_execute_check",
            side_effect=lambda check: {"name": check["name"], "status": "passed"},
        ):
            code, result = module.run(args)
        self.assertEqual(code, 3)
        self.assertEqual(result["classification"], "not-verified")
        self.assertIn(
            "not-run",
            {
                item["status"]
                for item in result["checks"]
                if item["name"] == "visual-browser-review"
            },
        )

    def test_visual_review_evidence_freezes_json_and_screenshot_hashes(self):
        _, visual_hash = self._materialize_visual_contract()
        implementation_file = self.root / "apps" / "frontend" / "reviewed.txt"
        implementation_file.parent.mkdir(parents=True, exist_ok=True)
        implementation_file.write_text("reviewed implementation\n", encoding="utf-8")
        implementation_relative = implementation_file.relative_to(self.root).as_posix()
        manifest_path = self.root / ".lks-sdd" / "project.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["implementation"] = {
            "status": "completed",
            "increment": "INC-001",
            "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
            "profile_version": "1.0.0-candidate.1",
            "changed_paths": [implementation_relative],
            "evidence_ids": [],
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        validator = _load_validator_module()
        implementation_hash, _, implementation_errors = (
            validator.implementation_fingerprint(self.root, manifest, "INC-001")
        )
        self.assertEqual(implementation_errors, [])
        self.assertIsNotNone(implementation_hash)
        evidence_root = self.docs / "evidence" / "visual"
        evidence_root.mkdir(parents=True, exist_ok=True)
        screenshot = evidence_root / "INC-001-request.png"
        screenshot.write_bytes(PNG_BYTES)
        screenshot_hash = hashlib.sha256(PNG_BYTES).hexdigest()
        evidence = evidence_root / "INC-001-review.json"
        evidence.write_text(
            json.dumps(
                {
                    "schema_version": "1.1",
                    "increment": "INC-001",
                    "status": "passed",
                    "review_type": "manual-browser",
                    "reviewed_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
                    "reviewer": {
                        "role": "quality-reviewer",
                        "alias": "synthetic-reviewer",
                    },
                    "human_validation": "validated-by-human",
                    "baseline": {
                        "baseline_id": "BL-0001",
                        "implementation_sha256": implementation_hash,
                        "increments_sha256": hashlib.sha256(
                            (self.docs / "04-delivery" / "increments.md").read_bytes()
                        ).hexdigest(),
                        "ux_contract_sha256": hashlib.sha256(
                            (self.docs / "03-solution" / "ux-accessibility.md").read_bytes()
                        ).hexdigest(),
                        "visual_assets": [
                            {"vis_id": "VIS-001", "sha256": visual_hash}
                        ],
                    },
                    "coverage": [
                        {
                            "ux_ids": ["UX-001", "UX-002", "UX-003"],
                            "vis_ids": ["VIS-001"],
                            "states": ["default", "error", "confirmation"],
                            "status": "passed",
                            "screenshots": ["SHOT-001"],
                        }
                    ],
                    "screenshots": [
                        {
                            "id": "SHOT-001",
                            "path": screenshot.relative_to(self.root).as_posix(),
                            "sha256": screenshot_hash,
                            "route": "/request",
                            "viewport": {"width": 1, "height": 1, "dpr": 1},
                            "capture": "viewport",
                        }
                    ],
                    "checks": [
                        {
                            "id": "critical-flow",
                            "status": "passed",
                            "ux_ids": ["UX-001", "UX-002", "UX-003"],
                            "screenshots": ["SHOT-001"],
                            "note": "Critical flow and states match the confirmed UX contract.",
                        }
                    ],
                    "limitations": [],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        module = _load_verification_module()
        outcome, limitations = module._visual_evidence_check(
            self.root, "INC-001", evidence
        )
        self.assertEqual(outcome["status"], "passed")
        self.assertEqual(
            outcome["evidence_sha256"], hashlib.sha256(evidence.read_bytes()).hexdigest()
        )
        self.assertEqual(
            outcome["screenshots"],
            [
                {
                    "id": "SHOT-001",
                    "path": screenshot.relative_to(self.root).as_posix(),
                    "sha256": screenshot_hash,
                }
            ],
        )
        self.assertEqual(limitations, [])

        canonical_evidence = self.docs / "evidence" / "EVID-001.json"
        canonical_evidence.parent.mkdir(parents=True, exist_ok=True)
        canonical_evidence.write_text(
            json.dumps(
                {
                    "evidence_id": "EVID-001",
                    "increment": "INC-001",
                    "profile_id": "WEB-FASTAPI-REACT-KEYCLOAK-PG",
                    "profile_version": "1.0.0-candidate.1",
                    "revision": None,
                    "classification": "verified",
                    "checks": [outcome],
                    "limitations": [],
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        trace = self.docs / "05-quality" / "traceability.md"
        trace.write_text(
            trace.read_text(encoding="utf-8").replace(
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | none |",
                "| FR-001 | AC-001 | ADR-001 | INC-001 | TEST-001 | EVID-001 |",
            ),
            encoding="utf-8",
            newline="\n",
        )
        _, validation = run_json(VALIDATE_SCRIPT, str(self.root))
        self.assertTrue(validation["valid"])

        screenshot.write_bytes(ALT_PNG_BYTES)
        code, invalid = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={2}
        )
        self.assertEqual(code, 2)
        self.assertTrue(
            any("visual-browser-review" in item for item in invalid["errors"])
        )
        with self.assertRaises(module.VerificationError):
            module._visual_evidence_check(self.root, "INC-001", evidence)
        screenshot.write_bytes(PNG_BYTES)
        _, restored = run_json(VALIDATE_SCRIPT, str(self.root))
        self.assertTrue(restored["valid"])

        implementation_file.write_text("mutated implementation\n", encoding="utf-8")
        code, invalid = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={2}
        )
        self.assertEqual(code, 2)
        self.assertTrue(
            any("implementation_sha256 no coincide" in item for item in invalid["errors"])
        )
        with self.assertRaises(module.VerificationError):
            module._visual_evidence_check(self.root, "INC-001", evidence)


if __name__ == "__main__":
    unittest.main()
