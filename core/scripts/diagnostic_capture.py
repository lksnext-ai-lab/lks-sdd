"""Explicit external diagnostics. No authorization, executable data or hidden writes."""
from contextlib import contextmanager
import copy
import json
import os
from pathlib import Path
import re
import time
import uuid

from v3_contract import ContractError, canonical, sha
from content_store import reference, object_path
from path_utils import filesystem_root, publish_new_file

FORMAT = "lks-sdd-diagnostic-run/1"
LIMIT = 64 * 1024 * 1024
MAX_FILES = 10000
MAX_OBSERVATIONS = 20000
ID = re.compile(r"[0-9a-f]{32}")
HASH = re.compile(r"[0-9a-f]{64}")


def safe_root(directory, consumer=None):
    from usage_bundle import no_links
    path = filesystem_root(no_links(filesystem_root(directory)))
    if consumer is not None:
        from v3_cli_presentation import export_path
        path = export_path(path, consumer)
    if path.exists() and not path.is_dir(): raise ContractError("Capture destination is not a directory")
    return filesystem_root(path,force_extended=True)


def clean(raw):
    from evidence_safety import sanitize
    try: value = json.loads(raw)
    except (ValueError, UnicodeError):
        try: value = raw.decode("utf-8")
        except UnicodeError: return
    if sanitize(value)[1]: raise ContractError("Credential-pattern material refused; exact capture not retained")


def read_file(path, maximum=LIMIT):
    from usage_bundle import no_links
    path = filesystem_root(no_links(path))
    size = path.stat().st_size
    if size > maximum: raise ContractError("Capture file exceeds budget")
    # Bound allocation to the observed file, not the entire capture budget.
    # The extra byte still detects growth; short reads and the limit still fail.
    with path.open("rb") as stream: raw = stream.read(size+1)
    if len(raw) != size or len(raw) > maximum: raise ContractError("Capture file changed while reading")
    return raw


def get(root, ref):
    object_path(ref)
    raw = read_file(root/"objects"/ref["sha256"], ref["bytes"])
    if len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]: raise ContractError("Capture object integrity mismatch")
    return raw


def publish(path, raw):
    from usage_bundle import no_links
    no_links(path)
    if path.exists():
        if read_file(path) != raw: raise ContractError("Capture identity/content collision")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path)
    try: publish_new_file(path, raw, prefix=".dc-")
    except FileExistsError:
        if read_file(path) != raw: raise ContractError("Capture identity/content collision")


@contextmanager
def locked(root):
    path = root/".capture.lock"
    publish(path, b"1")
    stream = path.open("r+b")
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        stream.close(); raise ContractError("Capture window is busy; retry capture recovery later") from exc
    try: yield
    finally:
        if os.name == "nt":
            stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else: fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def scan(root):
    """Bound before reading payloads; unknown files/links are never overwritten."""
    from usage_bundle import no_links
    count, size, found = 0, 0, {}
    for path in root.rglob("*"):
        no_links(path)
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            if relative not in {"objects", "pending", "entries"}: raise ContractError("Unknown capture directory")
            continue
        parts = relative.split("/")
        allowed = relative in {"run.json", ".capture.lock"} or (len(parts)==2 and
            ((parts[0]=="objects" and HASH.fullmatch(parts[1])) or
             (parts[0] in {"pending","entries"} and parts[1].endswith(".json") and ID.fullmatch(parts[1][:-5]))))
        if not allowed: raise ContractError("Unknown capture file")
        count += 1; size += path.stat().st_size
        if count > MAX_FILES or size > LIMIT: raise ContractError("Capture window exceeds file/byte budget")
        found[relative] = path.stat().st_size
    return found, size


def header(root):
    value = json.loads(read_file(root/"run.json", 1024*1024))
    if (not isinstance(value,dict) or set(value)!={"format","run_id","consumer","retention"} or value["format"]!=FORMAT
            or not isinstance(value["run_id"],str) or not 1<=len(value["run_id"])<=65536
            or not isinstance(value["consumer"],str) or not value["consumer"] or not isinstance(value["retention"],str)):
        raise ContractError("Unsupported capture window")
    return value


def batches(rows):
    from v3_usage import check_batch
    batch = []
    for row in rows:
        candidate = batch + [row]
        if len(candidate)>1000 or len(canonical({"format":"lks-sdd-usage/1","observations":candidate}))>1024*1024:
            if not batch: raise ContractError("Observation exceeds capture batch budget")
            check_batch(batch); yield batch; batch=[row]
        else: batch=candidate
    if batch: check_batch(batch); yield batch


