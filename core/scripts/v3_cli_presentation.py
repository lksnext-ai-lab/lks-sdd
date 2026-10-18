"""Opt-in CLI diagnostic projection; never an authority or observation batch."""
import copy
import json


USAGE_VIEW = "lks-sdd-usage-view/1"


def json_text(value, *, operational=False):
    """Lossless whitespace reduction; literal string bytes survive JSON decode."""
    return json.dumps(value,ensure_ascii=False,**({"separators":(",",":")} if operational else {"indent":2}))+"\n"


def completed_work_view(action, result):
    """Successful mutation receipt, not a replacement for reading a contract.

    Queries, previews, stops and partial effects always retain their literal
    contract. Core/API, details, output and capture keep the complete result.
    """
    if action not in {"work-continue","work-record-results"} or result.get("status")!="completed":return result
    shown={k:v for k,v in result.items() if k!="contract"}
    shown["contract_notice"]="Successful technical receipt; before new work read the current literal contract with work-prepare/context. Details/output/capture retain the full result only when explicitly selected and successful; check transport status before retrying. This receipt grants no authority."
    return shown


def usage_view(usage, *, exported=None):
    """Keep provenance/limits without retransmitting inputs, results or fragments.

    The original API result stays intact for compatible output and explicit export.
    This distinct format cannot be imported as a complete usage observation.
    """
    shown = {"format": USAGE_VIEW, "status": usage.get("status", "summary-only"),
             "observation_refs": [], "complete_observations_emitted": False}
    for key in ("cause", "quality", "conservation"):
        if key in usage: shown[key] = copy.deepcopy(usage[key])
    for row in usage.get("observations", []):
        ref = {key: copy.deepcopy(row[key]) for key in
               ("observation_id", "run_id", "invocation_id", "binding", "operation", "phase", "stage",
                "origin", "runtime", "window_state", "metrics", "gaps", "preview_hash", "application", "result_digest") if key in row}
        ref["fragment_count"] = len(row.get("fragments", []))
        ref["fragment_gaps"] = [{k: copy.deepcopy(v) for k, v in fragment.items()
                                  if k not in {"text", "text_ref", "data_ref"}}
                                 for fragment in row.get("fragments", []) if fragment.get("gap")]
        ref["diagnostic_gaps"] = {key: row[key]["gap"] for key in ("input", "result")
                                  if isinstance(row.get(key), dict) and row[key].get("gap")}
        shown["observation_refs"].append(ref)
    if "pending_observations" in usage:
        shown["pending_observation_count"] = len(usage["pending_observations"])
    shown["report_available"] = "summary" in usage or "prompt" in usage
    if "transport" in usage: shown["transport"] = copy.deepcopy(usage["transport"])
    shown["full_diagnostic"] = ({"status": "api-result-exported", "path": str(exported),
                                 "scope": "Full API envelope; existing source-capture gaps still apply"}
                                if exported else
                                {"status": "not-exported-by-this-call",
                                 "next": "Use --details to show the full envelope, or --output on the invocation to retain it"})
    return shown


def export_path(destination, root, source=None):
    """Validate transport destinations before executing any operation."""
    from pathlib import Path
    from path_utils import filesystem_root, same_filesystem_path
    from v3_contract import ContractError
    output = filesystem_root(Path(destination).resolve())
    root = filesystem_root(Path(root).resolve())
    # Compare each ancestor: the existing ancestor can resolve Windows 8.3 names
    # even when the complete deep output path does not exist yet.
    if (any(same_filesystem_path(parent, root) for parent in (output, *output.parents)) or
            any(same_filesystem_path(output, parent) for parent in root.parents)):
        raise ContractError("Output must be outside the consumer")
    if source is not None:
        source = filesystem_root(Path(source).resolve())
        if same_filesystem_path(output, source) or (output.exists() and source.exists() and output.samefile(source)):
            raise ContractError("Output must not replace its input")
    if output.is_file() and output.stat().st_nlink > 1:
        raise ContractError("Output must not overwrite a multiply-linked file")
    return output


def write_export(result, output):
    from v3_contract import canonical
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(result) + b"\n")


def export_summary(result, output):
    """Short transport reference retaining conditions; never a decision receipt."""
    shown = {"output": str(output), "status": result.get("status", "preview" if "preview" in result else "exported"),
             "preview_hash": result.get("preview", {}).get("preview_hash", result.get("preview_hash")),
             "export_notice": "Lea el resultado exportado antes de presentarlo o decidir; exportar no acredita lectura ni aprobación"}
    for key in ("complete", "issues", "errors", "warnings", "cause", "causes", "conditions", "sufficiency", "budget_notice", "writes", "current_conformance", "next", "planning_coverage", "effect", "collaboration"):
        if key in result: shown[key] = copy.deepcopy(result[key])
    if result.get("status") in {"applied", "previously-applied", "completed", "rolled-back", "compacted", "retained-originals", "rejected-stale-preview"} and result.get("receipt"):
        shown["receipt"] = result["receipt"]
    if isinstance(result.get("presentation"), dict):
        shown["presentation"] = {k: copy.deepcopy(result["presentation"][k]) for k in ("complete", "issues") if k in result["presentation"]}
    return shown


def operational_requested(arguments):
    """Read presentation flags at a dispatcher failure without parsing input data."""
    view, details, index = "compatible", False, 0
    while index < len(arguments):
        token = arguments[index]
        if token == "--": break
        if token in {"--input", "--output", "--authorize", "--receipt", "--capture-dir"}:
            index += 2; continue
        if token == "--view" and index + 1 < len(arguments):
            view = arguments[index + 1]; index += 2; continue
        if token.startswith("--view="): view = token.split("=", 1)[1]
        if token == "--details": details = True
        index += 1
    return view == "operational" and not details
