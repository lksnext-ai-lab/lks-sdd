"""Typed quality obligations: labels and successful process exits are not integration proof."""
from __future__ import annotations

from v2_contract import execution_context

SCOPES = {"component", "contract", "composition", "user-flow", "persistence", "visual"}


def obligations(model, tasks):
    context = execution_context(model, tasks)
    entries = [model.elements[e["meta"]["id"]] for e in context["elements"]]
    scopes, gates, interfaces, blockers = set(), set(), set(), []
    human = False
    for entry in entries:
        scopes.update(entry.meta.get("evidence_scopes", []))
        gates.update(entry.meta.get("gates", []))
        interfaces.update(entry.targets("interfaces"))
        human |= bool(entry.meta.get("human_review_required")) or entry.kind == "visual" or entry.meta.get("risk") in {"high", "critical"}
        if entry.kind == "interface":
            policy = interface_obligation(entry)
            gates.add(policy["gate_id"])
            scopes.update(policy["required_evidence_scopes"])
            if not entry.meta.get("protocol") or not entry.meta.get("contract") or not entry.meta.get("operations") or not entry.targets("bindings"):
                blockers.append("Interface needs protocol, exact contract, operations and participant bindings: " + entry.id)
            interfaces.add(entry.id)
            if policy["gate_id"] not in entry.meta.get("gates", []):
                blockers.append("Interface must name its protocol-derived gate: " + entry.id + ": " + policy["gate_id"])
            scopes.add("contract")
            if entry.meta.get("cross_component", True):
                scopes.add("composition")
            if entry.meta.get("persistent_mutation"):
                scopes.add("persistence")
            if not entry.meta.get("evidence_scopes") or not entry.meta.get("gates"):
                blockers.append("Interface requires explicit typed verification obligations: " + entry.id)
        if entry.kind == "visual":
            scopes.add("visual")
            if not entry.meta.get("viewports") or not entry.meta.get("states") or not entry.meta.get("baseline_assets"):
                blockers.append("Visual obligation requires baseline, states and viewports: " + entry.id)
    ux = [e for e in entries if e.kind == "applicability" and e.meta.get("domain") == "ux"]
    if any(e.meta.get("applicability") == "applicable" for e in ux):
        human = True
        scopes.update({"visual", "user-flow"})
        if not any(e.kind == "visual" for e in entries):
            blockers.append("Applicable UX requires a visual contract, not only a prototype or generic requirement")
    if scopes - SCOPES:
        blockers.append("Unknown evidence scope: " + ", ".join(sorted(scopes - SCOPES)))
    return {"scopes": sorted(scopes), "gates": sorted(gates), "interfaces": sorted(interfaces),
            "human_review_required": human, "blockers": blockers}


def observation_errors(observation, entry):
    from observation_contract import gate_observation_errors, persistence_errors
    from evidence_safety import evidence_safety_errors
    errors = evidence_safety_errors(observation)
    if observation.get("gate_id") != entry["gate_id"]:
        errors.append("Observation gate identity mismatch")
    if observation.get("status") != "passed":
        return errors
    errors.extend(gate_observation_errors(observation))
    scopes = set(observation.get("scopes", []))
    facts = observation.get("observations", {})
    if not isinstance(facts, dict):
        return errors + ["Structured observations must be an object"]
    if "persistence" in scopes:
        errors.extend(persistence_errors(facts))
    if scopes & {"composition", "user-flow", "persistence"}:
        if facts.get("domain_mocks") is not False or observation.get("mocks"):
            errors.append("Real integration must explicitly exclude domain mocks")
    if "visual" in scopes and not facts.get("screenshots"):
        errors.append("Visual evidence needs actual captures")
    if not observation.get("artifacts"):
        errors.append("Evidence needs immutable artifacts, not a pass label")
    if "gate" in entry:
        gate = entry["gate"]
        if scopes != set(gate["scopes"]) or set(observation.get("interfaces", [])) != set(gate["interfaces"]):
            errors.append("Observed scopes/interfaces differ from approved gate")
        if not facts:
            errors.append("Consumer observer needs structured runtime facts")
    from integration_contract import http_observation_errors, resource_observation_errors
    for obligation in entry.get("interface_obligations", []):
        if obligation["interface_id"] not in observation.get("interfaces", []):
            errors.append("Observation does not identify its interface")
        if obligation["observer"] in {"http", "browser-http"}:
            errors.extend(http_observation_errors(facts, obligation))
        else:
            errors.extend(resource_observation_errors(facts, obligation))
    return errors


def interface_obligation(entry):
    from integration_contract import interface_policy
    value = entry.meta
    adapted = {"Protocol": value.get("protocol", ""), "Contract": value.get("contract", ""),
               "Operations": ",".join(value.get("operations", [])), "Required evidence": ",".join(value.get("evidence_scopes", []))}
    policy = interface_policy(adapted)
    return {**policy, "interface_id": entry.id, "operations": value.get("operations", []),
            "required_evidence_scopes": policy["required_scopes"]}


def review_satisfied(model, tasks, evidence):
    """A declared reviewer is not authentication; bind the decision to exact evidence."""
    return any(e.meta.get("category") == "result-review" and e.meta["state"] == "approved"
               and e.meta.get("actor") and e.meta.get("evidence_id") == evidence["evidence_id"]
               and e.meta.get("evidence_sha256") == evidence["integrity_sha256"]
               and set(tasks) <= e.targets("verifies") for e in model.by_kind("receipt"))


def visual_coverage_errors(model, tasks, observations):
    entries = execution_context(model, tasks)["elements"]
    captures = [(c, o) for o in observations if o["status"] == "passed"
                for c in o.get("observations", {}).get("screenshots", []) if isinstance(c, dict)]
    errors = []
    for value in entries:
        visual = model.elements[value["meta"]["id"]]
        if visual.kind != "visual":
            continue
        for viewport in visual.meta.get("viewports", []):
            for state in visual.meta.get("states", []):
                found = any(c.get("visual_id") == visual.id and c.get("viewport") == viewport and c.get("state") == state
                    and visual.targets("acceptance") <= set(c.get("acceptance_ids", []))
                    and any(c.get("path") == a.get("path") and c.get("sha256") == a.get("sha256")
                            for a in observation.get("artifacts", [])) for c, observation in captures)
                if not found:
                    errors.append(f"{visual.id}: missing immutable capture for {viewport}/{state} and its acceptance scope")
    return errors
