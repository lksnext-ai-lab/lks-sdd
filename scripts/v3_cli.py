"""Portable shared CLI for Codex and Copilot. Documents are data, never commands."""
import argparse
import json
from pathlib import Path
import sys

from v3_contract import ContractError, INDEX, element, load, canonical


def is_v3(root):
    try: return str(json.loads((Path(root)/INDEX).read_bytes()).get("schema_version", "")).startswith("3.")
    except (OSError, ValueError):
        # A broken/missing index must not route v3 Markdown into an older writer.
        directory = Path(root)/"docs/lks-sdd"
        if directory.exists():
            for path in directory.rglob("*.md"):
                if "history" in path.parts or "migrations" in path.parts: continue
                try:
                    if b'schema_version: "3.' in path.read_bytes()[:256]: return True
                except OSError: continue
        return False


def items(values):
    return [obj if "meta" in obj else element(obj["kind"], obj["title"], obj["body"], **obj.get("data", {})) for obj in values]


def execute(action, root, data):
    from v3_authoring import initialize, author, approve, approve_and_authorize, governance
    from v3_guidance import status, readiness, trace
    from v3_workflow import transition, exception, propose_exception
    from v3_team import assign, handoff
    from v3_quality import record, run_existing, findings
    from v3_verification import evidence, integrate, accept
    from v3_context import context
    from v3_migration import diagnose, preview as migration_preview, continuation, old_branch
    from v3_adoption import inspect, record as adopt
    from v3_lifecycle import review, revoke, checkpoint, reconcile_migrated
    actor = data.get("actor")
    if action == "configure-collaboration":
        from v31_review import configure
        return configure(root, actor, data["collaboration"], data["statement"], requests=data.get("requests", []),
                         coordination=data.get("coordination"), runtime_bundle=data.get("runtime_bundle"))
    if action in {"review-proposal", "close-proposal", "review-task", "review-comment", "resolve-comment", "review-exception"}:
        from v31_review import execute as review_execute
        return review_execute(action, root, data)
    if action == "interventions":
        from v31_guidance import interventions
        return interventions(load(root).require_valid(), data["request"], actor=actor, offset=data.get("offset", 0), limit=data.get("limit", 20), object_offset=data.get("object_offset", 0))
    if action == "reject-result":
        from v31_corrections import reject
        return reject(root, actor, data["request"], data["statement"], phase=data["phase"], tasks=data["tasks"],
                      expected=data["expected"], observed=data["observed"], artifact=data["artifact"], requirements=data.get("requirements", []), refresh=data.get("refresh", False))
    if action == "define-correction":
        from v31_corrections import define
        return define(root, actor, data["correction"], data["classification"], data["statement"], data["acceptance"],
                      tasks=data.get("tasks"), requirements=data.get("requirements"), refresh=data.get("refresh", False))
    if action == "resolve-defect":
        from v31_corrections import resolve
        return resolve(root, actor, data["problem"], data["statement"], refresh=data.get("refresh", False))
    if action == "prepare-delivery":
        from v31_corrections import delivery
        return delivery(root, actor, data["request"], data["statement"], pr_url=data.get("pr_url"), refresh=data.get("refresh", False))
    if action == "init":
        return initialize(root, data["name"], data["actor_name"], data["profile"], data["controls"], data["statement"], target=data["target"], lifecycle=data.get("lifecycle", "evolution"), members=data.get("members"))
    if action == "validate":
        model = load(root)
        return {"status": "valid" if not model.errors else "blocked", "errors": model.errors, "warnings": model.warnings, "elements": len(model.elements), "writes": []}
    if action == "status": return status(root, request_id=data.get("request"), task_id=data.get("task"), offset=data.get("offset", 0), limit=data.get("limit", 10), task_offset=data.get("task_offset", 0), task_limit=data.get("task_limit", 10))
    if action == "trace": return trace(root, data["uid"], offset=data.get("offset", 0), limit=data.get("limit", 20))
    if action == "context": return context(root, data["roots"], data.get("operation", "implement"), comparison=data.get("comparison", False))
    if action == "readiness":
        if data.get("request") and not data.get("task"):
            from v31_guidance import request_readiness
            return request_readiness(load(root).require_valid(), data["request"], actor, data.get("action", "close-proposal"))
        return readiness(root, data["task"], actor, data.get("action", "start"))
    if action == "review": return review(root, data["request"], data.get("units"))
    if action == "revoke": return revoke(root, actor, data["decision"], data["reason"])
    if action == "checkpoint": return checkpoint(root, actor, data["task"], data["result"], data.get("pending", []), classification=data.get("classification", "progress"), analysis=data.get("analysis"))
    if action == "migration-reconcile": return reconcile_migrated(root, actor, data["items"], data["statement"])
    if action == "author": return author(root, actor, items(data["items"]))
    if action == "approve": return approve(root, actor, data["units"], data["purpose"], data["statement"], reason=data.get("reason", ""))
    if action == "authorize-plan": return approve_and_authorize(root, actor, data["plan"], data["statement"], review_tasks=data.get("review_tasks", []))
    if action == "governance": return governance(root, actor, items(data["items"]), data["statement"], data["reason"], requests=data.get("requests", []))
    if action in {"start", "resume", "implement", "verify", "close", "pause", "cancel", "reopen"}:
        return transition(root, actor, data["task"], action, data["reason"], refresh=data.get("refresh", False), review=data.get("review", False), offer=data.get("offer"))
    if action == "exception": return exception(root, actor, data["task"], data["rule"], data["action"], data["reason"], data["expires_at"], revokes=data.get("revokes"))
    if action == "propose-exception": return propose_exception(root, actor, data["task"], data["rule"], data["action"], data["reason"], data["effect"])
    if action == "assign": return assign(root, actor, data["task"], data["recipient"], data["reason"], accept=data.get("accept", False), previous=data.get("previous"))
    if action == "handoff": return handoff(root, actor, data["task"], data["recipient"], data["scope"], data["reason"], previous=data.get("previous"), accept=data.get("accept", False))
    if action == "analysis": return record(root, actor, data["tasks"], data["tool"], data["report"])
    if action == "analysis-findings": return findings(root, data["analysis"], offset=data.get("offset", 0), limit=data.get("limit", 20))
    if action == "analysis-run": return run_existing(root, actor, data["tasks"], data["tool"], data["executable"], data["arguments"], retry_of=data.get("retry_of"))
    if action == "evidence": return evidence(root, actor, data["task"], data["tests"], data["outcome"], data["source"], data["artifact"], data["explanation"])
    if action == "integrate": return integrate(root, actor, data["request"], data["trusted_root"], data["statement"], refresh=data.get("refresh", False), accept_result=data.get("accept_result", False))
    if action == "accept": return accept(root, actor, data["request"], data["statement"])
    if action == "adopt-inspect": return inspect(root, data["paths"], data["purpose"])
    if action == "adopt": return adopt(root, actor, data["inspection"], data["observations"], data["confirmed_intent"], data["statement"])
    if action == "migration-diagnose": return diagnose(root)
    if action == "migration-preview":
        return migration_preview(root, data["actor_name"], data["profile"], data["controls"], data["statement"], target=data["target"], runtime_bundle=data.get("runtime_bundle"))
    if action == "migration-continuation": return continuation(root)
    if action == "old-branch": return old_branch(root, data["old_root"])
    if action == "catalog":
        model = load(root).require_valid(); entities = sorted(model.elements.values(), key=lambda e: (e.kind, e.uid))
        if data.get("kind"): entities = [e for e in entities if e.kind == data["kind"]]
        offset, limit = data.get("offset", 0), data.get("limit", 20)
        if offset < 0 or not 1 <= limit <= 100: raise ContractError("Página fuera de límites")
        return {"total": len(entities), "elements": [{**e.source(), "title": e.meta["title"]} for e in entities[offset:offset+limit]],
                "next_offset": offset+limit if offset+limit < len(entities) else None, "writes": []}
    if action == "history":
        model = load(root).require_valid(); e = model.at(data["uid"], data["digest"])
        return {"source": e.source(), "meta": e.meta, "text": e.body, "writes": []}
    if action == "reindex":
        from v3_storage import prepare
        load(root).require_valid(); return prepare(root, [], "reindex")
    raise ContractError("Operación v3 desconocida: " + action)


