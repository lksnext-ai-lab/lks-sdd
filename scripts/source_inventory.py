"""Fresh bounded enumeration and identity-checked reads, without persistent trust caches."""
import os
from pathlib import Path
import stat

from v2_contract import ContractError, path_at, relative_parts, sha
from path_utils import filesystem_root

# Legacy trees retain every physical path, even when their content is repeated.
# Bound scan work separately from unique migration payload bytes.
MIGRATION_PATH_LIMIT = 250000
MIGRATION_SCAN_BYTES = 16 * 1024 * 1024 * 1024
MIGRATION_UNIQUE_BYTES = 2 * 1024 * 1024 * 1024
MIGRATION_CATALOG_BYTES = 64 * 1024 * 1024


def logical(path):
    value = str(path)
    if value.startswith("\\\\?\\UNC\\"): value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"): value = value[4:]
    return Path(value)


def signature(info):
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns


def linked(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def documents(root, *, excluded=(), limit=100000, byte_limit=None):
    root = Path(root)
    base = path_at(root, "docs/lks-sdd", missing=True)
    files, stack, total = {}, [(base, base.lstat())] if base.exists() else [], 0
    excluded = set(excluded)
    while stack:
        directory, observed_directory = stack.pop()
        if linked(directory.lstat()) or signature(directory.lstat())[:3] != signature(observed_directory)[:3]:
            raise ContractError("Document directory changed during enumeration")
        with os.scandir(directory) as entries:
            names = set()
            for entry in entries:
                names.add(entry.name)
                path = filesystem_root(Path(entry.path))
                relative = "docs/lks-sdd/" + logical(path).relative_to(logical(base)).as_posix()
                relative_parts(relative)
                # Windows DirEntry.stat may report st_ino=0; lstat supplies the
                # same file identity used by fstat/current checks on all platforms.
                info = path.lstat()
                if linked(info): raise ContractError("Link/junction rejected: " + relative)
                if stat.S_ISDIR(info.st_mode):
                    if (path/".git").exists(): raise ContractError("Nested repository rejected: " + relative)
                    if relative not in excluded: stack.append((path, info))
                elif stat.S_ISREG(info.st_mode):
                    total += info.st_size
                    files[relative] = (path, info)
                    if len(files) > limit or (byte_limit is not None and total > byte_limit):
                        raise ContractError("Document source inventory exceeds resource budget")
                else: raise ContractError("Non-regular documentary source: " + relative)
        if signature(directory.lstat())[:3] != signature(observed_directory)[:3]:
            raise ContractError("Document directory changed during enumeration")
        with os.scandir(directory) as current:
            if names != {entry.name for entry in current}: raise ContractError("Document membership changed during enumeration")
    return files


def read(entry, *, limit=64*1024*1024):
    path, observed = entry
    current = path.lstat()
    if linked(current) or not stat.S_ISREG(current.st_mode) or signature(current) != signature(observed) or current.st_size > limit:
        raise ContractError("Source changed or exceeds read budget: " + str(path))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if signature(opened) != signature(observed): raise ContractError("Source identity changed before reading")
        raw = stream.read(observed.st_size + 1)
        after = os.fstat(stream.fileno())
    if len(raw) != observed.st_size or signature(after) != signature(observed): raise ContractError("Source changed during reading")
    return raw


def digest(entry): return sha(read(entry))
