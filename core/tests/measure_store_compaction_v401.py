"""One supervised frozen 800 MB journey; development evidence, never a release gate.

No model calls, sign-ins, active plugin installs or host configuration changes.
The local supervisor waits for its owned worker and preserves failed fixtures.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
import ctypes
from ctypes import wintypes as W
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import time
import zipfile

MIB = 1024 * 1024
WINDOW = 45 * 60
WORK_WINDOW = 35 * 60


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def io_counters():
    from performance_command import IO
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.GetProcessIoCounters.argtypes = [W.HANDLE, ctypes.POINTER(IO)]
    result = IO()
    if not kernel.GetProcessIoCounters(kernel.GetCurrentProcess(), ctypes.byref(result)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {key: getattr(result, key) for key in ("read_bytes", "write_bytes", "read_ops", "write_ops")}


def worker(args):
    if sys.stdin.buffer.readline() != b"run\n":
        raise RuntimeError("Missing supervisor accounting handshake")
    # Reuse the V401-01 worker-only memory guard; it is not Codex/Windows isolation.
    from performance_command import constrain_owned_worker
    kernel, handle = constrain_owned_worker()
    operation = args.operation.resolve(strict=True)
    marker = json.loads((operation / "OWNER.json").read_text(encoding="utf-8-sig"))
    if marker.get("owner") != "Codex" or "V401-06" not in marker.get("tasks", []):
        raise RuntimeError("Unknown operation owner")
    started = time.monotonic()
    report = {"task": "V401-06", "status": "running", "phases": [], "billed_tokens": None,
              "Windows_H2": "pending-untouched", "installed": False, "published": False,
              "real_consumer_accessed": False, "interruption": "one injected exception after two durable batches",
              "failure_model": "process death covered by small focal test; volume uses exception interruption"}
    fixture = operation / "volume-fixture"
    report["fixture"] = str(fixture)
    progress = operation / "volume-progress.json"
    bindings = {"candidate_zip": digest(args.candidate.read_bytes()), "driver": digest(Path(__file__).read_bytes())}
    report["bindings"] = bindings

    def phase(label, function, *, closing=False):
        if time.monotonic() - started >= (WINDOW if closing else WORK_WINDOW):
            raise RuntimeError("No new phase started: final ten minutes reserved for recovery/closure")
        before, cpu, at = io_counters(), time.process_time(), time.monotonic()
        value = function()
        after = io_counters()
        report["phases"].append({"name": label, "seconds": time.monotonic() - at,
                                 "cpu_seconds": time.process_time() - cpu,
                                 **{key: after[key] - before[key] for key in before},
                                 "io_coverage": "Windows process transfer counters; not physical-disk throughput"})
        report["latest_phase"] = label
        report["elapsed_seconds"] = time.monotonic() - started
        save(progress, report)
        return value

    try:
        if fixture.exists():
            raise RuntimeError("Existing volume fixture preserved; no automatic second campaign")
        if shutil.disk_usage(operation).free < 4 * 1024**3:
            raise RuntimeError("At least 4 GiB initial free space required for fixture plus full maintenance")
        fixture.mkdir()
        consumer = fixture / "consumer"
        consumer.mkdir()

        def extract():
            with zipfile.ZipFile(args.candidate) as archive:
                for entry in archive.infolist():
                    relative = PurePosixPath(entry.filename)
                    if (relative.is_absolute() or ".." in relative.parts or "\\" in entry.filename
                            or ":" in entry.filename or entry.is_dir() or entry.file_size > 64 * MIB
                            or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                        raise RuntimeError("Unsafe candidate fixture entry")
                    path = consumer.joinpath(*relative.parts)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(entry))
            return json.loads((consumer / ".lks-sdd/distribution-lock.json").read_bytes())

        lock = phase("extract-synthetic-runtime", extract)
        runtime = consumer / lock["runtime"]
        sys.path.insert(0, str(runtime / "scripts"))
        import lks_sdd
        import store_compaction as maintenance
        from content_store import reference
        from v2_contract import canonical
        from runtime_doctor import check
        from source_inventory import linked
        assert Path(maintenance.__file__).resolve().is_relative_to(runtime.resolve())
        assert check(consumer)["status"] == "valid"
        definition_data = json.loads(args.definition.read_text(encoding="utf-8-sig"))["frozen_volume_fixture"]
        definition = definition_data["definition"]
        assert digest(canonical(definition)) == definition_data["definition_sha256"]
        report["frozen_definition_sha256"] = definition_data["definition_sha256"]
        initial = []
        canonical_file = consumer / "docs/lks-sdd/canonical-proof.md"
        canonical_file.parent.mkdir(parents=True, exist_ok=True)
        canonical_file.write_bytes(b"Synthetic canonical proof: no functional authority changes.\n")
        initial_nonobjects = {path.relative_to(consumer).as_posix(): digest(path.read_bytes())
                              for path in consumer.rglob("*") if path.is_file()}
        folder = consumer / ".lks-sdd/objects/sha256"
        folder.mkdir(parents=True)

        def object_body(kind, ordinal, size, refs):
            value = {"format": definition["format_field"], "ordinal": ordinal, "kind": kind,
                     "nodes": definition["nodes"], "refs": refs, "padding": ""}
            pad = size - len(canonical(value))
            if pad < 0:
                raise RuntimeError("Frozen object cannot fit its exact size")
            value["padding"] = "x" * pad
            raw = canonical(value)
            assert len(raw) == size
            return raw

        def add(kind, ordinal, size, refs):
            raw = object_body(kind, ordinal, size, refs)
            ref = reference(raw)
            (folder / ref["sha256"]).write_bytes(raw)
            initial.append({"sha256": ref["sha256"], "bytes": size, "protected": kind == "protected",
                            "refs": [item["sha256"] for item in refs]})
            return ref

        def generate():
            protected = [add("protected", -1 - ordinal, 37_862_685, []) for ordinal in range(3)]
            previous = None
            for ordinal in range(10_154):
                if time.monotonic() - started >= WORK_WINDOW:
                    raise RuntimeError("Frozen generation exceeded work window; fixture preserved")
                refs = [] if ordinal % 17 == 0 else [protected[ordinal % 3]] + ([previous] if previous else [])
                previous = add("eligible", ordinal, 67_654 if ordinal < 2499 else 67_653, refs)
            assert len(initial) == 10_157 and sum(row["bytes"] for row in initial) == 800_539_116
            assert len({row["sha256"] for row in initial}) == len(initial)
            save(operation / "initial-objects.json", {"definition_sha256": report["frozen_definition_sha256"], "objects": initial})

        phase("generate-frozen-corpus", generate)
        initial_count = sum(path.is_file() for path in consumer.rglob("*"))
        initial_bytes = sum(path.stat().st_size for path in consumer.rglob("*") if path.is_file())
        def path_key(path):
            value = os.path.abspath(str(path))
            if value.startswith("\\\\?\\UNC\\"):
                value = "\\\\" + value[8:]
            elif value.startswith("\\\\?\\"):
                value = value[4:]
            return os.path.normcase(value)
        lengths = {path_key(path): path.stat().st_size for path in fixture.rglob("*") if path.is_file()}
        occupancy = [sum(lengths.values()), sum(lengths.values())]
        peak_files = [len(lengths)]
        atomic_stack = []
        original_atomic, original_unlink = maintenance._atomic, Path.unlink
        original_checkpoint = maintenance._checkpoint
        interrupt_enabled, prepared_count = [False], [0]
        def observe(paths):
            delta = 0
            for path in paths:
                try:
                    size = path.lstat().st_size
                except FileNotFoundError:
                    size = None
                key_path = path_key(path)
                delta += (size or 0) - lengths.get(key_path, 0)
                if size is not None:
                    lengths[key_path] = size
                else:
                    lengths.pop(key_path, None)
            occupancy[0] += delta
            occupancy[1] = max(occupancy)
            peak_files[0] = max(peak_files[0], len(lengths))
        def tracked_atomic(path, raw, temporary, **options):
            pair = (Path(path), Path(temporary))
            observe(pair)
            atomic_stack.append(pair)
            try:
                return original_atomic(path, raw, temporary, **options)
            finally:
                observe(pair)
                atomic_stack.pop()
        def tracked_unlink(path, *arguments, **options):
            value = original_unlink(path, *arguments, **options)
            if path_key(path).startswith(path_key(fixture) + os.sep):
                observe((path,))
            return value
        def checkpoint(boundary):
            if boundary == "temporary-fsynced" and atomic_stack:
                observe(atomic_stack[-1])
            original_checkpoint(boundary)
            if interrupt_enabled[0] and boundary == "batch-prepared":
                prepared_count[0] += 1
                if prepared_count[0] == 2:
                    raise InterruptedError("Frozen V401-06 interruption after two durable batches")
        maintenance._atomic, maintenance._checkpoint, Path.unlink = tracked_atomic, checkpoint, tracked_unlink
        request = operation / "volume-request.json"
        preview_path = operation / "volume-preview.json"
        backup, restore = fixture / "backup", fixture / "restored"
        save(request, {"backup_dir": str(backup), "restore": str(restore)})

        def cli(action, *arguments):
            out, errors = io.StringIO(), io.StringIO()
            prior = sys.argv
            try:
                sys.argv = [str(runtime / "scripts/lks_sdd.py"), "v3", action, str(consumer), *map(str, arguments)]
                with redirect_stdout(out), redirect_stderr(errors):
                    code = lks_sdd.main()
            finally:
                sys.argv = prior
            value = json.loads(out.getvalue())
            if len(out.getvalue().encode("utf-8")) > 8192:
                raise RuntimeError("Operational stdout exceeds 8 KiB")
            return code, value

        code, shown = phase("public-preview", lambda: cli("store-preview", "--input", request, "--output", preview_path,
                                                           "--view", "operational", "--json"))
        assert code == 0, shown
        plan = json.loads(preview_path.read_bytes())
        manifest, key = plan["manifest"], plan["preview_hash"]
        assert digest(canonical(manifest)) == key
        assert len(manifest["objects"]) == 10_157 and sum(row["bytes"] for row in manifest["objects"]) == 800_539_116
        batch_by_object = {}
        for number, batch in enumerate(manifest["batches"]):
            for row in manifest["objects"][batch["first"]:batch["first"] + batch["count"]]:
                batch_by_object[row["sha256"]] = number
        cross = sum(batch_by_object[row["sha256"]] != batch_by_object[target] for row in initial for target in row["refs"])
        assert cross > 0
        additions = sum(len(batch["packs"]) for batch in manifest["batches"]) + 1
        assert additions <= 507, "Frozen preview cannot achieve >=95% net file reduction"
        report["preview_hash"] = key
        report["scope"] = {"objects": len(initial), "logical_bytes": 800_539_116, "eligible": 10_154,
                            "protected": 3, "batches": len(manifest["batches"]), "cross_batch_refs": cross,
                            "forecast_permanent_internal_additions": additions}
        save(progress, report)
        interrupt_enabled[0] = True
        try:
            code, result = phase("prepare-and-interrupt", lambda: cli("store-compact", "--input", preview_path,
                                    "--authorize", key, "--view", "operational", "--json"))
        finally:
            interrupt_enabled[0] = False
        assert code == 3 and result["effects"]["progress"]["prepared"] == 2, result
        assert len(list(folder.iterdir())) == 10_157
        assert not maintenance.status(consumer, key)["removal_authorized"]

        def continue_until(expected, *, remove=False):
            for attempt in range(8):
                closing = remove and attempt > 0
                if time.monotonic() - started >= (WINDOW if closing else WORK_WINDOW):
                    raise RuntimeError("Reserved recovery margin reached; same pending scope preserved")
                options = ["--authorize", key, "--view", "operational", "--json"]
                if remove:
                    options += ["--authorize-removal", key]
                code, value = phase(("withdraw" if remove else "recover-prepare") + f"-{attempt}",
                                     lambda: cli("store-recover", *options), closing=closing)
                if code == 0 and value.get("status") == expected:
                    return value
                if code != 3 or value.get("status") != "paused":
                    raise RuntimeError("Unexpected recovery state: " + json.dumps(value)[:1800])
            raise RuntimeError("Bounded continuation count exhausted; no new journey")

        continue_until("awaiting-removal-authorization")
        assert len(list(folder.iterdir())) == 10_157
        assert not maintenance.status(consumer, key)["removal_authorized"]
        at_prepared = sum(path.stat().st_size for path in fixture.rglob("*") if path.is_file())
        report["occupancy_meter_consistent_at_prepared"] = at_prepared == occupancy[0]
        assert report["occupancy_meter_consistent_at_prepared"], (at_prepared, occupancy[0])

        def verify_restoration():
            assert {path.name for path in restore.iterdir()} == {row["sha256"] for row in initial}
            for row in initial:
                raw = (restore / row["sha256"]).read_bytes()
                assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]
            return True

        report["independent_restore_verified_before_withdrawal"] = phase("verify-independent-restore", verify_restoration)
        result = continue_until("compacted", remove=True)
        assert not (consumer / ".lks-sdd/transaction.json").exists()
        report["terminal_receipt"] = result["receipt"]

        def final_verification():
            from content_store import read_object
            with maintenance.codec.evaluation():
                for row in initial:
                    raw = read_object(consumer, {"format": "lks-sdd-object/1", "sha256": row["sha256"], "bytes": row["bytes"]})
                    assert digest(raw) == row["sha256"]
            protected = {row["sha256"] for row in initial if row["protected"]}
            assert {path.name for path in folder.iterdir()} == protected
            for name, expected in initial_nonobjects.items():
                assert digest((consumer / name).read_bytes()) == expected
            assert check(consumer)["status"] == "valid"
            assert maintenance.recover(consumer, key)["previously_completed"]
            assert not maintenance._temporary_directory(consumer, key).exists()

        phase("final-logical-and-canonical-verification", final_verification, closing=True)
        final_files = {path.relative_to(consumer).as_posix(): path.stat().st_size for path in consumer.rglob("*") if path.is_file()}
        added = set(final_files) - set(initial_nonobjects) - {".lks-sdd/objects/sha256/" + row["sha256"] for row in initial}
        assert len(added) == additions and (10_154 - len(added)) / 10_154 >= .95
        report["files"] = {"internal_before": initial_count, "internal_after": len(final_files),
                           "eligible_originals_withdrawn": 10_154, "permanent_internal_additions": len(added),
                           "net_reduction_compactable_fraction": (10_154 - len(added)) / 10_154,
                           "external_backups": len(list(backup.iterdir())), "external_restored": len(initial),
                           "observed_peak_fixture_files_including_atomic_temporaries": peak_files[0]}
        report["bytes"] = {"internal_before": initial_bytes, "internal_after": sum(final_files.values()),
                           "external_backup": sum(path.stat().st_size for path in backup.iterdir()),
                           "external_restore": 800_539_116,
                           "temporary_peak_forecast": manifest["space_policy"],
                           "observed_peak_fixture_file_lengths": occupancy[1],
                           "observed_peak_new_file_lengths": occupancy[1] - initial_bytes,
                           "peak_coverage": "File lengths at completed atomic temporaries and removals, including originals/runtime; excludes filesystem allocation granularity and control outputs outside fixture"}
        assert occupancy[0] == sum(path.stat().st_size for path in fixture.rglob("*") if path.is_file())
        shutil.copyfile(consumer / result["receipt"], operation / "maintenance-receipt.json")
        assert bindings == {"candidate_zip": digest(args.candidate.read_bytes()), "driver": digest(Path(__file__).read_bytes())}
        maintenance._atomic, maintenance._checkpoint, Path.unlink = original_atomic, original_checkpoint, original_unlink
        assert not linked(fixture.lstat()) and fixture.resolve(strict=True).parent == operation and fixture.name == "volume-fixture"
        phase("remove-owned-successful-fixture", lambda: shutil.rmtree(fixture), closing=True)
        report.update(status="passed", fixture_removed=not fixture.exists(), elapsed_seconds=time.monotonic() - started,
                      canonical_and_runtime_unchanged=True, all_logical_objects_verified=True,
                      opaque_path_coverage="focal tests reused; frozen volume intentionally uses canonical JSON")
        assert report["elapsed_seconds"] <= WINDOW
    except Exception as exc:
        report.update(status="failed-preserved-for-inspection", cause=repr(exc),
                      fixture_preserved=fixture.exists(), elapsed_seconds=time.monotonic() - started,
                      next="Inspect same fixture and pending/receipt; no automatic new campaign")
    finally:
        if 'original_atomic' in locals():
            maintenance._atomic, maintenance._checkpoint, Path.unlink = original_atomic, original_checkpoint, original_unlink
        kernel.CloseHandle(handle)
        save(progress, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--definition", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if args.worker:
        print(json.dumps(worker(args), ensure_ascii=False))
        return
    from performance_command import run
    result_path = args.operation / "volume-result.json"
    if result_path.exists() or (args.operation / "volume-fixture").exists():
        raise RuntimeError("Existing volume evidence preserved; no automatic repeat")
    result, resources = run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                            "--operation", str(args.operation), "--candidate", str(args.candidate),
                            "--definition", str(args.definition), "--worker"],
                            args.operation, "v401-06-frozen-volume", timeout=WINDOW, direct_worker=True)
    result["resources"] = resources
    if (resources["job_peak_commit_bytes"] > 512 * MIB
            or resources["observed_main_peak_working_set_bytes"] > 512 * MIB
            or resources["job_active_processes_at_exit"] != 0):
        result["status"] = "failed-resource-acceptance"
    save(result_path, result)
    print(json.dumps({"status": result["status"], "result": str(result_path), "seconds": resources["seconds"],
                      "peak_commit_bytes": resources["job_peak_commit_bytes"],
                      "peak_working_set_bytes": resources["observed_main_peak_working_set_bytes"],
                      "files": result.get("files")}))


if __name__ == "__main__":
    main()
