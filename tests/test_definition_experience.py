from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eval_support import (
    HELP_SCRIPT,
    PLUGIN_ROOT,
    initialize,
    run_json,
    tree_digest,
)


class DefinitionExperienceTests(unittest.TestCase):
    def test_templates_expose_discovery_coverage_and_visual_contracts(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            initialize(root, "definition-experience")
            docs = root / "docs" / "lks-sdd"

            brief = (docs / "01-context" / "product-brief.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("## Dominio y contexto profesional", brief)
            self.assertIn("## Usuario, tarea, proceso o decisión", brief)
            self.assertIn("## Entradas, reglas y fuentes", brief)
            self.assertNotIn("aplicación genérica confirmada", brief)

            open_points = (docs / "00-control" / "open-points.md").read_text(
                encoding="utf-8"
            )
            for term in (
                "dominio",
                "quién",
                "tarea",
                "reglas",
                "fuentes",
                "resultado",
            ):
                self.assertIn(term, open_points)

            status = (docs / "00-control" / "project-status.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "| Dimensión | Estado | Alcance | Información disponible | "
                "Falta profundizar | Impacto |",
                status,
            )
            self.assertIn(
                "Completar encuadre inicial: dominio, usuario, tarea y resultado",
                status,
            )
            self.assertNotIn("%", status)

            increments = (docs / "04-delivery" / "increments.md").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "| Increment | Interface applicability | UX contract | "
                "Visual mode | Visual prototype | Reason |",
                increments,
            )
            self.assertIn("elementos `UX-###`", increments)

            ux_template = (
                PLUGIN_ROOT
                / "skills"
                / "lks-sdd-define"
                / "assets"
                / "templates"
                / "03-solution"
                / "ux-accessibility.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                "| ID | State | Asset | Format | Viewport | Screens or flow | "
                "Requirements | Source | Generated on | Prompt or brief | SHA-256 | "
                "Human validation | Confirmation scope | Limitations | Decision | Increment |",
                ux_template,
            )
            self.assertIn("docs/lks-sdd/03-solution/ui-prototypes/", ux_template)
            self.assertIn("rol-o-alias-no-identificativo", ux_template)
            self.assertIn("una y tres propuestas", ux_template)
            self.assertIn("no cree una fila `VIS-###`", ux_template)

    def test_context_help_groups_coverage_without_writing(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            initialize(root, "coverage-summary")
            status_path = (
                root
                / "docs"
                / "lks-sdd"
                / "00-control"
                / "project-status.md"
            )
            status = status_path.read_text(encoding="utf-8")
            status = status.replace(
                "| Contexto profesional, problema y valor | unknown | project | "
                "No confirmado durante la inicialización | Dominio, proceso, "
                "problema, tarea o decisión y resultado esperado | Impide "
                "confirmar el propósito y el valor |",
                "| Contexto profesional, problema y valor | sufficient | project | "
                "ART-BRIEF: dominio y problema confirmados | Ninguno para el "
                "encuadre actual | Permite avanzar a delimitar el alcance |",
                1,
            )
            status = status.replace(
                "| Stakeholders, usuarios y uso | unknown | project | No "
                "confirmado durante la inicialización | Perfiles, necesidades y "
                "situación de uso | Impide priorizar experiencia y requisitos |",
                "| Stakeholders, usuarios y uso | partial | project | ART-BRIEF: "
                "perfil principal identificado | Falta confirmar la situación de "
                "uso | Limita la priorización de experiencia |",
                1,
            )
            status = status.replace(
                "| Operación | unknown | project | Aplicabilidad no confirmada | "
                "Despliegue, observabilidad y continuidad | Puede dejar requisitos "
                "operativos sin tratar |",
                "| Operación | not-applicable: prototipo sin operación | project | "
                "El alcance no incluye explotación | Ninguno para este alcance | "
                "No condiciona el encuadre actual |",
                1,
            )
            status_path.write_text(status, encoding="utf-8", newline="\n")

            before = tree_digest(root)
            _, result = run_json(HELP_SCRIPT, str(root))
            after = tree_digest(root)

            self.assertEqual(result["structural_validity"]["status"], "valid")
            coverage = result["definition_coverage"]
            self.assertTrue(coverage["available"])
            self.assertEqual(coverage["source"], "ART-STATUS")
            self.assertIn(
                "Contexto profesional, problema y valor", coverage["sufficient"]
            )
            self.assertIn("Stakeholders, usuarios y uso", coverage["needs_depth"])
            self.assertIn("Alcance", coverage["unknown"])
            self.assertIn(
                "Operación: prototipo sin operación", coverage["not_applicable"]
            )
            self.assertEqual(
                result["next_decision"],
                "Completar encuadre inicial: dominio, usuario, tarea y resultado",
            )
            self.assertFalse(result["readiness_snapshot"]["revalidated"])
            self.assertEqual(before, after)

            process = subprocess.run(
                [sys.executable, "-X", "utf8", str(HELP_SCRIPT), str(root)],
                cwd=PLUGIN_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("✓ sufficient — suficiente para avanzar", process.stdout)
            self.assertIn("△ partial — requiere profundización", process.stdout)
            self.assertIn("○ unknown — aún desconocido", process.stdout)
            self.assertIn("⛔ blocked — bloqueos", process.stdout)
            self.assertIn("fase=definition", process.stdout)
            self.assertIn("alcance=coverage-summary", process.stdout)
            self.assertIn("→ Siguiente decisión", process.stdout)
            self.assertIn("no revalidado", process.stdout)
            self.assertEqual(before, tree_digest(root))

    def test_context_help_uses_conservative_legacy_fallback(self):
        with tempfile.TemporaryDirectory(prefix="lks-sdd-definition-") as directory:
            root = Path(directory)
            initialize(root, "legacy-coverage")
            manifest_path = root / ".lks-sdd" / "project.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plugin_version"] = "0.5.0"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            status_path = (
                root
                / "docs"
                / "lks-sdd"
                / "00-control"
                / "project-status.md"
            )
            status = status_path.read_text(encoding="utf-8")
            status = status.replace(
                'created_with_plugin_version: "0.6.0"',
                'created_with_plugin_version: "0.5.0"',
                1,
            )
            legacy_status = status.split(
                "## Cobertura cualitativa para el siguiente paso", 1
            )[0]
            legacy_status += (
                "La inicialización no confirma decisiones ni autoriza generación "
                "de código.\n"
            )
            status_path.write_text(
                legacy_status, encoding="utf-8", newline="\n"
            )

            before = tree_digest(root)
            _, result = run_json(HELP_SCRIPT, str(root))
            after = tree_digest(root)

            self.assertEqual(result["structural_validity"]["status"], "valid")
            coverage = result["definition_coverage"]
            self.assertFalse(coverage["available"])
            self.assertEqual(coverage["source"], "legacy-fallback")
            self.assertIn("no permite inferir suficiencia", coverage["fallback_reason"])
            self.assertTrue(
                any(
                    "no permite inferir suficiencia" in item
                    for item in result["missing_or_limits"]
                )
            )
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
