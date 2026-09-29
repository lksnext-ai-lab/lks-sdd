"""Exact previews and recoverable writes; reuse the proven local v2 journal wire format."""
import base64
import json
from pathlib import Path
import tempfile

from v2_contract import ContractError, canonical, read_bytes, sha
from v2_storage import (apply as journal_apply, ensure_idle, preview, protected_inventory,
                        recover as journal_recover, write_one, exists_hash)
from v3_contract import DOCS, HISTORY, INDEX, BLOCK, load, location, render, fingerprint


def staged_write(root, name, data):
    """Ephemeral validation copies need no durability journal/fsync; real writes still do."""
    from v3_contract import path_at
    path = path_at(root, name, missing=True)
    if data is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def stage(root, changes, sources):
    with tempfile.TemporaryDirectory(prefix="lks-v3-stage-") as temp:
        target = Path(temp)
        for name in sources:
            if name.startswith(DOCS + "/") or name == INDEX:
                staged_write(target, name, read_bytes(root, name, limit=64 * 1024 * 1024))
        for name, data in changes.items(): staged_write(target, name, data)
        model = load(target).require_valid()
        return model.index()


def prepare(root, items, operation, *, changes=None, sources=None, guards=None):
    root = Path(root).resolve()
    ensure_idle(root)
    changes = dict(changes or {})
    previous = load(root) if (root / DOCS).exists() else None
    sources = dict(sources or {})
    if previous and not previous.errors:
        from v3_policy import policy_for
        from v3_migration import include_confirmation_sources
        include_confirmation_sources(previous)
        for request in previous.by_kind("request"): policy_for(previous, request)
        sources.update(previous.hashes)
    keys = [item["meta"]["uid"] for item in items]
    if len(keys) != len(set(keys)): raise ContractError("Identidad repetida en la escritura")
    for path in protected_inventory(root, [INDEX]): sources[path] = exists_hash(root, path)
    for item in items:
        key = item["meta"]["uid"]
        path = location(item)
        if previous and key in previous.elements:
            old = previous.elements[key]
            path = old.path
            if sum(e.path == path for e in previous.elements.values()) != 1:
                text = changes.get(path, read_bytes(root, path)).decode("utf-8")
                block = BLOCK.search(render(item).decode("utf-8"))[0]
                changes[path] = BLOCK.sub(lambda m: block if json.loads(m[1])["uid"] == key else m[0], text).encode("utf-8")
            else: changes[path] = render(item)
            saved = HISTORY + "/" + key + "/" + old.digest() + ".md"
            raw = render(old.item())
            saved_hash = exists_hash(root, saved)
            if saved_hash not in {None, sha(raw)}:
                from v3_contract import parse
                prior, _ = parse(read_bytes(root, saved), saved)
                if len(prior) != 1 or prior[0].uid != old.uid or prior[0].digest() != old.digest():
                    raise ContractError("Snapshot histórico contradictorio")
            elif saved_hash is None: changes[saved] = raw
        else: changes[path] = render(item)
    # Existing index is a projection; derive it in staging before authorizing writes.
    changes[INDEX] = canonical({"schema_version": "3.0"})
    changes[INDEX] = canonical(stage(root, changes, sources))
    guards = guards or {}
    expected = preview(root, changes, sources=sources, operation="v3:" + operation + ":" + base64.b64encode(canonical(guards)).decode())
    return {"preview": expected, "payload": {p: base64.b64encode(raw).decode() if raw is not None else None
                                              for p, raw in changes.items()},
            "guards": guards, "summary": {"operation": operation, "files": len(changes), "decision": "Autorizar estos cambios exactos"}}


def check_guards(root, guards):
    if guards.get("git"):
        from v3_git import observe
        current = observe(root)
        if any(current[k] != guards["git"][k] for k in ("branch", "head")):
            raise ContractError("La rama/base cambió después de preparar la operación")
    if guards.get("subject"):
        from v3_git import subject
        if subject(root, guards["subject"]["scope"]) != guards["subject"]:
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


def apply(root, packet, authorized_hash, *, interrupt_after=None):
    if not isinstance(packet, dict) or not packet.get("preview", {}).get("operation", "").startswith("v3:"):
        raise ContractError("Vista previa v3 requerida")
    expected = packet["preview"]
    guards = packet.get("guards", {})
    if expected["operation"].rsplit(":", 1)[-1] != base64.b64encode(canonical(guards)).decode(): raise ContractError("Precondiciones alteradas")
    if expected["preview_hash"] != authorized_hash or fingerprint({k: expected[k] for k in
            ("operation", "sources", "before", "after", "document_inventory")}) != authorized_hash:
        raise ContractError("Autorización de preview incorrecta")
    changes = {p: base64.b64decode(raw, validate=True) if raw is not None else None
               for p, raw in packet["payload"].items()}
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
    check_guards(Path(root), guards)
    stage(Path(root), changes, expected["sources"])
    def validate_result():
        check_guards(Path(root), guards)
        load(root).require_valid()
        validate_runtime(root, guards)
    return journal_apply(Path(root), changes, expected, authorized_hash,
                         validator=validate_result, interrupt_after=interrupt_after)


def recover(root, authorized_hash, *, rollback=False, receipt=None):
    from v2_storage import _load_transaction
    journal, _ = _load_transaction(Path(root), authorized_hash, receipt)
    operation = journal["preview"]["operation"]
    if not operation.startswith("v3:"): raise ContractError("Use el recuperador del formato de origen")
    guards = json.loads(base64.b64decode(operation.rsplit(":", 1)[-1], validate=True))
    if not rollback: check_guards(Path(root), guards)
    result = journal_recover(Path(root), authorized_hash, rollback=rollback, receipt=receipt)
    if not rollback:
        load(root).require_valid()
        validate_runtime(root, guards)
    return result
