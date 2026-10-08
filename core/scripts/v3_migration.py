"""Explicit v2 -> v3 cutover. Originals, identities and prior decisions are retained."""
import copy
import json
from pathlib import Path
import re
import tempfile

import v2_contract as v2
from v3_contract import ContractError, DOCS, INDEX, METHOD, element, canonical, fingerprint, load, now, path_at, read_bytes, sha
from v3_policy import profile
from v3_git import observe
from v3_storage import prepare


def source_model(root, *, normalize=False):
    manifest = json.loads(read_bytes(root, INDEX))
    options = {}
    generated = {}
    temporary = None
    if normalize:
        from content_store import prepare_inventory, object_path, read_object
        temporary = tempfile.TemporaryDirectory(prefix="lks-migration-inventories-")
        target = Path(temporary.name)
        original_bytes = 0
        inventory_bytes, seen_inventories = 0, set()
        def transform(path, raw):
            nonlocal original_bytes
            original_bytes += len(raw)
            if original_bytes > 256*1024*1024: raise ContractError("Migration source Markdown budget exceeded (256 MiB)")
            # Validate every original block with the published parser before changing representation.
            v2.parse_document(raw.decode("utf-8").replace("\r\n", "\n"), path)
            def replace(match):
                nonlocal inventory_bytes
                meta = json.loads(match[1])
                if meta["kind"] not in {"execution", "checkpoint"}: return match[0]
                for field in ("baseline_files", "files", "source_hashes"):
                    if field in meta and field + "_ref" in meta: raise ContractError("Ambiguous original inventory")
                    if field in meta:
                        meta[field + "_ref"] = prepare_inventory(root, meta.pop(field), generated)
                    if field + "_ref" in meta:
                        ref = meta[field + "_ref"]; obj = object_path(ref)
                        if obj not in seen_inventories:
                            if inventory_bytes + ref["bytes"] > 32*1024*1024:
                                raise ContractError("Migration unique inventory byte budget exceeded")
                            inventory_bytes += ref["bytes"]; seen_inventories.add(obj)
                        if not (target/obj).exists():
                            from v3_storage import staged_write
                            staged_write(target, obj, generated[obj] if obj in generated else read_object(root, ref))
                return "<!-- lks-sdd: " + canonical(meta).decode() + " -->\n" + match[2] + "<!-- /lks-sdd -->"
            return v2.BLOCK.sub(replace, raw.decode("utf-8")).encode("utf-8")
        options = {"document_transform": transform, "inventory_root": target}
    # Published 2.0.x precedes TECH-001. Its absence is a known source format,
    # not permission to ignore a missing declaration in later projects.
    if manifest.get("plugin_version") in {"2.0.0", "2.0.1", "2.0.2"} and manifest.get("method_version") == "2.0.0":
        schema = json.loads((Path(__file__).resolve().parents[1]/"schemas/project-2.0-pre-technology.schema.json").read_bytes())
        model = v2.read_contract(root, project_schema=schema, require_technology=False, **options)
    else: model = v2.read_contract(root, **options)
    model.require_valid()
    # Newly generated objects are destination payloads, not existing source preconditions.
    for path in generated: model.hashes.pop(path, None)
    model.inventory_changes = generated
    model.inventory_temporary = temporary
    return model


def inventory(root, model):
    result = dict(model.hashes)
    from source_inventory import documents, digest as observed_digest
    for path, entry in documents(root, byte_limit=2*1024*1024*1024).items():
        digest = observed_digest(entry)
        if path in model.hashes and model.hashes[path] != digest: raise ContractError("Source changed while preparing migration: " + path)
        result[path] = digest
        if len(result) > 100000: raise ContractError("Migration source file budget exceeded (100000)")
    for path in (".lks-sdd/distribution-lock.json", "AGENTS.md", ".github/copilot-instructions.md", ".github/lks-sdd-host.md"):
        if (root / path).exists(): result[path] = sha(read_bytes(root, path))
    return result


