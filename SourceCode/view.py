from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QToolBar,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QLabel, QStatusBar,
    QSlider, QStackedWidget, QDockWidget, QTextEdit, QSpinBox,QHBoxLayout,QTextBrowser,QFrame, QSizePolicy
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QSize, QBuffer
from PySide6.QtGui import QIcon, QAction
import base64
from io import BytesIO

class MainView(QMainWindow):
    """
    Handles the user interface of the application.
    It creates all the widgets and layouts, but contains no application logic.
    The Controller will interact with it to update what the user sees.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocReader")
        self.resize(1200, 800)

        # Main UI setup
        self.setup_toolbar()
        self.setup_central_widget()
        self.setup_annotation_dock()
        self.setup_status_bar()
        self.setup_library_view()
        self.setup_reader_view()
        
    def setup_library_view(self):
        self.library_widget = QWidget()
        library_layout = QVBoxLayout()
        self.library_list = QListWidget()
        library_layout.addWidget(self.library_list)
        self.library_widget.setLayout(library_layout)
        self.stacked_widget.addWidget(self.library_widget)
        self.set_library_view_mode(0) # Default to Grid


    def setup_reader_view(self):
        """Configura la interfaz de visualización de documentos"""
        # Widget principal para la vista de lectura
        self.reader_widget = QWidget()
        self.reader_layout = QVBoxLayout(self.reader_widget)
        self.reader_layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins to prevent gaps/overlaps

        # Visor de documentos (QWebEngineView para compatibilidad)
        self.viewer = QWebEngineView()
        self.viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reader_layout.addWidget(self.viewer, stretch=1)  # Stretch to fill space without overlapping toolbar

        # Barra de herramientas inferior (usando QToolBar para docking y no overlap)
        self.reader_toolbar = QToolBar("Reader Toolbar")
        self.addToolBar(Qt.BottomToolBarArea, self.reader_toolbar)  # Dock at bottom to avoid overlap with central

        # Botón para regresar a la biblioteca
        self.back_action = QAction("← Biblioteca", self)
        self.reader_toolbar.addAction(self.back_action)

        self.reader_toolbar.addSeparator()

        # Botones de navegación
        self.prev_action = QAction("◀ Anterior", self)
        self.reader_toolbar.addAction(self.prev_action)

        # Etiqueta de página consolidada (muestra "Página X de Y")
        self.page_label = QLabel("Página 1 de 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(150)
        self.page_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")  # Visible styling
        self.reader_toolbar.addWidget(self.page_label)

        self.next_action = QAction("Siguiente ▶", self)
        self.reader_toolbar.addAction(self.next_action)

        self.reader_toolbar.addSeparator()

        # Zoom
        self.zoom_label = QLabel("Zoom:")
        self.reader_toolbar.addWidget(self.zoom_label)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 300)  # 50% to 300%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.reader_toolbar.addWidget(self.zoom_slider)

        # Añadir reader_widget al stacked
        self.stacked_widget.addWidget(self.reader_widget)

        # Inicialmente ocultar toolbar de reader
        self.reader_toolbar.setVisible(False)

    def setup_toolbar(self):
        """Creates the top toolbar with actions."""
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.open_button = QPushButton("Add File to Library")
        self.toolbar.addWidget(self.open_button)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search in library...")
        self.toolbar.addWidget(self.search_bar)

        self.toolbar.addSeparator()

        self.view_mode_label = QLabel("View:")
        self.toolbar.addWidget(self.view_mode_label)
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Grid", "List"])
        self.toolbar.addWidget(self.view_mode)

    def setup_central_widget(self):
        """Sets up the stacked widget for switching between library and reader."""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Reader View
        self.reader_widget = QWidget()
        reader_layout = QVBoxLayout()
        self.viewer = QWebEngineView()
        self.setup_reader_toolbar()
        reader_layout.addWidget(self.viewer)
        reader_layout.addWidget(self.reader_toolbar)
        self.reader_widget.setLayout(reader_layout)
        self.stacked_widget.addWidget(self.reader_widget)

    def setup_reader_toolbar(self):
        """Creates the bottom toolbar for navigation and zoom inside the reader."""
        self.reader_toolbar = QToolBar("Reader Toolbar")
        
        self.prev_btn = QAction(QIcon.fromTheme("go-previous"), "Previous Page", self)
        self.reader_toolbar.addAction(self.prev_btn)
        
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.reader_toolbar.addWidget(self.page_spin)

        self.page_label = QLabel("/ 1")
        self.reader_toolbar.addWidget(self.page_label)

        self.next_btn = QAction(QIcon.fromTheme("go-next"), "Next Page", self)
        self.reader_toolbar.addAction(self.next_btn)

        self.reader_toolbar.addSeparator()

        self.zoom_label = QLabel("Zoom:")
        self.reader_toolbar.addWidget(self.zoom_label)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 300) # 50% to 300%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.reader_toolbar.addWidget(self.zoom_slider)

    def setup_annotation_dock(self):
        """Creates the side panel for writing and viewing annotations."""
        self.annotation_dock = QDockWidget("Annotations", self)
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.annotation_input = QTextEdit()
        self.annotation_input.setPlaceholderText("Write notes here. Use $$ for LaTeX.")
        
        self.add_annotation_btn = QPushButton("Add Annotation")
        
        self.annotations_list = QListWidget()
        
        layout.addWidget(QLabel("New Annotation:"))
        layout.addWidget(self.annotation_input)
        layout.addWidget(self.add_annotation_btn)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Annotations for this page:"))
        layout.addWidget(self.annotations_list)
        
        widget.setLayout(layout)
        self.annotation_dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.annotation_dock)

    def setup_status_bar(self):
        """Creates the status bar at the bottom of the window."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.show_message("Welcome to DocReader")

    def show_message(self, message, timeout=4000):
        """Displays a message in the status bar for a specified time (in ms)."""
        self.status_bar.showMessage(message, timeout)

    def show_library_view(self):
        """Switches the main view to the library."""
        self.stacked_widget.setCurrentWidget(self.library_widget)
        self.annotation_dock.hide()

    def show_reader_view(self):
        """Switches the main view to the document reader."""
        self.stacked_widget.setCurrentWidget(self.reader_widget)
        self.annotation_dock.show()

    def update_library(self, documents, thumbnails):
        """Populates the library list with documents and their thumbnails."""
        self.library_list.clear()
        for doc, thumb in zip(documents, thumbnails):
            item = QListWidgetItem(QIcon(thumb), doc)
            self.library_list.addItem(item)

    def set_library_view_mode(self, index):
        """Switches the library between Grid (0) and List (1) mode."""
        if index == 0:  # Grid
            self.library_list.setViewMode(QListWidget.IconMode)
            self.library_list.setIconSize(QSize(120, 180))
            self.library_list.setGridSize(QSize(150, 210))
        else:  # List
            self.library_list.setViewMode(QListWidget.ListMode)
            self.library_list.setIconSize(QSize(40, 60))

    def show_document_page(self, pixmap):
        """Renders a QPixmap in the web viewer."""
        if not pixmap:
            self.viewer.setHtml("<h1>Error loading page</h1>")
            return
        
        # Use QBuffer to save the pixmap (compatible with QIODevice)
        buffer = QBuffer()
        buffer.open(QBuffer.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()

        # Get the byte data and encode to base64
        base64_data = base64.b64encode(buffer.data()).decode('utf-8')
        
        # Display the image in a simple, centered HTML page
        html_content = f"""
        <html><body style='background-color:#7F7F7F; text-align:center;'>
            <img src='data:image/png;base64,{base64_data}'>
        </body></html>
        """
        self.viewer.setHtml(html_content)

    def update_page_info(self, current_page, total_pages):
        """Updates the page number display in the reader toolbar."""
        # Block signals to prevent feedback loop with controller
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(current_page + 1)
        self.page_spin.blockSignals(False)
        self.page_label.setText(f"/ {total_pages}")

    def update_annotations_list(self, annotations):
        """Updates the list of annotations in the dock."""
        self.annotations_list.clear()
        for annotation in annotations:
            item = QListWidgetItem(annotation)
            self.annotations_list.addItem(item)

    def get_annotation_text(self):
        """Returns the text from the annotation input box."""
        return self.annotation_input.toPlainText()

    def clear_annotation_input(self):
        """Clears the annotation input box."""
        self.annotation_input.clear()

    def show_reader_view(self):
        """Muestra la vista de lectura"""
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setCurrentWidget(self.reader_widget)
        else:
            # Alternativa si no usas stacked widget
            self.library_widget.hide()
            self.reader_widget.show()
    
        #Asegurarse de que la barra de herramientas sea visible
        self.reader_toolbar.setVisible(True)

    def show_library_view(self):
        """Muestra la vista de biblioteca"""
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setCurrentWidget(self.library_widget)
        else:
            # Alternativa si no usas stacked widget
            self.reader_widget.hide()
            self.library_widget.show()