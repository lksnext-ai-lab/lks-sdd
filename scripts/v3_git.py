"""Bounded Git observation, never shell evaluation or automatic publication."""
import os
from pathlib import Path
import subprocess
import time
from contextlib import contextmanager
from contextvars import ContextVar

from v3_contract import ContractError, DOCS, fingerprint, now, path_at, read_bytes, sha
from v2_contract import contract_input_allowed
from capacity import require, limit

_OBSERVATION = ContextVar("lks_git_observation", default=None)
_REUSABLE = {("rev-parse", "--show-toplevel"), ("symbolic-ref", "--short", "HEAD"),
             ("rev-parse", "--verify", "HEAD"), ("ls-files", "-z", "--cached", "--others", "--exclude-standard")}
CODE_PATH_LIMIT = 20000
RAW_PATH_LIMIT = 200000
GIT_STDOUT_LIMIT = 16 * 1024 * 1024
GIT_STDERR_LIMIT = 64 * 1024
GIT_INVENTORY_TIMEOUT = 60


def _pipe_reader():
    """Only read available bytes, including on Python 3.11 Windows pipes."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        import msvcrt
        peek = ctypes.WinDLL("kernel32", use_last_error=True).PeekNamedPipe
        peek.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                         ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        peek.restype = wintypes.BOOL

        def read(stream, limit):
            available = wintypes.DWORD()
            if not peek(msvcrt.get_osfhandle(stream.fileno()), None, 0, None,
                        ctypes.byref(available), None):
                error = ctypes.get_last_error()
                if error == 109: return b""  # ERROR_BROKEN_PIPE: all writers closed.
                raise ctypes.WinError(error)
            # These handles have one reader, with no pending read on another thread.
            return stream.read(min(limit, available.value)) if available.value else None
    else:
        import select

        def read(stream, limit):
            return stream.read(limit) if select.select([stream], [], [], 0)[0] else None
    return read


def _bounded_ls_files(command, **options):
    """Bound both pipes while reading; never return a partial Git observation."""
    read_ready = _pipe_reader()
    deadline = time.monotonic() + limit("git_seconds", GIT_INVENTORY_TIMEOUT)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               bufsize=0, **options)
    buffers = [bytearray(), bytearray()]
    streams = {0: process.stdout, 1: process.stderr}
    limits = [limit("git_stdout_bytes", GIT_STDOUT_LIMIT), GIT_STDERR_LIMIT]
    records = 0
    try:
        while streams:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(command, GIT_INVENTORY_TIMEOUT)
            progressed = False
            for index, stream in list(streams.items()):
                chunk = read_ready(stream, min(65536, limits[index] + 1 - len(buffers[index])))
                if chunk is None: continue
                progressed = True
                if not chunk:
                    stream.close(); del streams[index]
                    continue
                buffers[index].extend(chunk)
                if len(buffers[index]) > limits[index]:
                    if index != 0: raise ContractError("Error Git excesivo")
                    limits[0] = require("git_stdout_bytes", len(buffers[0]), GIT_STDOUT_LIMIT, "Salida Git excesiva")
                if index == 0:
                    records += chunk.count(b"\0")
                    if records > RAW_PATH_LIMIT:
                        require("git_paths", records, RAW_PATH_LIMIT, "Enumeración Git demasiado amplia")
            if not progressed:
                time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        process.wait(timeout=max(0, deadline - time.monotonic()))
        return subprocess.CompletedProcess(command, process.returncode,
                                           bytes(buffers[0]), bytes(buffers[1]))
    finally:
        process.stdout.close(); process.stderr.close()
        if process.poll() is None:
            try: process.kill()
            except ProcessLookupError: pass
        process.wait(timeout=1)


@contextmanager
def observation_evaluation(root):
    """Read-only preparation only; physical guards must run after this exits."""
    from v3_evaluation import _owner
    state = {"root": Path(root).resolve(), "owner": _owner(), "cache": {}, "bytes": 0}
    token = _OBSERVATION.set(state)
    try:
        yield
    finally:
        state["cache"].clear(); state["owner"] = None
        _OBSERVATION.reset(token)


def _invocation(root, args):
    """Preserve Git discovery/prefix semantics without a legacy long process cwd."""
    from path_utils import filesystem_root, short_existing_path, owned_by_current_user
    root = filesystem_root(root)
    logical = str(root)
    if logical.startswith("\\\\?\\UNC\\"): logical = "\\\\" + logical[8:]
    elif logical.startswith("\\\\?\\"): logical = logical[4:]
    if os.name != "nt" or len(logical) < 248:
        return ["git", "-C", str(root), *args], None, None, None

    routing = ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
               "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_CONFIG")
    if any(os.environ.get(name) for name in routing):
        raise ContractError("Long Windows Git cannot reinterpret repository-routing environment variables; use a clean invocation or a shorter root")
    for name in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        value = os.environ.get(name)
        if value and value.lower()!=os.devnull.lower() and not Path(value).is_absolute():
            raise ContractError("Long Windows Git cannot reinterpret relative configuration environment paths")
    checkout = root
    while not (checkout/".git").exists():
        if checkout.parent == checkout:
            raise ContractError("Git repository not found for long Windows path")
        checkout = checkout.parent
    marker = checkout/".git"
    if marker.is_dir(): git_dir = marker
    else:
        if marker.is_symlink(): raise ContractError("Invalid Git directory pointer: linked file")
        with marker.open("rb") as stream: raw = stream.read(64*1024+1)
        if len(raw)>64*1024: raise ContractError("Invalid Git directory pointer: excessive size")
        if not raw.startswith(b"gitdir: "): raise ContractError("Invalid Git directory pointer")
        target = raw[8:].decode("utf-8").rstrip(" \t\r\n\v\f")
        if not target or "\n" in target or "\x00" in target: raise ContractError("Invalid Git directory pointer")
        git_dir = filesystem_root((checkout/target).resolve())
        if not git_dir.is_dir(): raise ContractError("Git directory pointer is unavailable")
    try:
        directory = short_existing_path(git_dir); tree = short_existing_path(checkout)
    except OSError as exc:
        raise ContractError("Git needs an existing Windows short alias for this long checkout; use a supported volume or a shorter root: " + str(exc)) from exc
    if not owned_by_current_user([checkout, marker, git_dir]):
        raise ContractError("Git ownership could not be verified for the long Windows checkout; use a trusted shorter root")
    prefix = root.relative_to(checkout).as_posix()
    prefix = "" if prefix == "." else prefix + "/"
    forwarded = list(args)
    if prefix and args and args[0] == "ls-files": forwarded += ["--", prefix]
    command = ["git", "-c", "core.longpaths=true", "--git-dir="+str(directory), "--work-tree="+str(tree), *forwarded]
    cwd = Path(tree.anchor)
    # Git's 8.3 spelling changes gitdir-conditional matching. Refuse that case,
    # rather than silently omitting configuration or promoting local settings.
    from v3_evaluation import count
    count("git_commands")
    config = subprocess.run([*command[:5], "config", "--includes", "--null", "--list"],
                            cwd=cwd, capture_output=True, timeout=60)
    if len(config.stdout)>16*1024*1024: raise ContractError("Git configuration output exceeded the observation bound")
    if config.returncode not in {0, 1}:
        raise ContractError("Git configuration could not be checked for this long Windows checkout: " + config.stderr.decode("utf-8",errors="replace")[:800])
    settings = [row.partition(b"\n")[::2] for row in config.stdout.split(b"\x00") if row]
    if any(key.lower().startswith(b"includeif.gitdir") for key,value in settings):
        raise ContractError("Long Windows Git paths cannot preserve gitdir-conditional configuration through a short alias; use a shorter checkout root")
    bare = [value for key,value in settings if key.lower()==b"core.bare"]
    if bare and bare[-1].lower() not in {b"false", b"no", b"off", b"0"}:
        raise ContractError("Long Windows Git cannot turn a bare repository into a working checkout")
    configured_tree = [value for key,value in settings if key.lower()==b"core.worktree"]
    if configured_tree:
        from path_utils import same_filesystem_path
        value = configured_tree[-1].decode("utf-8")
        if value.startswith("~") or not same_filesystem_path((git_dir/value).resolve(), checkout):
            raise ContractError("Git core.worktree does not identify this long Windows checkout")
    for name in (b"core.excludesfile", b"core.attributesfile", b"core.hookspath"):
        values = [value for key,value in settings if key.lower()==name]
        if values:
            value = values[-1].decode("utf-8")
            if value and not value.startswith("~") and not Path(value).is_absolute():
                absolute = str((checkout/value).resolve())
                if absolute.startswith("\\\\?\\UNC\\"): absolute = "\\\\"+absolute[8:]
                elif absolute.startswith("\\\\?\\"): absolute = absolute[4:]
                command[5:5] = ["-c",name.decode("ascii")+"="+absolute]
    if args and args[0]=="fetch":
        remote = args[-1]
        urls = [value.decode("utf-8") for key,value in settings if key==("remote."+remote+".url").encode("utf-8")]
        for url in urls or [remote]:
            if (":" not in url and not Path(url).is_absolute()) or (Path(url).drive and not Path(url).is_absolute()):
                raise ContractError("Long Windows Git fetch needs an absolute configured remote URL; relative URLs require a shorter checkout root")
    return command, cwd, prefix, checkout


def git(root, *args, optional=False):
    from v3_evaluation import count, _owner
    state = _OBSERVATION.get()
    reusable = state is not None and args in _REUSABLE and state["owner"] == _owner() and Path(root).resolve() == state["root"]
    if reusable and args in state["cache"]:
        count("git_observation_reuses")
        return state["cache"][args]
    try:
        command, cwd, prefix, checkout = _invocation(root, args)
        options = {"cwd":cwd} if cwd is not None else {}
        count("git_commands")
        if args and args[0] == "ls-files":
            result = _bounded_ls_files(command, **options)
        else:
            result = subprocess.run(command, capture_output=True,
                                    timeout=limit("git_seconds", GIT_INVENTORY_TIMEOUT), **options)
    except subprocess.TimeoutExpired as exc:
        from capacity import ACTIVE
        if ACTIVE.get() is not None:
            require("git_seconds", limit("git_seconds", GIT_INVENTORY_TIMEOUT) + 1,
                    GIT_INVENTORY_TIMEOUT, "Git excede el tiempo ordinario de observación")
        raise ContractError("Git no completó la observación dentro de 60 s") from exc
    if result.returncode and not optional:
        raise ContractError("Git no pudo completar la observación: " + result.stderr.decode("utf-8", errors="replace")[:800])
    require("git_stdout_bytes", len(result.stdout), 16 * 1024 * 1024, "Salida Git excesiva; delimite el ámbito")
    if result.returncode: return None
    if args and args[0] == "ls-files" and "-z" in args and result.stdout and not result.stdout.endswith(b"\0"):
        raise ContractError("Inventario Git incompleto")
    if checkout is not None and args == ("rev-parse", "--show-toplevel"):
        logical = str(checkout)
        if logical.startswith("\\\\?\\UNC\\"): logical = "\\\\"+logical[8:]
        elif logical.startswith("\\\\?\\"): logical = logical[4:]
        return (logical.replace("\\", "/")+"\n").encode("utf-8")
    if prefix and args and args[0] == "ls-files":
        raw_prefix = prefix.encode("utf-8")
        value = b"".join(p[len(raw_prefix):]+b"\x00" for p in result.stdout.split(b"\x00") if p.startswith(raw_prefix))
    else: value = result.stdout
    if reusable and state["bytes"] + len(value) <= 8*1024*1024:
        state["cache"][args] = value; state["bytes"] += len(value)
    return value


def reference(value):
    if not isinstance(value, str) or not value or value.startswith("-") or any(c in value for c in "\n\r\x00:"):
        raise ContractError("Referencia Git no válida")
    return value


def observe(root, *, refs=(), remote=None, refresh=False):
    root = Path(root).resolve()
    git(root, "rev-parse", "--show-toplevel")
    branch = git(root, "symbolic-ref", "--short", "HEAD", optional=True)
    head = git(root, "rev-parse", "--verify", "HEAD", optional=True)
    refreshed, error = False, None
    if refresh and remote:
        try:
            git(root, "fetch", "--", reference(remote))
            refreshed = True
        except (ContractError, subprocess.TimeoutExpired) as exc: error = str(exc)
    revisions = {}
    for ref in refs:
        raw = git(root, "rev-parse", "--verify", reference(ref) + "^{commit}", optional=True)
        revisions[ref] = raw.decode().strip() if raw else None
    return {"branch": branch.decode().strip() if branch else None,
            "head": head.decode().strip() if head else None, "unborn": head is None,
            "refs": revisions, "observed_at": now(), "refreshed": refreshed,
            "remote": remote, "refresh_error": error}


def subject(root, scope):
    root = Path(root).resolve()
    if not scope or len(scope) != len(set(scope)) or any(not isinstance(x, str) or not x.strip("/") for x in scope):
        raise ContractError("Declare las rutas de código/artefacto cubiertas")
    require("subject_entries", len(scope), 20000, "Declare las rutas de código/artefacto cubiertas")
    files = {}
    for relative in scope:
        path = path_at(root, relative, missing=True)
        if relative.startswith((DOCS + "/", ".lks-sdd/")):
            raise ContractError("El sujeto de código no incluye registros SDD")
        if not path.exists():
            files[relative] = None
        elif path.is_file(): files[relative] = sha(read_bytes(root, relative, limit=64 * 1024 * 1024))
        else:
            for directory, folders, names in os.walk(path, followlinks=False):
                for name in folders + names: path_at(root, (Path(directory) / name).relative_to(root).as_posix())
                for name in names:
                    rel = (Path(directory) / name).relative_to(root).as_posix()
                    files[rel] = sha(read_bytes(root, rel, limit=64 * 1024 * 1024))
                    require("subject_entries", len(files), 20000, "Sujeto demasiado amplio")
        require("subject_entries", len(files), 20000, "Sujeto demasiado amplio")
    return {"scope": sorted(scope), "files": dict(sorted(files.items())), "digest": fingerprint(files)}


def branch_check(model, request):
    observed = observe(model.root)
    if observed["branch"] not in request.data.get("branches", []):
        raise ContractError("La petición corresponde a otra rama; registre el cambio o su excepción")
    if not request.data.get("target"): raise ContractError("Falta el destino de integración")
    if observed["branch"] == request.data["target"]:
        raise ContractError("La petición debe trabajar en su rama identificada, separada del destino")
    return observed


def code_inventory(root):
    """Permitted tracked/non-ignored inputs; unrelated work is retained as baseline."""
    raw = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if len(raw) > GIT_STDOUT_LIMIT:
        require("git_stdout_bytes", len(raw), GIT_STDOUT_LIMIT, "Salida Git excesiva")
    if raw.count(b"\0") > RAW_PATH_LIMIT:
        require("git_paths", raw.count(b"\0"), RAW_PATH_LIMIT, "Enumeración Git demasiado amplia")
    if raw and not raw.endswith(b"\0"):
        raise ContractError("Inventario Git incompleto")
    paths = sorted(set(p.decode("utf-8") for p in raw.split(b"\0") if p))
    eligible = []
    for path in paths:
        if not contract_input_allowed(path): continue
        if path in {DOCS, ".lks-sdd"} or path.startswith((DOCS + "/", ".lks-sdd/")): continue
        eligible.append(path)
        if len(eligible) > CODE_PATH_LIMIT:
            require("code_files", len(eligible), CODE_PATH_LIMIT, "Inventario de código demasiado amplio")
    files = {}
    for path in eligible:
        files.update(subject(root, [path])["files"])
        if len(files) > CODE_PATH_LIMIT:
            require("code_files", len(files), CODE_PATH_LIMIT, "Inventario de código demasiado amplio")
    return files


def scope_changes(root, baseline, allowed):
    from v3_team import contains
    current = code_inventory(root)
    changed = [p for p in set(current) | set(baseline) if current.get(p) != baseline.get(p)]
    return {"changed": sorted(changed), "outside": sorted(p for p in changed if not contains(allowed, p)), "current": current}


def coordination(model, request, action, *, refresh=False):
    from v3_policy import policy_for
    policy = policy_for(model, request)
    refs = request.data.get("shared_refs", [])
    observed = observe(model.root, refs=refs, remote=request.data.get("remote"), refresh=refresh)
    if not refs: return {"state": "local", "observation": observed, "differences": []}
    unavailable = bool(observed["refresh_error"] or any(v is None for v in observed["refs"].values()))
    if request.data.get("remote") and not observed["refreshed"]: unavailable = True
    if unavailable:
        if action not in policy.data.get("offline_actions", ["query"]):
            raise ContractError("No se puede comprobar la referencia compartida; solo continúa el trabajo local permitido")
        return {"state": "last-known", "observation": observed, "differences": []}
    differences = []
    for ref in refs:
        for e in model.elements.values():
            if e.kind not in {"policy", "member", "assignment"}: continue
            raw = git(model.root, "show", reference(ref) + ":" + e.path, optional=True)
            if raw is None or sha(raw) != model.hashes[e.path]: differences.append(e.source())
    if differences and action != "query":
        raise ContractError("Gobierno/asignación difiere de la referencia compartida; reconciliar la porción antes de continuar")
    return {"state": "received" if not differences else "diverged", "observation": observed, "differences": differences}


def integration_guard(trusted, candidate):
    trusted.require_valid(); candidate.require_valid()
    if trusted.root == candidate.root: raise ContractError("Seleccione una base de confianza independiente del candidato")
    if trusted.project.uid != candidate.project.uid: raise ContractError("Proyectos distintos")
    changes = []
    for key in set(trusted.elements) | set(candidate.elements):
        before, after = trusted.elements.get(key), candidate.elements.get(key)
        if before and after and before.digest() == after.digest(): continue
        changes.append({"uid": key, "before": before.source() if before else None,
                        "after": after.source() if after else None,
                        "requires_review": bool((before or after).kind in {"project", "policy", "member"} or
                                                (before and before.kind in {"rule", "constraint", "interface", "proposal"}) or
                                                (after and after.data.get("global")))})
    return {"status": "needs-decision" if any(c["requires_review"] for c in changes) else "structurally-compatible",
            "changes": changes, "semantic_acceptance": "pending", "pr_approval": "not-granted"}
