"""V4-03 public presentation: exact content, guards, export and compatible API."""
import contextlib
import copy
import io
import itertools
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
from v3_cli import main, execute
from v3_contract import ContractError, element, load, render, sha
from v3_decision_presentation import decision_view
from v3_cli_presentation import USAGE_VIEW, operational_requested, usage_view
from path_utils import filesystem_root, is_within_filesystem_path
import test_v31_review as review_fixture


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts}


class MinimalPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from build_dual_distribution import collect_development
        from dual_distribution import project_files
        cls.payload = project_files(collect_development(ROOT), "v4-03-test", "development-unreleased", plugin_entrypoints=True)

    def setUp(self):
        self.case = review_fixture.IntegralTests(methodName="runTest"); self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root, self.actor = self.case.root, self.case.actor
        self.req, self.prop = self.case.req, self.case.prop
        for name, raw in self.payload.items():
            path = filesystem_root(self.root / name); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        self.exports = tempfile.TemporaryDirectory(prefix="v4-03-export-")
        self.addCleanup(self.exports.cleanup); self.out = Path(self.exports.name)
        self.sequence = itertools.count()

    def invoke(self, action, data=None, flags=()):
        args = [action, str(self.root)]
        if data is not None:
            source = self.out / ("input-" + str(next(self.sequence)) + ".json")
            source.write_text(json.dumps(data), encoding="utf-8"); args += ["--input", str(source)]
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout): code = main([*args, *map(str, flags)])
        return code, json.loads(stdout.getvalue()), stdout.getvalue()

    def decision(self):
        return {"event": "close-proposal", "data": {"actor": self.actor, "request": self.req,
                "statement": "Synthetic explicit review", "review": True}}

    def test_context_keeps_literals_and_does_not_duplicate_diagnostic_text(self):
        literal = "CONDICION-UNICA: no borrar datos; conservar euskara, negación y límite de 30."
        source = self.root / "docs/lks-sdd/unclassified.md"
        source.write_text('---\nschema_version: "3.1"\nartifact_type: "specification"\n---\n\n' + literal + '\n', encoding="utf-8")
        before = snapshot(self.root)
        c, old, old_text = self.invoke("context", {"roots": [self.prop]}, ["--json"])
        n, new, new_text = self.invoke("context", {"roots": [self.prop]}, ["--json", "--view", "operational"])
        self.assertEqual((0, 0), (c, n))
        # Cache hit/miss describes distinct calls, independently of display mode.
        self.assertEqual({k:v for k,v in old.items() if k not in {"usage", "runtime_cache"}},
                         {k:v for k,v in new.items() if k not in {"usage", "runtime_cache"}})
        self.assertGreaterEqual(old_text.count(literal), 2)
        self.assertEqual(1, new_text.count(literal))
        self.assertLess(len(new_text.encode("utf-8")), len(old_text.encode("utf-8")))
        self.assertEqual(USAGE_VIEW, new["usage"]["format"])
        self.assertNotIn("observations", new["usage"])
        self.assertFalse(new["usage"]["complete_observations_emitted"])
        self.assertEqual("operational", new["usage"]["transport"]["mode"])
        self.assertEqual(before, snapshot(self.root))
        # A projected view cannot be imported as an observation by mistake.
        from v3_usage import check_batch
        with self.assertRaises(ContractError): check_batch([new["usage"]])

    def test_flag_matrix_preserves_receipt_and_export_precedence(self):
        data = self.decision(); expected = decision_view(self.root, data["event"], data["data"])
        before = snapshot(self.root)
        for view, as_json, detail, export in itertools.product(["compatible", "operational"], [False, True], [None, "--compact", "--details"], [False, True]):
            with self.subTest(view=view, json=as_json, detail=detail, export=export):
                flags = ["--view", view] + (["--json"] if as_json else []) + ([detail] if detail else [])
                path = self.out / ("view-" + str(next(self.sequence)) + ".json")
                if export: flags += ["--output", path]
                code, shown, _ = self.invoke("decision-view", data, flags)
                self.assertEqual(0, code)
                full = json.loads(path.read_bytes()) if export else shown
                self.assertEqual(expected["receipt"], full["receipt"])
                self.assertEqual(expected["markdown"], full["markdown"])
                self.assertEqual(expected["complete"], full["complete"])
                self.assertEqual(expected["issues"], full["issues"])
                if export:
                    self.assertNotIn("markdown", shown)
                    self.assertNotIn("receipt", shown)
                    self.assertEqual(str(path.resolve()), shown["output"])
                    self.assertIn("observations", full["usage"])
                    self.assertEqual(path.stat().st_size, shown["usage"]["transport"]["prepared_file"]["bytes"])
                projected = view == "operational" and (export or detail != "--details")
                self.assertEqual(projected, shown["usage"].get("format") == USAGE_VIEW)
        self.assertEqual(before, snapshot(self.root))

    def test_review_uses_one_body_and_preserves_incomplete_conditions(self):
        from v3_authoring import author
        from test_v3_workflow import commit_packet
        item = copy.deepcopy(load(self.root).get(self.prop).item())
        item["meta"]["revision"] += 1; item["meta"]["data"]["unresolved"] = ["Falta decidir autenticación"]
        commit_packet(self.root, author(self.root, self.actor, [item]))
        code, value, _ = self.invoke("review", {"request": self.req}, ["--view", "operational", "--json"])
        self.assertEqual(0, code)
        self.assertFalse(value["presentation"]["complete"])
        self.assertIn("Falta decidir autenticación", value["presentation"]["markdown"])
        self.assertTrue(value["presentation"]["receipt"])
        self.assertNotIn("sources", value["presentation"])
        self.assertTrue(all("details" not in u and "description" not in u for u in value["units"]))
        code, exported, _=self.invoke("review",{"request":self.req},["--view","operational","--output",self.out/"review.json"])
        self.assertEqual(0,code)
        self.assertEqual(value["next"],exported["next"])
        self.assertEqual(value["planning_coverage"],exported["planning_coverage"])
        self.assertEqual(value["collaboration"],exported["collaboration"])
        self.assertEqual(value["presentation"]["issues"],exported["presentation"]["issues"])
        self.assertFalse(exported["presentation"]["complete"])

    def test_long_decision_tail_and_receipt_guard_are_unchanged(self):
        from v3_authoring import author
        from test_v3_workflow import commit_packet
        item = copy.deepcopy(load(self.root).get(self.prop).item()); item["meta"]["revision"] += 1
        item["body"] = "Contenido literal completo.\n" * 1000 + "NO OMITIR ESTA NEGACION FINAL."
        commit_packet(self.root, author(self.root, self.actor, [item]))
        data = self.decision()
        code, value, _ = self.invoke("decision-view", data, ["--view", "operational"])
        self.assertEqual(0, code); self.assertIn("NO OMITIR ESTA NEGACION FINAL.", value["markdown"])
        view = decision_view(self.root, data["event"], data["data"])
        self.assertEqual(view["receipt"], value["receipt"])
        item["meta"]["revision"] += 1; item["body"] += " Otra obligación posterior."
        commit_packet(self.root, author(self.root, self.actor, [item]))
        failed, body, _ = self.invoke("close-proposal", {**data["data"], "presented": value["receipt"]}, ["--view", "operational"])
        self.assertEqual(2, failed); self.assertEqual("blocked", body["status"])

    def test_nested_business_usage_fields_and_asset_obligations_are_not_filtered(self):
        item = element("interface", "Interfaz incierta", "No excluir esta interfaz.", usage="Campo contractual de negocio", usage_context="Contexto contractual")
        path = self.root / "docs/lks-sdd/interface.md"; path.write_bytes(render(item, "3.1"))
        code, value, _ = self.invoke("context", {"roots": [self.prop]}, ["--view", "operational"])
        self.assertEqual(0, code)
        source = next(s for s in value["sources"] if s["key"] == item["meta"]["uid"])
        self.assertEqual("Campo contractual de negocio", source["meta"]["data"]["usage"])
        self.assertEqual("Contexto contractual", source["meta"]["data"]["usage_context"])
        visual = {"event": "visual-choice", "data": {"screens": ["Inicio"], "assets": ["missing.png"], "alternatives": ["Claro"], "recommendation": "Claro", "selection_scope": "Inicio"}}
        code, result, _ = self.invoke("decision-view", visual, ["--view", "operational"])
        self.assertEqual(0, code); self.assertFalse(result["complete"]); self.assertTrue(result["issues"])
        for view in ("compatible", "operational"):
            code, exported, _ = self.invoke("decision-view", visual, ["--view", view, "--output", self.out/(view+"-incomplete.json")])
            self.assertEqual(0, code)
            self.assertEqual("exported", exported["status"])
            self.assertEqual(result["complete"], exported["complete"])
            self.assertEqual(result["issues"], exported["issues"])
            self.assertNotIn("receipt", exported)
        code, blocked, _ = self.invoke("readiness", {"request":self.req,"actor":self.actor,"action":"authorize-plan"}, ["--view","operational","--output",self.out/"blocked.json"])
        self.assertEqual(2,code); self.assertEqual("blocked",blocked["status"])
        self.assertTrue(blocked["causes"])
        self.assertEqual(json.loads((self.out/"blocked.json").read_bytes())["next"],blocked["next"])

    def test_export_cannot_overwrite_consumer_or_input_before_application(self):
        (self.root/"app.py").write_text("answer = 42\n",encoding="utf-8")
        before=snapshot(self.root)
        for view, destination in itertools.product(("compatible","operational"),
                (self.root/"app.py", self.root/".lks-sdd/project.json", self.root/"new"/"Ámbito"/"export.json")):
            with self.subTest(view=view,destination=destination):
                code, blocked, _=self.invoke("context",{"roots":[self.prop]},["--view",view,"--output",destination])
                self.assertEqual(2,code); self.assertIn("outside the consumer",blocked["cause"])
        source=self.out/"same.json"; source.write_text(json.dumps({"roots":[self.prop]}),encoding="utf-8")
        raw=source.read_bytes()
        for view in ("compatible","operational"):
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                code=main(["context",str(self.root),"--input",str(source),"--output",str(source),"--view",view])
            self.assertEqual(2,code); self.assertIn("replace its input",json.loads(stdout.getvalue())["cause"])
            self.assertEqual(raw,source.read_bytes())
        packet=self.out/"guarded.json"
        code, preview, _=self.invoke("author",{"actor":self.actor,"items":[element("request","Protección export","No aplicar si el transporte es inválido")]},["--output",packet])
        self.assertEqual(0,code)
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            code=main(["apply",str(self.root),"--input",str(packet),"--authorize",preview["preview_hash"],"--output",str(self.root/"app.py"),"--view","operational"])
        self.assertEqual(2,code); self.assertNotIn("effects",json.loads(stdout.getvalue()))
        self.assertEqual(before,snapshot(self.root))

    def test_real_preview_apply_replay_and_error_after_apply_keep_effects(self):
        request = element("request", "Nueva petición sintética", "Sin ejecución de código ni aceptación.")
        data = {"actor": self.actor, "items": [request]}
        packet_path = self.out / "packet.json"
        code, preview, _ = self.invoke("author", data, ["--view", "operational", "--compact", "--output", packet_path])
        self.assertEqual(0, code); self.assertTrue(preview["preview_hash"])
        self.assertNotIn("preview", preview); self.assertNotIn("payload", preview)
        from v3_packet import read
        packet = read(packet_path)
        bad, failure, _ = self.invoke("apply", packet, ["--view", "operational"])
        self.assertEqual(2, bad); self.assertIn("autorizar", failure["cause"])
        # An export failure after the first real apply must disclose its effects.
        impossible = self.out / "directory"; impossible.mkdir()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            good = main(["apply", str(self.root), "--input", str(packet_path), "--authorize", preview["preview_hash"], "--view", "operational", "--output", str(impossible)])
        applied = json.loads(stdout.getvalue()); self.assertEqual(2, good)
        self.assertIn(applied["effects"]["status"], {"applied", "completed"})
        self.assertTrue(applied["effects"]["receipt"])
        self.assertTrue(applied["effects"]["writes"])
        before = snapshot(self.root)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["apply", str(self.root), "--input", str(packet_path), "--authorize", preview["preview_hash"], "--view", "operational", "--details", "--output", str(impossible)])
        failure = json.loads(stdout.getvalue()); self.assertEqual(2, code)
        self.assertEqual("previously-applied", failure["effects"]["status"])
        self.assertEqual([], failure["effects"]["writes"])
        self.assertTrue(failure["effects"]["receipt"])
        self.assertIn("observations", failure["usage"])
        # A successful replay export includes its own observations, not a dangling reference.
        exported = self.out / "applied.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(["apply", str(self.root), "--input", str(packet_path), "--authorize", preview["preview_hash"], "--view", "operational", "--output", str(exported)])
        self.assertEqual(0, code)
        saved = json.loads(exported.read_bytes()); shown = json.loads(stdout.getvalue())
        self.assertEqual(saved["receipt"], applied["effects"]["receipt"])
        self.assertEqual([r["observation_id"] for r in saved["usage"]["observations"]],
                         [r["observation_id"] for r in shown["usage"]["observation_refs"]])
        self.assertEqual(before, snapshot(self.root))
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            code=main(["apply",str(self.root),"--input",str(packet_path),"--authorize",preview["preview_hash"],"--view","compatible","--output",str(impossible)])
        self.assertEqual(2,code); self.assertEqual("previously-applied",json.loads(stdout.getvalue())["effects"]["status"])
        self.assertEqual(before,snapshot(self.root))

    def test_direct_apply_output_failure_keeps_effects_capture_and_exact_recovery(self):
        import diagnostic_capture as dc
        for view in ('compatible','operational'):
            request=element('request','Aplicación directa '+view,'Solo un registro sintético autorizado.')
            impossible=self.out/('directory-'+view);impossible.mkdir()
            capture=self.out/('capture-'+view)
            code,failure,_=self.invoke('author',{'actor':self.actor,'items':[request]},
                ['--apply','--view',view,'--output',impossible,'--capture-dir',capture])
            self.assertEqual(2,code,failure)
            self.assertEqual('blocked',failure['status'])
            self.assertEqual('applied',failure['effects']['status'])
            self.assertTrue(failure['effects']['receipt'])
            self.assertEqual(request['body'],load(self.root).get(request['meta']['uid']).body)
            value=dc.load(capture)
            api=json.loads(dc.get(capture,value['entries'][0]['transport']['api_result']))
            self.assertEqual(failure['effects'],api['effects'])
            self.assertEqual('stored',dc.inspect(capture)['status'])
            before=snapshot(self.root)
            code,recovered,_=self.invoke('recover',flags=['--authorize',failure['effects']['preview_hash'],'--view',view])
            self.assertEqual(2,code,recovered)
            self.assertEqual(before,snapshot(self.root))
            code,recovered,_=self.invoke('recover',flags=['--authorize',failure['effects']['preview_hash'],
                '--receipt',failure['effects']['receipt'],'--view',view])
            self.assertEqual(0,code,recovered)
            self.assertEqual('completed',recovered['status'])
            self.assertEqual(before,snapshot(self.root))

    def test_real_recovery_result_keeps_journal_receipt(self):
        from v3_storage import apply
        from v3_packet import read
        path = self.out / "recovery.json"
        code, preview, _ = self.invoke("author", {"actor":self.actor,"items":[element("request","Interrupción","Caso de recuperación")]}, ["--output",path])
        self.assertEqual(0,code)
        with self.assertRaises(InterruptedError): apply(self.root, read(path), preview["preview_hash"], current=True, interrupt_after=1)
        # Recovery is rendered after the real journal resumes; no synthetic success.
        code, recovered, _ = self.invoke("recover", flags=["--authorize",preview["preview_hash"],"--view","operational"])
        self.assertEqual(0,code)
        self.assertIn(recovered["status"], {"completed","applied"})
        self.assertTrue(recovered.get("receipt"))
        self.assertEqual(USAGE_VIEW,recovered["usage"]["format"])

    def test_blocked_queries_preserve_cause_and_do_not_write(self):
        before = snapshot(self.root)
        code, value, _ = self.invoke("context", {"roots": ["missing"]}, ["--view", "operational"])
        self.assertEqual(2, code); self.assertEqual("blocked", value["status"]); self.assertTrue(value["cause"])
        self.assertEqual(before, snapshot(self.root)); self.assertEqual(USAGE_VIEW, value["usage"]["format"])
        code, incomplete, _ = self.invoke("context", {"roots": [self.prop], "usage_context": {"phase":42}}, ["--view", "operational"])
        self.assertEqual(0, code)
        self.assertEqual("incomplete", incomplete["usage"]["status"])
        self.assertEqual("unchanged", incomplete["usage"]["quality"])
        self.assertTrue(incomplete["usage"]["cause"])
        self.assertEqual(before, snapshot(self.root))

    def test_details_keeps_exportable_observations_and_does_not_promote_imports(self):
        from v3_usage import check_batch, imported
        code, value, _ = self.invoke("context", {"roots": [self.prop]}, ["--view", "operational", "--details"])
        self.assertEqual(0, code); rows = value["usage"]["observations"]; check_batch(rows)
        # Parsed transport is unverified input on re-import, regardless of view.
        self.assertEqual("agent-declared", imported(rows[0])["origin"]["kind"])

    def test_mutually_exclusive_flags_fail_before_export(self):
        output = self.out / "forbidden.json"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main(["context",str(self.root),"--compact","--details","--output",str(output)])
        self.assertEqual(2,caught.exception.code); self.assertFalse(output.exists())

    @unittest.skipUnless(os.name == "nt", "real Windows output paths")
    def test_operational_export_to_long_windows_path(self):
        long = filesystem_root(self.out / ("Ámbito con espacios-" + "a"*55) / ("b"*70) / ("c"*70) / "full.json")
        # Resolve Windows 8.3 aliases only after the owned path exists.
        long.parent.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(long.parent) if long.parent.exists() else None)
        self.assertTrue(is_within_filesystem_path(long.parent, self.out))
        self.assertGreater(len(str(long)),260)
        code, value, _ = self.invoke("decision-view", self.decision(), ["--view","operational","--compact","--output",long])
        self.assertEqual(0,code); saved=json.loads(long.read_bytes()); self.assertIn("markdown",saved)
        self.assertNotIn("markdown",value); self.assertEqual(sha(long.read_bytes()),value["usage"]["transport"]["prepared_file"]["sha256"])


