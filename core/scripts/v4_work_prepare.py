"""Read-only composition over current-method rules; no cached authorization."""
from datetime import datetime, timezone
import json
from pathlib import Path

from v3_contract import ContractError, document_paths, fingerprint, path_at, read_bytes, sha
from v3_evaluation import count, evaluation, measured_evaluation

REQUEST = "lks-sdd-operation-request/1"
RESULT = "lks-sdd-operation-result/1"
CAPABILITY = "work-prepare/1"
MAX_TASKS = 20
CAPABILITY_SOURCES = ("v4_work_prepare.py","v4_activity.py","v2_contract.py","v3_cli.py","v3_current.py","v3_guidance.py","v31_guidance.py",
    "v3_context.py","v3_scope.py","v3_approval.py","v3_authoring.py","v3_evaluation.py","v3_contract.py","v3_workflow.py","v3_git.py","v3_usage.py","diagnostic_capture.py","usage_bundle.py")


def request(root, data):
    from v3_workflow import TRANSITIONS
    if not isinstance(data,dict) or set(data)-{"format","version","operation_id","task","actor","parameters"}:
        raise ContractError("Unknown work-prepare request fields")
    if data.get("format")!=REQUEST or type(data.get("version")) is not int or data["version"]!=1:
        raise ContractError("Unsupported work-prepare request version")
    for field in ("task","operation_id"):
        if not isinstance(data.get(field),str) or not data[field].strip() or len(data[field])>256:
            raise ContractError("Missing or invalid work-prepare " + field)
    actor=data.get("actor")
    if actor is not None and (not isinstance(actor,str) or not actor.strip() or len(actor)>256):
        raise ContractError("Invalid work-prepare actor")
    parameters=data.get("parameters",{})
    if not isinstance(parameters,dict) or set(parameters)-{"action","reference","tasks"}:
        raise ContractError("Unknown work-prepare parameters")
    action=parameters.get("action","start")
    if not isinstance(action,str) or action not in TRANSITIONS:raise ContractError("Unknown intended task transition")
    reference=parameters.get("reference",False)
    if type(reference) is not bool:raise ContractError("reference must be a boolean")
    extra=parameters.get("tasks",[])
    if not isinstance(extra,list) or len(extra)>=MAX_TASKS or any(not isinstance(t,str) or not t.strip() or len(t)>256 for t in extra):
        raise ContractError("Select at most 20 explicit work tasks")
    tasks=[data["task"],*extra]
    if len(tasks)!=len(set(tasks)):raise ContractError("Duplicate work task selection")
    identity={"root":str(root),"task":data["task"],"actor":actor,"parameters":{"action":action,"reference":reference,"tasks":extra}}
    operation_id="wp-"+fingerprint(identity)
    if data["operation_id"] not in {"auto",operation_id}:
        raise ContractError("operation_id does not match these parameters; use auto for a new logical attempt")
    return {"operation_id":operation_id,"task":data["task"],"actor":actor,"action":action,"reference":reference,"tasks":tasks}


def _metadata(root):
    paths=(".lks-sdd/distribution-lock.json",".lks-sdd/project.json")
    return {p:sha(read_bytes(root,p,limit=64*1024*1024,package_data=True))
            if path_at(root,p,missing=True,package_data=True).exists() else None for p in paths}


def _periods(model):
    from v3_policy import active_period
    return {e.uid:active_period(e.data) for e in model.elements.values()
            if e.data.get("valid_from") or e.data.get("expires_at")}


def _fresh(root, model, paths, code, git, metadata, periods, contract):
    """Fresh physical checks, never the query's model cache or a write preview."""
    from v3_git import code_inventory, observe
    from runtime_doctor import check
    from v2_storage import ensure_idle
    count("freshness_boundaries")
    ensure_idle(root)
    if document_paths(root)!=paths:raise ContractError("Document membership changed during work preparation")
    for path,digest in model.hashes.items():
        if sha(read_bytes(root,path,limit=64*1024*1024))!=digest:
            raise ContractError("Source changed during work preparation: "+path)
    for asset in contract.get("attachments",[]):
        raw=read_bytes(root,asset["path"],limit=64*1024*1024)
        if sha(raw)!=asset["sha256"] or len(raw)!=asset["bytes"]:
            raise ContractError("Attachment changed during work preparation: "+asset["path"])
    if code_inventory(root)!=code:raise ContractError("Code/artifact base changed during work preparation")
    current=observe(root)
    if any(current[key]!=git[key] for key in ("branch","head")):raise ContractError("Git branch/base changed during work preparation")
    count("final_runtime_checks")
    runtime=check(root)
    if runtime["status"]!="valid":raise ContractError("Runtime changed during work preparation: "+str(runtime["errors"]))
    if _metadata(root)!=metadata:raise ContractError("Runtime/index declaration changed during work preparation")
    if _periods(model)!=periods:raise ContractError("Authority period changed during work preparation")
    ensure_idle(root)


