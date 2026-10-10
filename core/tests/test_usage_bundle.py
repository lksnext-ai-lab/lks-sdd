import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from usage_test_support import repeated, observation, late
from usage_bundle import preview, export, inspect, name
from v3_contract import ContractError

ROOT = Path(__file__).resolve().parents[1]


class BundleTests(unittest.TestCase):
    def test_exact_export_cold_independent_inspection_and_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            rows,materials = late()
            packet = preview({"observations":rows,"materials":materials})
            destination = Path(temp)/"case"
            export(packet,destination,packet["export_hash"])
            checked = inspect(destination)
            self.assertEqual("ready-for-investigation",checked["bundle_status"])
            process = subprocess.run([sys.executable,"-B","-X","utf8",str(ROOT/"scripts/lks_sdd.py"),"usage-inspect",str(destination)],capture_output=True,text=True,encoding="utf-8")
            self.assertEqual(0,process.returncode,process.stdout+process.stderr)
            (destination/"observations.json").write_text("{}")
            with self.assertRaises(ContractError): inspect(destination)

    def test_missing_material_preview_mutation_and_interruption(self):
        with tempfile.TemporaryDirectory() as temp:
            packet = preview({"observations":repeated()})
            self.assertEqual("needs-material",packet["manifest"]["status"])
            mutated = copy.deepcopy(packet); mutated["files"]["REPORT.md"] = "Yg=="
            with self.assertRaises(ContractError): export(mutated,Path(temp)/"changed",packet["export_hash"])
            mutated = copy.deepcopy(packet); mutated["manifest"]["status"] = "ready-for-investigation"
            with self.assertRaises(ContractError): export(mutated,Path(temp)/"changed-metadata",packet["export_hash"])
            with self.assertRaises(ContractError): export(packet,Path(temp)/"interrupted",packet["export_hash"],interrupt_after=0)
            self.assertFalse((Path(temp)/"interrupted").exists())
            export(packet,Path(temp)/"complete",packet["export_hash"])
            with self.assertRaises(ContractError): export(packet,Path(temp)/"complete",packet["export_hash"])

    def test_early_blocked_and_late_context_material_requirements(self):
        row = observation("failed","implement",result={"status":"blocked","cause":"needs-runtime-update"})
        packet = preview({"observations":[row],"materials":{"evidence/expected.json":{"expected":"current pinned runtime","environment":"synthetic Python"}}})
        self.assertEqual("ready-for-investigation",packet["manifest"]["status"])
        rows,materials = late()
        self.assertEqual("ready-for-investigation",preview({"observations":rows,"materials":materials})["manifest"]["status"])
        del materials["evidence/before.json"]
        self.assertEqual("needs-material",preview({"observations":rows,"materials":materials})["manifest"]["status"])

    def test_paths_links_unknown_files_and_false_readiness_reject(self):
        for path in ("../secret","a/../b","/absolute","C:/outside","CON.txt","a\\b","a//b"):
            with self.assertRaises(ContractError): name(path)
        with tempfile.TemporaryDirectory() as temp:
            packet = preview({"observations":repeated()})
            export(packet,Path(temp)/"case",packet["export_hash"])
            (Path(temp)/"case/unknown.txt").write_text("unexpected")
            with self.assertRaises(ContractError): inspect(Path(temp)/"case")
        invalid = preview({"observations":repeated(),"materials":{"reproduction/fixture.json":{"elements":[]}}})
        self.assertEqual("needs-material",invalid["manifest"]["status"])

    def test_coherent_material_is_required_for_late_context(self):
        rows,materials = late()
        materials["evidence/check.json"]["actual"] = "wrong"
        self.assertEqual("needs-material",preview({"observations":rows,"materials":materials})["manifest"]["status"])

    def test_redaction_preserves_original_and_transformed_hashes(self):
        row = observation(text="Authorization: Bearer synthetic-test-token")
        packet = preview({"observations":[row,row],"materials":{}})
        self.assertEqual("needs-material",packet["manifest"]["status"])
        self.assertTrue(packet["manifest"]["transformations"])
        self.assertNotIn("synthetic-test-token",str(packet["manifest"]))

    def test_external_dependencies_and_inconsistent_reference_cannot_claim_readiness(self):
        row = observation("failed","implement",result={"status":"blocked","cause":"synthetic failure"})
        data = {"observations":[row],"materials":{"evidence/expected.json":{"expected":"valid runtime"}},"dependencies":["original consumer database"]}
        self.assertEqual("needs-material",preview(data)["manifest"]["status"])
        with self.assertRaises(ContractError): preview({"observations":[row],"materials":{"sources/asset.bin":{"encoding":"unknown","data":"AA=="}}})
        rows,materials = late()
        f = rows[0]["fragments"][0]; source = f.pop("text")
        f["text_ref"] = {"format":"lks-sdd-object/1","sha256":f["sha256"],"bytes":f["bytes"]}
        f["end"] += 1; materials["sources/observed.txt"] = source
        with self.assertRaisesRegex(ContractError,"interval mismatch"): preview({"observations":rows,"materials":materials})