def diagnose(root, *, source=None):
    root = Path(root).resolve()
    try:
        manifest = json.loads(read_bytes(root, INDEX))
        if manifest.get("schema_version") != "2.0" or manifest.get("method_version") not in {"2.0.0", "2.1.0"}:
            return {"status": "unsupported", "source": manifest.get("schema_version"), "method": manifest.get("method_version"),
                    "cause": "Formato/método sin conversión probada; conserve el origen", "writes": []}
        model = source or source_model(root, normalize=True)
        runtime = {"version": manifest.get("plugin_version"), "assurance": "declared-in-index"}
        if (root / ".lks-sdd/distribution-lock.json").exists():
            from runtime_doctor import check
            runtime = check(root)
            if runtime["status"] != "valid": raise ContractError("Runtime fijado incompleto: " + "; ".join(runtime["errors"]))
        elif not (re.fullmatch(r"2\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", runtime.get("version") or "") or runtime.get("version") in {"3.0.0", "3.1.0"}):
            raise ContractError("Falta identificar el runtime de origen; no deducirlo del formato")
        sources = inventory(root, model)
        tasks = [{"id": t.id, "uid": t.meta["uid"], "state": t.meta["state"],
                  "continuation": "historical-result-preserved" if t.meta["state"] in {"done", "completed", "cancelled", "done-with-reservations"}
                  else "reconcile-open-slice-and-authorize-current-method"} for t in model.by_kind("task")]
        return {"status": "compatible", "format": "2.0", "method": manifest["method_version"], "runtime": runtime,
                "sources": sources, "snapshot": fingerprint(sources), "tasks": tasks, "writes": [],
                "next": "Confirme la configuración v3 y revise el efecto sobre el trabajo abierto en una única vista previa"}
    except (ContractError, OSError, ValueError, KeyError) as exc:
        return {"status": "reconciliation-required", "cause": str(exc), "writes": []}


