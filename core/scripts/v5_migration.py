"""Explicit full conversion with bounded ownership and a resumable, irreversible cutover.

The preview is temporary operational data. Only capabilities, tasks and plans
remain as durable method documents. No backup or rollback is created; staging is removed after completion.
"""
from __future__ import annotations

import json
import os
import posixpath
from pathlib import Path
import re
import subprocess
import time
import unicodedata

from v5_core import (Conflict, FORMAT, DELIVERY, atomic_write, current, digest, document, filesystem_root,
                     encode, file_digest, locked, parse, path_at, read, scope_digest,
                     task_path, unit_path, validate)
from v5_legacy import Reader, EVENTS, ARCHIVE, business_data, paths

WORK = ".sdd-work/migration"
JOURNAL = ".sdd-work/migration.json"
REPORT = "docs/informe-conversion-sdd-v5.md"
MARKER = re.compile(r"<!-- LKS-SDD:BEGIN -->.*?<!-- LKS-SDD:END -->", re.S | re.I)
OPERATING = {"task", "plan", "proposal", "request", "change", "increment", "release"}
RETIRED = {"retired", "cancelled", "canceled", "superseded", "obsolete"}
CONTROL_ONLY = {"execution", "checkpoint", "receipt", "migration", "assignment", "handoff", "analysis"}


def slug(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80]
    return result or "contenido"


def git(root, *args, binary=False):
    result = subprocess.run(["git", "-c", "core.longpaths=true", "-C", str(root), *args],
                            capture_output=True, check=True)
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def refs(element):
    return {x for v in element.relations.values() if isinstance(v, list) for x in v if isinstance(x, str)}


def compact_inventories(value):
    """Only byte inventories are compacted; business lists remain literal."""
    if isinstance(value, list):
        if value and all(isinstance(v, dict) and isinstance(v.get("path"), str) and
                isinstance(v.get("sha256"), str) and set(v) <= {"path", "sha256", "bytes", "size", "exists", "kind"}
                for v in value):
            return None  # No value after conversion; no receipt for a discarded receipt.
        return [compact_inventories(v) for v in value]
    if isinstance(value, dict):
        from v5_legacy import TECHNICAL
        return {k: result for k, v in value.items() if k not in TECHNICAL and k.removesuffix("_ref") not in TECHNICAL
                if (result := compact_inventories(v)) is not None}
    return value


def operational_policy(elements, resolution):
    """Translate known delivery/quality controls; unknown controls stay explicit."""
    if resolution is not None:
        if not isinstance(resolution, dict):
            raise ValueError("Policy resolution must be an explicit object")
        return resolution
    result, pending = {}, []
    scopes, unconditional = {}, set()
    for e in elements.values():
        if e.kind not in {"policy", "project"}:
            continue
        data = e.data.get("policy", e.data) if e.kind == "project" else e.data
        if not isinstance(data, dict):
            continue  # The project may reference a separately converted policy UID.
        for key in ("required_checks", "deployment_checks"):
            if key in data:
                result[key] = sorted(set(result.get(key, []) + data[key]))
                if key == "required_checks": unconditional.update(data[key])
        for name, control in data.get("controls", {}).items():
            if isinstance(control, dict) and control.get("mode") == "required":
                result["required_checks"] = sorted(set(result.get("required_checks", []) + [name]))
                scope = control.get("scope")
                if isinstance(scope, list) and scope and all(isinstance(p, str) and p for p in scope):
                    scopes[name] = sorted(set(scopes.get(name, []) + scope))
                else:
                    unconditional.add(name)
            elif not isinstance(control, dict) or control.get("mode") not in {"optional", "not-used", "disabled"}:
                pending.append("Conciliar control " + name + " de " + e.id)
    if pending:
        result["migration_pending"] = sorted(set(pending))
    if any(name not in unconditional for name in scopes):
        result["check_scopes"] = {name: scope for name, scope in scopes.items() if name not in unconditional}
    return result


def task_controls(origin, elements, resolution, targets=None):
    """Extract explicit criteria/check definitions without turning old passes into new ones."""
    resolution = resolution or {}
    related = [origin] if origin else []
    # A task does not acquire every acceptance criterion in the transitive product
    # graph. Only its explicit criteria and directly delegated plan/acceptance apply.
    related.extend(elements[uid] for uid in sorted(refs(origin) if origin else [])
                   if uid in elements and elements[uid].kind in {"acceptance", "plan"})
    criteria, checks = {}, {}
    for e in related:
        if e.kind == "acceptance":
            destination = (targets or {}).get(e.uid)
            criteria[e.id] = ("[" + e.id + "](/" + destination + "#" + slug(e.id) + ")" if destination else
                              e.data.get("statement") or e.body.strip())
        if e.kind in {"task", "plan", "request", "proposal"}:
            raw = e.data.get("criteria", e.data.get("acceptance_criteria", e.data.get("acceptance", {})))
            if isinstance(raw, list):
                raw = {"C" + str(i): text for i, text in enumerate(raw, 1)}
            criterion_ids = {}
            if isinstance(raw, dict):
                criterion_ids = {k: (k if e == origin else e.id + '-' + k) for k, v in raw.items()
                                 if isinstance(k, str) and isinstance(v, str) and v.strip()}
                criteria.update({criterion_ids[k]: raw[k] for k in criterion_ids})
            for name, definition in e.data.get("checks", {}).items():
                if isinstance(definition, dict) and definition.get("inputs") and definition.get("environment") and (definition.get("argv") or definition.get("provider")):
                    definition = {**definition, "criteria": [criterion_ids.get(k, k) for k in definition.get('criteria', [])]}
                    if name in checks and checks[name] != definition:
                        name = e.id + '-' + name
                    checks[name] = definition
    criteria.update(resolution.get("criteria", {}))
    checks.update(resolution.get("checks", {}))
    return criteria, checks