class DispatcherPresentationTests(unittest.TestCase):
    def test_export_boundaries_with_missing_long_paths_and_input_hardlinks(self):
        from v3_cli_presentation import export_path
        with tempfile.TemporaryDirectory(prefix="v4-export-guard-") as temp:
            base=Path(temp); consumer=base/"consumer"; consumer.mkdir()
            suffix=Path("Ámbito con espacios")/("a"*70)/("b"*70)/("c"*70)/"export.json"
            with self.assertRaises(ContractError): export_path(consumer/suffix,consumer)
            allowed=export_path(base/"external"/suffix,consumer)
            self.assertFalse(allowed.exists())
            self.assertFalse((base/"external").exists())
            source=base/"input.json"; source.write_text("{}",encoding="utf-8")
            alias=base/"hardlink.json"; os.link(source,alias)
            with self.assertRaisesRegex(ContractError,"replace its input"): export_path(alias,consumer,source)
            self.assertEqual(b"{}",source.read_bytes())
            protected=consumer/"canonical.md"; protected.write_text("SENTINEL",encoding="utf-8")
            consumer_alias=base/"consumer-alias.json"; os.link(protected,consumer_alias)
            with self.assertRaisesRegex(ContractError,"multiply-linked"): export_path(consumer_alias,consumer)
            self.assertEqual("SENTINEL",protected.read_text(encoding="utf-8"))

    def test_actual_large_and_binary_fragment_gaps_and_runtime_remain_visible(self):
        from v3_usage import observe
        row=observe("context",{}, {"sources":[{"key":"large-source","text":"x"*(70*1024)}],
            "attachments":[{"path":"screen.png","requires_observation":True,"sha256":"a"*64,"bytes":40}]})
        reference=usage_view({"observations":[row]})["observation_refs"][0]
        self.assertEqual(row["runtime"],reference["runtime"])
        self.assertEqual(row["window_state"],reference["window_state"])
        self.assertEqual(2,len(reference["fragment_gaps"]))
        self.assertTrue(all(f.get("gap") and f.get("sha256") for f in reference["fragment_gaps"]))
        self.assertTrue(all("text" not in f for f in reference["fragment_gaps"]))
        oversized=observe("context",{"large":"x"*(600*1024)},{"status":"blocked","cause":"Synthetic"})
        limited=usage_view({"observations":[oversized]})["observation_refs"][0]
        self.assertEqual(oversized["input"]["gap"],limited["diagnostic_gaps"]["input"])
        self.assertEqual(oversized["result"]["gap"],limited["diagnostic_gaps"]["result"])

    def test_early_runtime_failure_respects_both_views_and_details(self):
        from lks_sdd import runtime_failure
        for flags, projected in [(["--view","operational"],True),(["--view=operational"],True),(["--view","operational","--details"],False),([],False)]:
            stdout=io.StringIO()
            with contextlib.redirect_stdout(stdout):runtime_failure({"status":"blocked","error":"Pinned runtime integrity failed","writes":[]},"v3",["context","ROOT",*flags])
            result=json.loads(stdout.getvalue());self.assertEqual("blocked",result["status"]);self.assertEqual([],result["writes"])
            self.assertEqual(projected,result["usage"].get("format")==USAGE_VIEW)

    def test_input_filename_cannot_choose_a_view(self):
        self.assertFalse(operational_requested(["--input","--view=operational"]))
        self.assertFalse(operational_requested(["--view","operational","--view","compatible"]))
        self.assertTrue(operational_requested(["--output","--details","--view","operational"]))