def prepare(root,data):
    from v3_contract import query_evaluation
    with query_evaluation():return _prepare(root,data)


def _continuity(value, chosen):
    """Project already checked facts; no extra queries, authority or storage."""
    current = value["status"] != "blocked" and value.get("basis") is not None
    tasks = []
    if current:
        selected = set(value["portion"]["requested"])
        for request in value.get("work_state", {}).get("requests", []):
            for task in request.get("tasks", []):
                if task["uid"] in selected:
                    tasks.append({k: task[k] for k in ("uid", "state", "source", "owner", "contributions", "next_action") if k in task})
    basis = value.get("basis") if current else None
    return {"format": "lks-sdd-work-continuity/1", "version": 1,
            "status": "current" if current else "unavailable",
            "actor": chosen["actor"], "identity_inherited": False, "authority_granted": False,
            "basis": {k: basis[k] for k in ("source_snapshot", "git", "code_inventory_digest", "runtime_digest")} if basis else None,
            "tasks": tasks, "facts_ref": "work_state.requests", "interventions_ref": "interventions",
            "stops": [{k: row[k] for k in ("rule", "task", "cause", "causes") if k in row}
                      for row in value["conditions"] if not row.get("satisfied")],
            "required_reading": {"literal_contract_ref": "contract", "attachments_ref": "contract.attachments",
                                 "summaries_replace_contract": False},
            "next": value["next"],
            "validity": "This observed basis only; changed source, operator, runtime, branch or evidence requires a new preparation. Native writes recheck authority."}


