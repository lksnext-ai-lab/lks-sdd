"""Selective static excerpts. No parsing step imports or executes the project."""
from __future__ import annotations

import re
from query_context import normalize, terms
from query_sources import SourceReader, QueryError


def inspect_code(reader: SourceReader, paths: tuple[str, ...], topic: str, remaining: int) -> tuple[list[dict], list[dict]]:
    fragments, dependencies = [], []
    words = terms(topic)
    candidates = []
    explicit = set(paths)
    for scope in dict.fromkeys(paths):
        if scope.split("/")[0].casefold() in {".lks-sdd", ".git"}:
            raise QueryError("El runtime y el índice no son implementación del consumidor.")
        candidates.extend(reader.inventory(scope, code=True))
    for path in dict.fromkeys(candidates):
        source = reader.read(path, "code")
        if not source:
            continue
        if path not in explicit and words and not any(w in normalize(path + "\n" + source["text"]) for w in words):
            continue
        if len(source["text"]) > remaining:
            reader.exclude(path, "output-limit-unread-fragment")
            continue
        remaining -= len(source["text"])
        fragments.append({"source": path, "line": 1, "end_line": max(1, source["line_count"]),
                          "text": source["text"], "nature": "observed-in-code", "authority": "observation-only",
                          "included_because": ["explicit-code-scope" if path in explicit else "code-topic-candidate"]})
        for number, line in enumerate(source["text"].splitlines(), 1):
            if re.match(r"\s*(?:from\s+\S+\s+import|import\s+|.*require\s*\(|.*from\s+['\"]|(?:JOIN|REFERENCES)\s+)", line, re.I):
                dependencies.append({"source": path, "line": number, "text": line,
                                     "resolution": "not-followed", "nature": "lexical-candidate"})
                if len(dependencies) >= 100:
                    reader.warnings.append("dependency-candidate-limit")
                    return fragments, dependencies
    return fragments, dependencies
