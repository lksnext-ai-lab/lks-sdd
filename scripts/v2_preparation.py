"""Reference material preparation, separate from authorization and actual verification."""
from __future__ import annotations

from pathlib import Path
import sys
from v2_contract import ContractError, load, path_at, read_bytes, sha
from v2_lifecycle import current_authorization, validate_scope_path
from v2_storage import apply, preview


def reference_locks(model, tasks):
    from profile_registry import load_profile_bundle, resolve_profile
    changes = {}
    for identifier in sorted({b for t in tasks for b in model.elements[t].targets("bindings")}):
        binding = model.elements[identifier]
        profile = binding.meta["profile_id"]
        if not resolve_profile(profile).verifiable:
            raise ContractError("Reference profile is not currently certified: " + profile)
        bundle = load_profile_bundle(profile)
        relative = binding.meta.get("lock_path", f".lks-sdd/profiles/{identifier}.lock.json")
        if relative != f".lks-sdd/profiles/{identifier}.lock.json":
            raise ContractError("Reference locks use their dedicated binding path")
        raw = (bundle.root / "technology-profile.lock.json").read_bytes()
        path = path_at(model.root, relative, missing=True)
        if path.exists() and path.read_bytes() != raw:
            raise ContractError("Reference lock differs; never overwrite it silently")
        if not path.exists():
            changes[relative] = raw
    from v2_composition import preparation
    changes.update(preparation(model, tasks))
    return changes


def prepare(model, tasks, environment, *, authorized_hash=None):
    import fnmatch
    current_authorization(model, tasks, environment)
    from project_variants import load_config
    if load_config(model.root):
        raise ContractError("Variant preparation is part of v2 start; do not copy a reference scaffold into a variant")
    bindings = []
    for identifier in sorted({b for t in tasks for b in model.elements[t].targets("bindings")}):
        item = model.elements[identifier]
        if item.meta["state"] not in {"confirmed", "approved"}:
            raise ContractError("Technology selection is not confirmed")
        bindings.append({"binding_id": identifier, "profile_id": item.meta["profile_id"],
                         "unit_path": item.meta.get("unit_path", "."),
                         "lock_path": item.meta.get("lock_path", f".lks-sdd/profiles/{identifier}.lock.json")})
    if not bindings:
        raise ContractError("No explicit profile selected; preferred stack is never implicit")
    locks_and_compositions = reference_locks(model, tasks)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "skills/lks-sdd-implement/scripts"))
    from prepare_increment import _planned_files
    adopted = model.manifest.get("route") == "adopt-existing"
    planned, preserved, manual, locks = _planned_files(model.root, bindings, mode="adoption" if adopted else "new-project")
    if manual:
        raise ContractError("Reference scaffold collides with existing work: " + ", ".join(manual))
    changes = {**locks_and_compositions, **{path.relative_to(model.root).as_posix(): raw for path, raw in planned}}
    patterns = [p for t in tasks for p in model.elements[t].meta["paths"]]
    for name in changes:
        path_at(model.root, name, missing=True, package_data=True)
        internal = name.startswith((".lks-sdd/profiles/", ".lks-sdd/compositions/", ".lks-sdd/verification/compositions/"))
        internal |= adopted and any(name.startswith(".lks-sdd/verification/" + b["binding_id"] + "/") for b in bindings)
        if not internal and not any(fnmatch.fnmatchcase(name, p) for p in patterns):
            raise ContractError("Preparation outside approved TASK paths: " + name)
    result = preview(model.root, changes, sources=model.hashes, operation="prepare-exact-reference")
    return apply(model.root, changes, result, authorized_hash) if authorized_hash else {**result, "preserved": preserved, "locks": locks, "verification": "not-run"}
