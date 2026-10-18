"""Portable shared CLI for Codex and Copilot. Documents are data, never commands."""
from v3_presentation_guard import reviewed
import argparse
import json
from pathlib import Path
import sys
from functools import wraps

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
                    with path.open("rb") as stream:
                        if b'schema_version: "3.' in stream.read(256): return True
                except OSError: continue
        return False


def items(values):
    return [obj if "meta" in obj else element(obj["kind"], obj["title"], obj["body"], **obj.get("data", {})) for obj in values]


@reviewed()
def _execute(action, root, data, *, apply_work=False):
    from v3_current import READ_ONLY, SPECIAL, require_current
    if action not in READ_ONLY | SPECIAL | {"work-continue", "work-record-results"}: require_current(root, data)
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
    if action in {"work-continue", "work-record-results"}:
        from v4_work_operations import run
        return run(root, action, data, apply=apply_work)
    if action == "work-prepare":
        from v4_work_prepare import prepare
        return prepare(root,data)
    if action == "usage-record":
        if data.get("capture_dir"):
            from diagnostic_capture import record as capture_record
            return capture_record(root,data)
        from v3_usage import record
        return record(root, data)
    if action == "usage-report":
        if data.get("capture_dir"):
            from diagnostic_capture import imported_window
            from usage_report import report
            value,rows,_=imported_window(data["capture_dir"],root,entry_ids=data.get("capture_entries"))
            return report(rows,selector={"run_id":value["header"]["run_id"]},offset=data.get("offset",0),limit=data.get("limit",100),finding_id=data.get("finding_id"))
        from usage_report import query
        return query(root, data)
    if action == "usage-export":
        from usage_bundle import preview, export
        if data.get("destination"):
            return export(data["packet"], data["destination"], data["export_hash"], consumer=root)
        if data.get("capture_dir"):
            from diagnostic_capture import export_data
            return preview(export_data(root,data))
        from v3_usage import catalog
        from content_store import read_object
        rows = catalog(load(root).require_valid(), run_id=data.get("run_id"), request=data.get("request"), task=data.get("task"))
        materials = dict(data.get("materials", {}))
        for row in rows:
            for f in row["fragments"]:
                if "text_ref" in f or "data_ref" in f:
                    path = "sources/" + f["sha256"] + (".bin" if f.get("unit") == "bytes" else ".txt")
                    content = read_object(root,f.get("text_ref",f.get("data_ref")))
                    if f.get("unit") == "bytes":
                        import base64
                        raw = {"encoding":"base64","data":base64.b64encode(content).decode("ascii")}
                    else: raw = content.decode("utf-8")
                    if path in materials and materials[path] != raw: raise ContractError("Conflicting export material")
                    materials[path] = raw
        return preview({**data, "observations": rows, "materials":materials})
    if action == "decision-view":
        from v3_decision_presentation import decision_view
        if set(data) - {"event", "data"}: raise ContractError("decision-view admite únicamente event y data")
        return decision_view(root, data["event"], data.get("data", {}))
    if action == "configure-collaboration":
        from v31_review import configure
        return configure(root, actor, data["collaboration"], data["statement"], requests=data.get("requests", []),
                         coordination=data.get("coordination"), runtime_bundle=data.get("runtime_bundle"), pin_runtime=True,
                         packet_directory=data.get("packet_directory"))
    if action in {"review-proposal", "close-proposal", "review-task", "review-comment", "resolve-comment", "review-exception"}:
        from v31_review import execute as review_execute
        return review_execute(action, root, data)
    if action == "interventions":
        from v31_guidance import interventions
        return interventions(load(root).require_valid(), data["request"], actor=actor, offset=data.get("offset", 0), limit=data.get("limit", 20), object_offset=data.get("object_offset", 0))
    if action == "reject-result":
        from v31_corrections import reject
        return reject(root, actor, data["request"], data["statement"], phase=data["phase"], tasks=data["tasks"],
                      expected=data["expected"], observed=data["observed"], artifact=data.get("artifact"), requirements=data.get("requirements", []), refresh=data.get("refresh", False))
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
        return initialize(root, data["name"], data["actor_name"], data["profile"], data["controls"], data["statement"], target=data["target"], lifecycle=data.get("lifecycle", "evolution"), members=data.get("members"), method="3.1.0", collaboration=data.get("collaboration"), runtime_bundle=data.get("runtime_bundle"), packet_directory=data.get("packet_directory"))
    if action == "validate":
        model = load(root)
        return {"status": "valid" if not model.errors else "blocked", "errors": model.errors, "warnings": model.warnings, "elements": len(model.elements), "writes": []}
    if action == "status": return status(root, request_id=data.get("request"), task_id=data.get("task"), offset=data.get("offset", 0), limit=data.get("limit", 10), task_offset=data.get("task_offset", 0), task_limit=data.get("task_limit", 10))
    if action == "trace": return trace(root, data["uid"], offset=data.get("offset", 0), limit=data.get("limit", 20))
    if action == "context": return context(root, data["roots"], data.get("operation", "implement"), comparison=data.get("comparison", False), reference=data.get("reference", False))
    if action == "readiness":
        # A read-only readiness query must describe the actual public operating
        # boundary, including a required cutover, before suggesting execution.
        try: require_current(root, data)
        except ContractError as exc:
            result = {"status": "blocked", "causes": [str(exc)], "writes": [],
                      "next": "Prepare migration-preview with confirmed configuration and compatible runtime_bundle"}
            if data.get("request") or data.get("task"):
                # Preserve the factual journey while reporting that this runtime
                # cannot yet authorize the proposed public operation.
                try:
                    from v31_guidance import interventions
                    model = load(root).require_valid()
                    key = data.get("request") or model.get(data["task"], "task").data["request"]
                    result["journey"] = interventions(model, key, actor=actor)
                except ContractError: pass
            return result
        if data.get("request") and not data.get("task"):
            from v31_guidance import request_readiness
            return request_readiness(load(root).require_valid(), data["request"], actor, data.get("action", "close-proposal"))
        return readiness(root, data["task"], actor, data.get("action", "start"))
    if action == "review": return review(root, data["request"], data.get("units"))
    if action == "revoke": return revoke(root, actor, data["decision"], data["reason"])
    if action == "checkpoint": return checkpoint(root, actor, data["task"], data["result"], data.get("pending", []), classification=data.get("classification", "progress"), analysis=data.get("analysis"), operation_id=data.get("operation_id"))
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
    if action == "migration-diagnose":
        from v3_current import diagnose as current_diagnose
        return current_diagnose(root, include_inventory=data.get("include_inventory", False))
    if action == "migration-preview":
        from v3_current import upgrade
        return upgrade(root, data)
    if action == "migration-continuation": return continuation(root)
    if action == "old-branch": return old_branch(root, data["old_root"])
    if action == "catalog":
        model = load(root).require_valid()
        if data.get("kind") == "scope":
            from v3_scope import scope_preview
            return scope_preview(model, data["roots"], data.get("proposals", []),
                                 offset=data.get("offset", 0), limit=data.get("limit", 20))
        if data.get("kind") == "prose":
            from v3_scope import prose_catalog
            return prose_catalog(model, data.get("offset", 0), data.get("limit", 20))
        entities = sorted(model.elements.values(), key=lambda e: (e.kind, e.uid))
        if data.get("kind"): entities = [e for e in entities if e.kind == data["kind"]]
        offset, limit = data.get("offset", 0), data.get("limit", 20)
        if offset < 0 or not 1 <= limit <= 100: raise ContractError("Página fuera de límites")
        return {"total": len(entities), "elements": [{**e.source(), "title": e.meta["title"]} for e in entities[offset:offset+limit]],
                "next_offset": offset+limit if offset+limit < len(entities) else None, "writes": []}
    if action == "history":
        model = load(root).require_valid(); e = model.at(data["uid"], data["digest"])
        return {"source": e.source(), "meta": e.meta, "text": e.body, "writes": []}
    if action == "state-history":
        from document_state import export, manifest
        if data.get("destination"): return export(root, data["state"], data["destination"])
        value = manifest(root, data["state"])
        return {"state": data["state"], "files": value["files"], "writes": []}
    if action == "reindex":
        from v3_storage import prepare
        load(root).require_valid(); return prepare(root, [], "reindex")
    raise ContractError("Operación v3 desconocida: " + action)


