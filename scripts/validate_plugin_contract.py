#!/usr/bin/env python3
"""Validate the active LKS-SDD contract, distribution, and release evidence."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

if str(__file__).startswith("\\\\?\\"):
    _bootstrap = Path(__file__).with_name("import_bootstrap.py")
    _namespace = {}
    exec(compile(_bootstrap.read_bytes(), str(_bootstrap), "exec"), _namespace)
    _namespace["ensure_import_path"](__file__)
    del _bootstrap, _namespace

from path_utils import filesystem_root
import release_notes

EXPECTED_SKILLS = {
    "lks-sdd-help",
    "lks-sdd-define",
    "lks-sdd-assess-readiness",
    "lks-sdd-implement",
    "lks-sdd-verify",
    "lks-sdd-adopt-existing",
}
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
)
COPILOT_CATALOG_PATH = ".github/plugin/marketplace.json"
COPILOT_CATALOG_REPOSITORY = "lksnext-ai-lab/lks-sdd"
CANONICAL_HASHES = {
    "LKS-SDD_definicion_plugin_v1.md": "4DE2D0AE75B2FF75BBC0C38D05C38AC2D90B57EA4472D46A85BF33C597D79700",
    "LKS-SDD_paquete_preimplementacion_v0.1.md": "A5FFD0D5CA1D9B7AC96D1DABB4A411739E18A01345348D9250F857D5F941504B",
    "LKS-SDD_baseline_normativa_candidata_v0.1.md": "083DED8FB14D77D899CB4F955AEA67D9A21FBA66AC25D7CF28D8C5111C1D1162",
    "LKS-SDD_extension_definicion_visual_v0.1.md": "ABA2B063A31192D5971CE9DC05323405BF7655737076AC924011E77E2C15ACA3",
    "LKS-SDD_extension_contrato_documental_v1.1.md": "84CEAA4C5243B2942CAA0EDE9288173A603E12640645C6D1E0C2915DED3B0C7D",
    "LKS-SDD_extension_gobierno_entrega_perfiles_tareas_v1.2.md": "45EB724665ACC88913775EC56A9F0D4DD2F07579D7E6674C8E479A2D29790C53",
    "LKS-SDD_extension_planificacion_continuidad_v1.3.md": "1CE7721E3B75DF475572DDEEB451243B13EC5D1F0FCDEA0E3780E16327263942",
}
REQUIRED_ROOT_FILES = {
    ".gitattributes",
    "README.md",
    "CHANGELOG.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    "docs/ARCHITECTURE.md",
    "docs/COMPATIBILITY.md",
    "docs/INSTALLATION.md",
    "docs/LEARNING-GUIDE.md",
    "docs/COPILOT-PILOT.md",
    "docs/MAINTENANCE.md",
    "docs/PROJECT-QUERY.md",
    "docs/V2-AUTHORING.md",
    "docs/V2-GUARDRAILS.md",
    "docs/V2-HOST-ACCEPTANCE.md",
    "docs/V2-INDEX.md",
    "docs/V2-MIGRATION.md",
    "docs/V2-WORKFLOWS.md",
    "docs/VISUAL-HANDOFF.md",
    "docs/JIRA-ROVO-INTEGRATION.md",
    "docs/DISTRIBUTION.md",
    "docs/RELEASING.md",
    "docs/VALIDATION.md",
    "specs/SOURCES.md",
    "specs/proposed/LKS-SDD_extension_tracking_operativo_v1.4.md",
    "specs/proposed/LKS-SDD_extension_reporting_jira_v1.5.md",
    "specs/proposed/project-contract-2.0.md",
    "scripts/validate_spec.py",
    "scripts/check_traceability.py",
    "scripts/render_client_view.py",
    "scripts/validate_fixture_manifest.py",
    "scripts/manage_pilot.py",
    "scripts/build_candidate_package.py",
    "scripts/contract_engine.py",
    "scripts/evidence_contract.py",
    "scripts/experience_engine.py",
    "scripts/experience_fixture.py",
    "scripts/validation_evidence.py",
    "scripts/project_status.py",
    "scripts/work_task.py",
    "scripts/doctor_project.py",
    "scripts/benchmark_experience.py",
    "scripts/lks_sdd.py",
    "scripts/query_project.py",
    "scripts/query_sources.py",
    "scripts/query_context.py",
    "scripts/query_code.py",
    "scripts/query_render.py",
    "schemas/query-context.schema.json",
    "docs/PROJECT-QUERY.md",
    "scripts/delivery_engine.py",
    "scripts/manage_tasks.py",
    "scripts/planning_engine.py",
    "scripts/manage_planning.py",
    "scripts/task_tracking_engine.py",
    "scripts/manage_task_tracking.py",
    "scripts/jira_reporting_engine.py",
    "scripts/manage_continuity.py",
    "quality/fixture-manifest.json",
    "schemas/verification-evidence-1.2.schema.json",
    "schemas/verification-evidence-1.3.schema.json",
    "schemas/visual-review-evidence-1.2.schema.json",
    "schemas/visual-evidence-policy.schema.json",
    "schemas/task-evidence-summary-1.0.schema.json",
    "schemas/pilot-config.schema.json",
    "schemas/pilot-observation.schema.json",
    "schemas/pilot-summary.schema.json",
    "schemas/document-contracts.json",
    "schemas/document-contracts.schema.json",
    "schemas/project-1.5.schema.json",
    "schemas/frontmatter-1.5.schema.json",
    "schemas/delivery-evidence.schema.json",
    "distribution/marketplace.template.json",
    "pilot/pilot-config.example.json",
    "pilot/PLAN.md",
    "pilot/ONBOARDING.md",
    "pilot/ROLLBACK.md",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/bug-report.yml",
    ".github/ISSUE_TEMPLATE/pilot-feedback.yml",
    ".github/workflows/quality.yml",
    "templates/client/client-deliverable.md",
    "tests/fixtures/validation-evidence-v016.json",
}
EXPECTED_GIT_ATTRIBUTES = (
    "* text=auto eol=lf",
    "*.gif binary",
    "*.ico binary",
    "*.jpeg binary",
    "*.jpg binary",
    "*.pdf binary",
    "*.png binary",
    "*.webp binary",
    "*.zip binary",
)
REQUIRED_SKILL_RESOURCES = {
    "lks-sdd-help": {
        "references/sdd-concepts.md",
        "references/project-lifecycle.md",
        "references/capabilities-and-limits.md",
        "references/product-reality.md",
        "references/transition-summaries.md",
        "references/onboarding.md",
        "references/work-codex-guide.md",
        "references/jira-companion.md",
        "references/examples.md",
        "references/faq.md",
        "references/troubleshooting.md",
        "scripts/context_help.py",
        "agents/openai.yaml",
    },
    "lks-sdd-define": {
        "references/method.md",
        "references/document-contract.md",
        "references/technology-selection.md",
        "references/conditional-annexes.md",
        "references/definition-coverage.md",
        "references/discovery-interview.md",
        "references/frontend-design.md",
        "references/jira-planning-contract.md",
        "scripts/init_project.py",
        "agents/openai.yaml",
    },
    "lks-sdd-assess-readiness": {
        "references/readiness-rubric.md",
        "references/jira-readiness-contract.md",
        "scripts/assess_readiness.py",
        "agents/openai.yaml",
    },
    "lks-sdd-implement": {
        "references/implementation-contract.md",
        "references/jira-implementation-sync.md",
        "scripts/prepare_increment.py",
        "agents/openai.yaml",
    },
    "lks-sdd-verify": {
        "references/verification-contract.md",
        "references/client-view-rules.md",
        "references/jira-verification-sync.md",
        "scripts/run_verification.py",
        "assets/delivery-evidence.example.json",
        "agents/openai.yaml",
    },
    "lks-sdd-adopt-existing": {
        "references/adoption-contract.md",
        "references/jira-adoption-boundary.md",
        "scripts/adoption_common.py",
        "scripts/inspect_repository.py",
        "scripts/validate_adoption.py",
        "scripts/materialize_adoption.py",
        "agents/openai.yaml",
    },
}
REQUIRED_CONDITIONAL_TEMPLATES = {
    "01-context/stakeholders-and-users.md",
    "03-solution/architecture.md",
    "03-solution/data.md",
    "03-solution/integrations.md",
    "03-solution/security-privacy-identity.md",
    "03-solution/ux-accessibility.md",
    "03-solution/decisions/decision-record.md",
    "04-delivery/roadmap.md",
    "04-delivery/delivery-governance.md",
    "04-delivery/plans.md",
    "04-delivery/tasks.md",
    "04-delivery/task-detail.md",
    "04-delivery/planning-coverage.md",
    "04-delivery/task-tracking.md",
    "04-delivery/checkpoint.md",
    "05-quality/test-strategy.md",
    "06-operation/deployment.md",
    "06-operation/observability.md",
    "06-operation/operations.md",
}
REQUIRED_ADOPTION_TEMPLATES = {
    "inspection-scope.md",
    "repository-inventory.md",
    "observed-architecture.md",
    "observed-behavior.md",
    "gaps-and-unknowns.md",
    "reconciliation.md",
    "adoption-strategy.md",
    "baseline-record.md",
}
FORBIDDEN_RUNTIME_IMPORTS = {
    "ftplib",
    "httpx",
    "requests",
    "smtplib",
    "socket",
    "subprocess",
    "urllib",
}
RUNTIME_IMPORT_ALLOWLIST = {
    "scripts/v2_contract.py": {"urllib.parse"},
    "scripts/v2_storage.py": {"urllib.parse"},
    "scripts/consumer_observer.py": {"subprocess"},
    "scripts/integration_contract.py": {"urllib.parse"},
    # Pure URL/path encoding, not network access. Query execution stays offline.
    "scripts/query_context.py": {"urllib.parse"},
    "scripts/query_render.py": {"urllib.parse"},
    "scripts/build_candidate_package.py": {"subprocess"},
    "scripts/build_dual_distribution.py": {"subprocess"},
    "scripts/benchmark_experience.py": {"subprocess"},
    "scripts/delivery_engine.py": {"subprocess"},
    "scripts/experience_engine.py": {"subprocess"},
    "scripts/manage_continuity.py": {"subprocess"},
    "scripts/manage_task_tracking.py": {"urllib.parse"},
    "scripts/run_release_gate.py": {"subprocess"},
    "scripts/release_readiness.py": {"subprocess"},
    "scripts/validate_release_artifacts.py": {"subprocess"},
    # Read-only Git resolution of the configured release distribution ref.
    "scripts/validate_distribution_reference.py": {"subprocess"},
    "scripts/work_task.py": {"subprocess"},
    "scripts/task_tracking_engine.py": {"urllib.parse"},
    "skills/lks-sdd-verify/scripts/run_verification.py": {
        "subprocess",
        "urllib.error",
        "urllib.request",
    },
    "skills/lks-sdd-adopt-existing/scripts/adoption_common.py": {"subprocess"},
}


def _forbidden_runtime_imports(relative: str, tree: ast.AST) -> set[str]:
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    allowed = RUNTIME_IMPORT_ALLOWLIST.get(relative, set())
    return {
        module
        for module in imported_modules
        if module.split(".", 1)[0] in FORBIDDEN_RUNTIME_IMPORTS
        and module not in allowed
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def python_string_constant(path: Path, name: str) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    except (OSError, UnicodeError, SyntaxError):
        return None
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    return None


def validate_copilot_catalog(root: Path, plugin_version: str) -> list[str]:
    """Validate the static Copilot catalog binding for a release version."""

    catalog_path = root / COPILOT_CATALOG_PATH
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"Catálogo Copilot ilegible: {exc}"]
    if not isinstance(catalog, dict):
        return ["El catálogo Copilot debe ser un objeto JSON."]
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list):
        return ["El catálogo Copilot debe declarar una lista de plugins."]
    matches = [
        plugin
        for plugin in plugins
        if isinstance(plugin, dict) and plugin.get("name") == "lks-sdd"
    ]
    if len(matches) != 1:
        return [f"El catálogo Copilot debe declarar un único lks-sdd, no {len(matches)}."]
    plugin = matches[0]
    source = plugin.get("source")
    expected_source = {
        "source": "github",
        "repo": COPILOT_CATALOG_REPOSITORY,
        "ref": f"copilot-v{plugin_version}",
    }
    errors: list[str] = []
    if plugin.get("version") != plugin_version:
        errors.append("La versión del catálogo Copilot debe coincidir con el manifest.")
    if source != expected_source:
        errors.append(
            "La fuente Copilot debe apuntar a la etiqueta nativa "
            f"copilot-v{plugin_version} del repositorio acreditado."
        )
    return errors


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_ROOT_FILES):
        if not (root / relative).is_file():
            errors.append(f"Falta archivo de gobierno o documentación: {relative}")
    attributes_path = root / ".gitattributes"
    try:
        attributes = tuple(
            line.strip()
            for line in attributes_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    except (OSError, UnicodeError) as exc:
        errors.append(f".gitattributes ilegible: {exc}")
    else:
        if attributes != EXPECTED_GIT_ATTRIBUTES:
            errors.append(
                ".gitattributes debe fijar LF para texto y preservar sin conversión "
                "los formatos binarios declarados."
            )
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Manifest ilegible: {exc}"]
    if manifest.get("name") != "lks-sdd":
        errors.append("El nombre del manifest debe ser lks-sdd.")
    plugin_version = manifest.get("version")
    if not isinstance(plugin_version, str) or not SEMVER_RE.fullmatch(plugin_version):
        errors.append("El manifest debe declarar una versión SemVer válida.")
        plugin_version = None
    else:
        changelog_path = root / "CHANGELOG.md"
        try:
            changelog_text = changelog_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Changelog ilegible: {exc}")
        else:
            match = re.search(r"^##\s+([0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)\b", changelog_text, re.MULTILINE)
            if match is None or match.group(1) != plugin_version:
                errors.append(
                    "La primera versión del changelog debe coincidir con el manifest."
                )

        try:
            release_notes.extract(changelog_path.read_bytes(), plugin_version)
        except (OSError, release_notes.ReleaseNotesError) as exc:
            errors.append(
                f"El changelog no acredita una sección única y no vacía para "
                f"{plugin_version}: {exc}"
            )

        version_markers = {
            "README.md": f"versión `{plugin_version}`",
            "docs/ARCHITECTURE.md": f"versión {plugin_version}",
            "skills/lks-sdd-help/references/capabilities-and-limits.md": plugin_version,
        }
        for relative, marker in version_markers.items():
            path = root / relative
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if marker not in text:
                errors.append(f"{relative} no refleja la versión {plugin_version}.")

        runtime_version_files = (
            "skills/lks-sdd-define/scripts/init_project.py",
            "skills/lks-sdd-adopt-existing/scripts/materialize_adoption.py",
        )
        for relative in runtime_version_files:
            declared = python_string_constant(root / relative, "PLUGIN_VERSION")
            if declared != plugin_version:
                errors.append(
                    f"{relative} declara PLUGIN_VERSION={declared!r}; debe coincidir con {plugin_version}."
                )
        errors.extend(validate_copilot_catalog(root, plugin_version))
    interface = manifest.get("interface", {})
    codex_manifest_fields = {
        "description": manifest.get("description"),
        "interface.displayName": interface.get("displayName")
        if isinstance(interface, dict)
        else None,
        "interface.shortDescription": interface.get("shortDescription")
        if isinstance(interface, dict)
        else None,
        "interface.longDescription": interface.get("longDescription")
        if isinstance(interface, dict)
        else None,
    }
    for field, value in codex_manifest_fields.items():
        if not isinstance(value, str) or "codex" not in value.casefold():
            errors.append(
                f"El campo {field} debe identificar Codex como entorno del plugin."
            )
    manifest_positioning = (
        manifest.get("description", ""),
        interface.get("longDescription", "") if isinstance(interface, dict) else "",
    )
    if any("spec-anchored" not in value.casefold() for value in manifest_positioning):
        errors.append(
            "La descripción y longDescription deben presentar LKS-SDD como Spec-anchored."
        )
    if "codex" not in manifest.get("keywords", []):
        errors.append("El manifest debe incluir la keyword codex.")
    for unsupported in ("apps", "mcpServers", "hooks"):
        if unsupported in manifest:
            errors.append(
                f"El manifest no puede declarar {unsupported} en el alcance actual."
            )

    skills_root = root / "skills"
    discovered = (
        {path.name for path in skills_root.iterdir() if path.is_dir()}
        if skills_root.is_dir()
        else set()
    )
    if discovered != EXPECTED_SKILLS:
        errors.append(f"Skills descubribles inesperadas: {sorted(discovered)}")
    for skill, resources in REQUIRED_SKILL_RESOURCES.items():
        skill_root = skills_root / skill
        for relative in sorted(resources):
            if not (skill_root / relative).is_file():
                errors.append(f"Falta recurso de {skill}: {relative}")
        agent_config = skill_root / "agents" / "openai.yaml"
        if agent_config.is_file():
            agent_text = agent_config.read_text(encoding="utf-8")
            if "allow_implicit_invocation: true" not in agent_text:
                errors.append(f"La invocación implícita debe seguir activa en {skill}.")
            if "codex" not in agent_text.casefold():
                errors.append(
                    f"Los metadatos de interfaz deben identificar Codex en {skill}."
                )
        skill_entrypoint = skill_root / "SKILL.md"
        if skill_entrypoint.is_file():
            skill_text = skill_entrypoint.read_text(encoding="utf-8")
            frontmatter = (
                skill_text.split("---", 2)[1] if skill_text.startswith("---") else ""
            )
            if "codex" not in frontmatter.casefold():
                errors.append(
                    f"La descripción de la skill debe identificar Codex en {skill}."
                )

    positioning_markers = {
        "README.md": (
            "Codex",
            "GitHub Copilot",
            "Claude",
            "ImageGen",
            "Spec-anchored",
            "Spec-as-source",
            "Atlassian Rovo",
            "jira-hybrid",
        ),
        "docs/COMPATIBILITY.md": (
            "Codex",
            "ChatGPT Work",
            "GitHub Copilot",
            "Claude",
            "ImageGen",
            "Atlassian Rovo",
            "not-run",
        ),
        "docs/ARCHITECTURE.md": (
            "Codex",
            "ImageGen",
            "not-run",
            "Spec-anchored",
            "Spec-as-source",
            "ART-TRACKING",
            "SYNC-###",
        ),
        "skills/lks-sdd-help/references/sdd-concepts.md": (
            "Spec-first",
            "Spec-anchored",
            "Spec-as-source",
            "Baseline adoptada",
        ),
        "skills/lks-sdd-help/references/faq.md": (
            "Spec-anchored",
            "empresa de servicios",
            "repositorio existente",
        ),
        "docs/JIRA-ROVO-INTEGRATION.md": (
            "Atlassian Rovo",
            "milestone-reporting",
            "Jira Done",
            "not-assessed",
        ),
    }
    for relative, markers in positioning_markers.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative} debe documentar explícitamente {marker}.")

    template_root = skills_root / "lks-sdd-define" / "assets" / "templates"
    for relative in sorted(REQUIRED_CONDITIONAL_TEMPLATES):
        if not (template_root / relative).is_file():
            errors.append(f"Falta plantilla condicional: {relative}")
    adoption_template_root = (
        skills_root / "lks-sdd-adopt-existing" / "assets" / "current-state-templates"
    )
    for name in sorted(REQUIRED_ADOPTION_TEMPLATES):
        if not (adoption_template_root / name).is_file():
            errors.append(f"Falta plantilla de adopción: {name}")

    for forbidden in (".mcp.json", ".app.json", "hooks", "agents", ".agents"):
        if (root / forbidden).exists():
            errors.append(f"Componente raíz fuera de alcance: {forbidden}")

    for filename, expected in CANONICAL_HASHES.items():
        path = root / "specs" / "canonical" / filename
        if not path.is_file():
            errors.append(f"Falta especificación canónica: {filename}")
        elif sha256(path) != expected:
            errors.append(f"Hash no canónico: {filename}")
    canonical_root = root / "specs" / "canonical"
    discovered_canonical = (
        {path.name for path in canonical_root.glob("*.md")}
        if canonical_root.is_dir()
        else set()
    )
    if discovered_canonical != set(CANONICAL_HASHES):
        errors.append(
            "Las fuentes canónicas descubiertas no coinciden con el inventario de hashes: "
            f"{sorted(discovered_canonical ^ set(CANONICAL_HASHES))}"
        )

    contract_markers = {
        "specs/canonical/LKS-SDD_extension_definicion_visual_v0.1.md": (
            "Encuadre inicial sin presuposiciones",
            "Resumen visual del estado de definición",
            "debe generar entre una y tres propuestas",
            "ImageGen",
            "not-run",
        ),
        "specs/canonical/LKS-SDD_extension_contrato_documental_v1.1.md": (
            "active_contract_fingerprint",
            "specification_readiness",
            "automation_support",
            "FR-001..FR-079",
            "preimplementation",
        ),
        "specs/canonical/LKS-SDD_extension_gobierno_entrega_perfiles_tareas_v1.2.md": (
            "bounded-release",
            "continuous-evolution",
            "maintenance-stream",
            "BIND-###",
            "gate de composición",
            "RabbitMQ",
            "Kafka",
        ),
        "specs/canonical/LKS-SDD_extension_planificacion_continuidad_v1.3.md": (
            "completitud de planificación",
            "planning-required",
            "complete-before-implementation",
            "incremental-authorized",
            "checkpoints",
            "cancelled",
        ),
        "specs/proposed/LKS-SDD_extension_tracking_operativo_v1.4.md": (
            "propuesta candidate, no canónica",
            "repository-only",
            "jira-hybrid",
            "LKS-SDD-PROJECT: <project_id>; TASK: TASK-###",
            "Atlassian Rovo",
            "Jira `Done`",
            "not-run",
        ),
        "specs/proposed/LKS-SDD_extension_reporting_jira_v1.5.md": (
            "propuesta candidate, no canónica",
            "milestone-reporting",
            "preview-event",
            "append-only",
            "not-run",
        ),
        "specs/proposed/project-contract-2.0.md": (
            "propuesta vigente para v2",
            "`observed`",
            "`proposed`",
            "`confirmed`",
            "`unknown`",
            "`transition`",
            "Contexto tecnológico de las tareas",
            "`TASK-###`",
            "Corte seguro de 1.5 a 2.0",
            "perfiles globales, recetas, catálogos de capacidades",
        ),
        "specs/SOURCES.md": (
            CANONICAL_HASHES["LKS-SDD_extension_definicion_visual_v0.1.md"],
            CANONICAL_HASHES[
                "LKS-SDD_extension_gobierno_entrega_perfiles_tareas_v1.2.md"
            ],
            CANONICAL_HASHES[
                "LKS-SDD_extension_planificacion_continuidad_v1.3.md"
            ],
            "specs/proposed/LKS-SDD_extension_tracking_operativo_v1.4.md",
            "specs/proposed/LKS-SDD_extension_reporting_jira_v1.5.md",
            "no canónica",
        ),
        "scripts/run_quality_harness.py": (
            '"v0.17.0.json"',
            "PILOT_SUMMARY_SCHEMA_PATH",
            "METRIC_DIRECTIONS",
            '"tree_state": "dirty" if porcelain else "clean"',
        ),
        "skills/lks-sdd-define/references/discovery-interview.md": (
            "una a tres",
        ),
        "skills/lks-sdd-define/references/frontend-design.md": (
            "ImageGen",
            "not-run",
        ),
    }
    for relative, markers in contract_markers.items():
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{relative} no contiene el marcador contractual {marker!r}.")

    for schema_name in (
        "pilot-config.schema.json",
        "pilot-observation.schema.json",
        "pilot-summary.schema.json",
        "catalogs.json",
        "project-1.5.schema.json",
        "frontmatter-1.5.schema.json",
        "delivery-evidence.schema.json",
        "document-contracts.json",
        "document-contracts.schema.json",
        "technology-declaration-2.0.schema.json",
    ):
        try:
            json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Schema inválido {schema_name}: {exc}")



    try:
        marketplace = json.loads(
            (root / "distribution" / "marketplace.template.json").read_text(
                encoding="utf-8"
            )
        )
        expected_entry = {
            "name": "lks-sdd",
            "source": {"source": "local", "path": "./plugins/lks-sdd"},
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Developer Tools",
        }
        if marketplace.get("name") != "lks-sdd-development":
            errors.append("El marketplace M5 debe llamarse lks-sdd-development.")
        if marketplace.get("plugins") != [expected_entry]:
            errors.append("La entrada del marketplace M5 no respeta el contrato Codex.")
    except (OSError, json.JSONDecodeError, AttributeError):
        errors.append("El marketplace M5 no es legible o válido.")

    try:
        pilot_example = json.loads(
            (root / "pilot" / "pilot-config.example.json").read_text(
                encoding="utf-8"
            )
        )
        if pilot_example.get("status") != "prepared":
            errors.append("El ejemplo de piloto debe permanecer prepared.")
        if pilot_example.get("projects") or pilot_example.get("participants"):
            errors.append("El ejemplo de piloto no debe contener proyectos o participantes.")
        roles = pilot_example.get("roles", {})
        if not isinstance(roles, dict) or any(value is not None for value in roles.values()):
            errors.append("El ejemplo de piloto no debe inventar responsables.")
        privacy = pilot_example.get("privacy", {})
        for field in (
            "allow_client_content",
            "allow_secrets",
            "allow_personal_names",
        ):
            if privacy.get(field) is not False:
                errors.append(f"El ejemplo de piloto debe mantener {field}=false.")
        rollback = pilot_example.get("rollback", {})
        if plugin_version and rollback.get("candidate_version") != plugin_version:
            errors.append(
                "La candidate del ejemplo de piloto debe coincidir con el manifest."
            )
        if rollback.get("previous_version") != "1.0.0":
            errors.append("El rollback de la distribución dual debe conservar 1.0.0.")
    except (OSError, json.JSONDecodeError, AttributeError):
        errors.append("El ejemplo de piloto M5 no es legible o válido.")

    try:
        pilot_schema = json.loads(
            (root / "schemas" / "pilot-config.schema.json").read_text(encoding="utf-8")
        )
        schema_candidate = pilot_schema["properties"]["rollback"]["properties"][
            "candidate_version"
        ].get("const")
        schema_previous = pilot_schema["properties"]["rollback"]["properties"][
            "previous_version"
        ].get("const")
        if plugin_version and schema_candidate != plugin_version:
            errors.append(
                "pilot-config.schema.json debe fijar la misma candidate que el manifest."
            )
        if schema_previous != "1.0.0":
            errors.append("pilot-config.schema.json debe fijar previous_version 1.0.0.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, AttributeError):
        errors.append("pilot-config.schema.json no expone la versión candidate esperada.")

    if plugin_version and "-" not in plugin_version:
        current_path = root / "quality" / f"release-approval-v{plugin_version}.json"
        try:
            approval = json.loads(current_path.read_text(encoding="utf-8"))
            decision = approval.get("decision", {})
            if (
                approval.get("release_version") != plugin_version
                or approval.get("scope") != "stable-release"
                or approval.get("evidence_handling") != "aggregated-no-identities"
                or decision.get("status") != "approved"
                or decision.get("authority_role") != "project-owner"
                or decision.get("blocking_findings") != []
            ):
                errors.append(
                    "La release stable requiere aprobación vigente sin bloqueantes."
                )
        except (OSError, json.JSONDecodeError, AttributeError):
            errors.append("La aprobación estable vigente no es legible o válida.")

    package_builder = root / "scripts" / "build_candidate_package.py"
    if package_builder.is_file():
        package_text = package_builder.read_text(encoding="utf-8")
        if "plugin_version = manifest.get(\"version\")" not in package_text:
            errors.append(
                "El empaquetado debe derivar dinámicamente la versión desde el manifest."
            )
        for marker in (
            "--quality-report",
            "QUALITY_REPORT_NAME",
            "tree_state",
            "simple-release-gate-1.0",
            "package-integrity.json",
        ):
            if marker not in package_text:
                errors.append(
                    f"El empaquetado no protege la evidencia de calidad: falta {marker}."
                )

    public_cli = root / "scripts" / "lks_sdd.py"
    if public_cli.is_file():
        cli_text = public_cli.read_text(encoding="utf-8")
        for command in (
            "help",
            "define",
            "adopt-inspect",
            "adopt-validate",
            "adopt-materialize",
            "assess-readiness",
            "implement",
            "verify",
            "validate-project",
            "validate-spec",
            "traceability",
            "client-view",
            "tasks",
            "planning",
            "tracking",
            "continuity",
        ):
            if f'"{command}"' not in cli_text:
                errors.append(f"El dispatcher portable no declara {command}.")

    try:
        project_15 = json.loads(
            (root / "schemas" / "project-1.5.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required_15 = set(project_15["required"])
        properties_15 = project_15["properties"]
        if properties_15["schema_version"].get("const") != "1.5":
            errors.append("project-1.5.schema.json debe fijar schema_version 1.5.")
        if properties_15["method_version"].get("const") != "1.5.0":
            errors.append("project-1.5.schema.json debe fijar method_version 1.5.0.")
        if "task_tracking" not in required_15:
            errors.append("El índice 1.5 debe exigir task_tracking.")
        tracking_15 = properties_15["task_tracking"]
        expected_tracking_15 = {
            "source", "binding_id", "state", "mode", "provider", "decision",
            "site", "project_key", "issue_type", "sync_policy", "write_policy",
            "reporting_scope", "coordination_gate", "reporting_status",
            "last_reported_on", "projection_fingerprint", "sync_status",
            "last_sync_on",
        }
        if set(tracking_15.get("required", [])) != expected_tracking_15:
            errors.append("task_tracking 1.5 no conserva el índice cerrado esperado.")
        if tracking_15["properties"]["reporting_scope"].get("enum") != [
            "pending", "not-applicable", "projection-only", "milestone-reporting"
        ]:
            errors.append("El índice 1.5 no fija los scopes de reporting esperados.")
        if "advisory" not in tracking_15["properties"]["coordination_gate"].get(
            "enum", []
        ):
            errors.append("El índice 1.5 debe admitir coordination gate advisory.")
        if {"open_blockers", "readiness"} & (required_15 | set(properties_15)):
            errors.append("El índice 1.5 no debe persistir readiness derivado.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project-1.5.schema.json no expone el contrato esperado.")

    try:
        document_contracts = json.loads(
            (root / "schemas" / "document-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        if document_contracts.get("catalog_version") != "1.5":
            errors.append("document-contracts.json debe usar catalog_version 1.5.")
        if document_contracts.get("supported_project_schemas") != ["1.5"]:
            errors.append("El catálogo documental debe soportar únicamente schema 1.5.")
        if document_contracts.get("schema_inheritance") != {
            "1.2": "1.1",
            "1.3": "1.2",
            "1.4": "1.3",
            "1.5": "1.4",
        }:
            errors.append("La herencia documental debe fijar 1.5 → 1.4.")
        prefixes = document_contracts.get("identifier_prefixes", [])
        if not {"TRK", "RPT", "SYNC"} <= set(prefixes):
            errors.append("El catálogo 1.5 debe registrar TRK, RPT y SYNC.")
        tracking_artifact = document_contracts["artifacts"]["ART-TRACKING"]
        if (
            tracking_artifact.get("artifact_type") != "task-tracking"
            or tracking_artifact.get("path")
            != "docs/lks-sdd/04-delivery/task-tracking.md"
            or tracking_artifact.get("required_schemas") != ["1.4", "1.5"]
        ):
            errors.append("ART-TRACKING no respeta el contrato documental 1.4/1.5.")
        table_headers = {
            table.get("id"): table.get("headers")
            for table in tracking_artifact.get("tables", [])
            if isinstance(table, dict)
        }
        expected_headers = {
            "tracking.binding": [
                "Binding", "State", "Mode", "Provider", "Site", "Project",
                "Issue type", "Sync policy", "Write policy", "Decision",
                "Last reviewed",
            ],
            "tracking.mapping": [
                "Task", "State", "External ID", "External key", "URL",
                "Projection fingerprint", "Remote status", "Last synced",
                "Last operation", "Notes",
            ],
            "tracking.operations": [
                "ID", "State", "Task", "Action", "Preview hash",
                "Projection fingerprint", "Duplicate check", "Authorized by role", "Authorized on",
                "External ID", "External key", "Recorded on", "Result", "Notes",
            ],
            "tracking.reporting-policy": [
                "Reporting", "State", "Scope", "Coordination gate",
                "Comment policy", "Decision", "Last reviewed",
            ],
            "tracking.workflow-mapping": [
                "Local state", "State", "Jira status ID", "Jira status name",
                "Decision", "Last reviewed",
            ],
            "tracking.milestone-operations": [
                "ID", "State", "Task", "Source ref", "Event kind", "Action",
                "Event hash", "Preview hash", "Duplicate check",
                "Authorized by role", "Authorized on", "External ID",
                "External key", "Recorded on", "Result", "Notes",
            ],
        }
        if table_headers != expected_headers:
            errors.append("ART-TRACKING debe conservar exactamente sus seis tablas cerradas.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("document-contracts.json no expone ART-TRACKING 1.4/1.5.")

    markdown_files = list(root.rglob("*.md"))
    for path in markdown_files:
        if "specs" in path.parts and "canonical" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            errors.append(f"Markdown no UTF-8 {path.relative_to(root)}: {exc}")
            continue
        if "[TODO" in text:
            errors.append(f"Scaffold incompleto en {path.relative_to(root)}")

    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    # Help and the human-facing repository manual deliberately share these sources.
    # Other cross-skill/outside paths remain forbidden, and existence is still checked.
    shared_help_docs = {(root / "docs" / name).resolve() for name in (
        "LEARNING-GUIDE.md", "INSTALLATION.md", "COPILOT-PILOT.md", "V2-HOST-ACCEPTANCE.md",
    )}
    shared_v2_policies = {(root / name).resolve() for name in
                          ("docs/V2-WORKFLOWS.md", "docs/V2-SPEC-PLAN-TASK.md")}
    for skill in EXPECTED_SKILLS:
        skill_root = skills_root / skill
        for markdown in [
            skill_root / "SKILL.md",
            *sorted((skill_root / "references").glob("*.md")),
        ]:
            if not markdown.is_file():
                continue
            text = markdown.read_text(encoding="utf-8")
            for target in link_re.findall(text):
                if "://" in target or target.startswith("#"):
                    continue
                destination = (markdown.parent / target).resolve()
                try:
                    destination.relative_to(skill_root.resolve())
                except ValueError:
                    if destination not in shared_v2_policies and (skill != "lks-sdd-help" or destination not in shared_help_docs):
                        errors.append(f"Referencia fuera de la skill {skill}: {target}")
                        continue
                if not destination.is_file():
                    errors.append(f"Referencia ausente en {skill}: {target}")

    for script in root.rglob("*.py"):
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"), str(script))
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"Script inválido {script.relative_to(root)}: {exc}")
            continue
        relative_parts = script.relative_to(root).parts
        is_runtime_script = relative_parts[0] == "scripts" or (
            relative_parts[0] == "skills" and "scripts" in relative_parts
        )
        if not is_runtime_script:
            continue
        relative = script.relative_to(root).as_posix()
        forbidden = _forbidden_runtime_imports(relative, tree)
        if forbidden:
            errors.append(
                f"Script con import de red o ejecución externa no autorizado {relative}: {sorted(forbidden)}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = filesystem_root(args.plugin_root)
    errors = validate(root)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"ERROR: {error}")
        return 2
    try:
        manifest = json.loads(
            (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        version = manifest.get("version", "unknown")
    except (OSError, json.JSONDecodeError, AttributeError):
        version = "unknown"
    print(f"VALID: LKS-SDD {version} active contract (readers 1.5/2.0; six skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