def preview(root, actor_name, process, controls, statement, *, target, runtime_changes=None, runtime_bundle=None,
            method=METHOD, collaboration=None, members=None, packet_directory=None):
    root = Path(root).resolve()
    from v2_storage import ensure_idle
    ensure_idle(root)
    source = source_model(root, normalize=method == "3.1.0")
    diagnostic = diagnose(root, source=source)
    if diagnostic["status"] != "compatible": raise ContractError(diagnostic.get("cause", "Origen incompatible"))
    if not actor_name.strip() or not statement.strip(): raise ContractError("Confirme el responsable y la configuración de destino")
    git = observe(root)
    if not git["branch"]: raise ContractError("Acuerde la rama/base para el corte de migración")
    person = element("member", actor_name, "Responsabilidad de migración declarada ahora; no atribuye actuaciones históricas.",
                     roles=["owner", "specifier", "developer", "reviewer", "integrator"], active=True,
                     identity_history=[{"name": actor_name, "source": "migration-declaration", "since": now()}])
    policy = element("policy", "Proceso v3 acordado", statement, **profile(process, controls))
    additional, declared = [], []
    from v3_policy import ROLES
    for value in members or []:
        if not value.get("name") or not value.get("roles") or set(value["roles"])-ROLES: raise ContractError("Declare miembros y funciones del equipo")
        member = element("member", value["name"], "Funciones actuales declaradas para el corte.", roles=value["roles"], active=True,
                         identity_history=[{"name": value["name"], "source": "migration-declaration", "since": now()}])
        member["meta"].update(state="active", nature="decision")
        additional.append(member); declared.append((value.get("key"), member))
    if policy["meta"]["data"]["independent_review"] and not any("reviewer" in m["meta"]["data"]["roles"] for m in additional):
        raise ContractError("Declare el equipo y revisor antes de activar la revisión independiente")
    version = "3.1" if method == "3.1.0" else "3.0"
    if method == "3.1.0":
        from v3_current import declared_collaboration
        policy["meta"]["data"]["collaboration"] = declared_collaboration(collaboration, person, declared)
    elif method != METHOD: raise ContractError("Método de destino desconocido")
    person["meta"].update(state="active", nature="decision"); policy["meta"].update(state="active", nature="decision")
    receipt = element("migration", "Conversión de contrato 2.0 a " + version, statement,
                      actor={"member": person["meta"]["uid"], "assurance": "declared", "source": "explicit-migration"},
                      source=copy.deepcopy(diagnostic), target={"format": version, "method": method}, git=git, recorded_at=now())
    receipt["meta"].update(state="completed", nature="fact")
    changes = {}
    if packet_directory:
        from v3_packet import Spool
        output = Path(packet_directory).resolve()
        if output == root or root in output.parents or output in root.parents: raise ContractError("Packet output must be outside the consumer")
        changes = Spool(output)
    for path, raw in source.inventory_changes.items(): changes[path] = raw
    if method == "3.1.0":
        from document_state import prepare as preserve_state, PREFIX
        # Existing history is retained in place; only the active/cutover sources need new backing objects.
        originals = {p: h for p, h in diagnostic["sources"].items() if not p.startswith((v2.HISTORY + "/", DOCS + "/00-control/migrations/"))}
        original_state = preserve_state(root, originals, changes)
        prefix = PREFIX + original_state + "/tree/"
        receipt["meta"]["data"]["original_state"] = original_state
    else: prefix = DOCS + "/00-control/migrations/" + receipt["meta"]["uid"] + "/tree/"
    mapping = {old.id: old.meta["uid"] for old in source.elements.values()}
    converted = {}
    for old in source.elements.values():
        meta = old.meta
        retained = {k: copy.deepcopy(v) for k, v in meta.items() if k not in {"id", "uid", "kind", "title", "revision", "state", "nature", "relations"}}
        retained["legacy"] = {"schema": "2.0", "method": source.manifest["method_version"], "id": old.id,
                              "path": old.path, "state": meta["state"], "source_sha256": source.hashes[old.path],
                              "original": prefix + old.path, "migration": receipt["meta"]["uid"]}
        # Old untyped dependencies retain the stricter requirement until explicit reconciliation.
        if old.kind == "task":
            retained["dependencies"] = [{"uid": mapping[k], "type": "verified", "legacy_untyped": True}
                                        for k in old.relations.get("depends_on", [])]
            retained["continuation"] = "historical" if meta["state"] in {"done", "completed", "cancelled", "done-with-reservations"} else "reconciliation-required"
        if old.kind in {"decision", "authorization", "execution", "checkpoint", "receipt"}:
            retained["historical_only"] = True
        if old.kind == "project":
            retained.update(method_version=method, policy=policy["meta"]["uid"], target=target,
                            legacy_project_id=source.manifest["project_id"], migrated_at=now())
        item = element(old.kind, meta["title"], old.body, identifier=meta["uid"], **retained)
        item["meta"].update(id=old.id, revision=meta["revision"], state=meta["state"], nature=meta["nature"],
                            relations={rel: [mapping[k] for k in values] for rel, values in old.relations.items()})
        converted[old.id] = item
    for old in source.by_kind("plan"):
        converted[old.id]["meta"]["relations"]["tasks"] = [mapping[t.id] for t in source.by_kind("task") if old.id in t.relations.get("plan", [])]
    dispositions = []
    for path, digest in diagnostic["sources"].items():
        # The current cutover retains history in place: its complete fresh hashes
        # are protected by the preview, without reading unused bytes a second time.
        if method != "3.1.0": changes[prefix + path] = read_bytes(root, path, limit=64*1024*1024)
        disposition = "preserved"
        if path in source.documents:
            text = source.documents[path]
            def replace(match):
                current = json.loads(match[1]); item = converted[current["id"]]
                return "<!-- lks-sdd: " + canonical(item["meta"]).decode() + " -->\n" + match[2].rstrip("\r\n") + "\n<!-- /lks-sdd -->"
            text = v2.BLOCK.sub(replace, text)
            text = re.sub(r'^schema_version: .*$', 'schema_version: "' + version + '"', text, count=1, flags=re.M)
            changes[path] = text.encode("utf-8"); disposition = "converted-with-original"
        elif path == INDEX: disposition = "rebuilt-with-original"
        original = path if method == "3.1.0" and path.startswith((v2.HISTORY + "/", DOCS + "/00-control/migrations/")) else prefix+path
        dispositions.append({"path": path, "sha256": digest, "original": original, "disposition": disposition})
    if method == "3.1.0":
        from v3_current import runtime_changes as plan_runtime
        runtime_changes = plan_runtime(root, runtime_bundle, "2.0")
        for path, raw in runtime_changes.items(): changes[path] = raw
    elif (root / ".lks-sdd/distribution-lock.json").exists():
        if runtime_bundle:
            import importlib.util
            spec = importlib.util.spec_from_file_location("v3_distribution_install", Path(__file__).resolve().parents[1]/"distribution/install.py")
            installer = importlib.util.module_from_spec(spec); spec.loader.exec_module(installer)
            installation = installer.plan(Path(runtime_bundle), root, "copilot", contract_transition=("2.0", "3.0"))
            runtime_changes = {entry["path"]: bytes.fromhex(entry["content"]) if entry["content"] is not None else None for entry in installation["changes"]}
        if not runtime_changes: raise ContractError("La vista previa debe incluir el runtime v3 fijado y sus adaptadores; actualizarlo forma parte del corte")
        lock = json.loads(runtime_changes.get(".lks-sdd/distribution-lock.json", b"{}"))
        if lock.get("project_schema") != "3.0": raise ContractError("Runtime de destino no admite el contrato 3.0")
        for path, raw in runtime_changes.items():
            if path.startswith(DOCS + "/") or path == INDEX: raise ContractError("El runtime no puede reemplazar documentación de negocio")
            changes[path] = raw
    confirmations = {}
    from v3_contract import parse
    for path in source.documents:
        for converted_unit in parse(changes[path], path)[0]:
            old = source.elements[converted_unit.id]
            if old.kind in {"feature", "requirement", "acceptance", "rule", "constraint", "test", "interface", "technology", "applicability"} and old.meta["state"] in {"confirmed", "approved", "effective", "active"} and old.meta["nature"] == "decision":
                confirmations[converted_unit.uid] = {"target_digest": converted_unit.digest(), "source_id": old.id,
                    "source_normative": fingerprint(old.normative()), "original": prefix + old.path,
                    "original_sha256": source.hashes[old.path], "source_state": old.meta["state"],
                    "actor": old.meta.get("actor"), "assurance": "recorded-canonical-confirmation-not-new-approval"}
    receipt["meta"]["data"].update(mapping=mapping, inventory=dispositions, continuation=diagnostic["tasks"], content_confirmations=confirmations)
    if method == "3.1.0":
        from content_store import prepare_object
        receipt["meta"]["data"]["source"].pop("sources", None)
        receipt["meta"]["data"]["inventory_ref"] = prepare_object(root, canonical({"format": "lks-sdd-migration-inventory/1", "entries": dispositions}), changes)
        receipt["meta"]["data"].pop("inventory", None)
    additions = [person, policy, *additional, receipt]
    if not source.by_kind("technology"):
        unknown = element("technology", "Tecnología heredada por reconciliar", "El formato de origen no incluía una declaración tecnológica local. Conserve las decisiones existentes y confirme únicamente la porción activa.", critical=True)
        unknown["meta"].update(state="unknown", nature="unknown")
        additions.append(unknown)
    from v3_storage import documentary_membership
    before_membership = documentary_membership(root)
    after_membership = set(before_membership)
    for path in changes:
        if path.startswith(DOCS + "/"):
            if changes[path] is None: after_membership.discard(path)
            else: after_membership.add(path)
    for item in additions:
        from v3_contract import location
        after_membership.add(location(item))
    packet = prepare(root, additions, "migration", changes=changes, method=method,
                     sources=diagnostic["sources"], guards={"git": git, "target_runtime": bool(runtime_changes),
                     "document_membership": {"before": fingerprint(before_membership), "after": fingerprint(sorted(after_membership))}})
    packet["summary"].update(migration=receipt["meta"]["uid"], member=person["meta"]["uid"], mapping=mapping,
                            converted=len(source.documents), preserved=len(dispositions), tasks=diagnostic["tasks"],
                            acceptance="Decisión actual sobre conversión/configuración; aprobaciones históricas no renovadas")
    return packet


