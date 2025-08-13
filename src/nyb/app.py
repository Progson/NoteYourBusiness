from PyQt6.QtWidgets import QApplication
import sys
from nyb.gui.launcher import LauncherWindow

def run_gui() -> None:
    app = QApplication(sys.argv)
    w = LauncherWindow()
    w.show()
    sys.exit(app.exec())