def convert(reader, overrides=None, resolutions=None):
    """Preserve source content; explicit mappings can refine capability boundaries.

    Existing feature boundaries are used first. Unknown shared material remains
    in a named shared capability, never silently classified as accepted policy.
    """
    overrides = overrides or {}
    resolutions = resolutions or {}
    # Retain useful product knowledge and decisions, not all method execution history.
    elements = {uid: e for uid, e in reader.elements.items()
                if e.meta.get("state") not in RETIRED and e.kind not in CONTROL_ONLY
                and not (e.kind == "evidence" and not e.data.get("singular"))}
    approved = reader.approvals()
    policy = operational_policy(elements, resolutions.get("policy"))
    groups, target, source_targets = {}, {}, {}
    for uid, element in elements.items():
        feature = re.search(r"/features/([^/]+)/", element.source)
        if uid in overrides:
            groups[uid] = slug(overrides[uid])
        elif feature:
            groups[uid] = slug(feature[1])
    # Explicit functional relations attach details to capabilities. Ambiguous
    # cross-capability elements become shared instead of duplicated.
    for _ in range(4):
        additions = {}
        for uid, element in elements.items():
            if uid in groups or element.kind in EVENTS | OPERATING:
                continue
            linked = {groups[x] for x in refs(element) if x in groups}
            if len(linked) == 1:
                additions[uid] = next(iter(linked))
        if not additions:
            break
        groups.update(additions)
    unit_sections, task_sections, plan_sections, task_units = {}, {}, {}, {}
    task_ids = {uid: slug(e.id) for uid, e in elements.items() if e.kind == "task"}
    if len(set(task_ids.values())) != len(task_ids):
        raise ValueError("Task identifier collision")
    owners = {}
    for uid, e in elements.items():
        linked = refs(e)
        owners[uid] = {task_ids[x] for x in linked if x in task_ids}
    for uid, e in elements.items():
        if uid in task_ids:
            for related in refs(e):
                owners.setdefault(related, set()).add(task_ids[uid])
    # One parent task for each genuinely shared plan; no duplicated evolving plans.
    parents = {uid: "lote-" + slug(elements[uid].id) for uid, own in owners.items()
               if len(own) > 1 and elements[uid].kind == "plan"}
    parent_of = {}
    for uid, parent in parents.items():
        for child in sorted(owners[uid]):
            if child in parent_of and parent_of[child] != parent:
                raise ValueError("Task belongs to contradictory plans: " + child)
            parent_of[child] = parent
    work_ids = {**task_ids, **parents}
    # Requests, proposals and release records are knowledge, not new assignments.
    # Only actual source tasks and shared execution plans create task/plan pairs.
    if len(set(work_ids.values())) != len(work_ids):
        raise ValueError("Work identifier collision")
    for uid, e in elements.items():
        if uid in work_ids:
            name = task_path(work_ids[uid], "tarea" if e.kind != "plan" else "plan")
        elif e.kind in EVENTS | OPERATING:
            owning = sorted(owners[uid])
            if owning:
                name = task_path(owning[0], "plan")
            else:
                # Unassigned work records must not enter every task's policy/context.
                name = unit_path("antecedentes" if e.kind in OPERATING else "proyecto")
        else:
            group = groups.get(uid)
            if not group:
                group = ("proyecto" if e.kind in {"project", "policy", "member"} else
                         "reglas-compartidas" if e.kind in {"rule", "constraint", "applicability"} else
                         "arquitectura-compartida" if e.kind in {"technology", "binding", "interface", "environment"} else
                         "comportamiento-compartido")
            groups[uid] = group
            name = unit_path(group)
        target[uid] = name
        source_targets.setdefault(e.source, set()).add(name)
    all_task_ids = set(work_ids.values())
    for tid in all_task_ids:
        task_sections[tid], plan_sections[tid], task_units[tid] = [], [], set()
    for uid, e in elements.items():
        name = target[uid]
        # A technical receipt is not converted into a new mandatory document.
        # Preserve its human text and current decision provenance in the owner plan.
        data = business_data(e.data)
        if uid in work_ids and e.kind in {"task", "plan", "request", "proposal"}:
            # Remove only values actually normalized into operational metadata.
            selected = next((k for k in ("criteria", "acceptance_criteria", "acceptance") if k in e.data), None)
            raw_criteria = data.get(selected)
            values = raw_criteria.values() if isinstance(raw_criteria, dict) else raw_criteria
            if isinstance(raw_criteria, (dict, list)) and all(isinstance(v, str) and v.strip() for v in values):
                data.pop(selected, None)
            if isinstance(data.get("checks"), dict):
                data["checks"] = {k: v for k, v in data["checks"].items() if not
                    (isinstance(v, dict) and v.get("inputs") and v.get("environment") and (v.get("argv") or v.get("provider")))}
                if not data["checks"]:
                    data.pop("checks")
        if e.kind in EVENTS:
            data = {k: v for k, v in data.items() if k in {
                "outcome", "purpose", "actor", "decided_at", "reason", "statement", "status",
                "conclusion", "blocking_findings", "continuation", "health", "reconciliation_required",
                "next_step", "owner", "progress", "gates", "revokes", "historical_only"}}
        def materialize(value):
            if isinstance(value, dict):
                if value.get("format") == "lks-sdd-object/1":
                    raw = reader.payload(value)
                    try:
                        return json.loads(raw)
                    except (ValueError, UnicodeError):
                        raise ValueError("Business binary reference needs an explicit external artifact mapping: " + e.id)
                return {k: materialize(v) for k, v in value.items()}
            if isinstance(value, list):
                return [materialize(v) for v in value]
            return value
        data = compact_inventories(materialize(data))
        state = e.meta.get("state", "unknown")
        label = "Decisión vigente comprobada" if uid in approved else "Estado de origen: " + state
        links = sorted({target[x] for x in refs(e) if x in target and target[x] != name})
        section = (f'<a id="{slug(e.id)}"></a>\n\n## {e.id} · {e.meta.get("title", e.kind)}\n\n'
                   f'{label}.\n\n{e.body}\n')
        if data:
            section += "\nDatos conservados:\n\n```json\n" + encode(data) + "\n```\n"
        if links:
            section += "\nRelacionados: " + ", ".join(f"[{Path(p).stem}](/" + p + ")" for p in links) + ".\n"
        if name.startswith("docs/sdd/especificaciones/"):
            unit_sections.setdefault(Path(name).stem, []).append(section)
        else:
            tid = name.split("/")[-2]
            (task_sections if name.endswith("tarea.md") else plan_sections)[tid].append(section)
        for tid in owners[uid] | ({work_ids[uid]} if uid in work_ids else set()):
            if name.startswith("docs/sdd/especificaciones/"):
                task_units[tid].add(Path(name).stem)
            for related in refs(e):
                if related in groups:
                    task_units[tid].add(groups[related])
    # Preserve prose outside structured blocks exactly once, including decisions
    # not encoded as elements. Git history is not rewritten by conversion.
    for source, prose in reader.prose.items():
        source_elements = [e for e in reader.elements.values() if e.source == source]
        if source_elements and not any(e.uid in elements for e in source_elements):
            continue  # Do not retain headings/tables for retired control records.
        destinations = sorted(source_targets.get(source, []))
        name = destinations[0] if destinations else unit_path("contexto-compartido")
        source_targets.setdefault(source, set()).add(name)
        def compact_fence(match):
            try:
                value = json.loads(match[2])
            except ValueError:
                return match[0]
            return "```" + match[1] + "\n" + encode(compact_inventories(value)) + "\n```"
        prose = re.sub(r"```(lks-sdd-[\w-]+|json)\s*\n(.*?)\n```", compact_fence, prose, flags=re.S)
        section = "\n## Contexto conservado: " + Path(source).name + "\n\n" + prose + "\n"
        if name.startswith("docs/sdd/especificaciones/"):
            unit_sections.setdefault(Path(name).stem, []).append(section)
        else:
            (task_sections if name.endswith("tarea.md") else plan_sections)[name.split("/")[-2]].append(section)
    output = {}
    for unit, sections in sorted(unit_sections.items()):
        dependencies = sorted({groups[x] for uid, e in elements.items() if groups.get(uid) == unit
            for x in refs(e) if x in groups and groups[x] != unit})
        output[unit_path(unit)] = document({"format": FORMAT, "kind": "unit", "id": unit,
            "depends_on": dependencies, **({"policy": policy} if unit == "proyecto" else {})},
            "# " + unit + "\n\n" + "\n".join(dict.fromkeys(sections)))
    if policy and unit_path("proyecto") not in output:
        output[unit_path("proyecto")] = document({"format": FORMAT, "kind": "unit", "id": "proyecto",
            "depends_on": [], "policy": policy}, "# Política de proyecto")
    for tid in sorted(all_task_ids):
        origin = next((e for uid, e in elements.items() if work_ids.get(uid) == tid), None)
        units = sorted(task_units[tid])
        resolution = resolutions.get("tasks", {}).get(tid, {})
        criteria, checks = task_controls(origin, elements, resolution, target)
        task = {"format": FORMAT, "kind": "task", "id": tid, "units": units,
                "owner": origin.data.get("owner", "source-owner-pending") if origin else "migration-operator",
                "criteria": criteria, "policies": resolution.get("policies", [])}
        if origin and origin.data.get("paths"):
            task["paths"] = origin.data["paths"]
        if tid in parent_of:
            task["parent"] = parent_of[tid]
        children = sorted(k for k, p in parent_of.items() if p == tid)
        if children:
            task["subtasks"] = children
        body = "# " + tid + "\n\n" + "\n".join(task_sections[tid])
        if origin and origin.uid in approved:
            decisions = approved[origin.uid]
            # Reuse only explicit execution decisions. Approval of a proposal is
            # preserved as a decision, not promoted to execution authorization.
            execution = [d for d in decisions if d.data.get("purpose") in {"execution", "implementation"}]
            if execution:
                decision = execution[-1]
                task["authority"] = {"actor": decision.data.get("actor") or "recorded-source-actor",
                    "source": "Migrated decision " + decision.id, "scope": ["implement"],
                    "approved_scope": scope_digest(task, body)}
        source_state = origin.meta.get("state") if origin else "unknown"
        blockers = []
        # Old method flags are preserved in the source prose, not promoted to
        # functional work. Missing machine definitions are checked on use/close,
        # never instantiated as a migration backlog for every historical task.
        if origin:
            for key in ("blockers", "blocking_findings"):
                value = origin.data.get(key, [])
                if value:
                    blockers.extend(value if isinstance(value, list) else [value])
            if (source_state == "blocked" or origin.data.get("health") == "blocked") and not blockers:
                blockers.append("Bloqueo declarado en origen; consultar el alcance y dependencias conservados")
        state = "bloqueado" if blockers else {
            "retired": "cancelado", "cancelled": "cancelado", "superseded": "cancelado",
            "ready": "preparado", "approved": "preparado", "active": "en-curso", "in-progress": "en-curso",
            "in-review": "en-curso", "reconciliation-required": "en-curso",
            "blocked": "bloqueado", "closed": "cerrado", "completed": "cerrado", "done": "cerrado"
        }.get(source_state, "definido")
        plan = {"format": FORMAT, "kind": "plan", "id": tid, "state": state,
                "blockers": blockers, "checks": checks,
                "next": origin.data.get("next_step", "") if origin else "",
                "bases": {unit_path(u): digest(output[unit_path(u)]) for u in units},
                "delivery": {k: "unknown: consultar hechos históricos conservados; la conversión no los verifica" for k in DELIVERY}}
        if resolution.get("no_checks_reason"):
            plan["no_checks_reason"] = resolution["no_checks_reason"]
        output[task_path(tid, "tarea")] = document(task, body)
        output[task_path(tid, "plan")] = document(plan, "# Plan de " + tid + "\n\n" + "\n".join(plan_sections[tid]))
    mapping = {source: sorted(names)[0] for source, names in source_targets.items()}
    # Resolve Markdown links using their original document base before moving.
    # Retain referenced binary assets outside the method document tree.
    anchors = {slug(e.id): target[uid] for uid, e in elements.items()}
    for destination, raw in list(output.items()):
        text = raw.decode()
        origins = [p for p, names in source_targets.items() if destination in names]
        def link(match):
            label, href = match[1], match[2].strip("<>")
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", href) or href.startswith("#"):
                return match[0]
            base, _, anchor = href.partition("#")
            candidates = [base.lstrip("/")] if base.startswith(("/", "docs/", ".lks-sdd/")) else [
                posixpath.normpath(posixpath.join(posixpath.dirname(p), base)) for p in origins]
            found = [p for p in candidates if p in mapping or p in reader.inventory]
            if anchor.lower() in anchors:
                return f"[{label}](/" + anchors[anchor.lower()] + "#" + anchor.lower() + ")"
            if len(set(found)) != 1:
                return match[0]
            old = found[0]
            if old in mapping:
                return f"[{label}](/" + mapping[old] + ("#" + anchor if anchor else "") + ")"
            if old.startswith(ARCHIVE) or old.endswith(".md"):
                return label + " (referencia histórica retirada)"
            blob = read(reader.root, old)
            asset = "docs/assets/sdd/" + digest(blob)[:16] + "-" + Path(old).name
            output[asset] = blob
            return f"[{label}](/" + asset + ")"
        output[destination] = re.sub(r"\[([^\]\n]+)\]\(([^)\n]+)\)", link, text).encode()
    return output, mapping, {"source_elements": len(elements), "tasks": len(all_task_ids),
                            "units": len(unit_sections), "decisions_current": len(approved)}