def inherited_confirmations(model, expected):
    """Reuse only the exact canonical decisions supported by recoverable v2 bytes."""
    covered, originals = {}, {}
    from v3_approval import descriptor
    for receipt in model.by_kind("migration"):
        mapping = receipt.data.get("content_confirmations", {})
        for key, digest in expected.items():
            proof = mapping.get(key)
            if not proof or proof.get("target_digest") != digest: continue
            try:
                path = proof["original"]
                if path not in originals:
                    raw = read_bytes(model.root, path)
                    model.hashes[path] = sha(raw)
                    if sha(raw) != proof["original_sha256"]: continue
                    originals[path] = {e.id: e for e in v2.parse_document(raw.decode("utf-8"), path)[0]}
                old = originals[path][proof["source_id"]]
                if old.meta["nature"] != "decision" or old.meta["state"] not in {"confirmed", "approved", "active", "effective"}: continue
                if fingerprint(old.normative()) != proof["source_normative"]: continue
                dependencies = descriptor(model, [key])["units"]
                if any(mapping.get(k, {}).get("target_digest") != value for k, value in dependencies.items()): continue
                covered[key] = receipt.uid
            except (ContractError, KeyError, ValueError, UnicodeError): continue
    return covered


def include_confirmation_sources(model):
    paths = {p["original"] for r in model.by_kind("migration") for p in r.data.get("content_confirmations", {}).values()}
    for path in paths:
        try:
            model.hashes[path] = sha(read_bytes(model.root, path))
            from document_state import LINK, dependencies
            if LINK.fullmatch(path): model.hashes.update(dependencies(model.root, path))
        except ContractError: continue  # Missing support invalidates only a reuse that needs it.


