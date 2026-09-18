"""Proportional verification for explicitly approved project variants."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from project_variants import (
    ROOT,
    VariantError,
    proposal,
    current_approval,
    project_context,
    input_hashes,
    digest,
    checked_path,
    read_json,
    load_config,
)


def engine_fingerprint() -> str:
    paths = [
        "scripts/project_variants.py",
        "scripts/consumer_observer.py",
        "scripts/variant_verification.py",
        "scripts/variant_preparation.py",
        "scripts/manage_project_variants.py",
        "schemas/project-variants.schema.json",
        "schemas/consumer-observation.schema.json",
    ]
    return digest(
        {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    )


def applicability(context: dict, tasks: list[str]) -> list[dict]:
    from evidence_contract import (
        visual_gate_applicability,
        integration_gate_applicability,
    )
    from validate_project import (
        parse_frontmatter,
        table_rows_for_headers,
        parse_markdown_table_blocks,
        INTERFACE_CONTRACT_HEADERS,
        interface_applicability,
    )

    entry = next(
        a for a in context["manifest"]["artifacts"] if a["id"] == "ART-INCREMENTS"
    )
    _, body = parse_frontmatter(
        (context["root"] / entry["path"]).read_text(encoding="utf-8")
    )
    rows = (
        table_rows_for_headers(
            parse_markdown_table_blocks(body), INTERFACE_CONTRACT_HEADERS
        )
        or []
    )
    increments = {context["delivery"]["tasks"][t]["Increment"] for t in tasks}
    interface = any(
        r.get("Increment") in increments
        and interface_applicability(r.get("Interface applicability", ""))[0]
        == "applicable"
        for r in rows
    )
    return [
        visual_gate_applicability(
            tasks, context["delivery"], release_interface_applicable=interface
        ),
        *integration_gate_applicability(tasks, context["delivery"]),
    ]


def required_gates(context: dict, variant: dict) -> set[str]:
    gates = set()
    for task in variant["task_ids"]:
        definitions = context["delivery"]["task_details"][task].get("definition", [])
        for definition in definitions:
            gates.update(
                re.findall(
                    r"\bGATE-[A-Z0-9-]{3,80}\b", definition.get("Technical gates", "")
                )
            )
    gates.update(
        a["gate_id"]
        for a in applicability(context, variant["task_ids"])
        if a["status"] == "applicable"
    )
    return gates


def evidence_integrity(root: Path, evidence: dict) -> None:
    expected = digest({k: v for k, v in evidence.items() if k != "integrity_sha256"})
    if evidence.get("integrity_sha256") != expected:
        raise VariantError("Variant evidence integrity mismatch")
    for check in evidence.get("checks", []):
        for artifact in check.get("artifacts", []):
            path = checked_path(root, artifact["evidence_path"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                raise VariantError("Recorded observer artifact hash mismatch")


def _gate_material(
    root: Path, variant: dict, gate: dict, proposed: dict
) -> tuple[dict, dict]:
    hashes = input_hashes(root, gate.get("inputs", variant["inputs"]))
    hashes.update(proposed["material"]["dependency_hashes"])
    for observer_files in proposed["material"]["observer_hashes"].values():
        hashes.update(observer_files)
    material = {
        "inputs": hashes,
        "gate": gate,
        "approval_fingerprint": proposed["fingerprint"],
        "engine": engine_fingerprint(),
    }
    return material, hashes


def _fresh(timestamp: str, hours: int) -> bool:
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(timestamp)
        return timedelta(0) <= age <= timedelta(hours=hours)
    except (TypeError, ValueError):
        return False


def plan(
    root: Path,
    variant_id: str,
    environment: str,
    stage: str,
    *,
    reuse_evidence: str | None = None,
) -> dict:
    config = load_config(root)
    variant = next(
        (v for v in (config or {}).get("variants", []) if v["id"] == variant_id), None
    )
    if not variant:
        raise VariantError("No configured variant")
    context = project_context(root, variant, execution=True)
    proposed = proposal(root, variant_id, environment, stage, context=context)
    approval = current_approval(root, proposed)
    levels = {
        "development": 0,
        "integration": 1,
        "preproduction": 1,
        "release": 2,
        "production": 2,
    }
    required = required_gates(context, variant)
    gates = list(variant["gates"])
    if stage in {"release", "production"}:
        from profile_registry import load_profile_bundle

        base = load_profile_bundle(variant["profile_id"])
        required.update(
            c["id"]
            for c in base.driver["verify"]["checks"]
            if c.get("required") and c.get("phase") != "G4"
        )
    known = {g["id"] for g in gates}
    missing = sorted(required - known)
    cache = []
    if reuse_evidence and not re.fullmatch(r"EVID-\d{3}", reuse_evidence):
        raise VariantError("Reuse requires an EVID-###")
    for path in sorted((root / "docs/lks-sdd/evidence").glob("EVID-*.json")):
        value = read_json(checked_path(root, path.relative_to(root).as_posix()))
        if (
            value.get("project_variant", {}).get("approval_id")
            == approval["approval_id"]
        ):
            evidence_integrity(root, value)
            if not reuse_evidence or value["evidence_id"] == reuse_evidence:
                cache.append(value)
    if reuse_evidence and not cache:
        raise VariantError("Requested evidence is absent or outside this approval")
    checks = []
    for gate in gates:
        material, hashes = _gate_material(root, variant, gate, proposed)
        key = digest(material)
        reusable = None
        if gate["deterministic"] and stage not in {"release", "production"}:
            for previous in reversed(cache):
                candidate = next(
                    (
                        c
                        for c in previous["checks"]
                        if c.get("input_key") == key
                        and c["status"] == "passed"
                        and _fresh(
                            c.get("observed_at", previous["recorded_at"]),
                            proposed["material"]["policy"]["cache_max_age_hours"],
                        )
                    ),
                    None,
                )
                if candidate:
                    candidate = copy.deepcopy(candidate)
                    candidate.setdefault("observed_at", previous["recorded_at"])
                    reusable = {
                        "evidence_id": previous["evidence_id"],
                        "check": candidate,
                    }
                    break
        selected = levels[gate["stage"]] <= levels[stage]
        disposition = "reused" if reusable else "execute" if selected else "omitted"
        checks.append(
            {
                "gate": gate,
                "input_key": key,
                "input_hashes": hashes,
                "disposition": disposition,
                "reuse": reusable,
                "reason": "Current deterministic evidence"
                if reusable
                else "Selected stage"
                if selected
                else "Deferred to " + gate["stage"],
            }
        )
    return {
        "status": "planned",
        "variant": variant,
        "proposal": proposed,
        "approval": approval,
        "context": context,
        "checks": checks,
        "missing_critical_gates": missing,
        "required_gates": sorted(required),
        "stage": stage,
        "environment": environment,
        "human_confirmations_required": 0,
        "processes_executed": 0,
    }


def visual_check(
    root: Path,
    context: dict,
    variant: dict,
    requested: str | None,
    revision: dict | None = None,
) -> tuple[dict | None, list[str]]:
    """Use the existing human/browser contract; never accept a consumer self-attestation."""
    required = "GATE-VISUAL-BROWSER-REVIEW" in required_gates(context, variant)
    if not required:
        if requested:
            raise VariantError("Visual evidence is outside this TASK scope")
        return None, []
    base = {
        "name": "visual-browser-review",
        "gate_id": "GATE-VISUAL-BROWSER-REVIEW",
        "evidence_scopes": ["visual"],
        "interface_ids": [],
    }
    if not requested:
        return {
            **base,
            "status": "not-run",
            "reason": "manual-browser-evidence-missing",
        }, []
    from validate_project import validate_visual_review_evidence
    from validation_evidence import resolve_visual_policy

    policies, errors = resolve_visual_policy(variant["task_ids"], context["delivery"])
    if errors:
        raise VariantError("Invalid visual policy: " + "; ".join(errors))
    errors, outcome, limitations, files = validate_visual_review_evidence(
        root,
        context["manifest"],
        context["definitions"],
        variant["increment"],
        requested,
        require_fresh=True,
        task_ids=variant["task_ids"],
        policies=policies,
        require_v12=True,
        expected_revision=revision,
    )
    if errors or outcome is None:
        raise VariantError("Invalid visual evidence: " + "; ".join(errors))
    paths = set(files) | {outcome["evidence"]}
    outcome["visual_input_hashes"] = {
        p: hashlib.sha256(checked_path(root, p).read_bytes()).hexdigest() for p in paths
    }
    return {**outcome, **base}, limitations


def _identity(
    root: Path, context: dict, proposed: dict, checks: list[dict]
) -> tuple[dict, list[dict], str]:
    from profile_registry import load_profile_bundle
    from evidence_contract import _canonical_payload

    bindings, locks = [], []
    execution_locks = {
        l["binding_id"]: l["sha256"] for l in context["execution"].get("locks", [])
    }
    for binding_id in context["bindings"]:
        binding = context["delivery"]["bindings"][binding_id]
        bundle = load_profile_bundle(binding["profile_id"])
        path = checked_path(root, binding["lock_path"])
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if (
            raw != (bundle.root / "technology-profile.lock.json").read_bytes()
            or execution_locks.get(binding_id) != sha
        ):
            raise VariantError("Reference lock changed or is not linked to EXEC")
        bindings.append({**binding, "profile_version": bundle.profile["version"]})
        locks.append(
            {
                "binding_id": binding_id,
                "profile_id": binding["profile_id"],
                "profile_version": bundle.profile["version"],
                "sha256": sha,
                "path": binding["lock_path"],
            }
        )
    from composition_contract import resolve_compositions

    compositions, composition_errors = resolve_compositions(
        root,
        context["delivery"],
        proposed["material"]["variant"]["task_ids"],
        require_locks=True,
    )
    if composition_errors:
        raise VariantError(
            "Reference composition integrity failure: " + "; ".join(composition_errors)
        )
    material = {
        "profile_bindings": bindings,
        "locks": locks,
        "compositions": [
            {k: v for k, v in c.items() if k != "content"} for c in compositions
        ],
        "consumer_composition": proposed["material"]["variant"]["composition"],
        "variant_fingerprint": proposed["fingerprint"],
        "gate_inputs": {c["gate_id"]: c.get("input_key") for c in checks},
        "artifacts": sorted(
            {a["sha256"] for c in checks for a in c.get("artifacts", [])}
        ),
    }
    return (
        material,
        locks,
        "build-sha256:" + hashlib.sha256(_canonical_payload(material)).hexdigest(),
    )


def verify(
    root: Path,
    variant_id: str,
    environment: str,
    stage: str,
    *,
    execute: bool = False,
    evidence_id: str | None = None,
    force: bool = False,
    rerun_reason: str | None = None,
    reuse_evidence: str | None = None,
    visual_evidence: str | None = None,
) -> dict:
    selection = plan(
        root, variant_id, environment, stage, reuse_evidence=reuse_evidence
    )
    if force and not rerun_reason:
        raise VariantError("A forced rerun requires a reason")
    if force:
        for entry in selection["checks"]:
            if entry["disposition"] == "reused":
                entry.update(
                    disposition="execute",
                    reuse=None,
                    reason="Forced rerun: " + rerun_reason,
                )
    if not execute:
        return {
            "status": "planned",
            "checks": [
                {
                    "gate_id": c["gate"]["id"],
                    "disposition": c["disposition"],
                    "reason": c["reason"],
                }
                for c in selection["checks"]
            ],
            "missing_critical_gates": selection["missing_critical_gates"],
            "human_confirmations_required": 0,
            "processes_executed": 0,
            "profile_certification": selection["proposal"]["profile_certification"],
            "consumer_approval": {
                "status": "valid",
                "approval_id": selection["approval"]["approval_id"],
            },
        }
    if not evidence_id or not re.fullmatch(r"EVID-\d{3}", evidence_id):
        raise VariantError("Official execution needs a new EVID-###")
    evidence_path = checked_path(
        root, f"docs/lks-sdd/evidence/{evidence_id}.json", exists=False
    )
    if evidence_path.exists():
        existing = read_json(evidence_path)
        evidence_integrity(root, existing)
        # Repeating a record request is idempotent only for the same current subject.
        if (
            existing.get("project_variant", {}).get("approval_id")
            == selection["approval"]["approval_id"]
            and existing["project_variant"]["stage"] == stage
            and stage not in {"release", "production"}
            and _fresh(
                existing["recorded_at"],
                selection["proposal"]["material"]["policy"]["cache_max_age_hours"],
            )
            and all(
                any(
                    c.get("gate_id") == s["gate"]["id"]
                    and s["gate"]["deterministic"]
                    and c.get("input_key") == s["input_key"]
                    and c["status"] == "passed"
                    and _fresh(
                        c.get("observed_at", existing["recorded_at"]),
                        selection["proposal"]["material"]["policy"][
                            "cache_max_age_hours"
                        ],
                    )
                    for c in existing["checks"]
                )
                for s in selection["checks"]
                if s["disposition"] != "omitted"
            )
            and "GATE-VISUAL-BROWSER-REVIEW" not in selection["required_gates"]
            and not force
        ):
            return {
                "status": existing["classification"],
                "evidence_id": evidence_id,
                "changed": False,
                "processes_executed": 0,
                "evidence_recorded": True,
                "reused": True,
            }
        raise VariantError("Evidence IDs are immutable; choose a new EVID")
    from consumer_observer import execute as execute_observer
    from delivery_engine import repository_revision

    variant, context, proposed = (
        selection["variant"],
        selection["context"],
        selection["proposal"],
    )
    before_inputs = input_hashes(root, variant["inputs"])
    before_revision = repository_revision(root)
    checks, omitted, blobs, executed = [], [], {}, 0
    for entry in selection["checks"]:
        gate = entry["gate"]
        if entry["disposition"] == "omitted":
            omitted.append(
                {"gate_id": gate["id"], "status": "not-run", "reason": entry["reason"]}
            )
            continue
        if entry["reuse"] and not force:
            check = copy.deepcopy(entry["reuse"]["check"])
            check.update(
                disposition="reused", reused_from=entry["reuse"]["evidence_id"]
            )
        else:
            check, artifacts = execute_observer(
                root, gate, entry["input_hashes"], profile_id=variant["profile_id"]
            )
            executed += 1
            blobs.update(artifacts)
            check["disposition"] = "executed"
            check["observed_at"] = datetime.now(timezone.utc).isoformat()
            for artifact in check["artifacts"]:
                artifact["evidence_path"] = (
                    "docs/lks-sdd/evidence/variant-artifacts/" + artifact["sha256"]
                )
        check["input_key"] = entry["input_key"]
        checks.append(check)
    visual, visual_limitations = visual_check(
        root, context, variant, visual_evidence, before_revision
    )
    if visual:
        checks.append(visual)
    # All required scopes must have passed before the result can be used for closure.
    passed = {c["gate_id"] for c in checks if c["status"] == "passed"}
    missing = set(selection["required_gates"]) - passed
    if missing:
        checks.append(
            {
                "name": "required-task-gates",
                "gate_id": "GATE-VARIANT-CLOSURE",
                "status": "blocked",
                "evidence_scopes": ["contract"],
                "interface_ids": [],
                "reason": "Required gates pending: " + ", ".join(sorted(missing)),
            }
        )
    if not checks:
        checks.append(
            {
                "name": "no-selected-gates",
                "gate_id": "GATE-VARIANT-CLOSURE",
                "status": "not-run",
                "evidence_scopes": ["component"],
                "interface_ids": [],
            }
        )
    if (
        input_hashes(root, variant["inputs"]) != before_inputs
        or proposal(root, variant_id, environment, stage)["fingerprint"]
        != proposed["fingerprint"]
    ):
        raise VariantError("Project changed during verification; no evidence recorded")
    current_approval(root, proposed)
    for check in checks:
        if not check.get("artifacts"):
            # Persist an attributable result, including failures/not-run and manual review.
            raw = json.dumps(check, sort_keys=True, ensure_ascii=False).encode()
            sha = hashlib.sha256(raw).hexdigest()
            blobs[sha] = raw
            check["artifacts"] = [
                {
                    "path": "check-result.json",
                    "sha256": sha,
                    "size": len(raw),
                    "evidence_path": "docs/lks-sdd/evidence/variant-artifacts/" + sha,
                }
            ]
    material, locks, build_id = _identity(root, context, proposed, checks)
    limitations = [
        "Project-approved technology; consumer stack has no global certification.",
        f"Valid only for {stage}/{environment}; release and deployment need separate evidence and authorization.",
    ] + visual_limitations
    classification = (
        "verified-with-reservations"
        if all(c["status"] == "passed" for c in checks)
        else "not-verified"
    )
    artifacts = sorted(
        {"sha256:" + a["sha256"] for c in checks for a in c.get("artifacts", [])}
    )
    evidence = {
        "schema_version": "1.3",
        "evidence_id": evidence_id,
        "execution_id": context["execution"]["execution_id"],
        "increment": variant["increment"],
        "task_ids": variant["task_ids"],
        "profile_bindings": context["bindings"],
        "profile_locks": locks,
        "build_identity_material": material,
        "build_id": build_id,
        "revision": before_revision["revision"],
        "tree_id": before_revision["tree_id"],
        "tree_sha256": before_revision["tree_sha256"],
        "artifact_digests": artifacts,
        "environment": environment,
        "classification": classification,
        "checks": checks,
        "gate_applicability": applicability(context, variant["task_ids"]),
        "limitations": limitations,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "omitted_checks": omitted,
        "project_variant": {
            "id": variant_id,
            "fingerprint": proposed["fingerprint"],
            "approval_id": selection["approval"]["approval_id"],
            "stage": stage,
            "source_hashes": before_inputs,
            "engine_sha256": engine_fingerprint(),
        },
        "profile_certification": proposed["profile_certification"],
        "consumer_approval": {
            "status": "valid",
            "approval_id": selection["approval"]["approval_id"],
        },
        "verification_result": classification,
        "delivery_readiness": "not-assessed",
        "execution_accounting": {
            "executed": executed,
            "reused": sum(c.get("disposition") == "reused" for c in checks),
            "omitted": len(omitted),
            "rerun_reason": rerun_reason,
        },
    }
    from evidence_contract import canonical_top_level_profile_identity

    evidence.update(canonical_top_level_profile_identity(material["profile_bindings"]))
    from validate_project import evidence_document_errors
    from evidence_contract import (
        evidence_gate_applicability_errors,
        evidence_profile_identity_errors,
    )

    errors = evidence_document_errors(evidence, evidence_id)
    errors.extend(
        evidence_gate_applicability_errors(evidence, evidence["gate_applicability"])
    )
    errors.extend(evidence_profile_identity_errors(evidence, context["manifest"]))
    if errors:
        raise VariantError("Evidence failed canonical validation: " + "; ".join(errors))
    evidence["integrity_sha256"] = digest(evidence)
    record(root, evidence, context, blobs)
    return {
        "status": classification,
        "verification_result": classification,
        "evidence_id": evidence_id,
        "evidence_recorded": True,
        "changed": True,
        "profile_certification": evidence["profile_certification"],
        "consumer_approval": evidence["consumer_approval"],
        "delivery_readiness": "not-assessed",
        "task_status": "unchanged",
        "processes_executed": executed,
        "accounting": evidence["execution_accounting"],
        "human_confirmations_required": 0,
        "limitations": limitations,
    }


def record(root: Path, evidence: dict, context: dict, blobs: dict[str, bytes]) -> None:
    from work_task import _apply_project_transaction

    manifest_path = checked_path(root, ".lks-sdd/project.json")
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    if manifest != context["manifest"]:
        raise VariantError("Manifest changed during verification")
    verification = {
        k: evidence[k]
        for k in (
            "increment",
            "task_ids",
            "revision",
            "tree_id",
            "tree_sha256",
            "build_id",
            "artifact_digests",
            "environment",
            "execution_id",
            "limitations",
        )
    }
    verification.update(
        status=evidence["classification"],
        gate_ids=sorted({c["gate_id"] for c in evidence["checks"]}),
        evidence_ids=[evidence["evidence_id"]],
    )
    manifest["verification"] = verification
    for execution in manifest["executions"]:
        if execution["execution_id"] == evidence["execution_id"]:
            execution["evidence_ids"] = list(
                dict.fromkeys(
                    [*execution.get("evidence_ids", []), evidence["evidence_id"]]
                )
            )
    path = checked_path(
        root, f"docs/lks-sdd/evidence/{evidence['evidence_id']}.json", exists=False
    )
    replacements = {
        manifest_path: (
            original,
            (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode(),
        ),
        path: (
            None,
            (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode(),
        ),
    }
    for sha, data in blobs.items():
        artifact = checked_path(
            root, "docs/lks-sdd/evidence/variant-artifacts/" + sha, exists=False
        )
        if artifact.exists():
            if artifact.read_bytes() != data:
                raise VariantError("Immutable artifact collision")
        else:
            replacements[artifact] = (None, data)
    _apply_project_transaction(root, replacements)


def completion_fields(
    root: Path, manifest: dict, task_id: str | None = None
) -> dict | None:
    verification = manifest.get("verification", {})
    evidence_ids = verification.get("evidence_ids", [])
    if not evidence_ids:
        return None
    evidence_id = evidence_ids[-1]
    if not re.fullmatch(r"EVID-\d{3}", str(evidence_id)):
        raise VariantError("Invalid evidence reference")
    evidence = read_json(
        checked_path(root, f"docs/lks-sdd/evidence/{evidence_id}.json")
    )
    if "project_variant" not in evidence:
        return None
    evidence_integrity(root, evidence)
    data = evidence["project_variant"]
    proposed = proposal(root, data["id"], evidence["environment"], data["stage"])
    approval = current_approval(root, proposed)
    variant = proposed["material"]["variant"]
    if not proposed["material"]["policy"]["allow_task_closure"]:
        raise VariantError("Project policy does not allow TASK closure with a variant")
    if data["stage"] == "production":
        raise VariantError("Production requires a separate delivery workflow")
    if (
        approval["approval_id"] != data["approval_id"]
        or data["fingerprint"] != proposed["fingerprint"]
    ):
        raise VariantError("Evidence approval is no longer current")
    if data["engine_sha256"] != engine_fingerprint() or data[
        "source_hashes"
    ] != input_hashes(root, variant["inputs"]):
        raise VariantError("Implementation or verification engine changed; reverify")
    context = project_context(root, variant, execution=True)
    for check in evidence["checks"]:
        if check.get("name") == "visual-browser-review":
            actual, _ = visual_check(root, context, variant, check.get("evidence"))
            if (
                not actual
                or actual["status"] != "passed"
                or actual.get("visual_input_hashes") != check.get("visual_input_hashes")
            ):
                raise VariantError("Visual evidence changed or expired")
    if context["execution"]["execution_id"] != evidence[
        "execution_id"
    ] or evidence_id not in context["execution"].get("evidence_ids", []):
        raise VariantError("Evidence is not linked to the current EXEC")
    if task_id and task_id not in evidence["task_ids"]:
        raise VariantError("Evidence does not cover this TASK")
    if set(evidence["task_ids"]) != set(variant["task_ids"]):
        raise VariantError("Evidence TASK scope changed")
    if (
        evidence["classification"] not in {"verified", "verified-with-reservations"}
        or verification.get("status") != evidence["classification"]
    ):
        raise VariantError("TASK is not verified")
    if (
        not evidence["limitations"]
        or evidence["profile_certification"].get("consumer_certified") is not False
    ):
        raise VariantError("Variant evidence must preserve certification limitations")
    for field in (
        "revision",
        "build_id",
        "environment",
        "artifact_digests",
        "task_ids",
        "execution_id",
    ):
        if verification.get(field) != evidence.get(field):
            raise VariantError(
                "Verification index differs from canonical evidence: " + field
            )
    gates = {c["gate_id"] for c in evidence["checks"] if c["status"] == "passed"}
    if (
        any(c["status"] != "passed" for c in evidence["checks"])
        or not required_gates(context, variant) <= gates
    ):
        raise VariantError("Critical gates failed or remain pending")
    # Recompute every gate input, so per-gate reuse cannot hide a changed dependency/test.
    for gate in variant["gates"]:
        if gate["id"] in gates:
            material, _ = _gate_material(root, variant, gate, proposed)
            if not any(
                c["gate_id"] == gate["id"] and c.get("input_key") == digest(material)
                for c in evidence["checks"]
            ):
                raise VariantError("Gate inputs changed")
    _identity(root, context, proposed, evidence["checks"])
    return {
        "evidence": evidence_id,
        "revision": evidence["revision"],
        "build": evidence["build_id"],
        "artifact_digest": evidence["artifact_digests"][0],
        "environment": evidence["environment"],
        "gate": sorted(gates),
    }