def rewrite(text, mapping, runtime):
    for old, new in sorted(mapping.items(), key=lambda x: -len(x[0])):
        text = text.replace(old, new)
    text = re.sub(r"\.lks-sdd/runtime/[^\s`\"')]+/scripts/lks_sdd\.py", runtime + "/scripts/lks_sdd.py", text)
    text = re.sub(r"\.lks-sdd/runtime/[0-9][^\s`\"')/]*", runtime, text)
    text = text.replace("docs/V3-COMMON.md", "docs/V5.md")
    return text


def preview(root, *, core=None, mappings=None, dispositions=None, resolutions=None):
    root = filesystem_root(root)
    dispositions = dispositions or {}
    with locked(root):
        if read(root, JOURNAL) is not None or read(root, ".sdd-work/journal.json") is not None:
            raise Conflict("Resume pending operation first")
        if paths(root, "docs/sdd"):
            raise Conflict("Existing v5 documents require explicit reconciliation")
        if read(root, REPORT) is not None:
            raise Conflict("An existing conversion report requires explicit reconciliation: " + REPORT)
        reader = Reader(root)
        output, mapping, counts = convert(reader, mappings, resolutions)
        if core is None:
            from v5_distribution import core_files
            core = core_files(Path(__file__).resolve().parents[1])
        from v5_distribution import consumer_files, runtime_id
        runtime = ".lks-sdd/runtime/" + runtime_id(core)
        adapters = consumer_files(core)
        for name, raw in output.items():
            if name.startswith("docs/sdd/"):
                output[name] = rewrite(raw.decode(), mapping, runtime).encode()
        # References rewritten during conversion are part of the preserved scope.
        # Rebind bases/authority to the actual converted bytes, not a pre-rewrite copy.
        for name, raw in list(output.items()):
            if name.startswith("docs/sdd/"):
                meta, body = parse(raw)
                if meta["kind"] == "task" and meta.get("authority"):
                    meta["authority"]["approved_scope"] = scope_digest(meta, body)
                    output[name] = document(meta, body)
                elif meta["kind"] == "plan":
                    meta["bases"] = {p: digest(output[p]) for p in meta["bases"]}
                    output[name] = document(meta, body)
        managed = ("<!-- LKS-SDD:BEGIN -->\n# LKS-SDD v5\n"
                   f"Runtime: `{runtime}/scripts/lks_sdd.py`. Run `doctor` before governed writes.\n"
                   "Read task + its single plan + applicable capability specs under docs/sdd. "
                   "Reuse current authority; unresolved critical decisions block only their affected scope. "
                   "Use the six skills in the pinned runtime and docs/V5.md. "
                   "Do not infer deployment or acceptance from verification.\n<!-- LKS-SDD:END -->")
        original = (read(root, "AGENTS.md") or b"").decode("utf-8-sig")
        agents = MARKER.sub(lambda _: managed, original) if MARKER.search(original) else original.rstrip() + "\n\n" + managed + "\n"
        output.update(adapters)
        output["AGENTS.md"] = agents.encode()
        retired = set(reader.inventory + paths(root, ".lks-sdd"))
        known_metadata = {".gitattributes", "project.json", "distribution-lock.json", "installation.json",
                          "transactions.json", "history-compaction-completed.json", "runtime", "objects",
                          "handoffs", "requests", "maintenance", "cache", "locks"}
        unknown = [name for name in retired if name.startswith(".lks-sdd/") and
                   name.split("/")[1] not in known_metadata and not
                   re.fullmatch(r"GATE-[A-Z0-9_-]+\.json", name.split("/")[1])]
        if unknown:
            raise ValueError("Unclassified project-local files are preserved; reconcile ownership: " + ", ".join(sorted(unknown)))
        # Consumer adapters are owned only with their original LKS-SDD identity.
        for name in paths(root, ".github/skills"):
            if "/lks-sdd-" in name:
                retired.add(name)
        for name in (".github/lks-sdd-host.md", ".github/copilot-instructions.md"):
            raw = read(root, name)
            if raw and (b"LKS-SDD" in raw or b"lks-sdd" in raw):
                if name in adapters:
                    continue
                old_text = raw.decode("utf-8-sig")
                block = "<!-- LKS-SDD:BEGIN -->\nRead AGENTS.md and .github/lks-sdd-host.md. Use the pinned v5 six skills, capabilities, task and single evolving plan.\n<!-- LKS-SDD:END -->"
                output[name] = (MARKER.sub(lambda _: block, old_text) if MARKER.search(old_text) else
                    rewrite(old_text, mapping, runtime)).encode()
        # Scan Git tracked consumers, not dependency/vendor trees or arbitrary disk.
        try:
            commit = git(root, "rev-parse", "HEAD")
            tracked = git(root, "ls-files", "-z", binary=True).decode("utf-8").split("\0")
        except (OSError, subprocess.CalledProcessError):
            commit, tracked = None, []
        unresolved = []
        for name in tracked:
            if not name or name in retired or name in output or name.endswith(('.png', '.jpg', '.zip', '.pdf')):
                continue
            path = path_at(root, name)
            if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
                continue
            try:
                text = path.read_bytes().decode("utf-8")
            except UnicodeError:
                continue
            if "docs/lks-sdd" not in text and ".lks-sdd/runtime" not in text and name not in dispositions:
                continue
            disposition = dispositions.get(name)
            if disposition:
                if not disposition.get("reason") or disposition.get("sha256") != digest(path.read_bytes()):
                    raise Conflict("Consumer disposition needs current bytes and an explicit reason: " + name)
                if disposition.get("action") == "historical":
                    continue
                if disposition.get("action") == "retire":
                    retired.add(name)
                    continue
                if disposition.get("action") == "replace" and isinstance(disposition.get("text"), str):
                    output[name] = disposition["text"].encode()
                    continue
                raise ValueError("Unknown consumer disposition: " + name)
            revised = rewrite(text, mapping, runtime)
            # Never rewrite arbitrary application code by a broad textual guess.
            if name == ".gitattributes":
                lines = [line for line in text.splitlines() if not line.startswith(("docs/lks-sdd/", ".lks-sdd/objects/", ".lks-sdd/transactions"))]
                output[name] = ("\n".join(lines) + "\ndocs/sdd/**/*.md text eol=lf\n").encode()
            elif name.endswith((".md", ".yml", ".yaml")):
                revised = revised.replace("docs/lks-sdd", "docs/sdd")
                if re.search(r"lks_sdd\.py[^\n]*\bv[23]\b", revised):
                    unresolved.append(name)
                elif revised != text:
                    output[name] = revised.encode()
            else:
                unresolved.append(name)
        if unresolved:
            raise ValueError("Reconcile active legacy consumers before preview: " + ", ".join(unresolved))
        changes = {name: None for name in retired}
        changes.update(output)
        work = path_at(root, WORK)
        if work.exists():
            raise Conflict("A preview already exists; apply it or discard-preview explicitly")
        work.mkdir(parents=True)
        entries = {}
        for number, (name, after) in enumerate(sorted(changes.items())):
            path = path_at(root, name)
            before = file_digest(path) if path.is_file() else None
            after_hash = digest(after)
            if before == after_hash:
                continue
            staged = None
            if after is not None:
                staged = "stage/" + str(number)
                atomic_write(work / staged, after)
            entries[name] = {"before": before, "after": after_hash, "staged": staged}
        payload = {"format": "lks-sdd/5-migration-forward", "root": str(root), "commit": commit,
                   "source_inventory": sorted(retired), "entries": entries, "counts": counts}
        report = conversion_report(root, reader, changes, entries, counts)
        atomic_write(work / "report.md", report)
        payload["report_sha256"] = digest(report)
        raw = encode(payload).encode()
        atomic_write(work / "preview.json", raw)
        return {"status": "prepared", "preview_sha256": digest(raw), "counts": counts,
                "files_removed": sum(e["after"] is None for e in entries.values()),
                "files_written": sum(e["after"] is not None for e in entries.values()),
                "reversible": False, "review": str(work / "preview.json")}


