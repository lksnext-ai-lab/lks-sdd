"""Generic, synthetic project variants; no consumer code or credentials."""

from __future__ import annotations

import hashlib
import sys
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "skills/lks-sdd-implement/scripts"))
from eval_support import (
    initialize,
    materialize_ready_increment,
    confirm_planning,
    authorize_implementation,
)
from prepare_increment import prepare
from project_variants import CONFIG, markdown

IMAGE = "python@sha256:eb43ff125d8d58d7449dcba7d336c23bcac412f526d861db493b9994d8010280"
OBSERVER = """import hashlib, json, os, runpy
from pathlib import Path
gate = os.environ["LKS_GATE_ID"]
app = runpy.run_path("/input/component/service.py")
if gate == "GATE-API-TEST":
    assert app["acknowledge"]({"value": "example"}) == {"accepted": "example"}
    assert app["acknowledge"]({"value": ""}) == {"error": "required"}
    observations = {"assertions_passed": 2}
else:
    assert app["contract"] == {"request": ["value"], "response": ["accepted", "error"]}
    observations = {"contract_fields_checked": 3}
# Verify actual isolation, including the host canonical path being absent.
assert not Path("/input/.lks-sdd/project.json").exists()
try:
    Path("/input/component/service.py").write_text("tamper")
except OSError:
    observations["input_readonly"] = True
else:
    raise AssertionError("input was writable")
out = Path(os.environ["LKS_OUTPUT"]) / "observed.json"
raw = json.dumps(observations, sort_keys=True).encode()
out.write_bytes(raw)
print(json.dumps({"schema_version":"1.0", "gate_id":gate,
 "run_nonce":os.environ["LKS_RUN_NONCE"], "status":"passed", "scopes":["component"],
 "interfaces":[], "observations":observations,
 "artifacts":[{"path":"observed.json", "sha256":hashlib.sha256(raw).hexdigest()}]}))
"""


def materialize(root: Path, *, start_legacy: bool = True) -> dict:
    initialize(root, "synthetic-project-variant")
    materialize_ready_increment(root, confirm_plan=False)
    detail = root / "docs/lks-sdd/04-delivery/tasks/TASK-001.md"
    detail.write_text(
        detail.read_text(encoding="utf-8").replace(
            "GATE-API-TEST, GATE-API-OPENAPI, GATE-OCI-BUILD",
            "GATE-API-TEST, GATE-API-OPENAPI",
        ),
        encoding="utf-8",
    )
    confirm_planning(root)
    authorize_implementation(root)
    common = dict(
        project_root=root,
        increment="INC-001",
        task=["TASK-001"],
        date="2026-09-17",
        actor="synthetic-owner",
        as_json=True,
        authorize=False,
        preview_hash=None,
    )
    if start_legacy:
        code, preview = prepare(Namespace(**common, dry_run=True, apply=False))
        assert code == 0, preview
        code, applied = prepare(
            Namespace(
                **{
                    **common,
                    "authorize": True,
                    "preview_hash": preview["preview_hash"],
                },
                dry_run=False,
                apply=True,
            )
        )
        assert code == 0, applied
    component = root / "component"
    component.mkdir()
    (component / "service.py").write_text(
        'def acknowledge(request):\n    return {"accepted": request["value"]} if request["value"] else {"error": "required"}\ncontract = {"request": ["value"], "response": ["accepted", "error"]}\n'
    )
    (component / "requirements.txt").write_text("fastapi==0.140.0\nattrs==25.3.0\n")
    (component / "requirements.lock").write_text("fastapi==0.140.0\nattrs==25.3.0\n")
    (component / ".python-version").write_text("3.13.12\n")
    (root / "observer.py").write_text(OBSERVER, encoding="utf-8", newline="\n")
    sha = hashlib.sha256((root / "observer.py").read_bytes()).hexdigest()
    observer = {
        "path": "observer.py",
        "sha256": sha,
        "command": ["/usr/local/bin/python", "-I", "-B", "/input/observer.py"],
    }
    config = {
        "schema_version": "1.0",
        "policy": {
            "mode": "approved-project-variants",
            "allow_task_closure": True,
            "allowed_stages": ["development", "integration"],
            "approver_roles": ["synthetic-owner"],
            "max_age_days": 30,
            "cache_max_age_hours": 24,
        },
        "variants": [
            {
                "id": "VAR-001",
                "profile_id": "API-FASTAPI-STATELESS-OCI",
                "increment": "INC-001",
                "release": "REL-001",
                "task_ids": ["TASK-001"],
                "environment": "ENV-001",
                "technology_roots": ["component"],
                "inputs": ["component", "observer.py"],
                "composition": {
                    "layout": "component",
                    "runtime": "python-service",
                    "base_layout": "src/lks_sdd_api",
                },
                "gates": [
                    {
                        "id": gate,
                        "source": "approved-consumer",
                        "stage": stage,
                        "scopes": ["component"],
                        "interfaces": [],
                        "deterministic": True,
                        "timeout_seconds": 20,
                        "image": IMAGE,
                        "observer": observer,
                    }
                    for gate, stage in [
                        ("GATE-API-TEST", "development"),
                        ("GATE-API-OPENAPI", "integration"),
                    ]
                ],
            }
        ],
    }
    path = root / CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(markdown(config, "Synthetic technology variant"))
    return config
