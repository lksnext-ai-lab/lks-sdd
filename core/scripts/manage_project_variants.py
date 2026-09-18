#!/usr/bin/env python3
"""Diagnose, approve and verify a project variant; defaults are read-only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from project_variants import (
    VariantError,
    STAGES,
    diagnose,
    approval_preview,
    apply_approval,
    approved_status,
    load_config,
)


def render(value: dict, detailed: bool) -> dict:
    if detailed:
        return value
    keys = {
        "status",
        "compatibility",
        "summary",
        "preview_hash",
        "fingerprint",
        "profile_id",
        "approval_id",
        "changed",
        "consumer_approval",
        "profile_certification",
        "verification_result",
        "delivery_readiness",
        "task_status",
        "evidence_id",
        "evidence_recorded",
        "human_confirmations_required",
        "processes_executed",
        "accounting",
        "limitations",
        "checks",
        "missing_critical_gates",
        "affected_gates",
        "unchanged_gates",
        "error",
        "reused",
        "execution_id",
        "checkpoint",
        "created",
        "updated",
        "functional_files_written",
    }
    result = {k: v for k, v in value.items() if k in keys}
    if "differences" in value:
        result["differences"] = value["differences"][:8]
        result["difference_count"] = len(value["differences"])
    if "material" in value:
        m = value["material"]
        result["decision"] = {
            "tasks": m["variant"]["task_ids"],
            "increment": m["variant"]["increment"],
            "release": m["variant"]["release"],
            "stage": m["stage"],
            "environment": m["environment"],
            "composition": m["variant"]["composition"],
            "differences": m["differences"][:8],
            "difference_count": len(m["differences"]),
        }
    if "receipt" in value:
        result["approval"] = {
            k: value["receipt"][k]
            for k in (
                "approved_by_role",
                "reason",
                "accepted_risks",
                "expires_on",
                "scope_limit",
            )
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for name in ("diagnose", "status", "preview", "approve", "prepare", "verify"):
        p = sub.add_parser(name)
        p.add_argument("project_root", type=Path)
        p.add_argument("--json", action="store_true")
        p.add_argument("--detail", action="store_true")
        if name == "diagnose":
            p.add_argument("--profile")
            continue
        p.add_argument("--variant", required=True)
        p.add_argument("--environment")
        p.add_argument("--stage", choices=STAGES, default="development")
        if name in {"preview", "approve"}:
            p.add_argument("--actor", required=True)
            p.add_argument("--reason", required=True)
            p.add_argument("--risks", required=True)
            p.add_argument("--expires", required=True)
        if name == "approve":
            p.add_argument("--apply", action="store_true", required=True)
            p.add_argument(
                "--authorize", required=True, help="Exact hash shown by preview"
            )
        if name == "prepare":
            p.add_argument("--actor", default="codex")
            p.add_argument("--at", help="Required explicit timestamp for a v2 preparation/start preview")
            p.add_argument("--apply", action="store_true")
            p.add_argument("--authorize", help="Exact preparation preview hash")
        if name == "verify":
            p.add_argument("--execute", action="store_true")
            p.add_argument("--containers", action="store_true")
            p.add_argument("--plan", action="store_true")
            p.add_argument("--record-evidence")
            p.add_argument("--force", action="store_true")
            p.add_argument("--rerun-reason")
            p.add_argument("--reuse-evidence")
            p.add_argument("--visual-evidence")
    args = parser.parse_args(argv)
    try:
        root = args.project_root.resolve()
        if args.operation == "diagnose":
            result = diagnose(root, args.profile)
        else:
            config = load_config(root)
            variant = next(
                (
                    v
                    for v in (config or {}).get("variants", [])
                    if v["id"] == args.variant
                ),
                None,
            )
            environment = args.environment or (variant or {}).get(
                "environment", "not-applicable"
            )
            if args.operation == "status":
                result = approved_status(root, args.variant, environment, args.stage)
            elif args.operation == "prepare":
                from variant_preparation import prepare

                if not variant or environment != variant["environment"]:
                    raise VariantError(
                        "Environment differs from variant preparation scope"
                    )
                from v2_cli import is_v2
                if is_v2(root):
                    if not args.at:
                        raise VariantError("v2 prepare requires --at so preview/apply bind identical inputs")
                    from v2_contract import load
                    from v2_lifecycle import start
                    result = start(load(root), variant["task_ids"], environment, actor=args.actor, at=args.at,
                                   authorized_hash=args.authorize if args.apply else None)
                else:
                    result = prepare(
                    root,
                    args.variant,
                    stage=args.stage,
                    actor=args.actor,
                    apply=args.apply,
                    preview_hash=args.authorize,
                )
            elif args.operation in {"preview", "approve"}:
                result = approval_preview(
                    root,
                    args.variant,
                    environment,
                    args.stage,
                    actor=args.actor,
                    reason=args.reason,
                    risks=args.risks,
                    expires=args.expires,
                )
                if args.operation == "approve":
                    result = apply_approval(root, result, args.authorize)
            else:
                if args.execute and args.plan:
                    raise VariantError("Choose plan or execute")
                from variant_verification import verify

                from v2_cli import is_v2
                if is_v2(root):
                    if args.force or args.reuse_evidence or args.visual_evidence:
                        raise VariantError("v2 uses typed exact-subject evidence and explicit result-review; no legacy override flags")
                    from v2_contract import load
                    from v2_verification import verify as verify_v2
                    result = verify_v2(load(root), variant["task_ids"], environment, args.stage,
                                       execute=args.execute, evidence_id=args.record_evidence, containers=args.containers)
                else:
                    result = verify(
                    root,
                    args.variant,
                    environment,
                    args.stage,
                    execute=args.execute,
                    evidence_id=args.record_evidence,
                    force=args.force,
                    rerun_reason=args.rerun_reason,
                    reuse_evidence=args.reuse_evidence,
                    visual_evidence=args.visual_evidence,
                )
        print(json.dumps(render(result, args.detail), indent=2, ensure_ascii=False))
        return (
            3
            if result.get("status") in {"approval-required", "not-verified"}
            or result.get("compatibility") == "incompatible"
            else 0
        )
    except (VariantError, OSError, ValueError, KeyError) as exc:
        from evidence_safety import sanitize

        message, _ = sanitize(str(exc))
        print(
            json.dumps(
                {"status": "blocked", "changed": False, "error": message},
                ensure_ascii=False,
            )
        )
        return 3


def forward_verify(argv: list[str]) -> int:
    """Public verify façade retains AUTH/EXEC and uses only explicitly selected variants."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--increment", required=True)
    parser.add_argument("--task", action="append", required=True)
    parser.add_argument("--execution-id")
    parser.add_argument("--environment")
    parser.add_argument("--stage", choices=STAGES, default="development")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorize", action="store_true")
    parser.add_argument("--record-evidence")
    parser.add_argument("--reuse-evidence")
    parser.add_argument("--visual-evidence")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rerun-reason")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args(argv)
    try:
        from project_variants import project_context

        root = args.project_root.resolve()
        config = load_config(root)
        variant = next(
            (v for v in (config or {}).get("variants", []) if v["id"] == args.variant),
            None,
        )
        if (
            not variant
            or set(args.task) != set(variant["task_ids"])
            or args.increment != variant["increment"]
        ):
            raise VariantError(
                "The explicit TASK/increment selection differs from the approved variant scope"
            )
        context = project_context(root, variant, execution=True)
        if (
            args.execution_id
            and args.execution_id != context["execution"]["execution_id"]
        ):
            raise VariantError("Different EXEC selected")
        if args.execute and not args.authorize:
            raise VariantError("Official execution needs --execute --authorize")
        forwarded = [
            "verify",
            str(root),
            "--variant",
            args.variant,
            "--stage",
            args.stage,
        ]
        if args.environment:
            forwarded += ["--environment", args.environment]
        if args.execute:
            forwarded += ["--execute"]
        if args.plan:
            forwarded += ["--plan"]
        if args.record_evidence:
            forwarded += ["--record-evidence", args.record_evidence]
        if args.reuse_evidence:
            forwarded += ["--reuse-evidence", args.reuse_evidence]
        if args.visual_evidence:
            forwarded += ["--visual-evidence", args.visual_evidence]
        if args.force:
            forwarded += ["--force"]
        if args.rerun_reason:
            forwarded += ["--rerun-reason", args.rerun_reason]
        if args.detail:
            forwarded += ["--detail"]
        return main(forwarded)
    except (VariantError, ValueError, OSError) as exc:
        print(json.dumps({"status": "blocked", "changed": False, "error": str(exc)}))
        return 3


if __name__ == "__main__":
    sys.exit(main())
