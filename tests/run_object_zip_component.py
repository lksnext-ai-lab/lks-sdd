"""Replay frozen storage bytes/groups only, never a complete S8 lifecycle."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile


def replay(operation, destination, scripts, grouped):
    sys.path.insert(0, str(scripts))
    import content_store
    import path_utils
    from content_store import object_path, reference, read_object
    from v2_contract import relative_parts
    from v2_storage import write_one
    from v3_contract import load
    if grouped:
        from object_zip import Publisher, evaluation
    else:
        evaluation = contextlib.nullcontext
    config = json.loads((operation / "frozen-B.json").read_bytes())
    archive_path = operation / "frozen-B.zip"
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == config["input_zip_sha256"]
    destination.mkdir(parents=True, exist_ok=False)
    objects = ".lks-sdd/objects/sha256/"
    publications = {"loose": 0, "zip": 0, "max_publication_temporary_bytes": 0}
    original = path_utils.publish_new_file
    def counted(path, raw, **kwargs):
        prefix = kwargs.get("prefix", "")
        if prefix == ".lks-object-": publications["loose"] += 1
        if prefix == ".lks-pack-": publications["zip"] += 1
        publications["max_publication_temporary_bytes"] = max(publications["max_publication_temporary_bytes"], len(raw))
        return original(path, raw, **kwargs)
    with zipfile.ZipFile(archive_path) as archive:
        for name, digest in config["initial"].items():
            relative_parts(name, package_data=True)
            raw = archive.read("initial/" + name)
            assert hashlib.sha256(raw).hexdigest() == digest
            write_one(destination, name, raw)
        load(destination).require_valid()
        initial = set(config["initial"])
        path_utils.publish_new_file = content_store.publish_new_file = counted
        began = time.perf_counter()
        try:
            with evaluation():
                for group in config["groups"]:
                    publisher = Publisher(destination) if grouped else None
                    for name in group["publish_sequence"]:
                        raw = archive.read("final/" + name)
                        assert hashlib.sha256(raw).hexdigest() == config["final"][name]
                        if grouped: publisher.add(raw)
                        else: content_store.publish_object(destination, name, raw)
                    if grouped: publisher.flush()
                for name, digest in config["final"].items():
                    if name.startswith(objects): continue
                    raw = archive.read("final/" + name)
                    assert hashlib.sha256(raw).hexdigest() == digest
                    if name not in config["initial"] or config["initial"][name] != digest:
                        write_one(destination, name, raw)
                for name, digest in config["final"].items():
                    if not name.startswith(objects): continue
                    raw = archive.read("final/" + name)
                    assert read_object(destination, reference(raw)) == raw
                load(destination).require_valid()
        finally:
            path_utils.publish_new_file = content_store.publish_new_file = original
        seconds = time.perf_counter() - began
    files = {p.relative_to(destination).as_posix(): p.stat().st_size for p in destination.rglob("*") if p.is_file()}
    assert not initial - set(files), "No initial file may be removed to improve additions"
    for name in initial:
        if name.startswith(objects):
            assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == config["initial"][name]
    added = set(files) - initial
    changed = [name for name in files if name not in config["initial"] or
               hashlib.sha256((destination / name).read_bytes()).hexdigest() != config["initial"][name]]
    return {"status": "passed", "kind": "storage-component-not-full-journey", "grouped": grouped,
            "seconds_component_descriptive": seconds, "groups": len(config["groups"]),
            "new_persistent_files": len(added), "new_persistent_bytes": sum(files[n] for n in added),
            "changed_or_added_complete_bytes": sum(files[n] for n in changed),
            "initial_files_removed": 0, "logical_objects_validated": sum(n.startswith(objects) for n in config["final"]),
            "canonical_and_model_valid": True, "publications": publications,
            "loaded_content_store": content_store.__file__, "input_sha256": config["input_zip_sha256"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--grouped", action="store_true")
    parser.add_argument("--handshake", action="store_true")
    args = parser.parse_args()
    if args.handshake and sys.stdin.buffer.readline() != b"run\n": raise RuntimeError("Missing owned-job handshake")
    result = replay(args.operation, args.destination, args.scripts, args.grouped)
    print(json.dumps(result))


if __name__ == "__main__": main()
