import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_v3_workflow import ProjectFixture, commit_packet
from v3_cli import execute
from v3_contract import ContractError, load
from v3_usage import record, catalog
from v3_decision_presentation import decision_view


class UsageWorkflowTests(ProjectFixture):
    def test_large_text_and_binary_survive_source_removal_and_identical_resend(self):
        import base64
        from content_store import object_path
        from v3_contract import sha, canonical
        from v3_usage import observe, validate_receipt
        from usage_bundle import export, inspect
        text = "Contrato largo con euskara y español.\n" * 2500
        binary = b"\x00\xff\x80\x01" * 2000
        source_path = "docs/lks-sdd/large-note.md"
        raw_source = ('---\nschema_version: "3.0"\n---\n\n'+text).encode("utf-8")
        (self.root/source_path).write_bytes(raw_source)
        text = load(self.root).require_valid().prose[source_path]
        (self.root/"asset.bin").write_bytes(binary)
        result = {"sources":[{"key":"prose:"+source_path,"source":{"path":source_path,"sha256":sha(raw_source)},"text":text}],
                  "attachments":[{"path":"asset.bin","sha256":sha(binary),"bytes":len(binary),"requires_observation":True}]}
        rows = [observe("inspect-assets",{},result,context={"run_id":"source-conservation"}) for _ in range(2)]
        self.assertTrue(all(f.get("gap") for f in rows[0]["fragments"]))
        commit_packet(self.root,record(self.root,{"actor":self.actor,"observations":rows}))
        (self.root/source_path).unlink(); (self.root/"asset.bin").unlink()
        self.assertEqual("already-recorded",record(self.root,{"observations":rows})["status"])
        model = load(self.root).require_valid()
        restored = catalog(model,run_id="source-conservation")
        self.assertEqual("text_ref",next(k for k in restored[0]["fragments"][0] if k.endswith("_ref")))
        self.assertIn("data_ref",restored[0]["fragments"][1])
        packet = execute("usage-export",self.root,{"run_id":"source-conservation"})
        self.assertEqual("ready-for-investigation",packet["manifest"]["status"])
        self.assertEqual(binary,base64.b64decode(packet["files"]["sources/"+sha(binary)+".bin"]))
        self.assertEqual(text.encode(),base64.b64decode(packet["files"]["sources/"+sha(text.encode())+".txt"]))
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp)/"case"
            export(packet,destination,packet["export_hash"])
            self.assertEqual("ready-for-investigation",inspect(destination)["bundle_status"])
        receipt = next(e for e in model.by_kind("receipt") if e.data.get("run_id")=="source-conservation")
        # The second reference shares cached bytes, but its own interval is still validated.
        changed = copy.deepcopy(restored); changed[1]["fragments"][0]["end"] += 1
        raw = canonical({"format":"lks-sdd-usage/1","observations":changed})
        fake = copy.deepcopy(receipt)
        fake.meta["data"]["observations_ref"] = {"format":"lks-sdd-object/1","sha256":sha(raw),"bytes":len(raw)}
        with self.assertRaisesRegex(ContractError,"interval mismatch"):
            validate_receipt(load(self.root).require_valid(),fake,objects={object_path(fake.meta["data"]["observations_ref"]):raw})
        source = restored[0]["fragments"][1]["data_ref"]
        (self.root/object_path(source)).write_bytes(b"corrupted")
        with self.assertRaises(ContractError): load(self.root).require_valid()

    def test_large_historical_body_is_conserved_from_its_original_revision(self):
        from v3_contract import element, sha
        from v3_authoring import author
        from v3_usage import observe
        from content_store import read_object
        item = element("request","Fuente histórica sintética","Contrato inicial extenso.\n"*4000)
        commit_packet(self.root,author(self.root,self.actor,[item]))
        original = load(self.root).get(item["meta"]["uid"])
        row = observe("inspect-assets",{}, {"sources":[{"key":original.uid,"source":original.source(),"text":original.body}]},context={"run_id":"historical-source"})
        item = copy.deepcopy(original.item())
        item["meta"]["revision"] += 1; item["body"] = "Nueva revisión sintética distinta."
        commit_packet(self.root,author(self.root,self.actor,[item]))
        commit_packet(self.root,record(self.root,{"actor":self.actor,"observations":[row]}))
        fragment = catalog(load(self.root),run_id="historical-source")[0]["fragments"][0]
        self.assertEqual(original.body.encode(),read_object(self.root,fragment["text_ref"]))
        self.assertEqual(sha(original.body.encode()),fragment["sha256"])

    def test_real_context_record_resume_isolation_and_fresh_guard(self):
        self.plan()
        data = {"roots":[self.task],"usage_context":{"run_id":"synthetic-continuation","request":self.req,"tasks":[self.task]}}
        before = {p:p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        first = execute("context",self.root,data)
        second = execute("context",self.root,data)
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        rows = first["usage"]["observations"]+second["usage"]["observations"]
        view = decision_view(self.root,"authorize-plan",{"actor":self.actor,"plan":self.plan_id,"statement":"same decision"})
        traced_view = decision_view(self.root,"authorize-plan",{"actor":self.actor,"plan":self.plan_id,"statement":"same decision","usage_context":{"run_id":"arbitrary transport"}})
        self.assertEqual(view["receipt"],traced_view["receipt"])
        old_preview = record(self.root,{"actor":self.actor,"observations":[rows[0]]})
        packet = record(self.root,{"actor":self.actor,"observations":rows})
        commit_packet(self.root,packet)
        after = decision_view(self.root,"authorize-plan",{"actor":self.actor,"plan":self.plan_id,"statement":"same decision"})
        self.assertEqual(view["receipt"],after["receipt"])
        self.assertEqual(view["markdown"],after["markdown"])
        restored = catalog(load(self.root),run_id="synthetic-continuation")
        self.assertEqual(2,len(restored))
        self.assertTrue(all("text_ref" in f and "text" not in f for r in restored for f in r["fragments"] if not f.get("gap")))
        self.assertEqual("already-recorded",record(self.root,{"observations":rows})["status"])
        with self.assertRaises(ContractError): commit_packet(self.root,old_preview)
        report = execute("usage-report",self.root,{"run_id":"synthetic-continuation"})
        self.assertNotIn("usage",report); self.assertTrue(report["findings"])
        from usage_bundle import fixture, preview, export
        import subprocess, sys, json
        with tempfile.TemporaryDirectory() as temp:
            material = fixture(self.root,[self.task])
            packet = preview({"observations":rows,"materials":{"reproduction/fixture.json":material}})
            self.assertEqual("ready-for-investigation",packet["manifest"]["status"])
            exported = Path(temp)/"case"; export(packet,exported,packet["export_hash"])
            cold = subprocess.run([sys.executable,"-B","-X","utf8",str(Path(__file__).resolve().parents[1]/"scripts/lks_sdd.py"),"usage-inspect",str(exported),"--reproduce"],capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(0,cold.returncode,cold.stdout+cold.stderr)
            self.assertEqual("reproduced",json.loads(cold.stdout)["reproduction"]["status"])
        context = execute("context",self.root,data)
        self.assertFalse(any(s.get("meta",{}).get("data",{}).get("purpose")=="usage-observation" for s in context["sources"]))
        receipt = next(e for e in load(self.root).by_kind("receipt") if e.data.get("purpose")=="usage-observation")
        from content_store import object_path
        (self.root/object_path(receipt.data["observations_ref"])).write_bytes(b"corrupt")
        with self.assertRaises(ContractError): load(self.root).require_valid()

    def test_pre_runtime_error_is_transient_and_exportable(self):
        from usage_bundle import preview
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ContractError) as caught:
                execute("implement",root,{"task":"not-a-real-id","reason":"synthetic early failure","usage_context":{"run_id":"early-run"}})
            rows = caught.exception.usage["observations"]
            self.assertEqual(6,len(caught.exception.usage["summary"]))
            self.assertIn("Prompt de mantenimiento",caught.exception.usage["prompt"])
            self.assertFalse(list(root.iterdir()))
            self.assertEqual("failed",rows[0]["stage"])
            self.assertEqual({"request":None,"tasks":[],"state":"provisional"},rows[0]["binding"])
            value = preview({"observations":rows,"materials":{"evidence/expected.json":{"expected":"valid current runtime before implementation","actual":"uninitialized synthetic project"}}})
            self.assertEqual("ready-for-investigation",value["manifest"]["status"])

    def test_diagnostic_failure_does_not_mask_core_failure_or_change_query(self):
        result = execute("status",self.root,{"usage_context":{"phase":42}})
        self.assertEqual("incomplete",result["usage"]["status"])
        self.assertEqual("unchanged",result["usage"]["quality"])
        plain = execute("status",self.root,{})
        result.pop("usage"); plain.pop("usage")
        self.assertEqual(plain,result)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ContractError) as caught:
                execute("implement",Path(temp),{"task":"unknown","usage_context":{"phase":42}})
            self.assertNotIn("Invalid usage-observation",str(caught.exception))
            self.assertEqual("incomplete",caught.exception.usage["status"])

    def test_checkpoint_batches_once_in_same_journal_and_resumes_binding(self):
        self.plan()
        rows = execute("context",self.root,{"roots":[self.task],"usage_context":{"run_id":"synthetic-shared"}})["usage"]["observations"]
        from v3_usage import session
        from v3_lifecycle import checkpoint
        with session({"observations":rows}, {"actor":self.actor}):
            packet = checkpoint(self.root,self.actor,self.task,"Hito sintético observado",[])
        commit_packet(self.root,packet)
        self.assertEqual(1,len(catalog(load(self.root),run_id="synthetic-shared")))
        linked = execute("context",self.root,{"roots":[self.task],"usage_context":{"run_id":"synthetic-shared","request":self.req,"tasks":[self.task],"gaps":["No host tool log available"]}})["usage"]["observations"]
        commit_packet(self.root,record(self.root,{"actor":self.actor,"observations":linked}))
        self.assertEqual(2,len(catalog(load(self.root),request=self.req)))


class CurrentUsageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_v3_efficiency as ef
        cls.fixture_type = ef.EfficiencyTests
        cls.fixture_type.setUpClass()

    @classmethod
    def tearDownClass(cls): cls.fixture_type.tearDownClass()

    def test_current_cli_stages_transports_and_both_native_packages(self):
        import json, subprocess, sys, io, zipfile
        from v3_contract import element
        from v3_storage import apply
        from build_dual_distribution import collect_development
        from dual_distribution import artifacts
        from usage_bundle import fixture
        case = self.fixture_type(); case.setUp(); self.addCleanup(case.doCleanups)
        from presentation_test_support import present
        import test_v3_efficiency as ef
        with self.assertRaises(ContractError) as blocked:
            execute("implement",case.root,{"task":"unknown","reason":"synthetic startup","usage_context":{"run_id":"startup"}})
        pending_rows = blocked.exception.usage["observations"]
        init_data = {"name":"Synthetic","actor_name":"Declared fixture actor","profile":"individual-brief",
                     "controls":case.controls,"statement":"Explicit synthetic configuration","target":"main",
                     "collaboration":ef.configuration(),"runtime_bundle":str(case.bundle),
                     "usage_context":{"run_id":"startup","observations":pending_rows}}
        initialized = present(execute,"init",case.root,init_data)
        self.assertEqual("deferred-until-project-valid",initialized["usage"]["conservation"])
        apply(case.root,initialized,initialized["preview"]["preview_hash"],current=True)
        actor = initialized["summary"]["member"]
        conserved = execute("usage-record",case.root,{"actor":actor,"observations":pending_rows})
        apply(case.root,conserved,conserved["preview"]["preview_hash"],current=True)
        req = element("request","Caso de diagnóstico","Caso sintético para comprobar transporte y conservación.")
        authored = execute("author",case.root,{"actor":actor,"items":[req]})
        apply(case.root,authored,authored["preview"]["preview_hash"],current=True)
        request = req["meta"]["uid"]
        context = {"roots":[request],"usage_context":{"run_id":"cli-run","request":request}}
        rows = execute("context",case.root,context)["usage"]["observations"] + execute("context",case.root,context)["usage"]["observations"]
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp); input_path = temp/"input.json"
            input_path.write_text(json.dumps({"actor":actor,"observations":rows}),encoding="utf-8")
            cli = case.root/json.loads((case.root/".lks-sdd/distribution-lock.json").read_bytes())["runtime"]/"scripts/lks_sdd.py"
            # usage-* operations do not recursively observe themselves.
            run = subprocess.run([sys.executable,"-B","-X","utf8",str(cli),"v3","usage-record",str(case.root),"--input",str(input_path),"--apply"],capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(0,run.returncode,run.stdout+run.stderr)
            result = json.loads(run.stdout)
            self.assertNotIn("usage",result)
            before = {p:p.read_bytes() for p in case.root.rglob("*") if p.is_file()}
            context_path = temp/"context.json"; context_path.write_text(json.dumps(context),encoding="utf-8")
            for mode in ("--compact","--details"):
                output = temp/(mode[2:]+".json")
                run = subprocess.run([sys.executable,"-B","-X","utf8",str(cli),"v3","context",str(case.root),"--input",str(context_path),mode,"--output",str(output)],capture_output=True,text=True,encoding="utf-8")
                self.assertEqual(0,run.returncode,run.stdout+run.stderr)
                self.assertEqual("query",json.loads(output.read_bytes())["usage"]["observations"][0]["stage"])
                self.assertEqual("unobserved",json.loads(run.stdout)["usage"]["transport"]["host_received"])
                displayed = json.loads(run.stdout)["usage"]
                self.assertEqual(output.stat().st_size,displayed["transport"]["prepared_file"]["bytes"])
                self.assertEqual("output-file",displayed["observations"][0]["output"]["mode"])
            self.assertEqual(before,{p:p.read_bytes() for p in case.root.rglob("*") if p.is_file()})
            req2 = element("request","Segundo caso","Caso independiente para distinguir preview y aplicación.")
            input_path.write_text(json.dumps({"actor":actor,"items":[req2],"usage_context":{"run_id":"cli-write"}}),encoding="utf-8")
            run = subprocess.run([sys.executable,"-B","-X","utf8",str(cli),"v3","author",str(case.root),"--input",str(input_path),"--apply"],capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(0,run.returncode,run.stdout+run.stderr)
            events = json.loads(run.stdout)["usage"]["observations"]
            self.assertEqual(["prepared","applied"],[r["stage"] for r in events])
            self.assertEqual(events[0]["invocation_id"],events[1]["invocation_id"])
            export_data = {"run_id":"cli-run","materials":{"reproduction/fixture.json":fixture(case.root,[request])}}
            packet = execute("usage-export",case.root,export_data)
            input_path.write_text(json.dumps(packet),encoding="utf-8")
            run = subprocess.run([sys.executable,"-B","-X","utf8",str(cli),"usage-export","--input",str(input_path),"--destination",str(temp/"case"),"--authorize",packet["export_hash"]],capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(0,run.returncode,run.stdout+run.stderr)
            # Extracted native plugins execute the same independent full diagnosis.
            packages = artifacts(collect_development(Path(__file__).resolve().parents[1]),"synthetic","development-unreleased")
            for host,prefix in (("codex","lks-sdd-plugin-"),("copilot","lks-sdd-copilot-plugin-")):
                target = temp/host; target.mkdir()
                raw = next(v for k,v in packages.items() if k.startswith(prefix))
                with zipfile.ZipFile(io.BytesIO(raw)) as archive: archive.extractall(target)
                choices = list(target.rglob("scripts/lks_sdd.py"))
                host_cli = next(p for p in choices if "core" in p.parts) if host=="copilot" else choices[0]
                run = subprocess.run([sys.executable,"-B","-X","utf8",str(host_cli),"usage-inspect",str(temp/"case"),"--reproduce"],capture_output=True,text=True,encoding="utf-8")
                self.assertEqual(0,run.returncode,run.stdout+run.stderr)
                self.assertEqual("reproduced",json.loads(run.stdout)["reproduction"]["status"])