ACTIONS = ("decision-view configure-collaboration review-proposal close-proposal review-task review-comment resolve-comment review-exception interventions reject-result define-correction resolve-defect prepare-delivery "
           "init validate status trace context readiness review revoke checkpoint migration-reconcile author approve authorize-plan governance start resume implement verify close pause cancel reopen "
           "exception propose-exception assign handoff analysis analysis-run analysis-findings evidence integrate accept adopt-inspect adopt migration-diagnose migration-preview "
           "migration-continuation old-branch catalog history state-history reindex apply recover rollback usage-record usage-report usage-export work-prepare work-continue work-record-results store-preview store-compact store-recover").split()


@reviewed()
def _execute_persist(action, root, data, *, apply_work=False):
    from v3_packet import persist
    from v3_current import READ_ONLY
    if action in READ_ONLY:
        from v3_contract import query_evaluation
        with query_evaluation():
            return persist(_execute(action, root, data, apply_work=apply_work))
    return persist(_execute(action, root, data, apply_work=apply_work))


@wraps(_execute_persist)
def execute(action, root, data, **kwargs):
    # The existing read-only snapshot also validates the observation's binding.
    # Mutations keep their normal fresh loads and guards.
    from v3_current import READ_ONLY
    if action in READ_ONLY:
        from v3_contract import query_evaluation
        with query_evaluation(): return _observed_execute(action,root,data,**kwargs)
    return _observed_execute(action,root,data,**kwargs)


