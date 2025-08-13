# src/nyb/core/recycle.py
from __future__ import annotations
from pathlib import Path
from typing import Optional

def move_to_recycle_bin(path: str, logger=None) -> bool:
    """
    Przenieś do Kosza; gdy send2trash nie działa – zwróć False (nie usuwaj).
    """
    p = Path(path)
    if not p.exists():
        return True
    try:
        from send2trash import send2trash
        send2trash(str(p))
        return True
    except Exception as e:
        if logger:
            logger.warning(f"[recycle] send2trash failed for {p}: {e}")
        return False

def remove_permanently(path: str, logger=None) -> bool:
    """
    Permanentne usunięcie (ostrożnie).
    """
    p = Path(path)
    try:
        if p.is_dir():
            p.rmdir()
        else:
            p.unlink()
        return True
    except Exception as e:
        if logger:
            logger.warning(f"[recycle] permanent remove failed for {p}: {e}")
        return False
