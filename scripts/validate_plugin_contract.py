#!/usr/bin/env python3
"""Validate LKS-SDD M0-M5 plus the 0.15 product/quality invariants."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

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
    "docs/M1-COVERAGE.md",
    "docs/M2-COVERAGE.md",
    "docs/M3-COVERAGE.md",
    "docs/M4-COVERAGE.md",
    "docs/M5-COVERAGE.md",
    "docs/V0.6-DEFINITION-UX-COVERAGE.md",
    "docs/V0.7-CONTRACT-HANDOFF-COVERAGE.md",
    "docs/V0.8-DELIVERY-MULTIPROFILE-COVERAGE.md",
    "docs/V0.9-PLANNING-CONTINUITY-COVERAGE.md",
    "docs/V0.10-JIRA-ROVO-COVERAGE.md",
    "docs/V0.11-JIRA-MILESTONE-COVERAGE.md",
    "docs/V0.12-ENTRA-PROFILE-COVERAGE.md",
    "docs/V0.13-SIMULATED-OIDC-PROFILES.md",
    "docs/V0.14-INCREMENTAL-VERIFICATION-COVERAGE.md",
    "docs/V0.15-QUALITY-EFFICIENCY-COVERAGE.md",
    "docs/V0.15-PRODUCT-EXPERIENCE.md",
    "docs/releases/v0.14.0.md",
    "docs/releases/v0.14.2.md",
    "docs/releases/v0.15.0.md",
    "docs/JIRA-ROVO-INTEGRATION.md",
    "docs/QUALITY-HARNESS.md",
    "docs/DISTRIBUTION.md",
    "docs/RELEASING.md",
    "docs/VALIDATION.md",
    "specs/SOURCES.md",
    "specs/proposed/LKS-SDD_extension_tracking_operativo_v1.4.md",
    "specs/proposed/LKS-SDD_extension_reporting_jira_v1.5.md",
    "specs/proposed/LKS-SDD_extension_catalogo_capabilities_entra_v1.5.md",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/technology-profile.yaml",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/technology-profile.lock.json",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/profile-guide.md",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/profile-driver.json",
    "profiles/catalog.json",
    "scripts/validate_spec.py",
    "scripts/check_traceability.py",
    "scripts/render_client_view.py",
    "scripts/run_quality_harness.py",
    "scripts/validate_fixture_manifest.py",
    "scripts/manage_pilot.py",
    "scripts/build_candidate_package.py",
    "scripts/contract_engine.py",
    "scripts/evidence_contract.py",
    "scripts/experience_engine.py",
    "scripts/experience_fixture.py",
    "scripts/project_status.py",
    "scripts/work_task.py",
    "scripts/doctor_project.py",
    "scripts/benchmark_experience.py",
    "scripts/lks_sdd.py",
    "scripts/profile_registry.py",
    "scripts/automation_coverage.py",
    "scripts/delivery_engine.py",
    "scripts/manage_tasks.py",
    "scripts/planning_engine.py",
    "scripts/manage_planning.py",
    "scripts/task_tracking_engine.py",
    "scripts/manage_task_tracking.py",
    "scripts/jira_reporting_engine.py",
    "scripts/run_fast_validation.py",
    "scripts/quality_execution.py",
    "scripts/update_performance_baseline.py",
    "scripts/verify_profile_certifications.py",
    "scripts/manage_continuity.py",
    "scripts/update_profile_locks.py",
    "quality/catalog.json",
    "quality/corpora/activation.json",
    "quality/corpora/definition-v0.6.0.json",
    "quality/corpora/definition-v0.8.0.json",
    "quality/corpora/definition-v0.9.0.json",
    "quality/corpora/definition-v0.10.0.json",
    "quality/corpora/definition-v0.11.0.json",
    "quality/corpora/definition-v0.12.0.json",
    "quality/corpora/definition-v0.14.0.json",
    "quality/corpora/definition-v0.15.0.json",
    "quality/fixture-manifest.json",
    "quality/test-suites.json",
    "quality/v0.15-e2e-matrix.json",
    "quality/test-impact-map.json",
    "quality/performance-policy.json",
    "quality/baselines/v0.3.0.json",
    "quality/baselines/v0.4.0.json",
    "quality/baselines/v0.6.1.json",
    "quality/baselines/v0.10.0.json",
    "quality/baselines/v0.11.0.json",
    "quality/baselines/v0.12.0.json",
    "quality/baselines/v0.13.0.json",
    "quality/baselines/v0.14.2.json",
    "schemas/quality-observations.schema.json",
    "schemas/quality-report.schema.json",
    "schemas/quality-report-1.1.schema.json",
    "schemas/verification-evidence-1.2.schema.json",
    "schemas/pilot-config.schema.json",
    "schemas/pilot-observation.schema.json",
    "schemas/pilot-summary.schema.json",
    "schemas/document-contracts.json",
    "schemas/document-contracts.schema.json",
    "schemas/project-1.5.schema.json",
    "schemas/frontmatter-1.5.schema.json",
    "schemas/profile-catalog.schema.json",
    "schemas/profile-driver.schema.json",
    "schemas/profile-certification.schema.json",
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
    "tests/test_task_tracking_v14.py",
    "tests/test_jira_reporting_v15.py",
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
    "scripts/build_candidate_package.py": {"subprocess"},
    "scripts/benchmark_experience.py": {"subprocess"},
    "scripts/delivery_engine.py": {"subprocess"},
    "scripts/experience_engine.py": {"subprocess"},
    "scripts/manage_continuity.py": {"subprocess"},
    "scripts/manage_task_tracking.py": {"urllib.parse"},
    "scripts/run_reference_profile_gate.py": {"subprocess"},
    "scripts/run_quality_harness.py": {"subprocess"},
    "scripts/run_fast_validation.py": {"subprocess"},
    "scripts/quality_execution.py": {"subprocess"},
    "scripts/update_performance_baseline.py": {"subprocess"},
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

        release_path = root / "docs" / "releases" / f"v{plugin_version}.md"
        if not release_path.is_file():
            errors.append(f"Falta la nota de release docs/releases/v{plugin_version}.md.")
        else:
            release_text = release_path.read_text(encoding="utf-8")
            if not re.search(
                rf"^#\s+LKS-SDD\s+v{re.escape(plugin_version)}\b",
                release_text,
                re.MULTILINE,
            ):
                errors.append("La nota de release no coincide con la versión del manifest.")
            release_markers = (
                "**Fecha:**",
                "## Changelog",
                "## Compatibilidad",
                "## Perfiles y locks",
                "## Validación y evals",
                "## Vulnerabilidades conocidas y limitaciones",
                "## Actualización",
                "## Migración",
                "## Rollback",
                "## Soporte",
                "## Responsables",
            )
            for marker in release_markers:
                if marker not in release_text:
                    errors.append(
                        f"La nota de release {plugin_version} no contiene {marker!r}."
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
        "docs/V0.6-DEFINITION-UX-COVERAGE.md": (
            "FX-01",
            "FX-20",
            "FX-21",
            "not-run",
        ),
        "docs/V0.10-JIRA-ROVO-COVERAGE.md": (
            "FX-36",
            "FX-45",
            "Atlassian Rovo",
            "not-run",
            "Jira `Done`",
        ),
        "docs/V0.11-JIRA-MILESTONE-COVERAGE.md": (
            "FX-46",
            "FX-51",
            "milestone-reporting",
            "not-run",
            "advisory",
        ),
        "docs/V0.12-ENTRA-PROFILE-COVERAGE.md": (
            "FX-52",
            "FX-53",
            "automation_coverage",
            "Microsoft Entra",
            "not-run",
        ),
        "docs/V0.13-SIMULATED-OIDC-PROFILES.md": (
            "FX-54",
            "CAP-IDENTITY-OIDC-SIMULATED",
            "external_interoperability",
            "not-applicable",
            "production",
            "Microsoft Entra",
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
        "specs/proposed/LKS-SDD_extension_catalogo_capabilities_entra_v1.5.md": (
            "propuesta candidate, no canónica",
            "CAP-OIDC-DISCOVERY-JWKS",
            "CAP-ENTRA-CLAIMS",
            "automation_coverage",
            "not-run",
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
            "specs/proposed/LKS-SDD_extension_catalogo_capabilities_entra_v1.5.md",
            "no canónica",
        ),
        "scripts/run_quality_harness.py": (
            '"v0.14.2.json"',
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
        "technology-profile.schema.json",
        "technology-profile-lock.schema.json",
        "quality-observations.schema.json",
        "quality-report.schema.json",
        "pilot-config.schema.json",
        "pilot-observation.schema.json",
        "pilot-summary.schema.json",
        "catalogs.json",
        "project-1.5.schema.json",
        "frontmatter-1.5.schema.json",
        "profile-catalog.schema.json",
        "profile-driver.schema.json",
        "profile-certification.schema.json",
        "delivery-evidence.schema.json",
        "document-contracts.json",
        "document-contracts.schema.json",
    ):
        try:
            json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Schema inválido {schema_name}: {exc}")

    try:
        profile_catalog = json.loads(
            (root / "profiles" / "catalog.json").read_text(encoding="utf-8")
        )
        catalog_profiles = {
            item["id"]: item
            for item in profile_catalog.get("profiles", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        discovered_profiles = {
            path.name
            for path in (root / "profiles").iterdir()
            if path.is_dir() and (path / "technology-profile.yaml").is_file()
        }
        if discovered_profiles != set(catalog_profiles):
            errors.append(
                "El inventario físico de perfiles diverge del catálogo: "
                f"{sorted(discovered_profiles ^ set(catalog_profiles))}."
            )
        for profile_id, entry in catalog_profiles.items():
            profile_root = root / str(entry.get("path", ""))
            try:
                profile_root.resolve().relative_to((root / "profiles").resolve())
            except ValueError:
                errors.append(f"{profile_id}: path fuera de profiles/.")
                continue
            for filename in (
                "technology-profile.yaml",
                "technology-profile.lock.json",
                "profile-driver.json",
            ):
                if not (profile_root / filename).is_file():
                    errors.append(f"{profile_id}: falta {filename}.")
            if not (profile_root / "scaffold").is_dir():
                errors.append(f"{profile_id}: falta scaffold/.")
            if (
                entry.get("lifecycle") == "active"
                and not (profile_root / "certification-evidence.json").is_file()
            ):
                errors.append(
                    f"{profile_id}: active exige certification-evidence.json."
                )
        from profile_registry import validate_profile_bundle

        for profile_id, entry in sorted(catalog_profiles.items()):
            profile_errors = validate_profile_bundle(
                profile_id,
                require_validated=entry.get("lifecycle") == "active",
            )
            errors.extend(
                f"Contrato de perfil: {item}" for item in profile_errors
            )
    except (OSError, json.JSONDecodeError, TypeError, KeyError) as exc:
        errors.append(f"No se puede validar el inventario dinámico de perfiles: {exc}")

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
        if rollback.get("previous_version") != "0.14.2":
            errors.append("El rollback del piloto 0.15.0 debe conservar 0.14.2.")
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
        if schema_previous != "0.14.2":
            errors.append("pilot-config.schema.json debe fijar previous_version 0.14.2.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, AttributeError):
        errors.append("pilot-config.schema.json no expone la versión candidate esperada.")

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
            "baseline_sha256",
            "baseline_version",
            "baseline_relative",
            "_definition_corpus_relative",
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
            "profiles",
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

    try:
        quality_report = json.loads(
            (root / "schemas" / "quality-report.schema.json").read_text(
                encoding="utf-8"
            )
        )
        quality_required = set(quality_report["required"])
        source_contract = quality_report["properties"]["source"]
        if quality_report["properties"]["schema_version"].get("const") != "1.2":
            errors.append("quality-report.schema.json debe fijar schema_version 1.2.")
        if "source" not in quality_required or set(source_contract["required"]) != {
            "commit",
            "tree_state",
        }:
            errors.append(
                "El reporte de calidad debe exigir commit y estado del árbol fuente."
            )
        if source_contract["properties"]["tree_state"].get("enum") != [
            "clean",
            "dirty",
        ]:
            errors.append("El estado fuente debe distinguir clean y dirty.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("quality-report.schema.json no expone el vínculo de release 1.1.")

    try:
        baseline_061 = json.loads(
            (root / "quality" / "baselines" / "v0.6.1.json").read_text(
                encoding="utf-8"
            )
        )
        expected_metrics = {
            "automated_eval_cases": 5,
            "automated_eval_pass_rate": 1.0,
            "unit_tests_total": 81,
            "unit_tests_executed": 80,
            "unit_tests_passed": 80,
            "unit_tests_skipped": 1,
            "unit_tests_failed": 0,
            "critical_failures": 0,
            "profile_structure_gate": 1,
            "profile_complete_gate": 1,
        }
        if (
            baseline_061.get("plugin_version") != "0.6.1"
            or baseline_061.get("source_commit")
            != "7318ccc337570e296bffda68a8e49724bed94c99"
            or baseline_061.get("metrics") != expected_metrics
        ):
            errors.append("La baseline v0.6.1 no coincide con la release publicada.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.6.1.json no es una baseline válida.")

    try:
        baseline_010 = json.loads(
            (root / "quality" / "baselines" / "v0.10.0.json").read_text(
                encoding="utf-8"
            )
        )
        metrics_010 = baseline_010.get("metrics", {})
        if (
            baseline_010.get("plugin_version") != "0.10.0"
            or baseline_010.get("source_commit")
            != "9e8d6ed2a22073d11a50b303db884b9938e4e2c1"
            or metrics_010.get("unit_tests_total") != 231
            or metrics_010.get("unit_tests_passed") != 230
            or metrics_010.get("unit_tests_failed") != 0
            or metrics_010.get("profile_complete_gate") != 1
        ):
            errors.append("La baseline v0.10.0 no coincide con la release publicada.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.10.0.json no es una baseline válida.")

    try:
        baseline_011 = json.loads(
            (root / "quality" / "baselines" / "v0.11.0.json").read_text(
                encoding="utf-8"
            )
        )
        metrics_011 = baseline_011.get("metrics", {})
        if (
            baseline_011.get("plugin_version") != "0.11.0"
            or baseline_011.get("source_commit")
            != "ace1d2e95f0f7267f99e9e64da23160abccf1cfb"
            or metrics_011.get("unit_tests_total") != 237
            or metrics_011.get("unit_tests_passed") != 236
            or metrics_011.get("unit_tests_failed") != 0
            or metrics_011.get("profile_complete_gate") != 1
        ):
            errors.append("La baseline v0.11.0 no coincide con la release publicada.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.11.0.json no es una baseline válida.")

    try:
        baseline_012 = json.loads(
            (root / "quality" / "baselines" / "v0.12.0.json").read_text(
                encoding="utf-8"
            )
        )
        metrics_012 = baseline_012.get("metrics", {})
        if (
            baseline_012.get("plugin_version") != "0.12.0"
            or baseline_012.get("source_commit")
            != "64d83cd1389e765521c698a35df90da61428d870"
            or metrics_012.get("automated_catalog_cases") != 41
            or metrics_012.get("unit_tests_total") != 239
            or metrics_012.get("unit_tests_passed") != 238
            or metrics_012.get("unit_tests_skipped") != 1
            or metrics_012.get("unit_tests_failed") != 0
            or metrics_012.get("profile_complete_gate") != 1
        ):
            errors.append("La baseline v0.12.0 no coincide con la release publicada.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.12.0.json no es una baseline válida.")

    try:
        baseline_013 = json.loads(
            (root / "quality" / "baselines" / "v0.13.0.json").read_text(
                encoding="utf-8"
            )
        )
        metrics_013 = baseline_013.get("metrics", {})
        if (
            baseline_013.get("plugin_version") != "0.13.0"
            or baseline_013.get("source_commit")
            != "accb675d7fb66ebf19e151064acc88ae9d4a8c44"
            or metrics_013.get("automated_catalog_cases") != 42
            or metrics_013.get("unit_tests_total") != 240
            or metrics_013.get("unit_tests_passed") != 239
            or metrics_013.get("unit_tests_skipped") != 1
            or metrics_013.get("unit_tests_failed") != 0
            or metrics_013.get("profile_complete_gate") != 1
        ):
            errors.append("La baseline v0.13.0 no coincide con la release publicada.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.13.0.json no es una baseline válida.")

    try:
        baseline_0142 = json.loads(
            (root / "quality" / "baselines" / "v0.14.2.json").read_text(
                encoding="utf-8"
            )
        )
        metrics_0142 = baseline_0142.get("metrics", {})
        if (
            baseline_0142.get("plugin_version") != "0.14.2"
            or baseline_0142.get("source_commit")
            != "a303370c2555236c1778f276e187a4bb3c1926f5"
            or metrics_0142.get("automated_catalog_cases") != 43
            or metrics_0142.get("unit_tests_total") != 263
            or metrics_0142.get("unit_tests_passed") != 262
            or metrics_0142.get("unit_tests_skipped") != 1
            or metrics_0142.get("unit_tests_failed") != 0
            or metrics_0142.get("profile_complete_gate") != 1
        ):
            errors.append("La baseline v0.14.2 no coincide con la medición del commit publicado.")
    except (OSError, json.JSONDecodeError, TypeError):
        errors.append("quality/baselines/v0.14.2.json no es una baseline válida.")

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
    root = args.plugin_root.expanduser().resolve()
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
    print(f"VALID: LKS-SDD {version} contract (M0-M5 + schema 1.5 evolution)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
