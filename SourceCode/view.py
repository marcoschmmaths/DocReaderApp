from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QToolBar,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QLabel, QStatusBar,
    QSlider, QStackedWidget, QDockWidget, QTextEdit, QSpinBox, QScrollArea,
    QHBoxLayout, QSizePolicy,QTextBrowser
)
from PySide6.QtCore import Qt, QSize,Signal
from PySide6.QtGui import QIcon, QAction, QPixmap 

from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
from PySide6.QtCore import Qt, Signal, QPoint, QRect

class PageViewer(QLabel):
    """Muestra la página y los marcadores de anotaciones."""
    marker_clicked = Signal(int, QPoint)   # id y posición global del marcador
    page_clicked = Signal(float, float)  # coordenadas normalizadas (0-1)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.annotations = []  # lista de dicts: id, text, x, y
        self.add_annotation_mode = False
        self.setMouseTracking(True)

    def set_annotations(self, annotations):
        self.annotations = annotations
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap() or self.pixmap().isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pw = self.pixmap().width()
        ph = self.pixmap().height()

        for ann in self.annotations:
            x = ann.get('x')
            y = ann.get('y')
            if x is None or y is None:
                continue
            px = x * pw
            py = y * ph

            # Círculo semitransparente rojo
            painter.setBrush(QColor(255, 0, 0, 120))   # rojo con alfa 120
            painter.setPen(QPen(QColor(180, 0, 0), 1))  # borde más oscuro
            radius = 5
            painter.drawEllipse(QPoint(int(px), int(py)), radius, radius)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()

            # Primero comprobamos si se hizo clic sobre un marcador existente
            hit_id = self._hit_test(pos)
            if hit_id is not None:
                # Calcular la posición global del centro del marcador
                pw = self.pixmap().width()
                ph = self.pixmap().height()
                for ann in self.annotations:
                    if ann['id'] == hit_id:
                        x = ann.get('x', 0)
                        y = ann.get('y', 0)
                        px = x * pw
                        py = y * ph
                        # Convertir las coordenadas locales (respecto a la imagen) a globales
                        global_pt = self.mapToGlobal(QPoint(int(px), int(py)))
                        self.marker_clicked.emit(hit_id, global_pt)
                        return

                # Por si acaso no encuentra el dict (no debería ocurrir)
                self.marker_clicked.emit(hit_id, self.mapToGlobal(QPoint(0, 0)))
                return

            # Si no es un marcador y estamos en modo añadir, emitimos las coordenadas normalizadas
            if self.add_annotation_mode and self.pixmap():
                pw = self.pixmap().width()
                ph = self.pixmap().height()
                if pw > 0 and ph > 0:
                    nx = pos.x() / pw
                    ny = pos.y() / ph
                    if 0.0 <= nx <= 1.0 and 0.0 <= ny <= 1.0:
                        self.page_clicked.emit(nx, ny)
                        return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.add_annotation_mode:
            self.setCursor(Qt.CrossCursor)
        else:
            # Cambiar cursor al pasar sobre un marcador
            pos = event.position().toPoint()
            if self._hit_test(pos) is not None:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def _hit_test(self, point):
        """Devuelve el id del marcador bajo el punto, o None."""
        if not self.pixmap():
            return None
        pw = self.pixmap().width()
        ph = self.pixmap().height()
        for ann in self.annotations:
            x = ann.get('x')
            y = ann.get('y')
            if x is None or y is None:
                continue
            px = x * pw
            py = y * ph
            if (point.x() - px) ** 2 + (point.y() - py) ** 2 <= 8 ** 2:  # radio de 15 px
                return ann['id']
        return None