def checked_entry(root, raw, *, budget=None, verify_object=None):
    budget=budget if budget is not None else {"rows":0,"bytes":0}
    verify_object=verify_object or (lambda ref: get(root,ref))
    value = json.loads(raw)
    if (not isinstance(value,dict) or set(value)!={"format","id","run_id","usage_meta","batches","materials","transport","missing"}
            or value["format"]!=FORMAT or not isinstance(value["id"],str) or not ID.fullmatch(value["id"])):
        raise ContractError("Invalid capture entry")
    if value["run_id"] != header(root)["run_id"]: raise ContractError("Capture run identity collision")
    if (not isinstance(value["batches"],list) or not isinstance(value["materials"],dict)
            or not isinstance(value["transport"],dict) or not isinstance(value["usage_meta"],dict)
            or not isinstance(value["missing"],list) or not all(isinstance(m,str) for m in value["missing"])):
        raise ContractError("Invalid capture metadata types")
    rows=[]
    for ref in value["batches"]:
        object_path(ref)
        if ref["bytes"]>1024*1024: raise ContractError("Captured batch exceeds budget")
        if budget["bytes"]+ref["bytes"]>LIMIT:raise ContractError("Resolved capture batches exceed byte budget")
        budget["bytes"]+=ref["bytes"]
        batch=json.loads(get(root,ref))
        if set(batch)!={"format","observations"} or batch["format"]!="lks-sdd-usage/1": raise ContractError("Invalid captured batch")
        from v3_usage import check_batch
        check_batch(batch["observations"])
        if budget["rows"]+len(batch["observations"])>MAX_OBSERVATIONS:raise ContractError("Resolved capture exceeds observation budget")
        budget["rows"]+=len(batch["observations"]);rows.extend(batch["observations"])
    for field in ("argv","stdout","api_result","input","output_file","reproduction_fixture"):
        if field in value["transport"]:object_path(value["transport"][field])
    if not all(k in value["transport"] for k in ("argv","stdout","api_result")):raise ContractError("Missing captured transport")
    for ref in list(value["materials"].values()) + [v for v in value["transport"].values() if isinstance(v,dict) and v.get("format")=="lks-sdd-object/1"]:
        verify_object(ref)
    for key in ("input_packet","result_packet"):
        if key in value["transport"]:
            from usage_bundle import name
            payload=value["transport"][key]
            if not isinstance(payload,dict):raise ContractError("Invalid captured packet inventory")
            for path,ref in payload.items():
                name(path)
                if ref is not None:verify_object(ref)
    if any(k!=v["sha256"] for k,v in value["materials"].items()): raise ContractError("Captured material identity mismatch")
    if not all(k in value["transport"] for k in ("argv","stdout")): raise ContractError("Missing captured transport")
    if any(r["run_id"]!=value["run_id"] for r in rows): raise ContractError("Captured observation belongs to another run")
    return value, rows


def load(directory, *, consumer=None):
    root=safe_root(directory,consumer); found,size=scan(root); info=header(root)
    entries=[]; rows=[]; material={}; seen={};budget={"rows":0,"bytes":0}
    objects={}
    def verify_object(ref):
        # Collect identities, not trusted bytes or prior validation results.
        # Every unique object is physically read and hashed before this load
        # returns. A later load starts empty; batch expansion limits stay exact.
        object_path(ref)
        key=ref["sha256"]
        if key in objects and objects[key]!=ref:raise ContractError("Conflicting capture object reference")
        if key not in objects and len(objects)>=MAX_FILES:raise ContractError("Capture object references exceed budget")
        objects[key]=dict(ref)
    for name in sorted(n for n in found if n.startswith("entries/")):
        raw=read_file(root/name,1024*1024)
        value, observed=checked_entry(root,raw,budget=budget,verify_object=verify_object)
        if name != "entries/"+value["id"]+".json": raise ContractError("Capture entry name mismatch")
        duplicate="pending/"+value["id"]+".json"
        if duplicate in found and read_file(root/duplicate,1024*1024)!=raw:raise ContractError("Pending/committed capture collision")
        entries.append(value)
        for row in observed:
            key=row["observation_id"]; digest=sha(canonical(row))
            if key in seen and seen[key]!=digest: raise ContractError("Captured observation identity collision")
            if key not in seen: rows.append(row);seen[key]=digest
            if len(rows)>MAX_OBSERVATIONS: raise ContractError("Capture exceeds observation budget")
        material.update(value["materials"])
    pending=[n for n in found if n.startswith("pending/") and "entries/"+n[8:] not in found]
    referenced=set()
    def references(value):
        if isinstance(value,dict):
            if value.get("format")=="lks-sdd-object/1":referenced.add(value["sha256"])
            else:
                for child in value.values():references(child)
        elif isinstance(value,list):
            for child in value:references(child)
    for entry in entries:references(entry)
    unreferenced=sorted(n for n in found if n.startswith("objects/") and n[8:] not in referenced)
    for ref in objects.values():get(root,ref)
    return {"root":root,"header":info,"entries":entries,"observations":rows,"materials":material,
            "pending":pending,"unreferenced":unreferenced,"files":found,"bytes":size,"resolved_budget":budget}


