"""Extract exact version sections from the repository changelog."""

from __future__ import annotations

import re


SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?$"
)


class ReleaseNotesError(Exception):
    """Expected error while extracting a versioned changelog section."""


def extract(content: bytes, version: str) -> bytes:
    """Return the exact Markdown section for a published plugin version."""

    if not SEMVER_RE.fullmatch(version):
        raise ReleaseNotesError("La versión de release debe ser SemVer válida.")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseNotesError("CHANGELOG.md no es UTF-8.") from exc

    header = re.compile(
        rf"^##[ \t]+{re.escape(version)}(?:[ \t]+[—-].*)?[ \t]*$",
        re.MULTILINE,
    )
    matches = list(header.finditer(text))
    if len(matches) != 1:
        detail = "no existe" if not matches else "aparece más de una vez"
        raise ReleaseNotesError(
            f"La sección de changelog para la versión {version} {detail}."
        )
    start = matches[0].start()
    next_header = re.compile(r"^##[ \t]+", re.MULTILINE).search(text, matches[0].end())
    end = next_header.start() if next_header else len(text)
    section = text[start:end]
    if not section[matches[0].end() - start:].strip():
        raise ReleaseNotesError(
            f"La sección de changelog para la versión {version} está vacía."
        )
    return section.encode("utf-8")
