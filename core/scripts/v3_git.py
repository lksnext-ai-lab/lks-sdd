"""Bounded Git observation, never shell evaluation or automatic publication."""
import os
from pathlib import Path
import subprocess

from v3_contract import ContractError, DOCS, fingerprint, now, path_at, read_bytes, sha


def git(root, *args, optional=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=60)
    if result.returncode and not optional:
        raise ContractError("Git no pudo completar la observación: " + result.stderr.decode("utf-8", errors="replace")[:800])
    if len(result.stdout) > 16 * 1024 * 1024: raise ContractError("Salida Git excesiva; delimite el ámbito")
    return result.stdout if not result.returncode else None


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
    if not scope or any(not isinstance(x, str) or not x.strip("/") for x in scope):
        raise ContractError("Declare las rutas de código/artefacto cubiertas")
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
                    if len(files) > 20000: raise ContractError("Sujeto demasiado amplio")
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
    """Tracked and non-ignored files; existing unrelated work is retained as baseline."""
    raw = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    paths = sorted(set(p.decode("utf-8") for p in raw.split(b"\0") if p))
    if len(paths) > 20000: raise ContractError("Inventario de código demasiado amplio")
    files = {}
    for path in paths:
        if path == DOCS or path.startswith((DOCS + "/", ".lks-sdd/")): continue
        files.update(subject(root, [path])["files"])
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
