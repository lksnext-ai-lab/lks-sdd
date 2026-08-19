"""Shared read-only primitives for the LKS-SDD adoption workflow."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

REPORT_KIND = "lks-sdd-adoption-inventory"
DECISION_KIND = "lks-sdd-adoption-decision"
REPORT_VERSION = "1.0"
OUTPUT_PREFIXES = (".lks-sdd", "docs/lks-sdd")
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    "target",
}
SENSITIVE_NAMES = {
    ".env": "environment-file",
    ".npmrc": "package-credential-config",
    ".pypirc": "package-credential-config",
    "id_rsa": "private-key",
    "id_ed25519": "private-key",
    "credentials": "credential-store",
}
SENSITIVE_SUFFIXES = {
    ".pem": "certificate-or-key",
    ".key": "private-key",
    ".p12": "certificate-store",
    ".pfx": "certificate-store",
    ".jks": "certificate-store",
    ".keystore": "certificate-store",
}
BINARY_SUFFIXES = {
    ".7z",
    ".avi",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".doc",
    ".docx",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".o",
    ".obj",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".tar",
    ".webp",
    ".xls",
    ".xlsx",
    ".zip",
}
MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "pom.xml",
    "build.gradle",
    "cargo.toml",
    "go.mod",
    "composer.json",
    "dockerfile",
    "compose.yaml",
    "docker-compose.yml",
}
TEST_MARKERS = {"test", "tests", "spec", "specs", "__tests__"}


class AdoptionError(Exception):
    """Expected, actionable adoption failure."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return sha256_bytes(encoded)


def safe_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise AdoptionError(f"La raíz no existe o no es una carpeta: {root}")
    return root


def is_link_like(path: Path) -> bool:
    """Return whether a path is a symlink or a Windows directory junction."""
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def safe_scope(root: Path, requested: str) -> tuple[Path, str]:
    unresolved = root / requested
    current = unresolved
    while current != root:
        if is_link_like(current):
            raise AdoptionError(
                "El alcance debe ser una carpeta real y no un enlace simbólico o junction."
            )
        if current.parent == current:
            break
        current = current.parent
    candidate = unresolved.resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise AdoptionError(
            "El alcance debe permanecer dentro de la raíz confirmada."
        ) from exc
    if not candidate.is_dir():
        raise AdoptionError(
            "El alcance debe ser una carpeta real y no un enlace simbólico o junction."
        )
    return candidate, relative.as_posix() if relative.parts else "."


def is_generated_output(relative: str) -> bool:
    normalized = relative.strip("/")
    return any(
        normalized == prefix or normalized.startswith(prefix + "/")
        for prefix in OUTPUT_PREFIXES
    )


