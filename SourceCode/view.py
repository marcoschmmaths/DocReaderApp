from PySide6.QtWidgets import QMainWindow ,QVBoxLayout ,QWidget , QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self):  # Corregir a __init__ (double underscores)
        super().__init__()
        self.setWindowTitle("DocReaderApp")
        layout = QVBoxLayout()
        self.viewer = QWebEngineView() #para epub o latex
        self.toolbar = QWidget()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.viewer)
        central_widget = QWidget()
        central_widget.setLayout(layout)
