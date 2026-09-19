"""Bounded, non-executing source access for project questions.

No consumer imports, subprocesses, caches, logs or writes belong in this module.
Hashes identify bytes observed now, not approved requirements or deployed code.
"""
from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

if str(__file__).startswith("\\\\?\\"):
    _bootstrap = Path(__file__).with_name("import_bootstrap.py")
    _namespace = {}
    exec(compile(_bootstrap.read_bytes(), str(_bootstrap), "exec"), _namespace)
    _namespace["ensure_import_path"](__file__)
    del _bootstrap, _namespace

from path_utils import filesystem_root, is_max_path_error, max_path_message


DOCUMENT_SUFFIXES = {".md", ".mdx", ".txt", ".rst"}
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".sql", ".cs",
                 ".go", ".rb", ".php", ".rs", ".c", ".h", ".cpp", ".vue",
                 ".json", ".yaml", ".yml", ".toml", ".xml", ".properties"}
SKIP_DIRS = {".git", ".svn", ".hg", "node_modules", "vendor", ".venv", "venv",
             "dist", "build", "coverage", "__pycache__", ".next", ".idea",
             ".pytest_cache", ".mypy_cache", ".ruff_cache", "test-results",
             "playwright-report"}
SECRET_NAME = re.compile(r"(?i)(^\.env(?:\.|$)|(?:^|[._-])(?:secrets?|credentials?|id_rsa|id_ed25519)(?:[._-]|$)|\.(?:pem|key|pfx|p12|keystore)$)")
SECRET_LINE = re.compile(
    r"(?i)(?:password|passwd|secret|api[_-]?key|access[_-]?token|authorization)\s*[\"']?\s*[:=]\s*\S+"
    r"|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,})\b"
    r"|://[^\s/:]+:[^\s/@]+@|\bBearer\s+\S+"
)
SECRET_MARKERS = ("password", "passwd", "secret", "api", "access", "authorization",
                  "ghp_", "gho_", "ghu_", "ghs_", "ghr_", "akia", "sk-", "://", "bearer", "private key")


class QueryError(ValueError):
    """A bounded query cannot safely proceed."""


@dataclass(frozen=True)
class Limits:
    max_entries: int = 50000
    max_documents: int = 1500
    max_file_bytes: int = 1024 * 1024
    max_total_bytes: int = 32 * 1024 * 1024
    max_code_files: int = 100
    max_code_bytes: int = 4 * 1024 * 1024
    max_depth: int = 12
    relation_depth: int = 3
    max_relations: int = 10000
    max_index_items: int = 200
    max_output_chars: int = 120000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(value) -> str:
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def is_link(path: Path) -> bool:
    # FILE_ATTRIBUTE_REPARSE_POINT also covers junctions on Python < 3.12.
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def is_root_git_metadata(root: Path, parent: Path, name: str) -> bool:
    """Exclude only the repository's own Git control entry from an inventory."""
    return parent == root and name.casefold() == ".git"


def lexical_root(root: Path) -> Path:
    try:
        root = filesystem_root(root)
        for part in [*reversed(root.parents), root]:
            if is_link(part):
                raise QueryError("La raíz atraviesa un enlace simbólico o junction.")
        if not root.is_dir():
            raise QueryError("La raíz del proyecto no es un directorio accesible.")
        return root
    except OSError as exc:
        if is_max_path_error(exc):
            raise QueryError(max_path_message(root)) from exc
        raise


def safe_path(root: Path, relative: str, *, allow_git: bool = False) -> Path:
    if (not relative or "\\" in relative or ":" in relative or
            PurePosixPath(relative).is_absolute() or
            any(p in {"", ".", ".."} for p in relative.split("/"))):
        raise QueryError("Se requiere una ruta relativa interna sin escapes.")
    # Keep intermediate paths as strings: each component still receives a fresh
    # lstat and nested-repository check, without constructing O(depth) Path objects.
    current = os.fspath(root)
    parts = relative.split("/")
    for index, part in enumerate(parts):
        if not allow_git and part.casefold() == ".git":
            raise QueryError("Los objetos Git no son fuentes de consulta.")
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except OSError as exc:
            if is_max_path_error(exc):
                raise QueryError(max_path_message(Path(current))) from exc
            raise
        if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400):
            raise QueryError("No se siguen enlaces simbólicos ni junctions.")
        if index < len(parts) - 1 and stat.S_ISDIR(info.st_mode) and os.path.lexists(os.path.join(current, ".git")):
            raise QueryError("No se amplía la consulta a un repositorio anidado.")
    # Every component is lexical, nonempty, non-parent and non-link. Resolving
    # both paths again adds O(depth) filesystem calls without another boundary.
    current = Path(current)
    if not current.is_relative_to(root):
        raise QueryError("La ruta queda fuera del proyecto.")
    return current