def _observed_execute(action, root, data, **kwargs):
    """One observation at the shared boundary; transport never enters authority."""
    import time
    from v3_usage import session, observe
    data = dict(data)
    context = data.pop("usage_context", {})
    if action.startswith("usage-"): return _execute_persist(action, root, data, **kwargs)
    start = time.monotonic()
    try:
        with session(context, data) as usage_session: result = _execute_persist(action, root, data, **kwargs)
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        failure = {"status": "blocked", "cause": str(exc)}
        try:
            from usage_report import report
            rows = [observe(action, data, failure, context=context if isinstance(context,dict) else {}, elapsed=time.monotonic()-start, root=root)]
            value = report(rows)
            exc.usage = {"observations":rows, "summary":value["summary"], "prompt":value["prompt"]}
        except (ContractError, OSError, ValueError, KeyError, TypeError) as diagnostic_error:
            exc.usage = {"status":"incomplete","cause":str(diagnostic_error),"quality":"unchanged","observations":[]}
        raise
    try:
        row_context=context
        if action=="work-prepare" and result.get("basis") and isinstance(context,dict):
            row_context={**context,"tasks":result["portion"]["requested"]}
        row_stage = None
        if action in {"work-continue", "work-record-results"}:
            row_stage = ("applied" if kwargs.get("apply_work") and result.get("effects") else
                         "prepared" if result.get("status") == "ready" else
                         "failed" if result.get("status") in {"blocked", "partial"} else "query")
        row = observe(action, data, result, context=row_context, elapsed=time.monotonic()-start, root=root, stage=row_stage)
        result["usage"] = {"observations": [row], "continuation": "Conserve the envelope at the next authorized useful milestone; reuse run_id"}
        if usage_session.get("deferred"):
            result["usage"].update(conservation="deferred-until-project-valid", pending_observations=context["observations"])
        if action in {"implement", "verify", "prepare-delivery"} or result.get("status") == "blocked":
            from usage_report import report
            from v3_usage import catalog
            prior = context.get("observations", [])
            try:
                stored = catalog(load(root).require_valid(), run_id=row["run_id"])
                saved_ids = {r["observation_id"] for r in stored}
                prior = stored + [r for r in prior if r["observation_id"] not in saved_ids]
            except ContractError: pass  # Invalid project: transient envelope remains exportable.
            report_value = report(prior + [row])
            result["usage"]["summary"] = report_value["summary"]
            result["usage"]["prompt"] = report_value["prompt"]
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        result["usage"] = {"status": "incomplete", "cause": str(exc), "quality": "unchanged"}
    return result


