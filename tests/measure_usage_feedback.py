"""One focal comparison and three portable synthetic cases; not a release gate."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests")); sys.path.insert(0,str(ROOT/"scripts"))
from test_v3_workflow import ProjectFixture, commit_packet
from v3_cli import execute, _execute_persist
from v3_contract import canonical, element, load, sha
from v3_authoring import author
from v3_usage import record, summary_metrics
from usage_bundle import preview, export, fixture
from usage_test_support import late


def measured(fn):
    start = time.monotonic(); value = fn(); return value,time.monotonic()-start


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args(); output = args.output.resolve()
    if output == ROOT or ROOT in output.parents or output.exists(): raise ValueError("Choose a new directory outside the checkout")
    output.mkdir(parents=True)
    case = ProjectFixture(); case.setUp()
    try:
        case.plan()
        data = {"roots":[case.task]}
        _execute_persist("context",case.root,data)  # Equal warm cache conditions.
        control,control_time = measured(lambda:_execute_persist("context",case.root,data))
        _,control_again_time = measured(lambda:_execute_persist("context",case.root,data))
        actual,query_time = measured(lambda:execute("context",case.root,{**data,"usage_context":{"run_id":"focal-repeat","request":case.req,"tasks":[case.task]}}))
        again,again_time = measured(lambda:execute("context",case.root,{**data,"usage_context":{"run_id":"focal-repeat","request":case.req,"tasks":[case.task]}}))
        fields = ("sources","attachments","roots","widened","sufficiency","selection_digest")
        same_contract = all(control[k] == actual[k] for k in fields)
        if not same_contract: raise AssertionError("Instrumentation changed the literal contract")
        rows = actual["usage"]["observations"] + again["usage"]["observations"]
        packet,prepare_time = measured(lambda:record(case.root,{"actor":case.actor,"observations":rows}))
        new_objects = {p:len(base64.b64decode(b)) for p,b in packet["payload"].items() if b is not None and p.startswith(".lks-sdd/objects/") and not (case.root/p).exists()}
        _,apply_time = measured(lambda:commit_packet(case.root,packet))
        report_value,report_time = measured(lambda:execute("usage-report",case.root,{"run_id":"focal-repeat"}))
        export_data = {"run_id":"focal-repeat","selector":{"scenario":"repetition","synthetic":True},"materials":{"reproduction/fixture.json":fixture(case.root,[case.task])}}
        bundle,export_prepare_time = measured(lambda:execute("usage-export",case.root,export_data))
        _,export_time = measured(lambda:export(bundle,output/"repetition",bundle["export_hash"]))
        # Late recovery uses real before/after selector runs with different roots.
        before_fixture = fixture(case.root,[case.task])
        req = element("request","Segundo contrato sintético","El saludo de este alcance debe ser Kaixo.")
        rule = element("rule","Idioma del segundo alcance","La salida acordada es Kaixo.",request=req["meta"]["uid"])
        req["meta"]["relations"]["requirements"] = [rule["meta"]["uid"]]
        commit_packet(case.root,author(case.root,case.actor,[req,rule]))
        before_selection = execute("context",case.root,{"roots":[case.task]})
        after_selection = execute("context",case.root,{"roots":[req["meta"]["uid"]]})
        after_fixture = fixture(case.root,[req["meta"]["uid"]])
        combined = {"format":"lks-sdd-context-reproduction/1","cases":before_fixture["cases"]+after_fixture["cases"]}
        late_rows,materials = late()
        late_rows[0]["declarations"][0]["prior_applicability_proof"] = None
        late_rows[0]["declarations"][0]["scope_note"] = "Selection roots changed; no proof that the second rule applied to the initial task. Cause pending."
        materials["evidence/before.json"]["selection"] = [s["key"] for s in before_selection["sources"]]
        materials["evidence/after.json"]["selection"] = [s["key"] for s in after_selection["sources"]]
        materials["sources/contract.txt"] = rule["body"]
        materials["reproduction/fixture.json"] = combined
        late_bundle = preview({"observations":late_rows,"materials":materials,"selector":{"scenario":"late-context","synthetic":True}})
        export(late_bundle,output/"late-context",late_bundle["export_hash"])
        early_root = output/"early-origin"; early_root.mkdir()
        try: execute("implement",early_root,{"task":"invalid","reason":"synthetic early failure","usage_context":{"run_id":"early-case"}})
        except Exception as exc:
            if not hasattr(exc,"usage"): raise
            early_rows = exc.usage["observations"]
        if list(early_root.iterdir()): raise AssertionError("Early failure wrote in the consumer")
        early_bundle = preview({"observations":early_rows,"selector":{"scenario":"early-block","synthetic":True},"materials":{"evidence/expected.json":{"expected":"valid current runtime and task before implementation","environment":"uninitialized synthetic project; Python "+sys.version.split()[0]}}})
        export(early_bundle,output/"early-block",early_bundle["export_hash"])
        cold = {}
        for name,reproduce in (("repetition",True),("late-context",True),("early-block",False)):
            command = [sys.executable,"-B","-X","utf8",str(ROOT/"scripts/lks_sdd.py"),"usage-inspect",str(output/name)] + (["--reproduce"] if reproduce else [])
            run = subprocess.run(command,capture_output=True,text=True,encoding="utf-8",timeout=120)
            if run.returncode: raise AssertionError(run.stdout+run.stderr)
            checked = json.loads(run.stdout)
            if checked["bundle_status"] != "ready-for-investigation": raise AssertionError(checked["missing"])
            if reproduce and checked["reproduction"]["status"] != "reproduced": raise AssertionError("Cold reproduction failed")
            cold[name] = {"status":checked["status"],"bundle_status":checked["bundle_status"],"reproduction":checked.get("reproduction"),"manifest_sha256":sha((output/name/"manifest.json").read_bytes())}
        result = {"scope":"one synthetic task; monotonic timings, no universal speed or host/token claim",
                  "same_literal_contract":same_contract,"metrics":summary_metrics(rows),
                  "seconds":{"control_query":control_time,"observed_query":query_time,"envelope_collection":rows[0]["metrics"]["collection"]["value"],
                             "control_total_two_queries":control_time+control_again_time,"observed_total_two_queries":query_time+again_time,
                             "conservation_prepare":prepare_time,"conservation_apply":apply_time,"report":report_time,"export_prepare":export_prepare_time,"export_publish":export_time},
                  "new_objects":{"count":len(new_objects),"bytes":sum(new_objects.values())},"additional_mutations":1,
                  "query_counts":{"control":2,"observed":2,"unmeasured_warmup":1},
                  "finding_rules":sorted({f["rule"] for f in report_value["findings"]}),"cold_cases":cold,
                  "host_acceptance":"not-run","human_comprehension":"not-run"}
        (output/"measurement.json").write_bytes(canonical(result)+b"\n")
        print(json.dumps({"status":"passed","output":str(output),"seconds":result["seconds"],"new_objects":result["new_objects"],"cold_cases":{k:v["bundle_status"] for k,v in cold.items()}},ensure_ascii=False))
    finally: case.doCleanups()


if __name__ == "__main__": main()