def load_preview(root, expected_hash=None):
    raw = read(root, WORK + "/preview.json")
    if raw is None or (expected_hash and digest(raw) != expected_hash):
        raise Conflict("Preview missing or changed")
    payload = json.loads(raw)
    if payload.get("format") != "lks-sdd/5-migration-forward" or filesystem_root(payload["root"]) != filesystem_root(root):
        raise ValueError("Preview belongs to another project/format")
    for name, item in payload["entries"].items():
        path_at(root, name)
        if item["staged"] and digest(read(root, WORK + "/" + item["staged"])) != item["after"]:
            raise Conflict("Staged result changed")
    if digest(read(root, WORK + '/report.md')) != payload['report_sha256']:
        raise Conflict('Staged conversion report changed')
    return payload


def conversion_report(root, reader, changes, entries, counts):
    """One bounded human report; byte totals never assert semantic acceptance."""
    categories = ("Documentación SDD activa", "Histórico del método", "Control del plugin", "Runtime", "Recursos adjuntos", "Integraciones y apoyo")
    def category(name):
        if name.startswith(".lks-sdd/runtime/"): return "Runtime"
        if name.startswith(".lks-sdd/"): return "Control del plugin"
        if name.startswith(ARCHIVE): return "Histórico del método"
        if name.startswith("docs/assets/sdd/"): return "Recursos adjuntos"
        if name.startswith(("docs/lks-sdd/", "docs/sdd/")):
            return "Documentación SDD activa" if name.endswith(".md") else "Recursos adjuntos"
        return "Integraciones y apoyo"
    before = {k: [0, 0] for k in categories}
    after = {k: [0, 0] for k in categories}
    for name, raw in changes.items():
        path = path_at(root, name)
        key = category(name)
        if path.is_file():
            before[key][0] += 1; before[key][1] += path.stat().st_size
        if raw is not None:
            after[key][0] += 1; after[key][1] += len(raw)
    rows = ["| Categoría | Archivos antes | Archivos después | Bytes antes | Bytes después | Diferencia bytes |",
            "|---|---:|---:|---:|---:|---:|"]
    for key in categories:
        a, b = before[key], after[key]
        rows.append(f"| {key} | {a[0]} | {b[0]} | {a[1]} | {b[1]} | {b[1]-a[1]:+d} |")
    a = [sum(v[i] for v in before.values()) for i in (0, 1)]
    b = [sum(v[i] for v in after.values()) for i in (0, 1)]
    rows.append(f"| **Total del alcance convertido** | **{a[0]}** | **{b[0]}** | **{a[1]}** | **{b[1]}** | **{b[1]-a[1]:+d}** |")
    variation = f"{(b[1]-a[1])*100/a[1]:+.1f}%" if a[1] else "no comparable: origen vacío"
    created = sum(e['before'] is None for e in entries.values())
    removed = sum(e['after'] is None for e in entries.values())
    modified = len(entries) - created - removed
    pending, criteria, units = [], 0, 0
    for name, raw in changes.items():
        if raw is None or not name.startswith('docs/sdd/'): continue
        meta, _ = parse(raw)
        units += meta['kind'] == 'unit'
        if meta['kind'] == 'task': criteria += len(meta.get('criteria', {}))
        if meta['kind'] == 'plan' and meta.get('blockers'):
            pending.append((meta['id'], len(meta['blockers'])))
    reasons = {}
    for name, raw in changes.items():
        if raw is not None and name.startswith('docs/sdd/'):
            meta, _ = parse(raw)
            if meta['kind'] == 'plan':
                for reason in {r if isinstance(r, str) else encode(r) for r in meta.get('blockers', [])}:
                    reasons[reason] = reasons.get(reason, 0) + 1
    text = ("# Informe de conversión a LKS-SDD v5\n\n"
        "Conversión técnica completada y validada. Informe único de esta migración; no es un registro acumulativo.\n\n"
        f"Formatos de origen: {', '.join(sorted(reader.schemas))}. Destino: lks-sdd/5.\n\n"
        "## Volumen antes y después\n\n" + '\n'.join(rows) + '\n\n'
        f"Volumen total: **{a[1]/1048576:.3f} → {b[1]/1048576:.3f} MiB** ({variation}). Un MiB equivale a 1 048 576 bytes.\n\n"
        f"Archivos creados: **{created}**; modificados: **{modified}**; retirados: **{removed}**; sin cambios: **{len(changes)-len(entries)}**.\n\n"
        "Ámbito: archivos SDD y de apoyo que participan en la conversión, incluidos históricos del método, runtime e integraciones adaptadas. "
        "No incluye el resto del repositorio, Git ni temporales. Este informe añade **1 archivo** fuera del árbol canónico y se excluye de la tabla para evitar una medida autorreferente.\n\n"
        "## Resultado y estados conservados\n\n"
        f"Elementos de origen: **{len(reader.elements)}**; seleccionados para conversión: **{counts['source_elements']}**; "
        f"unidades funcionales: **{units}**; tareas con su plan: **{counts['tasks']}**; criterios operativos: **{criteria}**; "
        f"elementos con decisiones vigentes comprobadas: **{counts['decisions_current']}**.\n\n"
        f"Tareas con bloqueos declarados en origen: **{len(pending)}**. No son defectos funcionales comprobados por la conversión. "
        "Los detalles pertenecen al plan de cada tarea.\n\n"
        "La falta de configuración de pruebas no crea tareas ni bloqueos de migración. Los indicadores antiguos de reconciliación "
        "se conservan como contexto histórico, sin exigir reconstruir checkpoints, observers o recibos. "
        "Solicitudes, propuestas y registros de entrega no se convierten por sí solos en nuevas tareas. "
        "Los controles vigentes se configuran cuando se retome el alcance pertinente; se conserva su aplicabilidad.\n\n")
    for reason, total in sorted(reasons.items(), key=lambda item: (-item[1], item[0]))[:12]:
        text += f"- {total} tareas: {reason[:240].replace(chr(10), ' ')}\n"
    if len(reasons) > 12: text += f"- Otros {len(reasons)-12} motivos: consultar los planes afectados.\n"
    text += ("\nSe retira control histórico sustituido, inventarios redundantes y versiones anteriores del runtime. "
        "El conocimiento útil seleccionado se reorganiza en especificaciones, tareas y planes; los recursos referenciados se conservan como adjuntos.\n\n"
        "La migración es definitiva: no genera backups ni ofrece rollback. La preparación temporal se elimina al finalizar. "
        "Una interrupción se reanuda hacia v5. El historial Git no se modifica.\n\n"
        "La validación acredita estructura e integridad técnica. Los bytes y archivos no acreditan por sí solos equivalencia semántica, ahorro de tokens, "
        "aceptación humana ni pruebas de la aplicación. No se renuevan resultados históricos ni se reabren trabajos terminados por migrarlos.\n")
    return text.encode('utf-8')


