#!/usr/bin/env python3
"""Validate LKS-SDD M0-M5 plus the 0.9/method-contract 1.3 invariants."""

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
    "docs/QUALITY-HARNESS.md",
    "docs/DISTRIBUTION.md",
    "docs/VALIDATION.md",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/technology-profile.yaml",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/technology-profile.lock.json",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/profile-guide.md",
    "profiles/WEB-FASTAPI-REACT-KEYCLOAK-PG/profile-driver.json",
    "profiles/catalog.json",
    "scripts/validate_spec.py",
    "scripts/check_traceability.py",
    "scripts/migrate_project.py",
    "scripts/render_client_view.py",
    "scripts/run_quality_harness.py",
    "scripts/validate_fixture_manifest.py",
    "scripts/manage_pilot.py",
    "scripts/build_candidate_package.py",
    "scripts/contract_engine.py",
    "scripts/lks_sdd.py",
    "scripts/profile_registry.py",
    "scripts/delivery_engine.py",
    "scripts/manage_tasks.py",
    "scripts/planning_engine.py",
    "scripts/manage_planning.py",
    "scripts/manage_continuity.py",
    "scripts/update_profile_locks.py",
    "quality/catalog.json",
    "quality/corpora/activation.json",
    "quality/corpora/definition-v0.6.0.json",
    "quality/corpora/definition-v0.8.0.json",
    "quality/corpora/definition-v0.9.0.json",
    "quality/fixture-manifest.json",
    "quality/baselines/v0.3.0.json",
    "quality/baselines/v0.4.0.json",
    "quality/baselines/v0.6.1.json",
    "schemas/quality-observations.schema.json",
    "schemas/quality-report.schema.json",
    "schemas/pilot-config.schema.json",
    "schemas/pilot-observation.schema.json",
    "schemas/pilot-summary.schema.json",
    "schemas/document-contracts.json",
    "schemas/document-contracts.schema.json",
    "schemas/project-1.1.schema.json",
    "schemas/frontmatter-1.1.schema.json",
    "schemas/project-1.2.schema.json",
    "schemas/frontmatter-1.2.schema.json",
    "schemas/project-1.3.schema.json",
    "schemas/frontmatter-1.3.schema.json",
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
    "templates/client/client-deliverable.md",
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
        "scripts/init_project.py",
        "agents/openai.yaml",
    },
    "lks-sdd-assess-readiness": {
        "references/readiness-rubric.md",
        "scripts/assess_readiness.py",
        "agents/openai.yaml",
    },
    "lks-sdd-implement": {
        "references/implementation-contract.md",
        "scripts/prepare_increment.py",
        "agents/openai.yaml",
    },
    "lks-sdd-verify": {
        "references/verification-contract.md",
        "references/client-view-rules.md",
        "scripts/run_verification.py",
        "assets/delivery-evidence.example.json",
        "agents/openai.yaml",
    },
    "lks-sdd-adopt-existing": {
        "references/adoption-contract.md",
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
    "scripts/delivery_engine.py": {"subprocess"},
    "scripts/manage_continuity.py": {"subprocess"},
    "scripts/run_reference_profile_gate.py": {"subprocess", "urllib"},
    "scripts/run_quality_harness.py": {"subprocess"},
    "skills/lks-sdd-verify/scripts/run_verification.py": {"subprocess", "urllib"},
    "skills/lks-sdd-adopt-existing/scripts/adoption_common.py": {"subprocess"},
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
            "scripts/migrate_project.py",
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
        ),
        "docs/COMPATIBILITY.md": (
            "Codex",
            "ChatGPT Work",
            "GitHub Copilot",
            "Claude",
            "ImageGen",
        ),
        "docs/ARCHITECTURE.md": (
            "Codex",
            "ImageGen",
            "not-run",
            "Spec-anchored",
            "Spec-as-source",
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
        "specs/SOURCES.md": (
            CANONICAL_HASHES["LKS-SDD_extension_definicion_visual_v0.1.md"],
            CANONICAL_HASHES[
                "LKS-SDD_extension_gobierno_entrega_perfiles_tareas_v1.2.md"
            ],
            CANONICAL_HASHES[
                "LKS-SDD_extension_planificacion_continuidad_v1.3.md"
            ],
        ),
        "scripts/run_quality_harness.py": (
            '"v0.6.1.json"',
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
        "project.schema.json",
        "frontmatter.schema.json",
        "technology-profile.schema.json",
        "technology-profile-lock.schema.json",
        "quality-observations.schema.json",
        "quality-report.schema.json",
        "pilot-config.schema.json",
        "pilot-observation.schema.json",
        "pilot-summary.schema.json",
        "catalogs.json",
        "project-1.1.schema.json",
        "frontmatter-1.1.schema.json",
        "project-1.2.schema.json",
        "frontmatter-1.2.schema.json",
        "project-1.3.schema.json",
        "frontmatter-1.3.schema.json",
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
    except (OSError, json.JSONDecodeError, AttributeError):
        errors.append("El ejemplo de piloto M5 no es legible o válido.")

    try:
        pilot_schema = json.loads(
            (root / "schemas" / "pilot-config.schema.json").read_text(encoding="utf-8")
        )
        schema_candidate = pilot_schema["properties"]["rollback"]["properties"][
            "candidate_version"
        ].get("const")
        if plugin_version and schema_candidate != plugin_version:
            errors.append(
                "pilot-config.schema.json debe fijar la misma candidate que el manifest."
            )
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
            "EXPECTED_BASELINE_COMMIT",
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
            "migrate",
            "client-view",
            "tasks",
            "planning",
            "continuity",
            "profiles",
        ):
            if f'"{command}"' not in cli_text:
                errors.append(f"El dispatcher portable no declara {command}.")

    try:
        project_schema = json.loads(
            (root / "schemas" / "project.schema.json").read_text(encoding="utf-8")
        )
        technology_properties = project_schema["properties"]["technology"]["properties"]
        if "proposals" in technology_properties:
            errors.append(
                "project.json no debe almacenar propuestas tecnológicas sustantivas."
            )
        blocker_items = project_schema["properties"]["open_blockers"]["items"]
        if blocker_items.get("type") != "string":
            errors.append(
                "open_blockers debe indexar IDs, no duplicar el texto de los bloqueos."
            )
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project.schema.json no expone el contrato operativo esperado.")

    try:
        project_11 = json.loads(
            (root / "schemas" / "project-1.1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required_11 = set(project_11["required"])
        properties_11 = project_11["properties"]
        if project_11["properties"]["schema_version"].get("const") != "1.1":
            errors.append("project-1.1.schema.json debe fijar schema_version 1.1.")
        if project_11["properties"]["method_version"].get("const") != "1.1.0":
            errors.append("project-1.1.schema.json debe fijar method_version 1.1.0.")
        if {"open_blockers", "readiness"} & (required_11 | set(properties_11)):
            errors.append(
                "El índice 1.1 no debe persistir open_blockers ni snapshots de readiness."
            )
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project-1.1.schema.json no expone el contrato derivado esperado.")

    try:
        project_12 = json.loads(
            (root / "schemas" / "project-1.2.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required_12 = set(project_12["required"])
        properties_12 = project_12["properties"]
        if properties_12["schema_version"].get("const") != "1.2":
            errors.append("project-1.2.schema.json debe fijar schema_version 1.2.")
        if properties_12["method_version"].get("const") != "1.2.0":
            errors.append("project-1.2.schema.json debe fijar method_version 1.2.0.")
        expected = {
            "active_plan",
            "active_task",
            "delivery_governance",
            "version_control",
            "last_verified_revision",
        }
        if not expected <= required_12:
            errors.append(
                "El índice 1.2 debe exigir gobierno, plan/tarea y revisión verificable."
            )
        technology_required = set(
            properties_12["technology"].get("required", [])
        )
        if "profile_bindings" not in technology_required:
            errors.append("El índice 1.2 debe exigir profile_bindings.")
        if {"open_blockers", "readiness"} & (
            required_12 | set(properties_12)
        ):
            errors.append(
                "El índice 1.2 no debe persistir bloqueos o readiness derivados."
            )
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project-1.2.schema.json no expone el contrato esperado.")

    try:
        project_13 = json.loads(
            (root / "schemas" / "project-1.3.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required_13 = set(project_13["required"])
        properties_13 = project_13["properties"]
        if properties_13["schema_version"].get("const") != "1.3":
            errors.append("project-1.3.schema.json debe fijar schema_version 1.3.")
        if properties_13["method_version"].get("const") != "1.3.0":
            errors.append("project-1.3.schema.json debe fijar method_version 1.3.0.")
        expected_13 = {
            "active_tasks", "planning", "authorizations", "executions",
            "last_verified_revision",
        }
        if not expected_13 <= required_13:
            errors.append(
                "El índice 1.3 debe exigir planificación, autorizaciones, ejecuciones y tareas activas."
            )
        planning_required = set(properties_13["planning"].get("required", []))
        if not {
            "policy", "specification_fingerprint", "planning_fingerprint",
        } <= planning_required:
            errors.append("El índice 1.3 no fija los fingerprints separados.")
        if {"open_blockers", "readiness"} & (required_13 | set(properties_13)):
            errors.append("El índice 1.3 no debe persistir readiness derivado.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project-1.3.schema.json no expone el contrato esperado.")

    try:
        quality_report = json.loads(
            (root / "schemas" / "quality-report.schema.json").read_text(
                encoding="utf-8"
            )
        )
        quality_required = set(quality_report["required"])
        source_contract = quality_report["properties"]["source"]
        if quality_report["properties"]["schema_version"].get("const") != "1.1":
            errors.append("quality-report.schema.json debe fijar schema_version 1.1.")
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
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
        relative = script.relative_to(root).as_posix()
        forbidden = imported_roots.intersection(FORBIDDEN_RUNTIME_IMPORTS).difference(
            RUNTIME_IMPORT_ALLOWLIST.get(relative, set())
        )
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
    print(f"VALID: LKS-SDD {version} contract (M0-M5 + compatible evolution)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
