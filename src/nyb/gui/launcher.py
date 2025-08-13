from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NoteYourBusiness")
        w = QWidget(self)
        lay = QVBoxLayout(w)
        self.btn_encrypt = QPushButton("Szyfruj pliki/folder")
        self.btn_decrypt = QPushButton("Odszyfruj pliki/folder")
        self.btn_note = QPushButton("Nowa notatka")
        self.btn_settings = QPushButton("Ustawienia")
        for b in (self.btn_encrypt, self.btn_decrypt, self.btn_note, self.btn_settings):
            lay.addWidget(b)
        self.setCentralWidget(w)
        # TODO: connect to dialogs
