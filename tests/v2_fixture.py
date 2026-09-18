"""Synthetic, deliberately explicit v2 obligations. No real consumer data."""
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from v2_contract import DOCS, DOMAINS, canonical, make_element, render_document


def element(identifier, kind, body="Contenido confirmado para el caso sintético.", **values):
    title = values.pop("title", identifier)
    defaults = {"uid": str(uuid.uuid5(uuid.NAMESPACE_DNS, "synthetic-v2:" + identifier)),
                "state": "confirmed", "nature": "decision"}
    defaults.update(values)
    return make_element(identifier, kind, title, body, **defaults)


def write(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())


def project(root):
    feature = DOCS + "/02-specification/features/FTR-001-pedidos/specification.md"
    write(root, ".lks-sdd/project.json", canonical({"schema_version": "2.0", "method_version": "2.0.0",
                                                   "project_id": "synthetic-project", "artifacts": []}))
    write(root, feature, render_document("feature", "Gestión de pedidos", [
        element("FTR-001", "feature", "Gestionar pedidos y su impresión.", relations={"requirements": ["FR-001"]}),
        element("FR-001", "requirement", "Solo se imprime un pedido confirmado. Nunca incluir datos privados.",
                relations={"acceptance": ["AC-001"]}),
        element("AC-001", "acceptance", "Un pedido borrador debe rechazar la impresión.", relations={"tests": ["TEST-001"]}),
        element("TEST-001", "test", "Comprobar pedido confirmado y borrador.", cases=["positive", "negative", "regression"])]))
    write(root, DOCS + "/02-specification/shared/applicability.md", render_document("applicability", "Aplicabilidad", [
        element(f"APP-{i:03}", "applicability", domain=domain, scope="global", critical=True,
                applicability="not-applicable", reason="Caso de prueba acotado sin esta dimensión.")
        for i, domain in enumerate(DOMAINS, 1)]))
    write(root, DOCS + "/04-delivery/tasks/TASK-001.md", render_document("task", "Impresión", [
        element("TASK-001", "task", "Implementar impresión y sus pruebas negativas.", state="ready",
                owner="synthetic-developer", risk="low", change_types=["evolution"],
                relations={"implements": ["FTR-001"], "acceptance": ["AC-001"], "tests": ["TEST-001"],
                           "increment": ["INC-001"], "plan": ["PLAN-001"], "release": ["REL-001"]},
                paths=["src/print.py", "tests/test_print.py"], gates=["GATE-UNIT"],
                evidence_scopes=["component"], interfaces=[])]))
    write(root, DOCS + "/04-delivery/plans.md", render_document("planning", "Plan", [
        element("INC-001", "increment", relations={"requirements": ["FR-001"]}),
        element("REL-001", "release", relations={"increment": ["INC-001"]}),
        element("PLAN-001", "plan", planning_policy="complete", relations={"requirements": ["FR-001"], "implements": ["TASK-001"]})]))
    write(root, DOCS + "/04-delivery/governance.md", render_document("governance", "Gobierno sintético", [
        element("GOV-001", "decision", category="delivery-governance", delivery_model="continuous-evolution",
                versioning="semver", branching="reviewed-changes", ci="local-test-fixture", recovery="restore-tested-snapshot",
                review_policy="explicit-owner-review", tracking="repository-only")]))
    write(root, "src/print.py", "def print_order():\n    return 'draft'\n")
    return feature
