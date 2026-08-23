from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from typing import Any

from eval_support import (
    HELP_SCRIPT,
    IMPLEMENT_SCRIPT,
    READINESS_SCRIPT,
    VALIDATE_SCRIPT,
    VALIDATE_SPEC_SCRIPT,
    VERIFY_SCRIPT,
    initialize,
    run_json,
    tree_digest,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = PLUGIN_ROOT / "tests" / "fixtures" / "calculator-handoff-1.1.json"
TEMPLATE_ROOT = (
    PLUGIN_ROOT / "skills" / "lks-sdd-define" / "assets" / "templates"
)
TRACEABILITY_SCRIPT = PLUGIN_ROOT / "scripts" / "check_traceability.py"


def _png_bytes(width: int, height: int, rgb: list[int]) -> bytes:
    """Build a deterministic valid RGB PNG without optional image libraries."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    pixel = bytes(rgb)
    scanlines = b"".join(b"\x00" + pixel * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(scanlines, level=9))
        + chunk(b"IEND", b"")
    )


def _render_template(relative: str, project_id: str, date: str) -> str:
    content = (TEMPLATE_ROOT / relative).read_text(encoding="utf-8")
    return (
        content.replace("{{PROJECT_ID}}", project_id)
        .replace("{{BASELINE_ID}}", "BL-0001")
        .replace("{{DATE}}", date)
    )


def _append_rows(path: Path, header: str, rows: list[list[str]]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    index = lines.index(header)
    insertion = index + 2
    rendered = ["| " + " | ".join(row) + " |" for row in rows]
    lines[insertion:insertion] = rendered
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _remove_seed_open_point(path: Path) -> None:
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.startswith("| OPEN-001 |")
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _mark_definition_sufficient(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.startswith("| new |"):
            lines[index] = (
                "| new | readiness | G2 | INC-001 | derived-on-demand | "
                "Ejecutar readiness de solo lectura |"
            )
    coverage_header = (
        "| Dimensión | Estado | Alcance | Información disponible | "
        "Falta profundizar | Impacto |"
    )
    start = lines.index(coverage_header) + 2
    for index in range(start, len(lines)):
        if not lines[index].startswith("|"):
            break
        cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        cells[1:] = [
            "sufficient",
            "INC-001",
            "Contrato sintético confirmado y trazable",
            "none",
            "Sin bloqueo de handoff",
        ]
        lines[index] = "| " + " | ".join(cells) + " |"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _downgrade_initialized_project_to_11(root: Path) -> None:
    """Build a genuine compatibility fixture from the current initializer."""
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "schema_version": "1.1",
            "method_version": "1.1.0",
            "plugin_version": "0.7.0",
        }
    )
    for key in (
        "active_plan", "active_task", "active_tasks", "delivery_governance",
        "planning", "authorizations", "executions",
    ):
        manifest.pop(key, None)
    manifest["technology"].pop("profile_bindings", None)
    manifest["version_control"] = {
        "type": manifest["version_control"]["type"],
        "origin": manifest["version_control"]["origin"],
    }
    v12_only = {
        "ART-ARCH",
        "ART-GOVERNANCE",
        "ART-PLANS",
        "ART-TASKS",
        "ART-TEST-STRATEGY",
        "ART-DEPLOYMENT",
        "ART-PLANNING",
    }
    manifest["artifacts"] = [
        item for item in manifest["artifacts"] if item["id"] not in v12_only
    ]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for artifact in manifest["artifacts"]:
        path = root / artifact["path"]
        text = path.read_text(encoding="utf-8")
        text = text.replace('schema_version: "1.3"', 'schema_version: "1.1"', 1)
        text = text.replace('method_version: "1.3.0"', 'method_version: "1.1.0"', 1)
        text = text.replace(
            'created_with_plugin_version: "0.9.1"',
            'created_with_plugin_version: "0.7.0"',
            1,
        )
        text = text.replace(
            "PLAN-001 y REL-001 son propuestas iniciales",
            "La planificación de entrega todavía no está definida",
        )
        path.write_text(text, encoding="utf-8", newline="\n")


def _materialize_fixture(root: Path, fixture: dict[str, Any]) -> tuple[Path, Path]:
    docs = root / "docs" / "lks-sdd"
    manifest_path = root / ".lks-sdd" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update(
        {
            "phase": "readiness",
            "gate": "G2",
            "active_increment": fixture["increment"],
        }
    )
    manifest["technology"] = {
        "preferred_stack_assessed": True,
        "selected_profile": fixture["profile"]["id"],
        "selection_decision": fixture["profile"]["decision"],
    }
    for artifact in fixture["optional_artifacts"]:
        relative = artifact["path"]
        destination = docs / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        rendered = _render_template(
            relative, fixture["project_id"], fixture["date"]
        )
        if manifest.get("schema_version") == "1.1":
            rendered = rendered.replace(
                'schema_version: "1.3"', 'schema_version: "1.1"', 1
            ).replace(
                'method_version: "1.3.0"', 'method_version: "1.1.0"', 1
            ).replace(
                'created_with_plugin_version: "0.9.1"',
                'created_with_plugin_version: "0.7.0"',
                1,
            )
        destination.write_text(
            rendered,
            encoding="utf-8",
            newline="\n",
        )
        manifest["artifacts"].append(
            {
                "id": artifact["id"],
                "path": f"docs/lks-sdd/{relative}",
                "required": True,
            }
        )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    bundled_lock = (
        PLUGIN_ROOT
        / "profiles"
        / fixture["profile"]["id"]
        / "technology-profile.lock.json"
    )
    (root / ".lks-sdd" / "profile.lock.json").write_bytes(
        bundled_lock.read_bytes()
    )

    _remove_seed_open_point(docs / "00-control" / "open-points.md")
    _mark_definition_sufficient(docs / "00-control" / "project-status.md")
    for table in fixture["tables"]:
        _append_rows(docs / table["path"], table["header"], table["rows"])

    visuals = docs / "03-solution" / "ui-prototypes"
    visuals.mkdir(parents=True, exist_ok=True)
    active = fixture["visuals"]["active"]
    historical = fixture["visuals"]["historical"]
    active_path = visuals / active["filename"]
    historical_path = visuals / historical["filename"]
    active_bytes = _png_bytes(1440, 900, active["rgb"])
    historical_bytes = _png_bytes(1440, 900, historical["rgb"])
    active_path.write_bytes(active_bytes)
    historical_path.write_bytes(historical_bytes)

    ux_path = docs / "03-solution" / "ux-accessibility.md"
    visual_header = (
        "| ID | State | Asset | Format | Viewport | Screens or flow | "
        "Requirements | Source | Generated on | Prompt or brief | SHA-256 | "
        "Human validation | Confirmation scope | Limitations | Decision | Increment |"
    )
    _append_rows(
        ux_path,
        visual_header,
        [
            [
                active["id"],
                "confirmed",
                f"![Baseline activa](ui-prototypes/{active['filename']})",
                "PNG",
                "1440x900",
                "UX-001..UX-002, UX-010",
                "FR-001..FR-004, NFR-001",
                "ImageGen synthetic fixture; placeholder only",
                fixture["date"],
                "Jerarquía del editor, total persistente y navegación de versiones",
                hashlib.sha256(active_bytes).hexdigest(),
                "user-confirmed; role=synthetic-fixture-reviewer; date=2026-08-20; ref=ADR-002",
                "Jerarquía, densidad y flujo principal del fixture",
                "No demuestra responsive, accesibilidad ni comportamiento ejecutado",
                "ADR-002",
                "INC-001",
            ],
            [
                historical["id"],
                "rejected",
                f"![Alternativa histórica](ui-prototypes/{historical['filename']})",
                "PNG",
                "1440x900",
                "UX-001",
                "FR-001..FR-003",
                "ImageGen synthetic fixture; rejected placeholder",
                fixture["date"],
                "Alternativa de editor descartada por ocultar el total",
                hashlib.sha256(historical_bytes).hexdigest(),
                "rejected; role=synthetic-fixture-reviewer; date=2026-08-20; ref=ADR-002",
                "Historial de una dirección descartada",
                "No forma parte del contrato activo",
                "ADR-002",
                "INC-001",
            ],
        ],
    )
    return active_path, historical_path


class ComplexCalculatorHandoffTests(unittest.TestCase):
    def test_handoff_preflight_rejects_an_active_link_to_historical_visual(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="lks-sdd-active-visual-") as temporary:
            root = Path(temporary)
            initialize(root, fixture["project_id"])
            _downgrade_initialized_project_to_11(root)
            _materialize_fixture(root, fixture)

            increments_path = root / "docs/lks-sdd/04-delivery/increments.md"
            increments = increments_path.read_text(encoding="utf-8")
            increments_path.write_text(
                increments.replace(
                    "| new | VIS-003 |",
                    "| new | VIS-003, VIS-001 |",
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )

            validation_code, structural = run_json(VALIDATE_SCRIPT, str(root))
            self.assertEqual(validation_code, 0, structural)
            self.assertTrue(structural["valid"], structural["errors"])

            trace_code, traceability = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                "--phase",
                "preimplementation",
                expected_codes={3},
            )
            self.assertEqual(trace_code, 3, traceability)
            self.assertFalse(traceability["valid"])
            trace_codes = {
                item["code"] for item in traceability["diagnostics"]
            }
            self.assertIn("LKS-ACTIVE-HISTORICAL-REFERENCE", trace_codes)
            self.assertTrue(
                any(
                    "VIS-001 (rejected)" in gap
                    for gap in traceability["gaps"]
                ),
                traceability["gaps"],
            )

            _, context = run_json(HELP_SCRIPT, str(root))
            preflight = context["readiness_preflight"]
            self.assertEqual(preflight["status"], "incomplete")
            self.assertIn(
                "LKS-ACTIVE-HISTORICAL-REFERENCE",
                {item["code"] for item in preflight["diagnostics"]},
            )
            self.assertEqual(preflight["gaps"], traceability["gaps"])

            readiness_code, readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                expected_codes={3},
            )
            self.assertEqual(readiness_code, 3, readiness)
            self.assertEqual(readiness["status"], "specification-blocked")
            self.assertIn(
                "LKS-ACTIVE-HISTORICAL-REFERENCE",
                {item["code"] for item in readiness["diagnostics"]},
            )

    def test_calculator_contract_1_1_crosses_the_real_handoff_without_execution(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(fixture["classification"], "synthetic-only")
        with tempfile.TemporaryDirectory(prefix="lks-sdd-calculator-1-1-") as temporary:
            root = Path(temporary)
            initialized = initialize(root, fixture["project_id"])
            _downgrade_initialized_project_to_11(root)
            manifest = json.loads(
                (root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(initialized["status"], "initialized")
            self.assertEqual(manifest["schema_version"], "1.1")
            self.assertEqual(manifest["method_version"], "1.1.0")

            active_path, historical_path = _materialize_fixture(root, fixture)
            _, structural = run_json(VALIDATE_SCRIPT, str(root))
            self.assertTrue(structural["valid"], structural["errors"])

            _, specification = run_json(VALIDATE_SPEC_SCRIPT, str(root))
            self.assertTrue(specification["valid"], specification["errors"])
            self.assertEqual(specification["automation_support"]["profile_id"], fixture["profile"]["id"])

            _, context = run_json(HELP_SCRIPT, str(root))
            self.assertEqual(context["structural_validity"]["status"], "valid")
            self.assertEqual(context["readiness_snapshot"]["source"], "derived-on-demand")
            self.assertEqual(context["readiness_preflight"]["status"], "clear")
            self.assertFalse(context["action_started"])

            _, traceability = run_json(
                TRACEABILITY_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                "--phase",
                "preimplementation",
            )
            self.assertTrue(traceability["valid"], traceability["gaps"])
            self.assertEqual(
                set(traceability["checked"]),
                {
                    "FR-001",
                    "FR-002",
                    "FR-003",
                    "FR-004",
                    "NFR-001",
                    "NFR-002",
                    "TR-001",
                    "TR-002",
                },
            )
            self.assertFalse(traceability["evidence_required"])

            first_code, first_readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                expected_codes={3},
            )
            self.assertEqual(first_code, 3)
            self.assertEqual(first_readiness["status"], "planning-required")
            self.assertEqual(first_readiness["specification_readiness"]["status"], "ready")
            self.assertEqual(first_readiness["automation_support"]["status"], "supported")
            self.assertEqual(
                first_readiness["planning_completeness"]["status"],
                "not-applicable",
            )
            self.assertEqual(first_readiness["visual_prototypes"], ["VIS-003"])
            self.assertIn(active_path.relative_to(root).as_posix(), first_readiness["checked_files"])
            self.assertNotIn(historical_path.relative_to(root).as_posix(), first_readiness["checked_files"])
            active_fingerprint = first_readiness["active_contract_fingerprint"]
            document_fingerprint = first_readiness["document_fingerprint"]

            replacement_rgb = fixture["visuals"]["historical"]["replacement_rgb"]
            historical_path.write_bytes(_png_bytes(1440, 900, replacement_rgb))
            second_code, second_readiness = run_json(
                READINESS_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                expected_codes={3},
            )
            self.assertEqual(second_code, 3)
            self.assertEqual(second_readiness["status"], "planning-required")
            self.assertEqual(second_readiness["active_contract_fingerprint"], active_fingerprint)
            self.assertNotEqual(second_readiness["document_fingerprint"], document_fingerprint)

            before_plans = tree_digest(root)
            preparation_code, preparation = run_json(
                IMPLEMENT_SCRIPT,
                str(root),
                "--increment",
                fixture["increment"],
                "--dry-run",
                expected_codes={3},
            )
            self.assertEqual(preparation_code, 3)
            self.assertEqual(preparation["status"], "blocked")
            self.assertFalse(preparation["changed"])
            self.assertTrue(
                any("migrar" in item.casefold() for item in preparation["blockers"])
            )
            self.assertEqual(tree_digest(root), before_plans)
            self.assertFalse((root / "apps").exists())
            self.assertFalse((root / "docs" / "lks-sdd" / "evidence").exists())
            final_manifest = json.loads(
                (root / ".lks-sdd" / "project.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("implementation", final_manifest)
            self.assertNotIn("verification", final_manifest)


if __name__ == "__main__":
    unittest.main()
