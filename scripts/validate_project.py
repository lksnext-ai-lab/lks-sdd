#!/usr/bin/env python3
"""Validate an LKS-SDD project index and its essential Markdown contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCHEMA = PLUGIN_ROOT / "schemas" / "project.schema.json"
FRONTMATTER_SCHEMA = PLUGIN_ROOT / "schemas" / "frontmatter.schema.json"
CATALOGS = json.loads((PLUGIN_ROOT / "schemas" / "catalogs.json").read_text(encoding="utf-8"))
ID_PREFIX_PATTERN = "|".join(re.escape(prefix) for prefix in CATALOGS["identifier_prefixes"])
ID_RE = re.compile(rf"\b(?:{ID_PREFIX_PATTERN})-[0-9]{{3}}\b")
VALID_ELEMENT_STATES = set(CATALOGS["element_states"])
CORE_ARTIFACTS = {
    "ART-STATUS": ("docs/lks-sdd/00-control/project-status.md", "project-status"),
    "ART-SCOPE": ("docs/lks-sdd/00-control/scope-register.md", "scope-register"),
    "ART-OPEN": ("docs/lks-sdd/00-control/open-points.md", "open-points"),
    "ART-BRIEF": ("docs/lks-sdd/01-context/product-brief.md", "product-brief"),
    "ART-CONSTRAINTS": ("docs/lks-sdd/01-context/constraints.md", "constraints"),
    "ART-FR": ("docs/lks-sdd/02-requirements/functional-requirements.md", "functional-requirements"),
    "ART-NFR": ("docs/lks-sdd/02-requirements/non-functional-requirements.md", "non-functional-requirements"),
    "ART-TR": ("docs/lks-sdd/02-requirements/technical-requirements.md", "technical-requirements"),
    "ART-AC": ("docs/lks-sdd/02-requirements/acceptance-criteria.md", "acceptance-criteria"),
    "ART-SOLUTION": ("docs/lks-sdd/03-solution/solution-overview.md", "solution-overview"),
    "ART-INCREMENTS": ("docs/lks-sdd/04-delivery/increments.md", "increments"),
    "ART-RISK": ("docs/lks-sdd/04-delivery/risks-dependencies.md", "risks-dependencies"),
    "ART-QUALITY": ("docs/lks-sdd/05-quality/quality-strategy.md", "quality-strategy"),
    "ART-TRACE": ("docs/lks-sdd/05-quality/traceability.md", "traceability"),
}
REQUIRED_TABLE_HEADERS = {
    "ART-STATUS": [("Ruta", "Fase", "Puerta", "Incremento activo", "Readiness", "Próximo paso")],
    "ART-OPEN": [("ID", "State", "Question", "Impact", "Scope", "Blocking")],
    "ART-CONSTRAINTS": [("ID", "State", "Type", "Statement", "Source", "Impact")],
    "ART-FR": [("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")],
    "ART-NFR": [("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")],
    "ART-TR": [("ID", "State", "Statement", "Source", "Priority", "Acceptance", "Increment")],
    "ART-AC": [("ID", "State", "Condition", "Requirement", "Evidence")],
    "ART-SOLUTION": [
        ("ID", "State", "Option", "Support", "Fit", "Risks", "Alternative"),
        ("ID", "State", "Decision", "Requirements", "Impact"),
    ],
    "ART-INCREMENTS": [
        (
            "ID", "State", "In scope", "Out of scope", "Requirements", "Acceptance", "Decisions",
            "Data", "Identity", "Integrations", "Tests",
        )
    ],
    "ART-RISK": [("ID", "State", "Description", "Scope", "Impact", "Treatment", "Owner")],
    "ART-QUALITY": [("ID", "State", "Purpose", "Increment", "Acceptance")],
    "ART-TRACE": [("Requirement", "Acceptance", "Decision", "Increment", "Test", "Evidence")],
}


@dataclass
class ValidationReport:
    project_root: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_files: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "project_root": self.project_root,
            "errors": self.errors,
            "warnings": self.warnings,
            "checked_files": self.checked_files,
        }


def _matches_type(value: Any, expected: str) -> bool:
    mapping = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: type(item) is bool,
        "null": lambda item: item is None,
        "number": lambda item: isinstance(item, (int, float)) and type(item) is not bool,
        "integer": lambda item: isinstance(item, int) and type(item) is not bool,
    }
    return expected in mapping and mapping[expected](value)


def validate_json_schema(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    """Validate the JSON Schema subset used by this plugin without dependencies."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, option) for option in options):
            return [f"{location}: tipo inválido; se esperaba {options}."]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: debe ser {schema['const']!r}.")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: valor {value!r} fuera del catálogo permitido.")

    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{location}: texto demasiado corto.")
        pattern = schema.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            errors.append(f"{location}: no cumple el patrón {pattern!r}.")

    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{location}: contiene menos elementos de los requeridos.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_json_schema(item, item_schema, f"{location}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{location}: falta la propiedad obligatoria {key!r}.")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{location}: propiedad no admitida {key!r}.")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_json_schema(value[key], child_schema, f"{location}.{key}"))
    return errors


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("falta el delimitador inicial de front matter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("falta el delimitador final de front matter") from exc

    data: dict[str, Any] = {}
    list_key: str | None = None
    for line_number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if list_key is None or not isinstance(data.get(list_key), list):
                raise ValueError(f"lista sin clave en la línea {line_number}")
            data[list_key].append(_parse_scalar(line[4:]))
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"sintaxis no soportada en la línea {line_number}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"clave vacía en la línea {line_number}")
        if raw.strip():
            data[key] = _parse_scalar(raw)
            list_key = None
        else:
            data[key] = []
            list_key = key
    return data, "\n".join(lines[end + 1 :]).strip()


def parse_markdown_table_blocks(body: str) -> list[tuple[tuple[str, ...], list[dict[str, str]]]]:
    lines = body.splitlines()
    tables: list[tuple[tuple[str, ...], list[dict[str, str]]]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and separator_line.startswith("|")):
            index += 1
            continue
        headers = [cell.strip() for cell in header_line.strip("|").split("|")]
        separators = [cell.strip() for cell in separator_line.strip("|").split("|")]
        if len(headers) != len(separators) or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separators):
            index += 1
            continue
        rows: list[dict[str, str]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            index += 1
        tables.append((tuple(headers), rows))
    return tables


def parse_markdown_tables(body: str) -> list[list[dict[str, str]]]:
    return [rows for _, rows in parse_markdown_table_blocks(body)]


def _safe_relative_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None, f"ruta no permitida: {relative}"
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"ruta fuera de la raíz: {relative}"
    current = root
    for part in candidate.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            return None, f"la ruta usa un enlace simbólico: {relative}"
    return resolved, None


def load_project_manifest(project_root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = project_root / ".lks-sdd" / "project.json"
    if not path.is_file():
        return None, ["Falta .lks-sdd/project.json."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(PROJECT_SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"No se puede leer el índice o su esquema: {exc}"]
    return data, validate_json_schema(data, schema, "project")


def validate_project(project_root: Path) -> tuple[ValidationReport, dict[str, Any] | None, dict[str, dict[str, str]]]:
    root = project_root.expanduser().resolve()
    report = ValidationReport(project_root=str(root))
    if not root.is_dir():
        report.errors.append(f"La raíz no existe o no es una carpeta: {root}")
        return report, None, {}

    manifest, manifest_errors = load_project_manifest(root)
    report.errors.extend(manifest_errors)
    if manifest is None:
        return report, None, {}
    report.checked_files.append(".lks-sdd/project.json")
    if manifest_errors:
        return report, manifest, {}

    artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
    artifact_ids: set[str] = set()
    artifact_paths: set[str] = set()
    artifact_entries: dict[str, dict[str, Any]] = {}
    definitions: dict[str, dict[str, str]] = {}
    references: list[tuple[str, str]] = []
    frontmatter_schema = json.loads(FRONTMATTER_SCHEMA.read_text(encoding="utf-8"))

    for entry in artifacts if isinstance(artifacts, list) else []:
        if not isinstance(entry, dict):
            continue
        artifact_id = entry.get("id")
        relative = entry.get("path")
        if artifact_id in artifact_ids:
            report.errors.append(f"Identificador de artefacto duplicado: {artifact_id}")
        artifact_ids.add(artifact_id)
        if isinstance(artifact_id, str):
            artifact_entries.setdefault(artifact_id, entry)
        if relative in artifact_paths:
            report.errors.append(f"Ruta de artefacto duplicada: {relative}")
        artifact_paths.add(relative)
        if not isinstance(relative, str):
            continue
        path, path_error = _safe_relative_file(root, relative)
        if path_error:
            report.errors.append(path_error)
            continue
        if path is None or not path.is_file():
            if entry.get("required"):
                report.errors.append(f"Falta el artefacto obligatorio: {relative}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
            metadata, body = parse_frontmatter(text)
        except (OSError, UnicodeError, ValueError) as exc:
            report.errors.append(f"{relative}: Markdown inválido: {exc}")
            continue
        report.checked_files.append(relative)
        report.errors.extend(
            f"{relative}: {error}" for error in validate_json_schema(metadata, frontmatter_schema, "frontmatter")
        )
        if metadata.get("artifact_id") != artifact_id:
            report.errors.append(f"{relative}: artifact_id no coincide con el índice.")
        if metadata.get("project_id") != manifest.get("project_id"):
            report.errors.append(f"{relative}: project_id no coincide con el índice.")
        if metadata.get("baseline_id") != manifest.get("baseline_id"):
            report.errors.append(f"{relative}: baseline_id no coincide con el índice.")
        core_contract = CORE_ARTIFACTS.get(artifact_id)
        if core_contract and metadata.get("artifact_type") != core_contract[1]:
            report.errors.append(
                f"{relative}: artifact_type debe ser {core_contract[1]!r} para {artifact_id}."
            )
        if not body or not re.search(r"^#\s+\S", body, re.MULTILINE):
            report.errors.append(f"{relative}: el cuerpo no contiene un título y contenido legible.")
        if re.search(r"\{\{[A-Z0-9_]+\}\}", text):
            report.errors.append(f"{relative}: contiene tokens de plantilla sin resolver.")

        table_blocks = parse_markdown_table_blocks(body)
        actual_headers = {headers for headers, _ in table_blocks}
        for required_headers in REQUIRED_TABLE_HEADERS.get(artifact_id, []):
            if required_headers not in actual_headers:
                report.errors.append(
                    f"{relative}: falta la tabla contractual con cabeceras {list(required_headers)!r}."
                )

        for _, table in table_blocks:
            for row in table:
                element_id = row.get("ID")
                if element_id:
                    if not ID_RE.fullmatch(element_id):
                        report.errors.append(f"{relative}: identificador inválido {element_id!r}.")
                    elif element_id in definitions:
                        report.errors.append(f"Identificador de elemento duplicado: {element_id}")
                    else:
                        definitions[element_id] = {
                            "path": relative,
                            "artifact_type": metadata.get("artifact_type", "unknown"),
                            **row,
                        }
                state = row.get("State")
                if state and state not in VALID_ELEMENT_STATES:
                    report.errors.append(f"{relative}: estado de elemento no admitido {state!r}.")
                for column, cell in row.items():
                    if column != "ID":
                        references.extend((relative, item) for item in ID_RE.findall(cell))

    for relative, reference in references:
        if reference not in definitions:
            report.errors.append(f"{relative}: referencia sin definición: {reference}")

    for artifact_id, (expected_path, _) in CORE_ARTIFACTS.items():
        entry = artifact_entries.get(artifact_id)
        if entry is None:
            report.errors.append(f"Falta el artefacto del núcleo en el índice: {artifact_id}")
            continue
        if entry.get("path") != expected_path:
            report.errors.append(
                f"{artifact_id}: la ruta canónica debe ser {expected_path!r}, no {entry.get('path')!r}."
            )
        if entry.get("required") is not True:
            report.errors.append(f"{artifact_id}: el artefacto del núcleo debe ser obligatorio.")

    indexed_blockers = set(manifest.get("open_blockers", []))
    for blocker_id in indexed_blockers:
        blocker = definitions.get(blocker_id)
        if blocker is None or not blocker.get("path", "").endswith("open-points.md"):
            report.errors.append(f"El índice referencia un bloqueo sin definición en ART-OPEN: {blocker_id}")
        elif blocker.get("State") not in {"open", "blocked"}:
            report.errors.append(f"El bloqueo indexado {blocker_id} no está open ni blocked.")
        elif blocker.get("Blocking", "").strip().lower() != "true":
            report.errors.append(f"El bloqueo indexado {blocker_id} no declara Blocking=true en ART-OPEN.")
    for item_id, item in definitions.items():
        if not item.get("path", "").endswith("open-points.md"):
            continue
        is_blocking = item.get("Blocking", "").strip().lower() == "true"
        is_open = item.get("State") in {"open", "blocked"}
        if is_blocking and is_open and item_id not in indexed_blockers:
            report.errors.append(f"El bloqueo {item_id} está activo en ART-OPEN pero no aparece en el índice.")

    technology = manifest.get("technology", {})
    selected_profile = technology.get("selected_profile") if isinstance(technology, dict) else None
    selection_decision = technology.get("selection_decision") if isinstance(technology, dict) else None
    if selected_profile is not None and selection_decision is None:
        report.errors.append("Un perfil seleccionado requiere selection_decision en el índice.")
    if selected_profile is not None and technology.get("preferred_stack_assessed") is not True:
        report.errors.append("Un perfil seleccionado requiere preferred_stack_assessed=true.")
    if selection_decision is not None:
        decision = definitions.get(selection_decision)
        if selected_profile is None:
            report.errors.append("selection_decision no puede existir sin selected_profile.")
        if decision is None or decision.get("artifact_type") not in {
            "solution-overview",
            "architecture-decision",
        }:
            report.errors.append(
                f"La decisión de perfil {selection_decision} no está definida en un artefacto de solución o ADR."
            )
        elif decision.get("State") not in {"decision", "confirmed"}:
            report.errors.append(
                f"La decisión de perfil {selection_decision} no está confirmada; estado: {decision.get('State')}."
            )
        elif selected_profile not in " ".join(decision.values()):
            report.errors.append(
                f"La decisión {selection_decision} no identifica el perfil seleccionado {selected_profile}."
            )

    for field, increment_id in (
        ("active_increment", manifest.get("active_increment")),
        ("readiness.assessed_increment", manifest.get("readiness", {}).get("assessed_increment")),
    ):
        if increment_id is None:
            continue
        increment = definitions.get(increment_id)
        if increment is None or not increment.get("path", "").endswith("increments.md"):
            report.errors.append(f"{field} referencia un incremento no definido: {increment_id}")

    if manifest.get("route") == "adopt-existing":
        adoption = manifest.get("adoption")
        if not isinstance(adoption, dict):
            report.errors.append("La ruta adopt-existing requiere el bloque adoption.")
    elif "adoption" in manifest:
        report.warnings.append("La ruta new no necesita un bloque adoption.")

    return report, manifest, definitions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, _, _ = validate_project(args.project_root)
    if args.as_json:
        print(json.dumps(report.as_dict(), indent=2, ensure_ascii=False))
    else:
        print("VALID" if report.valid else "INVALID")
        print(f"Checked files: {len(report.checked_files)}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        for error in report.errors:
            print(f"ERROR: {error}")
    return 0 if report.valid else 2


if __name__ == "__main__":
    sys.exit(main())
