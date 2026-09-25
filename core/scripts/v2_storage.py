"""Preview-bound, recoverable local writes. Does not promise multi-file atomicity."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import tempfile
from contextvars import ContextVar

from v2_contract import ContractError, DOCS, canonical, document_paths, fingerprint, path_at, read_bytes, sha
from path_utils import filesystem_root

PENDING = ".lks-sdd/transaction.json"
TRANSACTION_STORE = ".lks-sdd/transactions.json"
LEGACY_TRANSACTION_PREFIX = ".lks-sdd/transactions/"
VALIDATING = ContextVar("lks_v2_validating_transaction", default=False)


def exists_hash(root: Path, relative: str):
    root = filesystem_root(root)
    path = path_at(root, relative, missing=True, package_data=True)
    if not path.exists():
        return None
    return sha(read_bytes(root, relative, limit=64 * 1024 * 1024, package_data=True))


def protected_inventory(root, extra=()):
    """Include later evidence/assets, not only Markdown, in recovery safety."""
    root = filesystem_root(root)
    base = path_at(root, DOCS, missing=True)
    result = []
    if base.exists():
        for directory, folders, files in os.walk(base, followlinks=False):
            folders[:] = [f for f in folders if (Path(directory) / f).relative_to(root).as_posix() not in {
                DOCS + "/00-control/history", DOCS + "/00-control/migrations"}]
            for name in folders + files:
                path_at(root, (Path(directory) / name).relative_to(root).as_posix())
            result.extend((Path(directory) / f).relative_to(root).as_posix() for f in files)
            if len(result) > 10000:
                raise ContractError("Protected document inventory exceeds recovery bounds")
    for relative in extra:
        if relative not in result:
            path_at(root, relative, missing=True, package_data=True)
            if path_at(root, relative, missing=True, package_data=True).exists():
                result.append(relative)
    return sorted(set(result))


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
    store["transactions"][transaction_hash] = journal
    write_one(root, TRANSACTION_STORE, canonical(store))


def _load_transaction(root: Path, authorized_hash: str, receipt: str | None) -> tuple[dict, str]:
    if receipt is None:
        source = PENDING
        journal = json.loads(read_bytes(root, source, limit=128 * 1024 * 1024))
        return journal, source
    legacy = LEGACY_TRANSACTION_PREFIX + authorized_hash + ".json"
    if receipt == TRANSACTION_STORE:
        store = _read_transaction_store(root)
        journal = store["transactions"].get(authorized_hash)
        if not isinstance(journal, dict):
            raise ContractError("Transaction store has no receipt for the authorized hash")
        return journal, receipt
    if receipt != legacy:
        raise ContractError("Receipt must identify the exact authorized transaction")
    return json.loads(read_bytes(root, receipt, limit=128 * 1024 * 1024)), receipt


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
            if candidate.is_file():
                checked[relative] = sha(read_bytes(root, relative, limit=16 * 1024 * 1024))
    with tempfile.TemporaryDirectory(prefix="lks-v2-stage-") as directory:
        stage_root = Path(directory)
        for relative in checked:
            if relative in changes or relative.startswith(".lks-sdd/runtime/"):
                continue
            write_one(stage_root, relative, read_bytes(root, relative, limit=64 * 1024 * 1024))
        for relative, raw in changes.items():
            if (relative.startswith(DOCS + "/") or relative == ".lks-sdd/project.json") and raw is not None:
                write_one(stage_root, relative, raw)
        load(stage_root).require_valid()
    return checked


def apply(root: Path, changes: dict[str, bytes | None], expected: dict, authorized_hash: str,
          *, validator=None, interrupt_after: int | None = None) -> dict:
    root = filesystem_root(root)
    ensure_idle(root)
    fresh = preview(root, changes, sources=expected["sources"], operation=expected["operation"])
    if fresh["preview_hash"] != authorized_hash or expected["preview_hash"] != authorized_hash:
        raise ContractError("Missing or stale exact preview authorization")
    for relative, value in expected["sources"].items():
        if exists_hash(root, relative) != value:
            raise ContractError("Source changed since preview: " + relative)
    before = {p: base64.b64encode(read_bytes(root, p, limit=64 * 1024 * 1024, package_data=True)).decode()
              if expected["before"][p] is not None else None for p in changes}
    journal = {"schema_version": "2.0", "preview": expected, "state": "applying", "before": before,
               "after": {p: base64.b64encode(data).decode() if data is not None else None for p, data in changes.items()}}
    journal_path = path_at(root, PENDING, missing=True)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects this local workspace only, not other clones.
    try:
        with journal_path.open("xb") as stream:
            stream.write(canonical(journal))
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise ContractError("Another local transaction owns the workspace") from exc
    try:
        for number, (relative, data) in enumerate(changes.items(), start=1):
            if exists_hash(root, relative) != expected["before"][relative]:
                raise ContractError("Concurrent modification during apply: " + relative)
            write_one(root, relative, data)
            if interrupt_after == number:
                raise InterruptedError("Injected interruption; durable journal retained")
        if validator:
            token = VALIDATING.set(True)
            try:
                validator()
            finally:
                VALIDATING.reset(token)
    except InterruptedError:
        raise
    except Exception:
        # Do not overwrite external edits made after our write.
        recover(root, authorized_hash, rollback=True)
        raise
    journal["state"] = "completed"
    _save_transaction(root, authorized_hash, journal)
    journal_path.unlink()
    return {"status": "applied", "preview_hash": authorized_hash, "receipt": TRANSACTION_STORE,
            "writes": sorted(changes)}


def recover(root: Path, authorized_hash: str, *, rollback: bool = False, receipt: str | None = None) -> dict:
    root = filesystem_root(root)
    journal, source = _load_transaction(root, authorized_hash, receipt)
    expected = journal["preview"]
    if expected["preview_hash"] != authorized_hash or fingerprint({k: expected[k] for k in
            ("operation", "sources", "before", "after", "document_inventory")}) != authorized_hash:
        raise ContractError("Transaction identity mismatch")
    for side in ("before", "after"):
        if set(journal[side]) != set(expected[side]):
            raise ContractError("Transaction payload inventory mismatch")
        for relative, encoded in journal[side].items():
            value = base64.b64decode(encoded, validate=True) if encoded is not None else None
            if (sha(value) if value is not None else None) != expected[side][relative]:
                raise ContractError("Transaction payload integrity mismatch")
    for relative in expected["before"]:
        current = exists_hash(root, relative)
        allowed = {expected["before"][relative], expected["after"][relative]}
        if receipt and journal["state"] == "completed":
            allowed = {expected["after"][relative]}
        if current not in allowed:
            raise ContractError("Recovery conflict; later work preserved: " + relative)
    for relative, digest in expected["sources"].items():
        if relative not in expected["before"] and exists_hash(root, relative) != digest:
            raise ContractError("Recovery source conflict; later work preserved: " + relative)
    current_documents = set(protected_inventory(root))
    allowed_documents = (set(expected["document_inventory"]) | set(expected["after"])
                         | set(expected["sources"]))
    if current_documents - allowed_documents:
        raise ContractError("Recovery conflict: new documents were created after the transaction")
    if receipt and journal["state"] == "rolled-back":
        raise ContractError("Transaction already rolled back; a new explicit preview is required")
    side = "before" if rollback else "after"
    for relative, encoded in journal[side].items():
        write_one(root, relative, base64.b64decode(encoded) if encoded is not None else None)
    journal["state"] = "rolled-back" if rollback else "completed"
    _save_transaction(root, authorized_hash, journal)
    if source.startswith(LEGACY_TRANSACTION_PREFIX):
        path_at(root, source, missing=True).unlink(missing_ok=True)
    pending = path_at(root, PENDING, missing=True)
    if pending.exists():
        pending.unlink()
    return {"status": journal["state"], "receipt": TRANSACTION_STORE, "writes": sorted(journal[side])}