class ReceiptTransportTests(unittest.TestCase):
    """Transport boundaries use a controlled core result; no business mutation."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v4-receipt-');self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.root=self.out/'consumer';self.root.mkdir()
        self.literal='Obligación íntegra: NO borrar datos. Euskara ñ.\n'*20

    def result(self,status='completed'):
        return {'format':'lks-sdd-operation-result/1','version':1,'operation':'work-continue/1',
                'operation_id':'observed','status':status,'task':'task','actor':'actor',
                'contract':{'sources':[{'key':'literal','text':self.literal}],'attachments':[]},
                'effects':[{'stage':'start','preview_hash':'exact'}] if status in {'completed','partial'} else [],
                'writes':['execution.md'] if status in {'completed','partial'} else [],
                'conditions':[{'rule':'fresh-stage-guards','satisfied':status=='completed'}],
                'next':'Read the current contract before another operation'}

    def call(self,result,flags=(),action='work-continue'):
        from unittest.mock import patch
        raw=io.StringIO()
        with patch('v3_cli.execute',return_value=copy.deepcopy(result)) as core,contextlib.redirect_stdout(raw):
            code=main([action,str(self.root),'--json',*map(str,flags)])
        return code,json.loads(raw.getvalue()),raw.getvalue(),core

    def test_completed_operational_receipt_preserves_effects_without_claiming_contract_delivery(self):
        result=self.result();before=copy.deepcopy(result)
        code,shown,raw,core=self.call(result,['--view','operational','--apply'])
        self.assertEqual(0,code);self.assertNotIn('contract',shown)
        for field in ('effects','writes','conditions','next'):self.assertEqual(result[field],shown[field])
        self.assertIn('before new work',shown['contract_notice'])
        self.assertEqual(before,result);self.assertTrue(core.call_args.kwargs['apply_work'])
        self.assertEqual(1,raw.count('\n'))

    def test_query_preview_stop_and_partial_always_deliver_exact_literals(self):
        for action,status in [('work-prepare','ready'),('work-continue','ready'),('work-continue','blocked'),
                              ('work-record-results','partial')]:
            with self.subTest(action=action,status=status):
                result=self.result(status);code,shown,raw,_=self.call(result,['--view','operational'],action)
                self.assertEqual(result['contract'],shown['contract'])
                self.assertEqual(self.literal,shown['contract']['sources'][0]['text'])
                self.assertEqual(result['effects'],shown['effects'])

    def test_compatible_details_and_export_keep_full_contract(self):
        result=self.result()
        for flags in ([],['--view','operational','--details']):
            _,shown,_,_=self.call(result,flags);self.assertEqual(result['contract'],shown['contract'])
        exported=self.out/'complete.json'
        _,shown,_,_=self.call(result,['--view','operational','--output',exported])
        self.assertEqual(result['contract'],json.loads(exported.read_bytes())['contract'])
        from path_utils import same_filesystem_path
        self.assertTrue(same_filesystem_path(exported,Path(shown['output'])))

    def test_real_capture_keeps_full_contract_and_exact_compact_stdout(self):
        import diagnostic_capture as dc
        capture=self.out/'capture';result=self.result()
        code,shown,raw,_=self.call(result,['--view','operational','--capture-dir',capture])
        self.assertEqual(0,code);self.assertNotIn('contract',shown)
        self.assertEqual('stored',shown['diagnostic_capture']['status'])
        loaded=dc.load(capture);entry=loaded['entries'][0]
        self.assertEqual(raw.encode(),dc.get(loaded['root'],entry['transport']['stdout']))
        self.assertEqual(result['contract'],json.loads(dc.get(loaded['root'],entry['transport']['api_result']))['contract'])

    def test_capture_failure_still_delivers_effects_and_current_stop_literals(self):
        from unittest.mock import patch
        for status in ('completed','partial'):
            with patch('diagnostic_capture.Capture.store',side_effect=OSError('fault')):
                _,shown,_,_=self.call(self.result(status),['--view','operational','--capture-dir',self.out/status])
            self.assertEqual([{'stage':'start','preview_hash':'exact'}],shown['effects'])
            self.assertEqual('failed',shown['diagnostic_capture']['status'])
            if status=='partial':self.assertEqual(self.literal,shown['contract']['sources'][0]['text'])


if __name__ == "__main__": unittest.main()