def finish_report(root, payload):
    raw = read(root, WORK + '/report.md')
    if digest(raw) != payload['report_sha256']:
        raise Conflict('Staged conversion report changed')
    existing = read(root, REPORT)
    if existing == raw: return
    if existing is not None:
        raise Conflict('Preserve externally edited conversion report: ' + REPORT)
    atomic_write(path_at(root, REPORT), raw, expected=None)


def validate_converted(root, entries):
    # Bind both retirement and the report to the bytes actually reviewed.
    for name, item in entries.items():
        if item['after'] is not None:
            path = path_at(root, name)
            if not path.is_file() or file_digest(path) != item['after']:
                raise Conflict('Converted output edited during migration: ' + name)
    from v5_distribution import doctor
    doctor(root)
    result = validate(root)
    if result['status'] != 'passed':
        raise ValueError('Converted documents require reconciliation: ' + encode(result))
    return result


def clean_staging(root):
    # This exact temporary directory is owned by preview, never a source tree.
    base = path_at(root, WORK)
    for directory, _, files in os.walk(base, topdown=False):
        for name in files:
            candidate = Path(directory) / name
            path_at(root, candidate.relative_to(filesystem_root(root)).as_posix()).unlink()
        Path(directory).rmdir()


def run(root, preview_hash=None, *, resume=False, interrupt_after=None):
    root = filesystem_root(root)
    with locked(root):
        if read(root, ".sdd-work/journal.json") is not None:
            raise Conflict("Recover the normal document transaction first")
        journal = read(root, JOURNAL)
        if resume and journal and json.loads(journal).get("phase") == "cleanup":
            if digest(read(root, REPORT)) != json.loads(journal).get('report_sha256'):
                raise Conflict('Conversion report changed during cleanup')
            clean_staging(root)
            path_at(root, JOURNAL).unlink()
            return {"status": "passed", "phase": "cleanup-complete", "reversible": False}
        if resume and not journal:
            if read(root, WORK + "/preview.json") is None and read(root, ".lks-sdd/distribution-lock.json"):
                from v5_distribution import doctor
                doctor(root)
                result = validate(root)
                if result["status"] == "passed":
                    return {"status": "unchanged", "files": 0, "reversible": False}
            raise ValueError("No interrupted migration; apply requires its reviewed hash")
        payload = load_preview(root, preview_hash)
        preview_digest = digest(read(root, WORK + "/preview.json"))
        if not resume and journal:
            raise Conflict("Use migration-resume for an interrupted cutover")
        if not resume and not preview_hash:
            raise ValueError("Apply requires the exact reviewed preview hash")
        if journal and json.loads(journal).get("preview") != preview_digest:
            raise Conflict("Journal and preview disagree")
        entries = payload["entries"]
        actual = set(paths(root, "docs/lks-sdd") + paths(root, ".lks-sdd"))
        if actual - (set(payload["source_inventory"]) | set(entries)):
            raise Conflict("New files appeared in the migration scope")
        for name, item in entries.items():
            path = path_at(root, name)
            now = file_digest(path) if path.is_file() else None
            if now not in ({item["before"], item["after"]} if resume else {item["before"]}):
                raise Conflict("Migration conflicts with edited source: " + name)
        atomic_write(path_at(root, JOURNAL), encode({"preview": preview_digest, "phase": "apply"}).encode())
        ordered = sorted(entries, key=lambda n: (entries[n]["after"] is None, not n.startswith("docs/sdd/"), n))
        checked = False
        for number, name in enumerate(ordered, 1):
            item = entries[name]
            if item["after"] is None and not checked:
                validate_converted(root, entries)
                checked = True  # Validate the new model before retiring its sources.
            path = path_at(root, name)
            now = file_digest(path) if path.is_file() else None
            if now not in {item["before"], item["after"]}:
                raise Conflict("Concurrent edit during migration: " + name)
            if now != item["after"]:
                if item["after"] is None:
                    path.unlink()
                else:
                    raw = read(root, WORK + "/" + item["staged"])
                    if digest(raw) != item["after"]:
                        raise Conflict("Staged result changed during migration")
                    atomic_write(path, raw, expected=item["before"])
            if number == interrupt_after:
                raise InterruptedError("Injected interruption; resume forward to v5")
        result = validate_converted(root, entries)
        for prefix in ("docs/lks-sdd", ".lks-sdd", ".github/skills"):
            base = path_at(root, prefix)
            for directory, _, _ in os.walk(base, topdown=False):
                try:
                    Path(directory).rmdir()
                except OSError:
                    pass
        finish_report(root, payload)
        atomic_write(path_at(root, JOURNAL), encode({"preview": preview_digest, "phase": "cleanup", "report_sha256": payload['report_sha256']}).encode())
        clean_staging(root)
        path_at(root, JOURNAL).unlink()
        return {**result, "reversible": False, "files": len(entries), "temporary_files": 0, "report": REPORT}


def discard_preview(root):
    """Discard only an unapplied preparation; a started conversion must finish."""
    with locked(root):
        if read(root, JOURNAL) is not None:
            raise Conflict("Migration started: resume forward; reversal is unsupported")
        clean_staging(root)
        return {"status": "discarded"}
