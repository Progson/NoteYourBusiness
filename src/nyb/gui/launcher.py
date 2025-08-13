# src/nyb/gui/launcher.py
from __future__ import annotations
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

from nyb.gui.encrypt_wizard import EncryptDialog
from nyb.gui.decrypt_wizard import DecryptDialog

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteYourBusiness")
        w = QWidget(self)
        lay = QVBoxLayout(w)
        self.btn_encrypt = QPushButton("Szyfruj pliki/folder", self)
        self.btn_decrypt = QPushButton("Odszyfruj pliki/folder", self)
        self.btn_note = QPushButton("Nowa notatka (wkrótce)", self)
        self.btn_settings = QPushButton("Ustawienia (wkrótce)", self)
        for b in (self.btn_encrypt, self.btn_decrypt, self.btn_note, self.btn_settings):
            lay.addWidget(b)
        self.setCentralWidget(w)

        self.btn_encrypt.clicked.connect(self._open_encrypt)
        self.btn_decrypt.clicked.connect(self._open_decrypt)

    def _open_encrypt(self):
        dlg = EncryptDialog(self)
        dlg.resize(800, 500)
        dlg.exec()

    def _open_decrypt(self):
        dlg = DecryptDialog(self)
        dlg.resize(800, 500)
        dlg.exec()