def continuation(root):
    model = load(root).require_valid()
    return {"tasks": [{"source": t.source(), "state": t.data.get("continuation", "native-v3"),
                       "next": "Conservar resultado histórico" if t.data.get("continuation") == "historical" else
                       "Reconciliar propuesta y plan existentes; reutilizar solo decisiones de contenido con correspondencia exacta; autorizar el trabajo abierto"}
                      for t in model.by_kind("task")], "writes": []}


def old_branch(root, old_root):
    model = load(root).require_valid(); old = source_model(Path(old_root))
    receipts = model.by_kind("migration")
    if len(receipts) != 1: raise ContractError("Seleccione un mapa de migración inequívoco")
    mapping = receipts[0].data["mapping"]
    changes = []
    for entity in old.elements.values():
        target = mapping.get(entity.id)
        if not target: changes.append({"old": entity.id, "status": "new-in-old-branch", "next": "Crear identidad independiente y revisar su intención"}); continue
        current = model.get(target)
        if current.data.get("legacy", {}).get("source_sha256") != old.hashes[entity.path]:
            changes.append({"old": entity.id, "uid": target, "status": "review-change", "source": entity.source(), "target": current.source()})
    return {"status": "needs-reconciliation" if changes else "unchanged", "changes": changes, "writes": [],
            "next": "Aplicar las diferencias revisadas por author usando este mapa; conservar el origen y las decisiones v3"}
