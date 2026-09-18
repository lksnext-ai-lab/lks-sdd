"""Opt-in project technology approvals. The certified profile engine is immutable."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from technology_resolution import inspect_dependencies, digest, safe_file

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "docs/lks-sdd/02-design/technology-variants.md"
APPROVALS = "docs/lks-sdd/02-design/technology-approvals"
STAGES = ("development", "integration", "preproduction", "release", "production")
SCOPES = {"component", "contract", "composition", "user-flow", "persistence", "visual"}


def variant_paths(root: Path) -> tuple[str, str]:
    """Versioned locations; updating the plugin never converts consumer sources."""
    manifest = root / ".lks-sdd/project.json"
    if manifest.is_file() and read_json(checked_path(root, ".lks-sdd/project.json")).get("schema_version") == "2.0":
        return "docs/lks-sdd/03-solution/technology-variants.md", "docs/lks-sdd/00-control/technology-approvals"
    return CONFIG, APPROVALS
BLOCK = re.compile(r"^```lks-sdd-variants\s*\n(.*?)^```\s*$", re.M | re.S)


class VariantError(ValueError):
    """Expected fail-closed approval/verification failure."""


def checked_path(root: Path, relative: str, *, exists: bool = True) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise VariantError("Use an explicit project-relative POSIX path")
    p = Path(relative)
    if p.is_absolute() or any(x in {"..", ""} for x in p.parts) or ":" in relative:
        raise VariantError("Path escapes the project")
    target = root / p
    try:
        target.resolve().relative_to(root.resolve())
        current = root
        for part in p.parts:
            current /= part
            if current.is_symlink() or (
                hasattr(current, "is_junction") and current.is_junction()
            ):
                raise VariantError("Linked paths are not permitted")
        if exists and not target.exists():
            raise VariantError(f"Missing input: {relative}")
    except (OSError, ValueError) as exc:
        raise VariantError(f"Unsafe input: {relative}: {exc}") from exc
    return target


def read_json(path: Path) -> dict:
    try:
        if path.stat().st_size > 16 * 1024 * 1024:
            raise VariantError("JSON exceeds 16 MB")
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise VariantError("Expected a JSON object")
        return obj
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VariantError(str(exc)) from exc


def markdown(value: dict, title: str) -> bytes:
    return (
        f"# {title}\n\n```lks-sdd-variants\n"
        + json.dumps(value, ensure_ascii=False, indent=2)
        + "\n```\n"
    ).encode()


def read_markdown(root: Path, relative: str) -> dict:
    text = safe_file(root, relative).read_text(encoding="utf-8")
    blocks = BLOCK.findall(text)
    if len(blocks) != 1:
        raise VariantError(
            f"{relative}: exactly one lks-sdd-variants block is required"
        )
    try:
        obj = json.loads(blocks[0])
        if not isinstance(obj, dict):
            raise VariantError("Expected an object")
        return obj
    except (ValueError, TypeError) as exc:
        raise VariantError(f"Invalid variant Markdown: {exc}") from exc


def validate_schema(value: dict, name: str) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise VariantError("Runtime dependency unavailable: install requirements-runtime.txt in the Python environment used by LKS-SDD; validation was not skipped") from exc

    schema = read_json(ROOT / "schemas" / name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda x: str(x.path)
    )
    if errors:
        raise VariantError(
            "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:8])
        )


def load_config(root: Path) -> dict | None:
    config_path, _ = variant_paths(root)
    if not (root / config_path).exists():
        return None
    value = read_markdown(root, config_path)
    validate_schema(value, "project-variants.schema.json")
    identifiers = [v["id"] for v in value["variants"]]
    if len(set(identifiers)) != len(identifiers):
        raise VariantError("Duplicate variant IDs")
    tasks = [t for v in value["variants"] for t in v["task_ids"]]
    if len(tasks) != len(set(tasks)):
        raise VariantError("A TASK must select one unambiguous variant")
    return value


def selected_variant(root: Path, task: str) -> dict | None:
    config = load_config(root)
    if not config or config["policy"]["mode"] != "approved-project-variants":
        return None
    return next((v for v in config["variants"] if task in v["task_ids"]), None)


def input_hashes(
    root: Path, paths: list[str], *, observer: bool = False
) -> dict[str, str]:
    files: dict[str, str] = {}
    total = 0
    for relative in paths:
        target = checked_path(root, relative)
        pending = [target]
        while pending:
            path = pending.pop()
            rel = path.relative_to(root).as_posix()
            checked_path(root, rel)
            parts = Path(rel).parts
            if any(
                p in {".git", ".lks-sdd", "node_modules", ".venv", "__pycache__"}
                for p in parts
            ) or rel.startswith("docs/lks-sdd/"):
                raise VariantError(
                    f"Canonical, private or generated input is forbidden: {rel}"
                )
            if any(
                p.startswith(".env")
                or p in {".ssh", ".aws", ".npmrc", ".pypirc", ".netrc"}
                or p.lower().endswith((".pem", ".key", ".pfx"))
                for p in parts
            ):
                raise VariantError(f"Secret-bearing input is forbidden: {rel}")
            if path.is_dir():
                pending.extend(sorted(path.iterdir()))
            elif path.is_file():
                raw = safe_file(root, rel).read_bytes()
                total += len(raw)
                if total > 128 * 1024 * 1024 or len(files) > 10000:
                    raise VariantError("Input snapshot exceeds bounded limits")
                files[rel] = hashlib.sha256(raw).hexdigest()
            else:
                raise VariantError(f"Not a regular input: {rel}")
    if not files:
        raise VariantError("Empty input set")
    return dict(sorted(files.items()))


def _expected(profile_id: str) -> tuple[dict, Any]:
    from profile_registry import load_profile_bundle

    bundle = load_profile_bundle(profile_id)
    if bundle.errors or not bundle.root:
        raise VariantError(f"Unresolved reference profile: {profile_id}")
    resolution = bundle.driver.get("variant", {}).get("resolution")
    if resolution:
        obj = read_json(safe_file(ROOT, resolution))
        return {
            "resolved": obj.get("packages", {}),
            "runtime_declared": obj.get("runtimes", {}),
            "tools_declared": obj.get("tools", {}),
        }, bundle
    return inspect_dependencies(bundle.root / "scaffold"), bundle


def diagnose(root: Path, profile_id: str | None = None) -> dict:
    """Read-only: hashes/metadata only; no build, Docker, browser or test process."""
    observed = inspect_dependencies(root)
    if profile_id is None:
        from profile_registry import load_catalog

        catalog, errors = load_catalog()
        if errors:
            raise VariantError("; ".join(errors))
        ranking = []
        keys = set(observed["declared"]) | set(observed["resolved"])
        for entry in catalog["profiles"]:
            expected, _ = _expected(entry["id"])
            overlap = len(
                keys & (set(expected.get("declared", {})) | set(expected["resolved"]))
            )
            ranking.append((overlap, entry["id"]))
        ranking.sort(key=lambda x: (-x[0], x[1]))
        if not ranking or ranking[0][0] == 0:
            return {
                "compatibility": "not-assessed",
                "summary": "Falta una referencia tecnológica evaluable.",
                "candidates": [],
                "diagnostic": observed,
                "processes_executed": 0,
            }
        profile_id = ranking[0][1]
    expected, bundle = _expected(profile_id)
    differences = []
    contradictions = []
    for key, declared in observed["declared"].items():
        resolved = observed["resolved"].get(key)
        if (
            re.fullmatch(r"\d+\.\d+\.\d+", declared)
            and resolved is not None
            and declared not in (resolved if isinstance(resolved, list) else [resolved])
        ):
            contradictions.append(f"{key}: manifest={declared}, lock={resolved}")
    for dimension in ("resolved", "runtime_declared", "tools_declared"):
        wanted, actual = expected.get(dimension, {}), observed[dimension]
        for key in sorted(set(wanted) | set(actual)):
            if wanted.get(key) != actual.get(key):
                kind = (
                    "additional"
                    if key not in wanted
                    else "missing"
                    if key not in actual
                    else "version"
                )
                differences.append(
                    {
                        "dimension": dimension,
                        "dependency": key,
                        "expected": wanted.get(key),
                        "actual": actual.get(key),
                        "kind": kind,
                        "risk": "Revisar contrato y gates afectados; la diferencia no demuestra incompatibilidad.",
                    }
                )
    from profile_registry import resolve_profile

    certified = resolve_profile(profile_id).verifiable
    if contradictions:
        state = "incompatible"
    elif observed["errors"] or not observed["input_hashes"]:
        state = "not-assessed"
    elif differences:
        state = "unassessed-variant"
    elif not expected.get("resolved"):
        state = "not-assessed"
    else:
        state = "exact-certified" if certified else "unassessed-variant"
    return {
        "compatibility": state,
        "profile_id": profile_id,
        "profile_version": bundle.profile["version"],
        "profile_certification": {
            "reference_certified": certified,
            "consumer_certified": state == "exact-certified",
        },
        "differences": differences,
        "contradictions": contradictions,
        "diagnostic": observed,
        "summary": f"{state}: {len(differences)} diferencias; {len(contradictions)} contradicciones.",
        "processes_executed": 0,
    }


def project_context(root: Path, variant: dict, *, execution: bool = False) -> dict:
    if read_json(checked_path(root, ".lks-sdd/project.json")).get("schema_version") == "2.0":
        from v2_verification import variant_context
        return variant_context(root, variant, execution=execution)
    from delivery_engine import validate_delivery_contract
    from planning_engine import assess_planning, assess_authorization
    from validate_project import validate_project

    report, manifest, definitions = validate_project(root)
    if not report.valid:
        raise VariantError("Invalid canonical project: " + "; ".join(report.errors[:6]))
    delivery = validate_delivery_contract(root, manifest)
    tasks = variant["task_ids"]
    for task in tasks:
        row = delivery["tasks"].get(task, {})
        if (
            row.get("Increment") != variant["increment"]
            or row.get("Release") != variant["release"]
        ):
            raise VariantError(
                "Variant TASK/release/increment is outside canonical scope"
            )
    planning = assess_planning(
        root, manifest, variant["increment"], release=variant["release"]
    )
    auth = assess_authorization(manifest, planning, tasks)
    if auth.get("status") != "authorized":
        raise VariantError("A current canonical AUTH is required for this TASK scope")
    matches = [
        e
        for e in manifest.get("executions", [])
        if set(tasks) <= set(e.get("task_ids", []))
        and e.get("authorization_id") == auth["authorization_id"]
        and e.get("status") not in {"cancelled", "completed"}
    ]
    if execution and len(matches) != 1:
        raise VariantError("A unique active EXEC for the current AUTH is required")
    bindings = {
        b
        for t in tasks
        for b in re.findall(
            r"BIND-\d{3}", delivery["tasks"][t].get("Profile binding", "")
        )
    }
    interfaces = {
        i: row
        for i, row in delivery.get("interfaces", {}).items()
        if set(tasks) & set(re.findall(r"TASK-\d{3}", row.get("Verification task", "")))
        and row.get("State") == "confirmed"
    }
    for row in interfaces.values():
        bindings.update(re.findall(r"BIND-\d{3}", row.get("Profile bindings", "")))
    bindings = sorted(bindings)
    if not bindings:
        raise VariantError("The TASK needs a reference profile binding")
    _, reference = _expected(variant["profile_id"])
    for binding in bindings:
        if binding not in delivery["bindings"]:
            raise VariantError("Missing canonical interface binding")
        if (
            reference.profile.get("profile_scope") != "system"
            and delivery["bindings"][binding]["profile_id"] != variant["profile_id"]
        ):
            raise VariantError("The variant reference must match the canonical binding")
    if reference.profile.get("profile_scope") == "system" and not any(
        row.get("Exact composition")
        == variant["profile_id"] + "@" + reference.profile["version"]
        for row in interfaces.values()
    ):
        raise VariantError("System reference must be linked by the canonical INT")
    return {
        "root": root,
        "manifest": manifest,
        "definitions": definitions,
        "delivery": delivery,
        "authorization": auth,
        "execution": matches[0] if len(matches) == 1 else None,
        "bindings": bindings,
        "planning": planning,
    }


def proposal(
    root: Path,
    variant_id: str,
    environment: str,
    stage: str,
    *,
    context: dict | None = None,
) -> dict:
    config = load_config(root)
    if not config or config["policy"]["mode"] != "approved-project-variants":
        raise VariantError("Strict policy: project variants are not enabled")
    variant = next((v for v in config["variants"] if v["id"] == variant_id), None)
    if not variant:
        raise VariantError("Unknown variant")
    if (
        stage not in STAGES
        or stage not in config["policy"]["allowed_stages"]
        or environment != variant["environment"]
    ):
        raise VariantError("Environment/stage outside project policy")
    context = context or project_context(root, variant)
    if environment != "not-applicable" and environment not in context["delivery"].get(
        "environments", {}
    ):
        raise VariantError(
            "Environment is not defined in canonical delivery governance"
        )
    environment_contract = (
        context["delivery"].get("environments", {}).get(environment, {})
    )
    role = str(environment_contract.get("Role", "")).casefold()
    if (
        re.search(r"\b(prod|production|producci[oó]n)\b", role)
        and stage != "production"
    ):
        raise VariantError("A production environment cannot use a development approval")
    diagnostics = []
    hashes = {}
    for location in variant["technology_roots"]:
        target = root if location == "." else checked_path(root, location)
        result = diagnose(target, variant["profile_id"])
        diagnostics.append(result)
        for name, sha in result["diagnostic"]["input_hashes"].items():
            hashes[(Path(location) / name).as_posix()] = sha
    if any(d["compatibility"] in {"incompatible", "not-assessed"} for d in diagnostics):
        raise VariantError(
            "Variant is incompatible or lacks reliable dependency information: "
            + "; ".join(d["summary"] for d in diagnostics)
        )
    observers = {}
    gate_ids = [g["id"] for g in variant["gates"]]
    if len(gate_ids) != len(set(gate_ids)):
        raise VariantError("Duplicate gates")
    for gate in variant["gates"]:
        if gate["id"] == "GATE-VISUAL-BROWSER-REVIEW":
            raise VariantError(
                "The canonical visual review cannot be replaced by an observer; use --visual-evidence"
            )
        if gate["source"] == "approved-consumer":
            obs = gate["observer"]
            material = input_hashes(
                root, [obs["path"], *obs.get("inputs", [])], observer=True
            )
            if material.get(obs["path"]) != obs["sha256"]:
                raise VariantError(
                    "Observer hash mismatch; review and approve new bytes"
                )
            observers[gate["id"]] = material
        elif gate["source"] == "packaged":
            _, bundle = _expected(variant["profile_id"])
            if not any(
                c["id"] == gate["id"] and c.get("kind") == "command"
                for c in bundle.driver["verify"]["checks"]
            ):
                raise VariantError("No packaged command for the declared gate")
        else:
            raise VariantError(
                "Experimental observers cannot enter an official approval"
            )
    _, bundle = _expected(variant["profile_id"])
    base_hash = hashlib.sha256(
        (bundle.root / "technology-profile.lock.json").read_bytes()
    ).hexdigest()
    material = {
        "schema_version": "1.0",
        "project_id": context["manifest"]["project_id"],
        "variant": variant,
        "policy": config["policy"],
        "environment": environment,
        "stage": stage,
        "authorization_id": context["authorization"]["authorization_id"],
        "environment_contract": environment_contract,
        "reference_bindings": [
            context["delivery"]["bindings"][b] for b in context["bindings"]
        ],
        "specification_fingerprint": context["planning"].get(
            "specification_fingerprint"
        ),
        "planning_fingerprint": context["planning"].get("planning_fingerprint"),
        "dependency_hashes": hashes,
        "observer_hashes": observers,
        "base_lock_sha256": base_hash,
        "differences": [x for d in diagnostics for x in d["differences"]],
        "stack": [
            {
                k: d["diagnostic"][k]
                for k in ("declared", "resolved", "runtime_declared", "tools_declared")
            }
            for d in diagnostics
        ],
    }
    for difference in material["differences"]:
        difference["affected_gates"] = [g["id"] for g in variant["gates"]]
        difference["impact"] = {
            "version": "Different API or runtime behavior may affect build and tests",
            "additional": "Additional dependency expands the dependency and security surface",
            "missing": "Reference dependency is absent; validate the equivalent composition",
        }[difference["kind"]]
    return {
        "status": "approval-required",
        "fingerprint": digest(material),
        "material": material,
        "summary": f"{variant_id}: {len(material['differences'])} diferencias, {len(observers)} observers del consumidor; {stage}/{environment}.",
        "affected_gates": [
            g["id"] for g in variant["gates"] if g["source"] != "packaged"
        ],
        "unchanged_gates": [
            g["id"] for g in variant["gates"] if g["source"] == "packaged"
        ],
        "profile_certification": {
            "reference_certified": diagnostics[0]["profile_certification"][
                "reference_certified"
            ],
            "consumer_certified": False,
        },
        "human_confirmations_required": 1,
        "processes_executed": 0,
    }


def approval_preview(
    root: Path,
    variant_id: str,
    environment: str,
    stage: str,
    *,
    actor: str,
    reason: str,
    risks: str,
    expires: str,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    value = proposal(root, variant_id, environment, stage)
    policy = value["material"]["policy"]
    if actor not in policy["approver_roles"] or not reason.strip() or not risks.strip():
        raise VariantError(
            "Authorized approver role, technical/functional reason and accepted risks are required"
        )
    until = date.fromisoformat(expires)
    if not today < until <= today + timedelta(days=policy["max_age_days"]):
        raise VariantError("Approval expiry must be in the permitted future window")
    receipt = {
        "schema_version": "1.0",
        "fingerprint": value["fingerprint"],
        "material": value["material"],
        "approved_by_role": actor,
        "approved_on": today.isoformat(),
        "expires_on": expires,
        "reason": reason,
        "accepted_risks": risks,
        "scope_limit": "Project technology only; no global certification or delivery authorization",
    }
    value["receipt"] = receipt
    value["preview_hash"] = digest(receipt)
    return value


def apply_approval(root: Path, preview: dict, authorized_hash: str) -> dict:
    receipt = preview["receipt"]
    fresh = approval_preview(
        root,
        receipt["material"]["variant"]["id"],
        receipt["material"]["environment"],
        receipt["material"]["stage"],
        actor=receipt["approved_by_role"],
        reason=receipt["reason"],
        risks=receipt["accepted_risks"],
        expires=receipt["expires_on"],
    )
    if authorized_hash != fresh["preview_hash"] or fresh["receipt"] != receipt:
        raise VariantError("Preview hash changed; review the current proposal")
    _, approvals_path = variant_paths(root)
    relative = f"{approvals_path}/{authorized_hash}.md"
    path = checked_path(root, relative, exists=False)
    content = markdown(
        {**receipt, "approval_id": authorized_hash},
        "Aprobación tecnológica de proyecto",
    )
    if path.exists():
        if path.read_bytes() != content:
            raise VariantError("Immutable approval was modified")
        return {
            "status": "approved-project-variant",
            "approval_id": authorized_hash,
            "changed": False,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    return {
        "status": "approved-project-variant",
        "approval_id": authorized_hash,
        "changed": True,
    }


def current_approval(root: Path, proposed: dict, *, today: date | None = None) -> dict:
    today = today or date.today()
    _, approvals_path = variant_paths(root)
    directory = checked_path(root, approvals_path, exists=False)
    matches = []
    for path in sorted(directory.glob("*.md")):
        value = read_markdown(root, path.relative_to(root).as_posix())
        identity = value.get("approval_id")
        if (
            path.stem != identity
            or digest({k: v for k, v in value.items() if k != "approval_id"})
            != identity
        ):
            raise VariantError("Approval integrity failure")
        if value.get("fingerprint") != proposed["fingerprint"]:
            continue
        policy = proposed["material"]["policy"]
        approved, expires = (
            date.fromisoformat(value["approved_on"]),
            date.fromisoformat(value["expires_on"]),
        )
        if (
            approved <= today < expires
            and (expires - approved).days <= policy["max_age_days"]
            and value["approved_by_role"] in policy["approver_roles"]
        ):
            matches.append(value)
    if not matches:
        raise VariantError(
            "Approval missing, expired or changed; review the current fingerprint once"
        )
    return max(
        matches, key=lambda v: (v["approved_on"], v["expires_on"], v["approval_id"])
    )


def approved_status(root: Path, variant_id: str, environment: str, stage: str) -> dict:
    value = proposal(root, variant_id, environment, stage)
    try:
        receipt = current_approval(root, value)
        value.update(
            status="approved-project-variant",
            consumer_approval={
                "status": "valid",
                "approval_id": receipt["approval_id"],
                "expires_on": receipt["expires_on"],
            },
            human_confirmations_required=0,
        )
    except VariantError as exc:
        value["consumer_approval"] = {"status": "required", "reason": str(exc)}
    return value