def presentation_output(action, result):
    """One literal presentation body; library/export results keep all detail."""
    from v3_decision_presentation import compact
    if action in {"work-continue", "work-record-results"}:
        return {k: v for k, v in result.items() if k != "packet"}
    if action == "decision-view": return compact(result)
    if action == "store-preview" and isinstance(result.get("manifest"), dict):
        from store_compaction import summary
        return {"status": result["status"], "preview_hash": result["preview_hash"],
                "summary": summary(result["manifest"]),
                "next": "Use --output outside backup/restore/staging to retain the full manifest before authorization"}
    if action == "review":
        shown = {k: v for k, v in result.items() if k not in {"units", "presentation"}}
        shown["units"] = [{k: v for k, v in unit.items() if k not in {"description", "details"}}
                          for unit in result["units"]]
        shown["presentation"] = compact(result["presentation"])
        return shown
    return result


def display_summary(value):
    if not isinstance(value, dict): return value
    shown = {key: entry for key, entry in value.items() if key != "mapping"}
    if "mapping" in value: shown["mapped_identities"] = len(value["mapping"])
    return shown


def main(argv=None, command=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if not command: parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--input", type=Path, help="Datos de la operación; nunca código ejecutable")
    parser.add_argument("--output", type=Path, help="Guardar resultado o paquete completo y mostrar su referencia")
    parser.add_argument("--apply", action="store_true", help="Aplicar dentro del alcance expresamente autorizado")
    parser.add_argument("--authorize", help="Hash exacto del paquete para apply/recover/rollback")
    parser.add_argument("--authorize-removal", help="Autorización separada del hash exacto para retirar duplicados físicos")
    parser.add_argument("--status", dest="store_status", action="store_true", help="Consultar mantenimiento sin escribir ni autorizar")
    parser.add_argument("--finalize-without-removal", action="store_true", help="Cerrar mantenimiento conservando todos los originales; requiere su hash exacto")
    parser.add_argument("--receipt")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--view", choices=("compatible", "operational"), default="compatible",
                        help="compatible conserva el comportamiento anterior; operational evita duplicación diagnóstica")
    parser.add_argument("--capture-dir",type=Path,help="Captura diagnóstica explícita en una ventana externa al consumidor")
    parser.add_argument("--activity", action="store_true", help="Actividad optativa por stderr; no acredita avance ni porcentaje")
    transport = parser.add_mutually_exclusive_group()
    transport.add_argument("--details", action="store_true", help="Incluir fuentes, secciones y diagnóstico completo")
    transport.add_argument("--compact", action="store_true", help="Un solo cuerpo de presentación, también con --json")
    args = parser.parse_args(argv); action = command or args.action
    from v4_activity import session
    with session(action, activity=args.activity):
        return _main(args, action, argv)