class MainView(QMainWindow):
    """
    Interfaz de usuario principal.
    No contiene lógica de aplicación; solo crea y muestra los widgets.
    Compatible con Android y Windows al usar QLabel para mostrar páginas.
    """
    next_page_key = Signal()
    prev_page_key = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocReader")
        self.resize(1200, 800)

        # Configuración central
        self.setup_toolbar()
        self.setup_central_widget()        # solo el QStackedWidget
        self.setup_library_view()
        self.setup_reader_view()           # crea el reader y su toolbar
        self.setup_annotation_dock()
        self.setup_status_bar()

        # Estado inicial
        self.show_library_view()
        self.installEventFilter(self)
        from PySide6.QtWidgets import QApplication
        QApplication.instance().installEventFilter(self)



    def eventFilter(self, obj, event):
        """Captura teclas de flecha cuando el lector está activo."""
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.KeyPress:
            if self.stacked_widget.currentWidget() == self.reader_widget:
                if event.key() == Qt.Key_Right:
                    self.next_page_key.emit()
                    return True   # evento consumido
                elif event.key() == Qt.Key_Left:
                    self.prev_page_key.emit()
                    return True
        # Para Arriba/Abajo y demás, comportamiento normal
        return super().eventFilter(obj, event)
    # ------------------------------------------------------------------
    # Configuración de los componentes principales
    # ------------------------------------------------------------------
    def setup_toolbar(self):
        """Barra superior con acción de añadir y búsqueda."""
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
        """Contenedor principal que alterna entre biblioteca y lector."""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

    def setup_library_view(self):
        """Vista de biblioteca con lista de documentos."""
        self.library_widget = QWidget()
        library_layout = QVBoxLayout()
        self.library_list = QListWidget()
        library_layout.addWidget(self.library_list)
        self.library_widget.setLayout(library_layout)
        self.stacked_widget.addWidget(self.library_widget)
        self.set_library_view_mode(0)  # Grid por defecto

    def setup_reader_view(self):
        """
        Vista de lectura:
        - QScrollArea con QLabel para mostrar la página (compatible con Android)
        - Barra de herramientas inferior (QToolBar) con navegación y zoom
        """
        # Widget contenedor del lector
        self.reader_widget = QWidget()
        reader_layout = QVBoxLayout(self.reader_widget)
        reader_layout.setContentsMargins(0, 0, 0, 0)

        # Área de desplazamiento para la imagen de la página
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        #self.page_label_reader = QLabel("No page loaded")
        #self.page_label_reader.setAlignment(Qt.AlignCenter)
        #self.page_label_reader.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.page_label_reader = PageViewer(self)
        self.page_label_reader.setAlignment(Qt.AlignCenter)
        self.page_label_reader.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.scroll_area.setWidget(self.page_label_reader)

        reader_layout.addWidget(self.scroll_area, stretch=1)

        # Añadir el lector al stacked widget
        self.stacked_widget.addWidget(self.reader_widget)

        # Crear la barra de herramientas inferior (separada, se añade a la ventana)
        self.reader_toolbar = QToolBar("Reader Toolbar")
        self.addToolBar(Qt.BottomToolBarArea, self.reader_toolbar)

        # Botón de regreso a la biblioteca
        self.back_action = QAction("← Biblioteca", self)
        self.reader_toolbar.addAction(self.back_action)
        self.reader_toolbar.addSeparator()

        # Navegación: anterior, página actual, siguiente
        self.prev_action = QAction("◀ Anterior", self)
        self.reader_toolbar.addAction(self.prev_action)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setValue(1)
        self.page_spin.setMinimumWidth(80)
        self.reader_toolbar.addWidget(self.page_spin)

        self.page_label = QLabel("/ 1")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(80)
        self.reader_toolbar.addWidget(self.page_label)

        self.next_action = QAction("Siguiente ▶", self)
        self.reader_toolbar.addAction(self.next_action)
        self.reader_toolbar.addSeparator()

        # Zoom
        self.zoom_label_widget = QLabel("Zoom:")
        self.reader_toolbar.addWidget(self.zoom_label_widget)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 300)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        self.reader_toolbar.addWidget(self.zoom_slider)

        # Ocultar la barra hasta que se abra un documento
        self.reader_toolbar.setVisible(False)

    def setup_annotation_dock(self):
        """Panel lateral para crear y ver anotaciones con soporte HTML/LaTeX."""
        self.annotation_dock = QDockWidget("Annotations", self)
        widget = QWidget()
        layout = QVBoxLayout()

        self.annotation_input = QTextEdit()
        self.annotation_input.setPlaceholderText("Write notes here. Use $$ for LaTeX.")

        self.add_annotation_btn = QPushButton("Add Annotation")
        self.annotations_browser = QTextBrowser()  # Soporta HTML
        self.annotations_browser.setOpenExternalLinks(False)
        self.annotations_browser.setPlaceholderText("No annotations for this page")

        layout.addWidget(QLabel("New Annotation:"))
        layout.addWidget(self.annotation_input)
        layout.addWidget(self.add_annotation_btn)
        layout.addSpacing(10)
        layout.addWidget(QLabel("Annotations for this page:"))
        layout.addWidget(self.annotations_browser)

        widget.setLayout(layout)
        self.annotation_dock.setWidget(widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.annotation_dock)
        self.annotation_dock.hide()

    def setup_status_bar(self):
        """Barra de estado inferior."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.show_message("Welcome to DocReader")

    # ------------------------------------------------------------------
    # Métodos de utilidad para actualizar la interfaz
    # ------------------------------------------------------------------
    def show_message(self, message, timeout=4000):
        self.status_bar.showMessage(message, timeout)

    # ------------------------------------------------------------------
    # Cambio de vistas
    # ------------------------------------------------------------------
    def show_library_view(self):
        """Muestra la biblioteca y oculta el lector."""
        self.stacked_widget.setCurrentWidget(self.library_widget)
        self.annotation_dock.hide()
        self.reader_toolbar.setVisible(False)

    def show_reader_view(self):
        """Muestra el lector, la barra de herramientas y el dock de anotaciones."""
        self.stacked_widget.setCurrentWidget(self.reader_widget)
        self.annotation_dock.show()
        self.reader_toolbar.setVisible(True)
        self.scroll_area.setFocus()

    # ------------------------------------------------------------------
    # Actualización de la biblioteca
    # ------------------------------------------------------------------
    def update_library(self, documents, thumbnails):
        self.library_list.clear()
        for doc, thumb in zip(documents, thumbnails):
            item = QListWidgetItem(QIcon(thumb), doc)
            self.library_list.addItem(item)

    def set_library_view_mode(self, index):
        if index == 0:  # Grid
            self.library_list.setViewMode(QListWidget.IconMode)
            self.library_list.setIconSize(QSize(120, 180))
            self.library_list.setGridSize(QSize(150, 210))
        else:           # List
            self.library_list.setViewMode(QListWidget.ListMode)
            self.library_list.setIconSize(QSize(40, 60))

    # ------------------------------------------------------------------
    # Actualización del visor de páginas (QLabel)
    # ------------------------------------------------------------------
    def show_document_page(self, pixmap):
        """
        Muestra un QPixmap en el QLabel. Si el pixmap es None,
        se muestra un mensaje de error.
        """
        if not pixmap or pixmap.isNull():
            self.page_label_reader.setText("Error loading page")
            return

        self.page_label_reader.setPixmap(pixmap)
        # Permite que el label se ajuste al tamaño de la imagen
        self.page_label_reader.setScaledContents(False)
        self.page_label_reader.setFixedSize(pixmap.size())

        # Reiniciar el desplazamiento al origen (esquina superior izquierda)
        self.scroll_area.verticalScrollBar().setValue(0)
        self.scroll_area.horizontalScrollBar().setValue(0)

    # ------------------------------------------------------------------
    # Información de página en la barra de herramientas
    # ------------------------------------------------------------------
    def update_page_info(self, current_page, total_pages):
        """Actualiza el SpinBox y la etiqueta de páginas."""
        # Bloquear señales para evitar llamadas cíclicas
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(current_page + 1)  # La vista usa 1‑based
        self.page_spin.blockSignals(False)
        self.page_label.setText(f"/ {total_pages}")

    # ------------------------------------------------------------------
    # Anotaciones
    # ------------------------------------------------------------------
    def update_annotations_list(self, processed_annotations):
        """
        Recibe una lista de strings HTML (ya procesados con LaTeX) y los muestra.
        """
        if not processed_annotations:
            self.annotations_browser.setHtml("<p style='color:gray;'>No hay anotaciones aún.</p>")
            return

        html_parts = ["<div style='font-family: sans-serif;'>"]
        for ann_html in processed_annotations:
            html_parts.append(f"<p style='margin: 8px 0;'>{ann_html}</p>")
        html_parts.append("</div>")
        self.annotations_browser.setHtml("".join(html_parts))

    def get_annotation_text(self):
        return self.annotation_input.toPlainText()

    def clear_annotation_input(self):
        self.annotation_input.clear()
    
    def enter_annotation_placement_mode(self):
        self.page_label_reader.add_annotation_mode = True
        self.add_annotation_btn.setText("Colocar en página...")
        self.show_message("Haz clic en la página para colocar la anotación")

    def exit_annotation_placement_mode(self):
        self.page_label_reader.add_annotation_mode = False
        self.add_annotation_btn.setText("Add Annotation")
        self.show_message("")