"""Independent, bounded portable diagnostics. Imported material is never executed."""
from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile

from v3_contract import ContractError, canonical, fingerprint, sha
from v3_usage import BATCH_BYTES, WINDOW_COUNT, validate
from usage_report import report

LIMIT = 64 * 1024 * 1024
MAX_FILES = 10000


def name(value):
    if not isinstance(value, str) or not value or len(value) > 1024 or "\\" in value or ":" in value or "\x00" in value:
        raise ContractError("Unsafe bundle path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in {".", ".."} or part.endswith((".", " ")) for part in value.split("/")):
        raise ContractError("Unsafe bundle path")
    if str(p) != value or any(part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM"+str(n) for n in range(1,10)), *("LPT"+str(n) for n in range(1,10))} for part in p.parts):
        raise ContractError("Unsafe bundle path")
    return value


def no_links(path):
    path = Path(os.path.abspath(path))
    from path_utils import file_attributes, filesystem_root
    native = filesystem_root(path, force_extended=True)
    for p in [native, *native.parents]:
        # Fresh native attributes include reparse points without following their
        # targets. Unavailable observations retain the portable lstat/error path.
        attributes = file_attributes(p)
        if attributes is not None:
            if attributes & 0x400:
                raise ContractError("Bundle symlinks/junctions/reparse points are forbidden")
            continue
        try: info = p.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ContractError("Bundle symlinks/junctions/reparse points are forbidden")
    return path


def assess(rows, findings, material, *, dependencies=()):
    from v3_usage import check_fragment
    missing = ["Required external dependency is not included: " + d for d in dependencies]
    source_bytes = {sha(raw):raw for raw in material.values()}
    if not rows: missing.append("No observations in the selected case")
    if not findings and not any(r["stage"] == "failed" for r in rows):
        missing.append("No substantiated trigger; supply a bounded case and expected behavior")
    for r in rows:
        if r["input"].get("gap") or r["result"].get("gap"): missing.append("Exact input/result missing: " + r["observation_id"])
        for f in r["fragments"]:
            if "text" not in f and f["sha256"] not in source_bytes:
                missing.append("Missing source bytes: " + f["source"])
            elif f["sha256"] in source_bytes: check_fragment(f,source_bytes[f["sha256"]])
        if r["stage"] == "failed" and not (r["result"].get("cause") or r["result"].get("causes")):
            missing.append("Exact error absent: " + r["observation_id"])
    for f in findings:
        involved = [r for r in rows if r["observation_id"] in f["occurrences"]]
        if f["rule"] in {"UF-01", "UF-02", "UF-05"} and any(r["operation"] in {"context","work-prepare"} for r in involved):
            if "reproduction/fixture.json" not in material: missing.append("Context graph, roots and selection revisions required: reproduction/fixture.json")
            else:
                try:
                    graph = check_fixture(json.loads(material["reproduction/fixture.json"]))
                    for r in involved:
                        if r["operation"] not in {"context","work-prepare"}: continue
                        observed = {part["source"]:part["sha256"] for part in r["fragments"]}
                        roots=r["input"].get("roots") or r.get("result",{}).get("roots")
                        matches = [case for case in graph["cases"] if case["roots"] == roots
                                   and all(case["expected_sources"].get(k) == v for k,v in observed.items())]
                        if not matches: missing.append("Reproduction graph does not recover this observed selection: " + r["observation_id"])
                except (ContractError, ValueError, KeyError, TypeError) as exc: missing.append("Invalid context reproduction material: " + str(exc))
        if f["rule"] in {"UF-04", "UF-05", "UF-06", "UF-07"}:
            for r in involved:
                if f["rule"] == "UF-04" and "evidence/freshness.json" not in material: missing.append("Prepared base and intervening change required: evidence/freshness.json")
                for d in r.get("declarations", []):
                    expected_type = {"UF-05":"late-context","UF-06":"repeated-question","UF-07":"diagnostic-overhead"}.get(f["rule"])
                    if expected_type and d.get("type") != expected_type: continue
                    required = {"UF-05": ("before", "after", "contract", "defect", "check"), "UF-06": ("question", "decision", "scope", "intervention"), "UF-07": ("evidence",)}.get(f["rule"], ())
                    for key in required:
                        path = d.get(key)
                        if not isinstance(path, str) or path not in material or not material[path].strip(): missing.append("Missing declared evidence: " + str(path or key))
                    if f["rule"] == "UF-05" and all(d.get(k) in material for k in required):
                        try:
                            before,after,defect,check = [json.loads(material[d[k]]) for k in ("before","after","defect","check")]
                            if (before == after or defect["actual"] != before["result"] or defect["expected"] != check["expected"]
                                    or after["result"] != check["actual"] or check["actual"] != check["expected"]):
                                missing.append("Late-context before/after/defect/check do not form a coherent case")
                            if "reproduction/fixture.json" in material:
                                graph = check_fixture(json.loads(material["reproduction/fixture.json"]))
                                selections = [set(case["expected_sources"]) for case in graph["cases"]]
                                if set(before["selection"]) not in selections or set(after["selection"]) not in selections:
                                    missing.append("Late-context reproduction graph does not recover declared before/after selections")
                        except (ValueError,TypeError,KeyError,ContractError): missing.append("Late-context evidence needs structured before/after/defect/check")
        if f["state"] == "needs-evidence": missing.append("Finding needs evidence: " + f["finding_id"])
    # An early failure still needs its expected runtime boundary to be investigable.
    if not findings and any(r["stage"] == "failed" for r in rows) and "evidence/expected.json" not in material:
        missing.append("Expected runtime/behavior and environment required: evidence/expected.json")
    if "evidence/expected.json" in material:
        try:
            expectation = json.loads(material["evidence/expected.json"])
            if not isinstance(expectation, dict) or not expectation.get("expected"): missing.append("Expected runtime behavior is not substantiated")
        except (ValueError, TypeError): missing.append("Expected runtime material must be structured JSON")
    for f in findings:
        for change in f["history"]:
            if change["state"] == "resolved-with-evidence" and change.get("evidence") not in material:
                missing.append("Resolution evidence absent: " + str(change.get("evidence")))
    return sorted(set(missing))


def selection_sources(result):
    """Literal selection identity includes observed binary obligations."""
    selected={s["key"]:sha(s["text"].encode("utf-8")) for s in result["sources"]}
    for asset in result.get("attachments",[]):
        if asset["path"] in selected:raise ContractError("Ambiguous selected source identity")
        selected[asset["path"]]=asset["sha256"]
    return selected


def fixture(root, roots, *, byte_budget=LIMIT):
    """Explicit snapshot for a focal case; preserves bytes, not a code backup."""
    from v3_contract import load, read_bytes
    from v3_context import select
    model = load(root).require_valid()
    files={};total=0
    for p in model.hashes:
        if not (p.startswith(("docs/lks-sdd/", ".lks-sdd/objects/")) or p == ".lks-sdd/project.json"):continue
        if len(files)>=MAX_FILES:raise ContractError("Reproduction path budget exceeded")
        raw=read_bytes(root,p,limit=max(0,min(LIMIT,byte_budget)-total));total+=len(raw)
        if sha(raw)!=model.hashes[p]:raise ContractError("Documentary fixture source changed while reading")
        files[p]=base64.b64encode(raw).decode("ascii")
    selected = select(model, roots)
    for asset in selected.get("attachments", []):
        p=asset["path"]
        if p in files:continue
        if len(files)>=MAX_FILES:raise ContractError("Reproduction path budget exceeded")
        raw=read_bytes(root,p,limit=max(0,min(LIMIT,byte_budget)-total));total+=len(raw)
        if sha(raw)!=asset["sha256"] or len(raw)!=asset["bytes"]:raise ContractError("Documentary attachment changed while reading")
        files[p]=base64.b64encode(raw).decode("ascii")
    value = {"format": "lks-sdd-context-reproduction/1", "cases": [{"files": files, "roots": roots,
              "expected_sources": selection_sources(selected)}]}
    check_fixture(value)
    return value


def check_fixture(value):
    if not isinstance(value, dict) or set(value) != {"format", "cases"} or value["format"] != "lks-sdd-context-reproduction/1":
        raise ContractError("Unsupported reproduction format")
    if not isinstance(value["cases"], list) or not 1 <= len(value["cases"]) <= 3: raise ContractError("Invalid reproduction cases")
    total, paths = 0, 0
    for case in value["cases"]:
        if not isinstance(case, dict) or set(case) != {"files", "roots", "expected_sources"} or not isinstance(case["files"], dict) or not case["files"]:
            raise ContractError("Missing source graph")
        if not isinstance(case["roots"], list) or not 1 <= len(case["roots"]) <= 1000 or not all(isinstance(k,str) for k in case["roots"]): raise ContractError("Invalid reproduction roots")
        if not isinstance(case["expected_sources"], dict) or not case["expected_sources"]: raise ContractError("Missing expected selection")
        paths += len(case["files"])
        if paths > MAX_FILES: raise ContractError("Reproduction path budget exceeded")
        for p,b in case["files"].items():
            name(p)
            if not (p.startswith(("docs/lks-sdd/", ".lks-sdd/objects/")) or p == ".lks-sdd/project.json"): raise ContractError("Reproduction contains non-documentary material")
            if not isinstance(b,str) or len(b) > 4*((LIMIT+2)//3): raise ContractError("Excessive reproduction object")
            total += (len(b)//4)*3
            if total > LIMIT: raise ContractError("Aggregate reproduction exceeds budget")
    return value


def reproduce(files):
    """Trusted selector only. Never launch supplied commands or import code."""
    from v3_contract import load
    from v3_context import select
    value = check_fixture(json.loads(files["reproduction/fixture.json"]))
    outcomes = []
    from path_utils import filesystem_root
    for case in value["cases"]:
        with tempfile.TemporaryDirectory(prefix="lks-usage-reproduction-",dir=filesystem_root(tempfile.gettempdir(),force_extended=True)) as temp:
            root = filesystem_root(temp)
            io_root = filesystem_root(temp,force_extended=True)
            for p,b in case["files"].items():
                raw = base64.b64decode(b, validate=True)
                path = io_root/name(p); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            result = select(load(root).require_valid(), case["roots"])
            actual = selection_sources(result)
            outcomes.append({"passed":actual == case["expected_sources"], "expected":case["expected_sources"], "actual":actual})
    return {"status":"reproduced" if all(o["passed"] for o in outcomes) else "not-reproduced",
            "scope":"literal context selections in isolated documentary fixtures; no code/causality/host acceptance claim",
            "fixture_sha256":sha(files["reproduction/fixture.json"]), "runtime":__import__("v3_usage").runtime_info(), "cases":outcomes}


def preview(data):
    from evidence_safety import sanitize
    original = data.get("observations", [])
    if not isinstance(original, list) or len(original) > WINDOW_COUNT: raise ContractError("Usage case exceeds window budget")
    if len(canonical(data)) > LIMIT: raise ContractError("Usage case exceeds 64 MiB")
    for row in original: validate(row, "usage-observation")
    # All imports have limited provenance; recomputed integrity is not authenticity.
    from v3_usage import imported
    normalized = [imported(r) for r in original]
    rows, redactions = sanitize(normalized)
    transformations = [{"kind": "credential-pattern-redaction", "location": v, "original_digest": fingerprint(original), "transformed_digest": fingerprint(rows)} for v in redactions]
    for r in rows:
        # Redaction can change exact fragment text; the transformed identity is explicit.
        for f in r["fragments"]:
            if "text" in f:
                raw = f["text"].encode("utf-8")
                if sha(raw) != f["sha256"]:
                    transformations.append({"kind": "fragment-redaction", "source": f["source"], "original_sha256": f["sha256"], "transformed_sha256": sha(raw)})
                    f.update(sha256=sha(raw), bytes=len(raw), end=f["start"]+len(f["text"]))
    supplied = data.get("materials", {})
    if not isinstance(supplied, dict) or len(supplied) > MAX_FILES - 5: raise ContractError("Excessive material inventory")
    materials, folded = {}, set()
    for path, value in supplied.items():
        name(path)
        if path.casefold() in folded or not path.startswith(("sources/", "evidence/", "reproduction/")): raise ContractError("Ambiguous or reserved bundle path")
        folded.add(path.casefold())
        cleaned, places = sanitize(value)
        if isinstance(cleaned,dict) and set(cleaned) == {"encoding","data"} and cleaned["encoding"] == "base64":
            if not isinstance(cleaned["data"],str) or len(cleaned["data"]) > 4*((LIMIT+2)//3): raise ContractError("Excessive binary material")
            raw = base64.b64decode(cleaned["data"],validate=True)
        elif isinstance(cleaned,dict) and "encoding" in cleaned: raise ContractError("Unsupported binary material encoding")
        else: raw = cleaned.encode("utf-8") if isinstance(cleaned, str) else canonical(cleaned)
        if len(raw) > LIMIT: raise ContractError("Material exceeds budget")
        materials[path] = raw
        if places: transformations.append({"kind": "material-redaction", "path": path, "locations": places, "original_digest": fingerprint(value), "transformed_sha256": sha(raw)})
    value = report(rows, selector=data.get("selector"), offset=data.get("offset", 0), limit=data.get("limit", 100), finding_id=data.get("finding_id"))
    missing = assess(rows, value["findings"], materials, dependencies=data.get("dependencies", []))
    if value["next_offset"] is not None: missing.append("Finding page incomplete; select a focal case or export subsequent pages")
    if transformations: missing.append("Redacted case must be rechecked; reproduction not established after transformation")
    files = {"REPORT.md": value["markdown"].encode("utf-8"), "MAINTENANCE-PROMPT.md": value["prompt"].encode("utf-8"),
             "observations.json": canonical({"format": "lks-sdd-usage/1", "observations": rows}), **materials}
    manifest = {"format": "lks-sdd-usage-bundle/1", "status": "needs-material" if missing else "ready-for-investigation",
                "files": {p: {"sha256": sha(b), "bytes": len(b)} for p,b in files.items()}, "selection": value["selector"],
                "missing": missing, "transformations": transformations, "dependencies": data.get("dependencies", []), "reproduction": None}
    validate(manifest, "usage-bundle")
    files["manifest.json"] = canonical(manifest)
    if len(files["manifest.json"]) > BATCH_BYTES or sum(len(b) for b in files.values()) > LIMIT: raise ContractError("Aggregate export exceeds budget; minimize the case")
    encoded = {p: base64.b64encode(b).decode("ascii") for p,b in files.items()}
    return {"format": "lks-sdd-usage-export/1", "status": "export-preview", "export_hash": fingerprint(encoded),
            "files": encoded, "manifest": manifest, "writes": [], "next": "Export these exact bytes to a new external destination"}


def decode(packet):
    if packet.get("format") != "lks-sdd-usage-export/1" or len(packet.get("files", {})) > MAX_FILES:
        raise ContractError("Unsupported export packet")
    values = packet["files"]
    if len(canonical(values)) > 90 * 1024 * 1024: raise ContractError("Encoded export exceeds budget")
    if fingerprint(values) != packet.get("export_hash"): raise ContractError("Export bytes changed since preview")
    files, size, folded = {}, 0, set()
    for p,b in values.items():
        name(p)
        if p.casefold() in folded: raise ContractError("Ambiguous bundle paths")
        folded.add(p.casefold())
        try: raw = base64.b64decode(b, validate=True)
        except (ValueError, TypeError) as exc: raise ContractError("Invalid export encoding") from exc
        size += len(raw)
        if size > LIMIT: raise ContractError("Aggregate export exceeds budget")
        files[p] = raw
    checked = inspect_files(files)
    if packet.get("manifest") != checked["manifest"]: raise ContractError("Export manifest changed since preview")
    return files


def export(packet, destination, authorized_hash, *, consumer=None, interrupt_after=None):
    if authorized_hash != packet.get("export_hash"): raise ContractError("Export hash mismatch")
    files = decode(packet)
    target = no_links(destination)
    if consumer:
        root = Path(consumer).resolve()
        if root == target or root in target.parents or target in root.parents: raise ContractError("Export must be outside the consumer")
    if target.exists(): raise ContractError("Export destination must be new")
    target.parent.mkdir(parents=True, exist_ok=True)
    no_links(target.parent)
    stage = Path(tempfile.mkdtemp(prefix=".lks-usage-incomplete-", dir=target.parent))
    try:
        for i,(p,raw) in enumerate(files.items()):
            path = stage/p; path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            if interrupt_after is not None and i == interrupt_after: raise ContractError("Export interrupted before publication")
        inspect(stage)
        # Windows rename is atomic and fails if the destination appeared meanwhile.
        # POSIX: reserve the destination name before publishing complete contents.
        if os.name != "nt":
            # Hard-link publication is exclusive for a file, but directories need a
            # no-replace rename. Refuse rather than weaken the exact-export contract.
            import ctypes
            libc = ctypes.CDLL(None, use_errno=True)
            if not hasattr(libc, "renameat2"): raise ContractError("Atomic no-replace directory rename unavailable")
            if libc.renameat2(-100, os.fsencode(stage), -100, os.fsencode(target), 1) != 0: raise OSError(ctypes.get_errno(), "Cannot publish bundle exclusively")
        else: os.rename(stage, target)
        return {"status": "exported", "destination": str(target), "export_hash": authorized_hash, "bundle_status": packet["manifest"]["status"], "writes": []}
    finally:
        if stage.exists(): shutil.rmtree(stage)


def inspect_files(files):
    if "manifest.json" not in files or len(files["manifest.json"]) > BATCH_BYTES: raise ContractError("Missing/excessive manifest")
    manifest = validate(json.loads(files["manifest.json"]), "usage-bundle")
    if set(files) != set(manifest["files"]) | {"manifest.json"}: raise ContractError("Missing or unknown bundle files")
    if sum(r["bytes"] for r in manifest["files"].values()) + len(files["manifest.json"]) > LIMIT: raise ContractError("Aggregate bundle exceeds budget")
    for p,ref in manifest["files"].items():
        name(p)
        if len(files[p]) != ref["bytes"] or sha(files[p]) != ref["sha256"]: raise ContractError("Bundle integrity mismatch: " + p)
    value = json.loads(files["observations.json"])
    if set(value) != {"format", "observations"} or value["format"] != "lks-sdd-usage/1": raise ContractError("Unsupported observations")
    rows = value["observations"]
    if not isinstance(rows, list) or len(rows) > WINDOW_COUNT: raise ContractError("Excessive observations")
    for r in rows:
        validate(r, "usage-observation")
        for f in r["fragments"]:
            if f["end"] < f["start"]: raise ContractError("Invalid fragment interval")
            if "text" in f and (sha(f["text"].encode("utf-8")) != f["sha256"] or len(f["text"].encode("utf-8")) != f["bytes"]): raise ContractError("Fragment bytes mismatch")
    from v3_usage import imported
    report_value = report([imported(r) for r in rows], selector=manifest["selection"])
    materials = {p:raw for p,raw in files.items() if p.startswith(("sources/", "evidence/", "reproduction/"))}
    missing = assess(rows, report_value["findings"], materials, dependencies=manifest["dependencies"])
    if manifest["status"] != "needs-material" and (missing or manifest["missing"] or manifest["transformations"]): raise ContractError("Bundle falsely claims investigation readiness")
    if manifest["status"] == "reproduced" and not manifest["reproduction"]: raise ContractError("Reproduced status lacks independent evidence")
    return {"status": "valid", "bundle_status": "needs-material" if missing or manifest["missing"] else "ready-for-investigation",
            "missing": sorted(set(missing + manifest["missing"])), "manifest": manifest, "report": report_value,
            "authenticity": "hashes establish internal integrity only; imported origins are claims",
            "reproduction":{"status":"not-run","imported_claim":manifest["reproduction"]}, "writes": []}


def inspect(directory, *, run_reproduction=False):
    root = no_links(directory)
    manifest_path = root/"manifest.json"
    no_links(manifest_path)
    if manifest_path.stat().st_size > BATCH_BYTES: raise ContractError("Excessive manifest")
    manifest = validate(json.loads(manifest_path.read_bytes()), "usage-bundle")
    if sum(r["bytes"] for r in manifest["files"].values()) + manifest_path.stat().st_size > LIMIT: raise ContractError("Aggregate bundle exceeds budget")
    expected = set(manifest["files"]) | {"manifest.json"}
    allowed_dirs = {str(parent) for p in expected for parent in PurePosixPath(name(p)).parents if str(parent) != "."}
    if len({p.casefold() for p in expected}) != len(expected): raise ContractError("Ambiguous bundle paths")
    files, visited = {}, set()
    for directory, dirs, names in os.walk(root, followlinks=False):
        for entry in dirs:
            if (Path(directory)/entry).relative_to(root).as_posix() not in allowed_dirs: raise ContractError("Unknown bundle directory")
        for entry in dirs + names: no_links(Path(directory)/entry)
        for entry in names:
            path = Path(directory)/entry; p = path.relative_to(root).as_posix(); name(p)
            if p not in expected: raise ContractError("Unknown bundle file: " + p)
            visited.add(p)
        if len(visited) > MAX_FILES: raise ContractError("Excessive bundle files")
    if visited != expected: raise ContractError("Missing bundle material")
    for p in expected:
        path = no_links(root/name(p))
        maximum = BATCH_BYTES if p == "manifest.json" else manifest["files"][p]["bytes"]
        if path.stat().st_size > maximum: raise ContractError("Excessive/corrupt bundle file")
        files[p] = path.read_bytes()
    result = inspect_files(files)
    if run_reproduction:
        if "reproduction/fixture.json" not in files: raise ContractError("No supported reproduction fixture")
        result["reproduction"] = reproduce(files)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["usage-inspect", "usage-export"])
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--authorize")
    parser.add_argument("--reproduce", action="store_true", help="Run only the trusted context selector against documentary fixtures")
    parser.add_argument("--recover-capture",action="store_true",help="Publicar entradas diagnósticas pendientes; no reejecuta operaciones")
    args = parser.parse_args(argv)
    try:
        if args.recover_capture and args.action!="usage-inspect": raise ContractError("Capture recovery requires usage-inspect")
        if args.action == "usage-inspect":
            from path_utils import filesystem_root
            if (filesystem_root(args.path)/"run.json").exists():
                from diagnostic_capture import inspect as capture_inspect, recover as capture_recover
                if args.reproduce: raise ContractError("Capture inspection does not execute reproduction; export a bounded portable case first")
                result=capture_recover(args.path) if args.recover_capture else capture_inspect(args.path)
            elif args.recover_capture: raise ContractError("Not a supported diagnostic capture window")
            else: result = inspect(args.path, run_reproduction=args.reproduce)
        else:
            if not args.input or args.input.stat().st_size > 90*1024*1024: raise ContractError("Missing/excessive export input")
            value = json.loads(args.input.read_bytes())
            result = export(value, args.destination, args.authorize) if args.destination else preview(value)
        if args.output:
            from path_utils import publish_new_file
            out = no_links(args.output); out.parent.mkdir(parents=True, exist_ok=True); publish_new_file(out, canonical(result))
            result = {k:v for k,v in result.items() if k not in {"files", "report"}}
            result["output"] = str(out)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "cause": str(exc)}, ensure_ascii=False)); return 2


if __name__ == "__main__": sys.exit(main())
