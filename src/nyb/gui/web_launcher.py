# src/nyb/gui/web_launcher.py
from __future__ import annotations
from pathlib import Path

from PyQt6.QtWidgets import QMainWindow
from nyb.gui.web_pages.base import WebView
from nyb.gui.web_pages.encrypt import EncryptController
from nyb.gui.web_pages.decrypt import DecryptController

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets" / "gui"
LAUNCHER_HTML = ASSETS_DIR / "launcher.html"

class WebLauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteYourBusiness")
        self.resize(900, 658)

        self.view = WebView(self._handle_action, self)
        self.setCentralWidget(self.view)

        self.encrypt = EncryptController(self.view, self.load_page)
        self.decrypt = DecryptController(self.view, self.load_page)

        self.load_page("launcher")

    def load_page(self, name: str):
        if name == "launcher":
            self.view.load_file(LAUNCHER_HTML, self._bind_launcher)
        elif name == "encrypt":
            self.encrypt.load()
        elif name == "decrypt":
            self.decrypt.load()
        else:
            self.view.load_file(LAUNCHER_HTML, self._bind_launcher)

    def _bind_launcher(self):
        self.view.js("""
        (function(){
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
        """)

    def _handle_action(self, host: str, sub: str | None):
        if host == "launcher":
            self.load_page("launcher"); return
        if host == "encrypt":
            if sub is None: self.load_page("encrypt")
            else: self.encrypt.handle(sub)
            return
        if host == "decrypt":
            if sub is None: self.load_page("decrypt")
            else: self.decrypt.handle(sub)
            return
        # note/settings – backlog
        return

