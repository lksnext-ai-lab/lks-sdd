"""Explicit 1.5 -> 2.0 conversion with preserved originals and recoverable apply.

Mechanical conversion does not infer feature boundaries, intent or new authority.
All unidentified semantics remain visible reconciliation work.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import posixpath
import re
import uuid

from v2_contract import (ContractError, DOCS, HISTORY, VERSION, METHOD, DOMAINS, ID, LINK,
                         ASSET, canonical, fingerprint, load, make_element, path_at, read_bytes,
                         render_document, resolve_link, sha)
from v2_storage import apply, ensure_idle, preview, recover, stage_contract

PREFIX_KIND = {"FR": "requirement", "NFR": "requirement", "TR": "requirement", "BR": "rule",
               "AC": "acceptance", "TEST": "test", "ADR": "decision", "TASK": "task",
               "INC": "increment", "PLAN": "plan", "REL": "release", "INT": "interface",
               "BIND": "binding", "ENV": "environment", "AUTH": "authorization", "EXEC": "execution",
               "CKPT": "checkpoint", "PROB": "problem", "CHG": "change", "PCH": "change"}
RELATION_COLUMNS = {"requirements": "requirements", "requirement": "requirements", "acceptance": "acceptance",
                    "tests": "tests", "dependencies": "depends_on", "increment": "increment", "release": "release",
                    "plan": "plan", "profile binding": "bindings", "profile bindings": "bindings",
                    "interfaces": "interfaces", "decisions": "decision", "decision": "decision"}


def inventory(root: Path) -> dict[str, str]:
    result = {".lks-sdd/project.json": sha(read_bytes(root, ".lks-sdd/project.json"))}
    manifest = json.loads(read_bytes(root, ".lks-sdd/project.json"))
    for binding in manifest.get("technology", {}).get("profile_bindings", []):
        for relative in (binding.get("lock_path"), ".lks-sdd/profiles/" + binding["binding_id"] + ".profile.json"):
            if relative and path_at(root, relative, missing=True).is_file():
                result[relative] = sha(read_bytes(root, relative))
    for directory, folders, files in os.walk(path_at(root, DOCS), followlinks=False):
        folders[:] = sorted(folders)
        for name in folders + files:
            path_at(root, (Path(directory) / name).relative_to(root).as_posix())
        for name in sorted(files):
            relative = (Path(directory) / name).relative_to(root).as_posix()
            if relative.startswith(HISTORY + "/") or relative.startswith(DOCS + "/00-control/migrations/"):
                continue
            result[relative] = sha(read_bytes(root, relative, limit=64 * 1024 * 1024))
            if len(result) > 10000:
                raise ContractError("Migration inventory exceeds bound")
    # Preserve explicitly linked attachments outside the document subtree too.
    pending = [p for p in result if p.endswith(".md")]
    visited = set()
    total = 0
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        raw = read_bytes(root, source)
        total += len(raw)
        if total > 64 * 1024 * 1024:
            raise ContractError("Migration linked-source budget exceeded")
        text = raw.decode("utf-8")
        targets = [a or p for _, a, p in LINK.findall(text)] + [a or p for a, p in ASSET.findall(text)]
        for target in targets:
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                continue
            relative, _ = resolve_link(source, target)
            destination_path = path_at(root, relative)
            if destination_path.is_dir() or relative in result:
                continue
            data = read_bytes(root, relative, limit=64 * 1024 * 1024)
            result[relative] = sha(data)
            if len(result) > 10000:
                raise ContractError("Migration linked inventory exceeds bound")
            if relative.endswith(".md"):
                pending.append(relative)
    return result


def destination(relative: str) -> str:
    suffix = relative[len(DOCS) + 1:]
    if suffix.startswith("01-definition/"):
        suffix = "02-specification/shared/legacy/" + suffix[len("01-definition/"):]
    elif suffix.startswith("02-requirements/"):
        suffix = "02-specification/shared/" + suffix[len("02-requirements/"):]
    elif suffix.startswith("02-design/"):
        suffix = "03-solution/" + suffix[len("02-design/"):]
    elif suffix.startswith("03-implementation/"):
        suffix = "04-delivery/legacy/" + suffix[len("03-implementation/"):]
    return DOCS + "/" + suffix


def diagnose(root: Path) -> dict:
    from runtime_doctor import check
    ensure_idle(root)
    manifest = json.loads(read_bytes(root, ".lks-sdd/project.json"))
    version = manifest.get("schema_version")
    if version == VERSION:
        return {"status": "already-v2", "writes": [], "source_schema": version}
    if version != "1.5" or manifest.get("method_version") != "1.5.0":
        return {"status": "blocked", "reason": "Only contract 1.5/method 1.5.0 is an implemented migration origin", "writes": []}
    runtime = check(root)
    if runtime["status"] == "blocked":
        return {"status": "blocked", "reason": "Pinned source runtime integrity failure", "runtime": runtime, "writes": []}
    from contract_engine import build_project_model
    model = build_project_model(root)
    problems = [d.message for d in model.diagnostics if d.severity == "error"]
    sources = inventory(root)
    handoffs = root / ".lks-sdd/handoffs/visual"
    for pattern in ("VH-*/request.json", "v2/VH-*/request.json"):
        for request in handoffs.glob(pattern):
            if not (request.parent / "result.json").exists() and not (request.parent / "cancelled.json").exists():
                problems.append("Close or reconcile the pending visual handoff before migration: " + request.parent.name)
    return {"status": "blocked" if problems else "preview-available", "source_schema": "1.5", "target_schema": VERSION,
            "source_snapshot": fingerprint(sources), "sources": sources, "runtime": runtime,
            "errors": problems, "open_executions": [e for e in manifest.get("executions", []) if e.get("status") not in {"completed", "cancelled"}],
            "semantic_reconciliation": "Feature boundaries, paths, applicability and authority require explicit review", "writes": []}


def _rewrite_links(text: str, source: str, target: str, paths: dict, identities: dict) -> str:
    def replace(match):
        label, destination_value = match[1], match[2] or match[3]
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", destination_value):
            return match[0]
        try:
            original, anchor = resolve_link(source, destination_value)
        except ContractError:
            return match[0]  # Validator reports unsafe links; never fetch them.
        mapped = paths.get(original, original)
        mentioned = ID.findall(label)
        if len(mentioned) == 1 and mentioned[0] in identities:
            mapped, anchor = identities[mentioned[0]], mentioned[0].lower()
        relative = posixpath.relpath(mapped, posixpath.dirname(target))
        return "[" + label + "](<" + relative + ("#" + anchor if anchor else "") + ">)"
    return LINK.sub(replace, text)


def plan(root: Path, *, target_runtime: Path | None = None) -> tuple[dict, dict]:
    ensure_idle(root)
    diagnostic = diagnose(root)
    if diagnostic["status"] != "preview-available":
        raise ContractError(diagnostic.get("reason", diagnostic["status"]) + ": " + "; ".join(diagnostic.get("errors", [])))
    from contract_engine import build_project_model, _parse_frontmatter, _parse_markdown_tables
    old = build_project_model(root)
    source_snapshot = diagnostic["source_snapshot"]
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, str(old.manifest["project_id"]))
    originals = HISTORY + "/migration-" + source_snapshot[:16]
    changes, mapping, active_paths, pending = {}, {}, {}, []
    sources = dict(diagnostic["sources"])
    for relative in sources:
        raw = read_bytes(root, relative, limit=64 * 1024 * 1024)
        archive = originals + "/tree/" + relative
        changes[archive] = raw
        if relative.startswith(DOCS + "/") and relative.endswith(".md") and not relative.startswith(DOCS + "/evidence/"):
            active_paths[relative] = destination(relative)
        mapping[relative] = {"archive": archive, "destination": active_paths.get(relative, relative), "sha256": sources[relative]}
    if len(set(active_paths.values())) != len(active_paths):
        raise ContractError("Migration destination collision between source documents")
    for origin, target in active_paths.items():
        if target != origin and target in sources:
            raise ContractError("Migration would overwrite an existing customization: " + target)
    # Task identity belongs in its detail, never in both board and detail.
    identities = {}
    for identifier, row in old.nodes.items():
        relative = active_paths.get(row.path)
        if relative:
            if identifier.startswith("TASK-"):
                relative = DOCS + "/04-delivery/tasks/" + identifier + ".md"
            identities[identifier] = relative
    # 1.5 indexes executions and bindings outside the table-node graph. Preserve
    # those declared records explicitly, without granting their old authority.
    indexed = {}
    for kind, field, records, directory in (
        ("binding", "binding_id", old.manifest.get("technology", {}).get("profile_bindings", []), "03-solution/bindings"),
        ("execution", "execution_id", old.manifest.get("executions", []), "04-delivery/executions"),
        ("authorization", "authorization_id", old.manifest.get("authorizations", []), "00-control/authorizations"),
    ):
        for value in records:
            identifier = value.get(field)
            if not identifier or not ID.fullmatch(identifier):
                raise ContractError("Invalid legacy index identity: " + str(identifier))
            if identifier in indexed:
                raise ContractError("Duplicate legacy index identity: " + identifier)
            indexed[identifier] = (kind, value)
            identities.setdefault(identifier, DOCS + "/" + directory + "/" + identifier + ".md")
    checkpoints = {}
    for relative, target in active_paths.items():
        text = read_bytes(root, relative).decode("utf-8").replace("\r\n", "\n")
        front, body, offset = _parse_frontmatter(text) if text.startswith("---\n") else ({}, text, 1)
        if front.get("artifact_type") != "implementation-checkpoint":
            continue
        for table in _parse_markdown_tables(body, offset):
            for row_line, cells in table.rows:
                identifier = cells.get("Checkpoint", "")
                if not re.fullmatch(r"CKPT-\d{3,}", identifier):
                    continue
                if identifier in identities or identifier in checkpoints:
                    raise ContractError("Duplicate legacy checkpoint identity: " + identifier)
                identities[identifier] = target
                checkpoints[identifier] = (relative, row_line, cells)
    by_path = {}
    for identifier, row in old.nodes.items():
        if identifier not in identities:
            continue
        prefix = identifier.split("-")[0]
        kind = PREFIX_KIND.get(prefix, "legacy")
        state = row.state or "unknown"
        from v2_contract import STATES
        if state not in STATES:
            state = "unknown"
        if kind == "authorization":
            state = "revoked"
        if kind == "execution":
            state = "reconciliation-required"
        relations = {}
        for column, parsed in row.reference_results.items():
            relation = RELATION_COLUMNS.get(column.lower(), "sources")
            targets = [t for t in parsed.references if t in identities and t != identifier]
            if targets:
                relations.setdefault(relation, []).extend(targets)
        relations = {k: sorted(set(v)) for k, v in relations.items()}
        body = "\n\n".join("**" + key + ":** " + value for key, value in row.cells.items())
        item = make_element(identifier, kind, row.cells.get("Title", row.cells.get("Name", identifier)), body,
                            uid=str(uuid.uuid5(namespace, identifier)), state=state,
                            nature="unknown" if state == "unknown" else "fact", relations=relations,
                            legacy_columns=row.cells, migration={"origin": row.path, "line": row.line,
                            "snapshot": source_snapshot, "semantics": "preserved-not-reauthorized"})
        if kind in {"task", "binding", "interface", "plan", "environment"}:
            item["meta"]["reconciliation_required"] = True
            pending.append(identifier + ": completar equivalencia semántica v2 antes de ejecutar")
        by_path.setdefault(identities[identifier], []).append(item)
    for identifier, (kind, value) in indexed.items():
        existing = next((item for items in by_path.values() for item in items if item["meta"]["id"] == identifier), None)
        if existing is not None:
            existing["meta"]["legacy_index_record"] = value
            continue
        relations = {}
        for field, relation in (("task_ids", "affects"), ("increment", "increment"), ("release", "release"),
                                ("profile_bindings", "bindings"), ("authorization_id", "sources"),
                                ("selection_decision", "decision"), ("unit_id", "sources")):
            targets = value.get(field, [])
            if isinstance(targets, str):
                targets = [targets]
            for ref in targets:
                if ref not in identities:
                    raise ContractError("Unresolved legacy index reference: " + identifier + " -> " + str(ref))
            if targets:
                relations.setdefault(relation, []).extend(targets)
        latest = value.get("latest_checkpoint")
        if latest:
            refs = [key for key, (origin, _, _) in checkpoints.items() if origin == latest]
            if len(refs) != 1:
                raise ContractError("Legacy execution checkpoint needs explicit reconciliation: " + str(latest))
            relations.setdefault("sources", []).extend(refs)
        item = make_element(identifier, kind, "Registro histórico " + identifier,
            "Registro declarado por el índice 1.5; no constituye autoridad ni verificación v2.\n\n" +
            "\n\n".join("**" + key + ":** " + json.dumps(raw, ensure_ascii=False) for key, raw in value.items()),
            uid=str(uuid.uuid5(namespace, identifier)), nature="fact",
            state="revoked" if kind == "authorization" else "reconciliation-required",
            relations={k: sorted(set(v)) for k, v in relations.items()}, legacy_index_record=value,
            reconciliation_required=True, migration={"origin": ".lks-sdd/project.json", "snapshot": source_snapshot,
                                                     "semantics": "preserved-not-reauthorized"})
        by_path.setdefault(identities[identifier], []).append(item)
        pending.append(identifier + ": reconciliar registro operativo anterior; no concede autoridad v2")
    for identifier, (relative, row_line, cells) in checkpoints.items():
        relations = {"execution": [cells["Execution"]]} if cells.get("Execution") in identities else {}
        item = make_element(identifier, "checkpoint", "Checkpoint histórico " + identifier,
            "\n\n".join("**" + key + ":** " + value for key, value in cells.items()),
            uid=str(uuid.uuid5(namespace, identifier)), nature="fact", state="reconciliation-required",
            relations=relations, legacy_columns=cells,
            migration={"origin": relative, "line": row_line, "snapshot": source_snapshot})
        by_path.setdefault(identities[identifier], []).append(item)
    # Preserve every table cell and custom prose, including keyless/historical rows.
    for relative, target in active_paths.items():
        text = read_bytes(root, relative).decode("utf-8").replace("\r\n", "\n")
        if relative.endswith("technology-variants.md"):
            changes[target] = text.encode()
            continue
        if "/technology-approvals/" in relative:
            # Historical approvals remain byte-identical archives, not current authority.
            changes[relative] = None
            mapping[relative]["destination"] = mapping[relative]["archive"]
            continue
        front, body, line = _parse_frontmatter(text) if text.startswith("---\n") else ({}, text, 1)
        if front:
            identifier = "LEG-" + str(int(sha((relative + ":frontmatter").encode())[:12], 16))
            by_path.setdefault(target, []).append(make_element(identifier, "legacy", "Metadatos originales",
                "Metadatos de procedencia 1.5 conservados; no trasladan aprobación al contrato v2.",
                uid=str(uuid.uuid5(namespace, identifier)), state="unknown", nature="fact", legacy_frontmatter=front))
        lines = body.splitlines()
        remove = set()
        for table in _parse_markdown_tables(body, line):
            if not table.rows:
                continue
            first_line = table.rows[0][0] - line
            remove.update(range(max(0, first_line - 2), table.rows[-1][0] - line + 1))
            for row_line, cells in table.rows:
                if any(origin == relative and number == row_line for origin, number, _ in checkpoints.values()):
                    continue
                existing = next((r for r in old.rows.values() if r.path == relative and r.line == row_line), None)
                if existing and existing.key in identities and old.nodes.get(existing.key) is existing:
                    continue
                identifier = "LEG-" + str(int(sha((relative + ":" + str(row_line)).encode())[:12], 16))
                item = make_element(identifier, "legacy", "Contenido conservado de " + Path(relative).stem,
                                    "\n\n".join("**" + k + ":** " + v for k, v in cells.items()),
                                    uid=str(uuid.uuid5(namespace, identifier)), state="unknown", nature="fact",
                                    migration={"origin": relative, "line": row_line, "snapshot": source_snapshot})
                by_path.setdefault(target, []).append(item)
        narrative = "\n".join(value for i, value in enumerate(lines) if i not in remove)
        if narrative.strip():
            pending.append(relative + ": prosa personalizada conservada; revisar aplicabilidad")
        elements = by_path.get(target, [])
        changes[target] = render_document("migrated", Path(relative).stem, elements,
                                          preamble=narrative + "\n\nMigración mecánica: no concede aprobación ni verificación nuevas.")
        if target != relative:
            changes[relative] = None
    for target, elements in by_path.items():
        if target not in changes or changes[target] is None:
            changes[target] = render_document("migrated", Path(target).stem, elements,
                                              preamble="Contenido migrado. Reconciliación semántica pendiente.")
    for target in list(changes):
        if target.startswith(originals + "/") or not target.endswith(".md") or changes[target] is None:
            continue
        original = next((p for p, q in active_paths.items() if q == target), target)
        # Only human Markdown is relocated; historical raw JSON cells remain exact.
        changes[target] = "\n".join(line if line.startswith("<!-- lks-sdd:") else
            _rewrite_links(line, original, target, active_paths, identities)
            for line in changes[target].decode().split("\n")).encode()
    apps = [make_element(f"APP-{i:03}", "applicability", domain, "Reconciliar con la documentación migrada; no se presume no aplicable.",
                         uid=str(uuid.uuid5(namespace, f"APP-{i:03}")), state="unknown", nature="unknown",
                         scope="global", domain=domain, applicability="unknown", critical=True)
            for i, domain in enumerate(DOMAINS, 1)]
    app_path = DOCS + "/02-specification/shared/applicability.md"
    if app_path in changes or path_at(root, app_path, missing=True).exists():
        raise ContractError("Migration destination collision: " + app_path)
    changes[app_path] = render_document("applicability", "Reconciliación de aplicabilidad", apps)
    manifest = {"schema_version": VERSION, "method_version": METHOD, "project_id": old.manifest["project_id"],
                "plugin_version": json.loads((Path(__file__).resolve().parents[1] / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"], "name": old.manifest.get("name", "Proyecto migrado"),
                "migration": {"origin_schema": "1.5", "source_snapshot": source_snapshot, "state": "reconciliation-required"},
                "artifacts": [{"path": p} for p in sorted(set(active_paths.values()) | set(by_path) | {app_path})
                              if changes.get(p) is not None]}
    runtime_info = _runtime_transition(root, target_runtime, diagnostic["runtime"], changes, sources)
    changes[".lks-sdd/project.json"] = canonical(manifest) + b"\n"
    receipt = {"source_snapshot": source_snapshot, "origin": "1.5", "target": VERSION,
               "mapping": mapping, "elements": {identifier: {"path": p, "anchor": identifier.lower()} for identifier, p in identities.items()},
               "pending": sorted(set(pending)), "runtime": runtime_info,
               "open_executions": diagnostic["open_executions"], "authorization": "reconciliation-required",
               "verification": "not-run", "feature_classification": "not-inferred"}
    receipt_path = DOCS + "/00-control/migrations/" + source_snapshot[:16] + ".json"
    from v2_schema import validate
    validate("migration-receipt", receipt)
    changes[receipt_path] = canonical(receipt) + b"\n"
    sources.update(stage_contract(root, changes, diagnostic["sources"]))
    result = preview(root, changes, sources=sources, operation="migrate-1.5-to-2.0")
    result.update(mapping=mapping, semantic_pending=receipt["pending"], runtime=runtime_info,
                  receipt=receipt_path, evidence_policy="original-bytes-unchanged", feature_classification="not-inferred")
    return result, changes


def _runtime_transition(root, target_runtime, old_runtime, changes, sources):
    if old_runtime["status"] == "unmanaged":
        if target_runtime is not None:
            raise ContractError("Unmanaged project: installing a runtime is a separate explicit operation")
        return {"status": "unmanaged", "installation": "not-performed"}
    if target_runtime is None:
        raise ContractError("Pinned source requires an explicit validated target runtime")
    from dual_distribution import project_files
    from query_sources import lexical_root
    target_runtime = lexical_root(target_runtime)
    integrity = json.loads(read_bytes(target_runtime, "package-integrity.json", limit=16 * 1024 * 1024))
    records = integrity.get("files")
    if not isinstance(records, list) or not records:
        raise ContractError("Target runtime requires its package integrity inventory")
    core = {}
    for entry in records:
        name, expected = entry["path"], entry["sha256"]
        raw = read_bytes(target_runtime, name, limit=64 * 1024 * 1024, package_data=True)
        if sha(raw) != expected:
            raise ContractError("Target runtime integrity failure: " + name)
        core[name] = raw
    core["package-integrity.json"] = read_bytes(target_runtime, "package-integrity.json", limit=16 * 1024 * 1024)
    if not json.loads(core[".codex-plugin/plugin.json"])["version"].startswith("2."):
        raise ContractError("Migration target must be an explicit v2 runtime")
    old_lock = json.loads(read_bytes(root, ".lks-sdd/distribution-lock.json"))
    sources[".lks-sdd/distribution-lock.json"] = sha(read_bytes(root, ".lks-sdd/distribution-lock.json"))
    generated = project_files(core, "migration:" + fingerprint({k: sha(v) for k, v in core.items()}),
                              "migration-not-release-acceptance", plugin_entrypoints=old_lock.get("entrypoints") == "plugin")
    from dual_distribution import BEGIN, END
    for name, data in generated.items():
        path = path_at(root, name, missing=True, package_data=True)
        if name in {"AGENTS.md", ".github/copilot-instructions.md"} and path.exists():
            original = path.read_text(encoding="utf-8")
            if original.count(BEGIN) != 1 or original.count(END) != 1:
                raise ContractError("Cannot replace ambiguous managed instructions")
            new_block = data.decode().strip()
            data = (original.split(BEGIN)[0] + new_block + original.split(END)[1]).encode()
        elif path.exists() and name not in old_lock.get("managed_files", {}) and name != ".lks-sdd/distribution-lock.json" and path.read_bytes() != data:
            raise ContractError("Target runtime/adaptor collision: " + name)
        changes[name] = data
    installation = ".lks-sdd/installation.json"
    if path_at(root, installation, missing=True).exists():
        original_receipt = read_bytes(root, installation, limit=16 * 1024 * 1024)
        sources[installation] = sha(original_receipt)
        old_receipt = json.loads(original_receipt)
        if old_receipt.get("host") != "copilot" or old_receipt.get("schema_version") != "1.0":
            raise ContractError("Installation receipt must be reconciled before runtime migration")
        ownership = {}
        for name, data in generated.items():
            previous = old_receipt.get("files", {}).get(name)
            if name in {"AGENTS.md", ".github/copilot-instructions.md"}:
                text = data.decode()
                block = (BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END).replace("\r\n", "\n").encode()
                ownership[name] = {"sha256": sha(block), "kind": "block",
                                   "created_file": bool(previous and previous.get("created_file"))}
            else:
                ownership[name] = {"sha256": sha(data), "kind": "file"}
        for name, record in old_receipt.get("files", {}).items():
            raw = read_bytes(root, name, limit=64 * 1024 * 1024, package_data=True)
            if record.get("kind") == "block":
                text = raw.decode()
                raw = (BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END).replace("\r\n", "\n").encode()
            if sha(raw) != record.get("sha256"):
                raise ContractError("Locally changed managed installation entry: " + name)
            if name not in generated and not name.startswith(old_lock["runtime"] + "/"):
                raise ContractError("Old adapter needs explicit reconciliation: " + name)
        new_lock = json.loads(generated[".lks-sdd/distribution-lock.json"])
        changes[installation] = canonical({"schema_version": "1.0", "host": "copilot", "version": new_lock["version"],
            "channel": new_lock["channel"], "runtime_digest": new_lock["runtime_digest"], "files": ownership,
            "preserved_historical_runtime": old_lock["runtime"], "history_is_not_active_installation": True})
    return {"status": "explicit-pinned-transition", "source": old_lock["runtime"],
            "target": json.loads(generated[".lks-sdd/distribution-lock.json"])["runtime"]}


def migrate(root: Path, authorized_hash: str, *, target_runtime: Path | None = None,
            interrupt_after: int | None = None) -> dict:
    if diagnose(root)["status"] == "already-v2":
        return {"status": "already-v2", "writes": [], "authorization": "not-granted"}
    result, changes = plan(root, target_runtime=target_runtime)
    outcome = apply(root, changes, result, authorized_hash, validator=lambda: load(root).require_valid(), interrupt_after=interrupt_after)
    return {**outcome, "migration_receipt": result["receipt"], "semantic_pending": result["semantic_pending"],
            "authorization": "reconciliation-required", "verification": "not-run"}
