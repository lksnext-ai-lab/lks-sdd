"""Synthetic, bounded cases. No real identities or host observations."""
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from v3_usage import observe
from v3_contract import sha


def observation(stage="query", operation="context", text="Contrato literal del fixture", run="synthetic-run", result=None):
    result = result if result is not None else {"sources": [{"key": "synthetic-rule", "source": {"digest": sha(text.encode())}, "text": text}], "selection_digest": sha(text.encode())}
    return observe(operation, {"roots": ["synthetic-request"]}, result,
                   context={"run_id": run, "phase": "implementation"}, stage=stage, elapsed=0.001)


def repeated():
    return [observation(), observation()]


def late():
    row = observation(stage="declared", operation="implement")
    row["declarations"] = [{"type": "late-context", "case": "synthetic-late", "before": "evidence/before.json", "after": "evidence/after.json",
                            "contract": "sources/contract.txt", "defect": "evidence/defect.json", "check": "evidence/check.json"}]
    materials = {"evidence/before.json": {"selection": [], "result": "Hola"}, "evidence/after.json": {"selection": ["contract"], "result": "Kaixo"},
                 "sources/contract.txt": "La salida acordada es Kaixo", "evidence/defect.json": {"expected": "Kaixo", "actual": "Hola"},
                 "evidence/check.json": {"expected": "Kaixo", "actual": "Kaixo", "outcome": "passed", "source": "synthetic"}}
    return [row], materials