def safe_exclusions(root: Path, values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        candidate = (root / value).resolve()
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise AdoptionError(f"Exclusión fuera de la raíz: {value}") from exc
        if relative == ".":
            raise AdoptionError("No se puede excluir toda la raíz confirmada.")
        normalized.append(relative)
    return sorted(set(normalized))


def is_excluded(relative: str, exclusions: list[str]) -> bool:
    normalized = relative.strip("/")
    return any(
        normalized == prefix or normalized.startswith(prefix + "/")
        for prefix in exclusions
    )


def sensitive_category(path: Path) -> str | None:
    lowered = path.name.casefold()
    if lowered in SENSITIVE_NAMES:
        return SENSITIVE_NAMES[lowered]
    if lowered.startswith(".env."):
        return "environment-file"
    return SENSITIVE_SUFFIXES.get(path.suffix.casefold())


def file_category(relative: Path) -> str:
    lowered_parts = {part.casefold() for part in relative.parts}
    lowered_name = relative.name.casefold()
    if lowered_name in MANIFEST_NAMES:
        return "manifest"
    if (
        lowered_parts.intersection(TEST_MARKERS)
        or ".test." in lowered_name
        or ".spec." in lowered_name
    ):
        return "test"
    if relative.suffix.casefold() in {".md", ".rst", ".adoc"}:
        return "documentation"
    if relative.suffix.casefold() in {
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".xml",
    }:
        return "configuration"
    if relative.suffix.casefold() in {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".kt",
        ".vue",
        ".svelte",
    }:
        return "source"
    if relative.suffix.casefold() in BINARY_SUFFIXES:
        return "binary-excluded"
    return "other"


def inventory(
    root: Path, scope: Path, max_files: int, exclusions: list[str]
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    sensitive: list[dict[str, str]] = []
    sensitive_state: list[dict[str, Any]] = []
    symlinks_excluded: list[str] = []
    submodules_excluded: list[str] = []
    counts: dict[str, int] = {}
    truncated = False
    for current, dirs, names in os.walk(scope, followlinks=False):
        current_path = Path(current)
        safe_dirs: list[str] = []
        for name in sorted(dirs):
            candidate = current_path / name
            relative = candidate.relative_to(root).as_posix()
            if (
                name in IGNORED_DIRS
                or is_generated_output(relative)
                or is_excluded(relative, exclusions)
            ):
                continue
            if is_link_like(candidate):
                symlinks_excluded.append(relative)
                continue
            if (candidate / ".git").is_file():
                submodules_excluded.append(relative)
                continue
            safe_dirs.append(name)
        dirs[:] = safe_dirs
        for name in sorted(names):
            path = current_path / name
            relative_path = path.relative_to(root)
            relative = relative_path.as_posix()
            if is_generated_output(relative) or is_excluded(relative, exclusions):
                continue
            if is_link_like(path):
                symlinks_excluded.append(relative)
                continue
            if len(files) + len(sensitive) >= max_files:
                truncated = True
                break
            category = sensitive_category(path)
            try:
                stat = path.stat()
            except OSError as exc:
                files.append(
                    {
                        "path": relative,
                        "category": "unreadable",
                        "error": type(exc).__name__,
                    }
                )
                counts["unreadable"] = counts.get("unreadable", 0) + 1
                continue
            if category:
                sensitive.append({"path": relative, "category": category})
                sensitive_state.append(
                    {
                        "path": relative,
                        "category": category,
                        "size": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns,
                    }
                )
                counts["sensitive-excluded"] = counts.get("sensitive-excluded", 0) + 1
                continue
            category = file_category(relative_path)
            entry: dict[str, Any] = {
                "path": relative,
                "category": category,
                "size": stat.st_size,
            }
            if category == "binary-excluded":
                entry["content_inspected"] = False
            else:
                try:
                    entry["sha256"] = sha256_file(path)
                    entry["content_inspected"] = True
                except OSError as exc:
                    entry.update(
                        {
                            "category": "unreadable",
                            "error": type(exc).__name__,
                            "content_inspected": False,
                        }
                    )
                    category = "unreadable"
            files.append(entry)
            counts[category] = counts.get(category, 0) + 1
        if truncated:
            break
    fingerprint_payload = {
        "files": files,
        "sensitive": sensitive_state,
        "symlinks": symlinks_excluded,
        "submodules": submodules_excluded,
        "truncated": truncated,
    }
    return {
        "files": files,
        "sensitive_indicators": sensitive,
        "symlinks_excluded": symlinks_excluded,
        "submodules_excluded": submodules_excluded,
        "counts": dict(sorted(counts.items())),
        "truncated": truncated,
        "fingerprint": stable_hash(fingerprint_payload),
    }


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )


def git_snapshot(root: Path) -> dict[str, Any]:
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "type": "none",
            "origin": "none",
            "revision": None,
            "branch": None,
            "dirty": False,
            "changed_count": 0,
            "status_digest": None,
        }
    revision_result = _git(root, "rev-parse", "HEAD")
    branch_result = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    status_result = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status_result.returncode != 0:
        raise AdoptionError(
            "No se pudo obtener un estado Git saneado y de solo lectura."
        )
    relevant_lines = []
    for line in status_result.stdout.splitlines():
        path_part = line[3:] if len(line) > 3 else ""
        destination = path_part.split(" -> ")[-1].strip('"')
        if not is_generated_output(destination.replace("\\", "/")):
            relevant_lines.append(line)
    origin_result = _git(root, "remote", "get-url", "origin")
    remote = (
        origin_result.stdout.strip().casefold() if origin_result.returncode == 0 else ""
    )
    origin = (
        "github"
        if "github" in remote
        else "gitlab"
        if "gitlab" in remote
        else "other"
        if remote
        else "none"
    )
    return {
        "type": "git",
        "origin": origin,
        "revision": revision_result.stdout.strip()
        if revision_result.returncode == 0
        else None,
        "branch": branch_result.stdout.strip()
        if branch_result.returncode == 0
        else "detached",
        "dirty": bool(relevant_lines),
        "changed_count": len(relevant_lines),
        "status_digest": stable_hash(relevant_lines),
    }


def repository_snapshot(
    root: Path, scope: Path, max_files: int, exclusions: list[str] | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    scanned = inventory(root, scope, max_files, exclusions or [])
    git = git_snapshot(root)
    state = {"inventory_fingerprint": scanned["fingerprint"], "git": git}
    return {**state, "fingerprint": stable_hash(state)}, scanned


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdoptionError(f"No se puede leer {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdoptionError(f"{label} debe ser un objeto JSON.")
    return value


def report_scope(root: Path, report: dict[str, Any]) -> tuple[Path, int, list[str]]:
    preflight = report.get("preflight", {})
    if not isinstance(preflight, dict):
        raise AdoptionError("El informe no conserva un preflight válido.")
    scope, _ = safe_scope(root, str(preflight.get("scope", ".")))
    max_files = preflight.get("max_files")
    if not isinstance(max_files, int) or max_files < 1:
        raise AdoptionError("El informe no conserva un límite de inventario válido.")
    raw_exclusions = preflight.get("exclusions", [])
    if not isinstance(raw_exclusions, list) or not all(
        isinstance(item, str) for item in raw_exclusions
    ):
        raise AdoptionError("El informe no conserva exclusiones válidas.")
    exclusions = safe_exclusions(root, raw_exclusions)
    return scope, max_files, exclusions


def compare_baseline(root: Path, report: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    scope, max_files, exclusions = report_scope(root, report)
    current, _ = repository_snapshot(root, scope, max_files, exclusions)
    expected = report.get("baseline", {})
    return current == expected, current
