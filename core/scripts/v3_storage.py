"""Exact previews and recovery through the shared, versioned local journal."""
import base64
import json
from pathlib import Path
import tempfile
import copy

from v2_contract import ContractError, canonical, read_bytes, sha
from v2_storage import (apply as journal_apply, ensure_idle, preview, protected_inventory,
                        recover as journal_recover, exists_hash)
from v3_contract import DOCS, HISTORY, INDEX, BLOCK, load, location, render, fingerprint
from object_zip import evaluated


def staged_write(root, name, data):
    """Ephemeral validation copies need no durability journal/fsync; real writes still do."""
    from v3_contract import path_at
    path = path_at(root, name, missing=True)
    if data is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


@evaluated
def stage(root, changes, sources, *, history_catalog=False, guards=None):
    with tempfile.TemporaryDirectory(prefix="lks-v3-stage-") as temp:
        target = Path(temp)
        from object_zip import stage_writer
        write, finish_objects = stage_writer(target, staged_write)
        needed_history = set()
        from v2_contract import LINK, ASSET, resolve_link
        from urllib.parse import urlsplit
        for path, raw in changes.items():
            if raw is None or not path.endswith(".md") or path.startswith(HISTORY + "/"): continue
            text = raw.decode("utf-8")
            links = [a or p for _, a, p in LINK.findall(text)] + [a or p for a, p in ASSET.findall(text)]
            for link in links:
                if not urlsplit(link).scheme:
                    needed_history.add(resolve_link(path, link)[0])
        for name in sources:
            if name in changes: continue
            from document_state import LINK as STATE_LINK, dependencies
            if STATE_LINK.fullmatch(name):
                for dependency in dependencies(root, name):
                    if dependency not in changes: write(dependency, read_bytes(root, dependency, limit=64*1024*1024))
                continue
            if name.startswith((HISTORY + "/", DOCS + "/00-control/migrations/")) and name not in needed_history:
                # Approved historical units are explicit sources; unlike migration's complete catalog.
                if history_catalog: continue
            if name.startswith((DOCS + "/", ".lks-sdd/objects/")) or name == INDEX:
                write(name, read_bytes(root, name, limit=64 * 1024 * 1024))
        for name, data in changes.items(): write(name, data)
        if guards and guards.get("target_runtime"):
            lock_path = ".lks-sdd/distribution-lock.json"
            lock_raw = changes.get(lock_path)
            if lock_raw is None: lock_raw = read_bytes(root, lock_path)
            lock = json.loads(lock_raw)
            names = [lock_path, *(lock["runtime"] + "/" + p for p in lock["runtime_files"]), *lock["managed_files"]]
            for name in names:
                if name not in changes: write(name, read_bytes(root, name, limit=64*1024*1024, package_data=True))
        finish_objects()
        model = load(target).require_valid()
        staged_write(target, INDEX, canonical(model.index()))
        if guards: validate_runtime(target, guards)
        return model.index()


