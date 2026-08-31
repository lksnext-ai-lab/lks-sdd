"""Packaged adoption adapters: inspect and prepare verification resources only."""
from __future__ import annotations

import json
import ast
from pathlib import Path
from typing import Any

from technology_resolution import LAYOUTS, diagnose, inspect_dependencies


def adoption_preview(root: Path, binding: dict[str, Any], driver: dict[str, Any]) -> dict[str, Any]:
    policy = driver.get("prepare", {}).get("adoption", {})
    if policy.get("strategy") != "verification-only":
        raise ValueError("El perfil no ofrece adopción segura; no se copiará el scaffold funcional.")
    root = root.resolve()
    unit = root / str(binding.get("unit_path", "."))
    unit.resolve().relative_to(root)
    if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in [unit, *unit.parents] if p != root.parent):
        raise ValueError("Adoption path must not traverse links")
    inspection = inspect_dependencies(root)
    matches = sorted(set(inspection["layouts"]) & set(policy.get("adapters", [])))
    if len(matches) > 1:
        raise ValueError("Estructura ambigua; seleccionar unidades explícitas antes de preparar.")
    adapter = matches[0] if matches else "unit" if "unit" in policy.get("adapters", []) and unit.is_dir() else None
    if adapter is None:
        raise ValueError("La estructura observada no tiene adaptador empaquetado.")
    resolution = diagnose(unit, str(binding["profile_id"]))
    unit_paths = LAYOUTS.get(adapter, {"unit": str(binding.get("unit_path", "."))})
    entries = []
    contracts = []
    for relative in unit_paths.values():
        base = root / relative
        # The adapter recognizes known ASGI entrypoints without importing code.
        candidates = [p for p in ["src/lks_sdd_app/main.py", "src/local_auth/main.py", "app/main.py", "main.py"] if (base / p).is_file()]
        entries.extend((Path(relative) / p).as_posix() for p in candidates)
        for candidate in candidates:
            path = base / candidate
            if path.is_symlink() or path.stat().st_size > 1024 * 1024:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (ValueError, SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr in {"get", "post", "put", "patch", "delete"} and decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                            contracts.append({"method": decorator.func.attr.upper(), "path_fragment": decorator.args[0].value,
                                              "source": path.relative_to(root).as_posix(), "line": node.lineno,
                                              "router_prefix_verified": False, "runtime_verified": False})
    return {"schema_version": "1.0", "mode": "adoption", "binding_id": binding["binding_id"],
            "profile_id": binding["profile_id"], "adapter": adapter, "unit_paths": unit_paths,
            "entries_observed": entries, "contracts_observed": contracts, "resolution": resolution,
            "functional_files_written": [], "consumer_changes": [],
            "fit_matrix": [{"dimension": "layout", "observed": adapter, "plugin_change": "packaged-adapter", "consumer_change": "none"},
                           {"dimension": "dependencies", "observed": resolution["compatibility"], "plugin_change": "exact-resolution", "consumer_change": "explicit-reconciliation" if resolution["reasons"] else "none"},
                           {"dimension": "functional-contract", "observed": "not-executed", "plugin_change": "contract-observers", "consumer_change": "assess-endpoints-session-and-permissions"}],
            "blockers": resolution["reasons"],
            "commands_from_metadata": False}


def adoption_resources(root: Path, binding: dict[str, Any], driver: dict[str, Any]) -> list[tuple[Path, bytes]]:
    preview = adoption_preview(root, binding, driver)
    relative = Path(".lks-sdd/verification") / str(binding["binding_id"]) / "adoption.json"
    # No consumer Python/JS is copied, imported or executed. This receipt pins
    # the dependency inventory to the same guarded preview/apply transaction.
    result = [(root / relative, (json.dumps(preview, sort_keys=True, indent=2) + "\n").encode())]
    from profile_registry import PLUGIN_ROOT, load_profile_bundle, profile_source_files
    bundle = load_profile_bundle(binding["profile_id"])
    resources = PLUGIN_ROOT / "profiles/_shared/local-auth/verification"
    base = root / relative.parent
    for source in profile_source_files(resources):
        result.append((base / "observer" / source.relative_to(resources), source.read_bytes()))
    config = json.loads((bundle.root / "scaffold/profile-runtime.json").read_text())
    config.update({"mode": "adoption", "unit_paths": preview["unit_paths"],
                   "functional_contract_status": "pending-review",
                   "fixture_status": "pending-isolated-fixture",
                   "entrypoints_observed": preview["entries_observed"]})
    result.append((base / "profile-runtime.json", (json.dumps(config, sort_keys=True, indent=2) + "\n").encode()))
    return result
