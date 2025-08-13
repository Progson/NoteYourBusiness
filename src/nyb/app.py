# src/nyb/app.py
from __future__ import annotations
from PyQt6.QtWidgets import QApplication
import sys

def run_gui():
    from nyb.gui.web_launcher import WebLauncherWindow  # <- NOWY
    app = QApplication.instance() or QApplication(sys.argv)
    win = WebLauncherWindow()
    win.show()
    app.exec()
