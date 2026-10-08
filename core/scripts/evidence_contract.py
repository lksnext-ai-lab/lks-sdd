#!/usr/bin/env python3
"""Shared verification-evidence identity and TASK-slice applicability rules."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

from contract_engine import expand_reference_ids
from delivery_engine import EVIDENCE_SCOPES
from evidence_safety import evidence_safety_errors
from integration_contract import (
    INTEGRATION_GATES, BROWSER_GATE, HTTP_GATE, POSTGRES_GATE, MIGRATION_GATE,
    interface_policy, http_observation_errors,
)


VISUAL_GATE_ID = "GATE-VISUAL-BROWSER-REVIEW"
FULLSTACK_GATE_ID = "GATE-BROWSER-FULLSTACK-E2E"
REQUIREMENT_RE = re.compile(r"\b(?:FR|NFR|TR|BR)-[0-9]{3}\b")


def _canonical_payload(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def selected_task_requirements(task_ids: Iterable[str], delivery: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for task_id in task_ids:
        details = delivery.get("task_details", {}).get(task_id, {})
        rows = details.get("definition", [])
        if len(rows) == 1:
            result.update(
                expand_reference_ids(
                    rows[0].get("Requirements", ""), {"FR", "NFR", "TR", "BR"}
                )
            )
    return result




def _release_scope(task_ids: list[str], delivery: dict[str, Any]) -> tuple[bool, str | None]:
    releases = {delivery.get("tasks", {}).get(task_id, {}).get("Release") for task_id in task_ids}
    releases.discard(None)
    if len(releases) != 1:
        return False, None
    release_id = str(next(iter(releases)))
    release_tasks = {
        candidate_id for candidate_id, row in delivery.get("tasks", {}).items()
        if row.get("Release") == release_id
    }
    return bool(release_tasks) and set(task_ids) == release_tasks, release_id


def visual_gate_applicability(
    task_ids: Iterable[str], delivery: dict[str, Any], *, release_interface_applicable: bool = False
) -> dict[str, Any]:
    selected = sorted(set(task_ids))
    release_scope, release_id = _release_scope(selected, delivery)
    triggers: list[str] = []
    inspected: list[str] = []
    for task_id in selected:
        task = delivery.get("tasks", {}).get(task_id, {})
        details = delivery.get("task_details", {}).get(task_id, {})
        rows = details.get("definition", [])
        definition = rows[0] if len(rows) == 1 else {}
        unit = delivery.get("units", {}).get(task.get("Unit"), {})
        fields = {
            "in-scope": definition.get("In scope", ""),
            "out-of-scope": definition.get("Out of scope", ""),
            "requirements": definition.get("Requirements", ""),
            "acceptance": definition.get("Acceptance", ""),
            "capabilities": definition.get("Required capabilities", ""),
            "gates": definition.get("Technical gates", ""),
            "unit": " ".join(str(unit.get(key, "")) for key in ("Component", "Responsibility", "Runtime boundary", "Interfaces")),
        }
        joined = " ".join(fields.values())
        refs = sorted(set(re.findall(r"\b(?:UX|VIS)-[0-9]{3}\b", joined)))
        if refs:
            triggers.append(f"{task_id}:refs={','.join(refs)}")
        contract_ids = re.findall(
            r"\b(?:CAP|GATE)-[A-Z0-9-]{3,80}\b",
            " ".join([fields["capabilities"], fields["gates"]]),
        )
        direct_frontend = sorted({item for item in contract_ids if {"FRONTEND", "BROWSER", "UI"} & set(item.split("-"))})
        if direct_frontend:
            triggers.append(f"{task_id}:frontend-contract={','.join(direct_frontend)}")
        in_scope = fields["in-scope"].casefold()
        backend_only = bool(re.search(r"\b(?:backend|api|worker|consumer|processor|database)\b", in_scope)) and not bool(
            re.search(r"\b(?:frontend|browser|interfaz|interface|ui|spa|screen)\b", in_scope)
        )
        if not backend_only and re.search(r"\b(?:frontend|browser|interfaz|interface|client-side|spa)\b", fields["unit"].casefold()):
            triggers.append(f"{task_id}:unit={task.get('Unit')}")
        inspected.append(task_id)
    if triggers:
        return {
            "gate_id": VISUAL_GATE_ID,
            "status": "applicable",
            "scope": "release" if release_scope else "task-slice",
            "task_ids": selected,
            "reason": "selected-task-interface-signals:" + ";".join(sorted(set(triggers))),
        }
    if release_scope and release_interface_applicable:
        return {
            "gate_id": VISUAL_GATE_ID, "status": "applicable", "scope": "release",
            "task_ids": selected, "reason": f"release-{release_id}-delivers-interface",
        }
    return {
        "gate_id": VISUAL_GATE_ID,
        "status": "not-applicable",
        "scope": "task-slice",
        "task_ids": selected,
        "reason": "selected-tasks-have-no-ux-vis-frontend-browser-or-interface-unit-signals:" + ",".join(inspected),
    }


def integration_gate_applicability(
    task_ids: Iterable[str], delivery: dict[str, Any]
) -> list[dict[str, Any]]:
    """Resolve typed cross-unit obligations for an exact TASK slice.

    Only canonical INT rows and the task's structured integration table are
    considered. Free-text Integration points never enables or satisfies an
    integration gate.
    """

    selected = sorted(set(task_ids))
    result: list[dict[str, Any]] = []
    for interface_id, interface in sorted(delivery.get("interfaces", {}).items()):
        if interface.get("State", "").strip().casefold() != "confirmed":
            continue
        verification_tasks = expand_reference_ids(
            interface.get("Verification task", ""), {"TASK"}
        )
        if not set(verification_tasks) & set(selected):
            continue
        scopes = sorted(
            {
                item.strip().casefold()
                for item in interface.get("Required evidence", "").split(",")
                if item.strip()
            }
        )
        units = sorted(
            expand_reference_ids(interface.get("Consumer unit", ""), {"UNIT"})
            | expand_reference_ids(interface.get("Producer unit", ""), {"UNIT"})
        )
        bindings = sorted(
            expand_reference_ids(interface.get("Bindings", ""), {"BIND"})
        )
        policy = interface_policy(interface)
        result.append(
            {
                "gate_id": policy["gate_id"],
                "status": "applicable",
                "scope": "interface",
                "interface_id": interface_id,
                "task_ids": selected,
                "unit_ids": units,
                "binding_ids": bindings,
                "required_evidence_scopes": sorted(set(scopes) | set(policy["required_scopes"])),
                "operations": sorted(
                    {
                        item.strip().casefold()
                        for item in interface.get("Operations", "").split(",")
                        if item.strip()
                    }
                ),
                "exact_composition": interface.get("Exact composition"),
                "observer": policy["observer"],
                "contract": policy["contract"],
                "http_operations": policy["http_operations"],
                "reason": "confirmed-cross-unit-interface",
            }
        )
    if result:
        return result
    return [
        {
            "gate_id": FULLSTACK_GATE_ID,
            "status": "not-applicable",
            "scope": "task-slice",
            "task_ids": selected,
            "reason": "selected-tasks-own-no-confirmed-cross-unit-interface",
        }
    ]


def _check_scopes(check: dict[str, Any]) -> set[str]:
    scopes = check.get("evidence_scopes")
    if isinstance(scopes, list):
        return {str(item).casefold() for item in scopes if isinstance(item, str)}
    scope = check.get("evidence_scope")
    if isinstance(scope, str):
        return {scope.casefold()}
    return {"component"}


def integration_evidence_errors(
    evidence: dict[str, Any], expected: list[dict[str, Any]]
) -> list[str]:
    """Fail closed when lower-scope or mocked evidence claims integration."""

    applicable = [item for item in expected if item.get("status") == "applicable"]
    if not applicable:
        return []
    errors: list[str] = evidence_safety_errors(evidence)
    checks = [
        item for item in evidence.get("checks", []) if isinstance(item, dict)
    ]
    for check in checks:
        scopes = _check_scopes(check)
        if not scopes <= EVIDENCE_SCOPES:
            errors.append(f"{check.get('name', 'check')}: evidence_scopes inválidos")
    for obligation in applicable:
        interface_id = str(obligation["interface_id"])
        material = evidence.get("build_identity_material", {})
        compositions = material.get("compositions", []) if isinstance(material, dict) else []
        candidates = [item for item in compositions if isinstance(item, dict) and item.get("interface_id") == interface_id]
        if candidates:
            composition = candidates[-1].get("material", {})
            if not isinstance(composition, dict):
                errors.append(f"{interface_id}: material de composición local inválido")
            else:
                serialized = (json.dumps(composition, sort_keys=True, indent=2) + "\n").encode()
                if candidates[-1].get("sha256") != hashlib.sha256(serialized).hexdigest():
                    errors.append(f"{interface_id}: digest de composición local incorrecto")
                participants = composition.get("participants", [])
                if not isinstance(participants, list) or {item.get("binding_id") for item in participants if isinstance(item, dict)} != set(obligation.get("binding_ids", [])):
                    errors.append(f"{interface_id}: bindings de composición local no coinciden")

        required = set(obligation.get("required_evidence_scopes", []))
        matching = [
            check
            for check in checks
            if interface_id in check.get("interface_ids", [])
            and check.get("status") == "passed"
        ]
        demonstrated: set[str] = set()
        for check in matching:
            scopes = _check_scopes(check)
            mocked = check.get("mocks", [])
            domain_mocks = [
                item
                for item in mocked
                if isinstance(item, dict)
                and item.get("kind") != "identity-provider"
            ] if isinstance(mocked, list) else []
            if domain_mocks and scopes & {"composition", "user-flow", "persistence"}:
                errors.append(
                    f"{interface_id}: un mock funcional no acredita "
                    "composition, user-flow ni persistence"
                )
                continue
            demonstrated.update(scopes)
        missing = sorted(required - demonstrated)
        if missing:
            errors.append(
                f"{interface_id}: evidencia insuficiente; faltan scopes "
                + ", ".join(missing)
            )
        fullstack = [
            check
            for check in matching
            if check.get("gate_id") == obligation.get("gate_id")
        ]
        if not fullstack:
            errors.append(
                f"{interface_id}: falta {obligation.get('gate_id')} ejecutado y passed"
            )
            continue
        for check in fullstack:
            observations = check.get("observations")
            browser_required = obligation.get("gate_id") == BROWSER_GATE
            http_required = obligation.get("gate_id") in {BROWSER_GATE, HTTP_GATE}
            required_observations = {"runtime_units"}
            if http_required:
                required_observations.add("requests")
            if browser_required:
                required_observations.update({"browser", "viewport", "reload", "screenshots", "console_errors"})
            if "persistence" in required:
                required_observations.update({"mutation", "read_back", "persistence"})
            if not isinstance(observations, dict) or not required_observations <= set(observations):
                errors.append(
                    f"{interface_id}: el gate full-stack no contiene observaciones estructuradas completas"
                )
                continue
            if http_required:
                errors.extend(f"{interface_id}: {message}" for message in http_observation_errors(observations, obligation))
            else:
                from integration_contract import resource_observation_errors
                errors.extend(f"{interface_id}: {message}" for message in resource_observation_errors(observations, obligation))
            if "persistence" in required:
                from observation_contract import persistence_errors
                errors.extend(f"{interface_id}: {message}" for message in persistence_errors(observations))
            if (browser_required and observations.get("reload") is not True) or (
                "persistence" in required and (observations.get("persistence") is not True or not observations.get("read_back"))
            ):
                errors.append(
                    f"{interface_id}: no se confirmó recarga y persistencia"
                )
            if observations.get("console_errors") not in ([], None):
                errors.append(
                    f"{interface_id}: existen errores relevantes de consola"
                )
    return list(dict.fromkeys(errors))


def evidence_binding_identity_errors(
    evidence: dict[str, Any], manifest: dict[str, Any], *, require_canonical_single: bool = False
) -> list[str]:
    """Validate only local generic binding identifiers in historical evidence."""
    bindings = {item.get("binding_id") for item in manifest.get("bindings", []) if isinstance(item, dict)}
    material = evidence.get("build_identity_material", {})
    declared = material.get("bindings", []) if isinstance(material, dict) else []
    if not isinstance(declared, list):
        return ["build_identity_material.bindings debe ser una lista"]
    unknown = sorted({item.get("binding_id") for item in declared if isinstance(item, dict) and item.get("binding_id")} - bindings)
    return ["binding no declarado: " + item for item in unknown]

def evidence_gate_applicability_errors(
    evidence: dict[str, Any], expected: dict[str, Any] | list[dict[str, Any]]
) -> list[str]:
    expected_values = expected if isinstance(expected, list) else [expected]
    values = evidence.get("gate_applicability")
    if not isinstance(values, list):
        return ["gate_applicability debe ser una lista"]
    expected_visual = next(
        (item for item in expected_values if item.get("gate_id") == VISUAL_GATE_ID),
        None,
    )
    expected_integrations = [item for item in expected_values if item.get("gate_id") in INTEGRATION_GATES]
    visual = [item for item in values if isinstance(item, dict) and item.get("gate_id") == VISUAL_GATE_ID]
    if len(visual) != 1:
        return ["gate_applicability debe declarar exactamente una decisión visual"]
    if expected_visual is None or visual[0] != expected_visual:
        return ["gate_applicability visual no coincide con el TASK slice"]
    checks = evidence.get("checks")
    visual_checks = [
        item for item in checks
        if isinstance(item, dict) and item.get("name") == "visual-browser-review"
    ] if isinstance(checks, list) else []
    classification = evidence.get("classification")
    if expected_visual.get("status") == "applicable" and classification in {"verified", "verified-with-reservations"}:
        if len(visual_checks) != 1 or visual_checks[0].get("status") != "passed":
            return ["un TASK slice visual requiere exactamente una revisión ejecutada y passed"]
    if expected_visual.get("status") == "not-applicable" and visual_checks:
        return ["un gate visual no aplicable no debe aparecer como check ejecutado o not-run"]
    observed_integrations = [
        item for item in values if isinstance(item, dict) and item.get("gate_id") in INTEGRATION_GATES
    ]
    if observed_integrations != expected_integrations:
        return ["gate_applicability de integración no coincide con el TASK slice"]
    return integration_evidence_errors(evidence, expected_integrations)
