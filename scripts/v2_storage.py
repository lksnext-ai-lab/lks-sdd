"""Preview-bound, recoverable local writes. Does not promise multi-file atomicity."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import tempfile
from contextvars import ContextVar
from capacity import recovering, CapacityRequired
from v2_contract import ContractError, DOCS, HISTORICAL_SOURCE, _read_regular, canonical, document_paths, fingerprint, path_at, read_bytes, sha
from path_utils import filesystem_root, publish_new_file
from object_zip import evaluated, invalidate, Publisher, PACKS, FORMAT as ZIP_FORMAT

PENDING = ".lks-sdd/transaction.json"
TRANSACTION_STORE = ".lks-sdd/transactions.json"
LEGACY_TRANSACTION_PREFIX = ".lks-sdd/transactions/"
VALIDATING = ContextVar("lks_v2_validating_transaction", default=False)
JOURNAL_BYTES = 128 * 1024 * 1024


def _journal_bytes(value):
    raw = canonical(value)
    if len(raw) > JOURNAL_BYTES:
        raise ContractError("Transaction metadata exceeds compatible recovery format; no changes authorized")
    return raw


def exists_hash(root: Path, relative: str):
    root = filesystem_root(root)
    path = path_at(root, relative, missing=True, package_data=True)
    if relative.startswith(".lks-sdd/objects/sha256/"):
        from object_zip import contains
        return sha(read_bytes(root, relative, limit=64*1024*1024)) if contains(root, relative) else None
    from document_state import LINK as STATE_LINK
    if STATE_LINK.fullmatch(relative): return sha(read_bytes(root, relative, limit=64*1024*1024, package_data=True))
    if HISTORICAL_SOURCE.fullmatch(relative):
        prefix = relative.split("/tree/", 1)[0]
        if path_at(root, prefix + "/snapshot.json", missing=True).is_file():
            return sha(read_bytes(root, relative, limit=64 * 1024 * 1024))
        # A legacy interrupted transaction can have written its tree before its
        # manifest. Hash physical bytes only for transaction conflict detection.
        if path.exists():
            return sha(_read_regular(root, relative, limit=64 * 1024 * 1024, package_data=True))
    if not path.exists():
        return None
    return sha(read_bytes(root, relative, limit=64 * 1024 * 1024, package_data=True))


def protected_inventory(root, extra=()):
    """Include later evidence/assets, not only Markdown, in recovery safety."""
    root = filesystem_root(root)
    from source_inventory import documents
    result = set(documents(root, excluded=(DOCS + "/00-control/history", DOCS + "/00-control/migrations"), limit=10000))
    known = {}
    if len(extra) >= 128:
        from source_inventory import documents, MIGRATION_PATH_LIMIT, MIGRATION_SCAN_BYTES
        known = documents(root, limit=MIGRATION_PATH_LIMIT, byte_limit=MIGRATION_SCAN_BYTES)
    for relative in extra:
        if relative not in result:
            if relative in known:
                result.add(relative)
                continue
            path_at(root, relative, missing=True, package_data=True)
            from object_zip import contains, OBJECTS
            if (contains(root, relative) if relative.startswith(OBJECTS)
                    else path_at(root, relative, missing=True, package_data=True).exists()):
                result.add(relative)
    return sorted(result)


def assert_sources(root, sources):
    # Large migration catalogs are enumerated once per check. Every byte is still
    # hashed freshly; virtual sources retain the reference-aware reader.
    known = {}
    if len(sources) >= 128:
        from source_inventory import documents, MIGRATION_PATH_LIMIT, MIGRATION_SCAN_BYTES
        known = documents(root, limit=MIGRATION_PATH_LIMIT, byte_limit=MIGRATION_SCAN_BYTES)
    from source_inventory import digest
    for relative, expected in sources.items():
        current = digest(known[relative]) if relative in known else exists_hash(root, relative)
        if current != expected: raise ContractError("Source changed since preview: " + relative)


def _pack_path(root, relative):
    key = relative.casefold()
    if key == PACKS.rstrip("/") or key.startswith(PACKS): return True
    # Windows 8.3 aliases can also name an existing reserved directory. Only
    # inspect possible aliases; normal business paths need no extra I/O.
    parts = relative.split("/")
    if os.name == "nt" and len(parts) >= 3 and any("~" in p for p in parts[:3]):
        from path_utils import same_filesystem_path
        return same_filesystem_path(path_at(root, "/".join(parts[:3]), missing=True, package_data=True),
                                    path_at(root, PACKS.rstrip("/"), missing=True))
    return False


def assert_reader_compatible(root, lock):
    """A pin-only rollback cannot make grouped objects readable by an old reader."""
    if lock is None: return False  # no target pinned reader; retain loose backups
    if isinstance(lock, bytes): lock = json.loads(lock)
    if not isinstance(lock, dict) or not isinstance(lock.get("storage_formats", []), list):
        raise ContractError("Invalid target storage capabilities")
    if ZIP_FORMAT in lock.get("storage_formats", []): return True
    folder = path_at(root, PACKS.rstrip("/"), missing=True)
    if folder.exists():
        if not folder.is_dir(): raise ContractError("Invalid object ZIP directory")
        with os.scandir(folder) as entries:
            if next(entries, None) is not None:
                raise ContractError("Incompatible ZIP reader: restore a verified compatible store before changing the pin")
    return False


@evaluated
def preview(root: Path, changes: dict[str, bytes | None], *, sources: dict[str, str], operation: str) -> dict:
    root = filesystem_root(root)
    paths = sorted(changes)
    before = {p: exists_hash(root, p) for p in paths}
    after = {p: sha(changes[p]) if changes[p] is not None else None for p in paths}
    inventory = protected_inventory(root, sources)
    payload = {"operation": operation, "sources": sources, "before": before, "after": after,
               "document_inventory": inventory}
    return {**payload, "preview_hash": fingerprint(payload), "writes": paths, "status": "preview"}


def write_one(root: Path, relative: str, data: bytes | None):
    root = filesystem_root(root)
    path = path_at(root, relative, missing=True, package_data=True)
    if data is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path_at(root, relative, missing=True, package_data=True)
    descriptor, name = tempfile.mkstemp(prefix=".lks-write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def ensure_idle(root: Path):
    root = filesystem_root(root)
    if path_at(root, PENDING, missing=True).exists():
        raise ContractError("Interrupted transaction: recover or rollback before any other mutation")


def _read_transaction_store(root: Path) -> dict:
    """Read the compact plugin-owned history of completed transactions."""
    root = filesystem_root(root)
    path = path_at(root, TRANSACTION_STORE, missing=True)
    if not path.exists():
        return {"schema_version": "2.0", "transactions": {}}
    try:
        value = json.loads(read_bytes(root, TRANSACTION_STORE, limit=128 * 1024 * 1024))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Transaction store is not valid JSON") from exc
    if not isinstance(value, dict) or value.get("schema_version") != "2.0":
        raise ContractError("Transaction store has an unsupported schema")
    transactions = value.get("transactions")
    if not isinstance(transactions, dict) or any(not isinstance(key, str) or not isinstance(item, dict)
                                                  for key, item in transactions.items()):
        raise ContractError("Transaction store has an invalid transaction map")
    return value


def _save_transaction(root: Path, transaction_hash: str, journal: dict) -> None:
    store = _read_transaction_store(root)
    if journal.get("schema_version") == "2.1":
        journal = {k: v for k, v in journal.items() if k != "preview"}
    store["transactions"][transaction_hash] = journal
    write_one(root, TRANSACTION_STORE, _journal_bytes(store))


def _expand_journal(root, journal):
    if journal.get("schema_version") == "2.1":
        from content_store import read_object
        from capacity import recorded, _preview
        approval = journal.get("capacity")
        with recorded(root, approval):
            journal = dict(journal, preview=json.loads(read_object(root, journal["preview_ref"])))
        if approval is not None and _preview(journal["preview"], journal["preview_hash"]) != approval:
            raise ContractError("Capacity recovery header differs from authorized preview")
    elif journal.get("schema_version") != "2.0":
        raise ContractError("Unsupported transaction journal format")
    return journal


def _payload(root, journal, encoded):
    if encoded is None:
        return None
    if journal["schema_version"] == "2.1":
        from content_store import read_object
        return read_object(root, encoded)
    return base64.b64decode(encoded, validate=True)


def _load_transaction(root: Path, authorized_hash: str, receipt: str | None) -> tuple[dict, str]:
    if receipt is None:
        source = PENDING
        journal = json.loads(read_bytes(root, source, limit=128 * 1024 * 1024))
        return _expand_journal(root, journal), source
    legacy = LEGACY_TRANSACTION_PREFIX + authorized_hash + ".json"
    if receipt == TRANSACTION_STORE:
        store = _read_transaction_store(root)
        journal = store["transactions"].get(authorized_hash)
        if not isinstance(journal, dict):
            raise ContractError("Transaction store has no receipt for the authorized hash")
        return _expand_journal(root, journal), receipt
    if receipt != legacy:
        raise ContractError("Receipt must identify the exact authorized transaction")
    return _expand_journal(root, json.loads(read_bytes(root, receipt, limit=128 * 1024 * 1024))), receipt


@evaluated
def stage_contract(root, changes, sources):
    """Validate prospective Markdown in an isolated temporary tree, not the consumer."""
    root = filesystem_root(root)
    from v2_contract import load, LINK, ASSET, BLOCK, resolve_link
    from urllib.parse import urlsplit
    checked = dict(sources)
    for name, raw in changes.items():
        if raw is None or not name.endswith(".md") or "/00-control/history/" in name:
            continue
        content = raw.decode("utf-8")
        targets = [angled or plain for _, angled, plain in LINK.findall(content)]
        targets += [angled or plain for angled, plain in ASSET.findall(content)]
        for match in BLOCK.finditer(content):
            meta = json.loads(match[1])
            for asset in meta.get("baseline_assets", []):
                if asset not in changes and asset not in checked:
                    checked[asset] = sha(read_bytes(root, asset, limit=16 * 1024 * 1024))
        for target in targets:
            if urlsplit(target).scheme:
                continue
            relative, _ = resolve_link(name, target)
            if relative in changes or relative in checked:
                continue
            candidate = path_at(root, relative, missing=True)
            if candidate.is_file() or HISTORICAL_SOURCE.fullmatch(relative):
                checked[relative] = sha(read_bytes(root, relative, limit=16 * 1024 * 1024))
    with tempfile.TemporaryDirectory(prefix="lks-v2-stage-") as directory:
        stage_root = Path(directory)
        from object_zip import stage_writer
        write, finish_objects = stage_writer(stage_root, write_one)
        from v2_history import link_dependencies
        for relative in list(checked):
            if HISTORICAL_SOURCE.fullmatch(relative):
                checked.update(link_dependencies(root, relative))
        for relative in checked:
            if relative in changes or relative.startswith(".lks-sdd/runtime/"):
                continue
            write(relative, read_bytes(root, relative, limit=64 * 1024 * 1024))
        for relative, raw in changes.items():
            if (relative.startswith((DOCS + "/", ".lks-sdd/objects/")) or relative == ".lks-sdd/project.json") and raw is not None:
                write(relative, raw)
        finish_objects()
        load(stage_root).require_valid()
    return checked


@evaluated
def apply(root: Path, changes: dict[str, bytes | None], expected: dict, authorized_hash: str,
          *, validator=None, interrupt_after: int | None = None) -> dict:
    root = filesystem_root(root)
    ensure_idle(root)
    invalidate(root)
    if any(_pack_path(root, p) for p in changes):
        raise ContractError("Business transactions cannot alter object ZIP containers")
    fresh = preview(root, changes, sources=expected["sources"], operation=expected["operation"])
    if fresh["preview_hash"] != authorized_hash or expected["preview_hash"] != authorized_hash:
        raise ContractError("Missing or stale exact preview authorization")
    assert_sources(root, expected["sources"])
    pin = ".lks-sdd/distribution-lock.json"
    target_zip = assert_reader_compatible(root, changes[pin]) if pin in changes else None
    from content_store import OBJECTS, publish_object
    for p, data in changes.items():
        if p.startswith(OBJECTS) and (data is None or p != OBJECTS + sha(data)):
            raise ContractError("Content objects are immutable")
    publisher = Publisher(root)
    if target_zip is False: publisher.enabled = False
    publish = publisher.add
    before = {p: publish(read_bytes(root, p, limit=64 * 1024 * 1024, package_data=True))
              if expected["before"][p] is not None else None for p in changes}
    after = {p: publish(data) if data is not None else None for p, data in changes.items()}
    journal = {"schema_version": "2.1", "preview_ref": publish(canonical(expected)),
               "preview_hash": authorized_hash, "state": "applying", "before": before, "after": after}
    from capacity import _preview
    if resource_consent := _preview(expected, authorized_hash):
        journal["capacity"] = resource_consent
    pending_raw = _journal_bytes(journal)
    terminal_store = _read_transaction_store(root)
    terminal_store["transactions"][authorized_hash] = {**journal, "state": "rolled-back"}
    _journal_bytes(terminal_store)
    publisher.flush()
    if pin in changes: assert_reader_compatible(root, changes[pin])
    # Unreferenced immutable objects may survive a failure before the journal.
    # They have no authority; recovery never deletes shared content objects.
    journal_path = path_at(root, PENDING, missing=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects this local workspace only, not other clones.
    try:
        path_at(root, PENDING, missing=True)
        publish_new_file(journal_path, pending_raw, prefix=".lks-transaction-")
    except FileExistsError as exc:
        raise ContractError("Another local transaction owns the workspace") from exc
    modified = False
    try:
        # Another transaction may have finished during object preparation. Owning
        # the journal now does not authorize restoring bytes written by that actor.
        invalidate(root)
        if protected_inventory(root, expected["sources"]) != expected["document_inventory"]:
            raise ContractError("Document inventory changed before journal ownership")
        assert_sources(root, expected["sources"])
        if pin in changes: assert_reader_compatible(root, changes[pin])
        for number, (relative, data) in enumerate(changes.items(), start=1):
            actual = exists_hash(root, relative)
            if actual != expected["before"][relative] and not (relative.startswith(OBJECTS) and actual == expected["after"][relative]):
                raise ContractError("Concurrent modification during apply: " + relative)
            if actual != expected["after"][relative]:
                if relative.startswith(OBJECTS):
                    publish_object(root, relative, data)
                else:
                    write_one(root, relative, data)
                    modified = True
            if interrupt_after == number:
                raise InterruptedError("Injected interruption; durable journal retained")
        if validator:
            token = VALIDATING.set(True)
            try:
                validator()
            finally:
                VALIDATING.reset(token)
    except (InterruptedError, CapacityRequired):
        raise
    except Exception:
        if modified:
            # Do not overwrite external edits made after our write.
            recover(root, authorized_hash, rollback=True)
        elif exists_hash(root, PENDING) == sha(canonical(journal)):
            # No mutable source was written: remove only our exact journal. Shared
            # prepared objects remain harmless; preserve the competing work.
            journal_path.unlink()
        raise
    journal["state"] = "completed"
    _save_transaction(root, authorized_hash, journal)
    journal_path.unlink()
    return {"status": "applied", "preview_hash": authorized_hash, "receipt": TRANSACTION_STORE,
            "writes": sorted(changes)}


@evaluated
@recovering
def recover(root: Path, authorized_hash: str, *, rollback: bool = False, receipt: str | None = None) -> dict:
    root = filesystem_root(root)
    invalidate(root)
    if path_at(root, PENDING, missing=True).exists():
        # Preserve the legacy 128 MiB admission bound. Only maintenance has the
        # smaller journal budget; its dispatcher must not narrow business 2.0.
        tag = json.loads(_read_regular(root, PENDING, limit=128*1024*1024)).get("schema_version")
        if tag in {"lks-sdd-store-maintenance/1", "lks-sdd-store-maintenance/2"}:
            if rollback or receipt: raise ContractError("Business rollback cannot alter physical storage")
            if tag.endswith('/2'):
                from store_compaction import recover as maintenance_recover
            else:
                from store_maintenance import recover as maintenance_recover
            return maintenance_recover(root, authorized_hash)
    journal, source = _load_transaction(root, authorized_hash, receipt)
    expected = journal["preview"]
    if expected["preview_hash"] != authorized_hash or fingerprint({k: expected[k] for k in
            ("operation", "sources", "before", "after", "document_inventory")}) != authorized_hash:
        raise ContractError("Transaction identity mismatch")
    from content_store import OBJECTS, publish_object
    for side in ("before", "after"):
        if set(journal[side]) != set(expected[side]):
            raise ContractError("Transaction payload inventory mismatch")
        for relative, encoded in journal[side].items():
            if _pack_path(root, relative):
                raise ContractError("Business recovery cannot alter object ZIP containers")
            value = _payload(root, journal, encoded)
            if (sha(value) if value is not None else None) != expected[side][relative]:
                raise ContractError("Transaction payload integrity mismatch")
            if relative.startswith(OBJECTS) and value is not None and relative != OBJECTS + sha(value):
                raise ContractError("Content objects are immutable")
    for relative in expected["before"]:
        current = exists_hash(root, relative)
        allowed = {expected["before"][relative], expected["after"][relative]}
        if receipt and journal["state"] == "completed":
            allowed = {expected["after"][relative]}
        if current not in allowed:
            raise ContractError("Recovery conflict; later work preserved: " + relative)
    assert_sources(root, {relative: digest for relative, digest in expected["sources"].items() if relative not in expected["before"]})
    current_documents = set(protected_inventory(root))
    allowed_documents = (set(expected["document_inventory"]) | set(expected["after"])
                         | set(expected["sources"]))
    if current_documents - allowed_documents:
        raise ContractError("Recovery conflict: new documents were created after the transaction")
    if receipt and journal["state"] == "rolled-back":
        raise ContractError("Transaction already rolled back; a new explicit preview is required")
    side = "before" if rollback else "after"
    pin = ".lks-sdd/distribution-lock.json"
    if pin in journal[side]: assert_reader_compatible(root, _payload(root, journal, journal[side][pin]))
    for relative, encoded in journal[side].items():
        if relative.startswith(OBJECTS) and encoded is None:
            continue
        value = _payload(root, journal, encoded)
        if relative.startswith(OBJECTS):
            publish_object(root, relative, value)
        else:
            write_one(root, relative, value)
    journal["state"] = "rolled-back" if rollback else "completed"
    _save_transaction(root, authorized_hash, journal)
    if source.startswith(LEGACY_TRANSACTION_PREFIX):
        path_at(root, source, missing=True).unlink(missing_ok=True)
    pending = path_at(root, PENDING, missing=True)
    if pending.exists():
        pending.unlink()
    return {"status": journal["state"], "receipt": TRANSACTION_STORE, "writes": sorted(journal[side])}