def inspect(directory):
    value=load(directory)
    return {"format":FORMAT,"status":"incomplete" if not value["entries"] or value["pending"] or value["unreferenced"] or any(e["missing"] for e in value["entries"]) else "stored",
            "run_id":value["header"]["run_id"],"entries":len(value["entries"]),"observations":len(value["observations"]),
            "files":len(value["files"]),"bytes":value["bytes"],"pending":value["pending"],
            "unreferenced_objects":value["unreferenced"],
            "missing":sorted({m for e in value["entries"] for m in e["missing"]}),
            "prepared_stdout_bytes":sum(e["transport"]["stdout"]["bytes"] for e in value["entries"]),
            "input_file_bytes":sum(e["transport"].get("input",{}).get("bytes",0) for e in value["entries"]),
            "argv_bytes":sum(e["transport"]["argv"]["bytes"] for e in value["entries"]),
            "host_received":"unobserved","billed_tokens":None,"writes":[]}


def recover(directory):
    root=safe_root(directory)
    from v3_cli_presentation import export_path
    export_path(root,header(root)["consumer"])
    for parent in (root,*root.parents):
        if (parent/".lks-sdd/project.json").is_file(): raise ContractError("Capture recovery must be outside a consumer")
    with locked(root):
        value=load(root)
        pending=[];seen={r["observation_id"]:sha(canonical(r)) for r in value["observations"]};budget=dict(value["resolved_budget"])
        for name in value["pending"]:
            raw=read_file(root/name,1024*1024); entry,rows=checked_entry(root,raw,budget=budget)
            if name!="pending/"+entry["id"]+".json": raise ContractError("Pending capture identity mismatch")
            for row in rows:
                key=row["observation_id"];digest=sha(canonical(row))
                if key in seen and seen[key]!=digest: raise ContractError("Pending observation identity collision")
                seen[key]=digest
            pending.append((entry,raw))
        if len(value["files"])+len(pending)>MAX_FILES or value["bytes"]+sum(len(raw) for _,raw in pending)>LIMIT or len(seen)>MAX_OBSERVATIONS:
            raise ContractError("Recovery would exceed capture window budget")
        for entry,raw in pending:
            publish(root/"entries"/(entry["id"]+".json"),raw)
    return {**inspect(root),"writes":[str(root/"entries"/(entry["id"]+".json")) for entry,_ in pending]}


