"""Bounded, fresh integrity checks for queries; no persistent trust cache.

Enumerate once, hash every runtime/adapter file in parallel, then recheck the
inventory. This preserves the pinned-runtime contract without repeated O(depth)
path resolution for each already-enumerated file. No consumer code is executed.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import stat

from dual_distribution import BEGIN, END, SKILLS, digest, filesystem_root, json_bytes, safe_name
from path_utils import same_filesystem_path
from query_sources import QueryError, SECRET_NAME, safe_path


def _inventory(runtime):
    found, stack, count = {}, [runtime], 0
    while stack:
        with os.scandir(stack.pop()) as entries:
            for entry in entries:
                count += 1
                info = entry.stat(follow_symlinks=False)
                if count > 30000 or stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400 or entry.name.casefold() == ".git":
                    raise QueryError("Inventario de runtime inseguro o excesivo.")
                if stat.S_ISDIR(info.st_mode):
                    stack.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    path = Path(entry.path)
                    if "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                        found[path.relative_to(runtime).as_posix()] = (path, info)
                else:
                    raise QueryError("Runtime contiene una fuente no regular.")
    return found


def _read(job):
    name, path, observed, expected = job
    current = path.lstat()
    if (stat.S_ISLNK(current.st_mode) or getattr(current, "st_file_attributes", 0) & 0x400 or
            not stat.S_ISREG(current.st_mode) or (current.st_size, current.st_mtime_ns) != (observed.st_size, observed.st_mtime_ns)):
        raise QueryError("Runtime cambió durante la consulta: " + name)
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns):
            raise QueryError("La identidad del archivo cambió antes de leer.")
        # The size was bounded before opening. A maximum-sized read for every
        # tiny file would allocate tens of GiB per query on some Python builds.
        # Read one extra byte to reject growth without that allocation cost.
        raw = stream.read(current.st_size + 1)
        after = os.fstat(stream.fileno())
    if len(raw) != current.st_size or after.st_mtime_ns != current.st_mtime_ns:
        raise QueryError("Runtime cambió durante lectura.")
    content = raw
    if name in {"AGENTS.md", ".github/copilot-instructions.md"}:
        text = raw.decode("utf-8").replace("\r\n", "\n")
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            raise QueryError("Bloque gestionado ambiguo: " + name)
        content = (BEGIN + text.split(BEGIN)[1].split(END)[0] + END + "\n").encode()
    if digest(content) != expected:
        raise QueryError("Integridad del runtime fijado inválida; no se usa el global: " + name)
    return name, raw if name.endswith("/.codex-plugin/plugin.json") else None


def validate(root, plugin_root):
    lock_path = safe_path(root, ".lks-sdd/distribution-lock.json")
    if lock_path.stat().st_size > 8 * 1024 * 1024:
        raise QueryError("Lock de runtime demasiado grande.")
    original = lock_path.read_bytes()
    lock = json.loads(original)
    if not isinstance(lock, dict) or lock.get("schema_version") != "1.0" or lock.get("project_schema") not in {"1.5", "2.0"}:
        raise QueryError("Contrato de distribución no soportado.")
    runtime_name = safe_name(lock["runtime"])
    if not runtime_name.startswith(".lks-sdd/runtime/"):
        raise QueryError("Runtime fuera de su ubicación contractual.")
    runtime = safe_path(root, runtime_name)
    if not same_filesystem_path(runtime, plugin_root):
        raise QueryError("Utilice la CLI exacta del runtime fijado: " + runtime_name + "/scripts/lks_sdd.py")
    mode = lock.get("entrypoints", "project")
    if mode not in {"project", "plugin"}:
        raise QueryError("Modo de entrypoints inválido.")
    if mode == "plugin" and any((root / f".github/skills/lks-sdd-{s}/SKILL.md").exists() for s in SKILLS):
        raise QueryError("Skills duplicadas entre plugin y proyecto.")
    files, managed = lock["runtime_files"], lock["managed_files"]
    if not isinstance(files, dict) or not files or not isinstance(managed, dict) or len(files) + len(managed) > 20000:
        raise QueryError("Inventario de runtime inválido.")
    for name, expected in {**files, **managed}.items():
        safe_name(name)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise QueryError("Hash de runtime inválido.")
        parts = name.split("/")
        template = name in files and re.fullmatch(r"profiles/[A-Z0-9-]+/scaffold/(?:[A-Za-z0-9_-]+/)*\.env\.example", name)
        observation = name in files and re.fullmatch(r"profiles/[A-Z0-9-]+/certification-details/[0-9a-f]{64}/GATE-LOCAL-CREDENTIALS\.json", name)
        if any(SECRET_NAME.search(p) for p in parts[:-1]) or SECRET_NAME.search(parts[-1]) and not (template or observation):
            raise QueryError("El lock no puede convertir un secreto en fuente de consulta.")
    allowed_managed = {"AGENTS.md", ".github/copilot-instructions.md", ".github/lks-sdd-host.md",
                       ".github/.gitattributes", ".lks-sdd/.gitattributes"}
    allowed_managed.update(f".github/skills/lks-sdd-{s}/SKILL.md" for s in SKILLS)
    if set(managed) - allowed_managed:
        raise QueryError("El lock no puede incorporar código del consumidor como adaptador.")
    observed = _inventory(runtime)
    if set(observed) != set(files):
        raise QueryError("Inventario de runtime incompleto o con archivos inesperados.")
    jobs = [(runtime_name + "/" + name, path, info, files[name]) for name, (path, info) in observed.items()]
    for name, expected in managed.items():
        path = safe_path(root, name)
        jobs.append((name, path, path.stat(), expected))
    if any(not stat.S_ISREG(info.st_mode) or info.st_size > 32 * 1024 * 1024 for _, _, info, _ in jobs) or sum(i.st_size for _, _, i, _ in jobs) > 512 * 1024 * 1024:
        raise QueryError("Archivo de runtime inválido o excesivo.")
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="lks-runtime-read") as executor:
        groups = [jobs[i:i + 16] for i in range(0, len(jobs), 16)]
        results = dict(result for batch in executor.map(lambda group: [_read(job) for job in group], groups)
                       for result in batch)
    if digest(json_bytes(files)) != lock.get("runtime_digest"):
        raise QueryError("Digest del inventario de runtime incoherente.")
    manifest = json.loads(results[runtime_name + "/.codex-plugin/plugin.json"])
    if not isinstance(manifest, dict) or manifest.get("version") != lock.get("version"):
        raise QueryError("Versión del runtime incoherente.")
    index = root / ".lks-sdd/project.json"
    if os.path.lexists(index):
        index = safe_path(root, ".lks-sdd/project.json")
        if index.stat().st_size > 4 * 1024 * 1024:
            raise QueryError("Índice de proyecto excesivo.")
        project = json.loads(index.read_bytes())
        if not isinstance(project, dict) or project.get("schema_version") != lock["project_schema"]:
            raise QueryError("Schema del proyecto y runtime fijado no coinciden.")
    renewed = _inventory(runtime)
    signature = lambda entries: {p: (s.st_size, s.st_mtime_ns) for p, (_, s) in entries.items()}
    if signature(renewed) != signature(observed) or safe_path(root, ".lks-sdd/distribution-lock.json").read_bytes() != original:
        raise QueryError("Inventario/runtime cambió durante la comprobación.")
