#!/usr/bin/env python3
"""Inspect an existing repository statically without modifying its root."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from adoption_common import (
    REPORT_KIND,
    REPORT_VERSION,
    AdoptionError,
    is_link_like,
    repository_snapshot,
    safe_exclusions,
    safe_root,
    safe_scope,
)


def inspect(args: argparse.Namespace) -> tuple[int, dict]:
    root = safe_root(args.project_root)
    scope_path, scope_relative = safe_scope(root, args.scope)
    exclusions = safe_exclusions(root, args.exclude)
    before, scanned = repository_snapshot(root, scope_path, args.max_files, exclusions)
    manifest_names = sorted(
        item["path"] for item in scanned["files"] if item.get("category") == "manifest"
    )
    source_extensions = sorted(
        {
            Path(item["path"]).suffix.casefold()
            for item in scanned["files"]
            if item.get("category") == "source" and Path(item["path"]).suffix
        }
    )
    limitations = [
        "El inventario es estático: no se ejecutaron aplicación, builds, tests, contenedores, hooks ni gestores de paquetes.",
        "El código observado acredita implementación, no intención de negocio ni comportamiento productivo.",
        "Los posibles secretos y binarios se registraron solo por ruta/categoría o metadatos; sus valores no se leyeron ni reprodujeron.",
    ]
    if scanned["truncated"]:
        limitations.append(
            "El límite de archivos dejó el inventario parcial; el alcance debe confirmarse expresamente."
        )
    if scanned["symlinks_excluded"]:
        limitations.append(
            "Se excluyeron enlaces simbólicos para impedir salir de la raíz confirmada."
        )
    if scanned["submodules_excluded"]:
        limitations.append(
            "Se excluyeron submódulos; requieren una ampliación explícita de alcance y un inventario propio."
        )
    report = {
        "kind": REPORT_KIND,
        "contract_version": REPORT_VERSION,
        "generated_at": args.date,
        "preflight": {
            "root": str(root),
            "scope": scope_relative,
            "production_state": args.production_state,
            "permissions": "read-only",
            "exclusions": exclusions,
            "max_files": args.max_files,
        },
        "baseline": before,
        "coverage": {
            "files_inventoried": len(scanned["files"]),
            "sensitive_files_excluded": len(scanned["sensitive_indicators"]),
            "truncated": scanned["truncated"],
            "counts": scanned["counts"],
        },
        "inventory": {
            "files": scanned["files"],
            "sensitive_indicators": scanned["sensitive_indicators"],
            "symlinks_excluded": scanned["symlinks_excluded"],
            "submodules_excluded": scanned["submodules_excluded"],
            "manifest_paths": manifest_names,
            "source_extensions": source_extensions,
        },
        "observations": [
            {
                "statement": f"Se inventariaron {len(scanned['files'])} archivos dentro del alcance confirmado.",
                "source": "static-inventory",
                "nature": "fact",
                "confidence": "high",
                "limitations": "No acredita cobertura fuera del alcance ni comportamiento en ejecución.",
            },
            {
                "statement": f"Se detectaron manifiestos: {', '.join(manifest_names) if manifest_names else 'ninguno'}.",
                "source": "file-names",
                "nature": "observation",
                "confidence": "high",
                "limitations": "Un manifiesto no demuestra que la dependencia o servicio se use en producción.",
            },
        ],
        "limitations": limitations,
        "read_only_proof": {"before": before, "after": None, "unchanged": False},
    }
    after, _ = repository_snapshot(root, scope_path, args.max_files, exclusions)
    report["read_only_proof"].update({"after": after, "unchanged": before == after})
    return (0 if before == after else 3), report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--scope", default=".")
    parser.add_argument(
        "--production-state",
        choices=("production", "pre-production", "inactive", "unknown"),
        required=True,
    )
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--max-files", type=int, default=20000)
    parser.add_argument("--date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        date.fromisoformat(args.date)
        if args.max_files < 1:
            raise AdoptionError("--max-files debe ser positivo.")
        code, report = inspect(args)
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            root = safe_root(args.project_root)
            unresolved = args.output.expanduser()
            if not unresolved.is_absolute():
                unresolved = Path.cwd() / unresolved
            current = unresolved
            while current.parent != current:
                if is_link_like(current):
                    raise AdoptionError(
                        "El informe externo no se escribe mediante symlinks o junctions."
                    )
                current = current.parent
            output = unresolved.resolve()
            try:
                output.relative_to(root)
            except ValueError:
                pass
            else:
                raise AdoptionError(
                    "El informe provisional debe escribirse fuera del repositorio inspeccionado."
                )
            if not output.parent.is_dir() or output.exists():
                raise AdoptionError(
                    "La carpeta externa debe existir y el archivo de salida no debe existir."
                )
            output.write_text(encoded, encoding="utf-8", newline="\n")
            result = {
                "status": "inventory-complete" if code == 0 else "repository-changed",
                "report_path": str(output),
                "read_only_proof": report["read_only_proof"],
            }
            print(
                json.dumps(result, indent=2, ensure_ascii=False)
                if args.as_json
                else result["status"]
            )
        else:
            print(encoded, end="")
        return code
    except (AdoptionError, OSError, ValueError) as exc:
        result = {"status": "error", "changed": False, "error": str(exc)}
        print(
            json.dumps(result, indent=2, ensure_ascii=False)
            if args.as_json
            else f"ERROR: {exc}"
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
