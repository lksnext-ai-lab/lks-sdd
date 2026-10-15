"""Explicit ownership by proposal units; missing classification stays uncertain."""
EDGES = {"requirements", "acceptance", "constraints", "interfaces", "uses", "depends_on", "tests", "technology"}


def memberships(model):
    from v3_evaluation import memo
    result = memo(model, ("memberships",), lambda: _memberships(model),
                  lambda result: (sum(map(len, result.values())), 0))
    return {key: set(owners) for key, owners in result.items()}


def _memberships(model):
    result = {}
    roots = model.by_kind("proposal") + [e for e in model.by_kind("feature") if e.data.get("legacy")]
    for proposal in roots:
        seen, pending = set(), [proposal.uid]
        while pending:
            key = pending.pop()
            if key in seen: continue
            seen.add(key); result.setdefault(key, set()).add(proposal.uid)
            e = model.get(key)
            pending.extend(k for rel in EDGES for k in e.relations.get(rel, []))
    return result


def work_scope(model, roots):
    """Resolve proposal ownership before a plan exists; explicit slices take precedence."""
    entries = [model.get(key) for key in roots]
    units = {e.uid for e in entries if e.kind in {"proposal", "feature"}}
    for e in entries:
        if e.kind in {"task", "plan"}: units.update(e.data.get("proposal_units", []))
        if e.kind == "task" and not e.data.get("proposal_units"):
            units.update(u for p in model.by_kind("plan") if e.uid in p.relations.get("tasks", [])
                         for u in p.data.get("proposal_units", []))
    requests = {e.uid for e in entries if e.kind == "request"}
    requests.update(e.data["request"] for e in entries if e.data.get("request"))
    if not units:
        units.update(u for key in requests for u in model.get(key, "request").relations.get("proposal", []))
    classified = memberships(model)
    if not units:
        units.update(u for e in entries for u in classified.get(e.uid, set()))
    return {model.get(u).uid for u in units}, requests, classified


PROSE_SCOPE = "lks-sdd-prose-scope/1"


def validate_prose_scope(model):
    """Structural validation is separate from authorization and content freshness."""
    from v3_contract import ContractError
    value = model.project.data.get("context_scopes")
    if value is None: return
    if not isinstance(value, dict) or set(value) != {"version", "sources"} or value.get("version") != PROSE_SCOPE or not isinstance(value["sources"], list):
        raise ContractError("Declaraciones de prosa inválidas o de formato no soportado")
    paths = set()
    for row in value["sources"]:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "units", "global", "reason"}:
            raise ContractError("Declare fuente, contenido, alcance y fundamento de la prosa")
        if not isinstance(row["path"], str) or row["path"] in paths:
            raise ContractError("Fuente de prosa duplicada o inválida")
        paths.add(row["path"])
        from v3_contract import path_at
        path_at(model.root, row["path"], missing=True)
        digest = row["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ContractError("Huella de prosa inválida")
        if not isinstance(row["global"], bool) or not isinstance(row["reason"], str) or not row["reason"].strip():
            raise ContractError("Declare carácter global y fundamento del alcance")
        keys = row["units"]
        if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys) or len(keys) != len(set(keys)) or (not keys and not row["global"]):
            raise ContractError("Una prosa no global necesita ámbito explícito")
        for key in keys:
            e = model.get(key)
            if e.uid != key or e.kind not in {"request", "proposal", "task", "plan", "feature"}:
                raise ContractError("Ámbito de prosa inexistente o de tipo incorrecto")


def prose_scopes(model):
    """Only current, explicitly governed declarations can exclude literal prose."""
    from v3_contract import sha
    value = model.project.data.get("context_scopes")
    if not value: return {}, None
    validate_prose_scope(model)
    revoked = {e.data.get("revokes") for e in model.by_kind("decision") if e.data.get("outcome") == "revoked"}
    records = [e for e in model.by_kind("decision") if e.uid not in revoked and not e.data.get("historical_only")
               and e.data.get("purpose") == "governance" and e.data.get("outcome") == "approved"
               and isinstance(e.data.get("presentation"), dict)
               and e.data.get("presentation", {}).get("version") == "lks-sdd-presentation/2"
               and e.data.get("presentation", {}).get("event") == "governance"
               and isinstance(e.data.get("descriptor"), dict)
               and isinstance(e.data["descriptor"].get("units"), dict)
               and e.data.get("descriptor", {}).get("units", {}).get(model.project.uid) == model.project.digest()]
    if not records: return {}, None
    proof = max(records, key=lambda e: (e.data.get("decided_at", ""), e.uid))
    return {r["path"]: r for r in value["sources"] if r["path"] in model.prose
            and not any(model.get(k).retired for k in r["units"])
            and sha(model.prose[r["path"]].encode("utf-8")) == r["sha256"]}, proof


def prose_catalog(model, offset=0, limit=20):
    from v3_contract import ContractError, sha
    if offset < 0 or not 1 <= limit <= 100: raise ContractError("Página fuera de límites")
    scopes, proof = prose_scopes(model)
    declared = {r["path"]: r for r in model.project.data.get("context_scopes", {}).get("sources", [])}
    paths = sorted(model.prose)
    rows = []
    for path in paths[offset:offset+limit]:
        status = "accredited" if path in scopes else "stale" if proof and path in declared else "unapproved" if path in declared else "unclassified"
        rows.append({"path": path, "sha256": sha(model.prose[path].encode("utf-8")), "source_sha256": model.hashes[path],
                     "characters": len(model.prose[path]), "scope_status": status,
                     "scope": scopes.get(path), "decision": proof.source() if path in scopes else None})
    return {"total": len(paths), "elements": rows, "next_offset": offset+limit if offset+limit < len(paths) else None, "writes": []}
