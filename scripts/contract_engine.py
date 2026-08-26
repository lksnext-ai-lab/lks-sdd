#!/usr/bin/env python3
"""Shared declarative contract engine for LKS-SDD Markdown projects.

The module deliberately has no dependency on the workflow CLIs.  It provides
one parser and one normalized graph that validation, help, readiness,
implementation, and verification can consume without interpreting reference
cells independently.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = PLUGIN_ROOT / "schemas" / "document-contracts.json"
ELEMENT_ID_RE = re.compile(r"^(?P<prefix>[A-Z][A-Z0-9]*)-(?P<number>[0-9]{3})$")
TRACKING_IDENTIFIER_PREFIXES = frozenset({"TRK", "SYNC"})
V15_ONLY_IDENTIFIER_PREFIXES = frozenset({"RPT"})
ARTIFACT_MARKER_RE = re.compile(r"\bART-[A-Z0-9-]+\b")
MARKDOWN_IMAGE_RE = re.compile(r"^!\[[^\]]*\]\(([^)]+)\)$")
EMPTY_REFERENCE_VALUES = {"", "none", "n/a"}
APPLICABILITY_VALUES = {"pending", "not-applicable"}


class ContractEngineError(ValueError):
    """Raised when the packaged registry itself is inconsistent."""


@dataclass(frozen=True)
class SourceLocation:
    path: str | None = None
    artifact_id: str | None = None
    table_id: str | None = None
    row: int | None = None
    column: str | None = None
    source_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "path": self.path,
                "artifact_id": self.artifact_id,
                "table_id": self.table_id,
                "row": self.row,
                "column": self.column,
                "source_id": self.source_id,
            }.items()
            if value is not None
        }


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    stage: str
    message: str
    location: SourceLocation = SourceLocation()
    observed: Any = None
    expected: Any = None
    remediation: str | None = None
    cause: str | None = None

    def as_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "stage": self.stage,
            "message": self.message,
            "location": self.location.as_dict(),
        }
        for key, item in (
            ("observed", self.observed),
            ("expected", self.expected),
            ("remediation", self.remediation),
            ("cause", self.cause),
        ):
            if item is not None:
                value[key] = item
        return value

    @property
    def deduplication_key(self) -> tuple[Any, ...]:
        location = self.location
        return (
            self.code,
            self.severity,
            self.stage,
            location.path,
            location.artifact_id,
            location.table_id,
            location.row,
            location.column,
            location.source_id,
            json.dumps(self.observed, sort_keys=True, ensure_ascii=True, default=str),
            self.cause,
        )


def deduplicate_diagnostics(items: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    seen: set[tuple[Any, ...]] = set()
    result: list[Diagnostic] = []
    for item in items:
        key = item.deduplication_key
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


@dataclass(frozen=True)
class StatePolicy:
    name: str
    allowed: frozenset[str]
    active: frozenset[str]
    pending: frozenset[str]
    inactive: frozenset[str]
    legacy_classes: Mapping[str, str]

    def allowed_for(self, schema_version: str) -> frozenset[str]:
        if schema_version == "1.0":
            return self.allowed | frozenset(self.legacy_classes)
        return self.allowed

    def classify(self, value: str, schema_version: str) -> str:
        if value in self.active:
            return "active"
        if value in self.pending:
            return "pending"
        if value in self.inactive:
            return "inactive"
        if schema_version == "1.0" and value in self.legacy_classes:
            return self.legacy_classes[value]
        return "invalid"


@dataclass(frozen=True)
class RelationSpec:
    column: str
    targets: frozenset[str]
    minimum: int
    maximum: int | None
    active_input: bool
    require_defined: bool = True
    allow_empty: bool = False
    allow_applicability: frozenset[str] = frozenset()
    allow_legacy_artifact_marker: bool = False
    targets_by_column: str | None = None
    targets_by_value: Mapping[str, frozenset[str]] = field(default_factory=dict)

    def targets_for(self, cells: Mapping[str, str]) -> frozenset[str]:
        if self.targets_by_column is None:
            return self.targets
        discriminator = cells.get(self.targets_by_column, "").strip().casefold()
        return self.targets_by_value.get(discriminator, frozenset())


@dataclass(frozen=True)
class ApplicabilitySpec:
    domain_column: str
    applicability_column: str
    references_column: str
    reason_column: str
    domains: tuple[str, ...]


@dataclass(frozen=True)
class AssetSpec:
    path_column: str
    hash_column: str


@dataclass(frozen=True)
class TableContract:
    artifact_id: str
    table_id: str
    headers: tuple[str, ...]
    minimum_occurrences: int
    maximum_occurrences: int | None
    key_column: str | None
    key_prefixes: frozenset[str]
    state_column: str | None
    state_policy: str | None
    scope_column: str | None
    relations: Mapping[str, RelationSpec]
    applicability: ApplicabilitySpec | None
    asset: AssetSpec | None


@dataclass(frozen=True)
class ArtifactContract:
    artifact_id: str
    artifact_type: str
    path: str | None
    required: bool
    tables: tuple[TableContract, ...]

    @property
    def tables_by_headers(self) -> Mapping[tuple[str, ...], TableContract]:
        return {table.headers: table for table in self.tables}


@dataclass(frozen=True)
class ContractRegistry:
    catalog_version: str
    schema_version: str
    identifier_prefixes: frozenset[str]
    max_range_size: int
    state_policies: Mapping[str, StatePolicy]
    artifacts: Mapping[str, ArtifactContract]

    def artifact_for(
        self, artifact_id: str, artifact_type: str | None = None
    ) -> ArtifactContract | None:
        exact = self.artifacts.get(artifact_id)
        if exact is not None:
            return exact
        if artifact_type:
            matches = [
                artifact
                for artifact in self.artifacts.values()
                if artifact.artifact_type == artifact_type
            ]
            if len(matches) == 1:
                return matches[0]
        return None


@dataclass(frozen=True)
class ReferenceResult:
    references: tuple[str, ...]
    canonical: str | None
    applicability: str | None
    reason: str | None
    syntax: str
    diagnostics: tuple[Diagnostic, ...]

    @property
    def valid(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)


@dataclass
class ProjectRow:
    uid: str
    artifact_id: str
    artifact_type: str
    path: str
    table_id: str
    line: int
    cells: dict[str, str]
    contract: TableContract
    key: str | None = None
    state: str | None = None
    state_class: str = "neutral"
    reference_results: dict[str, ReferenceResult] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectEdge:
    source_uid: str
    source_id: str | None
    column: str
    target_id: str
    active_input: bool
    require_defined: bool


@dataclass(frozen=True)
class ProjectAsset:
    owner_id: str
    path: str
    sha256: str | None
    declared_sha256: str | None
    state_class: str


@dataclass
class ProjectModel:
    root: Path
    schema_version: str
    manifest: dict[str, Any]
    registry: ContractRegistry | None
    rows: dict[str, ProjectRow]
    nodes: dict[str, ProjectRow]
    edges: tuple[ProjectEdge, ...]
    assets: tuple[ProjectAsset, ...]
    diagnostics: tuple[Diagnostic, ...]
    checked_files: tuple[str, ...]
    source_hashes: Mapping[str, str]

    @property
    def valid(self) -> bool:
        return not any(item.severity == "error" for item in self.diagnostics)


@dataclass(frozen=True)
class ActiveContract:
    increment: str
    project: Mapping[str, Any]
    rows: tuple[ProjectRow, ...]
    node_ids: tuple[str, ...]
    edges: tuple[ProjectEdge, ...]
    assets: tuple[ProjectAsset, ...]
    diagnostics: tuple[Diagnostic, ...]
    checked_files: tuple[str, ...]
    fingerprint: str


def _read_catalog(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractEngineError(
            f"No se puede leer el catálogo documental: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise ContractEngineError("El catálogo documental debe ser un objeto JSON.")
    return value


def _validate_catalog(value: Mapping[str, Any]) -> None:
    required = {
        "catalog_version",
        "supported_project_schemas",
        "schema_inheritance",
        "identifier_prefixes",
        "reference_grammar",
        "state_policies",
        "artifacts",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ContractEngineError(f"Catálogo incompleto; faltan {missing}.")
    if value.get("catalog_version") != "1.5":
        raise ContractEngineError(
            "El catálogo documental debe usar catalog_version 1.5."
        )
    supported = value.get("supported_project_schemas")
    if not isinstance(supported, list) or set(supported) != {
        "1.0", "1.1", "1.2", "1.3", "1.4", "1.5"
    }:
        raise ContractEngineError(
            "El catálogo debe declarar soporte explícito 1.0 a 1.5."
        )
    inheritance = value.get("schema_inheritance")
    if inheritance != {
        "1.2": "1.1",
        "1.3": "1.2",
        "1.4": "1.3",
        "1.5": "1.4",
    }:
        raise ContractEngineError(
            "schema_inheritance debe declarar la cadena 1.2 -> 1.1 hasta 1.5 -> 1.4."
        )
    prefixes = value.get("identifier_prefixes")
    if (
        not isinstance(prefixes, list)
        or not prefixes
        or len(prefixes) != len(set(prefixes))
        or any(re.fullmatch(r"[A-Z][A-Z0-9]*", item or "") is None for item in prefixes)
    ):
        raise ContractEngineError(
            "identifier_prefixes es inválido o contiene duplicados."
        )
    policies = value.get("state_policies")
    if not isinstance(policies, dict) or not policies:
        raise ContractEngineError("Faltan políticas de estado por tabla.")
    for name, raw in policies.items():
        if not isinstance(raw, dict):
            raise ContractEngineError(f"Política de estado inválida: {name}")
        allowed = set(raw.get("allowed", []))
        active = set(raw.get("active", []))
        pending = set(raw.get("pending", []))
        inactive = set(raw.get("inactive", []))
        classified = active | pending | inactive
        if not classified <= allowed:
            raise ContractEngineError(
                f"La política {name} clasifica estados fuera de allowed."
            )
        if active & pending or active & inactive or pending & inactive:
            raise ContractEngineError(
                f"La política {name} tiene clasificaciones de estado solapadas."
            )
        legacy = raw.get("legacy_classes", {})
        if not isinstance(legacy, dict) or any(
            item not in {"active", "pending", "inactive"} for item in legacy.values()
        ):
            raise ContractEngineError(f"legacy_classes inválido en {name}.")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ContractEngineError("El catálogo no declara artefactos.")
    table_ids: set[str] = set()
    declared_prefixes = set(prefixes)
    for artifact_id, artifact in artifacts.items():
        if re.fullmatch(r"ART-[A-Z0-9-]+", artifact_id) is None:
            raise ContractEngineError(
                f"artifact_id inválido en catálogo: {artifact_id}"
            )
        if not isinstance(artifact, dict) or not isinstance(
            artifact.get("tables"), list
        ):
            raise ContractEngineError(f"Contrato de artefacto inválido: {artifact_id}")
        for table in artifact["tables"]:
            table_id = table.get("id") if isinstance(table, dict) else None
            headers = table.get("headers") if isinstance(table, dict) else None
            schemas = table.get("schemas") if isinstance(table, dict) else None
            if not isinstance(table_id, str) or table_id in table_ids:
                raise ContractEngineError(f"table_id ausente o duplicado: {table_id}")
            table_ids.add(table_id)
            if (
                not isinstance(headers, list)
                or not headers
                or len(headers) != len(set(headers))
            ):
                raise ContractEngineError(f"Cabeceras inválidas en {table_id}.")
            if not isinstance(schemas, list) or not set(schemas) <= set(supported):
                raise ContractEngineError(f"Schemas inválidos en {table_id}.")
            key = table.get("key")
            if key:
                if key.get("column") not in headers:
                    raise ContractEngineError(f"Key fuera de cabeceras en {table_id}.")
                if not set(key.get("prefixes", [])) <= declared_prefixes:
                    raise ContractEngineError(
                        f"Prefijo de key no declarado en {table_id}."
                    )
            state = table.get("state")
            if state:
                if state.get("column") not in headers:
                    raise ContractEngineError(
                        f"State fuera de cabeceras en {table_id}."
                    )
                if state.get("policy") not in policies:
                    raise ContractEngineError(f"Política desconocida en {table_id}.")
            if table.get("scope_column") and table["scope_column"] not in headers:
                raise ContractEngineError(
                    f"scope_column fuera de cabeceras en {table_id}."
                )
            for column, relation in table.get("relations", {}).items():
                if column not in headers:
                    raise ContractEngineError(
                        f"Relación {column!r} fuera de cabeceras en {table_id}."
                    )
                if not set(relation.get("targets", [])) <= declared_prefixes:
                    raise ContractEngineError(
                        f"Relación con prefijo desconocido en {table_id}.{column}."
                    )
                targets_by = relation.get("targets_by")
                if targets_by:
                    if targets_by.get("column") not in headers:
                        raise ContractEngineError(
                            f"Discriminador fuera de cabeceras en {table_id}.{column}."
                        )
                    for dynamic in targets_by.get("values", {}).values():
                        if not set(dynamic) <= declared_prefixes:
                            raise ContractEngineError(
                                f"Prefijo dinámico desconocido en {table_id}.{column}."
                            )


def load_registry(
    schema_version: str = "1.1", catalog_path: Path | None = None
) -> ContractRegistry:
    """Load and internally validate the registry for one project schema."""

    path = (catalog_path or DEFAULT_CATALOG).resolve()
    value = _read_catalog(path)
    _validate_catalog(value)
    if schema_version not in value["supported_project_schemas"]:
        raise ContractEngineError(
            f"Schema de proyecto no soportado por el catálogo: {schema_version!r}."
        )
    policies = {
        name: StatePolicy(
            name=name,
            allowed=frozenset(raw["allowed"]),
            active=frozenset(raw["active"]),
            pending=frozenset(raw["pending"]),
            inactive=frozenset(raw["inactive"]),
            legacy_classes=dict(raw.get("legacy_classes", {})),
        )
        for name, raw in value["state_policies"].items()
    }
    artifacts: dict[str, ArtifactContract] = {}
    for artifact_id, raw_artifact in value["artifacts"].items():
        table_schema = schema_version
        inheritance = value.get("schema_inheritance", {})
        visited_schemas: set[str] = set()
        while not any(
            table_schema in raw_table.get("schemas", [])
            for raw_table in raw_artifact["tables"]
            if isinstance(raw_table, dict)
        ):
            if table_schema in visited_schemas or table_schema not in inheritance:
                break
            visited_schemas.add(table_schema)
            table_schema = inheritance[table_schema]
        tables: list[TableContract] = []
        for raw_table in raw_artifact["tables"]:
            if table_schema not in raw_table["schemas"]:
                continue
            relations: dict[str, RelationSpec] = {}
            for column, raw_relation in raw_table.get("relations", {}).items():
                raw_targets_by = raw_relation.get("targets_by") or {}
                relations[column] = RelationSpec(
                    column=column,
                    targets=frozenset(raw_relation.get("targets", [])),
                    minimum=int(raw_relation.get("min", 0)),
                    maximum=raw_relation.get("max"),
                    active_input=bool(raw_relation.get("active_input", False)),
                    require_defined=bool(raw_relation.get("require_defined", True)),
                    allow_empty=bool(raw_relation.get("allow_empty", False)),
                    allow_applicability=frozenset(
                        raw_relation.get("allow_applicability", [])
                    ),
                    allow_legacy_artifact_marker=bool(
                        raw_relation.get("allow_legacy_artifact_marker", False)
                    ),
                    targets_by_column=raw_targets_by.get("column"),
                    targets_by_value={
                        key.casefold(): frozenset(targets)
                        for key, targets in raw_targets_by.get("values", {}).items()
                    },
                )
            raw_key = raw_table.get("key") or {}
            raw_state = raw_table.get("state") or {}
            raw_applicability = raw_table.get("applicability")
            raw_asset = raw_table.get("asset")
            tables.append(
                TableContract(
                    artifact_id=artifact_id,
                    table_id=raw_table["id"],
                    headers=tuple(raw_table["headers"]),
                    minimum_occurrences=int(raw_table.get("min_occurs", 0)),
                    maximum_occurrences=raw_table.get("max_occurs"),
                    key_column=raw_key.get("column"),
                    key_prefixes=frozenset(raw_key.get("prefixes", [])),
                    state_column=raw_state.get("column"),
                    state_policy=raw_state.get("policy"),
                    scope_column=raw_table.get("scope_column"),
                    relations=relations,
                    applicability=(
                        ApplicabilitySpec(
                            domain_column=raw_applicability["domain_column"],
                            applicability_column=raw_applicability[
                                "applicability_column"
                            ],
                            references_column=raw_applicability["references_column"],
                            reason_column=raw_applicability["reason_column"],
                            domains=tuple(raw_applicability["domains"]),
                        )
                        if raw_applicability
                        else None
                    ),
                    asset=(
                        AssetSpec(
                            path_column=raw_asset["path_column"],
                            hash_column=raw_asset["hash_column"],
                        )
                        if raw_asset
                        else None
                    ),
                )
            )
        artifacts[artifact_id] = ArtifactContract(
            artifact_id=artifact_id,
            artifact_type=raw_artifact["artifact_type"],
            path=raw_artifact.get("path"),
            required=bool(raw_artifact.get("required", False))
            or schema_version in raw_artifact.get("required_schemas", []),
            tables=tuple(tables),
        )
    identifier_prefixes = set(value["identifier_prefixes"])
    if schema_version not in {"1.4", "1.5"}:
        identifier_prefixes -= TRACKING_IDENTIFIER_PREFIXES
    if schema_version != "1.5":
        identifier_prefixes -= V15_ONLY_IDENTIFIER_PREFIXES
    return ContractRegistry(
        catalog_version=value["catalog_version"],
        schema_version=schema_version,
        identifier_prefixes=frozenset(identifier_prefixes),
        max_range_size=int(value["reference_grammar"]["max_range_size"]),
        state_policies=policies,
        artifacts=artifacts,
    )


def _diagnostic(
    code: str,
    message: str,
    *,
    location: SourceLocation,
    severity: str = "error",
    stage: str = "structure",
    observed: Any = None,
    expected: Any = None,
    remediation: str | None = None,
    cause: str | None = None,
) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=severity,
        stage=stage,
        message=message,
        location=location,
        observed=observed,
        expected=expected,
        remediation=remediation,
        cause=cause,
    )


def _clean_reference_text(value: str) -> str:
    return value.strip().replace("`", "")


def _parse_element_id(value: str) -> tuple[str, int] | None:
    match = ELEMENT_ID_RE.fullmatch(value)
    if match is None:
        return None
    return match.group("prefix"), int(match.group("number"))


def parse_reference_cell(
    value: str,
    relation: RelationSpec,
    known_ids: Iterable[str] | None = None,
    *,
    mode: str = "strict",
    location: SourceLocation = SourceLocation(),
    max_range_size: int = 999,
) -> ReferenceResult:
    """Parse one declared relation cell without accepting partial ranges.

    ``strict`` accepts single IDs, comma/semicolon lists, and inclusive ``..``
    ranges. ``compat`` additionally accepts the legacy Spanish ``a`` range and
    old ``ART-*`` markers, but always emits a migration warning.
    """

    if mode not in {"strict", "compat"}:
        raise ValueError("mode debe ser 'strict' o 'compat'.")
    raw = _clean_reference_text(value or "")
    lowered = raw.casefold()
    diagnostics: list[Diagnostic] = []
    if lowered in EMPTY_REFERENCE_VALUES:
        if not relation.allow_empty:
            message = (
                "La relación requiere al menos una referencia."
                if relation.minimum > 0
                else "La relación no admite una celda vacía."
            )
            expected = (
                f"mínimo {relation.minimum}"
                if relation.minimum > 0
                else "ID explícito o aplicabilidad permitida con motivo"
            )
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-REQUIRED",
                    message,
                    location=location,
                    observed=raw,
                    expected=expected,
                    remediation="Añada IDs explícitos o documente una aplicabilidad permitida con motivo.",
                )
            )
        return ReferenceResult((), None, None, None, "empty", tuple(diagnostics))

    for applicability in sorted(APPLICABILITY_VALUES, key=len, reverse=True):
        if lowered == applicability or lowered.startswith(applicability + ":"):
            reason = raw.partition(":")[2].strip()
            if applicability not in relation.allow_applicability:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-APPLICABILITY-NOT-ALLOWED",
                        f"{applicability} no está permitido en esta relación.",
                        location=location,
                        observed=raw,
                        expected=sorted(relation.allow_applicability),
                    )
                )
            if not reason:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-APPLICABILITY-REASON",
                        f"{applicability} requiere un motivo explícito.",
                        location=location,
                        observed=raw,
                        remediation=f"Use `{applicability}: motivo`.",
                    )
                )
            return ReferenceResult(
                (),
                f"{applicability}: {reason}" if reason else applicability,
                applicability,
                reason or None,
                "applicability",
                tuple(diagnostics),
            )

    artifact_markers = ARTIFACT_MARKER_RE.findall(raw)
    if artifact_markers:
        if mode == "compat" and relation.allow_legacy_artifact_marker:
            raw = ARTIFACT_MARKER_RE.sub(" ", raw).strip()
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-LEGACY-ARTIFACT-MARKER",
                    "Se ignoró un marcador ART-* heredado; no expande elementos implícitamente.",
                    location=location,
                    severity="warning",
                    observed=artifact_markers,
                    remediation="Elimine ART-* y enumere únicamente los IDs activos.",
                )
            )
        else:
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-ARTIFACT-MARKER",
                    "Una relación activa no admite referencias ART-*.",
                    location=location,
                    observed=artifact_markers,
                    remediation="Enumere IDs de fila concretos o un rango canónico resuelto.",
                )
            )

    # 1.0 projects often separated IDs only with spaces. Accept this only in
    # compatibility mode and normalize it to the declared list grammar.
    id_pattern = r"[A-Z][A-Z0-9]*-[0-9]{3}"
    whitespace_list = re.fullmatch(rf"\s*{id_pattern}(?:\s+{id_pattern})+\s*", raw)
    if whitespace_list:
        if mode == "compat":
            raw = ", ".join(re.findall(id_pattern, raw))
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-LEGACY-WHITESPACE-LIST",
                    "Se normalizó una lista heredada separada solo por espacios.",
                    location=location,
                    severity="warning",
                    remediation="Separe IDs con coma o punto y coma.",
                )
            )
        else:
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-LIST-SEPARATOR",
                    "Las listas de referencias deben usar coma o punto y coma.",
                    location=location,
                    observed=value,
                    remediation="Use `FR-001, FR-002`.",
                )
            )

    parts = [item.strip() for item in re.split(r"[;,]", raw) if item.strip()]
    if not parts and not diagnostics:
        diagnostics.append(
            _diagnostic(
                "LKS-REF-SYNTAX",
                "La celda no contiene una referencia reconocible.",
                location=location,
                observed=value,
            )
        )
    known = set(known_ids) if known_ids is not None else None
    expanded: list[str] = []
    canonical_parts: list[str] = []
    syntax = "canonical"
    for part in parts:
        canonical_match = re.fullmatch(rf"({id_pattern})\s*\.\.\s*({id_pattern})", part)
        legacy_match = re.fullmatch(
            rf"({id_pattern})\s+a\s+({id_pattern})", part, re.IGNORECASE
        )
        if legacy_match:
            if mode != "compat":
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-LEGACY-RANGE",
                        "El rango heredado con `a` no es válido en schema 1.1.",
                        location=location,
                        observed=part,
                        expected="PREFIX-001..PREFIX-999",
                        remediation="Sustituya `a` por el operador inclusivo `..`.",
                    )
                )
                continue
            canonical_match = legacy_match
            syntax = "legacy"
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-LEGACY-RANGE",
                    "Se expandió un rango heredado con `a`.",
                    location=location,
                    severity="warning",
                    observed=part,
                    remediation="Migre el rango al formato inclusivo `..`.",
                )
            )
        if canonical_match:
            start_text, end_text = canonical_match.groups()
            start = _parse_element_id(start_text)
            end = _parse_element_id(end_text)
            assert start is not None and end is not None
            if start[0] != end[0]:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-RANGE-PREFIX",
                        "Los extremos del rango deben usar el mismo prefijo.",
                        location=location,
                        observed=part,
                        expected=start[0],
                    )
                )
                continue
            if start[0] not in relation.targets:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-TARGET-PREFIX",
                        "El prefijo del rango no está permitido en esta relación.",
                        location=location,
                        observed=start[0],
                        expected=sorted(relation.targets),
                    )
                )
                continue
            if start[1] > end[1]:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-RANGE-ORDER",
                        "El rango está invertido.",
                        location=location,
                        observed=part,
                        remediation="Ordene los extremos de menor a mayor.",
                    )
                )
                continue
            size = end[1] - start[1] + 1
            if size > max_range_size:
                diagnostics.append(
                    _diagnostic(
                        "LKS-REF-RANGE-SIZE",
                        "El rango supera el máximo admitido.",
                        location=location,
                        observed=size,
                        expected=max_range_size,
                    )
                )
                continue
            range_ids = tuple(
                f"{start[0]}-{number:03d}" for number in range(start[1], end[1] + 1)
            )
            if known is not None:
                missing = [item for item in range_ids if item not in known]
                if missing:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-REF-RANGE-HOLE",
                            "El rango contiene extremos o IDs interiores sin definición.",
                            location=location,
                            observed=missing,
                            expected="todos los IDs del rango definidos",
                            remediation="Defina los IDs ausentes o use una lista explícita sin huecos.",
                        )
                    )
                    continue
            expanded.extend(range_ids)
            canonical_parts.append(f"{start_text}..{end_text}")
            continue

        parsed = _parse_element_id(part)
        if parsed is None:
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-SYNTAX",
                    "La referencia no usa un ID, lista o rango admitido.",
                    location=location,
                    observed=part,
                    expected="ID, ID, ID o ID..ID",
                )
            )
            continue
        if parsed[0] not in relation.targets:
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-TARGET-PREFIX",
                    "El prefijo no está permitido en esta relación.",
                    location=location,
                    observed=parsed[0],
                    expected=sorted(relation.targets),
                )
            )
            continue
        if known is not None and part not in known:
            diagnostics.append(
                _diagnostic(
                    "LKS-REF-UNDEFINED",
                    "La referencia no tiene una definición registrada.",
                    location=location,
                    observed=part,
                    expected="ID definido en su tabla propietaria",
                )
            )
            continue
        expanded.append(part)
        canonical_parts.append(part)

    duplicates = sorted(item for item, count in Counter(expanded).items() if count > 1)
    if duplicates:
        diagnostics.append(
            _diagnostic(
                "LKS-REF-DUPLICATE",
                "La relación repite IDs mediante listas o rangos solapados.",
                location=location,
                observed=duplicates,
                remediation="Elimine duplicados y solapamientos.",
            )
        )
    if relation.maximum is not None and len(expanded) > relation.maximum:
        diagnostics.append(
            _diagnostic(
                "LKS-REF-CARDINALITY-MAX",
                "La relación contiene más referencias de las permitidas.",
                location=location,
                observed=len(expanded),
                expected=relation.maximum,
            )
        )
    if len(expanded) < relation.minimum and not any(
        item.code in {"LKS-REF-REQUIRED", "LKS-REF-APPLICABILITY-REASON"}
        for item in diagnostics
    ):
        diagnostics.append(
            _diagnostic(
                "LKS-REF-CARDINALITY-MIN",
                "La relación no alcanza el mínimo de referencias.",
                location=location,
                observed=len(expanded),
                expected=relation.minimum,
            )
        )
    if any(item.severity == "error" for item in diagnostics):
        # A malformed range or list is rejected as one unit. Returning no
        # references prevents downstream checks from reporting its endpoints
        # as if the rest of the range never existed.
        return ReferenceResult(
            (),
            None,
            None,
            None,
            syntax,
            deduplicate_diagnostics(diagnostics),
        )
    return ReferenceResult(
        tuple(expanded),
        ", ".join(canonical_parts) if canonical_parts else None,
        None,
        None,
        syntax,
        deduplicate_diagnostics(diagnostics),
    )


def _parse_scalar(value: str) -> Any:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    lowered = stripped.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    return stripped


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("falta el delimitador inicial de front matter")
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("falta el delimitador final de front matter") from exc
    data: dict[str, Any] = {}
    list_key: str | None = None
    for line_number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if list_key is None or not isinstance(data.get(list_key), list):
                raise ValueError(f"lista sin clave en línea {line_number}")
            data[list_key].append(_parse_scalar(line[4:]))
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"sintaxis no soportada en línea {line_number}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if raw.strip():
            data[key] = _parse_scalar(raw)
            list_key = None
        else:
            data[key] = []
            list_key = key
    return data, "\n".join(lines[end + 1 :]), end + 2


@dataclass(frozen=True)
class _RawTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[int, dict[str, str]], ...]


def _parse_markdown_tables(body: str, first_body_line: int) -> tuple[_RawTable, ...]:
    lines = body.splitlines()
    result: list[_RawTable] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and separator_line.startswith("|")):
            index += 1
            continue
        headers = tuple(cell.strip() for cell in header_line.strip("|").split("|"))
        separators = [cell.strip() for cell in separator_line.strip("|").split("|")]
        if len(headers) != len(separators) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            index += 1
            continue
        rows: list[tuple[int, dict[str, str]]] = []
        index += 2
        while index < len(lines) and lines[index].strip().startswith("|"):
            cells = [
                cell.strip() for cell in lines[index].strip().strip("|").split("|")
            ]
            if len(cells) == len(headers):
                rows.append((first_body_line + index, dict(zip(headers, cells))))
            index += 1
        result.append(_RawTable(headers=headers, rows=tuple(rows)))
    return tuple(result)


def _safe_relative_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        return None, "ruta absoluta o con '..' no permitida"
    unresolved = root / requested
    current = root
    for part in requested.parts:
        current = current / part
        if current.is_symlink() or (
            hasattr(current, "is_junction") and current.is_junction()
        ):
            return None, "ruta mediante symlink o junction no permitida"
    try:
        resolved = unresolved.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None, "ruta fuera del proyecto"
    return resolved, None


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: Any) -> str:
    serialized = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _hash_bytes(serialized)


def _manifest_error_model(
    root: Path, diagnostic: Diagnostic, manifest: dict[str, Any] | None = None
) -> ProjectModel:
    return ProjectModel(
        root=root,
        schema_version=str((manifest or {}).get("schema_version", "unknown")),
        manifest=manifest or {},
        registry=None,
        rows={},
        nodes={},
        edges=(),
        assets=(),
        diagnostics=(diagnostic,),
        checked_files=(),
        source_hashes={},
    )


def _asset_target(value: str) -> str | None:
    raw = value.strip()
    match = MARKDOWN_IMAGE_RE.fullmatch(raw)
    if match:
        return match.group(1).strip().split(maxsplit=1)[0].strip("<>")
    if raw and not any(character in raw for character in "\r\n"):
        return raw
    return None


def build_project_model(
    project_root: Path,
    *,
    catalog_path: Path | None = None,
) -> ProjectModel:
    """Read a project into a typed graph without changing any project file."""

    root = project_root.expanduser().resolve()
    manifest_relative = ".lks-sdd/project.json"
    manifest_path, path_error = _safe_relative_file(root, manifest_relative)
    manifest_location = SourceLocation(path=manifest_relative)
    if path_error or manifest_path is None or not manifest_path.is_file():
        return _manifest_error_model(
            root,
            _diagnostic(
                "LKS-PROJECT-MANIFEST",
                "No se puede leer el índice operativo del proyecto.",
                location=manifest_location,
                observed=path_error or "missing",
            ),
        )
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _manifest_error_model(
            root,
            _diagnostic(
                "LKS-PROJECT-MANIFEST",
                "El índice operativo no es JSON UTF-8 válido.",
                location=manifest_location,
                observed=str(exc),
            ),
        )
    if not isinstance(manifest, dict):
        return _manifest_error_model(
            root,
            _diagnostic(
                "LKS-PROJECT-MANIFEST",
                "El índice operativo debe ser un objeto JSON.",
                location=manifest_location,
            ),
        )
    schema_version = str(manifest.get("schema_version", ""))
    try:
        registry = load_registry(schema_version, catalog_path)
    except ContractEngineError as exc:
        return _manifest_error_model(
            root,
            _diagnostic(
                "LKS-PROJECT-SCHEMA",
                str(exc),
                location=manifest_location,
                observed=schema_version,
                expected=["1.0", "1.1"],
            ),
            manifest,
        )

    diagnostics: list[Diagnostic] = []
    rows: dict[str, ProjectRow] = {}
    nodes: dict[str, ProjectRow] = {}
    source_hashes: dict[str, str] = {manifest_relative: _hash_bytes(manifest_bytes)}
    checked_files: list[str] = [manifest_relative]
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        diagnostics.append(
            _diagnostic(
                "LKS-PROJECT-ARTIFACTS",
                "project.json debe declarar una lista de artefactos.",
                location=manifest_location,
            )
        )
        artifacts = []
    declared_artifact_ids = {
        item.get("id")
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for artifact_id, artifact_contract in registry.artifacts.items():
        if artifact_contract.required and artifact_id not in declared_artifact_ids:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-MISSING",
                    f"Falta el artefacto obligatorio {artifact_id} en el índice.",
                    location=manifest_location,
                    expected=artifact_contract.path,
                )
            )

    for entry in artifacts:
        if not isinstance(entry, dict):
            continue
        artifact_id = entry.get("id")
        relative = entry.get("path")
        if not isinstance(artifact_id, str) or not isinstance(relative, str):
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-ENTRY",
                    "El índice contiene una entrada de artefacto inválida.",
                    location=manifest_location,
                    observed=entry,
                )
            )
            continue
        location = SourceLocation(path=relative, artifact_id=artifact_id)
        path, artifact_path_error = _safe_relative_file(root, relative)
        if artifact_path_error or path is None or not path.is_file():
            severity = "error" if entry.get("required") else "warning"
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-FILE",
                    f"No se puede leer {artifact_id}.",
                    location=location,
                    severity=severity,
                    observed=artifact_path_error or "missing",
                )
            )
            continue
        try:
            content = path.read_bytes()
            text = content.decode("utf-8")
            metadata, body, body_line = _parse_frontmatter(text)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-MARKDOWN",
                    f"{artifact_id} no es Markdown UTF-8 estructurado válido.",
                    location=location,
                    observed=str(exc),
                )
            )
            continue
        source_hashes[relative] = _hash_bytes(content)
        checked_files.append(relative)
        artifact_type = str(metadata.get("artifact_type", ""))
        contract = registry.artifact_for(artifact_id, artifact_type)
        if contract is None:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-UNDECLARED",
                    "El artefacto indexado no tiene contrato declarativo.",
                    location=location,
                    severity="warning" if schema_version == "1.0" else "error",
                    observed={
                        "artifact_id": artifact_id,
                        "artifact_type": artifact_type,
                    },
                    remediation="Añada su contrato por artefacto y tabla antes de usarlo en relaciones activas.",
                )
            )
            continue
        if metadata.get("artifact_id") != artifact_id:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-ID",
                    "artifact_id no coincide con el índice.",
                    location=location,
                    observed=metadata.get("artifact_id"),
                    expected=artifact_id,
                )
            )
        if artifact_type != contract.artifact_type:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-TYPE",
                    "artifact_type no coincide con el catálogo.",
                    location=location,
                    observed=artifact_type,
                    expected=contract.artifact_type,
                )
            )
        if metadata.get("schema_version") != schema_version:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-SCHEMA",
                    "schema_version del Markdown no coincide con project.json.",
                    location=location,
                    observed=metadata.get("schema_version"),
                    expected=schema_version,
                )
            )
        if contract.path is not None and relative != contract.path:
            diagnostics.append(
                _diagnostic(
                    "LKS-ARTIFACT-PATH",
                    "La ruta no coincide con la ruta contractual del artefacto.",
                    location=location,
                    observed=relative,
                    expected=contract.path,
                )
            )

        raw_tables = _parse_markdown_tables(body, body_line)
        matches_by_table: Counter[str] = Counter()
        known_headers = contract.tables_by_headers
        for raw_index, raw_table in enumerate(raw_tables, 1):
            table_contract = known_headers.get(raw_table.headers)
            if table_contract is None:
                if contract.tables:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-TABLE-UNDECLARED",
                            "La tabla no coincide con ninguna cabecera declarada para el artefacto.",
                            location=SourceLocation(
                                path=relative,
                                artifact_id=artifact_id,
                                row=raw_table.rows[0][0] - 2
                                if raw_table.rows
                                else None,
                            ),
                            severity="warning" if schema_version == "1.0" else "error",
                            observed=list(raw_table.headers),
                            expected=[list(item.headers) for item in contract.tables],
                        )
                    )
                continue
            matches_by_table[table_contract.table_id] += 1
            for row_index, (line, cells) in enumerate(raw_table.rows, 1):
                uid = f"{artifact_id}:{table_contract.table_id}:{raw_index}:{row_index}"
                row_location = SourceLocation(
                    path=relative,
                    artifact_id=artifact_id,
                    table_id=table_contract.table_id,
                    row=line,
                )
                key: str | None = None
                if table_contract.key_column:
                    key = cells.get(table_contract.key_column, "").strip()
                    parsed_key = _parse_element_id(key)
                    if parsed_key is None:
                        diagnostics.append(
                            _diagnostic(
                                "LKS-ID-SYNTAX",
                                "La clave de fila no usa PREFIX-###.",
                                location=replace(
                                    row_location,
                                    column=table_contract.key_column,
                                    source_id=key or None,
                                ),
                                observed=key,
                            )
                        )
                    elif parsed_key[0] not in table_contract.key_prefixes:
                        diagnostics.append(
                            _diagnostic(
                                "LKS-ID-OWNER",
                                "El prefijo no pertenece a esta tabla.",
                                location=replace(
                                    row_location,
                                    column=table_contract.key_column,
                                    source_id=key,
                                ),
                                observed=parsed_key[0],
                                expected=sorted(table_contract.key_prefixes),
                                remediation="Mueva la definición a su tabla propietaria o use el prefijo declarado.",
                            )
                        )
                    elif key in nodes:
                        diagnostics.append(
                            _diagnostic(
                                "LKS-ID-DUPLICATE",
                                "El identificador ya está definido en otra fila.",
                                location=replace(
                                    row_location,
                                    column=table_contract.key_column,
                                    source_id=key,
                                ),
                                observed=key,
                                expected=nodes[key].path,
                            )
                        )
                state: str | None = None
                state_class = "neutral"
                if table_contract.state_column and table_contract.state_policy:
                    state = cells.get(table_contract.state_column, "").strip()
                    policy = registry.state_policies[table_contract.state_policy]
                    state_class = policy.classify(state, schema_version)
                    if state not in policy.allowed_for(schema_version):
                        diagnostics.append(
                            _diagnostic(
                                "LKS-STATE-TABLE",
                                "El estado no está permitido por la política de esta tabla.",
                                location=replace(
                                    row_location,
                                    column=table_contract.state_column,
                                    source_id=key,
                                ),
                                observed=state,
                                expected=sorted(policy.allowed_for(schema_version)),
                            )
                        )
                project_row = ProjectRow(
                    uid=uid,
                    artifact_id=artifact_id,
                    artifact_type=artifact_type,
                    path=relative,
                    table_id=table_contract.table_id,
                    line=line,
                    cells=cells,
                    contract=table_contract,
                    key=key or None,
                    state=state,
                    state_class=state_class,
                )
                rows[uid] = project_row
                if key and _parse_element_id(key) is not None and key not in nodes:
                    nodes[key] = project_row
        for table_contract in contract.tables:
            count = matches_by_table[table_contract.table_id]
            if count < table_contract.minimum_occurrences:
                diagnostics.append(
                    _diagnostic(
                        "LKS-TABLE-MISSING",
                        f"Falta la tabla contractual {table_contract.table_id}.",
                        location=location,
                        observed=count,
                        expected=table_contract.minimum_occurrences,
                    )
                )
            if (
                table_contract.maximum_occurrences is not None
                and count > table_contract.maximum_occurrences
            ):
                diagnostics.append(
                    _diagnostic(
                        "LKS-TABLE-DUPLICATE",
                        f"La tabla {table_contract.table_id} aparece más veces de las permitidas.",
                        location=location,
                        observed=count,
                        expected=table_contract.maximum_occurrences,
                    )
                )

    edges: list[ProjectEdge] = []
    for row in rows.values():
        applicability = row.contract.applicability
        applicability_value: str | None = None
        if applicability is not None:
            applicability_value = (
                row.cells.get(applicability.applicability_column, "").strip().casefold()
            )
            domain = row.cells.get(applicability.domain_column, "").strip().casefold()
            reason = row.cells.get(applicability.reason_column, "").strip()
            references_value = row.cells.get(
                applicability.references_column, ""
            ).strip()
            references_empty = references_value.casefold() in EMPTY_REFERENCE_VALUES
            app_location = SourceLocation(
                path=row.path,
                artifact_id=row.artifact_id,
                table_id=row.table_id,
                row=row.line,
                column=applicability.applicability_column,
                source_id=row.key,
            )
            if domain not in applicability.domains:
                diagnostics.append(
                    _diagnostic(
                        "LKS-DOMAIN-NAME",
                        "El dominio no pertenece al catálogo de aplicabilidad.",
                        location=replace(
                            app_location, column=applicability.domain_column
                        ),
                        observed=domain,
                        expected=list(applicability.domains),
                    )
                )
            if applicability_value not in {"applicable", "pending", "not-applicable"}:
                diagnostics.append(
                    _diagnostic(
                        "LKS-DOMAIN-APPLICABILITY",
                        "La aplicabilidad debe ser applicable, pending o not-applicable.",
                        location=app_location,
                        observed=applicability_value,
                    )
                )
            elif applicability_value == "applicable":
                if references_empty:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-DOMAIN-REFERENCES",
                            "Un dominio aplicable requiere referencias de fila.",
                            location=replace(
                                app_location,
                                column=applicability.references_column,
                            ),
                        )
                    )
            else:
                if not reason:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-DOMAIN-REASON",
                            "pending y not-applicable requieren un motivo.",
                            location=replace(
                                app_location, column=applicability.reason_column
                            ),
                        )
                    )
                if not references_empty:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-DOMAIN-REFERENCE-CONFLICT",
                            "Un dominio pending o not-applicable no debe declarar referencias activas.",
                            location=replace(
                                app_location,
                                column=applicability.references_column,
                            ),
                            observed=references_value,
                        )
                    )

        for column, base_relation in row.contract.relations.items():
            allowed_targets = base_relation.targets_for(row.cells)
            relation = replace(base_relation, targets=allowed_targets)
            if (
                applicability is not None
                and column == applicability.references_column
                and applicability_value == "applicable"
            ):
                relation = replace(
                    relation, minimum=max(1, relation.minimum), allow_empty=False
                )
            location = SourceLocation(
                path=row.path,
                artifact_id=row.artifact_id,
                table_id=row.table_id,
                row=row.line,
                column=column,
                source_id=row.key,
            )
            result = parse_reference_cell(
                row.cells.get(column, ""),
                relation,
                nodes if relation.require_defined else None,
                mode="compat" if schema_version == "1.0" else "strict",
                location=location,
                max_range_size=registry.max_range_size,
            )
            row.reference_results[column] = result
            diagnostics.extend(result.diagnostics)
            if not result.valid:
                continue
            edges.extend(
                ProjectEdge(
                    source_uid=row.uid,
                    source_id=row.key,
                    column=column,
                    target_id=target,
                    active_input=relation.active_input,
                    require_defined=relation.require_defined,
                )
                for target in result.references
            )

    # Domain rows form a complete matrix per increment in schema 1.1.  This is
    # validated after references so malformed scope cells do not create a
    # cascade of invented missing-domain messages.
    applicability_tables = [
        (artifact, table)
        for artifact in registry.artifacts.values()
        for table in artifact.tables
        if table.applicability is not None
    ]
    for artifact_contract, table_contract in applicability_tables:
        table_id = table_contract.table_id
        applicability = table_contract.applicability
        assert applicability is not None
        table_rows = [row for row in rows.values() if row.table_id == table_id]
        by_scope: dict[str, list[ProjectRow]] = {}
        for row in table_rows:
            scope_result = row.reference_results.get(row.contract.scope_column or "")
            if (
                scope_result
                and scope_result.valid
                and len(scope_result.references) == 1
            ):
                by_scope.setdefault(scope_result.references[0], []).append(row)
        scope_relation = table_contract.relations.get(table_contract.scope_column or "")
        expected_scopes = {
            node_id
            for node_id in nodes
            if scope_relation is not None
            and _parse_element_id(node_id) is not None
            and _parse_element_id(node_id)[0] in scope_relation.targets
        }
        for scope in sorted(expected_scopes | set(by_scope)):
            scoped_rows = by_scope.get(scope, [])
            domains = [
                row.cells.get(applicability.domain_column, "").strip().casefold()
                for row in scoped_rows
            ]
            missing = sorted(set(applicability.domains) - set(domains))
            duplicates = sorted(
                domain for domain, count in Counter(domains).items() if count > 1
            )
            if missing:
                scope_node = nodes.get(scope)
                diagnostics.append(
                    _diagnostic(
                        "LKS-DOMAIN-MISSING",
                        "La matriz de aplicabilidad no cubre todos los dominios.",
                        location=SourceLocation(
                            path=(
                                scoped_rows[0].path
                                if scoped_rows
                                else artifact_contract.path or ".lks-sdd/project.json"
                            ),
                            artifact_id=(
                                scoped_rows[0].artifact_id
                                if scoped_rows
                                else next(
                                    (
                                        artifact_id
                                        for artifact_id, candidate in registry.artifacts.items()
                                        if candidate is artifact_contract
                                    ),
                                    None,
                                )
                            ),
                            table_id=table_id,
                            source_id=scope,
                        ),
                        severity=(
                            "warning"
                            if scope_node is not None
                            and scope_node.state_class == "pending"
                            else "error"
                        ),
                        observed=missing,
                        expected=list(applicability.domains),
                    )
                )
            if duplicates:
                diagnostics.append(
                    _diagnostic(
                        "LKS-DOMAIN-DUPLICATE",
                        "La matriz repite dominios para el mismo incremento.",
                        location=SourceLocation(
                            path=scoped_rows[0].path,
                            artifact_id=scoped_rows[0].artifact_id,
                            table_id=table_id,
                            source_id=scope,
                        ),
                        observed=duplicates,
                    )
                )

    assets: list[ProjectAsset] = []
    for row in rows.values():
        if row.contract.asset is None or row.key is None:
            continue
        spec = row.contract.asset
        raw_target = _asset_target(row.cells.get(spec.path_column, ""))
        declared = row.cells.get(spec.hash_column, "").strip().casefold() or None
        asset_location = SourceLocation(
            path=row.path,
            artifact_id=row.artifact_id,
            table_id=row.table_id,
            row=row.line,
            column=spec.path_column,
            source_id=row.key,
        )
        actual: str | None = None
        asset_relative = raw_target or ""
        if raw_target:
            target_path = Path(raw_target)
            if target_path.parts[:2] == ("docs", "lks-sdd"):
                asset_relative = target_path.as_posix()
            else:
                asset_relative = (Path(row.path).parent / target_path).as_posix()
            path, asset_error = _safe_relative_file(root, asset_relative)
            if not asset_error and path is not None and path.is_file():
                content = path.read_bytes()
                actual = _hash_bytes(content)
                source_hashes[asset_relative] = actual
                checked_files.append(asset_relative)
            else:
                diagnostics.append(
                    _diagnostic(
                        "LKS-ASSET-MISSING",
                        "No se puede leer el asset enlazado.",
                        location=asset_location,
                        severity="warning"
                        if row.state_class == "inactive"
                        else "error",
                        observed=asset_relative or asset_error or "missing",
                    )
                )
        else:
            diagnostics.append(
                _diagnostic(
                    "LKS-ASSET-SYNTAX",
                    "La celda Asset no contiene una ruta o imagen Markdown válida.",
                    location=asset_location,
                    severity="warning" if row.state_class == "inactive" else "error",
                    observed=row.cells.get(spec.path_column, ""),
                )
            )
        if actual is not None and declared != actual:
            diagnostics.append(
                _diagnostic(
                    "LKS-ASSET-HASH",
                    "El SHA-256 declarado no coincide con el asset.",
                    location=replace(asset_location, column=spec.hash_column),
                    severity="warning" if row.state_class == "inactive" else "error",
                    observed=declared,
                    expected=actual,
                )
            )
        assets.append(
            ProjectAsset(
                owner_id=row.key,
                path=asset_relative,
                sha256=actual,
                declared_sha256=declared,
                state_class=row.state_class,
            )
        )

    profile_lock = root / ".lks-sdd" / "profile.lock.json"
    if profile_lock.is_file() and not profile_lock.is_symlink():
        relative = profile_lock.relative_to(root).as_posix()
        content = profile_lock.read_bytes()
        source_hashes[relative] = _hash_bytes(content)
        checked_files.append(relative)
    profile_locks = root / ".lks-sdd" / "profiles"
    if profile_locks.is_dir() and not profile_locks.is_symlink():
        for candidate in sorted(profile_locks.glob("BIND-*.lock.json")):
            if not candidate.is_file() or candidate.is_symlink():
                continue
            relative = candidate.relative_to(root).as_posix()
            source_hashes[relative] = _hash_bytes(candidate.read_bytes())
            checked_files.append(relative)

    return ProjectModel(
        root=root,
        schema_version=schema_version,
        manifest=manifest,
        registry=registry,
        rows=rows,
        nodes=nodes,
        edges=tuple(edges),
        assets=tuple(assets),
        diagnostics=deduplicate_diagnostics(diagnostics),
        checked_files=tuple(dict.fromkeys(checked_files)),
        source_hashes=dict(source_hashes),
    )


def validate_model(
    model: ProjectModel,
    stage: str = "structure",
    increment: str | None = None,
) -> tuple[Diagnostic, ...]:
    """Return stage-scoped diagnostics while preserving the common structure."""

    if stage not in {"structure", "handoff", "readiness", "verification"}:
        raise ValueError("stage no reconocido")
    if increment is None or stage == "structure":
        return model.diagnostics
    active = resolve_active_increment(model, increment)
    return deduplicate_diagnostics((*model.diagnostics, *active.diagnostics))


def document_fingerprint(model: ProjectModel) -> str:
    """Hash the exact read snapshot, including historical rows and assets."""

    return _canonical_hash(
        {
            "fingerprint_schema": "lks-sdd-document-v1",
            "files": [
                {"path": path, "sha256": digest}
                for path, digest in sorted(model.source_hashes.items())
            ],
        }
    )


def _active_payload(
    model: ProjectModel,
    increment: str,
    active_rows: Sequence[ProjectRow],
    node_ids: set[str],
    edges: Sequence[ProjectEdge],
    assets: Sequence[ProjectAsset],
) -> dict[str, Any]:
    profile_lock_hash = model.source_hashes.get(".lks-sdd/profile.lock.json")
    if profile_lock_hash is None:
        technology = model.manifest.get("technology")
        selected_profile = (
            technology.get("selected_profile")
            if isinstance(technology, dict)
            else None
        )
        if isinstance(selected_profile, str) and re.fullmatch(
            r"[A-Z][A-Z0-9-]{2,63}", selected_profile
        ):
            packaged_lock = (
                PLUGIN_ROOT
                / "profiles"
                / selected_profile
                / "technology-profile.lock.json"
            )
            if packaged_lock.is_file() and not packaged_lock.is_symlink():
                profile_lock_hash = _hash_bytes(packaged_lock.read_bytes())
    profile_lock_hashes: dict[str, str] = {
        path: digest
        for path, digest in model.source_hashes.items()
        if re.fullmatch(r"\.lks-sdd/profiles/BIND-[0-9]{3}\.lock\.json", path)
    }
    technology = model.manifest.get("technology")
    if (
        str(model.manifest.get("schema_version")) in {"1.2", "1.3", "1.4", "1.5"}
        and isinstance(technology, dict)
    ):
        for binding in technology.get("profile_bindings", []):
            if not isinstance(binding, dict) or binding.get("state") != "confirmed":
                continue
            lock_path = binding.get("lock_path")
            profile_id = binding.get("profile_id")
            if (
                isinstance(lock_path, str)
                and lock_path not in profile_lock_hashes
                and isinstance(profile_id, str)
            ):
                packaged_lock = (
                    PLUGIN_ROOT
                    / "profiles"
                    / profile_id
                    / "technology-profile.lock.json"
                )
                if packaged_lock.is_file() and not packaged_lock.is_symlink():
                    profile_lock_hashes[lock_path] = _hash_bytes(
                        packaged_lock.read_bytes()
                    )
    project = {
        "project_id": model.manifest.get("project_id"),
        "route": model.manifest.get("route"),
        "method_version": model.manifest.get("method_version"),
        "schema_version": model.manifest.get("schema_version"),
        "baseline_id": model.manifest.get("baseline_id"),
        "technology": model.manifest.get("technology"),
        "profile_lock_sha256": profile_lock_hash,
        "profile_locks_sha256": dict(sorted(profile_lock_hashes.items())),
    }
    row_payloads = [
        {
            "artifact_id": row.artifact_id,
            "table_id": row.table_id,
            "key": row.key,
            "state_class": row.state_class,
            "cells": {key: row.cells[key] for key in sorted(row.cells)},
        }
        for row in active_rows
    ]
    edge_payloads = [
        {
            "source": edge.source_id
            or next(
                (
                    {
                        "artifact_id": row.artifact_id,
                        "table_id": row.table_id,
                        "cells": {key: row.cells[key] for key in sorted(row.cells)},
                    }
                    for row in active_rows
                    if row.uid == edge.source_uid
                ),
                edge.source_uid,
            ),
            "column": edge.column,
            "target": edge.target_id,
        }
        for edge in edges
        if edge.target_id in node_ids
    ]
    return {
        "fingerprint_schema": "lks-sdd-active-contract-v1",
        "project": project,
        "increment": increment,
        "rows": sorted(
            row_payloads,
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True),
        ),
        "edges": sorted(
            edge_payloads,
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True),
        ),
        "assets": sorted(
            (
                {"owner_id": asset.owner_id, "path": asset.path, "sha256": asset.sha256}
                for asset in assets
            ),
            key=lambda item: (item["owner_id"], item["path"]),
        ),
    }


def active_contract_fingerprint(active: ActiveContract) -> str:
    """Return the fingerprint already bound to an active contract result."""

    return active.fingerprint


def resolve_active_increment(model: ProjectModel, increment: str) -> ActiveContract:
    """Resolve only explicit active inputs for one increment.

    Historical nodes remain in ``ProjectModel`` and its document fingerprint,
    but rejected, superseded, and retired nodes are not traversed or hashed as
    implementation inputs.
    """

    diagnostics: list[Diagnostic] = []
    increment_row = model.nodes.get(increment)
    if increment_row is None or not increment.startswith("INC-"):
        diagnostics.append(
            _diagnostic(
                "LKS-ACTIVE-INCREMENT",
                "El incremento no tiene una definición INC-### registrada.",
                location=SourceLocation(source_id=increment),
                stage="handoff",
                observed=increment,
            )
        )
        payload = _active_payload(model, increment, (), set(), (), ())
        return ActiveContract(
            increment=increment,
            project=payload["project"],
            rows=(),
            node_ids=(),
            edges=(),
            assets=(),
            diagnostics=tuple(diagnostics),
            checked_files=(".lks-sdd/project.json",),
            fingerprint=_canonical_hash(payload),
        )

    edges_by_source: dict[str, list[ProjectEdge]] = {}
    for edge in model.edges:
        edges_by_source.setdefault(edge.source_uid, []).append(edge)

    included_uids: set[str] = {increment_row.uid}
    included_node_ids: set[str] = {increment}
    queue: deque[str] = deque([increment_row.uid])

    def belongs_to_active_scope(row: ProjectRow) -> bool:
        """Keep scoped association rows inside the requested increment.

        Keyless detail tables (for example UX screen details and states) do not
        declare a scope column and are intentionally eligible for reverse
        traversal through their active parent.  Scoped association tables such
        as traceability must explicitly point to this increment; otherwise a
        shared requirement could import the contract of another increment.
        """

        scope_column = row.contract.scope_column
        if not scope_column:
            return True
        result = row.reference_results.get(scope_column)
        return bool(result and result.valid and increment in result.references)

    # Rows such as interface, domains, and traceability are scoped by an INC
    # relation instead of owning an ID. They become roots only for this scope.
    for row in model.rows.values():
        scope_column = row.contract.scope_column
        if not scope_column:
            continue
        if belongs_to_active_scope(row):
            if row.uid not in included_uids:
                included_uids.add(row.uid)
                queue.append(row.uid)

    while queue:
        source_uid = queue.popleft()
        for edge in edges_by_source.get(source_uid, []):
            if not edge.active_input:
                continue
            target = model.nodes.get(edge.target_id)
            if target is None:
                if edge.require_defined:
                    diagnostics.append(
                        _diagnostic(
                            "LKS-ACTIVE-UNDEFINED",
                            "Una relación activa no puede resolverse.",
                            location=SourceLocation(
                                path=model.rows[source_uid].path,
                                artifact_id=model.rows[source_uid].artifact_id,
                                table_id=model.rows[source_uid].table_id,
                                row=model.rows[source_uid].line,
                                column=edge.column,
                                source_id=model.rows[source_uid].key,
                            ),
                            stage="handoff",
                            observed=edge.target_id,
                        )
                    )
                continue
            if target.state_class == "inactive":
                diagnostics.append(
                    _diagnostic(
                        "LKS-ACTIVE-HISTORICAL-REFERENCE",
                        "Una relación activa enlaza un elemento histórico no implementable.",
                        location=SourceLocation(
                            path=model.rows[source_uid].path,
                            artifact_id=model.rows[source_uid].artifact_id,
                            table_id=model.rows[source_uid].table_id,
                            row=model.rows[source_uid].line,
                            column=edge.column,
                            source_id=model.rows[source_uid].key,
                        ),
                        stage="handoff",
                        observed={"id": edge.target_id, "state": target.state},
                        expected="elemento activo y confirmado",
                        remediation="Retire el ID de la celda activa; conserve su fila histórica en el artefacto propietario.",
                    )
                )
                continue
            if target.state_class == "pending":
                diagnostics.append(
                    _diagnostic(
                        "LKS-ACTIVE-UNCONFIRMED",
                        "Una relación activa enlaza un elemento aún no confirmado.",
                        location=SourceLocation(
                            path=model.rows[source_uid].path,
                            artifact_id=model.rows[source_uid].artifact_id,
                            table_id=model.rows[source_uid].table_id,
                            row=model.rows[source_uid].line,
                            column=edge.column,
                            source_id=model.rows[source_uid].key,
                        ),
                        stage="handoff",
                        observed={"id": edge.target_id, "state": target.state},
                        expected="confirmed",
                    )
                )
            included_node_ids.add(edge.target_id)
            if target.uid not in included_uids:
                included_uids.add(target.uid)
                queue.append(target.uid)

        # Detail/state rows point into keyed nodes rather than the keyed node
        # pointing back. Include those supplemental rows once their target is
        # active, without scanning unrelated history into the contract.
        changed = True
        while changed:
            changed = False
            for candidate in model.rows.values():
                if candidate.uid in included_uids or candidate.key is not None:
                    continue
                if not belongs_to_active_scope(candidate):
                    continue
                candidate_edges = [
                    edge
                    for edge in edges_by_source.get(candidate.uid, [])
                    if edge.active_input
                ]
                if any(edge.target_id in included_node_ids for edge in candidate_edges):
                    included_uids.add(candidate.uid)
                    queue.append(candidate.uid)
                    changed = True

    active_rows = tuple(
        sorted(
            (model.rows[uid] for uid in included_uids),
            key=lambda row: (row.artifact_id, row.table_id, row.key or "", row.line),
        )
    )
    active_edges = tuple(
        edge
        for edge in model.edges
        if edge.source_uid in included_uids and edge.active_input
    )
    active_assets = tuple(
        asset
        for asset in model.assets
        if asset.owner_id in included_node_ids and asset.state_class != "inactive"
    )
    checked = {".lks-sdd/project.json"}
    checked.update(row.path for row in active_rows)
    checked.update(asset.path for asset in active_assets if asset.sha256 is not None)
    if ".lks-sdd/profile.lock.json" in model.source_hashes:
        checked.add(".lks-sdd/profile.lock.json")
    payload = _active_payload(
        model,
        increment,
        active_rows,
        included_node_ids,
        active_edges,
        active_assets,
    )
    return ActiveContract(
        increment=increment,
        project=payload["project"],
        rows=active_rows,
        node_ids=tuple(sorted(included_node_ids)),
        edges=active_edges,
        assets=active_assets,
        diagnostics=deduplicate_diagnostics(diagnostics),
        checked_files=tuple(sorted(checked)),
        fingerprint=_canonical_hash(payload),
    )


def legacy_messages(diagnostics: Iterable[Diagnostic]) -> dict[str, list[str]]:
    """Provide backward-compatible string views without losing typed output."""

    errors: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    for item in deduplicate_diagnostics(diagnostics):
        location = item.location
        prefix_parts = [
            value
            for value in (
                location.path,
                location.table_id,
                f"línea {location.row}" if location.row else None,
                location.column,
            )
            if value
        ]
        message = f"[{item.code}] "
        if prefix_parts:
            message += " / ".join(prefix_parts) + ": "
        message += item.message
        if item.severity == "warning":
            warnings.append(message)
        else:
            errors.append(message)
            if item.stage in {"handoff", "readiness"}:
                blockers.append(message)
    return {"errors": errors, "warnings": warnings, "blockers": blockers}


__all__ = [
    "ActiveContract",
    "ApplicabilitySpec",
    "ArtifactContract",
    "AssetSpec",
    "ContractEngineError",
    "ContractRegistry",
    "Diagnostic",
    "ELEMENT_ID_RE",
    "ProjectAsset",
    "ProjectEdge",
    "ProjectModel",
    "ProjectRow",
    "ReferenceResult",
    "RelationSpec",
    "SourceLocation",
    "StatePolicy",
    "TableContract",
    "active_contract_fingerprint",
    "build_project_model",
    "deduplicate_diagnostics",
    "document_fingerprint",
    "legacy_messages",
    "load_registry",
    "parse_reference_cell",
    "resolve_active_increment",
    "validate_model",
]
