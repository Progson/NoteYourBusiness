# src/nyb/gui/encrypt_wizard.py
from __future__ import annotations
from copy import deepcopy
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QCheckBox,
    QFileDialog, QLabel, QMessageBox, QHBoxLayout
)

from nyb.gui.progress_view import ProgressView
from nyb.gui.worker import Worker, Task, start_in_thread
from nyb.gui.common import PasswordDialog
from nyb.config import manager as cfgman
from nyb.core import walker
from nyb.core import io as nybio


class EncryptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Szyfruj pliki/foldery")
        self._thread = None
        self._worker = None
        self._selected: list[str] = []

        self.cfg = cfgman.load_config()
        lay = QVBoxLayout(self)

        self.lbl = QLabel(
            "Dodaj pliki i/lub foldery do szyfrowania (pliki .nyb i .nybnote są pomijane).",
            self
        )
        lay.addWidget(self.lbl)

        row = QHBoxLayout()
        self.btn_choose_files = QPushButton("Wybierz pliki…", self)
        self.btn_choose_dirs = QPushButton("Wybierz foldery…", self)
        self.btn_start = QPushButton("Start", self)
        self.btn_start.setEnabled(False)
        row.addWidget(self.btn_choose_files)
        row.addWidget(self.btn_choose_dirs)
        row.addStretch(1)
        row.addWidget(self.btn_start)
        lay.addLayout(row)

        self.lbl_selected = QLabel("Wybrano: 0 elementów", self)
        lay.addWidget(self.lbl_selected)

        self.chk_recursive = QCheckBox("Rekursywnie", self)
        self.chk_recursive.setChecked(bool(self.cfg.get("defaults", {}).get("recursive", True)))
        lay.addWidget(self.chk_recursive)

        self.chk_replace = QCheckBox("Zachowaj tylko zaszyfrowane (przenieś oryginały do Kosza)", self)
        self.chk_replace.setChecked(True)
        lay.addWidget(self.chk_replace)

        self.progress = ProgressView(self)
        lay.addWidget(self.progress)

        # sygnały
        self.btn_choose_files.clicked.connect(self.choose_files)
        self.btn_choose_dirs.clicked.connect(self.choose_dirs)
        self.btn_start.clicked.connect(self._ask_password_and_start)
        self.progress.cancel_clicked.connect(self.close)
        self.progress.open_folder_clicked.connect(self._open_folder)
        self.chk_recursive.toggled.connect(self._refresh_selected_label)  # <- przeliczaj przy zmianie rekursji

    # ---------- UI pomocnicze ----------

    def _refresh_selected_label(self):
        # Przelicz pliki kwalifikujące się do szyfrowania
        exclusions = self.cfg.get("exclusions", [])
        recursive = self.chk_recursive.isChecked()
        qualify = 0
        for t in walker.iter_targets(self._selected, recursive, exclusions):
            if t.kind == "file" and t.path.suffix.lower() not in (".nyb", ".nybnote"):
                qualify += 1

        self.lbl_selected.setText(f"Wybrano: {len(self._selected)} elementów (kwalifikuje się: {qualify})")
        self.btn_start.setEnabled(qualify > 0)

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Wybierz pliki do szyfrowania", "", "Wszystkie pliki (*.*)")
        if files:
            self._selected += [f for f in files if f not in self._selected]
            self._refresh_selected_label()

    def choose_dirs(self):
        d = QFileDialog(self, "Wybierz foldery do szyfrowania")
        d.setFileMode(QFileDialog.FileMode.Directory)
        d.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if d.exec():
            for folder in d.selectedFiles():
                if folder not in self._selected:
                    self._selected.append(folder)
            self._refresh_selected_label()

    # ---------- Start operacji ----------

    def _ask_password_and_start(self):
        exclusions = self.cfg.get("exclusions", [])
        files: list[Path] = []
        for t in walker.iter_targets(self._selected, self.chk_recursive.isChecked(), exclusions):
            if t.kind == "file" and t.path.suffix.lower() not in (".nyb", ".nybnote"):
                files.append(t.path)
        if not files:
            QMessageBox.information(self, "NoteYourBusiness", "Brak plików do zaszyfrowania.")
            return

        dlg = PasswordDialog(confirm=True, show_apply_all=True, parent=self)
        if not dlg.exec():
            return
        apply_all = dlg.remember_checked()
        first_pw = dlg.password_bytes()

        cfg_run = deepcopy(self.cfg)
        cfg_run.setdefault("defaults", {})
        cfg_run["defaults"]["replace_original"] = bool(self.chk_replace.isChecked())
        cfg_run["defaults"]["send_to_recycle_bin"] = True

        tasks: list[Task] = []
        if apply_all:
            for p in files:
                tasks.append(Task(path=p, op="encrypt", pw=first_pw))
        else:
            for p in files:
                per = PasswordDialog(confirm=True, show_apply_all=False, parent=self)
                per.setWindowTitle(f"Hasło dla: {p.name}")
                if not per.exec():
                    continue
                tasks.append(Task(path=p, op="encrypt", pw=per.password_bytes()))
            if not tasks:
                QMessageBox.information(self, "NoteYourBusiness", "Przerwano – brak plików z nadanym hasłem.")
                return

        def do_encrypt(path: Path, pw_bytes: bytes) -> str:
            return nybio.encrypt_file(path, (lambda: pw_bytes), cfg_run)

        self._worker = Worker(tasks, do_encrypt, None)
        self._thread = start_in_thread(self._worker)
        self._worker.item_progress.connect(self.progress.update_item)
        self._worker.overall.connect(self.progress.set_overall_progress)
        self._worker.finished.connect(self._on_finished)

    # ---------- Kontrola życia wątku ----------

    def _on_cancel(self):
        if self._worker:
            self._worker.stop()
        self.progress.btn_cancel.setEnabled(False)
        self.btn_start.setEnabled(False)

    def _on_finished(self):
        try:
            if self._thread:
                self._thread.quit()
                self._thread.wait()
        except Exception:
            pass
        self._thread = None
        self._worker = None

    def closeEvent(self, ev):
        try:
            if self._worker:
                self._worker.stop()
            if self._thread:
                self._thread.quit()
                self._thread.wait()
        except Exception:
            pass
        self._thread = None
        self._worker = None
        super().closeEvent(ev)

    def _open_folder(self):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        if self._selected:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self._selected[0]).parent)))