ACTIONS = ("configure-collaboration review-proposal close-proposal review-task review-comment resolve-comment review-exception interventions reject-result define-correction resolve-defect prepare-delivery "
           "init validate status trace context readiness review revoke checkpoint migration-reconcile author approve authorize-plan governance start resume implement verify close pause cancel reopen "
           "exception propose-exception assign handoff analysis analysis-run analysis-findings evidence integrate accept adopt-inspect adopt migration-diagnose migration-preview "
           "migration-continuation old-branch catalog history reindex apply recover rollback").split()


def main(argv=None, command=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if not command: parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--input", type=Path, help="Datos de la operación; nunca código ejecutable")
    parser.add_argument("--output", type=Path, help="Guardar paquete exacto completo y mostrar solo resumen")
    parser.add_argument("--apply", action="store_true", help="Aplicar dentro del alcance expresamente autorizado")
    parser.add_argument("--authorize", help="Hash exacto del paquete para apply/recover/rollback")
    parser.add_argument("--receipt")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv); action = command or args.action
    try:
        root = args.project_root.resolve()
        data = {}
        if args.input:
            if args.input.stat().st_size > 64*1024*1024: raise ContractError("Entrada excesiva")
            data = json.loads(args.input.read_bytes())
        from v3_storage import apply, recover
        if action == "apply":
            if not args.authorize: raise ContractError("Falta autorizar el paquete exacto")
            result = apply(root, data, args.authorize)
        elif action in {"recover", "rollback"}:
            if not args.authorize: raise ContractError("Falta identificar la operación a recuperar")
            result = recover(root, args.authorize, rollback=action == "rollback", receipt=args.receipt)
        else:
            result = execute(action, root, data)
            if args.apply and result.get("status") != "already-recorded":
                if "preview" not in result: raise ContractError("Esta operación es de solo lectura o ya está registrada")
                applied = apply(root, result, result["preview"]["preview_hash"])
                result = {**applied, "summary": result["summary"], "next": "Consulte el estado actualizado y continúe el siguiente paso ya autorizado"}
        if args.output:
            # Operational artifacts are explicitly selected output files, never hidden canonical state.
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(canonical(result) + b"\n")
            shown = {"output": str(args.output.resolve()), "status": result.get("status", "preview"),
                     "summary": result.get("summary"), "preview_hash": result.get("preview", {}).get("preview_hash")}
        elif "preview" in result:
            shown = {"status": "preview", "summary": result["summary"], "preview_hash": result["preview"]["preview_hash"],
                     "next": "Use --output para guardar el paquete completo, o --apply si esta operación ya está autorizada"}
        else: shown = result
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        return 2 if result.get("status") in {"blocked", "unsupported", "reconciliation-required"} else 0
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "cause": str(exc), "next": "Resuelva esta causa concreta; se conserva el trabajo existente"}, ensure_ascii=False))
        return 2


if __name__ == "__main__": sys.exit(main())
