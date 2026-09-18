"""Make local imports work when Python launches a script through ``\\?\\``."""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


def ensure_import_path(script_file: str) -> None:
    if os.name != "nt":
        return
    script_path = os.fspath(script_file)
    if not script_path.startswith("\\\\?\\"):
        return
    get_short_path = ctypes.windll.kernel32.GetShortPathNameW
    get_short_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    get_short_path.restype = ctypes.c_uint32
    size = 260
    while True:
        buffer = ctypes.create_unicode_buffer(size)
        result = get_short_path(script_path, buffer, size)
        if result == 0:
            raise OSError(
                "Windows MAX_PATH prevented Python from importing the plugin "
                f"entrypoint: {script_path}"
            )
        if result < size:
            break
        size = result + 1
    scripts_dir = str(Path(buffer.value).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
