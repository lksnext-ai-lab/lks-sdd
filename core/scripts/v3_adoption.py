"""Bounded static observations do not infer the intended behavior of an existing system."""
from pathlib import Path
from v3_contract import ContractError, element, load, read_bytes, sha, now
from v3_authoring import initialize
from v3_storage import prepare
from v3_policy import operator
from v3_git import observe


def inspect(root, paths, purpose):
    root = Path(root).resolve()
    if not paths or len(paths) > 50 or not purpose.strip(): raise ContractError("Seleccione hasta 50 fuentes y la finalidad de la inspección")
    sources = []
    total = 0
    for path in sorted(set(paths)):
        data = read_bytes(root, path, limit=1024*1024); total += len(data)
        if total > 8*1024*1024: raise ContractError("Acote la inspección a una porción útil")
        sources.append({"path": path, "sha256": sha(data), "bytes": len(data)})
    return {"purpose": purpose, "sources": sources, "coverage": "partial", "intent": "unconfirmed", "writes": [],
            "next": "Describa las observaciones con sus fuentes y confirme la intención de la porción; no deduzca ausencia de funciones"}


def record(root, actor, inspection, observations, confirmed_intent, statement):
    model = load(root).require_valid(); identity = operator(model, actor, "define")
    if not observations or not statement.strip(): raise ContractError("Faltan observaciones y decisión sobre su incorporación")
    hashes = {s["path"]: s["sha256"] for s in inspection["sources"]}
    for path, digest in hashes.items():
        if sha(read_bytes(model.root, path)) != digest: raise ContractError("Fuente de adopción modificada")
    for item in observations:
        if item.get("nature") not in {"fact", "inference", "pending"} or not item.get("text") or not set(item.get("sources", [])) <= set(hashes):
            raise ContractError("Distinga observación, inferencia y pendiente con fuentes locales")
        if item["nature"] == "fact" and not item.get("sources"): raise ContractError("Un hecho observado necesita fuente")
    event = element("adoption", "Adopción parcial de sistema existente", statement, actor=identity,
                    inspection=inspection, observations=observations, confirmed_intent=confirmed_intent,
                    coverage="partial", recorded_at=now(), global_scope=True)
    event["meta"].update(state="confirmed", nature="decision")
    return prepare(root, [event], "adoption", sources=hashes, guards={"git": observe(model.root)})
