# src/nyb/core/metadata.py
from __future__ import annotations
import os
import stat
import ctypes
from pathlib import Path
from typing import Dict

FILE_ATTRIBUTE_HIDDEN = 0x2

def _is_hidden_windows(p: Path) -> bool:
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
        return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        return False

def _set_hidden_windows(p: Path, hidden: bool) -> None:
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
    if attrs == -1:
        return
    if hidden:
        attrs |= FILE_ATTRIBUTE_HIDDEN
    else:
        attrs &= ~FILE_ATTRIBUTE_HIDDEN
    ctypes.windll.kernel32.SetFileAttributesW(str(p), attrs)

def read_meta(path: str) -> Dict:
    p = Path(path)
    st = p.stat()
    ro = not bool(st.st_mode & stat.S_IWRITE)
    hidden = _is_hidden_windows(p)
    return {
        "mtime": int(st.st_mtime),
        "attribs": {"ro": ro, "hidden": hidden},
    }

def apply_meta(path: str, meta: Dict) -> None:
    p = Path(path)
    # mtime
    if "mtime" in meta:
        os.utime(p, (meta["mtime"], meta["mtime"]))
    # readonly
    ro = meta.get("attribs", {}).get("ro")
    if ro is not None:
        st = p.stat().st_mode
        if ro:
            os.chmod(p, st & ~stat.S_IWRITE)
        else:
            os.chmod(p, st | stat.S_IWRITE)
    # hidden
    hidden = meta.get("attribs", {}).get("hidden")
    if hidden is not None:
        try:
            _set_hidden_windows(p, bool(hidden))
        except Exception:
            pass