def _main(args, action, argv):
    from v4_activity import checkpoint, phase, OperationInterrupted
    capture=None; capture_error=None; input_raw=None; captured_output=None
    try:
        phase("prepare")
        root = args.project_root.resolve()
        data = {}
        if action=="work-prepare" and args.apply:raise ContractError("work-prepare is read-only; apply requires an existing transition preview")
        if args.capture_dir:
            try:
                from diagnostic_capture import Capture
                capture=Capture(args.capture_dir,root)
            except (ContractError,OSError,ValueError,TypeError,KeyError) as exc: capture_error=str(exc)
        from v3_cli_presentation import export_path, export_summary, write_export, json_text, completed_work_view
        operational_output=args.view=="operational" and not args.details
        output = export_path(args.output, root, args.input) if args.output else None
        if args.capture_dir and args.output: export_path(args.output,args.capture_dir,args.input)
        if args.input:
            if args.input.stat().st_size > 64*1024*1024: raise ContractError("Entrada excesiva")
            from v3_packet import read as read_packet
            if args.capture_dir:
                from v3_contract import read_bytes
                source=args.input.resolve()
                input_raw=read_bytes(source.parent,source.name,limit=64*1024*1024,package_data=True)
            data = read_packet(args.input,raw=input_raw)
        if args.capture_dir and not capture_error:
            try:
                from diagnostic_capture import Capture
                context=data.get("usage_context",{})
                capture=Capture(args.capture_dir,root,context.get("run_id") if isinstance(context,dict) else None)
                if not action.startswith("usage-") and action not in {"apply","recover","rollback"} and isinstance(context,dict):
                    data["usage_context"]={**context,"run_id":capture.run_id}
            except (ContractError,OSError,ValueError,TypeError,KeyError) as exc: capture_error=str(exc)
        from v3_storage import apply, recover
        if (args.store_status or args.finalize_without_removal) and action != "store-recover":
            raise ContractError("--status y --finalize-without-removal requieren store-recover")
        if action.startswith("store-"):
            from store_maintenance import preview as store_preview, apply as store_apply, recover as store_recover
            from store_compaction import transport_guard, is_v2_input
            if args.apply: raise ContractError("Use la operación de almacenamiento explícita y sus hashes")
            transport_guard(root, action, data, args.authorize, output)
            if action == "store-preview":
                if args.authorize or args.authorize_removal: raise ContractError("El preview no autoriza retiradas")
                if ("backup" in data) == ("backup_dir" in data):
                    raise ContractError("Indique exactamente uno de backup o backup_dir")
                if "backup_dir" in data:
                    from store_compaction import preview as store_preview
                    result = store_preview(root, data['backup_dir'], data['restore'])
                else:
                    result = store_preview(root, data['backup'], data['restore'])
                if is_v2_input(result):
                    transport_guard(root, "store-compact", result, result['preview_hash'], output)
            elif action == "store-compact":
                if args.authorize_removal: raise ContractError("Verifique respaldo y restauración antes de autorizar retirada")
                if is_v2_input(data):
                    from store_compaction import apply as store_apply
                result = store_apply(root, data, args.authorize)
            else:
                from store_compaction import pending_v2
                if pending_v2(root, args.authorize):
                    from store_compaction import recover as store_recover, status as store_status
                    if args.store_status:
                        if args.authorize_removal or args.finalize_without_removal:
                            raise ContractError("Consultar estado no autoriza ni finaliza mantenimiento")
                        result = store_status(root, args.authorize)
                    else:
                        result = store_recover(root, args.authorize, remove_authorized=args.authorize_removal,
                                               finalize_without_removal=args.finalize_without_removal)
                else:
                    if args.store_status or args.finalize_without_removal:
                        raise ContractError("Estas opciones requieren mantenimiento /2")
                    result = store_recover(root, args.authorize, remove_authorized=args.authorize_removal)
        elif action == "apply":
            if not args.authorize: raise ContractError("Falta autorizar el paquete exacto")
            result = apply(root, data, args.authorize, current=True)
        elif action in {"recover", "rollback"}:
            if not args.authorize: raise ContractError("Falta identificar la operación a recuperar")
            result = recover(root, args.authorize, rollback=action == "rollback", receipt=args.receipt)
        else:
            composed = action in {"work-continue", "work-record-results"}
            result = execute(action, root, data, **({"apply_work": args.apply} if composed else {}))
            if args.apply and not composed and result.get("status") != "already-recorded":
                if "preview" not in result: raise ContractError("Esta operación es de solo lectura o ya está registrada")
                prepared_usage = result.get("usage", {})
                prepared_rows = prepared_usage.get("observations", [])
                applied = apply(root, result, result["preview"]["preview_hash"], current=True)
                result = {**applied, "summary": result["summary"], "next": "Consulte el estado actualizado y continúe el siguiente paso ya autorizado"}
                if not action.startswith("usage-"):
                    from v3_usage import observe
                    result["usage"] = {**prepared_usage, "observations": prepared_rows + [observe(action, {k:v for k,v in data.items() if k != "usage_context"},
                        {**result, "preview": {"preview_hash": applied["preview_hash"]}},
                        context=data.get("usage_context",{}), invocation_id=prepared_rows[0]["invocation_id"] if prepared_rows else None,
                        stage="applied",root=root)]}
        # Prepare application observations before an explicit export so the file
        # also contains the diagnostic rows referenced by the printed view.
        phase("output")
        if action in {"apply", "recover", "rollback"} and "usage" not in result:
            from v3_usage import observe
            result["usage"] = {"observations": [observe(action, {"preview_hash": args.authorize}, result,
                context={"run_id":capture.run_id} if capture else None,
                stage="applied" if result.get("status") in {"applied", "previously-applied", "completed", "rolled-back"} else None)]}
        if args.output:
            # Operational artifacts are explicitly selected output files, never hidden canonical state.
            if "preview" in result:
                from v3_packet import save
                if not (hasattr(result, "base") and output == result.base/"packet.json"):
                    result = save(result, output)
            else:
                write_export(result, output)
            captured_output=output
            shown = {**export_summary(result, output), "summary": display_summary(result.get("summary"))}
        elif "preview" in result:
            shown = {"status": "preview", "summary": display_summary(result["summary"]), "preview_hash": result["preview"]["preview_hash"],
                     "next": "Use --output para guardar el paquete completo, o --apply si esta operación ya está autorizada"}
            if hasattr(result, "base"): shown["packet"] = str(result.base/"packet.json")
        else: shown = {**result, "summary": display_summary(result["summary"])} if "summary" in result else result
        if not args.output and not args.details and (args.view == "operational" or args.compact or not args.json) and "preview" not in result:
            shown = presentation_output(action, result)
            if operational_output:shown=completed_work_view(action,shown)
        if not action.startswith("usage-"):
            from v3_usage import observe
            if result.get("usage"):
                from v3_contract import sha
                body = {k:v for k,v in shown.items() if k != "usage"}
                raw_body = json_text(body,operational=operational_output).encode("utf-8")
                transport = {"mode": "output-file" if args.output else "details" if args.details else "compact" if args.compact else "default",
                    "requested_display":"details" if args.details else "compact" if args.compact else "default",
                    "prepared_bytes": len(raw_body), "prepared_sha256": sha(raw_body),
                    "coverage":"prepared display body excluding diagnostic envelope; output file includes full API payload", "host_received": "unobserved"}
                if args.view == "operational":
                    transport["view"] = "operational"
                    if not args.output and not args.details:
                        transport.update(mode="operational", requested_display="operational")
                if args.output:
                    from path_utils import filesystem_root
                    raw_file = filesystem_root(args.output).read_bytes()
                    transport["prepared_file"] = {"bytes":len(raw_file),"sha256":sha(raw_file),"coverage":"exact output descriptor; referenced packet objects remain in its inventory"}
                result["usage"]["transport"] = transport
                for row in result["usage"].get("observations",[]): row["output"] = transport
                shown = {**shown, "usage": result["usage"]}
        if args.view == "operational" and (args.output or not args.details) and "usage" in shown:
            from v3_cli_presentation import usage_view
            shown = {**shown, "usage": usage_view(shown["usage"], exported=args.output.resolve() if args.output else None)}
        if args.capture_dir:
            from diagnostic_capture import emit
            phase("capture")
            emit(shown,result,capture,capture_error,argv=list(argv if argv is not None else sys.argv[1:]),input_raw=input_raw,input_data=data,output_file=captured_output,compact_output=operational_output)
        else:
            checkpoint()
            sys.stdout.write(json_text(shown,operational=operational_output))
        if result.get("interruption"): return 3 if result.get("effects") or result.get("recovery") else 130
        if action=="work-prepare":return 0 if result.get("status")=="ready" else 3 if result.get("status")=="partial" else 2
        if action in {"work-continue", "work-record-results"}:
            return 0 if result.get("status") in {"ready", "completed"} else 3 if result.get("status") == "partial" else 2
        if action.startswith("store-") and result.get("status") == "paused": return 3
        return 2 if result.get("status") in {"blocked", "unsupported", "reconciliation-required", "rejected-stale-preview"} else 0
    except (OperationInterrupted, ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        failure = {"status": "blocked", "cause": str(exc), "next": "Resuelva esta causa concreta; se conserva el trabajo existente"}
        if isinstance(exc, OperationInterrupted):
            failure.update(status="interrupted", interruption=exc.interruption,
                           next="Inspect preserved receipts and technical artifacts; retry only the exact authorized intent")
        if not action.startswith("usage-"):
            from v3_usage import observe
            from usage_report import report
            actual_data = locals().get("data", {})
            observed_result = locals().get("result", {})
            if observed_result.get("preview"): failure["preview"] = {"preview_hash":observed_result["preview"]["preview_hash"]}
            elif action == "apply" and actual_data.get("preview",{}).get("preview_hash"):
                failure["preview"] = {"preview_hash":actual_data["preview"]["preview_hash"]}
            usage = getattr(exc, "usage", None)
            if usage is None:
                try:
                    usage = {"observations":observed_result.get("usage",{}).get("observations",[]) +
                        [observe(action, {k:v for k,v in actual_data.items() if k != "usage_context"}, failure,
                                 context={**(actual_data.get("usage_context") if isinstance(actual_data.get("usage_context"),dict) else {}),
                                          **({"run_id":capture.run_id} if capture else {})}, stage="failed",root=locals().get("root"))]}
                except (ContractError, OSError, ValueError, KeyError, TypeError) as diagnostic_error:
                    usage = {"status":"incomplete","cause":str(diagnostic_error),"quality":"unchanged","observations":[]}
            try:
                value = report(usage["observations"])
                usage.update(summary=value["summary"], prompt=value["prompt"])
            except (ContractError, ValueError, KeyError, TypeError): usage["status"] = "incomplete"
            failure["usage"] = usage
        # Output/diagnostic failure cannot hide applied effects in either view.
        observed_result = locals().get("result", {})
        if action in {"store-compact", "store-recover"} and args.authorize:
            try:
                from store_compaction import status as store_status
                state = store_status(locals().get("root", args.project_root), args.authorize)
                failure.update(status="partial" if state.get("pending") else "blocked", effects=state,
                               next="Inspect pending/receipt; use store-recover with the same hash, never blindly repeat store-compact")
            except (ContractError, OSError, ValueError, KeyError, TypeError):
                pass
        if observed_result.get("format") == "lks-sdd-operation-result/1" and action in {"work-continue", "work-record-results"}:
            failure.update({key: observed_result[key] for key in
                ("format", "version", "operation", "operation_id", "task", "actor", "effects", "writes", "recovery") if key in observed_result})
            failure["operation_status"] = observed_result["status"]
            if observed_result.get("effects") or observed_result.get("recovery"):
                failure["status"] = "partial"
                failure["next"] = "Preserve these stage receipts; retry the exact intent after resolving the transport failure"
        elif observed_result.get("status") in {"applied", "previously-applied", "completed", "rolled-back"}:
            failure["effects"] = {key: observed_result[key] for key in
                ("status", "receipt", "preview_hash", "writes", "current_conformance") if key in observed_result}
        capture_result=dict(failure)
        if args.view == "operational" and "usage" in failure and not args.details:
            from v3_cli_presentation import usage_view
            failure["usage"] = usage_view(failure["usage"])
        if args.capture_dir and capture is None and capture_error is None:
            try:
                from diagnostic_capture import Capture
                capture=Capture(args.capture_dir,locals().get("root",args.project_root))
            except (ContractError,OSError,ValueError,TypeError,KeyError) as capture_exc: capture_error=str(capture_exc)
        if isinstance(exc, OperationInterrupted):
            if args.capture_dir:
                failure["diagnostic_capture"] = {"status":"inspection-required", "directory":str(args.capture_dir),
                    "next":"An external entry or immutable objects may exist; inspect before retrying capture"}
            print(json.dumps(failure,ensure_ascii=False))
        elif args.capture_dir:
            from diagnostic_capture import emit
            emit(failure,capture_result,capture,capture_error,argv=list(argv if argv is not None else sys.argv[1:]),input_raw=input_raw,input_data=locals().get("data"),compact_output=args.view=="operational" and not args.details)
        else: print(json.dumps(failure,ensure_ascii=False))
        return 3 if failure["status"] == "partial" else 130 if isinstance(exc, OperationInterrupted) else 2


if __name__ == "__main__": sys.exit(main())
