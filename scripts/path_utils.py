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


def filesystem_root(path: Path, *, force_extended: bool = False) -> Path:
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
    if len(logical) < 248 and not force_extended:
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


def short_existing_path(path: Path) -> Path:
    """Existing Windows 8.3 spelling for legacy external tools; no cached trust."""
    path = filesystem_root(path, force_extended=True)
    if os.name != "nt": return path
    get_short = ctypes.windll.kernel32.GetShortPathNameW
    get_short.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    get_short.restype = ctypes.c_uint32
    size = 260
    while size <= 32768:
        buffer = ctypes.create_unicode_buffer(size)
        required = get_short(os.fspath(path), buffer, size)
        if not required: raise OSError("Windows cannot supply an existing short path for Git")
        if required < size:
            value = buffer.value
            if value.startswith("\\\\?\\UNC\\"): value = "\\\\" + value[8:]
            elif value.startswith("\\\\?\\"): value = value[4:]
            alias = Path(value)
            if len(value) >= 248 or not same_filesystem_path(path, alias):
                raise OSError("Windows short path is unavailable or does not identify the same Git directory")
            return alias
        size = required + 1
    raise OSError("Windows short path exceeds the supported path bound")


def owned_by_current_user(paths) -> bool:
    """Conservative Windows Git trust check, independent of functional authority."""
    if os.name != "nt": return False
    kernel = ctypes.windll.kernel32; security = ctypes.windll.advapi32
    handle = ctypes.c_void_p
    current = kernel.GetCurrentProcess; current.restype = handle
    open_token = security.OpenProcessToken
    open_token.argtypes = [handle, ctypes.c_uint32, ctypes.POINTER(handle)]
    open_token.restype = ctypes.c_int
    information = security.GetTokenInformation
    information.argtypes = [handle, ctypes.c_uint32, handle, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    information.restype = ctypes.c_int
    descriptor = security.GetNamedSecurityInfoW
    descriptor.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(handle), handle, handle, handle, ctypes.POINTER(handle)]
    descriptor.restype = ctypes.c_uint32
    equal = security.EqualSid; equal.argtypes = [handle, handle]; equal.restype = ctypes.c_int
    free = kernel.LocalFree; free.argtypes = [handle]; free.restype = handle
    close = kernel.CloseHandle; close.argtypes = [handle]; close.restype = ctypes.c_int
    class User(ctypes.Structure):
        _fields_ = [("sid", handle), ("attributes", ctypes.c_uint32)]
    token = handle()
    if not open_token(current(), 8, ctypes.byref(token)): return False
    try:
        size = ctypes.c_uint32()
        information(token, 1, None, 0, ctypes.byref(size))
        if not 0 < size.value <= 65536: return False
        buffer = ctypes.create_string_buffer(size.value)
        if not information(token, 1, buffer, size, ctypes.byref(size)): return False
        user = ctypes.cast(buffer, ctypes.POINTER(User)).contents.sid
        for path in paths:
            owner = handle(); allocated = handle()
            result = descriptor(str(filesystem_root(path, force_extended=True)), 1, 1,
                                ctypes.byref(owner), None, None, None, ctypes.byref(allocated))
            try:
                if result or not owner or not equal(user, owner): return False
            finally:
                if allocated: free(allocated)
        return True
    finally:
        close(token)
