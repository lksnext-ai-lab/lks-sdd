"""Human-facing v2 dispatcher. Mutations default to an exact, read-only preview."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from v2_contract import ContractError, DOCS, canonical, execution_context, load, path_at, read_bytes
from v2_storage import apply, recover


def is_v2(root: Path) -> bool:
    path = root / ".lks-sdd/project.json"
    if not path.is_file():
        return False
    return json.loads(read_bytes(root, ".lks-sdd/project.json")).get("schema_version") == "2.0"


def parser_for(command=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if command is None:
        parser.add_argument("command", choices=("init", "author", "catalog", "history", "validate", "context", "readiness",
            "authorize", "start", "diff", "review-diff", "checkpoint", "resume", "verify", "close", "status",
            "migration-diagnose", "migration-preview", "migration-status", "migration-continuation",
            "migrate", "rollback", "recover", "merge-preview", "guard", "adopt",
            "feature", "decompose", "rename-aliases", "revoke", "problem", "correct", "replan", "accept-result", "delivery", "authorize-delivery", "guard-review", "prepare",
            "tracking-status", "tracking-project", "tracking-authorize", "tracking-result", "tracking-reconcile", "tracking-milestone",
            "visual-request", "visual-inspect", "visual-observe", "visual-accept", "visual-cancel"))
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize", metavar="PREVIEW_HASH")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--name", default="")
    parser.add_argument("--project-id")
    parser.add_argument("--request", type=Path, help="Reviewed authoring request, JSON with Markdown documents")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--increment", help="Optional human selector; TASKs remain the execution scope")
    parser.add_argument("--environment", default="not-applicable")
    parser.add_argument("--actor", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--at")
    parser.add_argument("--expires-at")
    parser.add_argument("--reason", default="")
    parser.add_argument("--state", default="paused")
    parser.add_argument("--summary", default="")
    parser.add_argument("--next-action", default="")
    parser.add_argument("--diff-fingerprint")
    parser.add_argument("--stage", default="development")
    parser.add_argument("--evidence-id")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--containers", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--snapshot")
    parser.add_argument("--receipt")
    parser.add_argument("--id")
    parser.add_argument("--duplicate-check", choices=("matched", "no-match"))
    parser.add_argument("--target-runtime", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--incoming", type=Path)
    parser.add_argument("--source", action="append", default=[])
    return parser


def run(command, args):
    from query_sources import lexical_root
    root = lexical_root(args.project_root)
    if not root.is_dir():
        raise ContractError("Project root must already exist")
    if args.apply and (not args.authorize or args.dry_run or args.preview):
        raise ContractError("Apply requires the exact --authorize hash, without preview/dry-run")
    authorized = args.authorize if args.apply else None
    from v2_authoring import (initialize, author, commit, catalog, catalog_markdown, historical, export_catalog)
    from v2_lifecycle import (planning, authorize, start, diff_guard, review_diff, checkpoint, resume, now, semantic_merge)
    if command == "init":
        result, changes = initialize(root, args.name or args.project_id or "Proyecto", project_id=args.project_id)
        return apply(root, changes, result, authorized, validator=lambda: load(root).require_valid()) if args.apply else result
    if command in {"migration-diagnose", "migration-preview", "migration-status",
                   "migration-continuation", "migrate"}:
        from v2_migration import diagnose, plan, migrate, migration_status, continuation_status
        if command == "migration-diagnose":
            return diagnose(root)
        if command == "migration-status":
            return migration_status(root)
        if command == "migration-continuation":
            return continuation_status(root, args.task)
        if command == "migrate" and args.apply:
            return migrate(root, authorized, target_runtime=args.target_runtime)
        return plan(root, target_runtime=args.target_runtime)[0]
    if command in {"rollback", "recover"}:
        if not args.apply:
            raise ContractError("Recovery changes files; require --apply --authorize TRANSACTION_HASH")
        return recover(root, authorized, rollback=command == "rollback", receipt=args.receipt)
    if command == "adopt":
        from v2_adoption import adopt
        return adopt(root, args.source, name=args.name, description=args.summary, authorized_hash=authorized)
    from v2_migration import migration_status
    cutover = migration_status(root)
    if cutover["status"] == "blocked" and command not in {"validate", "status", "catalog", "context", "readiness"}:
        raise ContractError("; ".join(cutover.get("errors", ["Project migration is blocked"])))
    model = load(root)
    if command == "guard-review":
        from v2_integration_guard import review
        if not args.incoming:
            raise ContractError("Select independent --incoming worktree")
        return review(root, args.incoming, args.task, read_request(args.request), authorized_hash=authorized)
    if command == "authorize-delivery":
        from v2_controls import authorize_delivery
        return authorize_delivery(model, read_request(args.request), authorized_hash=authorized)
    if args.increment and any(t not in model.elements or args.increment not in model.elements[t].targets("increment") for t in args.task):
        raise ContractError("TASK selector does not match the requested increment")
    if command == "validate":
        return {"status": "valid" if model.valid else "invalid", "valid": model.valid,
                "schema_version": "2.0", "errors": model.errors, "warnings": model.warnings,
                "checked_files": sorted(model.hashes), "writes": []}
    if command == "status":
        diagnostics = list(model.errors) + list(cutover.get("errors", []))
        return {"status": "documented" if model.valid and cutover["status"] != "blocked" else "blocked",
                "project": model.manifest.get("name"),
                "migration": cutover,
                "features": len(model.by_kind("feature")),
                "tasks": [{"id": t.id, "title": t.meta["title"], "state": t.meta["state"],
                           "health": t.meta.get("health", "unknown"), "evidence": t.meta.get("evidence_ids", [])} for t in model.by_kind("task")],
                "problems": [{"id": p.id, "state": p.meta["state"], "description": p.body} for p in model.by_kind("problem")],
                "delivery": "not-assessed", "diagnostics": diagnostics, "writes": []}
    if command == "author":
        if not args.request:
            raise ContractError("Author requires a reviewed --request file")
        request = read_request(args.request)
        return commit(model, request, authorized) if args.apply else author(model, request)[0]
    if command == "catalog":
        return export_catalog(model, authorized) if args.export else catalog(model)
    if command == "history":
        if not args.snapshot:
            raise ContractError("History requires an exact --snapshot")
        return historical(root, args.snapshot)
    if command == "context":
        return execution_context(model, args.task)
    if command == "readiness":
        return planning(model, args.task)
    if command == "authorize":
        if not args.at or not args.expires_at:
            raise ContractError("Use explicit --at and --expires-at so preview/apply have identical inputs")
        return authorize(model, args.task, actor=args.actor, role=args.role, environment=args.environment,
                         approved_at=args.at, expires_at=args.expires_at, reason=args.reason, authorized_hash=authorized)
    if command == "start":
        if not args.at or not args.actor:
            raise ContractError("Start requires explicit --at and --actor")
        return start(model, args.task, args.environment, actor=args.actor, at=args.at, authorized_hash=authorized)
    if command == "diff":
        return diff_guard(model)
    if command == "review-diff":
        return review_diff(model, actor=args.actor, reason=args.reason, observed_diff=args.diff_fingerprint, authorized_hash=authorized)
    if command == "checkpoint":
        if not args.at:
            raise ContractError("Checkpoint requires explicit --at")
        return checkpoint(model, state=args.state, actor=args.actor, at=args.at, summary=args.summary,
                          next_action=args.next_action, authorized_hash=authorized)
    if command == "resume":
        return resume(model, args.task)
    if command in {"verify", "close"}:
        from v2_verification import verify, close
        if command == "verify":
            return verify(model, args.task, args.environment, args.stage, evidence_id=args.evidence_id, execute=args.execute, containers=args.containers)
        if not args.at:
            raise ContractError("Close requires explicit --at")
        return close(model, args.task, args.evidence_id, actor=args.actor, at=args.at, authorized_hash=authorized)
    if command == "merge-preview":
        if not args.base or not args.incoming:
            raise ContractError("Provide --base and --incoming project roots")
        return semantic_merge(load(args.base), load(args.incoming), model)
    if command == "guard":
        if not args.base:
            raise ContractError("Guard requires an independently trusted --base")
        from v2_integration_guard import assess
        return assess(args.base, root, args.task)
    if command in {"feature", "rename-aliases", "decompose"}:
        from v2_features import create, rename_aliases, decomposition
        if command == "decompose":
            return decomposition(model, args.id)
        return (create if command == "feature" else rename_aliases)(model, read_request(args.request), authorized_hash=authorized)
    if command == "prepare":
        from v2_preparation import prepare
        return prepare(model, args.task, args.environment, authorized_hash=authorized)
    if command == "problem":
        from v2_lifecycle import report_problem
        if not args.at:
            raise ContractError("Problem requires explicit --at")
        return report_problem(model, args.task, description=args.reason, actor=args.actor, at=args.at, authorized_hash=authorized)
    if command in {"revoke", "correct", "replan", "accept-result", "delivery"}:
        from v2_controls import revoke, correction, accept_result, delivery_observation
        if command == "delivery":
            return delivery_observation(model, read_request(args.request), authorized_hash=authorized)
        if not args.at:
            raise ContractError("Transition requires explicit --at")
        common = dict(actor=args.actor, at=args.at, reason=args.reason, authorized_hash=authorized)
        if command == "revoke":
            return revoke(model, args.id, **common)
        if command == "accept-result":
            return accept_result(model, args.task, args.evidence_id, **common)
        return correction(model, args.task, replan=command == "replan", **common)
    if command.startswith("tracking-"):
        from v2_tracking import readiness, projection, authorize_projection, record_result
        if command == "tracking-status":
            return readiness(model, args.task)
        if command == "tracking-milestone":
            from v2_tracking import milestone
            if len(args.task) != 1:
                raise ContractError("Select one TASK for milestone reporting")
            return milestone(model, args.task[0], read_request(args.request), authorized_hash=authorized)
        if command in {"tracking-project", "tracking-authorize"}:
            if len(args.task) != 1:
                raise ContractError("Select exactly one TASK per remote receipt")
            if command == "tracking-project":
                return projection(model, args.task[0])
            if not args.at:
                raise ContractError("Projection authorization requires explicit --at")
            return authorize_projection(model, args.task[0], actor=args.actor, at=args.at,
                                        duplicate_check=args.duplicate_check, authorized_hash=authorized)
        return record_result(model, args.id, read_request(args.request), reconcile=command == "tracking-reconcile", authorized_hash=authorized)
    if command.startswith("visual-"):
        from v2_visual import request, inspect, observe, accept, cancel
        if command == "visual-cancel":
            return cancel(model, args.id, read_request(args.request), authorized_hash=authorized)
        if command == "visual-inspect":
            return inspect(model, args.id)
        if command == "visual-request":
            return request(model, read_request(args.request), authorized_hash=authorized)
        if command == "visual-accept":
            return accept(model, args.id, read_request(args.request), authorized_hash=authorized)
        return observe(model, args.id, read_request(args.request), authorized_hash=authorized)
    raise ContractError("Unsupported v2 command")


def read_request(path):
    if path is None or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise ContractError("An explicit bounded --request JSON file is required")
    from query_sources import is_link
    if is_link(path):
        raise ContractError("Request must not be a link/junction")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError("Request must be an object")
    return value


def human_status(value):
    lines = ["# Estado del proyecto", "", f'Funcionalidades documentadas: {value["features"]}.', "",
             "| Tarea | Estado de trabajo | Salud |", "|---|---|---|"]
    for task in value["tasks"]:
        title = task["title"].replace("|", "\\|").replace("\n", " ")
        lines.append(f'| {task["id"]} · {title} | {task["state"]} | {task["health"]} |')
    lines += ["", "La implementación, la verificación y la entrega se evalúan por separado.",
              "Entrega: no evaluada. Consulte el catálogo o solicite detalle de una funcionalidad."]
    if value["diagnostics"]:
        lines += ["", "Incidencias documentales:", *["- " + d for d in value["diagnostics"]]]
    return "\n".join(lines)


def main(argv=None, *, command=None):
    args = parser_for(command).parse_args(argv)
    command = command or args.command
    try:
        value = run(command, args)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        value = {"status": "blocked", "error": str(exc), "writes": []}
    if command == "catalog" and not args.json and not args.export and value.get("status") != "blocked":
        from v2_authoring import catalog_markdown
        print(catalog_markdown(load(args.project_root)))
    elif not args.json and value.get("status") == "blocked":
        print("No se puede continuar: " + value.get("error", "; ".join(value.get("blockers", value.get("missing_critical_gates", []))) or value.get("reason", "Revise el diagnóstico.")))
    elif command == "status" and not args.json:
        print(human_status(value))
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    return 2 if value.get("status") in {"blocked", "invalid", "conflict"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