class Capture:
    def __init__(self, directory, consumer, run_id=None):
        self.root=safe_root(directory,consumer); self.consumer=str(Path(consumer).resolve())
        if self.root.exists(): scan(self.root)
        old=header(self.root) if (self.root/"run.json").exists() else None
        self.run_id=run_id or (old["run_id"] if old else "capture-"+uuid.uuid4().hex)
        if run_id is not None and (not isinstance(run_id,str) or not 1<=len(run_id)<=65536):raise ContractError("Invalid capture run identity")
        self.info={"format":FORMAT,"run_id":self.run_id,"consumer":self.consumer,
                   "retention":"Explicit caller-owned window; retain while referenced, apply declared area policy; no automatic deletion"}
        if old and old!=self.info: raise ContractError("Capture window identity collision")
        self.id=uuid.uuid4().hex

    def store(self, shown, result, *, argv, input_raw=None, input_data=None, output_file=None, interrupt_after=None, compact_output=False):
        started=time.monotonic(); objects={}; missing=[]; materials={}
        def add(raw):
            if not isinstance(raw,bytes) or len(raw)>LIMIT: raise ContractError("Capture object exceeds byte budget")
            clean(raw); ref=reference(raw);objects[ref["sha256"]]=raw
            if sum(map(len,objects.values()))>LIMIT: raise ContractError("Capture invocation exceeds byte budget")
            return ref
        usage=result.get("usage",{})
        rows=usage.get("observations",[])
        if len(rows)>MAX_OBSERVATIONS:raise ContractError("Capture exceeds observation budget")
        seen={}
        for row in rows:
            key=row["observation_id"];digest=sha(canonical(row))
            if key in seen and seen[key]!=digest:raise ContractError("Observation identity collision")
            if row["run_id"]!=self.run_id:raise ContractError("Observation belongs to another capture run")
            seen[key]=digest
        if len(seen)>MAX_OBSERVATIONS:raise ContractError("Capture exceeds observation budget")
        if usage.get("status")=="incomplete": missing.append("Diagnostic envelope is incomplete; core result is unchanged")
        if usage.get("pending_observations"):missing.append("Deferred observations retained in metadata; conserve their original windows/materials explicitly")
        batch_refs=[add(canonical({"format":"lks-sdd-usage/1","observations":b})) for b in batches(rows)]
        literal=result.get("contract",{}) if result.get("format")=="lks-sdd-operation-result/1" else result
        for source in literal.get("sources",[]) + literal.get("attachments",[]):
            raw=source.get("text")
            if isinstance(raw,str): raw=raw.encode("utf-8")
            elif source.get("requires_observation"):
                try:
                    from v3_contract import read_bytes
                    raw=read_bytes(Path(self.consumer),source["path"],limit=LIMIT)
                    if sha(raw)!=source["sha256"] or len(raw)!=source["bytes"]: raise ContractError("Attachment changed")
                except (ContractError,OSError,KeyError): missing.append("Attachment unavailable or changed: "+str(source.get("path")));continue
            if isinstance(raw,bytes): materials[sha(raw)]=add(raw)
        for row in rows:
            for fragment in row["fragments"]:
                digest=fragment["sha256"]
                if "text" in fragment: materials[digest]=add(fragment["text"].encode("utf-8"))
                elif digest not in materials:
                    try:
                        from content_store import read_object
                        ref=fragment.get("text_ref",fragment.get("data_ref"))
                        if ref is None: raise ContractError("Missing original source")
                        materials[digest]=add(read_object(Path(self.consumer),ref))
                    except (ContractError,OSError): missing.append("Source bytes unavailable: "+fragment["source"])
        transport={"argv":add(canonical(argv)),"argv_coverage":"Shared CLI argv values serialized as UTF-8 JSON; entry point/shell/OS wire unobserved",
                   "host_received":"unobserved","stdout_coverage":"Exact prepared UTF-8 stdout including diagnostic reference; emission/host receipt unobserved"}
        if literal.get("roots") and literal.get("sources") and any(row["operation"] in {"context","work-prepare"} for row in rows):
            try:
                from usage_bundle import fixture,selection_sources
                graph=fixture(Path(self.consumer),literal["roots"],byte_budget=max(0,(LIMIT-sum(map(len,objects.values())))//2))
                import base64
                for case in graph["cases"]:
                    for encoded in case["files"].values():clean(base64.b64decode(encoded,validate=True))
                expected=selection_sources(literal)
                if graph["cases"][0]["expected_sources"]!=expected:raise ContractError("Context changed before capture fixture")
                transport["reproduction_fixture"]=add(canonical(graph))
            except (ContractError,OSError,ValueError,KeyError,TypeError):missing.append("Documentary reproduction fixture unavailable, changed or over budget")
        transport["api_result"]=add(canonical(result))
        if input_raw is not None: transport["input"]=add(input_raw)
        if output_file is not None: transport["output_file"]=add(read_file(output_file))
        from v3_packet import FORMAT as PACKET, Payload
        for field,packet in (("input_packet",input_data),("result_packet",result)):
            if isinstance(packet,dict) and packet.get("format")==PACKET:
                if not hasattr(packet,"base"): missing.append("Referenced packet objects unavailable: "+field);continue
                payload={}
                values=Payload(packet)
                for name in values:
                    raw_object=values[name]
                    payload[name]=None if raw_object is None else add(raw_object)
                    if raw_object is not None: materials[sha(raw_object)]=payload[name]
                transport[field]=payload
        if input_raw is not None and input_data is None:
            try:
                if json.loads(input_raw).get("format")==PACKET:missing.append("Input packet objects not observed at this boundary")
            except (ValueError,AttributeError):pass
        reference_view={"format":FORMAT,"status":"stored-with-gaps" if missing else "stored","run_id":self.run_id,
                        "entry":str(self.root/"entries"/(self.id+".json")),"host_received":"unobserved"}
        shown={**shown,"diagnostic_capture":reference_view}
        if result.get("format")=="lks-sdd-operation-result/1":shown["diagnostic_ref"]=reference_view
        from v3_cli_presentation import json_text
        text=json_text(shown,operational=compact_output)
        transport["stdout"]=add(text.encode("utf-8"))
        entry={"format":FORMAT,"id":self.id,"run_id":self.run_id,"usage_meta":{k:v for k,v in usage.items() if k!="observations"},
               "batches":batch_refs,"materials":materials,"transport":transport,"missing":sorted(set(missing))}
        raw=canonical(entry)
        if len(raw)>1024*1024: raise ContractError("Capture entry exceeds metadata budget")
        self.root.mkdir(parents=True,exist_ok=True)
        with locked(self.root):
            found,size=scan(self.root)
            run_raw=canonical(self.info)
            planned={"run.json":run_raw,"pending/"+self.id+".json":raw,"entries/"+self.id+".json":raw,
                     **{"objects/"+key:value for key,value in objects.items()}}
            if len(set(found)|set(planned))>MAX_FILES or size+sum(len(v) for k,v in planned.items() if k not in found)>LIMIT:
                raise ContractError("Capture window exceeds file/byte budget")
            for name,value in planned.items():
                if name in found and read_file(self.root/name)!=value: raise ContractError("Capture identity/content collision")
            if "run.json" in found:
                existing=load(self.root)
                if existing["header"]!=self.info: raise ContractError("Capture window identity collision")
                if any(name!="pending/"+self.id+".json" for name in existing["pending"]):
                    raise ContractError("Recover pending capture entries before appending another invocation")
                if "entries/"+self.id+".json" not in found:
                    if existing["resolved_budget"]["rows"]+len(rows)>MAX_OBSERVATIONS or existing["resolved_budget"]["bytes"]+sum(ref["bytes"] for ref in batch_refs)>LIMIT:
                        raise ContractError("Resolved capture window exceeds budget")
                all_ids={r["observation_id"]:sha(canonical(r)) for r in existing["observations"]}
                for row in rows:
                    if row["observation_id"] in all_ids and all_ids[row["observation_id"]]!=sha(canonical(row)): raise ContractError("Observation identity collision")
                if len(set(all_ids)|{r["observation_id"] for r in rows})>MAX_OBSERVATIONS: raise ContractError("Capture exceeds observation budget")
            for index,(name,value) in enumerate(planned.items()):
                if name.startswith("pending/") or name.startswith("entries/"): continue
                publish(self.root/name,value)
                if interrupt_after is not None and index==interrupt_after: raise InterruptedError("Capture interrupted before entry publication")
            publish(self.root/"pending"/(self.id+".json"),raw)
            if interrupt_after == "pending": raise InterruptedError("Capture pending publication")
            publish(self.root/"entries"/(self.id+".json"),raw)
        self.elapsed_seconds=time.monotonic()-started
        return text


def emit(shown, result, capture=None, error=None, **kwargs):
    """Capture success/failure never changes the normative result or exit code."""
    import sys
    from v4_activity import checkpoint, OperationInterrupted
    from v3_cli_presentation import json_text
    compact_output=kwargs.pop("compact_output",False)
    if capture is None and error is None:
        sys.stdout.write(json_text(shown,operational=compact_output));return
    try:
        if error: raise ContractError(error)
        text=capture.store(shown,result,compact_output=compact_output,**kwargs)
    except OperationInterrupted:
        raise
    except (ContractError,OSError,ValueError,KeyError,TypeError) as exc:
        shown={**shown,"diagnostic_capture":{"format":FORMAT,"status":"failed","cause":str(exc),
                 "next":"Inspect/recover the external window; do not repeat an applied normative operation to repair capture","host_received":"unobserved"}}
        if result.get("format")=="lks-sdd-operation-result/1":shown["diagnostic_ref"]=shown["diagnostic_capture"]
        text=json_text(shown,operational=compact_output)
    checkpoint()
    if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8",newline="\n")
    sys.stdout.write(text)


def imported_window(directory, consumer=None, *, entry_ids=None):
    from v3_usage import imported
    value=load(directory,consumer=consumer)
    if value["pending"]: raise ContractError("Capture has pending entries; recover explicitly first")
    if entry_ids is not None:
        if not isinstance(entry_ids,list) or not entry_ids or not all(isinstance(i,str) and ID.fullmatch(i) for i in entry_ids):raise ContractError("Invalid focal capture entry selection")
        selected=[e for e in value["entries"] if e["id"] in entry_ids]
        if {e["id"] for e in selected}!=set(entry_ids):raise ContractError("Capture entry selection is absent")
        value["entries"]=selected;value["materials"]={k:r for e in selected for k,r in e["materials"].items()}
        value["observations"]=[r for e in selected for ref in e["batches"] for r in json.loads(get(value["root"],ref))["observations"]]
    rows=[imported(r,external=True) for r in value["observations"]]
    materials={key:get(value["root"],ref) for key,ref in value["materials"].items()}
    return value,rows,materials


def record(root,data):
    from v3_usage import additions
    from v3_storage import prepare
    if "observations" in data: raise ContractError("Capture and explicit observations are mutually exclusive")
    value,rows,materials=imported_window(data["capture_dir"],root,entry_ids=data.get("capture_entries"))
    if not rows:raise ContractError("No committed observations to conserve")
    items=[];changes={}
    for batch in batches(rows):
        added,objects=additions(root,batch,data.get("actor"),materials=materials)
        items.extend(added)
        for key,raw in objects.items():
            if key in changes and changes[key]!=raw: raise ContractError("Capture material collision")
            changes[key]=raw
    result=prepare(root,items,"usage-record",changes=changes) if items else {"status":"already-recorded","writes":[]}
    result["capture_source"]={"run_id":value["header"]["run_id"],"observations":len(rows),"provenance":"unverified-import"}
    return result


def export_data(root,data):
    import base64
    value,rows,materials=imported_window(data["capture_dir"],root,entry_ids=data.get("capture_entries"))
    supplied={"sources/"+key+".bin":{"encoding":"base64","data":base64.b64encode(raw).decode("ascii")} for key,raw in materials.items()}
    for entry in value["entries"]:
        for field in ("argv","input","stdout","output_file","api_result"):
            if field in entry["transport"]:
                supplied["evidence/"+entry["id"]+"-"+field+".bin"]={"encoding":"base64","data":base64.b64encode(get(value["root"],entry["transport"][field])).decode("ascii")}
        supplied["evidence/"+entry["id"]+"-transport.json"]=entry["transport"]
    cases=[]
    for entry in value["entries"]:
        if "reproduction_fixture" in entry["transport"]:
            graph=json.loads(get(value["root"],entry["transport"]["reproduction_fixture"]))
            for case in graph["cases"]:
                if case not in cases:cases.append(case)
    if cases:
        if len(cases)>3:raise ContractError("Select capture_entries for at most three documentary reproduction cases")
        supplied["reproduction/fixture.json"]={"format":"lks-sdd-context-reproduction/1","cases":cases}
    for key,material in data.get("materials",{}).items():
        if key in supplied: raise ContractError("Conflicting supplied capture material")
        supplied[key]=material
    return {**data,"observations":rows,"materials":supplied,"dependencies":list(data.get("dependencies",[]))+sorted({m for entry in value["entries"] for m in entry["missing"]})}


def early_options(arguments):
    """Full option names only; input filenames can never enable capture."""
    values={};index=0
    options={"--input","--output","--authorize","--receipt","--view","--capture-dir"}
    while index<len(arguments):
        token=arguments[index]
        if token=="--": break
        key=token.split("=",1)[0]
        if key in options:
            if "=" in token: values[key]=token.split("=",1)[1]
            elif index+1<len(arguments):index+=1;values[key]=arguments[index]
        index+=1
    return values


def early_consumer(arguments):
    """Locate the two v3 positionals without mistaking option values for roots."""
    values={"--input","--output","--authorize","--receipt","--view","--capture-dir"}
    flags={"--apply","--json","--details","--compact"}
    positionals=[];index=0
    while index<len(arguments):
        token=arguments[index];key=token.split("=",1)[0]
        if token=="--":positionals.extend(arguments[index+1:]);break
        if key in values:
            if "=" not in token:index+=1
        elif token in flags:pass
        elif token.startswith("-"):raise ContractError("Ambiguous early capture arguments")
        else:positionals.append(token)
        index+=1
    if len(positionals)!=2:raise ContractError("Missing or ambiguous consumer root for early capture")
    return Path(positionals[1])
