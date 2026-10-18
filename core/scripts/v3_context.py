"""Sufficient, literal, deduplicated project context. No canonical cache writes."""
import json
import copy
from collections import OrderedDict, deque
import posixpath
import re
from urllib.parse import unquote, urlsplit

from v3_contract import ContractError, EVENTS, load, read_bytes, sha, fingerprint
from v3_policy import policy_for

LINK = re.compile(r'!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)')
EDGE = {"requirements", "acceptance", "constraints", "interfaces", "uses", "depends_on", "covers", "tests", "technology", "proposal"}
_CACHE = OrderedDict()
SELECTOR_VERSION = "lks-sdd-v4/1"
TEXT_SUFFIXES = (".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".log", ".py", ".html", ".htm", ".js", ".ts", ".css", ".sql", ".xml")


def linked_assets(model, sources, *, included_paths=()):
    """Recover referenced bytes only after selecting the literal sources."""
    assets, seen = [], set()
    included_paths = set(included_paths) | {s["source"]["path"] for s in sources}
    queue = deque((s["source"]["path"], s["text"]) for s in sources)
    while queue:
        path, text = queue.popleft()
        for match in LINK.finditer(text):
            raw = match[1] or match[2]; link = urlsplit(raw)
            if link.scheme or link.netloc: continue
            target = unquote(link.path)
            if not target: continue
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if relative in seen or relative in included_paths: continue
            seen.add(relative)
            data = read_bytes(model.root, relative)
            asset = {"path": relative, "sha256": sha(data), "bytes": len(data), "reason": "adjunto referenciado"}
            if relative.lower().endswith(TEXT_SUFFIXES):
                asset["text"] = data.decode("utf-8"); queue.append((relative, asset["text"]))
            else: asset["requires_observation"] = True
            assets.append(asset)
    return assets


def select(model, roots, operation="implement", *, conservative=False):
    from v3_evaluation import count
    count("context_selections")
    if not roots: raise ContractError("Seleccione una petición o tarea; una raíz vacía no acredita suficiencia")
    selected, reasons, widened = {}, {}, []
    from v3_scope import work_scope, prose_scopes, incoming_index
    allowed_units, requested, classified = work_scope(model, roots)
    conflicts = set()
    for e in model.elements.values():
        owners = {model.get(u).data.get("request") for u in classified.get(e.uid, set())} - {None}
        if e.data.get("request") and owners and e.data["request"] not in owners:
            conflicts.add(e.uid)
    def outside(e):
        return bool(allowed_units and classified.get(e.uid) and not classified[e.uid] & allowed_units
                    and not e.data.get("global") and e.uid not in conflicts)
    def add(e, reason):
        if e.uid in selected: return
        if e.retired: raise ContractError("Dependencia aplicable retirada: " + e.id)
        selected[e.uid] = e; reasons[e.uid] = reason
        for relation in EDGE:
            for key in e.relations.get(relation, []):
                child = model.get(key)
                if e.kind == "request" and relation == "proposal" and outside(child): continue
                add(child, relation + " de " + e.id)
        if e.data.get("request"): add(model.get(e.data["request"], "request"), "petición de " + e.id)
        for dependency in e.data.get("dependencies", []): add(model.get(dependency["uid"]), "dependencia tipada de " + e.id)
    for key in roots:
        e = model.get(key)
        if e.retired: raise ContractError("La raíz de trabajo está retirada; seleccione una porción vigente")
        if e.kind in EVENTS or e.kind in {"member", "legacy"}: raise ContractError("Seleccione una raíz normativa de trabajo")
        add(e, "raíz solicitada")
    requests = {e.uid for e in selected.values() if e.kind == "request"}
    for plan in model.by_kind("plan"):
        if set(plan.relations.get("tasks", [])) & set(selected): add(plan, "reglas del plan de la porción")
    for e in model.elements.values():
        if e.retired or e.kind in EVENTS | {"legacy", "member", "project", "policy", "plan", "task", "request"}: continue
        if outside(e): continue
        scope = e.data.get("request")
        if e.uid in conflicts:
            widened.append({"uid": e.uid, "code": "conflicting-membership", "reason": "Petición declarada y pertenencia por relaciones discrepantes; conservar"})
        # Missing ownership is uncertainty, not proof of irrelevance.
        if e.uid in conflicts or e.data.get("global") or scope in requests or classified.get(e.uid, set()) & allowed_units or not scope:
            if e.uid not in selected and not scope and not e.data.get("global"):
                widened.append({"uid": e.uid, "reason": "Sin clasificación de ámbito; conservar hasta aclarar"})
            add(e, "regla global o alcance incierto" if not scope else "contrato de la petición")
    # Incoming contributions and contracts can constrain a slice even when it omitted
    # the outgoing link. Iterate to closure, retaining distinct scope-specific rules.
    incoming = incoming_index(model)
    visited = set()
    while set(selected) - visited:
        for key in sorted(set(selected) - visited):
            visited.add(key)
            for source in sorted(incoming.get(key, ())): add(model.get(source), "contrato/contribución entrante")
    if conservative:
        for e in model.elements.values():
            if not e.retired and e.kind not in EVENTS | {"legacy", "member", "policy"}:
                add(e, "referencia conservadora para comparación del selector")
    policy_sources = {}
    for request in (e for e in selected.values() if e.kind == "request"):
        policy = policy_for(model, request)
        policy_sources[policy.uid + ":" + policy.digest()] = policy
    sources = []
    for e in sorted(selected.values(), key=lambda x: (x.kind, x.uid)):
        if e.kind in EVENTS: continue
        sources.append({"key": e.uid, "source": e.source(), "reason": reasons[e.uid], "meta": e.meta, "text": e.body})
    for key, policy in policy_sources.items():
        if key not in {s["key"] for s in sources}:
            sources.append({"key": key, "source": policy.source(), "reason": "proceso aplicable", "meta": policy.meta, "text": policy.body})
    # Unclassified preambles and standalone Markdown cannot be silently discarded.
    declarations, proof = prose_scopes(model)
    excluded = []
    for path, prose in model.prose.items():
        declaration = declarations.get(path)
        if declaration and not conservative and not declaration["global"]:
            applicable = set(declaration["units"]) & (set(selected) | allowed_units | requests)
            if not applicable:
                excluded.append({"path": path, "sha256": declaration["sha256"], "reason": declaration["reason"], "decision": proof.uid})
                continue
        sources.append({"key": "prose:" + path, "source": {"path": path, "sha256": model.hashes[path]},
                        "reason": "prosa con alcance acreditado" if declaration else "prosa fuera de bloques; ámbito no acreditado", "text": prose})
    provenance = [model.project.source(), proof.source()] if proof else []
    declared_paths = {r["path"] for r in model.project.data.get("context_scopes", {}).get("sources", [])}
    diagnostics = [{"path": path, "code": "unclassified" if path not in declared_paths else "unaccredited-or-stale",
                    "action": "include-literal"} for path in model.prose if path not in declarations]
    excluded_units = [{"uid": e.uid, "source": e.source(), "request": e.data.get("request"),
                       "units": sorted(classified.get(e.uid, ())), "reason": "outside-declared-applicability"}
                      for e in model.elements.values() if e.uid not in selected and not e.retired
                      and e.kind not in EVENTS | {"legacy", "member", "project", "policy"}]
    exclusion_assets = [a for row in excluded for a in proof.data.get("scope_assets", {}).get(row["path"], [])] if proof else []
    assets = linked_assets(model, sources)
    characters = sum(len(s["text"]) + len(json.dumps(s.get("meta", {}), ensure_ascii=False)) for s in sources)
    characters += sum(len(a.get("text", "")) for a in assets)
    return {"operation": operation, "roots": roots, "sources": sources, "attachments": assets, "widened": widened, "excluded_prose": excluded,
            "excluded_units": excluded_units, "scope_diagnostics": diagnostics, "scope_exclusion_assets": exclusion_assets,
            "scope_provenance": provenance,
            "snapshot": model.snapshot(), "selection_digest": fingerprint({s["key"]: s["source"] for s in sources}),
            "measurement": {"method": "characters-divided-by-4-estimate", "characters": characters,
                            "estimated_tokens": (characters+3)//4, "billed_tokens": None},
            "budget_notice": "El contrato necesario supera el objetivo; conserve obligaciones o reduzca el alcance acordado" if characters > 32000 else None,
            "sufficiency": "requires-attachment-observation" if any(a.get("requires_observation") for a in assets) else "literal-selected",
            "session_reuse": "full-core-reloaded; host retention not assumed"}


def context(root, roots, operation="implement", *, comparison=False, reference=False):
    model = load(root).require_valid()
    from v3_git import observe
    git = observe(model.root)
    for request in model.by_kind("request"): policy_for(model, request)
    key = fingerprint({"selector": SELECTOR_VERSION, "root": str(model.root), "sources": model.hashes,
                       "operation": operation, "roots": roots, "branch": git["branch"], "head": git["head"], "comparison": comparison, "reference": reference})
    cached = _CACHE.get(key)
    if cached:
        try:
            dependencies = cached["attachments"] + cached.get("scope_exclusion_assets", []) + cached.get("comparison_assets", [])
            valid = all(sha(read_bytes(model.root, a["path"])) == a["sha256"] for a in dependencies)
        except ContractError: valid = False
        if valid:
            result = copy.deepcopy(cached); result["runtime_cache"] = "hit; literal text reloaded for host"
            _CACHE.move_to_end(key)
            return result
    result = select(model, roots, operation, conservative=reference)
    if comparison:
        full = result if reference else select(model, roots, operation, conservative=True)
        chosen, complete = ({s["key"]: s for s in packet["sources"]} for packet in (result, full))
        result["comparison"] = {
            "reference_only": sorted(set(complete) - set(chosen)), "selected_only": sorted(set(chosen) - set(complete)),
            "shared_literal_equal": all(chosen[k]["text"] == complete[k]["text"] and chosen[k].get("meta") == complete[k].get("meta") for k in set(chosen) & set(complete)),
            "semantic_equivalence": "not-established", "reference_characters": full["measurement"]["characters"],
            "selected_characters": result["measurement"]["characters"]}
        result["comparison_assets"] = [{"path": a["path"], "sha256": a["sha256"]} for a in full["attachments"]]
    result["selector_mode"] = "conservative-reference" if reference else "comparison-only" if comparison else "applicable-literal"
    result["activation"] = "Literal applicability closure; unclassified obligations retained; full reference available explicitly"
    result["runtime_cache"] = "miss"
    _CACHE[key] = copy.deepcopy(result)
    while len(_CACHE) > 8: _CACHE.popitem(last=False)
    return result
