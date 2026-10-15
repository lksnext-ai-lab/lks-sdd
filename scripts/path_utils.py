"""Filesystem path helpers shared by the offline runtime."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import tempfile

_GET_FILE_ATTRIBUTES = ctypes.windll.kernel32.GetFileAttributesW if os.name == "nt" else None
if _GET_FILE_ATTRIBUTES is not None:
    _GET_FILE_ATTRIBUTES.argtypes = [ctypes.c_wchar_p]
    _GET_FILE_ATTRIBUTES.restype = ctypes.c_uint32


def file_attributes(path: Path):
    """Fresh Windows link/directory attributes; None requests the portable fallback.

    No pathname or trust result is cached. Callers retain their existing error
    behaviour when the API cannot observe a path. Windows returns the attributes
    of a symbolic link itself, not its target.
    https://learn.microsoft.com/windows/win32/api/fileapi/nf-fileapi-getfileattributesw
    """
    if _GET_FILE_ATTRIBUTES is None: return None
    value = _GET_FILE_ATTRIBUTES(os.fspath(path))
    return None if value == 0xFFFFFFFF else value


def publish_new_file(path: Path, data: bytes, *, prefix=".lks-new-") -> None:
    """Publish complete, fsynced bytes without replacing an existing destination.

    Callers validate the path and create its parent before entering this helper.
    FileExistsError leaves the winning writer's file intact.
    """
    descriptor, temporary = tempfile.mkstemp(prefix=prefix, dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name == "nt":
            os.rename(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def filesystem_root(path: Path) -> Path:
    """Return a filesystem-safe absolute root without changing logical paths."""
    expanded = Path(path).expanduser()
    absolute = os.path.abspath(os.fspath(expanded))
    if os.name != "nt":
        return Path(absolute)
    logical = absolute
    if logical.startswith("\\\\?\\UNC\\"):
        logical = "\\\\" + logical[8:]
    elif logical.startswith("\\\\?\\"):
        logical = logical[4:]
    if len(logical) < 248:
        return Path(logical)
    if absolute.startswith("\\\\?\\"):
        return Path(absolute)
    if logical.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + logical[2:])
    return Path("\\\\?\\" + logical)


def same_filesystem_path(left: Path, right: Path) -> bool:
    """Compare Windows paths while treating 8.3 aliases as their long names."""
    if os.name != "nt":
        return os.path.abspath(os.fspath(Path(left).expanduser())) == os.path.abspath(
            os.fspath(Path(right).expanduser())
        )

    return _comparison_path(left) == _comparison_path(right)


def is_within_filesystem_path(path: Path, root: Path) -> bool:
    """Check containment after expanding 8.3 aliases, without following links."""
    if os.name != "nt":
        try:
            Path(path).absolute().relative_to(Path(root).absolute())
            return True
        except ValueError:
            return False
    try:
        _comparison_path(path).relative_to(_comparison_path(root))
        return True
    except ValueError:
        return False


def _comparison_path(path: Path) -> Path:
    value = os.path.abspath(os.fspath(Path(path).expanduser()))
    if not value.startswith("\\\\?\\"):
        if value.startswith("\\\\"):
            value = "\\\\?\\UNC\\" + value[2:]
        else:
            value = "\\\\?\\" + value
    get_long_path = ctypes.windll.kernel32.GetLongPathNameW
    get_long_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    get_long_path.restype = ctypes.c_uint32
    size = 260
    while True:
        buffer = ctypes.create_unicode_buffer(size)
        result = get_long_path(value, buffer, size)
        if result == 0:
            return Path(os.path.normcase(value))
        if result < size:
            return Path(os.path.normcase(buffer.value))
        size = result + 1


def is_max_path_error(exc: OSError) -> bool:
    """Recognize the Windows legacy MAX_PATH failure."""
    return os.name == "nt" and getattr(exc, "winerror", None) == 206


def max_path_message(path: Path) -> str:
    return (
        "Windows MAX_PATH prevented access to an existing path. "
        "Use a current Windows/Python runtime with long-path support or move "
        f"the project/runtime to a shorter directory: {path}"
    )
