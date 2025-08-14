# src/nyb/gui/web_pages/decrypt.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from nyb.gui.web_pages.base import WebView
from nyb.gui.worker import Worker, Task, start_in_thread
from nyb.gui.common import PasswordDialog
from nyb.config import manager as cfgman
from nyb.core import walker
from nyb.core import io as nybio

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "gui"
DECRYPT_HTML = ASSETS_DIR / "decrypt.html"

@dataclass
class DecItem:
    path: Path
    size: int

class DecryptController:
    def __init__(self, view: WebView, navigate_to: callable):
        self.view = view
        self.navigate_to = navigate_to
        self.items: List[DecItem] = []
        self.recursive: bool = True
        self.keep_nyb: bool = False
        self._thread = None
        self._worker: Worker | None = None
        self._done = 0

    # ---------- lifecycle ----------

    def load(self):
        self.items.clear()
        self._stop_threads()
        self.view.load_file(DECRYPT_HTML, self._bind)

    def _bind(self):
        self.items.clear()
        cfg = cfgman.load_config()
        self.recursive = bool(cfg.get("defaults", {}).get("recursive", True))
        # domyślnie NIE zachowujemy .nyb (po sukcesie do Kosza)
        self.keep_nyb = not bool(cfg.get("defaults", {}).get("remove_nyb_after_decrypt", True))  # checkbox odwrotnie

        # Bind przycisków -> nyb://decrypt/...
        self.view.js("""
        (function(){
          const nav = (sub) => window.location.href = 'nyb://decrypt/' + sub;
          const byId = (id) => document.getElementById(id);

          byId('addFiles')?.addEventListener('click', e => { e.preventDefault(); nav('add-files'); });
          byId('addFolders')?.addEventListener('click', e => { e.preventDefault(); nav('add-folders'); });
          byId('startBtn')?.addEventListener('click', e => { e.preventDefault(); nav('start'); });
          byId('clearBtn')?.addEventListener('click', e => { e.preventDefault(); nav('clear'); });
          byId('closeBtn')?.addEventListener('click', e => { e.preventDefault(); nav('close'); });
          byId('openFolder')?.addEventListener('click', e => { e.preventDefault(); nav('open-folder'); });

          byId('recursive')?.addEventListener('change', e => { nav('set-recursive:' + (e.target.checked ? '1':'0')); });
          byId('keepNyb')?.addEventListener('change', e => { nav('set-keepnyb:' + (e.target.checked ? '1':'0')); });
        })();
        """)
        # Helpery wywoływane z Pythona
        self.view.js("""
        (function(){
          window.NYB = window.NYB || {};
          NYB.clearRows = function(){
            const rows = document.getElementById('rows'); if(rows){ rows.innerHTML=''; }
            const bar = document.getElementById('barFill'); if(bar){ bar.style.width='0%'; }
            const p = document.getElementById('percent'); if(p){ p.textContent='0%'; }
            const cnt = document.getElementById('selectedCount'); if(cnt){ cnt.textContent='Wybrano: 0 elementów (kwalifikuje się: 0)'; }
            const start = document.getElementById('startBtn'); if(start){ start.disabled = true; }
          };
          NYB.addRow = function(path, sizeStr){
            const rows = document.getElementById('rows'); if(!rows) return;
            const tr = document.createElement('tr');
            tr.innerHTML = `<td title="${path}">${path}</td>
                            <td><span class="status">Oczekuje</span></td>
                            <td>${sizeStr}</td>
                            <td class="time">—</td>`;
            rows.appendChild(tr);
            NYB.updateSummary();
          };
          NYB.updateSummary = function(){
            const rows = document.getElementById('rows'); if(!rows) return;
            const count = rows.children.length;
            // kwalifikujące się to wszystkie (bo filtrujemy w Pythonie po .nyb)
            const el = document.getElementById('selectedCount'); if(el){ el.textContent = `Wybrano: ${count} elementów (kwalifikuje się: ${count})`; }
            const start = document.getElementById('startBtn'); if(start){ start.disabled = count === 0; }
          };
          NYB.setRowStatus = function(index, label, ok, ms){
            const rows = document.getElementById('rows'); if(!rows) return;
            const tr = rows.children[index]; if(!tr) return;
            const st = tr.querySelector('.status'); if(!st) return;
            st.textContent = label;
            st.className = 'status ' + (ok===true ? 'ok' : ok===false ? 'err' : '');
            const tm = tr.querySelector('.time'); if(tm && ms !== null){ tm.textContent = String(ms); }
          };
          NYB.setProgress = function(pct){
            const bar = document.getElementById('barFill'); if(bar){ bar.style.width = pct + '%'; }
            const p = document.getElementById('percent'); if(p){ p.textContent = Math.round(pct) + '%'; }
          };
        })();
        """)
        # Inicjalizacja checkboxów
        self.view.js(f"""
        (function(){{
          const r = document.getElementById('recursive'); if(r) r.checked = {str(self.recursive).lower()};
          const k = document.getElementById('keepNyb'); if(k) k.checked = {str(self.keep_nyb).lower()};
        }})();
        """)

    # ---------- handlers z routera ----------

    def handle(self, sub: str | None):
        if not sub:
            self.load(); return
        if sub.startswith("set-recursive:"):
            self.recursive = (sub.split(":",1)[1] == "1"); return
        if sub.startswith("set-keepnyb:"):
            self.keep_nyb = (sub.split(":",1)[1] == "1"); return
        if sub == "add-files":
            self._add_files(); return
        if sub == "add-folders":
            self._add_folders(); return
        if sub == "clear":
            self.items.clear(); self.view.js("NYB.clearRows();"); return
        if sub == "close":
            self._stop_threads(); self.navigate_to("launcher"); return
        if sub == "open-folder":
            self._open_folder(); return
        if sub == "start":
            self._start(); return

    # ---------- file ops ----------

    def _fmt_size(self, n: int) -> str:
        if n < 1024: return f"{n} B"
        if n < 1024*1024: return f"{n//1024} KB"
        return f"{n/(1024*1024):.1f} MB"

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(None, "Wybierz pliki .nyb do odszyfrowania", "", "Pliki NYB (*.nyb)")
        if not files: return
        added = 0
        for f in files:
            p = Path(f)
            if not p.exists() or not p.is_file(): continue
            if p.suffix.lower() != ".nyb": continue
            if any(x.path == p for x in self.items): continue
            size = p.stat().st_size
            self.items.append(DecItem(p, size))
            self.view.js(f"NYB.addRow({WebView.q(p)}, {WebView.q(self._fmt_size(size))});")
            added += 1
        if added: self.view.js("NYB.updateSummary();")

    def _add_folders(self):
        folder = QFileDialog.getExistingDirectory(None, "Wybierz folder z plikami .nyb")
        if not folder: return
        cfg = cfgman.load_config()
        exclusions = cfg.get("exclusions", [])
        for t in walker.iter_targets([folder], self.recursive, exclusions):
            if t.kind == "file" and t.path.suffix.lower() == ".nyb":
                p = t.path
                if any(x.path == p for x in self.items): continue
                try: size = p.stat().st_size
                except Exception: size = 0
                self.items.append(DecItem(p, size))
                self.view.js(f"NYB.addRow({WebView.q(p)}, {WebView.q(self._fmt_size(size))});")
        self.view.js("NYB.updateSummary();")

    def _open_folder(self):
        dest = Path.home()
        if self.items:
            dest = self.items[0].path.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(dest)))

    # ---------- run decryption ----------

    def _start(self):
        if not self.items: return
        dlg = PasswordDialog(confirm=False, show_apply_all=True)
        if not dlg.exec(): return
        apply_all = dlg.remember_checked()
        first_pw = dlg.password_bytes()

        cfg_run = cfgman.load_config()
        cfg_run.setdefault("defaults", {})
        # remove_nyb_after_decrypt odwrotnie do checkboxa „Zachowaj kopię .nyb”
        cfg_run["defaults"]["remove_nyb_after_decrypt"] = (not self.keep_nyb)

        tasks: List[Task] = []
        if apply_all:
            for it in self.items:
                tasks.append(Task(path=it.path, op="decrypt", pw=first_pw))
        else:
            for it in self.items:
                per = PasswordDialog(confirm=False, show_apply_all=False)
                per.setWindowTitle(f"Hasło dla: {it.path.name}")
                if not per.exec(): continue
                tasks.append(Task(path=it.path, op="decrypt", pw=per.password_bytes()))
            if not tasks: return

        def do_decrypt(path: Path, pw_bytes: bytes) -> str:
            return nybio.decrypt_file(path, (lambda: pw_bytes), cfg_run)

        self._worker = Worker(tasks, None, do_decrypt)
        self._thread = start_in_thread(self._worker)
        self._done = 0
        total = len(tasks)

        def on_item_progress(path_str: str, status: str, size: int, elapsed_ms: int):
            try:
                p = Path(path_str)
                idx = next(i for i, it in enumerate(self.items) if it.path == p)
            except Exception:
                idx = 0
            ok = True if status.lower().startswith("sukces") else (False if status.lower().startswith(("błąd","blad")) else None)
            label = "Odszyfrowano" if ok is True else ("Błąd" if ok is False else status)
            self.view.js(f"NYB.setRowStatus({idx}, {WebView.q(label)}, {'true' if ok is True else ('false' if ok is False else 'null')}, {elapsed_ms if elapsed_ms is not None else 'null'});")
            self._done += 1
            pct = self._done / total * 100.0
            self.view.js(f"NYB.setProgress({pct});")

        def on_finished():
            self._stop_threads()

        self._worker.item_progress.connect(on_item_progress)
        self._worker.finished.connect(on_finished)

    def _stop_threads(self):
        try:
            if self._worker: self._worker.stop()
            if self._thread:
                self._thread.quit()
                self._thread.wait()
        except Exception:
            pass
        self._worker = None
        self._thread = None
