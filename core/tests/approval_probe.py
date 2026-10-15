"""Isolated differential worker; imports exactly one selected runtime."""
import argparse
import copy
import json
from pathlib import Path
import tempfile

from approval_performance_support import runtime, synthetic, capture, stable_generation, semantic


def probe(root):
    from v3_approval import approved, descriptor, decision
    from v3_contract import Element, element, location
    from v31_review import overlay
    from approval_performance_support import key
    output = {}
    for historical in (False, True):
        model, tech, proposal, person = synthetic(root, 65, 4, historical=historical)
        label = "historical" if historical else "current"
        def results():
            return [{p: capture(lambda e=e, p=p: approved(model, [e.uid], p)) for p in ("technology", "proposal")} for e in tech]
        output[label] = {"approvals": results(), "descriptor": descriptor(model, [tech[0].uid]),
                         "sources": dict(model.hashes)}
        uncertain = element("interface", "Unclassified shared interface", "Applicability has not been established",
                            identifier=key("uncertain"))
        overlay(model, [uncertain])
        output[label]["uncertain-obligation"] = results()
        del model.elements[uncertain["meta"]["uid"]]
        if historical:
            receipt = model.by_kind("migration")[0]
            first_proof = next(iter(receipt.data["content_confirmations"].values()))
            output[label]["malformed-proofs"] = []
            for field in ("original_sha256", "source_id", "source_normative", "target_digest", "original"):
                saved = copy.deepcopy(first_proof[field])
                for value in ([], {}, None, 1, True, "invalid"):
                    first_proof[field] = value
                    output[label]["malformed-proofs"].append({"field": field, "value": value, "result": capture(lambda: approved(model, [tech[0].uid], "technology"))})
                first_proof[field] = saved
            proof = receipt.data["content_confirmations"][tech[0].uid]
            original = root / proof["original"]; raw = original.read_bytes()
            original.write_bytes(raw + b"\nchanged")
            output[label]["modified"] = results()
            original.unlink()
            output[label]["missing"] = results()
            original.write_bytes(raw)
            proof["source_normative"] = "f" * 64
            output[label]["inconsistent"] = results()
        else:
            revoked = element("decision", "Revocation", "Explicit synthetic revocation", identifier=key("revocation"),
                              outcome="revoked", revokes=model.by_kind("decision")[0].uid)
            overlay(model, [revoked]); output[label]["revoked"] = results()
            person.meta["data"]["roles"] = []
            output[label]["permission"] = capture(lambda: decision(model, person.uid, [tech[0].uid], "technology", "Observed statement"))
        tech[0].body += " Changed normative revision."
        tech[0].meta["revision"] += 1
        output[label]["revision"] = results()
        tech[1].relations["depends_on"] = [key("missing")]
        output[label]["invalid-reference"] = capture(lambda: descriptor(model, [tech[1].uid]))
    model, tech, _, _ = synthetic(root, 30, 2)
    e, other = tech
    output["identities"] = []
    def identities():
        return [capture(lambda value=value, kind=kind: model.get(value, kind).source()) for value, kind in (
            (e.uid, None), (e.id, None), (model.project.uid + "/" + e.id, "technology"),
            (key("foreign") + "/" + e.uid, None), (e.id, "request"), ("absent", None), ([], None))]
    output["identities"].append(identities())
    other.meta["id"] = e.id; output["identities"].append(identities())
    other.meta["id"] = e.uid; output["identities"].append(identities())
    del model.elements[other.uid]; output["identities"].append(identities())
    e.meta["id"] = e.uid; output["identities"].append(identities())
    replacement = copy.deepcopy(e.item()); replacement["meta"]["id"] = "NEW-ALIAS"
    overlay(model, [replacement]); output["identities"].append(identities())
    e = model.get("NEW-ALIAS"); e.meta = {**e.meta, "id": "absent", "kind": "requirement"}
    output["identities"].append(identities())
    cloned = copy.deepcopy(model)
    copied = cloned.get(e.uid)
    copied.meta["id"] = "COPY-ALIAS"
    output["copied-model"] = {"old": capture(lambda: cloned.get("absent").source()),
                              "new": capture(lambda: cloned.get("COPY-ALIAS").source()),
                              "source": model.get(e.uid).source()}
    shallow = copy.copy(model)
    e.meta["id"] = "SHARED-REFERENCE-ALIAS"
    addition = element("rule", "Shared table addition", "Preserve ordinary shallow-copy sharing",
                       identifier=key("shallow-added"))
    overlay(model, [addition])
    model.elements |= {}
    output["shallow-model"] = {"shared_table": shallow.elements is model.elements,
                               "updated": shallow.get(e.id).source(), "source": model.get(e.id).source(),
                               "added": shallow.get(addition["meta"]["uid"]).source()}
    from v3_git import integration_guard
    trusted, _, _, _ = synthetic(root / "trusted", 30, 2)
    candidate, changed, _, _ = synthetic(root / "candidate", 30, 2)
    changed[0].body += " Explicit reviewed change."
    overlay(candidate, [element("receipt", "Integration observation", "Synthetic observation", identifier=key("new-observation"))])
    output["integration-comparison"] = integration_guard(trusted, candidate)
    return semantic(output, [(root, "$PROJECT")])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with runtime(args.original), tempfile.TemporaryDirectory(prefix="approval-probe-") as temp:
        stable_generation()
        args.output.write_text(json.dumps(probe(Path(temp)), sort_keys=True), encoding="utf-8")
