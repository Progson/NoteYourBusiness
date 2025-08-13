# src/nyb/utils/naming.py
from __future__ import annotations
from pathlib import Path

def with_suffix_n(path: Path, n: int) -> Path:
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    candidate = f"{stem} ({n}){suffix}"
    return parent / candidate

def next_collision_free(path: Path) -> Path:
    if not path.exists():
        return path
    n = 1
    while True:
        candidate = with_suffix_n(path, n)
        if not candidate.exists():
            return candidate
        n += 1