def redact(text: str) -> tuple[str, bool]:
    lowered = text.lower()
    if not any(marker in lowered for marker in SECRET_MARKERS):
        # splitlines/join would allocate one object per ordinary Markdown line.
        # Preserve its exact behavior, including Unicode separators, while
        # keeping the common LF-only path to a scan and optional final slice.
        if not re.search(r"[\r\v\f\x1c-\x1e\x85\u2028\u2029]", text):
            return text.removesuffix("\n"), False
        return "\n".join(text.splitlines()), False
    output, private, changed = [], False, False
    for line in text.splitlines():
        if "PRIVATE KEY-----" in line and re.search(r"-----BEGIN .*PRIVATE KEY-----", line):
            private = True
        hidden = private or bool(SECRET_LINE.search(line))
        output.append("[contenido sensible omitido]" if hidden else line)
        changed |= hidden
        if "PRIVATE KEY-----" in line and re.search(r"-----END .*PRIVATE KEY-----", line):
            private = False
    return "\n".join(output), changed


class SourceReader:
    def __init__(self, root: Path, limits: Limits | None = None):
        self.root = lexical_root(root)
        self.limits = limits or Limits()
        self._reset_read_state()

    def _reset_read_state(self):
        self.sources: dict[str, dict] = {}
        self._source_keys: dict[str, str] = {}
        self.exclusions: list[dict] = []
        self._excluded_keys: set[tuple[str, str]] = set()
        self.warnings: list[str] = []
        self.metrics = {"entries_listed": 0, "document_files_read": 0, "code_files_read": 0,
                        "bytes_read": 0, "code_bytes_read": 0, "revalidation_bytes": 0}

    def exclude(self, path: str, reason: str):
        key = (path, reason)
        if key in self._excluded_keys:
            return
        self._excluded_keys.add(key)
        item = {"path": path, "reason": reason}
        if len(self.exclusions) < self.limits.max_index_items:
            self.exclusions.append(item)
        elif "exclusion-index-truncated" not in self.warnings:
            self.warnings.append("exclusion-index-truncated")
        if reason not in {"generated-or-tooling", "unsupported-format"} and reason not in self.warnings:
            self.warnings.append(reason)

    def inventory(self, scope: str | None = None, *, code: bool = False) -> list[str]:
        start = self.root if scope is None else safe_path(self.root, scope)
        if start.is_file():
            return [start.relative_to(self.root).as_posix()]
        found: list[str] = []
        stack = [(start, 0)]
        count = 0
        while stack:
            folder, depth = stack.pop()
            relative = folder.relative_to(self.root).as_posix()
            if folder != self.root and is_link(folder):
                self.exclude(relative, "nested-repository-or-link")
                continue
            if depth > self.limits.max_depth:
                self.exclude(relative, "depth-limit")
                continue
            try:
                with os.scandir(folder) as entries:
                    # Bound enumeration itself, not only the resulting file list.
                    batch = []
                    for entry in entries:
                        count += 1
                        if count > self.limits.max_entries:
                            self.exclude(relative, "entry-limit")
                            self.metrics["entries_listed"] += count - 1
                            return sorted(found)
                        batch.append(entry)
                # Detect nested repositories in the already bounded directory
                # listing, before accepting any file or descending into it.
                if folder != self.root and any(e.name.casefold() == ".git" for e in batch):
                    self.exclude(relative, "nested-repository-or-link")
                    continue
                for entry in sorted(batch, key=lambda e: e.name):
                    rel = entry.name if relative == "." else relative + "/" + entry.name
                    # DirEntry carries Windows reparse metadata from directory
                    # enumeration. Avoid a redundant lstat for every entry;
                    # directory traversal and every content read/revalidation
                    # still perform their own fresh no-link checks.
                    entry_info = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(entry_info.st_mode) or bool(getattr(entry_info, "st_file_attributes", 0) & 0x400):
                        self.exclude(rel, "link-excluded")
                    elif is_root_git_metadata(self.root, folder, entry.name):
                        continue
                    elif SECRET_NAME.search(entry.name):
                        self.exclude(rel, "sensitive-path")
                    elif entry.is_dir(follow_symlinks=False):
                        if rel in {"docs/lks-sdd/00-control/history", "docs/lks-sdd/00-control/migrations"}:
                            continue  # Historical sources require an explicit historical query.
                        if entry.name.casefold() in SKIP_DIRS or entry.name.casefold() == ".lks-sdd":
                            continue
                        stack.append((Path(entry.path), depth + 1))
                    elif os.path.splitext(entry.name)[1].lower() in (CODE_SUFFIXES if code else DOCUMENT_SUFFIXES):
                        found.append(rel)
                    elif not code and os.path.splitext(entry.name)[1].lower() in {".pdf", ".docx", ".png", ".jpg"}:
                        self.exclude(rel, "unsupported-format")
            except OSError as exc:
                if is_max_path_error(exc):
                    raise QueryError(max_path_message(folder)) from exc
                self.exclude(relative, "unreadable-directory")
        self.metrics["entries_listed"] += count
        return sorted(found)

    def read(self, relative: str, kind: str = "document") -> dict | None:
        cached = self.lookup(relative)
        if cached:
            return cached
        if any(SECRET_NAME.search(p) for p in relative.split("/")):
            self.exclude(relative, "sensitive-path")
            return None
        suffix = PurePosixPath(relative).suffix.lower()
        if (kind == "document" and suffix not in DOCUMENT_SUFFIXES) or (kind == "code" and suffix not in CODE_SUFFIXES):
            self.exclude(relative, "unsupported-format")
            return None
        counter = "code_files_read" if kind == "code" else "document_files_read"
        maximum = self.limits.max_code_files if kind == "code" else self.limits.max_documents
        if self.metrics[counter] >= maximum:
            self.exclude(relative, "file-count-limit")
            return None
        try:
            path = safe_path(self.root, relative)
            info = path.stat()
            if not stat.S_ISREG(info.st_mode):
                raise QueryError("not-regular-file")
            size = info.st_size
            if size > self.limits.max_file_bytes:
                self.exclude(relative, "file-size-limit")
                return None
            if self.metrics["bytes_read"] + size > self.limits.max_total_bytes or (
                kind == "code" and self.metrics["code_bytes_read"] + size > self.limits.max_code_bytes
            ):
                self.exclude(relative, "byte-limit")
                return None
            # O_NOFOLLOW where supported; recheck identity before using the bytes.
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
            with os.fdopen(descriptor, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino, opened.st_size) != (info.st_dev, info.st_ino, info.st_size):
                    raise QueryError("source-changed-during-read")
                raw = stream.read(size)
                after = os.fstat(stream.fileno())
            # Charge attempted content reads, including invalid UTF-8/binary
            # files. Otherwise rejected files could bypass the byte/file budget.
            self.metrics[counter] += 1
            self.metrics["bytes_read"] += len(raw)
            if kind == "code":
                self.metrics["code_bytes_read"] += len(raw)
            if len(raw) > self.limits.max_file_bytes or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise QueryError("source-changed-during-read")
            decoded = raw.decode("utf-8-sig")
            if "\x00" in decoded:
                raise QueryError("binary-content")
            text, redacted = redact(decoded)
            if redacted:
                self.exclude(relative, "sensitive-content-redacted")
            source = {"path": relative, "sha256": digest(raw), "kind": kind, "text": text,
                      "line_count": text.count("\n") + int(bool(text) and not text.endswith("\n")), "redacted": redacted,
                      "authority": "mixed-or-unknown" if kind != "code" else "observation-only"}
            self.sources[relative] = source
            self._source_keys[os.path.normcase(relative)] = relative
            return source
        except (OSError, ValueError, UnicodeError):
            self.exclude(relative, "unreadable-or-unsafe-source")
            return None

    def lookup(self, relative: str) -> dict | None:
        key = self._source_keys.get(os.path.normcase(relative))
        return self.sources.get(key) if key is not None else None

    def read_documents(self, paths):
        """Bounded parallel reads with deterministic selection and budget accounting.

        Reserve a full maximum-sized file for each queued read before launching
        a batch. Near either budget use the original sequential reader. Workers
        share only the already checked root and immutable limits; every file
        still uses fresh safe_path, descriptor identity and content checks.
        """
        ordered, seen = [], set()
        for path in paths:
            key = os.path.normcase(path)
            if key not in seen:
                seen.add(key)
                ordered.append(path)
        if len(ordered) < 32:
            for path in ordered:
                self.read(path)
            return

        def isolated(path):
            reader = object.__new__(SourceReader)
            reader.root, reader.limits = self.root, self.limits
            reader._reset_read_state()
            reader.read(path)
            return reader

        def group(paths):
            return [isolated(path) for path in paths]

        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="lks-document-read") as executor:
            position = 0
            while position < len(ordered):
                available_files = self.limits.max_documents - self.metrics["document_files_read"]
                available_bytes = self.limits.max_total_bytes - self.metrics["bytes_read"]
                slots = min(32, available_files, available_bytes // max(1, self.limits.max_file_bytes))
                if slots < 4:
                    self.read(ordered[position])
                    position += 1
                    continue
                pending = ordered[position:position + slots]
                position += len(pending)
                pending = [p for p in pending if not self.lookup(p)]
                groups = [pending[i:i + 8] for i in range(0, len(pending), 8)]
                readers = (reader for group_result in executor.map(group, groups) for reader in group_result)
                for reader in readers:
                    self.sources.update(reader.sources)
                    self._source_keys.update(reader._source_keys)
                    for key, value in reader.metrics.items():
                        self.metrics[key] += value
                    for item in reader.exclusions:
                        self.exclude(item["path"], item["reason"])
                    for warning in reader.warnings:
                        if warning not in self.warnings:
                            self.warnings.append(warning)

    def revision(self) -> dict:
        """Read local Git identity without running Git, hooks or fsmonitor.

        External gitdirs (including worktrees) are intentionally not followed.
        Source hashes remain available when revision identity is unavailable.
        """
        result = {"revision": None, "branch": None, "working_tree": "not-compared"}
        try:
            head = safe_path(self.root, ".git/HEAD", allow_git=True)
            if head.stat().st_size > 4096:
                return result
            value = head.read_text(encoding="utf-8").strip()
            if value.startswith("ref: "):
                ref = value[5:]
                result["branch"] = ref
                try:
                    path = safe_path(self.root, ".git/" + ref, allow_git=True)
                    value = path.read_text(encoding="ascii").strip() if path.stat().st_size < 4096 else ""
                except OSError:
                    packed = safe_path(self.root, ".git/packed-refs", allow_git=True)
                    if packed.stat().st_size > self.limits.max_file_bytes:
                        return result
                    value = next((line.split()[0] for line in packed.read_text(encoding="ascii").splitlines()
                                  if line.endswith(" " + ref)), "")
            if re.fullmatch(r"[a-f0-9]{40,64}", value):
                result["revision"] = value
        except (OSError, ValueError, UnicodeError):
            pass
        return result

    def revalidate(self) -> list[str]:
        def check(item):
            relative, source = item
            try:
                path = safe_path(self.root, relative)
                info = path.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_size > self.limits.max_file_bytes:
                    return relative, 0
                descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
                with os.fdopen(descriptor, "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if (opened.st_dev, opened.st_ino, opened.st_size) != (info.st_dev, info.st_ino, info.st_size):
                        return relative, 0
                    raw = stream.read(info.st_size)
                    after = os.fstat(stream.fileno())
                if digest(raw) != source["sha256"] or (opened.st_size, opened.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    return relative, len(raw)
                return None, len(raw)
            except (OSError, ValueError):
                return relative, 0
        changed = []
        items = tuple(self.sources.items())
        # Parallelize only independent verification reads. Selection, budgets,
        # cache mutation and result order stay single-threaded/deterministic.
        # No process or consumer code is launched, and no check is removed.
        if len(items) < 32:
            results = list(map(check, items))
        else:
            with ThreadPoolExecutor(max_workers=4, thread_name_prefix="lks-query-read") as executor:
                groups = [items[i:i + 16] for i in range(0, len(items), 16)]
                results = [result for group in executor.map(lambda batch: [check(item) for item in batch], groups)
                           for result in group]
        for relative, size in results:
            self.metrics["revalidation_bytes"] += size
            if relative is not None:
                changed.append(relative)
        return changed


def check_query_runtime(root: Path, plugin_root: Path) -> None:
    """Check the complete pinned runtime afresh without executing consumer code."""
    root = lexical_root(root)
    lock = root / ".lks-sdd/distribution-lock.json"
    if not os.path.lexists(lock) and not os.path.lexists(root / ".lks-sdd"):
        return
    if os.path.lexists(root / ".lks-sdd") and is_link(root / ".lks-sdd"):
        raise QueryError("Índice/runtime mediante enlace: consulta bloqueada.")
    if not os.path.lexists(lock):
        return
    try:
        from query_runtime import validate
        validate(root, plugin_root)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, QueryError):
            raise
        raise QueryError("No se puede comprobar de forma segura el runtime fijado.") from exc
