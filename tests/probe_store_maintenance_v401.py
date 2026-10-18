"""V401-01 development probe; never a runtime or automatic release test.

Uses published codecs unchanged. Experimental inventory/manifest code below has
no mutation API and grants no business or maintenance authority.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes as W
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
import object_zip as codec
import store_maintenance as maintenance
from content_store import object_path
from v2_contract import ContractError, canonical, sha

MIB = 1024 * 1024
NODES = 1_000_000
CASES = ("inventory", "maximum_batch", "large_json", "large_unicode_json", "dense_json_within_nodes",
         "dense_json_over_nodes", "large_unicode_key", "unicode_with_metadata",
         "many_unicode_keys", "all_unicode_json", "all_unicode_with_metadata", "metadata")


def constrain_owned_worker():
    """Probe safety only: a nested job caps this worker's private commit at 512 MiB.

    Does not change Codex isolation, machine policy, or the production parser.
    """
    from performance_command import constrain_owned_worker as guard
    return guard()


def inspect_json(raw, logical):
    from store_json_inspector import inspect
    return inspect(raw, logical, node_limit=NODES)


def inventory_case(base):
    objects = base / codec.OBJECTS
    objects.mkdir(parents=True)
    logical = {}
    for i in range(9):
        raw = bytes([65 + i]) * (8 * MIB)
        digest = sha(raw)
        (objects / digest).write_bytes(raw)
        logical[digest] = len(raw)
    target = next(iter(logical))
    ref = {"format": "lks-sdd-object/1", "sha256": target, "bytes": logical[target]}
    for i in range(12):
        raw = canonical({"row": i, "ref": ref, "nodes": [0] * 100_000})
        digest = sha(raw)
        (objects / digest).write_bytes(raw)
        logical[digest] = len(raw)
    del raw
    observed = {p.name: p.stat().st_size for p in objects.iterdir()}
    assert observed == logical
    nodes = refs = 0
    for digest, size in sorted(observed.items()):
        raw = codec.read_logical(base, codec.OBJECTS + digest, maintenance.LIMIT)
        assert len(raw) == size and sha(raw) == digest
        count, found = inspect_json(raw, observed)
        nodes += count
        refs += found
        del raw
    assert sum(logical.values()) > maintenance.LIMIT and nodes > NODES and refs == 12
    missing = canonical({"ref": {**ref, "sha256": "0" * 64}})
    try:
        inspect_json(missing, observed)
    except ContractError:
        pass
    else:
        raise AssertionError("Absent reference accepted")
    return {"status": "passed", "logical_objects": len(logical),
            "logical_bytes": sum(logical.values()), "nodes_checked": nodes,
            "references_checked": refs, "absent_reference_rejected": True,
            "production_preview_exercised": False}


def maximum_batch_case(base):
    bodies = {sha(raw): raw for raw in (bytes([i + 65]) * (8 * MIB) for i in range(8))}
    assert sum(map(len, bodies.values())) == 64 * MIB
    backup = maintenance._backup_bytes(bodies)
    backup_size, first = len(backup), sha(backup)
    assert backup_size == 64 * MIB + 204 * len(bodies) + 22
    assert backup_size <= 66 * MIB
    with zipfile.ZipFile(io.BytesIO(backup)) as archive:
        assert set(archive.namelist()) == set(bodies)
        for digest in bodies:
            assert archive.read(digest) == bodies[digest]
    del backup
    backup = maintenance._backup_bytes(dict(reversed(list(bodies.items()))))
    assert sha(backup) == first
    del backup
    packs = []
    for group in maintenance._groups(bodies):
        encoded = codec.encode(group)
        digest = sha(encoded)
        destination = base / (codec.PACKS + digest + ".zip")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encoded)
        assert encoded == codec.encode(dict(reversed(list(group.items()))))
        packs.append(digest)
        del encoded
    with codec.evaluation():
        for digest, raw in bodies.items():
            assert codec.read_logical(base, codec.OBJECTS + digest, maintenance.LIMIT) == raw
    return {"status": "passed", "logical_bytes": 64 * MIB, "objects": len(bodies),
            "backup_bytes": backup_size, "backup_sha256": first, "packs": len(packs),
            "order_independent_bytes": True, "actual_dual_reader_roundtrip": True}


def json_case(case):
    size = 64 * MIB
    resident = None
    if case in {"unicode_with_metadata", "all_unicode_with_metadata"}:
        rows = [{"sha256": sha(str(i).encode()), "bytes": 65_536, "loose": True} for i in range(50_000)]
        resident = (rows, canonical(rows), {r['sha256']:r['bytes'] for r in rows}, bytearray(16 * MIB))
        case = "all_unicode_json" if case == "all_unicode_with_metadata" else "large_unicode_json"
    if case in {"large_json", "large_unicode_json", "large_unicode_key"}:
        prefix, suffix = b'{"payload":"', b'"}'
        if case == "large_unicode_json":
            prefix += "\U0001f600".encode("utf-8")
        elif case == "large_unicode_key":
            prefix, suffix = b'{"' + "\U0001f600".encode("utf-8"), b'":0}'
        raw = prefix + b"x" * (size - len(prefix) - len(suffix)) + suffix
    elif case == "many_unicode_keys":
        data = io.BytesIO(); data.write(b'{')
        for i in range(999_998):
            key = ('K' + str(i).zfill(6) + 'x' * 49 + "\U0001f600").encode('utf-8')
            data.write(b'"' + key + b'":0,')
        data.write(b'"last'); data.write("\U0001f600".encode('utf-8'))
        data.write(b'x' * (size - data.tell() - 4)); data.write(b'":0}')
        raw = data.getvalue(); data.close()
    elif case == "all_unicode_json":
        prefix, suffix = b'{"payload":"', b'"}'
        count, remainder = divmod(size - len(prefix) - len(suffix), 4)
        raw = prefix + "\U0001f600".encode('utf-8') * count + b'x' * remainder + suffix
    else:
        count = 999_999 if case == "dense_json_within_nodes" else (size - 4) // 5
        prefix = b"[" + b'"ab",' * (count - 1) + b'"'
        raw = prefix + b"x" * (size - len(prefix) - 2) + b'"]'
        del prefix
    assert len(raw) == size
    try:
        from store_json_inspector import prepare, inspect_prepared
        prepared = prepare(raw)
        del raw  # Source stays on disk in the real inventory; never retain both.
        nodes, refs = inspect_prepared(prepared, {}, node_limit=NODES)
    except MemoryError:
        return {"status": "memory-limit-before-node-guard", "input_bytes": size,
                "worker_private_commit_limit": 512 * MIB,
                "production_memory_enforcement": False}
    except ContractError as exc:
        return {"status": "rejected-by-node-budget", "input_bytes": size, "reason": str(exc)}
    expected = NODES if case in {"dense_json_within_nodes", "many_unicode_keys"} else 2
    assert nodes == expected and refs == 0, (case, nodes, refs)
    return {"status": "passed", "input_bytes": size, "nodes_checked": nodes,
            "references_checked": refs, "resident_metadata_rows": 50_000 if resident is not None else 0,
            "resident_extra_index_bytes":16 * MIB if resident is not None else 0}


def metadata_case():
    # Layout stress only; these are not claims of physically verified objects.
    objects = [{"sha256": sha(str(i).encode()), "bytes": 65_536, "loose": True}
               for i in range(50_000)]
    objects.sort(key=lambda x: x["sha256"])
    batches = []
    for first in range(0, len(objects), 1024):
        count = min(1024, len(objects) - first)
        batches.append({"first": first, "count": count,
            "backup": {"sha256": "a" * 64, "bytes": count * 65_536 + 204 * count + 22},
            "packs": [{"sha256": sha(str(start).encode()), "bytes": 128 * 65_536 + 204 * 128 + 22,
                       "members": list(range(start, min(start + 128, first + count)))}
                      for start in range(first, first + count, 128)]})
    manifest = {"format": "lks-sdd-store-maintenance/2", "operation": "physical-compaction",
                "pin_sha256": "b" * 64, "destinations": {"backup_dir": "C:/probe/backup", "restore": "C:/probe/restore"},
                "objects": objects, "existing_packs": {}, "batches": batches,
                "limits": {"batch_bytes": 64 * MIB, "batch_objects": 4096},
                "space_policy": "logical-backup-plus-restore-plus-packs-plus-overhead"}
    raw = canonical(manifest)
    key = sha(raw)
    journal = {"schema_version": manifest["format"], "manifest": manifest, "preview_hash": key,
               "phase": "owned", "removal_authorized": False, "progress": {}}
    journal_bytes = len(canonical(journal))
    assert len(raw) <= 12 * MIB and journal_bytes <= 16 * MIB
    assert sha(canonical({"manifest": manifest, "free_bytes": 1}["manifest"])) == key
    assert sha(canonical({"manifest": manifest, "free_bytes": 2}["manifest"])) == key
    return {"status": "passed", "physical_inventory": False, "logical_rows": len(objects),
            "manifest_bytes": len(raw), "journal_bytes": journal_bytes,
            "manifest_sha256": key, "hash_excludes_observed_free_space": True,
            "layout": "single sorted object table; batch ranges; integer pack members"}


def worker(case, base):
    if sys.stdin.buffer.readline() != b"run\n":
        raise RuntimeError("Missing accounting handshake")
    kernel, handle = constrain_owned_worker()
    started = time.perf_counter()
    try:
        if case == "inventory":
            result = inventory_case(base)
        elif case == "maximum_batch":
            result = maximum_batch_case(base)
        elif case == "metadata":
            result = metadata_case()
        else:
            result = json_case(case)
        result["worker_seconds"] = time.perf_counter() - started
        return result
    finally:
        kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", type=Path, required=True)
    parser.add_argument("--worker", choices=CASES)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker, args.operation), ensure_ascii=False))
        return
    from performance_command import run
    operation = args.operation.resolve(strict=True)
    marker = operation / "OWNER.json"
    if json.loads(marker.read_text(encoding="utf-8-sig")).get("task") != "V401-01":
        raise RuntimeError("Unknown operation owner")
    source_files = ["scripts/store_maintenance.py", "scripts/object_zip.py", "scripts/v2_contract.py",
                    "tests/performance_command.py", "tests/probe_store_maintenance_v401.py"]
    bindings = {name: sha((ROOT / name).read_bytes()) for name in source_files}
    report = {"task": "V401-01", "source_sha256": bindings, "cases": {},
              "production_changed": False, "full_volume_runs": 0,
              "Windows_H2": "pending-untouched", "installed": False, "published": False,
              "billed_tokens": None}
    for case in CASES:
        base = operation / ("fixture-" + case)
        base.mkdir(exist_ok=False)
        try:
            result, metrics = run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
                "--operation", str(base), "--worker", case], ROOT,
                "v401-01-" + case, timeout=120, direct_worker=True)
            report["cases"][case] = {"result": result, "resources": metrics}
        except Exception as exc:
            report["cases"][case] = {"status": "probe-error", "reason": str(exc)}
        finally:
            # Only the checked, newly created child of this owned operation.
            if base.resolve(strict=True).parent != operation or not base.name.startswith("fixture-") or base.is_symlink():
                raise RuntimeError("Unsafe synthetic cleanup target")
            shutil.rmtree(base)
        report["cases"][case]["owned_fixture_removed"] = not base.exists()
        (operation / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(case + ": " + report["cases"][case].get("result", {}).get("status", "probe-error"), flush=True)
    assert all(sha((ROOT / name).read_bytes()) == digest for name, digest in bindings.items())
    report["sources_stable"] = True
    report["owned_active_descendants"] = 0 if all(
        row.get("resources", {}).get("job_active_processes_at_exit") == 0 for row in report["cases"].values()) else None
    (operation / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
