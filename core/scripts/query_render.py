"""Source-linked, deterministic fallback; conversational synthesis lives in skills."""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import quote


def label(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", text).replace("\n", " ")


def source_link(root: Path, path: str, line: int = 1, *, line_links: bool = True) -> str:
    target = (root / path).absolute().as_posix()
    if target.startswith("//?/UNC/"):
        target = "//" + target[8:]
    elif target.startswith("//?/"):
        target = target[4:]
    target = quote(target, safe="/:_-.")
    if line_links:
        target += ":" + str(line)
    return f"[{label(path)}](<{target}>)"


def diagram(result: dict) -> str | None:
    """Only explicitly typed relations, never lexical similarity or dependency hints."""
    known = {item["id"] for item in result["entities"]} - set(result["duplicates"])
    edges = [r for r in result["relations"] if r["nature"] == "declared"
             and r["source_id"] in known and r["target_id"] in known]
    if not 3 <= len(edges) <= 12:
        return None
    lines = ["flowchart LR"]
    for edge in edges:
        left, right = (edge[k].replace("-", "_") for k in ("source_id", "target_id"))
        relation = re.sub(r"[^A-Za-z0-9 /_-]", "", edge["relation"])[:60]
        lines.append(f'  {left}["{edge["source_id"]}"] -->|"{relation}"| {right}["{edge["target_id"]}"]')
    return "\n".join(lines)


def markdown(result: dict, root: Path, *, line_links: bool = True) -> str:
    if result["status"] == "blocked":
        return "No se ha podido consultar el proyecto. " + result["error"] + "\n"
    if any(e.get("contract_version") == "2.0" for e in result.get("entities", [])):
        from v2_query import human_markdown
        return human_markdown(result, root, line_links=line_links)
    request = result["request"]
    title = request.get("entity") or request.get("topic") or "documentos seleccionados"
    lines = [f"## Contexto de {label(title)}", "",
             "Fuentes recuperadas para elaborar la respuesta. Su suficiencia requiere revisión; "
             "esta vista no valida el contrato ni acredita el estado de producción.", ""]
    if result["entities"]:
        lines += ["| Elemento | Estado declarado | Fuente |", "|---|---|---|"]
        for row in result["entities"]:
            lines.append(f'| {row["id"]} | {label(row["declared_state"] or "No consta")} | '
                         f'{source_link(root, row["source"], row["line"], line_links=line_links)} |')
        lines.append("")
    for fragment in result["fragments"]:
        kind = "Documentación" if fragment["nature"] == "documented" else "Observación estática de código"
        lines += [f'### {kind}: {source_link(root, fragment["source"], fragment["line"], line_links=line_links)}', ""]
        # Fenced excerpts keep consumer Markdown/HTML/images inert in this fallback.
        fence = "`" * max(3, 1 + max((len(m) for m in re.findall(r"`+", fragment["text"])), default=0))
        lines += [fence + "text", fragment["text"], fence, ""]
    if result["relations"]:
        lines += ["### Relaciones documentadas", ""]
        for r in result["relations"]:
            lines.append(f'- {r["source_id"]} → {r["target_id"]}: {label(r["relation"])} '
                         f'({source_link(root, r["source"], r["line"], line_links=line_links)}).')
        lines.append("")
    if result["gaps"] or result["warnings"]:
        lines += ["### Límites y pendientes", ""]
        lines.extend("- " + label(gap) for gap in result["gaps"])
        lines.extend("- " + label(item) for item in result["warnings"])
    if result["diagram"]:
        lines += ["", "Relaciones explícitas; la lista anterior es su alternativa textual.", "", "```mermaid", result["diagram"], "```"]
    return "\n".join(lines).rstrip() + "\n"
