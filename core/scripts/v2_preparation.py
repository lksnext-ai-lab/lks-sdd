"""Prepare only local, authorized v2 records; never materialize technology scaffolds."""
from __future__ import annotations

import fnmatch

from v2_contract import ContractError, path_at
from v2_lifecycle import current_authorization
from v2_storage import apply, preview


def prepare(model, tasks, environment, *, authorized_hash=None):
    current_authorization(model, tasks, environment)
    from v2_contract import technology_readiness
    readiness = technology_readiness(model, tasks)
    if readiness["blockers"]:
        raise ContractError("; ".join(readiness["blockers"]))
    from v2_composition import preparation
    changes = preparation(model, tasks)
    patterns = [pattern for task in tasks for pattern in model.elements[task].meta["paths"]]
    for name in changes:
        path_at(model.root, name, missing=True, package_data=True)
        internal = name.startswith(".lks-sdd/compositions/")
        if not internal and not any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns):
            raise ContractError("Preparation outside approved TASK paths: " + name)
    result = preview(model.root, changes, sources=model.hashes, operation="prepare-local-records")
    if authorized_hash:
        return apply(model.root, changes, result, authorized_hash)
    return {**result, "preserved": [], "verification": "not-run"}