def _prepare(root, data):
    root=Path(root).resolve(); chosen=request(root,data)
    with measured_evaluation() as metrics:
        value={"format":RESULT,"version":1,"operation":CAPABILITY,"operation_id":chosen["operation_id"],
               "task":chosen["task"],"actor":chosen["actor"],"basis":None,"status":"blocked","conditions":[],
               "contract":{"sources":[],"attachments":[],"reason":"Preparation not yet sufficient"},
               "effects":[],"writes":[],"portion":{"requested":chosen["tasks"],"ready":[],"blocked":chosen["tasks"]},
               "diagnostic_ref":None,"diagnostic_note":"The CLI adds an external reference only when capture is explicitly requested",
               "next":"Resolve the stated cause; no authority is granted by this query"}
        try:
            metadata=_metadata(root)
            paths=document_paths(root)
            from v3_current import require_current
            count("current_method_boundaries")
            model=require_current(root,{"tasks":chosen["tasks"]})
            tasks=[model.get(key,"task") for key in chosen["tasks"]]
            if len({t.uid for t in tasks})!=len(tasks):raise ContractError("Aliases select the same work task twice")
            if any(t.retired for t in tasks):raise ContractError("Work task is retired; select a current explicit portion")
            requests={t.data["request"] for t in tasks}
            if len(requests)!=1:raise ContractError("Select independent portions of one request per preparation")
            lock_raw=read_bytes(root,".lks-sdd/distribution-lock.json",limit=1024*1024,package_data=True)
            if sha(lock_raw)!=metadata[".lks-sdd/distribution-lock.json"]:
                raise ContractError("Runtime/index declaration changed before work preparation")
            lock=json.loads(lock_raw)
            if "scripts/v4_work_prepare.py" not in lock["runtime_files"]:
                raise ContractError("needs-runtime-update: pinned runtime does not provide work-prepare/1")
            for name in CAPABILITY_SOURCES:
                raw=(Path(__file__).parent/name).read_bytes().replace(b'\r\n',b'\n')
                if lock["runtime_files"].get("scripts/"+name)!=sha(raw):
                    raise ContractError("needs-runtime-update: work-prepare/1 does not match the pinned implementation: "+name)
            from v3_git import code_inventory, observe, observation_evaluation
            git=observe(root);code=code_inventory(root);periods=_periods(model)
            value["task"]=tasks[0].uid
            value["basis"]={"source_snapshot":model.snapshot(),"git":{k:git[k] for k in ("branch","head")},
                "code_inventory_digest":fingerprint(code),"runtime_digest":lock["runtime_digest"],"metadata":metadata,
                "observed_at":datetime.now(timezone.utc).isoformat(),"validity":"Informational snapshot; authority and physical inputs must be rechecked before application"}
            from v3_guidance import status, readiness
            from v31_guidance import interventions
            from v3_context import context
            request_id=next(iter(requests))
            with evaluation(model), observation_evaluation(root):
                from v3_git import subject
                from v3_workflow import state
                value["operation_bases"]={t.uid:{"source_snapshot":model.snapshot(),
                    "git":{k:git[k] for k in ("branch","head")},"code_inventory_digest":fingerprint(code),
                    "subject":subject(root,t.data["scope"]),"state":state(model,t)} for t in tasks}
                value["work_state"]=status(root,request_id=request_id,task_ids={t.uid for t in tasks},task_limit=MAX_TASKS,include_journey=False)
                value["preparation"]=[{"task":t.uid,"readiness":readiness(root,t.uid,chosen["actor"],chosen["action"],include_journey=False)} for t in tasks]
                try:value["interventions"]=interventions(model,request_id,actor=chosen["actor"])
                except ContractError as exc:value["interventions"]={"status":"blocked","causes":[str(exc)],"writes":[]}
                value["contract"]=context(root,[t.uid for t in tasks],chosen["action"],reference=chosen["reference"])
            contract=value["contract"]
            if not contract["sources"] or not any(s.get("text","").strip() for s in contract["sources"]):
                raise ContractError("Empty literal contract cannot prepare work")
            selected=[t.uid for t in tasks]
            if contract.get("roots")!=selected or not set(selected)<=set(s.get("key") for s in contract["sources"]):
                raise ContractError("Literal contract omits a requested work task")
            if contract.get("snapshot")!=model.snapshot():raise ContractError("Literal contract has another source snapshot")
            _fresh(root,model,paths,code,git,metadata,periods,contract)
            value["basis"]["source_snapshot"]=contract["snapshot"]
            value["basis"]["checked_at"]=datetime.now(timezone.utc).isoformat()
            attachment_pending=any(a.get("requires_observation") for a in contract["attachments"])
            ready=[row["task"] for row in value["preparation"] if row["readiness"]["status"]=="allowed" and not attachment_pending and chosen["actor"] is not None]
            blocked=[t.uid for t in tasks if t.uid not in ready]
            value["portion"]={"requested":[t.uid for t in tasks],"ready":ready,"blocked":blocked,"scope":"Explicit selected tasks only; no authorization of other request work"}
            value["conditions"]=[{"rule":"current-method-and-runtime","satisfied":True},
                {"rule":"coherent-basis","satisfied":True},
                {"rule":"actor-identified","satisfied":chosen["actor"] is not None},
                {"rule":"literal-contract","satisfied":True},
                {"rule":"attachment-observation","satisfied":not attachment_pending}]
            value["conditions"] += [{"rule":"task-transition","task":row["task"],"satisfied":row["task"] in ready,
                "causes":row["readiness"].get("causes",[])} for row in value["preparation"]]
            value["status"]="ready" if not blocked else "partial" if ready else "action-required"
            value["next"]={"actor":chosen["actor"],"action":chosen["action"] if ready else "resolve-conditions",
                "tasks":ready,"reason":"Prepare the existing transition; recheck current guards before applying" if ready else
                "Read the literal obligations and resolve identity, transition or attachment conditions; retain independent work"}
        except (ContractError,OSError,ValueError,KeyError,TypeError) as exc:
            value["status"]="blocked";value["portion"]["ready"]=[]
            value["conditions"].append({"rule":"preparation-boundary","satisfied":False,"cause":str(exc)})
            value["cause"]=str(exc)
            value["next"]="Resolve this cause and prepare a new snapshot; do not execute using this result"
        value["continuity"]=_continuity(value, chosen)
        value["evaluation_metrics"]={"counters":dict(metrics),"scope":"Instrumented synchronous core calls in this preparation, including freshness checks; excludes usage-envelope generation, capture and host delivery"}
        return value
