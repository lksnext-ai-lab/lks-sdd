"""Reproducible synthetic contracts and verified test-only 3.4.2 reference."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/fixtures/approval-reference"


@contextmanager
def runtime(original=False):
    if "v3_contract" in sys.modules: raise RuntimeError("Select the runtime before importing it")
    with tempfile.TemporaryDirectory(prefix="approval-reference-") as temp:
        sys.path.insert(0, str(ROOT / "scripts"))
        if original:
            manifest = json.loads((REFERENCE / "manifest.json").read_bytes())
            with zipfile.ZipFile(REFERENCE / "original.zip") as archive:
                if set(archive.namelist()) != set(manifest["files"]): raise AssertionError("Reference inventory changed")
                for name, digest in manifest["files"].items():
                    raw = archive.read(name)
                    if hashlib.sha256(raw).hexdigest() != digest: raise AssertionError("Reference hash changed: " + name)
                    (Path(temp) / name).write_bytes(raw)
            sys.path.insert(0, temp)
        yield


def stable_generation():
    import v3_contract
    counter = iter(range(1000000))
    uuid.uuid4 = lambda: uuid.uuid5(uuid.NAMESPACE_OID, "approval-generated-" + str(next(counter)))
    v3_contract.now = lambda: "2026-10-14T00:00:00.000000+00:00"


def key(label): return str(uuid.uuid5(uuid.NAMESPACE_URL, "https://synthetic.invalid/approval/" + label))


def synthetic(root, size=100, technologies=5, *, historical=False, project="one"):
    from v3_contract import Model, Element, element, location, fingerprint, render, sha
    from v3_policy import profile
    from v3_approval import descriptor
    model = Model(root)
    def add(kind, name, **data):
        item = element(kind, name, "Complete synthetic contract: " + name, identifier=key(project + "/" + name), **data)
        item["meta"].update(state="active", nature="decision")
        e = Element(item["meta"], item["body"], location(item))
        model.elements[e.uid] = e
        return e
    person = add("member", "actor", roles=["owner", "specifier", "developer", "reviewer", "integrator"], active=True)
    controls = {c: {"mode": "not-used", "reason": "Explicit synthetic contract"} for c in ("sonar", "dependency-check")}
    policy = add("policy", "policy", **profile("individual-brief", controls))
    add("project", "project", method_version="3.0.0", policy=policy.uid, target="main")
    request = add("request", "request", policy=policy.uid, policy_digest=policy.digest(), flags={})
    proposal = add("proposal", "proposal", request=request.uid, part="joint", objective="Synthetic operation",
                   included=["app.py"], excluded=[], impact="Synthetic", acceptance=["result"],
                   behavior="Return synthetic result", solution={"components": [{"name": "synthetic"}]})
    request.relations["proposal"] = [proposal.uid]
    tech = [add("technology", "technology-" + str(i), request=request.uid) for i in range(technologies)]
    proposal.relations["technology"] = [e.uid for e in tech]
    shared = [add("rule", "global-" + str(i), **{"global": True}) for i in range(min(24, max(2, size // 20)))]
    for i, e in enumerate(shared[1:]): e.relations["depends_on"] = [shared[i].uid]
    for e in tech: e.relations["constraints"] = [shared[-1].uid]
    while len(model.elements) < size:
        add("feature", "feature-" + str(len(model.elements)), request=request.uid)
    if historical:
        import v2_contract as v2
        old = []
        inherited = shared + tech
        for i, e in enumerate(inherited):
            item = v2.make_element(("TECH" if e.kind == "technology" else "RULE") + f"-{i+1:04}", e.kind, e.id, e.body,
                                   uid=e.uid, state="confirmed", nature="decision")
            if e.kind == "technology":
                item["meta"]["technology"] = {"subject": "Synthetic technology", "state": "confirmed", "critical": True,
                                              "scope": ["global"], "evidence": [{"kind": "consumer-document", "path": "synthetic.md", "sha256": "0" * 64}], "provenance": []}
            old.append(item)
        raw = v2.render_document("specification", "Synthetic originals", old)
        parsed = {e.id: e for e in v2.parse_document(raw.decode(), "original")[0]}
        paths = ["docs/lks-sdd/00-control/migrations/synthetic/original-a.md",
                 "docs/lks-sdd/00-control/migrations/synthetic/original-b.md"]
        for path in paths:
            target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        mapping = {}
        for i, (e, source) in enumerate(zip(inherited, old)):
            mapping[e.uid] = {"target_digest": e.digest(), "original": paths[i % 2], "original_sha256": sha(raw),
                              "source_id": source["meta"]["id"], "source_normative": fingerprint(parsed[source["meta"]["id"]].normative())}
        add("migration", "migration", content_confirmations=mapping)
    else:
        # Two mechanisms are necessary: neither alone approves all technologies.
        for purpose, selected in (("technology", tech[::2]), ("proposal", tech[1::2])):
            if selected:
                desc = descriptor(model, [e.uid for e in selected])
                add("decision", purpose + "-decision", purpose=purpose, outcome="approved", descriptor=desc)
    for e in model.elements.values():
        raw = render(e.item()); target = root / e.path
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        model.hashes[e.path] = sha(raw)
    return model, tech, proposal, person


def capture(callback):
    from v3_contract import ContractError
    try: return {"result": callback()}
    except (ContractError, KeyError, ValueError, TypeError) as exc:
        return {"error": type(exc).__name__, "message": str(exc)}


def shared_inventory_history(model, events=80, files=6000):
    """Valid repeated event references to one physical technical inventory."""
    from content_store import prepare_inventory
    from v3_contract import element, location, render, fingerprint
    entries = {f"src/f{i:05}.py": "0" * 64 for i in range(files)}
    changes = {}
    ref = prepare_inventory(model.root, entries, changes)
    for name, raw in changes.items():
        target = model.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for i in range(events):
        item = element("execution", f"Historical execution {i}", "Unrelated completed work",
                       identifier=key(f"memory-event-{i}"),
                       subject={"scope": sorted(entries), "files_ref": ref, "digest": fingerprint(entries)})
        (model.root / location(item)).write_bytes(render(item))
    return ref


def semantic(value, roots=()):
    """Keep all fields; rewrite only explicitly declared environment root strings.

    Generated UUIDs and timestamps are seeded/fixed before importing the runtime.
    No digest, source, decision, pending item or error is discarded.
    """
    if isinstance(value, dict): return {semantic(k, roots): semantic(v, roots) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [semantic(v, roots) for v in value]
    if isinstance(value, set): return sorted(value)
    if isinstance(value, str):
        for root, label in roots: value = value.replace(str(root), label).replace(str(root).replace("\\", "/"), label)
    return value
