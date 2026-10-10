"""Bind new explicit decisions to the exact view; retain existing authority rules."""
from contextvars import ContextVar
from functools import wraps
import inspect
from pathlib import Path

from v3_contract import ContractError
from v3_decision_profiles import INFORMATION

ACTIVE = ContextVar("lks_presented_decision", default=None)


def call_data(function, args, kwargs):
    bound = inspect.signature(function).bind(*args, **kwargs)
    values = dict(bound.arguments)
    root = values.pop("root")
    action = values.pop("action", None) if function.__name__ in {"execute", "_execute", "_execute_persist", "transition"} else None
    data = values.pop("data", values)
    if isinstance(data, dict) and "actor" in values and "actor" not in data: data = {**data, "actor": values["actor"]}
    return root, action, data


def required(event, data):
    if event in INFORMATION or event in {"review", "review-comment", "reject-result", "propose-exception"}: return False
    if event in {"review-proposal", "review-task"} and data.get("outcome") == "changes-requested": return False
    if event in {"start", "resume"}: return bool(data.get("review") or data.get("offer"))
    return event in {"init", "approve", "authorize-plan", "governance", "configure-collaboration", "adopt", "migration-preview", "migration-reconcile",
                     "review-proposal", "close-proposal", "review-task", "resolve-comment", "review-exception", "exception", "revoke",
                     "assign", "handoff", "integrate", "accept", "define-correction", "resolve-defect", "pause", "cancel", "reopen"}


def reviewed(event=None):
    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            supplied = kwargs.pop("presented", None)
            root, chosen, data = call_data(function, args, kwargs)
            chosen = event or chosen
            supplied = supplied or data.get("presented")
            current = ACTIVE.get()
            if current is not None and current["root"] == str(Path(root).resolve()):
                return function(*args, **kwargs)
            if not required(chosen, data): return function(*args, **kwargs)
            from v3_decision_presentation import decision_view
            view = decision_view(root, chosen, data)
            reused = view["intervention"] == "already-authorized"
            if not reused:
                if not view["complete"]: raise ContractError("Complete el contenido antes de aprobar: " + "; ".join(view["issues"]))
                if supplied != view["receipt"]:
                    raise ContractError("Presente el contenido vigente con decision-view y conserve su receipt antes de registrar esta decisión")
            token = ACTIVE.set({"root": str(Path(root).resolve()), "receipt": view["receipt"] if not reused else None,
                                "sources": view["sources"], "basis": view["basis"], "intervention": view["intervention"]})
            try: return function(*args, **kwargs)
            finally: ACTIVE.reset(token)
        return run
    return decorate


def stamp(root, items, sources, guards):
    active = ACTIVE.get()
    if not active or active["root"] != str(Path(root).resolve()) or not active["receipt"]: return
    for item in items:
        # Never alter normative policy/task hashes already used by the transaction.
        # Presentation provenance belongs to the event, not to the proposed rules.
        if item["meta"]["kind"] in {"decision", "authorization", "exception", "assignment", "handoff", "adoption", "receipt", "migration", "execution"}:
            item["meta"]["data"]["presentation"] = active["receipt"]
    from v3_contract import read_bytes, sha
    for path, digest in active["basis"]["source_files"].items():
        if sha(read_bytes(root, path)) != digest or (path in sources and sources[path] != digest):
            raise ContractError("Una fuente cambió después de presentar la decisión: " + path)
        sources[path] = digest
    for asset in active["basis"]["attachments"]: sources[asset["path"]] = asset["sha256"]
    if active["basis"].get("subject"): guards["subject"] = active["basis"]["subject"]
    return set(active["basis"]["source_files"]) | {asset["path"] for asset in active["basis"]["attachments"]}
