"""Prepare only reference locks and AUTH/EXEC/CKPT for an approved consumer stack."""

from __future__ import annotations
import copy
import hashlib
import sys
from datetime import date
from pathlib import Path

from project_variants import (
    ROOT,
    VariantError,
    load_config,
    project_context,
    proposal,
    current_approval,
    digest,
    checked_path,
)


def prepare(
    root: Path,
    variant_id: str,
    *,
    stage: str = "development",
    actor: str = "codex",
    apply: bool = False,
    preview_hash: str | None = None,
) -> dict:
    root = root.resolve()
    config = load_config(root)
    variant = next(
        (v for v in (config or {}).get("variants", []) if v["id"] == variant_id), None
    )
    if not variant:
        raise VariantError("Missing project variant")
    context = project_context(root, variant)
    proposed = proposal(
        root, variant_id, variant["environment"], stage, context=context
    )
    approval = current_approval(root, proposed)
    if context["execution"]:
        return {
            "status": "already-started",
            "changed": False,
            "execution_id": context["execution"]["execution_id"],
            "human_confirmations_required": 0,
        }
    from delivery_engine import delivery_readiness, repository_revision
    from task_tracking_engine import assess_tracking

    ready = delivery_readiness(
        root, context["manifest"], variant["increment"], task_ids=variant["task_ids"]
    )
    blockers = list(ready.get("blockers", [])) + assess_tracking(
        root, context["manifest"], variant["task_ids"]
    ).get("blockers", [])
    if blockers:
        raise VariantError("; ".join(blockers))
    if any(
        context["delivery"]["tasks"][t]["Workflow state"] != "ready"
        for t in variant["task_ids"]
    ):
        raise VariantError("Variant preparation requires ready TASKs")
    manifest_path = checked_path(root, ".lks-sdd/project.json")
    original = manifest_path.read_bytes()
    manifest = copy.deepcopy(context["manifest"])
    revision = repository_revision(root)
    from profile_registry import load_profile_bundle
    from composition_contract import resolve_compositions

    planned, locks = [], []
    for binding_id in context["bindings"]:
        binding = context["delivery"]["bindings"][binding_id]
        bundle = load_profile_bundle(binding["profile_id"])
        data = (bundle.root / "technology-profile.lock.json").read_bytes()
        destination = checked_path(root, binding["lock_path"], exists=False)
        if destination.exists():
            if destination.read_bytes() != data:
                raise VariantError("A reference lock was modified; cannot overwrite it")
        else:
            planned.append((destination, data))
        locks.append(
            {"binding_id": binding_id, "sha256": hashlib.sha256(data).hexdigest()}
        )
    compositions, errors = resolve_compositions(
        root, context["delivery"], variant["task_ids"]
    )
    if errors:
        raise VariantError("; ".join(errors))
    for composition in compositions:
        destination = checked_path(root, composition["path"], exists=False)
        data = composition["content"].encode()
        if destination.exists() and destination.read_bytes() != data:
            raise VariantError("Reference composition lock changed")
        if not destination.exists():
            planned.append((destination, data))
    sys.path.insert(0, str(ROOT / "skills/lks-sdd-implement/scripts"))
    from prepare_increment import (
        _next_indexed_id,
        _task_replacements,
        _render_initial_checkpoint,
        _write_transaction,
    )

    execution_id = _next_indexed_id(
        [e["execution_id"] for e in manifest["executions"]], "EXEC"
    )
    checkpoint_id = _next_indexed_id(
        [
            p.stem
            for p in (root / "docs/lks-sdd/04-delivery/checkpoints").glob("CKPT-*.md")
        ],
        "CKPT",
    )
    checkpoint_path = checked_path(
        root, f"docs/lks-sdd/04-delivery/checkpoints/{checkpoint_id}.md", exists=False
    )
    planning, authorization = (
        context["planning"],
        context["authorization"]["authorization_id"],
    )
    day = date.today().isoformat()
    continuity = {
        "checkpoint": f"../checkpoints/{checkpoint_id}.md",
        "authorization": authorization,
        "scope": ", ".join(variant["task_ids"]),
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "next_safe_action": "Implement approved TASK scope; verify with project variant",
    }
    replacements = _task_replacements(
        root, manifest, variant["task_ids"], revision, day, actor, continuity
    )
    anticipated = repository_revision(
        root,
        overrides={p.relative_to(root).as_posix(): b for p, b in planned}
        | {p.relative_to(root).as_posix(): b for p, _, b in replacements},
    )
    checkpoint = _render_initial_checkpoint(
        root,
        manifest,
        execution_id,
        checkpoint_id,
        variant["task_ids"],
        variant["release"],
        authorization,
        planning,
        revision,
        anticipated,
        day,
        actor,
        [],
        planned,
        replacements,
    )
    planned.append((checkpoint_path, checkpoint))
    material = {
        "approval_id": approval["approval_id"],
        "actor": actor,
        "date": day,
        "manifest": hashlib.sha256(original).hexdigest(),
        "created": {
            p.relative_to(root).as_posix(): hashlib.sha256(b).hexdigest()
            for p, b in planned
        },
        "updated": {
            p.relative_to(root).as_posix(): hashlib.sha256(b).hexdigest()
            for p, _, b in replacements
        },
    }
    expected = digest(material)
    result = {
        "status": "dry-run",
        "changed": False,
        "preview_hash": expected,
        "execution_id": execution_id,
        "checkpoint": checkpoint_path.relative_to(root).as_posix(),
        "created": list(material["created"]),
        "updated": list(material["updated"]),
        "functional_files_written": [],
        "human_confirmations_required": 0,
    }
    if not apply:
        return result
    if preview_hash != expected:
        raise VariantError("Preparation preview changed")
    # Approval and current canonical scope were re-evaluated in this very apply call.
    changed = result["created"] + result["updated"]
    execution = {
        "execution_id": execution_id,
        "status": "in-progress",
        "increment": variant["increment"],
        "release": variant["release"],
        "task_ids": variant["task_ids"],
        "profile_bindings": context["bindings"],
        "locks": locks,
        "branch": revision.get("branch"),
        "revision_start": revision["revision"],
        "last_observed_revision": anticipated["revision"],
        "authorization_id": authorization,
        "specification_fingerprint": planning["specification_fingerprint"],
        "planning_fingerprint": planning["planning_fingerprint"],
        "latest_checkpoint": result["checkpoint"],
        "changed_paths": changed,
        "evidence_ids": [],
    }
    manifest["executions"].append(execution)
    manifest["implementation"] = {
        k: v
        for k, v in execution.items()
        if k not in {"execution_id", "release", "last_observed_revision"}
    }
    manifest.update(
        phase="implementation", gate="G3", active_increment=variant["increment"]
    )
    manifest["active_tasks"] = sorted(
        set(manifest.get("active_tasks", [])) | set(variant["task_ids"])
    )
    manifest["active_task"] = (
        manifest["active_tasks"][0] if len(manifest["active_tasks"]) == 1 else None
    )
    _write_transaction(root, manifest, original, planned, replacements)
    return {**result, "status": "prepared", "changed": True}
