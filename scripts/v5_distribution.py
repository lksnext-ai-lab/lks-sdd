"""Curated v5 payloads. The converted consumer needs no v1-v4 runtime modules."""
from __future__ import annotations
import hashlib
import ast
import io
import json
from pathlib import Path
import zipfile
import sys

from v5_core import digest, encode, file_digest, filesystem_root, path_at, read

SKILLS = ("help", "define", "adopt-existing", "assess-readiness", "implement", "verify")
RUNTIME = ("v5_core", "v5_legacy", "v5_migration", "v5_results", "v5_distribution", "v5_cli")


def core_files(root):
    manifest = json.loads((Path(root) / "distribution/v5.json").read_bytes())
    # Repository text has an LF policy; deterministic bundles must agree across
    # Windows checkouts and committed Git blobs.
    return {name: path_at(root, name).read_bytes().replace(b"\r\n", b"\n") for name in manifest["files"]}


def inventory(files):
    return {name: digest(raw) for name, raw in sorted(files.items())}


def runtime_id(core):
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    return version + "-" + digest(encode(inventory(core)).encode())[:12]


def consumer_files(core):
    runtime = ".lks-sdd/runtime/" + runtime_id(core)
    result = {runtime + "/" + name: raw for name, raw in core.items()}
    result[".github/lks-sdd-host.md"] = (
        "# GitHub Copilot / LKS-SDD v5\n\n"
        f"Use `{runtime}` as the pinned core. Its CLI checks integrity automatically; use doctor before direct document edits.\n"
        "Read its six full skills and docs/V5.md. Capabilities, task and one evolving plan are canonical. "
        "Use project adapters once; do not also invoke the installed plugin for the same operation. "
        "Keep host-specific missing tools not-run, never fabricate verification or acceptance. "
        "Do not configure MCP, hooks, providers or personal settings.\n").encode()
    for suffix in SKILLS:
        name = "lks-sdd-" + suffix
        result[".github/skills/" + name + "/SKILL.md"] = (
            f"---\nname: {name}\ndescription: Use GitHub Copilot to " + {
                "help": "understand the LKS-SDD project and resume context.",
                "define": "define requested behavior and its single evolving plan.",
                "adopt-existing": "adopt or explicitly migrate existing project knowledge.",
                "assess-readiness": "assess whether a task can proceed with current decisions.",
                "implement": "implement authorized work and record proportional checks.",
                "verify": "verify results and consolidate the delivered capability."}[suffix] +
            f"\n---\n\nRead `{runtime}/skills/{name}/SKILL.md` and resolve `<plugin-root>` "
            f"to `{runtime}`. The CLI checks integrity automatically; before direct document edits run "
            f"`python {runtime}/scripts/lks_sdd.py doctor --root .`. "
            "Stop on integrity errors; never substitute a different installed runtime. "
            "Follow the full workflow and reuse the current authority.\n").encode()
    result[".lks-sdd/distribution-lock.json"] = encode({"format": "lks-sdd/5-lock", "runtime": runtime,
        "version": json.loads(core[".codex-plugin/plugin.json"])["version"], "files": inventory(result),
        "hosts": ["codex", "copilot"], "entrypoints": "project"}).encode()
    result[".lks-sdd/project.json"] = encode({"schema_version": "5.0", "method_version": "5.0.0",
        "source_of_truth": "docs/sdd", "derived": True}).encode()
    result[".lks-sdd/.gitattributes"] = b"runtime/** -text\ndistribution-lock.json -text\n"
    result[".github/.gitattributes"] = b"/skills/lks-sdd-*/** -text\n/lks-sdd-host.md -text\n"
    return result


def doctor(root):
    root = filesystem_root(root)
    raw = read(root, ".lks-sdd/distribution-lock.json")
    if raw is None:
        return {"status": "unbound", "detail": "Using installed plugin; no consumer-local runtime"}
    lock = json.loads(raw)
    if lock.get("format") != "lks-sdd/5-lock":
        raise ValueError("Legacy project: explicit v5 migration is required before v5 writes")
    errors = [name for name, expected in lock["files"].items()
              if not path_at(root, name).is_file() or file_digest(path_at(root, name)) != expected]
    runtime = path_at(root, lock["runtime"])
    actual = {p.relative_to(Path(root).resolve()).as_posix() for p in runtime.rglob("*") if p.is_file()}
    expected = {name for name in lock["files"] if name.startswith(lock["runtime"] + "/")}
    errors.extend(sorted(actual - expected))
    if errors:
        raise ValueError("Runtime/adapter integrity mismatch: " + ", ".join(errors))
    return {"status": "passed", "runtime": lock["runtime"], "files": len(lock["files"])}


