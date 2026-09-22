"""Human feature authoring and explicit identity reconciliation; never infer feature boundaries."""
from __future__ import annotations

import json
import posixpath
import re
import uuid
from v2_contract import (ContractError, DOCS, BLOCK, OPERATIONAL, canonical, fingerprint, make_element, render_document, render_block, load)
from v2_authoring import author, commit, history_changes
from v2_storage import preview, apply

SECTIONS = ("Finalidad", "Alcance", "Comportamiento", "Reglas y excepciones", "Aceptación", "Relaciones", "Evolución")


def feature_request(model, request):
    identifier, title = request.get("id", ""), request.get("title", "")
    if not re.fullmatch(r"FTR-\d{3,}", identifier) or identifier in model.elements or not title.strip():
        raise ContractError("New, unoccupied feature alias and descriptive title required")
    sections = request.get("sections", {})
    if any(not isinstance(sections.get(k), str) or not sections[k].strip() for k in SECTIONS):
        raise ContractError("Feature needs purpose, scope, behavior, exceptions, acceptance, relations and evolution")
    slug = request.get("slug", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ContractError("Provide a stable lowercase folder slug")
    relative = DOCS + "/02-specification/features/" + identifier + "-" + slug + "/specification.md"
    # Same short alias in independent clones must not imply the same identity.
    # A supplied UUID is preferable; otherwise bind only the initial creation intent.
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, model.manifest["project_id"] + ":" + fingerprint(request))
    body = "\n\n".join("### " + key + "\n\n" + sections[key] for key in SECTIONS)
    feature = make_element(identifier, "feature", title, body, uid=request.get("uid", str(uuid.uuid5(namespace, identifier))),
                           relations=request.get("relations", {}), state="draft", nature="proposal")
    elements = [feature]
    for value in request.get("obligations", []):
        if value["kind"] not in {"requirement", "acceptance", "rule", "test"} or value["id"] in model.elements:
            raise ContractError("Feature obligations must be new requirement/acceptance/rule/test identities")
        elements.append(make_element(value["id"], value["kind"], value["title"], value["body"],
                                     uid=str(uuid.uuid5(namespace, value["id"])), relations=value.get("relations", {})))
    # Explicit typed relations are also human-navigable; no reverse source to maintain.
    locations = {i: e.path for i, e in model.elements.items()}
    locations.update({e["meta"]["id"]: relative for e in elements})
    for element in elements:
        for relation, targets in element["meta"]["relations"].items():
            for target in targets:
                if target not in locations:
                    raise ContractError("Relation target not documented: " + target)
                link = posixpath.relpath(locations[target], posixpath.dirname(relative)) + "#" + target.lower()
                element["body"] += f"\n\n{relation}: [{target}](<{link}>)."
    text = render_document("feature", title, elements).decode()
    return {"documents": [{"path": relative, "text": text}]}


def create(model, request, *, authorized_hash=None):
    value = feature_request(model, request)
    return commit(model, value, authorized_hash) if authorized_hash else author(model, value)[0]


def task_requirements(model, task):
    """Coverage is explicit or traced from acceptance, never inherited from a feature."""
    covered = task.targets("requirements")
    accepted = task.targets("acceptance")
    for requirement in model.by_kind("requirement"):
        obligations = requirement.targets("acceptance")
        if obligations and obligations <= accepted:
            covered.add(requirement.id)
    return covered


def decomposition(model, plan_id):
    plan = model.elements.get(plan_id)
    if not plan or plan.kind != "plan":
        raise ContractError("Select a documented PLAN")
    requested = plan.targets("requirements")
    rows, blockers, covered = [], [], set()
    tasks = [t for t in model.by_kind("task") if plan_id in t.targets("plan") and t.meta["state"] != "cancelled"]
    for task in tasks:
        primary = [i for i in task.targets("implements") if model.elements[i].kind == "feature"]
        contributors = [i for i in task.targets("contributes_to") if model.elements[i].kind == "feature"]
        if len(primary) != 1:
            blockers.append("TASK must identify one primary feature: " + task.id)
        obligations = task_requirements(model, task)
        covered |= obligations
        rows.append({"task": task.id, "primary": primary, "contributors": contributors,
                     "requirements": sorted(obligations), "source": task.source()})
    missing, extra = sorted(requested - covered), sorted(covered - requested)
    if model.manifest["method_version"] == "2.1.0":
        from v2_change_control import assess_plan
        analysis = assess_plan(model, plan_id)
        blockers.extend(analysis["blockers"])
        missing = sorted(set(missing) | set(analysis["missing"]))
        extra = sorted(set(extra) | set(analysis["extra"]))
    return {"status": "covered" if not missing and not extra and not blockers else "incomplete",
            "plan": plan_id, "tasks": rows, "missing": missing, "extra": extra, "blockers": blockers, "writes": []}


def rename_aliases(model, request, *, authorized_hash=None):
    """Explicit collision repair in the incoming clone. UID/history remain stable."""
    mapping = request.get("mapping", {})
    if not mapping or not request.get("reason") or not request.get("actor"):
        raise ContractError("Collision repair requires explicit alias map, actor and reason")
    if len(set(mapping.values())) != len(mapping) or any(old not in model.elements or new in model.elements
            or not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z]+)*-\d{3,}", new) for old, new in mapping.items()):
        raise ContractError("Alias repair requires unused, unique target aliases")
    _, changes = history_changes(model)
    if any(e.kind in OPERATIONAL and (e.id in mapping or e.targets() & set(mapping)) for e in model.elements.values()):
        raise ContractError("Published operational identities cannot be rewritten; repair unpublished incoming aliases before merging")
    def transform(value):
        if isinstance(value, list):
            return [transform(v) for v in value]
        if isinstance(value, dict):
            return {k: transform(v) for k, v in value.items()}
        return mapping.get(value, value) if isinstance(value, str) else value
    for path, text in model.documents.items():
        def replace(match):
            meta = json.loads(match[1])
            if meta["kind"] in OPERATIONAL:
                return match[0]
            old = meta["id"]
            updated = transform(meta)
            if old in mapping:
                updated["aliases"] = [*meta.get("aliases", []), {"id": old, "reason": request["reason"], "actor": request["actor"]}]
            body = match[2]
            for source, target in mapping.items():
                body = re.sub(r"\b" + re.escape(source) + r"\b", target, body)
                body = body.replace('id="' + source.lower() + '"', 'id="' + target.lower() + '"')
                body = body.replace("#" + source.lower(), "#" + target.lower())
            if updated != meta or body != match[2]:
                updated["revision"] = meta["revision"] + 1
            return render_block(updated, body).rstrip()
        updated = BLOCK.sub(replace, text)
        if updated != text:
            changes[path] = updated.encode()
    # Renaming invalidates contract-bound AUTH. Never forge replacement authority.
    from v2_authoring import edit_elements
    for auth in model.by_kind("authorization"):
        if auth.meta["state"] == "active":
            path = auth.path
            text = changes.get(path, model.documents[path].encode()).decode()
            changes[path] = text.replace('"state":"active"', '"state":"revoked"').encode()
    result = preview(model.root, changes, sources=model.hashes, operation="resolve-alias-collision")
    return apply(model.root, changes, result, authorized_hash, validator=lambda: load(model.root).require_valid()) if authorized_hash else result
