# src/nyb/gui/web_pages/base.py
from __future__ import annotations
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

class ActionPage(QWebEnginePage):
    """Przechwytuje nyb://host/path i woła handler z okna."""
    def __init__(self, handler: Callable[[str, str | None], None], parent=None):
        super().__init__(parent)
        self._handler = handler

    def acceptNavigationRequest(self, url: QUrl, navtype, isMainFrame: bool) -> bool:
        if url.scheme().lower() == "nyb":
            host = url.host().lower()
            sub = url.path().lstrip("/").lower() or None
            self._handler(host, sub)
            return False
        return super().acceptNavigationRequest(url, navtype, isMainFrame)

class WebView(QWebEngineView):
    """QWebEngineView z wygodnymi helperami."""
    def __init__(self, handler: Callable[[str, str | None], None], parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setPage(ActionPage(handler, self))

    def load_file(self, path: Path, on_ready: Callable[[], None] | None = None):
        url = QUrl.fromLocalFile(str(path))
        self.load(url)
        if on_ready:
            # SingleShot, żeby nie dublować po przeładowaniu
            self.loadFinished.connect(lambda ok: on_ready() if ok else None,
                                      Qt.ConnectionType.SingleShotConnection)

    def js(self, code: str):
        self.page().runJavaScript(code)

    @staticmethod
    def q(s: str | Path) -> str:
        """Bezpieczny string do wstrzyknięcia w JS."""
        s = str(s).replace("\\", "\\\\").replace("`", "\\`").replace('"', '\\"')
        return f'"{s}"'