@evaluated
def prepare(root, items, operation, *, changes=None, sources=None, guards=None, packet_directory=None, method=None, state_sources=None):
    root = Path(root).resolve()
    ensure_idle(root)
    from v3_packet import Spool
    if isinstance(changes, Spool):
        pass
    elif packet_directory:
        output = Path(packet_directory).resolve()
        if output == root or root in output.parents or output in root.parents:
            raise ContractError("Packet output must be outside the consumer")
        spool = Spool(output)
        for path, raw in (changes or {}).items(): spool[path] = raw
        changes = spool
    else: changes = dict(changes or {})
    from v3_inventories import externalize
    items = copy.deepcopy(items)
    from v3_usage import pending
    usage_items, usage_changes = pending(root)
    items += usage_items
    for path, raw in usage_changes.items():
        if path in changes and changes[path] != raw: raise ContractError("Conflicting usage object")
        changes[path] = raw
    sources = dict(sources or {})
    guards = dict(guards or {})
    from v3_presentation_guard import stamp
    presented_sources = stamp(root, items, sources, guards) or set()
    guards = externalize(root, "execution", guards, changes)
    for item in items:
        item["meta"]["data"] = externalize(root, item["meta"]["kind"], item["meta"]["data"], changes)
    from v3_cli import is_v3
    previous = load(root) if is_v3(root) else None
    sources = dict(sources or {})
    if previous and not previous.errors:
        from v3_policy import policy_for
        from v3_migration import include_confirmation_sources
        include_confirmation_sources(previous)
        for request in previous.by_kind("request"): policy_for(previous, request)
        if any(path in sources and sources[path] != digest for path, digest in previous.hashes.items()):
            raise ContractError("Una fuente cambió durante la preparación; presente de nuevo el contenido afectado")
        sources.update(previous.hashes)
    # A presentation guard can have published an inventory before an event first
    # references it. Existing immutable objects still belong in staging sources.
    from content_store import object_path, read_object
    from v3_inventories import subjects, FIELDS, KINDS, MAP_KINDS
    for inventory_kind, data in [("execution", guards), *((item["meta"]["kind"], item["meta"]["data"]) for item in items)]:
        if inventory_kind not in KINDS: continue
        refs = [data[field + "_ref"] for field in FIELDS if inventory_kind in MAP_KINDS and field + "_ref" in data]
        refs += [parent[field]["files_ref"] for parent, field in subjects(data) if "files_ref" in parent[field]]
        if inventory_kind == "receipt" and data.get("purpose") == "usage-observation":
            ref = data["observations_ref"]; refs.append(ref)
            raw = changes[object_path(ref)] if object_path(ref) in changes else read_object(root,ref)
            value = json.loads(raw)
            refs += [f.get("text_ref",f.get("data_ref")) for row in value["observations"] for f in row["fragments"] if "text_ref" in f or "data_ref" in f]
        for ref in refs:
            name = object_path(ref)
            if name not in changes:
                read_object(root, ref)
                sources[name] = ref["sha256"]
    keys = [item["meta"]["uid"] for item in items]
    project = next((i for i in items if i["meta"]["kind"] == "project"), None)
    method = method or (project["meta"]["data"]["method_version"] if project else (previous.project.data["method_version"] if previous and not previous.errors else "3.0.0"))
    from v3_contract import METHODS
    version = METHODS[method]
    if len(keys) != len(set(keys)): raise ContractError("Identidad repetida en la escritura")
    protected = protected_inventory(root, [INDEX])
    for path in protected: sources[path] = exists_hash(root, path)
    state = None
    if previous and not previous.errors and items:
        from document_state import prepare as preserve_state
        # Keep approved per-UID revisions and preserve exact files/assets for state reconstruction.
        documentary = sources
        if state_sources is not None:
            # Code preconditions remain in the exact preview and all fresh checks.
            # Preserve only documentary inputs, plus canonical and presented dependencies.
            names = set(state_sources) | set(protected) | set(previous.hashes) | presented_sources
            if not names <= set(sources): raise ContractError("Documentary state source missing from exact preconditions")
            documentary = {p: sources[p] for p in names}
        state = preserve_state(root, documentary, changes)
    for item in items:
        key = item["meta"]["uid"]
        path = location(item)
        if previous and key in previous.elements:
            old = previous.elements[key]
            path = old.path
            if sum(e.path == path for e in previous.elements.values()) != 1:
                text = changes.get(path, read_bytes(root, path)).decode("utf-8")
                block = BLOCK.search(render(item, version).decode("utf-8"))[0]
                changes[path] = BLOCK.sub(lambda m: block if json.loads(m[1])["uid"] == key else m[0], text).encode("utf-8")
            else: changes[path] = render(item, version)
            saved = HISTORY + "/" + key + "/" + old.digest() + ".md"
            raw = render(old.item())
            saved_hash = exists_hash(root, saved)
            if saved_hash not in {None, sha(raw)}:
                from v3_contract import parse
                prior, _ = parse(read_bytes(root, saved), saved)
                if len(prior) != 1 or prior[0].uid != old.uid or prior[0].digest() != old.digest():
                    raise ContractError("Snapshot histórico contradictorio")
            elif saved_hash is None: changes[saved] = raw
        else: changes[path] = render(item, version)
    # Existing index is a projection; derive it in staging before authorizing writes.
    changes[INDEX] = canonical({"schema_version": version})
    changes[INDEX] = canonical(stage(root, changes, sources, history_catalog=operation == "migration", guards=guards))
    guards = guards or {}
    expected = preview(root, changes, sources=sources, operation="v3:" + operation + ":" + base64.b64encode(canonical(guards)).decode())
    packet = {"preview": expected,
            "guards": guards, "summary": {"operation": operation, "files": len(changes), "decision": "Aplicar solo dentro del alcance ya autorizado; presentar cualquier decisión nueva con decision-view"}}
    if state: packet["summary"]["previous_state"] = state
    if isinstance(changes, Spool):
        from v3_packet import finish
        return finish(packet, changes)
    return {**packet, "payload": {p: base64.b64encode(raw).decode() if raw is not None else None
                                              for p, raw in changes.items()},
            }


