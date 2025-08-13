# src/nyb/gui/worker.py
from __future__ import annotations
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from PyQt6.QtCore import QObject, QThread, pyqtSignal

@dataclass
class Task:
    path: Path
    op: str  # "encrypt" | "decrypt"
    pw: bytes  # hasło dla tego pliku

class Worker(QObject):
    item_progress = pyqtSignal(str, str, int, int)   # path, status, size, elapsed_ms
    overall = pyqtSignal(int, int)                   # done, total
    finished = pyqtSignal()

    # callable przyjmuje (Path, pw_bytes)
    def __init__(self, tasks: List[Task], do_encrypt: Callable[[Path, bytes], str] | None, do_decrypt: Callable[[Path, bytes], str] | None):
        super().__init__()
        self._tasks = tasks
        self._stop = False
        self._do_encrypt = do_encrypt
        self._do_decrypt = do_decrypt

    def stop(self):
        self._stop = True

    def run(self):
        total = len(self._tasks)
        done = 0
        self.overall.emit(done, total)
        for t in self._tasks:
            if self._stop:
                self.item_progress.emit(str(t.path), "Pominięto (anulowano)", 0, 0)
                done += 1
                self.overall.emit(done, total)
                continue
            start = time.perf_counter()
            try:
                if t.op == "encrypt" and self._do_encrypt:
                    out = self._do_encrypt(t.path, t.pw)
                elif t.op == "decrypt" and self._do_decrypt:
                    out = self._do_decrypt(t.path, t.pw)
                else:
                    out = ""
                elapsed = int((time.perf_counter() - start) * 1000)
                size = t.path.stat().st_size if t.path.exists() else 0
                status = "Sukces" if out else "Pominięto"
                self.item_progress.emit(str(t.path), status, size, elapsed)
            except Exception as e:
                elapsed = int((time.perf_counter() - start) * 1000)
                self.item_progress.emit(str(t.path), f"Błąd: {e}", 0, elapsed)
            done += 1
            self.overall.emit(done, total)
        self.finished.emit()

def start_in_thread(worker: Worker) -> QThread:
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.start()
    return thread
