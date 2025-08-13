# src/nyb/core/walker.py
from __future__ import annotations
import os
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Iterable

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400

def _is_symlink_or_reparse(p: Path) -> bool:
    try:
        if p.is_symlink():
            return True
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
        if attrs == -1:
            return False
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return True  # ostrożnie: lepiej pominąć niż wejść w pętlę

def _is_excluded(p: Path, exclusions: list[str]) -> bool:
    low = str(p).lower()
    return any(excl.lower() in low for excl in exclusions)

@dataclass
class PathTask:
    path: Path
    kind: str  # "file" | "dir"

def iter_targets(paths: Iterable[str], recursive: bool, exclusions: list[str]) -> Iterator[PathTask]:
    """
    Zwraca pliki/katalogi do przetworzenia z pominięciem:
    - symlinków/junctions (reparse),
    - ścieżek pasujących do exclusions.
    Dla recursive=False katalogi są rozwijane do **plików z bieżącego poziomu**.
    """
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            continue
        if _is_symlink_or_reparse(p) or _is_excluded(p, exclusions):
            continue
        if p.is_file():
            yield PathTask(path=p, kind="file")
        elif p.is_dir():
            if not recursive:
                # tylko pliki z tego katalogu (poziom 0)
                try:
                    for child in p.iterdir():
                        if child.is_file() and not _is_symlink_or_reparse(child) and not _is_excluded(child, exclusions):
                            yield PathTask(path=child, kind="file")
                except Exception:
                    pass
            else:
                yield PathTask(path=p, kind="dir")
                for root, dirs, files in os.walk(p):
                    rootp = Path(root)
                    if _is_excluded(rootp, exclusions):
                        dirs[:] = []
                        continue
                    kept = []
                    for d in dirs:
                        dp = rootp / d
                        if not _is_symlink_or_reparse(dp):
                            kept.append(d)
                    dirs[:] = kept
                    for f in files:
                        fp = rootp / f
                        if not _is_symlink_or_reparse(fp) and not _is_excluded(fp, exclusions):
                            yield PathTask(path=fp, kind="file")
