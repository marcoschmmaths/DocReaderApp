from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QToolBar,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QLabel, QStatusBar,
    QSlider, QStackedWidget, QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocReaderApp - Inspired by ReadEra")
        self.resize(800, 600)

        # Estilos básicos (claro por default, como ReadEra)
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QLabel { color: #000; }
        """)

        # Toolbar superior (búsqueda y acciones)
        self.toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.open_button = QPushButton("Abrir Archivo")
        self.toolbar.addWidget(self.open_button)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar en biblioteca...")
        self.toolbar.addWidget(self.search_bar)

        self.view_mode = QComboBox()
        self.view_mode.addItems(["Lista", "Grid"])
        self.toolbar.addWidget(self.view_mode)

        # Stacked widget para biblioteca y lector
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Página 1: Biblioteca
        self.library_widget = QWidget()
        library_layout = QVBoxLayout()
        self.library_list = QListWidget()
        self.library_list.setViewMode(QListWidget.IconMode)  # Grid default
        self.library_list.setIconSize(QSize(100, 150))
        self.library_list.setResizeMode(QListWidget.Adjust)
        library_layout.addWidget(self.library_list)
        self.library_widget.setLayout(library_layout)
        self.stacked_widget.addWidget(self.library_widget)

        # Página 2: Vista de lectura
        self.reader_widget = QWidget()
        reader_layout = QVBoxLayout()

        self.viewer = QWebEngineView()  # Para EPUB/HTML; usa QLabel para PDF si necesitas
        reader_layout.addWidget(self.viewer)

        # Controles inferiores
        bottom_toolbar = QWidget()
        bottom_layout = QVBoxLayout()
        self.page_label = QLabel("Página 1 / 1")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.annotate_button = QPushButton("Anotar")
        bottom_layout.addWidget(self.page_label)
        bottom_layout.addWidget(self.zoom_slider)
        bottom_layout.addWidget(self.annotate_button)
        bottom_toolbar.setLayout(bottom_layout)
        reader_layout.addWidget(bottom_toolbar)

        self.reader_widget.setLayout(reader_layout)
        self.stacked_widget.addWidget(self.reader_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Bienvenido a DocReaderApp")

    def update_library(self, documents, thumbnails):
        """Actualiza lista de biblioteca con thumbnails"""
        self.library_list.clear()
        for doc, thumb in zip(documents, thumbnails):
            item = QListWidgetItem(QIcon(thumb), doc)
            self.library_list.addItem(item)

    def show_document(self, content):
        """Muestra contenido en el visor"""
        self.stacked_widget.setCurrentIndex(1)
        self.viewer.setHtml(content)

    def update_zoom(self, value):
        self.viewer.setZoomFactor(value / 100.0)
        self.status_bar.showMessage(f"Zoom: {value}%")

    def show_message(self, message):
        self.status_bar.showMessage(message)