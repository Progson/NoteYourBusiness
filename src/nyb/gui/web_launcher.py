# src/nyb/gui/web_launcher.py
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage  # <-- WAŻNE: z QtWebEngineCore!
from PyQt6.QtCore import QUrl, Qt

from nyb.gui.encrypt_wizard import EncryptDialog
from nyb.gui.decrypt_wizard import DecryptDialog

# ładujemy launcher.html (zmieniona nazwa pliku startowego)
ASSETS_HTML = Path(__file__).resolve().parents[1] / "assets" / "gui" / "launcher.html"


class _ActionPage(QWebEnginePage):
    """
    Przechwytuje nawigacje typu:
      nyb://encrypt | nyb://decrypt | nyb://note | nyb://settings
    i woła odpowiednie akcje w oknie.
    """
    def __init__(self, parent_window: "WebLauncherWindow"):
        super().__init__(parent_window)
        self._win = parent_window

    # sygnatura pod PyQt6
    def acceptNavigationRequest(self, url: QUrl, navtype, isMainFrame: bool) -> bool:
        if url.scheme().lower() == "nyb":
            action = url.host().lower() or url.path().lstrip("/").lower()
            self._win.handle_action(action)
            return False  # nie nawiguj
        return super().acceptNavigationRequest(url, navtype, isMainFrame)


class WebLauncherWindow(QMainWindow):
    """
    Launcher HTML (2×2 kafelki) w QWebEngineView.
    Kliknięcia kafelków przechwytujemy przez schemat 'nyb://...'.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteYourBusiness")
        self.resize(900, 658)

        self.view = QWebEngineView(self)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        page = _ActionPage(self)
        self.view.setPage(page)

        # Wstrzykuj JS, który podpina akcje do przycisków
        def _inject_bindings(ok: bool):
            if not ok:
                return
            js = """
            (function(){
                document.body.classList.add('allow-motion');   // <-- NAJWAŻNIEJSZE
                const bind = (cls, action) => {
                    const btn = document.querySelector('.' + cls + ' .btn');
                    if(!btn) return;
                    btn.addEventListener('click', (e) => {
                        e.preventDefault();
                        window.location.href = 'nyb://' + action;
                    }, {once:false});
                };
                bind('encrypt','encrypt');
                bind('decrypt','decrypt');
                bind('note','note');
                bind('settings','settings');
            })();
            """
            self.view.page().runJavaScript(js)

        self.view.loadFinished.connect(_inject_bindings)

        # Załaduj lokalny launcher.html
        url = QUrl.fromLocalFile(str(ASSETS_HTML))
        self.view.load(url)
        self.setCentralWidget(self.view)

    # --- akcje z HTML ---

    def handle_action(self, action: str):
        if action == "encrypt":
            dlg = EncryptDialog(self)
            dlg.resize(900, 600)
            dlg.exec()
        elif action == "decrypt":
            dlg = DecryptDialog(self)
            dlg.resize(900, 600)
            dlg.exec()
        elif action == "note":
            # TODO: edytor notatek w HTML lub PyQt
            pass
        elif action == "settings":
            # TODO: settings dialog / HTML
            pass