def documentary_membership(root):
    from source_inventory import documents, MIGRATION_PATH_LIMIT, MIGRATION_SCAN_BYTES
    return sorted(documents(root, limit=MIGRATION_PATH_LIMIT, byte_limit=MIGRATION_SCAN_BYTES))


def check_guards(root, guards, *, phase="before", changes=None):
    if guards.get("document_membership") and phase is not None:
        if fingerprint(documentary_membership(root)) != guards["document_membership"][phase]:
            raise ContractError("Historical/document membership changed after preparation")
    if guards.get("git"):
        from v3_git import observe
        current = observe(root)
        if any(current[k] != guards["git"][k] for k in ("branch", "head")):
            raise ContractError("La rama/base cambió después de preparar la operación")
    if guards.get("subject"):
        from v3_git import subject
        value = guards["subject"]
        from v3_inventories import subject as resolve_subject
        if "files_ref" in value and changes is not None:
            from content_store import object_path, read_object
            ref = value["files_ref"]; name = object_path(ref)
            raw = changes[name] if name in changes else read_object(root, ref)
            if raw is None or len(raw) != ref["bytes"] or sha(raw) != ref["sha256"]: raise ContractError("Guard inventory altered")
            inventory = json.loads(raw)
            if set(inventory) != {"format", "files"} or inventory["format"] != "lks-sdd-inventory/1": raise ContractError("Invalid guard inventory")
            value = {"scope": value["scope"], "digest": value["digest"], "files": inventory["files"]}
        value = resolve_subject(root, value)
        if subject(root, value["scope"]) != value:
            raise ContractError("Las entradas cambiaron después de preparar la operación")
    if guards.get("code_inventory"):
        from v3_git import code_inventory
        if fingerprint(code_inventory(root)) != guards["code_inventory"]:
            raise ContractError("El inventario de código cambió después de la comprobación de alcance")
    if guards.get("expires_at"):
        from v3_policy import active_period
        if not active_period(guards): raise ContractError("La evidencia o excepción venció antes de persistir el avance")
    if guards.get("trusted"):
        expected = guards["trusted"]
        trusted = load(expected["root"]).require_valid()
        if trusted.snapshot() != expected["snapshot"]:
            raise ContractError("La base de confianza cambió después de revisar la integración")
        if expected.get("git"):
            from v3_git import observe
            current = observe(trusted.root)
            if any(current[k] != expected["git"][k] for k in ("head", "branch")):
                raise ContractError("La rama destino cambió después de revisar la integración")


def validate_runtime(root, guards):
    if guards.get("target_runtime"):
        from runtime_doctor import check
        result = check(Path(root))
        if result["status"] != "valid": raise ContractError("Runtime de destino incompleto: " + str(result["errors"]))


