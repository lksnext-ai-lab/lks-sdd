"""Explicit ownership by proposal units; missing classification stays uncertain."""
EDGES = {"requirements", "acceptance", "constraints", "interfaces", "uses", "depends_on", "tests", "technology"}


def memberships(model):
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
