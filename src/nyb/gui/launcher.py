# src/nyb/gui/launcher.py
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGridLayout,
    QStyle,
    QApplication,
    QToolButton,
)

from nyb.gui.encrypt_wizard import EncryptDialog
from nyb.gui.decrypt_wizard import DecryptDialog
# (backlog) from nyb.gui.note_editor import NoteEditor
# (backlog) from nyb.gui.settings_dialog import SettingsDialog

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _load_icon(basename: str, fallback: QStyle.StandardPixmap) -> QIcon:
    """
    Ładowanie ikon: najpierw PNG, potem ICO, w razie porażki – fallback systemowy.
    Wypisuje do konsoli, czego próbował.
    """
    candidates = [
        ASSETS / f"{basename}.png",
        ASSETS / f"{basename}.ico",
        Path.cwd() / "assets" / f"{basename}.png",
        Path.cwd() / "assets" / f"{basename}.ico",
    ]
    for p in candidates:
        if p.exists():
            ic = QIcon(str(p))
            if not ic.isNull():
                print(f"[launcher] icon loaded: {p}")
                return ic
            else:
                print(f"[launcher] icon file exists but QIcon isNull(): {p}")
    style = QApplication.instance().style() if QApplication.instance() else None
    print(f"[launcher] using fallback icon for '{basename}'. Looked at:")
    for p in candidates:
        print(f"  - {p}")
    return (style or QStyle()).standardIcon(fallback)


def _make_tile(text: str, icon: QIcon, w: int = 340, h: int = 260) -> QToolButton:
    """
    Kafelek 2×2: ikona nad tekstem, tekst WIELKIMI LITERAMI.
    """
    btn = QToolButton()
    btn.setIcon(icon)
    btn.setIconSize(QSize(128, 128))            # duża ikona
    btn.setText(text.upper())                   # CAPS
    btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    btn.setFixedSize(w, h)
    btn.setCheckable(False)
    btn.setStyleSheet("""
        QToolButton {
            font-size: 18px;
            padding-top: 10px;
            padding-bottom: 10px;
            border: 1px solid #d0d0d0;
            border-radius: 16px;
            background: #fafafa;
        }
        QToolButton:hover  { background: #f0f0f0; }
        QToolButton:pressed{ background: #e6e6e6; }
    """)
    return btn


class LauncherWindow(QMainWindow):
    """
    Ekran startowy w układzie 2×2:
      [ SZYFRUJ ]   [ ODSZYFRUJ ]
      [  NOTATKA ]  [ USTAWIENIA ]
    Okno ma stały rozmiar liczony „na styk” do siatki kafelków.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteYourBusiness")

        central = QWidget(self)
        grid = QGridLayout(central)

        # Geometria siatki
        M = 24   # marginesy
        S = 20   # odstęp
        grid.setSpacing(S)
        grid.setContentsMargins(M, M, M, M)

        # Ikony
        icon_encrypt  = _load_icon("encrypt",  QStyle.StandardPixmap.SP_DialogYesButton)
        icon_decrypt  = _load_icon("decrypt",  QStyle.StandardPixmap.SP_DialogOpenButton)
        icon_note     = _load_icon("note",     QStyle.StandardPixmap.SP_FileIcon)
        icon_settings = _load_icon("settings", QStyle.StandardPixmap.SP_FileDialogDetailedView)

        # Rozmiar kafli
        TILE_W, TILE_H = 340, 260

        # Kafelki (ikona nad tekstem, CAPS)
        self.btn_encrypt  = _make_tile("Szyfruj pliki / folder",  icon_encrypt,  TILE_W, TILE_H)
        self.btn_decrypt  = _make_tile("Odszyfruj pliki / folder", icon_decrypt, TILE_W, TILE_H)
        self.btn_note     = _make_tile("Nowa notatka (.nybnote)",   icon_note,    TILE_W, TILE_H)
        self.btn_settings = _make_tile("Ustawienia",                icon_settings,TILE_W, TILE_H)

        # Siatka 2×2
        grid.addWidget(self.btn_encrypt,  0, 0)
        grid.addWidget(self.btn_decrypt,  0, 1)
        grid.addWidget(self.btn_note,     1, 0)
        grid.addWidget(self.btn_settings, 1, 1)
        self.setCentralWidget(central)

        # Okno dopasowane do siatki
        total_w = M * 2 + TILE_W * 2 + S
        total_h = M * 2 + TILE_H * 2 + S
        self.setFixedSize(total_w, total_h)

        # Akcje
        self.btn_encrypt.clicked.connect(self._open_encrypt)
        self.btn_decrypt.clicked.connect(self._open_decrypt)
        self.btn_note.clicked.connect(self._open_note)
        self.btn_settings.clicked.connect(self._open_settings)

        # Ikona okna (możesz podmienić np. na "app")
        self.setWindowIcon(_load_icon("encrypt", QStyle.StandardPixmap.SP_ComputerIcon))

    # --- akcje ---

    def _open_encrypt(self):
        dlg = EncryptDialog(self)
        dlg.resize(900, 600)
        dlg.exec()

    def _open_decrypt(self):
        dlg = DecryptDialog(self)
        dlg.resize(900, 600)
        dlg.exec()

    def _open_note(self):
        # TODO: edytor notatek (backlog)
        pass

    def _open_settings(self):
        # TODO: SettingsDialog (edytor config.json) — w kolejnym kroku
        pass