def zip_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return stream.getvalue()


def artifacts(core, source, channel):
    version = json.loads(core[".codex-plugin/plugin.json"])["version"]
    codex = {"plugins/lks-sdd/" + name: raw for name, raw in core.items()}
    codex[".agents/plugins/marketplace.json"] = core["distribution/marketplace.template.json"]
    # Both hosts carry identical full workflows; Copilot changes only routing.
    copilot = {"lks-sdd/core/" + name: raw for name, raw in core.items()}
    for suffix in SKILLS:
        name = "lks-sdd/skills/lks-sdd-" + suffix + "/SKILL.md"
        full = core["skills/lks-sdd-" + suffix + "/SKILL.md"].decode()
        header = full.split("---", 2)[1].replace("Use with Codex.", "Use with GitHub Copilot.")
        copilot[name] = ("---" + header + "---\n\n"
            "Resolve this native plugin root from this file, not cwd. With a project lock "
            "whose entrypoints is project, use its project adapter instead of this duplicate route. "
            "Otherwise read the pinned runtime's full workflow after doctor. Without a project lock "
            f"read [the full workflow](../../core/skills/lks-sdd-{suffix}/SKILL.md); "
            "resolve plugin-root to core. No implicit initialization or migration. "
            "The full workflow controls authority, scope and verification.\n").encode()
    copilot["lks-sdd/plugin.json"] = encode({"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "lks-sdd", "version": version,
        "description": "Capability specifications and one evolving plan per task", "skills": "./skills/"}).encode()
    copilot["lks-sdd/native-integrity.json"] = encode({"format": "lks-sdd/5-native", "source": source,
        "channel": channel, "files": {name[len("lks-sdd/"):]: digest(raw) for name, raw in sorted(copilot.items())}}).encode()
    result = {f"lks-sdd-plugin-v{version}.zip": zip_bytes({"lks-sdd/" + n: b for n, b in core.items()}),
              f"lks-sdd-marketplace-v{version}.zip": zip_bytes(codex),
              f"lks-sdd-copilot-plugin-v{version}.zip": zip_bytes(copilot),
              f"lks-sdd-copilot-v{version}.zip": zip_bytes(consumer_files(core))}
    result["distribution-manifest.json"] = encode({"version": version, "source": source, "channel": channel,
        "runtime": runtime_id(core), "artifacts": inventory(result), "hosts": ["codex", "copilot"],
        "host_acceptance": "not-run", "installation": "not-run", "publication": "not-run"}).encode()
    result["SHA256SUMS"] = "".join(f"{digest(raw)}  {name}\n" for name, raw in sorted(result.items())).encode()
    return result


def validate_payload(core):
    """Validate a curated payload without relying on unshipped source-repo tools."""
    manifest = json.loads(core[".codex-plugin/plugin.json"])
    expected = set(json.loads(core["distribution/v5.json"])["files"])
    if set(core) - {"package-integrity.json"} != expected or manifest["name"] != "lks-sdd":
        raise ValueError("Curated payload inventory/identity mismatch")
    if json.loads(core["distribution/dual.json"])["project_schema"] != "5.0":
        raise ValueError("Unexpected method")
    for name, raw in core.items():
        if name.endswith(".py"):
            tree = ast.parse(raw, filename=name)
            for node in ast.walk(tree):
                modules = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else (
                    [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
                if any(m not in sys.stdlib_module_names and m not in RUNTIME for m in modules):
                    raise ValueError("Unshipped runtime dependency: " + name)
    for suffix in SKILLS:
        raw = core[f"skills/lks-sdd-{suffix}/SKILL.md"]
        if len(raw) < 900 or b"docs/V5.md" not in raw:
            raise ValueError("Incomplete full workflow")
    if "package-integrity.json" in core:
        integrity = json.loads(core["package-integrity.json"])
        # The source builder's inventory is independently bound by its release manifest.
        for item in integrity.get("files", []):
            if item["path"] in core and digest(core[item["path"]]) != item["sha256"]:
                raise ValueError("Packaged source integrity mismatch")
    return {"status": "valid", "version": manifest["version"], "skills": 6,
            "runtime_digest": digest(encode(inventory(core)).encode()), "host_acceptance": "not-run"}
