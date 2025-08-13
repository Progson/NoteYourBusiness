# src/nyb/gui/common.py
from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QCheckBox, QDialogButtonBox, QLabel

class PasswordDialog(QDialog):
    def __init__(self, confirm: bool = False, show_apply_all: bool = True, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hasło")
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Podaj hasło:"))
        self.edit = QLineEdit(self)
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.edit)

        self.edit2 = None
        if confirm:
            lay.addWidget(QLabel("Powtórz hasło:"))
            self.edit2 = QLineEdit(self)
            self.edit2.setEchoMode(QLineEdit.EchoMode.Password)
            lay.addWidget(self.edit2)

        self.remember = None
        if show_apply_all:
            self.remember = QCheckBox("Zastosuj do wszystkich plików", self)
            self.remember.setChecked(True)  # domyślnie ON
            self.remember.toggled.connect(self._on_apply_all_toggled)
            lay.addWidget(self.remember)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_apply_all_toggled(self, checked: bool):
        # jeśli odznaczone -> wyszarz pola (hasła nie podajemy teraz)
        self.edit.setEnabled(checked)
        if self.edit2:
            self.edit2.setEnabled(checked)

    def _accept(self):
        # jeśli checkbox istnieje i jest odznaczony → akceptuj bez walidacji haseł
        if self.remember and not self.remember.isChecked():
            self.accept()
            return
        if self.edit2 and self.edit.text() != self.edit2.text():
            self.edit2.setText("")
            self.edit2.setPlaceholderText("Hasła się nie zgadzają")
            return
        self.accept()

    def password_bytes(self) -> bytes:
        return self.edit.text().encode("utf-8")

    def remember_checked(self) -> bool:
        return bool(self.remember and self.remember.isChecked())
