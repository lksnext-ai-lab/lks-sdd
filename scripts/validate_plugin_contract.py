#!/usr/bin/env python3
"""Validate LKS-SDD M0-M1 invariants beyond the official plugin validator."""

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
}
BACKLOG_SKILLS = {
    "lks-sdd-adopt-existing",
    "lks-sdd-implement",
    "lks-sdd-verify",
}
CANONICAL_HASHES = {
    "LKS-SDD_definicion_plugin_v1.md": "4DE2D0AE75B2FF75BBC0C38D05C38AC2D90B57EA4472D46A85BF33C597D79700",
    "LKS-SDD_paquete_preimplementacion_v0.1.md": "A5FFD0D5CA1D9B7AC96D1DABB4A411739E18A01345348D9250F857D5F941504B",
    "LKS-SDD_baseline_normativa_candidata_v0.1.md": "083DED8FB14D77D899CB4F955AEA67D9A21FBA66AC25D7CF28D8C5111C1D1162",
}
REQUIRED_ROOT_FILES = {
    "README.md",
    "CHANGELOG.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    "docs/ARCHITECTURE.md",
    "docs/M1-COVERAGE.md",
    "docs/VALIDATION.md",
}
REQUIRED_SKILL_RESOURCES = {
    "lks-sdd-help": {
        "references/sdd-concepts.md",
        "references/project-lifecycle.md",
        "references/capabilities-and-limits.md",
        "references/product-reality.md",
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
        "scripts/init_project.py",
        "agents/openai.yaml",
    },
    "lks-sdd-assess-readiness": {
        "references/readiness-rubric.md",
        "scripts/assess_readiness.py",
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
    "05-quality/test-strategy.md",
    "06-operation/deployment.md",
    "06-operation/observability.md",
    "06-operation/operations.md",
}
FORBIDDEN_RUNTIME_IMPORTS = {"ftplib", "httpx", "requests", "smtplib", "socket", "subprocess", "urllib"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in sorted(REQUIRED_ROOT_FILES):
        if not (root / relative).is_file():
            errors.append(f"Falta archivo de gobierno o documentación: {relative}")
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Manifest ilegible: {exc}"]
    if manifest.get("name") != "lks-sdd":
        errors.append("El nombre del manifest debe ser lks-sdd.")
    if manifest.get("version") != "0.1.0":
        errors.append("El incremento M0-M1 debe declarar la versión 0.1.0.")
    for unsupported in ("apps", "mcpServers", "hooks"):
        if unsupported in manifest:
            errors.append(f"El manifest no puede declarar {unsupported} en M0-M1.")

    skills_root = root / "skills"
    discovered = {path.name for path in skills_root.iterdir() if path.is_dir()} if skills_root.is_dir() else set()
    if discovered != EXPECTED_SKILLS:
        errors.append(f"Skills descubribles inesperadas: {sorted(discovered)}")
    for name in BACKLOG_SKILLS:
        if (skills_root / name).exists():
            errors.append(f"La skill de backlog no debe aparentar implementación: {name}")

    for skill, resources in REQUIRED_SKILL_RESOURCES.items():
        skill_root = skills_root / skill
        for relative in sorted(resources):
            if not (skill_root / relative).is_file():
                errors.append(f"Falta recurso de {skill}: {relative}")
        agent_config = skill_root / "agents" / "openai.yaml"
        if agent_config.is_file() and "allow_implicit_invocation: true" not in agent_config.read_text(encoding="utf-8"):
            errors.append(f"La invocación implícita debe seguir activa en {skill}.")

    template_root = skills_root / "lks-sdd-define" / "assets" / "templates"
    for relative in sorted(REQUIRED_CONDITIONAL_TEMPLATES):
        if not (template_root / relative).is_file():
            errors.append(f"Falta plantilla condicional: {relative}")

    for forbidden in (".mcp.json", ".app.json", "hooks", "agents"):
        if (root / forbidden).exists():
            errors.append(f"Componente raíz fuera de alcance: {forbidden}")

    for filename, expected in CANONICAL_HASHES.items():
        path = root / "specs" / "canonical" / filename
        if not path.is_file():
            errors.append(f"Falta especificación canónica: {filename}")
        elif sha256(path) != expected:
            errors.append(f"Hash no canónico: {filename}")

    for schema_name in (
        "project.schema.json",
        "frontmatter.schema.json",
        "technology-profile.schema.json",
        "technology-profile-lock.schema.json",
        "catalogs.json",
    ):
        try:
            json.loads((root / "schemas" / schema_name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Schema inválido {schema_name}: {exc}")

    try:
        project_schema = json.loads((root / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
        technology_properties = project_schema["properties"]["technology"]["properties"]
        if "proposals" in technology_properties:
            errors.append("project.json no debe almacenar propuestas tecnológicas sustantivas.")
        blocker_items = project_schema["properties"]["open_blockers"]["items"]
        if blocker_items.get("type") != "string":
            errors.append("open_blockers debe indexar IDs, no duplicar el texto de los bloqueos.")
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        errors.append("project.schema.json no expone el contrato operativo esperado.")

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
        for markdown in [skill_root / "SKILL.md", *sorted((skill_root / "references").glob("*.md"))]:
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
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
        forbidden = imported_roots.intersection(FORBIDDEN_RUNTIME_IMPORTS)
        if forbidden:
            errors.append(
                f"Script M1 con import de red o ejecución externa {script.relative_to(root)}: {sorted(forbidden)}"
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
    print("VALID: LKS-SDD M0-M1 contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