def apply(root, packet, authorized_hash, *, interrupt_after=None, current=False):
    if not isinstance(packet, dict) or not packet.get("preview", {}).get("operation", "").startswith("v3:"):
        raise ContractError("Vista previa v3 requerida")
    expected = packet["preview"]
    guards = packet.get("guards", {})
    if expected["operation"].rsplit(":", 1)[-1] != base64.b64encode(canonical(guards)).decode(): raise ContractError("Precondiciones alteradas")
    if expected["preview_hash"] != authorized_hash or fingerprint({k: expected[k] for k in
            ("operation", "sources", "before", "after", "document_inventory")}) != authorized_hash:
        raise ContractError("Autorización de preview incorrecta")
    from v3_packet import FORMAT, Payload, InlinePayload
    if packet.get("format") == FORMAT: changes = Payload(packet)
    elif "format" in packet: raise ContractError("Unsupported packet format")
    else:
        changes = InlinePayload(packet)
    if set(changes) != set(expected["after"]): raise ContractError("Inventario de preview alterado")
    if any((sha(raw) if raw is not None else None) != expected["after"][p] for p, raw in changes.items()):
        raise ContractError("Contenido de preview alterado")
    from v2_storage import _load_transaction, TRANSACTION_STORE
    if (Path(root)/TRANSACTION_STORE).exists():
        try: journal, _ = _load_transaction(Path(root), authorized_hash, TRANSACTION_STORE)
        except ContractError: journal = None
        if journal and journal["state"] == "completed" and journal["preview"] == expected:
            return {"status": "previously-applied", "preview_hash": authorized_hash, "receipt": TRANSACTION_STORE,
                    "writes": [], "current_conformance": "not-reasserted; consult current state"}
    check_guards(Path(root), guards, changes=changes)
    target = stage(Path(root), changes, expected["sources"], history_catalog=expected["operation"].startswith("v3:migration:"), guards=guards)
    if current:
        if target["method_version"] != "3.1.0": raise ContractError("Current public writes require method 3.1.0")
        cutover = any(expected["operation"].startswith("v3:" + name + ":") for name in ("migration", "initialize", "configure-collaboration"))
        if cutover and not guards.get("target_runtime"): raise ContractError("Current cutover requires its pinned runtime")
        if not cutover:
            from v3_current import require_current, require_requests
            from v3_contract import parse
            current_model = require_current(root)
            selected = set()
            for path in changes:
                if not path.startswith(DOCS + "/") or path.startswith(HISTORY + "/") or not path.endswith(".md") or changes[path] is None: continue
                for item in parse(changes[path], path)[0]:
                    keys = {item.uid}
                    keys.update(item.data.get(field) for field in ("request", "task", "plan", "problem", "correction") if isinstance(item.data.get(field), str))
                    descriptor = item.data.get("descriptor")
                    if isinstance(descriptor, dict) and isinstance(descriptor.get("units"), dict):
                        # Normative roots that are actually approved/authorized;
                        # shared read-only requirements do not activate their scope.
                        keys.update(key for key in descriptor["units"] if key in current_model.elements and
                                    current_model.elements[key].kind in {"request", "proposal", "task", "plan"})
                    for key in keys:
                        entry = current_model.elements.get(key)
                        if entry:
                            if entry.kind == "request": selected.add(entry.uid)
                            elif entry.data.get("request"): selected.add(entry.data["request"])
            require_requests(current_model, selected)
    def validate_result():
        check_guards(Path(root), guards, phase="after")
        load(root).require_valid()
        validate_runtime(root, guards)
    return journal_apply(Path(root), changes, expected, authorized_hash,
                         validator=validate_result, interrupt_after=interrupt_after)


def recover(root, authorized_hash, *, rollback=False, receipt=None):
    from v2_storage import PENDING
    pending = Path(root)/PENDING
    if pending.exists():
        from v2_contract import _read_regular
        from store_maintenance import FORMAT, recover as maintenance_recover
        journal_tag = json.loads(_read_regular(root, PENDING, limit=128*1024*1024)).get('schema_version')
        if journal_tag == FORMAT:
            if rollback or receipt: raise ContractError("Use explicit maintenance recovery; business rollback cannot alter physical storage")
            return maintenance_recover(root, authorized_hash)
    from v2_storage import _load_transaction
    journal, _ = _load_transaction(Path(root), authorized_hash, receipt)
    operation = journal["preview"]["operation"]
    if not operation.startswith("v3:"): raise ContractError("Use el recuperador del formato de origen")
    guards = json.loads(base64.b64decode(operation.rsplit(":", 1)[-1], validate=True))
    if guards.get("document_membership"):
        allowed = set(journal["preview"]["document_inventory"]) | set(journal["preview"]["after"])
        if set(documentary_membership(Path(root))) - allowed:
            raise ContractError("Recovery conflict: later historical/documentary membership preserved")
    if not rollback: check_guards(Path(root), guards, phase=None)
    result = journal_recover(Path(root), authorized_hash, rollback=rollback, receipt=receipt)
    if not rollback:
        check_guards(Path(root), guards, phase="after")
        load(root).require_valid()
        validate_runtime(root, guards)
    return result
