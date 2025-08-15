# src/nyb/gui/progress_view.py
from __future__ import annotations
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox

from pathlib import Path
from PyQt6.QtGui import QColor, QGuiApplication, QIcon  # (import Path powyżej)

class ProgressView(QWidget):
    cancel_clicked = pyqtSignal()
    open_folder_clicked = pyqtSignal()
    copy_report_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = {}
        lay = QVBoxLayout(self)

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        lay.addWidget(self.bar)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Ścieżka", "Status", "Rozmiar", "Czas [ms]"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table)

        hl = QHBoxLayout()
        self.btn_open = QPushButton("Otwórz folder", self)
        self.btn_copy = QPushButton("Kopiuj raport", self)
        self.btn_cancel = QPushButton("Zamknij", self)
        self.btn_open.setEnabled(False)
        hl.addWidget(self.btn_open)
        hl.addWidget(self.btn_copy)
        hl.addStretch(1)
        hl.addWidget(self.btn_cancel)
        lay.addLayout(hl)

        self.btn_cancel.clicked.connect(self.cancel_clicked)
        self.btn_open.clicked.connect(self.open_folder_clicked)
        self.btn_copy.clicked.connect(self._copy_report)

    def set_overall_progress(self, done: int, total: int):
        val = 0 if total == 0 else int(done * 100 / total)
        self.bar.setValue(val)
        if done >= total and total > 0:
            self.btn_open.setEnabled(True)

    # --- REPLACE in progress_view.py ---

    def _ensure_row(self, path: str) -> int:
        if path in self._rows:
            return self._rows[path]
        r = self.table.rowCount()
        self.table.insertRow(r)

        name = Path(path).name
        it_name = QTableWidgetItem(name)
        it_name.setToolTip(path)  # pełna ścieżka w tooltipie
        self.table.setItem(r, 0, it_name)

        self.table.setItem(r, 1, QTableWidgetItem(""))
        self.table.setItem(r, 2, QTableWidgetItem(""))
        self.table.setItem(r, 3, QTableWidgetItem(""))
        self._rows[path] = r
        return r

    def update_item(self, path: str, status: str, size: int | None, elapsed_ms: int | None):
        r = self._ensure_row(path)

        # odśwież tooltip (gdyby path się zmienił)
        it_name = self.table.item(r, 0)
        if it_name:
            it_name.setToolTip(path)

        it_status = QTableWidgetItem(status)
        color = None
        s = status.lower()
        if s.startswith("sukces"):
            color = QColor(0, 128, 0)
        elif s.startswith("pomin"):
            color = QColor(128, 128, 128)
        elif s.startswith("błąd") or s.startswith("blad"):
            color = QColor(200, 0, 0)
        if color:
            it_status.setForeground(color)
        self.table.setItem(r, 1, it_status)

        self.table.setItem(r, 2, QTableWidgetItem("" if size is None else str(size)))
        self.table.setItem(r, 3, QTableWidgetItem("" if elapsed_ms is None else str(elapsed_ms)))

    def _copy_report(self):
        rows = []
        for r in range(self.table.rowCount()):
            row = [self.table.item(r, c).text() if self.table.item(r, c) else "" for c in range(4)]
            rows.append("\t".join(row))
        QGuiApplication.clipboard().setText("\n".join(rows))
        QMessageBox.information(self, "Raport", "Raport został skopiowany do schowka.")
