#!/usr/bin/env python3
"""Render a safe draft client view from confirmed client/public canonical sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from validate_project import parse_frontmatter, validate_project

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_CLASSIFICATIONS = {"client", "public"}
SENSITIVE_PATTERNS = [
    re.compile(
        r"(?i)(?:password|passwd|secret|api[_ -]?key|access[_ -]?token|client[_ -]?secret)\s*[:=]"
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:^|[/\\])\.env(?:\.|$)"),
]


class ClientViewError(Exception):
    """Expected, actionable client-view failure."""


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _one_line(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


def _safe_output(root: Path, requested: Path) -> Path:
    unresolved = requested if requested.is_absolute() else root / requested
    current = unresolved
    while current != root:
        if _is_link_like(current):
            raise ClientViewError(
                f"No se escribe a través de enlaces simbólicos o junctions: {current}"
            )
        if current.parent == current:
            break
        current = current.parent
    output = unresolved.resolve()
    try:
        relative = output.relative_to(root).as_posix()
    except ValueError as exc:
        raise ClientViewError(
            "La vista derivada debe permanecer dentro del proyecto."
        ) from exc
    if output == root:
        raise ClientViewError(
            "La vista derivada debe ser un archivo dentro del proyecto."
        )
    if relative == "docs/lks-sdd" or relative.startswith("docs/lks-sdd/"):
        raise ClientViewError(
            "La vista cliente no puede escribirse dentro de la fuente canónica."
        )
    return output


def _contains_sensitive_indicator(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


def _nest_headings(body: str) -> str:
    lines = []
    for line in body.strip().splitlines():
        if line.startswith("#"):
            lines.append("##" + line)
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def render(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = args.project_root.expanduser().resolve()
    report, manifest, _ = validate_project(root)
    if not report.valid or manifest is None:
        return 2, {
            "status": "invalid-project",
            "changed": False,
            "errors": report.errors,
        }
    included: list[dict[str, str]] = []
    excluded_count = 0
    blocked_ids: list[str] = []
    for entry in manifest["artifacts"]:
        path = root / entry["path"]
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if (
            metadata.get("classification") not in ALLOWED_CLASSIFICATIONS
            or metadata.get("status") != "confirmed"
        ):
            excluded_count += 1
            continue
        if _contains_sensitive_indicator(body):
            blocked_ids.append(entry["id"])
            continue
        included.append({"id": entry["id"], "body": body})
    if blocked_ids:
        return 3, {
            "status": "blocked-sensitive-source",
            "changed": False,
            "blockers": [
                f"{artifact_id}: contiene un indicador sensible; corrija la fuente canónica antes de derivar."
                for artifact_id in blocked_ids
            ],
        }
    if not included:
        return 3, {
            "status": "blocked-no-eligible-sources",
            "changed": False,
            "blockers": [
                "No hay artefactos confirmed con clasificación client o public."
            ],
        }
    provenance_payload = [
        {
            "id": item["id"],
            "sha256": hashlib.sha256(item["body"].encode("utf-8")).hexdigest(),
        }
        for item in included
    ]
    provenance_hash = hashlib.sha256(
        json.dumps(provenance_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    sections = "\n\n".join(
        f"## Fuente {item['id']}\n\n{_nest_headings(item['body'])}" for item in included
    )
    replacements = {
        "PROJECT_ID": manifest["project_id"],
        "AUDIENCE": _one_line(args.audience),
        "PURPOSE": _one_line(args.purpose),
        "DATE": args.date,
        "BASELINE_ID": manifest["baseline_id"],
        "SECTIONS": sections,
        "SOURCE_IDS": ", ".join(f"`{item['id']}`" for item in included),
        "EXCLUDED_COUNT": str(excluded_count),
        "PROVENANCE_HASH": provenance_hash,
    }
    content = (
        PLUGIN_ROOT / "templates" / "client" / "client-deliverable.md"
    ).read_text(encoding="utf-8")
    for token, value in replacements.items():
        content = content.replace("{{" + token + "}}", value)
    if re.search(r"\{\{[A-Z0-9_]+\}\}", content):
        raise ClientViewError("La plantilla cliente conserva tokens sin resolver.")
    if _contains_sensitive_indicator(content):
        raise ClientViewError(
            "La transformación produjo un indicador sensible y se bloqueó."
        )
    content = content.rstrip() + "\n"
    output = _safe_output(root, args.output)
    preview_hash = hashlib.sha256(
        output.relative_to(root).as_posix().encode("utf-8")
        + b"\0"
        + content.encode("utf-8")
    ).hexdigest()
    result = {
        "status": "dry-run" if args.dry_run else "rendered",
        "changed": False,
        "output": output.relative_to(root).as_posix(),
        "preview_hash": preview_hash,
        "source_ids": [item["id"] for item in included],
        "excluded_count": excluded_count,
        "classification": "draft-client-view",
        "approval": "pending",
    }
    if args.dry_run:
        return 0, result
    if not args.apply or not args.authorize:
        raise ClientViewError(
            "Aplicar requiere --apply y --authorize tras revisar el dry-run."
        )
    if args.preview_hash != preview_hash:
        raise ClientViewError("El preview hash no coincide; repita el dry-run.")
    if output.exists():
        if output.is_file() and output.read_text(encoding="utf-8") == content:
            result.update({"status": "already-rendered", "changed": False})
            return 0, result
        raise ClientViewError(
            f"Colisión; no se sobrescribirá {output.relative_to(root)}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    except OSError as exc:
        try:
            output.unlink()
        except OSError:
            pass
        raise ClientViewError(f"No se pudo crear la vista cliente: {exc}") from exc
    result.update({"status": "rendered", "changed": True})
    return 0, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument(
        "--output", type=Path, default=Path("deliverables/lks-sdd/client-view.md")
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--preview-hash")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.date)
        if not args.audience.strip() or not args.purpose.strip():
            raise ClientViewError("Audiencia y propósito no pueden estar vacíos.")
        code, result = render(args)
    except (ClientViewError, ValueError) as exc:
        code, result = 2, {"status": "error", "changed": False, "error": str(exc)}
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["status"])
        if result.get("preview_hash"):
            print(f"preview_hash={result['preview_hash']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
