"""Sufficient, literal, deduplicated project context. No canonical cache writes."""
import json
import copy
from collections import OrderedDict
import posixpath
import re
from urllib.parse import unquote, urlsplit

from v3_contract import ContractError, EVENTS, load, read_bytes, sha, fingerprint
from v3_policy import policy_for

LINK = re.compile(r'!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)')
EDGE = {"requirements", "acceptance", "constraints", "interfaces", "uses", "depends_on", "covers", "tests", "technology", "proposal"}
_CACHE = OrderedDict()
SELECTOR_VERSION = "lks-sdd-v3/2"


def select(model, roots, operation="implement", *, conservative=False):
    if not roots: raise ContractError("Seleccione una petición o tarea; una raíz vacía no acredita suficiencia")
    selected, reasons, widened = {}, {}, []
    from v3_scope import memberships
    classified = memberships(model)
    allowed_units = {u for key in roots for u in model.get(key).data.get("proposal_units", [])}
    for key in roots:
        root = model.get(key)
        if root.kind == "task" and not root.data.get("proposal_units"):
            plans = [p for p in model.by_kind("plan") if root.uid in p.relations.get("tasks", [])]
            allowed_units.update(u for p in plans for u in p.data.get("proposal_units", []))
    def outside(e):
        return bool(allowed_units and classified.get(e.uid) and not classified[e.uid] & allowed_units and not e.data.get("global"))
    def add(e, reason):
        if e.uid in selected: return
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
        # Missing ownership is uncertainty, not proof of irrelevance.
        if e.data.get("global") or scope in requests or not scope:
            if e.uid not in selected and not scope and not e.data.get("global"):
                widened.append({"uid": e.uid, "reason": "Sin clasificación de ámbito; conservar hasta aclarar"})
            add(e, "regla global o alcance incierto" if not scope else "contrato de la petición")
    # Incoming contributions and contracts can constrain a slice even when it omitted
    # the outgoing link. Iterate to closure, retaining distinct scope-specific rules.
    changed = True
    while changed:
        count = len(selected)
        for e in model.elements.values():
            if e.retired or e.kind in EVENTS | {"legacy", "member", "project", "policy"}: continue
            incoming = {k for rel in ("implements", "modifies", "contributes_to", "interfaces", "depends_on") for k in e.relations.get(rel, [])}
            if incoming & set(selected): add(e, "contrato/contribución entrante")
        changed = len(selected) != count
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
    for path, prose in model.prose.items():
        sources.append({"key": "prose:" + path, "source": {"path": path, "sha256": model.hashes[path]},
                        "reason": "prosa fuera de bloques; ámbito no acreditado", "text": prose})
    assets, seen = [], set()
    queue = [(s["source"]["path"], s["text"]) for s in sources]
    while queue:
        path, text = queue.pop(0)
        for match in LINK.finditer(text):
            raw = match[1] or match[2]; link = urlsplit(raw)
            if link.scheme or link.netloc: continue
            target = unquote(link.path)
            if not target: continue
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if relative in seen or relative in {s["source"]["path"] for s in sources}: continue
            seen.add(relative)
            data = read_bytes(model.root, relative)
            asset = {"path": relative, "sha256": sha(data), "bytes": len(data), "reason": "adjunto referenciado"}
            if relative.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
                asset["text"] = data.decode("utf-8"); queue.append((relative, asset["text"]))
            else: asset["requires_observation"] = True
            assets.append(asset)
    characters = sum(len(s["text"]) + len(json.dumps(s.get("meta", {}), ensure_ascii=False)) for s in sources)
    characters += sum(len(a.get("text", "")) for a in assets)
    return {"operation": operation, "roots": roots, "sources": sources, "attachments": assets, "widened": widened,
            "snapshot": model.snapshot(), "selection_digest": fingerprint({s["key"]: s["source"] for s in sources}),
            "measurement": {"method": "characters-divided-by-4-estimate", "characters": characters,
                            "estimated_tokens": (characters+3)//4, "billed_tokens": None},
            "budget_notice": "El contrato necesario supera el objetivo; conserve obligaciones o reduzca el alcance acordado" if characters > 32000 else None,
            "sufficiency": "requires-attachment-observation" if any(a.get("requires_observation") for a in assets) else "literal-selected",
            "session_reuse": "full-core-reloaded; host retention not assumed"}


def context(root, roots, operation="implement", *, comparison=False):
    model = load(root).require_valid()
    from v3_git import observe
    git = observe(model.root)
    for request in model.by_kind("request"): policy_for(model, request)
    key = fingerprint({"selector": SELECTOR_VERSION, "root": str(model.root), "sources": model.hashes,
                       "operation": operation, "roots": roots, "branch": git["branch"], "head": git["head"], "comparison": comparison})
    cached = _CACHE.get(key)
    if cached:
        try:
            valid = all(sha(read_bytes(model.root, a["path"])) == a["sha256"] for a in cached["attachments"])
        except ContractError: valid = False
        if valid:
            result = copy.deepcopy(cached); result["runtime_cache"] = "hit; literal text reloaded for host"
            _CACHE.move_to_end(key)
            return result
    result = select(model, roots, operation, conservative=not comparison)
    result["selector_mode"] = "comparison-only" if comparison else "conservative-reference"
    result["activation"] = "Optimized selector pending observed acceptance; comparison must not replace execution context"
    result["runtime_cache"] = "miss"
    _CACHE[key] = copy.deepcopy(result)
    while len(_CACHE) > 8: _CACHE.popitem(last=False)
    return result
