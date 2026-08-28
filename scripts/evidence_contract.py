#!/usr/bin/env python3
"""Shared verification-evidence identity and TASK-slice applicability rules."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from profile_registry import load_profile_bundle


VISUAL_GATE_ID = "GATE-VISUAL-BROWSER-REVIEW"
REQUIREMENT_RE = re.compile(r"\b(?:FR|NFR|TR|BR)-[0-9]{3}\b")


def _canonical_payload(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def selected_task_requirements(
    task_ids: Iterable[str], delivery: dict[str, Any]
) -> set[str]:
    """Return requirements explicitly assigned to the exact TASK selection."""

    result: set[str] = set()
    for task_id in task_ids:
        details = delivery.get("task_details", {}).get(task_id, {})
        definition_rows = details.get("definition", [])
        if len(definition_rows) != 1:
            continue
        result.update(REQUIREMENT_RE.findall(definition_rows[0].get("Requirements", "")))
    return result


def canonical_top_level_profile_identity(
    material_bindings: Iterable[dict[str, Any]],
) -> dict[str, str]:
    """Emit the top-level pair only when the selected identity is singular."""

    selected = list(material_bindings)
    if len(selected) != 1:
        return {}
    profile_id = selected[0].get("profile_id")
    profile_version = selected[0].get("profile_version")
    if not isinstance(profile_id, str) or not isinstance(profile_version, str):
        return {}
    return {"profile_id": profile_id, "profile_version": profile_version}


def _release_scope(task_ids: list[str], delivery: dict[str, Any]) -> tuple[bool, str | None]:
    releases = {
        delivery.get("tasks", {}).get(task_id, {}).get("Release")
        for task_id in task_ids
    }
    releases.discard(None)
    if len(releases) != 1:
        return False, None
    release_id = str(next(iter(releases)))
    release_tasks = {
        candidate_id
        for candidate_id, row in delivery.get("tasks", {}).items()
        if row.get("Release") == release_id
    }
    return bool(release_tasks) and set(task_ids) == release_tasks, release_id


def visual_gate_applicability(
    task_ids: Iterable[str],
    delivery: dict[str, Any],
    *,
    release_interface_applicable: bool = False,
) -> dict[str, Any]:
    """Derive the visual gate only from the exact TASK slice and release boundary."""

    selected = sorted(set(task_ids))
    release_scope, release_id = _release_scope(selected, delivery)
    triggers: list[str] = []
    inspected: list[str] = []
    for task_id in selected:
        task = delivery.get("tasks", {}).get(task_id, {})
        details = delivery.get("task_details", {}).get(task_id, {})
        definition_rows = details.get("definition", [])
        definition = definition_rows[0] if len(definition_rows) == 1 else {}
        unit = delivery.get("units", {}).get(task.get("Unit"), {})
        binding = delivery.get("bindings", {}).get(task.get("Profile binding"), {})
        textual_fields = {
            "in-scope": definition.get("In scope", ""),
            "out-of-scope": definition.get("Out of scope", ""),
            "requirements": definition.get("Requirements", ""),
            "acceptance": definition.get("Acceptance", ""),
            "capabilities": definition.get("Required capabilities", ""),
            "gates": definition.get("Technical gates", ""),
            "unit": " ".join(
                str(unit.get(key, ""))
                for key in (
                    "Component",
                    "Responsibility",
                    "Runtime boundary",
                    "Interfaces",
                )
            ),
        }
        joined = " ".join(textual_fields.values())
        refs = sorted(set(re.findall(r"\b(?:UX|VIS)-[0-9]{3}\b", joined)))
        if refs:
            triggers.append(f"{task_id}:refs={','.join(refs)}")
        contract_ids = re.findall(
            r"\b(?:CAP|GATE)-[A-Z0-9-]{3,80}\b",
            " ".join([textual_fields["capabilities"], textual_fields["gates"]]),
        )
        direct_frontend = sorted(
            {
                item
                for item in contract_ids
                if {"FRONTEND", "BROWSER", "UI"} & set(item.split("-"))
            }
        )
        if direct_frontend:
            triggers.append(f"{task_id}:frontend-contract={','.join(direct_frontend)}")
        in_scope_text = textual_fields["in-scope"].casefold()
        backend_only = bool(
            re.search(
                r"\b(?:backend|api|worker|consumer|processor|database)\b",
                in_scope_text,
            )
        ) and not bool(
            re.search(
                r"\b(?:frontend|browser|interfaz|interface|ui|spa|screen)\b",
                in_scope_text,
            )
        )
        unit_text = textual_fields["unit"].casefold()
        if not backend_only and re.search(
            r"\b(?:frontend|browser|interfaz|interface|client-side|spa)\b",
            unit_text,
        ):
            triggers.append(f"{task_id}:unit={task.get('Unit')}")
        profile_id = str(binding.get("profile_id", ""))
        if not backend_only and profile_id:
            try:
                bundle = load_profile_bundle(profile_id)
            except (FileNotFoundError, ValueError):
                bundle = None
            roles = {
                str(item.get("role", "")).casefold()
                for item in (bundle.profile.get("units", []) if bundle else [])
                if isinstance(item, dict)
            }
            if "frontend" in roles and "backend" not in roles:
                triggers.append(f"{task_id}:profile={profile_id}")
        inspected.append(task_id)

    if triggers:
        return {
            "gate_id": VISUAL_GATE_ID,
            "status": "applicable",
            "scope": "release" if release_scope else "task-slice",
            "task_ids": selected,
            "reason": "selected-task-interface-signals:"
            + ";".join(sorted(set(triggers))),
        }
    if release_scope and release_interface_applicable:
        return {
            "gate_id": VISUAL_GATE_ID,
            "status": "applicable",
            "scope": "release",
            "task_ids": selected,
            "reason": f"release-{release_id}-delivers-interface",
        }
    return {
        "gate_id": VISUAL_GATE_ID,
        "status": "not-applicable",
        "scope": "task-slice",
        "task_ids": selected,
        "reason": (
            "selected-tasks-have-no-ux-vis-frontend-browser-or-interface-unit-signals:"
            + ",".join(inspected)
        ),
    }


def evidence_profile_identity_errors(
    evidence: dict[str, Any],
    manifest: dict[str, Any],
    *,
    require_canonical_single: bool = False,
) -> list[str]:
    """Validate top-level, binding, lock and build identity as one contract.

    Evidence schema 1.2 remains readable when legacy top-level identity is null or
    absent, but only if the binding identity is otherwise exact and unambiguous.
    New single-binding evidence must use the canonical top-level pair.
    """

    errors: list[str] = []
    binding_ids = evidence.get("profile_bindings")
    if binding_ids is None and evidence.get("schema_version") in {None, "1.2"}:
        top_id = evidence.get("profile_id")
        top_version = evidence.get("profile_version")
        if not isinstance(top_id, str) or not top_id or not isinstance(top_version, str) or not top_version:
            return ["la evidencia 1.2 heredada necesita profile_id y profile_version"]
        matching = [
            item
            for item in manifest.get("technology", {}).get("profile_bindings", [])
            if isinstance(item, dict) and item.get("profile_id") == top_id
        ]
        if not matching and manifest.get("technology", {}).get("selected_profile") != top_id:
            return ["profile_id heredado no pertenece al contrato tecnológico"]
        return []
    if (
        not isinstance(binding_ids, list)
        or not binding_ids
        or not all(isinstance(item, str) and re.fullmatch(r"BIND-[0-9]{3}", item) for item in binding_ids)
        or len(set(binding_ids)) != len(binding_ids)
    ):
        return ["profile_bindings debe contener BIND-### únicos"]
    selected = set(binding_ids)
    manifest_bindings = {
        item.get("binding_id"): item
        for item in manifest.get("technology", {}).get("profile_bindings", [])
        if isinstance(item, dict) and item.get("binding_id")
    }
    if selected - set(manifest_bindings):
        errors.append("profile_bindings referencia bindings inexistentes")

    material = evidence.get("build_identity_material")
    if not isinstance(material, dict):
        return errors + ["build_identity_material es obligatorio"]
    material_bindings = material.get("profile_bindings")
    locks = evidence.get("profile_locks")
    material_locks = material.get("locks")
    if not isinstance(material_bindings, list):
        material_bindings = []
        errors.append("build_identity_material.profile_bindings debe ser una lista")
    if not isinstance(locks, list):
        locks = []
        errors.append("profile_locks debe ser una lista")
    if not isinstance(material_locks, list):
        material_locks = []
        errors.append("build_identity_material.locks debe ser una lista")

    def indexed(items: list[Any], label: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("binding_id"), str):
                errors.append(f"{label} contiene una entrada sin binding_id")
                continue
            binding_id = item["binding_id"]
            if binding_id in result:
                errors.append(f"{label} repite {binding_id}")
            result[binding_id] = item
        return result

    built = indexed(material_bindings, "build_identity_material.profile_bindings")
    declared_locks = indexed(locks, "profile_locks")
    built_locks = indexed(material_locks, "build_identity_material.locks")
    for label, values in (
        ("build_identity_material.profile_bindings", built),
        ("profile_locks", declared_locks),
        ("build_identity_material.locks", built_locks),
    ):
        if set(values) != selected:
            errors.append(f"{label} no coincide con profile_bindings")

    identities: dict[str, tuple[str, str]] = {}
    for binding_id in sorted(selected):
        manifest_binding = manifest_bindings.get(binding_id, {})
        built_binding = built.get(binding_id, {})
        declared_lock = declared_locks.get(binding_id, {})
        built_lock = built_locks.get(binding_id, {})
        profile_id = built_binding.get("profile_id")
        profile_version = built_binding.get("profile_version")
        if not isinstance(profile_id, str) or not profile_id:
            errors.append(f"{binding_id}: falta profile_id en build_identity_material")
            continue
        if not isinstance(profile_version, str) or not profile_version:
            errors.append(f"{binding_id}: falta profile_version en build_identity_material")
            continue
        identities[binding_id] = (profile_id, profile_version)
        if manifest_binding.get("profile_id") != profile_id:
            errors.append(f"{binding_id}: profile_id diverge del manifest")
        for label, lock in (("profile_locks", declared_lock), ("build_identity_material.locks", built_lock)):
            if lock.get("profile_id") != profile_id:
                errors.append(f"{binding_id}: {label} diverge del profile_id del binding")
            lock_version = lock.get("profile_version")
            if lock_version is None:
                if require_canonical_single:
                    errors.append(f"{binding_id}: {label} no declara profile_version")
            elif lock_version != profile_version:
                errors.append(f"{binding_id}: {label} diverge de profile_version")
        if declared_lock.get("sha256") != built_lock.get("sha256"):
            errors.append(f"{binding_id}: el digest del lock diverge del build")
        try:
            expected_version = load_profile_bundle(profile_id).profile.get("version")
        except (FileNotFoundError, ValueError):
            expected_version = None
        if expected_version is not None and profile_version != expected_version:
            errors.append(f"{binding_id}: profile_version diverge del perfil publicado")

    top_id = evidence.get("profile_id")
    top_version = evidence.get("profile_version")
    top_missing = top_id is None and top_version is None
    if (top_id is None) != (top_version is None):
        errors.append("profile_id y profile_version superiores deben aparecer juntos")
    elif len(selected) == 1:
        expected = identities.get(next(iter(selected)))
        if top_missing:
            if require_canonical_single:
                errors.append("una evidencia nueva de un binding requiere profile_id y profile_version superiores")
        elif expected is not None and (top_id, top_version) != expected:
            errors.append("profile_id/profile_version superiores divergen del binding seleccionado")
    elif not top_missing and (top_id, top_version) not in set(identities.values()):
        errors.append("la identidad superior heredada no pertenece a los bindings seleccionados")

    declared_build_id = evidence.get("build_id")
    if isinstance(declared_build_id, str) and declared_build_id.startswith("build-sha256:"):
        computed = "build-sha256:" + hashlib.sha256(_canonical_payload(material)).hexdigest()
        if declared_build_id != computed:
            errors.append("build_id no coincide con build_identity_material")
    return errors


def evidence_gate_applicability_errors(
    evidence: dict[str, Any], expected: dict[str, Any]
) -> list[str]:
    """Require one exact, deterministic applicability decision for the visual gate."""

    values = evidence.get("gate_applicability")
    if not isinstance(values, list):
        return ["gate_applicability debe ser una lista"]
    visual = [
        item
        for item in values
        if isinstance(item, dict) and item.get("gate_id") == VISUAL_GATE_ID
    ]
    if len(visual) != 1:
        return ["gate_applicability debe declarar exactamente una decisión visual"]
    if visual[0] != expected:
        return ["gate_applicability visual no coincide con el TASK slice"]
    checks = evidence.get("checks")
    visual_checks = [
        item
        for item in checks
        if isinstance(item, dict) and item.get("name") == "visual-browser-review"
    ] if isinstance(checks, list) else []
    classification = evidence.get("classification")
    if expected.get("status") == "applicable" and classification in {
        "verified",
        "verified-with-reservations",
    }:
        if len(visual_checks) != 1 or visual_checks[0].get("status") != "passed":
            return ["un TASK slice visual requiere exactamente una revisión ejecutada y passed"]
    if expected.get("status") == "not-applicable" and visual_checks:
        return ["un gate visual no aplicable no debe aparecer como check ejecutado o not-run"]
    return []
