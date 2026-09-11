#!/usr/bin/env python3
"""Offline visual handoff: immutable requests/results, canonical validation, no generation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from dual_distribution import digest, json_bytes, safe_name, filesystem_root
from runtime_doctor import check as check_runtime
from validate_project import load_project_manifest, validate_project, validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
BASE = ".lks-sdd/handoffs/visual"
ID = re.compile(r"VH-[a-f0-9]{24}")
VERSION = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
OPERATIONAL = {"ART-STATUS", "ART-OPEN"}


def safe(root, relative):
    root = filesystem_root(root)
    safe_name(relative)
    path = root / relative
    for candidate in [path, *path.parents]:
        if candidate == root:
            break
        if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
            raise ValueError(f"Linked path is not allowed: {relative}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path outside project: {relative}")
    return path


def project(root):
    root = filesystem_root(root)
    runtime = check_runtime(root)
    if runtime["status"] == "blocked":
        raise ValueError("Project runtime integrity failed: " + "; ".join(runtime["errors"]))
    if runtime.get("version") and runtime["version"] != VERSION:
        raise ValueError("Use the exact project-pinned runtime, not a different plugin version")
    manifest, errors = load_project_manifest(root)
    if errors or not manifest:
        raise ValueError("Invalid project index: " + "; ".join(errors))
    return manifest


def index(manifest):
    return {item["id"]: item["path"] for item in manifest["artifacts"] if item["id"] not in OPERATIONAL}


def normalize_source(data, artifact, known_decisions):
    """Ignore only documented visual output cells; substantive source text stays hashed."""
    if not artifact.startswith("ART-"):
        return data
    text = data.decode("utf-8")
    lines, header = [], []
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells[0] in {"ID", "Increment", "Screen"}:
                header = cells
            elif artifact == "ART-UX" and re.fullmatch(r"VIS-\d{3}", cells[0]):
                continue
            elif re.fullmatch(r"ADR-\d{3}", cells[0]) and cells[0] not in known_decisions:
                continue
            elif len(cells) == len(header):
                ignored = set()
                if artifact == "ART-UX" and "Aspect" in header:
                    ignored = {"State", "Human validation", "Decision"}
                if artifact == "ART-INCREMENTS" and "Visual prototype" in header:
                    ignored = {"Visual mode", "Visual prototype"}
                if ignored:
                    cells = ["<visual-output>" if column in ignored else cell for column, cell in zip(header, cells)]
                    line = "| " + " | ".join(cells) + " |"
        elif line.strip():
            header = []
        lines.append(line)
    return ("\n".join(lines) + "\n").encode("utf-8")


def source_hashes(root, sources, known_decisions):
    return {relative: digest(normalize_source(safe(root, relative).read_bytes(), artifact, known_decisions))
            for relative, artifact in sorted(sources.items())}


def request_markdown(request):
    return (
        f"# Relevo visual {request['id']}\n\n"
        f"Proyecto: `{request['project_id']}`. Incremento: `{request['increment']}`.\n"
        f"Runtime: `{request['plugin_version']}`. Responsable: `{request['owner_role']}`.\n\n"
        f"## Brief y alcance\n\nLeer `{request['brief']}` y las fuentes enumeradas en request.json.\n"
        f"Objetivo: {request['scope']}\n\nExcluido: {request['excluded_scope']}\n\n"
        "## Mensaje para continuar en Codex\n\n"
        f"Continúa únicamente el prototipado de `{BASE}/{request['id']}/request.md`. "
        "Valida el relevo con visual-handoff inspect antes de generar. Lee el brief y sus "
        "fuentes, genera/revisa con ImageGen integrado, conserva las alternativas y pide "
        "aprobación humana explícita. Guarda imágenes PNG/JPEG y registros VIS/ADR en "
        "los documentos canónicos. No implementes código ni crees AUTH/EXEC ficticios. "
        "Registra el resultado con visual-handoff complete mediante preview/hash/apply. "
        "Después puedo continuar aquí o volver a Copilot.\n"
    ).encode("utf-8")


def validate_request(request):
    schema = json.loads((ROOT / "schemas/visual-handoff.schema.json").read_text(encoding="utf-8"))
    errors = validate_json_schema(request, schema)
    if errors:
        raise ValueError("Invalid handoff request: " + "; ".join(errors))
    material = {key: value for key, value in request.items() if key != "id"}
    if request["id"] != "VH-" + digest(json_bytes(material))[:24]:
        raise ValueError("Request identity/content mismatch")


def request_dir(root, handoff_id):
    if not ID.fullmatch(handoff_id):
        raise ValueError("Invalid handoff ID; select an explicit VH ID")
    return safe(root, f"{BASE}/{handoff_id}")


def load_request(root, handoff_id):
    directory = request_dir(root, handoff_id)
    request = json.loads(safe(root, f"{BASE}/{handoff_id}/request.json").read_text(encoding="utf-8"))
    validate_request(request)
    if request["id"] != handoff_id or safe(root, f"{BASE}/{handoff_id}/request.md").read_bytes() != request_markdown(request):
        raise ValueError("Handoff request was modified or moved under another ID")
    return request


def current_inputs(root, request):
    manifest = project(root)
    for field, expected in (("project_id", request["project_id"]), ("schema_version", "1.5"), ("method_version", "1.5.0")):
        if manifest.get(field) != expected:
            raise ValueError(f"Project identity/contract mismatch: {field}")
    if request["plugin_version"] != VERSION:
        raise ValueError("Handoff version mismatch; reconcile explicitly before upgrading")
    if index(manifest) != request["artifact_index"]:
        raise ValueError("Canonical artifact index changed; reconciliation required")
    actual = source_hashes(root, request["sources"], request["known_decisions"])
    changed = [name for name in actual if actual[name] != request["input_hashes"][name]]
    if changed:
        raise ValueError("Source drift; reconciliation required: " + ", ".join(changed))
    return manifest


def prepare(root, args):
    if args.host == "codex":
        return {"status": "native-codex", "writes": [], "invitation": None}
    manifest = project(root)
    artifact_index = index(manifest)
    if "ART-UX" not in artifact_index:
        raise ValueError("Document ART-UX and the sufficient visual brief before preparing a handoff")
    brief = safe(root, args.brief)
    if not args.brief.startswith("docs/lks-sdd/") or brief.suffix != ".md" or not brief.read_text(encoding="utf-8").strip():
        raise ValueError("Brief must be a nonempty project Markdown under docs/lks-sdd")
    if args.brief in artifact_index.values():
        raise ValueError("Use a separate durable brief file; canonical output tables are not immutable briefs")
    _, _, definitions = validate_project(root)
    if args.increment not in definitions:
        raise ValueError("Increment is not present in the canonical contract")
    if args.task and args.task not in definitions:
        raise ValueError("Referenced TASK does not exist")
    if args.execution:
        execution = next((item for item in manifest.get("executions", []) if item.get("execution_id") == args.execution), None)
        if not execution or execution.get("increment") != args.increment:
            raise ValueError("Referenced execution does not exist in this increment")
        if execution.get("status") not in {"paused", "blocked"}:
            raise ValueError("Pause/checkpoint the existing execution before a visual handoff")
        if args.task and args.task not in execution.get("task_ids", []):
            raise ValueError("TASK is outside the referenced execution")
    elif any(item.get("increment") == args.increment and item.get("status") in {"in-progress", "paused", "blocked", "in-review"}
             for item in manifest.get("executions", [])):
        raise ValueError("Select and pause the existing execution explicitly before the handoff")
    if args.task and args.increment not in re.findall(r"INC-\d{3}", str(definitions[args.task])):
        raise ValueError("TASK does not belong to the requested increment")
    sources = {path: artifact for artifact, path in artifact_index.items()}
    sources[args.brief] = "brief"
    for relative in args.input:
        sources[safe_name(relative)] = "reference"
    # Existing image references must not be edited in place during a handoff.
    for definition in definitions.values():
        if definition.get("_asset_path"):
            sources[definition["_asset_path"]] = "reference"
    decisions = sorted(name for name in definitions if name.startswith("ADR-"))
    request = {
        "schema_version": "1.0", "plugin_version": VERSION, "project_id": manifest["project_id"],
        "increment": args.increment, "task": args.task, "execution": args.execution,
        "brief": args.brief, "scope": args.scope, "excluded_scope": args.exclude,
        "owner_role": args.owner_role, "revision": args.revision,
        "artifact_index": artifact_index, "sources": sources, "known_decisions": decisions,
        "input_hashes": source_hashes(root, sources, decisions),
    }
    request["id"] = "VH-" + digest(json_bytes(request))[:24]
    validate_request(request)
    directory = request_dir(root, request["id"])
    existing = directory.exists()
    if existing and load_request(root, request["id"]) != request:
        raise ValueError("Handoff collision")
    if existing and (directory / "cancelled.json").exists():
        raise ValueError("Cancelled request is immutable; use a new explicit revision")
    pending = {} if existing else {
        f"{BASE}/{request['id']}/request.json": json_bytes(request),
        f"{BASE}/{request['id']}/request.md": request_markdown(request),
    }
    result = mutation(root, "prepare", pending, args)
    return {**result, "id": request["id"], "request": f"{BASE}/{request['id']}/request.md",
            "invitation": None if existing or not args.apply else
            "El brief está listo. Abre este proyecto en Codex para generar y revisar los prototipos. "
            "La ficha conserva el contexto. Después puedes seguir en Codex o volver aquí."}


def result_selection(root, request, visual_ids):
    report, _, definitions = validate_project(root)
    # Do not accept approval based only on the auxiliary handoff record.
    if not report.valid:
        raise ValueError("Canonical validation failed: " + "; ".join(report.errors))
    selected = {}
    for visual_id in sorted(set(visual_ids)):
        if not re.fullmatch(r"VIS-\d{3}", visual_id):
            raise ValueError("Result requires explicit VIS IDs")
        row = definitions.get(visual_id, {})
        if row.get("State") != "confirmed" or request["increment"] not in re.findall(r"INC-\d{3}", row.get("Increment", "")):
            raise ValueError(f"{visual_id}: explicit confirmed visual approval for this increment is missing")
        if not row.get("_asset_sha256") or not row.get("_asset_path"):
            raise ValueError(f"{visual_id}: missing checked image asset")
        if request["brief"] not in row.get("Prompt or brief", ""):
            raise ValueError(f"{visual_id}: Prompt or brief must reference the handoff brief path")
        decision_ids = re.findall(r"ADR-\d{3}", row.get("Decision", ""))
        selected[visual_id] = {"visual": row, "decisions": {name: definitions[name] for name in decision_ids}}
    if not selected:
        raise ValueError("At least one approved VIS is required")
    return selected


def inspect(root, handoff_id):
    root = filesystem_root(root)
    request = load_request(root, handoff_id)
    current_inputs(root, request)
    directory = request_dir(root, handoff_id)
    if (directory / "cancelled.json").exists():
        return {"id": handoff_id, "status": "cancelled", "writes": []}
    result_path = safe(root, f"{BASE}/{handoff_id}/result.json")
    if not result_path.exists():
        return {"id": handoff_id, "status": "pending-visual-approval", "request": f"{BASE}/{handoff_id}/request.md", "writes": []}
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "1.0" or result.get("request_sha256") != digest(json_bytes(request)):
        raise ValueError("Result belongs to another request or version")
    selected = result_selection(root, request, result["visual_ids"])
    if digest(json_bytes(selected)) != result["selection_sha256"]:
        raise ValueError("Visual result/approval changed; reconciliation required")
    return {"id": handoff_id, "status": "completed", "visual_ids": result["visual_ids"],
            "next": "Recompute normal readiness for the selected scope; no implementation authorization is implied.", "writes": []}


def mutation(root, operation, files, args):
    intent = {"operation": operation, "files": {name: digest(data) for name, data in sorted(files.items())}}
    preview_hash = digest(json_bytes(intent))
    if args.apply:
        if args.authorize != preview_hash:
            raise ValueError("Preview hash does not match; review a fresh preview")
        if files:
            base = safe(root, BASE)
            base.mkdir(parents=True, exist_ok=True)
            lock = base / ".writer-lock"
            lock.mkdir()  # no implicit lock stealing, including after a crash
            try:
                # Recheck mutable sources after acquiring the local writer lock.
                # A preview is not permission to publish a result for changed inputs.
                if operation == "prepare":
                    request_data = next(data for name, data in files.items() if name.endswith("/request.json"))
                    current_inputs(root, json.loads(request_data))
                else:
                    current_request = load_request(root, args.id)
                    current_inputs(root, current_request)
                    if operation == "complete":
                        selection = result_selection(root, current_request, args.visual)
                        expected = json.loads(next(iter(files.values())))["selection_sha256"]
                        if digest(json_bytes(selection)) != expected:
                            raise ValueError("Visual approval changed during apply")
                if operation == "prepare":
                    directory = safe(root, next(iter(files))).parent
                    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=base) as staging:
                        for relative, data in files.items():
                            (Path(staging) / Path(relative).name).write_bytes(data)
                        # Directory rename publishes request+Markdown together.
                        if directory.exists():
                            raise ValueError("Concurrent request creation; read existing state")
                        os.rename(staging, directory)
                else:
                    for relative, data in files.items():
                        path = safe(root, relative)
                        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                            temporary = Path(handle.name)
                            handle.write(data)
                            handle.flush()
                            os.fsync(handle.fileno())
                        try:
                            # Exclusive hard-link publication prevents overwrite and partial JSON.
                            os.link(temporary, path)
                        finally:
                            temporary.unlink(missing_ok=True)
            finally:
                lock.rmdir()
    return {"status": "applied" if args.apply else "preview", "preview_hash": preview_hash,
            "writes": sorted(files)}


def run(root, args):
    root = filesystem_root(root)
    if args.action == "prepare":
        return prepare(root, args)
    if args.action == "status":
        base = safe(root, BASE)
        requests = []
        for path in sorted(base.glob("VH-*")) if base.exists() else []:
            try:
                requests.append(inspect(root, path.name))
            except (ValueError, OSError, KeyError, TypeError) as exc:
                requests.append({"id": path.name, "status": "reconciliation-required", "error": str(exc)})
        return {"status": "ok", "handoffs": requests, "writes": []}
    if args.action == "inspect":
        return inspect(root, args.id)
    request = load_request(root, args.id)
    current_inputs(root, request)
    directory = request_dir(root, args.id)
    if args.action == "cancel":
        if (directory / "result.json").exists():
            raise ValueError("Completed results remain historical; use a new revision")
        content = json_bytes({"schema_version": "1.0", "reason": args.reason,
                              "request_sha256": digest(json_bytes(request))})
        name = "cancelled.json"
    else:
        if (directory / "cancelled.json").exists():
            raise ValueError("Cannot complete a cancelled request")
        selected = result_selection(root, request, args.visual)
        content = json_bytes({"schema_version": "1.0", "request_sha256": digest(json_bytes(request)),
                              "visual_ids": sorted(set(args.visual)), "selection_sha256": digest(json_bytes(selected))})
        name = "result.json"
    destination = directory / name
    if destination.exists() and destination.read_bytes() != content:
        raise ValueError("Immutable result already exists; reconcile through a new revision")
    files = {} if destination.exists() else {f"{BASE}/{args.id}/{name}": content}
    return {**mutation(root, args.action, files, args), "id": args.id}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("prepare", "inspect", "status", "complete", "cancel"):
        command = sub.add_parser(name)
        command.add_argument("project_root", type=Path)
        command.add_argument("--json", action="store_true")
        if name not in {"status", "prepare"}:
            command.add_argument("--id", required=True)
        if name in {"prepare", "complete", "cancel"}:
            command.add_argument("--apply", action="store_true")
            command.add_argument("--authorize")
        if name == "prepare":
            command.add_argument("--host", choices=["codex", "copilot"], required=True)
            command.add_argument("--brief", required=True)
            command.add_argument("--increment", required=True)
            command.add_argument("--scope", required=True)
            command.add_argument("--exclude", default="Application implementation, external writes and deployment")
            command.add_argument("--owner-role", required=True)
            command.add_argument("--revision", default="1")
            command.add_argument("--input", action="append", default=[])
            command.add_argument("--task")
            command.add_argument("--execution")
        if name == "complete":
            command.add_argument("--visual", action="append", required=True)
        if name == "cancel":
            command.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        result = run(args.project_root, args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "reconciliation-required", "error": str(exc), "writes": []}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
