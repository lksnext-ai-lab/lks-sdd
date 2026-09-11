#!/usr/bin/env python3
"""Offline, preview-first installer. No downloads, account changes or activation."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

BEGIN = "<!-- LKS-SDD:BEGIN -->"
END = "<!-- LKS-SDD:END -->"
BLOCK_FILES = {"AGENTS.md", ".github/copilot-instructions.md"}
LOCK = ".lks-sdd-install.lock"
JOURNAL = ".lks-sdd-install-recovery.json"


def filesystem_root(path):
    resolved = str(path.resolve())
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        resolved = "\\\\?\\UNC\\" + resolved[2:] if resolved.startswith("\\\\") else "\\\\?\\" + resolved
    return Path(resolved)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def safe(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe path: {relative!r}")
    parts = PurePosixPath(relative).parts
    if relative.startswith("/") or any(p in {"", ".", ".."} for p in relative.split("/")):
        raise ValueError(f"Unsafe path: {relative}")
    root = filesystem_root(root)
    target = root.joinpath(*parts)
    for candidate in [target, *target.parents]:
        if candidate == root:
            break
        if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
            raise ValueError(f"Links/junctions are not installation targets: {relative}")
    if not target.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes destination: {relative}")
    return target


def read(root, relative):
    path = safe(root, relative)
    if path.exists() and not path.is_file():
        raise ValueError(f"Expected a file: {relative}")
    return path.read_bytes() if path.exists() else None


def block_parts(data):
    text = (data or b"").decode("utf-8")
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError("Ambiguous or incomplete managed instruction block")
    if BEGIN not in text:
        return text, None, ""
    left, rest = text.split(BEGIN, 1)
    middle, right = rest.split(END, 1)
    return left, (BEGIN + middle + END).replace("\r\n", "\n").encode("utf-8"), right


def load_payload(bundle, host):
    manifest = json.loads((bundle / "payload-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0" or not isinstance(manifest.get("files"), dict):
        raise ValueError("Invalid payload manifest")
    files = {}
    payload_name = f"payload/{host}.zip"
    # Validate the whole setup, including launcher scripts, before accepting any bytes.
    for name, expected in manifest["files"].items():
        data = read(bundle, name)
        if data is None or sha(data) != expected:
            raise ValueError(f"Damaged setup payload: {name}")
        if name == payload_name:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                seen = set()
                if sum(item.file_size for item in archive.infolist()) > 1024 * 1024 * 1024:
                    raise ValueError("Payload is too large")
                for item in archive.infolist():
                    safe(bundle, item.filename)
                    if item.filename.casefold() in seen or item.is_dir() or (item.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("Duplicate, directory or linked payload entry")
                    seen.add(item.filename.casefold())
                    files[item.filename] = archive.read(item)
    if not files:
        raise ValueError("Empty host payload")
    return manifest, files


def receipt_name(host):
    return ".lks-sdd/installation.json" if host == "copilot" else ".lks-sdd-installation.json"


def plan(bundle, destination, host, remove=False):
    destination = filesystem_root(destination)
    if host == "copilot" and not destination.is_dir():
        raise ValueError("Copilot destination must be the existing consumer project root")
    if (destination / JOURNAL).exists() or (destination / LOCK).exists():
        raise ValueError("Incomplete installation; inspect and run --recover before retrying")
    receipt_path = receipt_name(host)
    previous = read(destination, receipt_path)
    old = json.loads(previous) if previous else {"files": {}, "host": host, "schema_version": "1.0"}
    if old.get("host") != host or old.get("schema_version") != "1.0":
        raise ValueError("Incompatible installation receipt")
    if remove and previous is None:
        raise ValueError("No managed installation to remove")
    metadata, payload = ({}, {}) if remove else load_payload(bundle, host)
    if previous and (remove or old.get("runtime_digest") != metadata.get("runtime_digest")):
        handoffs = destination / ".lks-sdd/handoffs/visual"
        for request in handoffs.glob("VH-*/request.json") if handoffs.exists() else []:
            if not (request.parent / "result.json").exists() and not (request.parent / "cancelled.json").exists():
                raise ValueError("Close or reconcile pending visual handoffs before changing/removing the runtime")
    desired, ownership = {}, {}
    for name in sorted(set(old["files"]) | set(payload)):
        allowed = (name.startswith("plugins/lks-sdd/") or name == ".agents/plugins/marketplace.json") if host == "codex" else (
            name.startswith(".lks-sdd/runtime/") or name.startswith(".github/skills/lks-sdd-") or name in {
                "AGENTS.md", ".github/copilot-instructions.md", ".github/lks-sdd-host.md",
                ".github/.gitattributes", ".lks-sdd/.gitattributes", ".lks-sdd/distribution-lock.json"})
        if not allowed:
            raise ValueError(f"Out-of-scope installation entry: {name}")
        actual = read(destination, name)
        entry = old["files"].get(name)
        incoming = payload.get(name)
        if name in BLOCK_FILES and host == "copilot":
            left, managed, right = block_parts(actual)
            if entry and (managed is None or sha(managed) != entry["sha256"]):
                raise ValueError(f"Locally edited managed instructions: {name}")
            if managed is not None and not entry:
                raise ValueError(f"Unowned managed block: {name}")
            if incoming is None:
                # Only the block is owned; surrounding instructions are never removed.
                desired[name] = (left + right).encode("utf-8")
                if not desired[name].strip() and entry.get("created_file"):
                    desired[name] = None
            else:
                _, new_block, _ = block_parts(incoming)
                if new_block is None:
                    raise ValueError("Missing instruction block in payload")
                separator = "\n\n" if managed is None and left and not left.endswith("\n\n") else ""
                desired[name] = (left + separator).encode("utf-8") + new_block + right.encode("utf-8")
                ownership[name] = {"sha256": sha(new_block), "kind": "block",
                                   "created_file": entry["created_file"] if entry else actual is None}
        else:
            if entry and (actual is None or sha(actual) != entry["sha256"]):
                raise ValueError(f"Locally modified or missing managed file: {name}")
            if not entry and actual is not None:
                raise ValueError(f"Unowned file collision: {name}")
            desired[name] = incoming
            if incoming is not None:
                ownership[name] = {"sha256": sha(incoming), "kind": "file"}
    desired[receipt_path] = None if remove else encoded({
        "schema_version": "1.0", "host": host, "version": metadata["version"],
        "channel": metadata["channel"], "runtime_digest": metadata["runtime_digest"], "files": ownership,
    })
    changes = []
    for name, content in sorted(desired.items()):
        before = read(destination, name)
        if content != before:
            changes.append({"path": name, "before": sha(before) if before is not None else None,
                            "after": sha(content) if content is not None else None,
                            "content": content.hex() if content is not None else None})
    intent = {"host": host, "destination": str(destination), "remove": remove, "changes": changes}
    return {**intent, "preview_hash": sha(encoded(intent))}


def atomic_write(path, content):
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".lks-sdd-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply(plan_value, authorization):
    if authorization != plan_value["preview_hash"]:
        raise ValueError("Preview changed or authorization hash does not match")
    root = Path(plan_value["destination"])
    if not plan_value["changes"]:
        return
    root.mkdir(parents=True, exist_ok=True)
    lock = safe(root, LOCK)
    lock.mkdir()  # exclusive local writer; never steal a live lock
    backups = []
    try:
        for change in plan_value["changes"]:
            current = read(root, change["path"])
            if (sha(current) if current is not None else None) != change["before"]:
                raise ValueError(f"Concurrent change: {change['path']}")
            backups.append({**change, "original": current.hex() if current is not None else None})
        atomic_write(safe(root, JOURNAL), encoded({"schema_version": "1.0", "changes": backups}))
        for change in backups:
            current = read(root, change["path"])
            if (sha(current) if current is not None else None) != change["before"]:
                raise ValueError(f"Concurrent change during apply: {change['path']}")
            atomic_write(safe(root, change["path"]), bytes.fromhex(change["content"]) if change["content"] is not None else None)
        safe(root, JOURNAL).unlink()
    except Exception:
        # The durable journal permits explicit recovery after a crash/failure.
        raise
    finally:
        lock.rmdir()


def recover(root):
    root = filesystem_root(root)
    path = safe(root, JOURNAL)
    journal = json.loads(path.read_text(encoding="utf-8"))
    if journal.get("schema_version") != "1.0":
        raise ValueError("Invalid recovery journal")
    for change in journal["changes"]:
        current = read(root, change["path"])
        observed = sha(current) if current is not None else None
        if observed not in {change["before"], change["after"]}:
            raise ValueError(f"Recovery would overwrite a later edit: {change['path']}")
        original = bytes.fromhex(change["original"]) if change["original"] is not None else None
        if (sha(original) if original is not None else None) != change["before"]:
            raise ValueError("Corrupt recovery backup")
    for change in reversed(journal["changes"]):
        atomic_write(safe(root, change["path"]), bytes.fromhex(change["original"]) if change["original"] is not None else None)
    path.unlink()
    lock = safe(root, LOCK)
    if lock.is_dir():
        lock.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", choices=["codex", "copilot"])
    parser.add_argument("destination", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--authorize")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    try:
        if args.recover:
            if not args.apply:
                raise ValueError("Recovery writes files; requires --recover --apply and no running installer")
            recover(args.destination.resolve())
            result = {"status": "recovered"}
        else:
            value = plan(Path(__file__).resolve().parent, args.destination, args.host, args.remove)
            if args.apply:
                apply(value, args.authorize)
            result = {"status": "applied" if args.apply else "preview", "host": args.host,
                      "preview_hash": value["preview_hash"], "destination": value["destination"],
                      "changes": [{k: v for k, v in item.items() if k != "content"} for item in value["changes"]]}
            if args.host == "codex" and not args.remove:
                result["activation"] = "Register this destination as a local marketplace, then install lks-sdd@lks-sdd-development and start a new task. No activation was performed."
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
