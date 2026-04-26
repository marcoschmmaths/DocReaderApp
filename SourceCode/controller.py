import os
import shutil
from PySide6.QtWidgets import QFileDialog,QToolTip
from Services.latex_render import LatexRenderer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QPoint



class Controller:
    """
    Conecta la Vista y el Modelo.
    Maneja las acciones del usuario y actualiza la interfaz.
    """
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.latex_renderer = LatexRenderer()  # Servicio de renderizado
        self._pending_annotation_text = None
        self._current_popup = None

        # Conectar señales
        self._connect_signals()

        # Estado inicial
        self.view.show_library_view()
        self.load_library()

    def _connect_signals(self):
        """Conecta todas las señales de la interfaz a los métodos del controlador."""
        # Biblioteca
        self.view.open_button.clicked.connect(self.add_file_to_library)
        self.view.library_list.itemDoubleClicked.connect(self.open_selected_document)
        self.view.view_mode.currentIndexChanged.connect(self.view.set_library_view_mode)
        self.view.next_page_key.connect(self.go_to_next_page)
        self.view.prev_page_key.connect(self.go_to_prev_page)
        # Lector
        self.view.next_action.triggered.connect(self.go_to_next_page)
        self.view.prev_action.triggered.connect(self.go_to_prev_page)
        self.view.page_spin.valueChanged.connect(self.go_to_specific_page)
        self.view.back_action.triggered.connect(self.back_to_library)
        self.view.zoom_slider.valueChanged.connect(self._update_document_view)

        # Anotaciones antiguo
        #self.view.add_annotation_btn.clicked.connect(self.add_annotation)
        # Anotaciones
        self.view.add_annotation_btn.clicked.connect(self.on_add_annotation_clicked)
        self.view.page_label_reader.marker_clicked.connect(self.on_marker_clicked)
        self.view.page_label_reader.page_clicked.connect(self.on_page_clicked)
        #pasar de pagina por el teclado
        

    def load_library(self):
        """Carga los documentos desde el modelo y actualiza la vista de biblioteca."""
        documents = self.model.load_documents()
        thumbnails = [self.model.generate_thumbnail(doc) for doc in documents]
        self.view.update_library(documents, thumbnails)
        self.view.show_message(f"{len(documents)} documents in library.")

    def add_file_to_library(self):
        """Añade un nuevo documento a la biblioteca."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, "Add Document", "", "Documents (*.pdf *.epub *.djvu)"
        )
        if file_path:
            try:
                dest_path = os.path.join(self.model.documents_dir, os.path.basename(file_path))
                if not os.path.exists(dest_path):
                    shutil.copy(file_path, dest_path)
                    self.view.show_message(f"Added: {os.path.basename(file_path)}")
                    self.load_library()
                else:
                    self.view.show_message("File already exists in library.")
            except Exception as e:
                self.view.show_message(f"Error adding file: {e}")

    def open_selected_document(self, item):
        """Abre el documento seleccionado en la biblioteca."""
        file_name = item.text()
        if self.model.open_document(file_name):
            self.view.show_reader_view()
            self._update_document_view()
            self._update_annotations_view()
            self.view.show_message(f"Opened: {file_name}")
        else:
            self.view.show_message(f"Error opening {file_name}")

    def go_to_next_page(self):
        """Avanza a la página siguiente."""
        if self.model.next_page():
            self._update_document_view()

    def go_to_prev_page(self):
        """Retrocede a la página anterior."""
        if self.model.prev_page():
            self._update_document_view()

    def go_to_specific_page(self, page_value):
        """Salta a la página indicada por el spinbox (1‑based)."""
        if self.model.go_to_page(page_value - 1):
            self._update_document_view()


    def _show_annotation_popup(self, ann, global_pos):
        """Muestra un popup persistente con la anotación renderizada."""
        # Cerrar popup anterior si existe
        if self._current_popup:
            self._current_popup.close()
            self._current_popup.deleteLater()
            self._current_popup = None

        # Convertir el texto LaTeX a HTML
        html = self.latex_renderer.replace_latex_in_text(ann['text'])

        # Crear el popup
        popup = QWidget(self.view, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        popup.setAttribute(Qt.WA_ShowWithoutActivating)  # no roba foco
        popup.setStyleSheet("background: white; border: 1px solid #888; border-radius: 6px;")

        layout = QVBoxLayout(popup)
        layout.setContentsMargins(8, 4, 8, 8)

        # Barra superior con botón de cierre
        header = QHBoxLayout()
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("border: none; font-weight: bold; color: red;")
        close_btn.clicked.connect(popup.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Contenido de la anotación
        # Envolver el HTML en un div con estilo explícito para que el texto siempre se vea
        full_html = f"""<div style="
            font-family: sans-serif;
            font-size: 14px;
            color: #000;
            background: #fff;
            padding: 4px;
        ">{html}</div>"""
        label = QLabel(full_html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setOpenExternalLinks(False)
        label.setMaximumWidth(400)
        label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(label)

        popup.adjustSize()

        # Posicionar el popup cerca del marcador, ajustando a los bordes de la pantalla
        screen = self.view.screen().availableGeometry()
        x = global_pos.x() + 15
        y = global_pos.y() + 15
        if x + popup.width() > screen.right():
            x = screen.right() - popup.width()
        if y + popup.height() > screen.bottom():
            y = global_pos.y() - popup.height() - 15
        popup.move(x, y)

        # Conectar el cierre para limpiar la referencia
        def on_popup_closed():
            if self._current_popup == popup:
                self._current_popup = None
        popup.destroyed.connect(on_popup_closed)

        popup.show()
        self._current_popup = popup


    def on_add_annotation_clicked(self):
        """Se ejecuta al pulsar el botón de nueva anotación."""
        text = self.view.get_annotation_text().strip()
        if not text:
            self.view.show_message("Escribe primero el texto de la anotación.")
            return
        self._pending_annotation_text = text
        self.view.enter_annotation_placement_mode()

    def on_page_clicked(self, x, y):
        """Coloca la anotación pendiente en las coordenadas normalizadas (x,y)."""
        if self._pending_annotation_text is None:
            return

        success = self.model.add_annotation(self._pending_annotation_text, x=x, y=y)
        if success:
            self.view.clear_annotation_input()
            self.view.exit_annotation_placement_mode()
            self._pending_annotation_text = None
            self._update_annotations_view()
            self.view.show_message("Anotación colocada")
        else:
            self.view.show_message("Error al guardar la anotación")

    def on_marker_clicked(self, ann_id, global_pos):
        """Muestra la anotación en un popup persistente al hacer clic en su marcador."""
        ann = self.model.get_annotation_by_id(ann_id)
        if ann:
            self._show_annotation_popup(ann, global_pos)
    def _update_document_view(self):
        """
        Refresca la vista del lector: página actual, zoom y anotaciones.
        Se llama tras cualquier cambio de página o zoom.
        """
        if not self.model.doc:
            return

        zoom_level = self.view.zoom_slider.value() / 100.0
        pixmap = self.model.get_current_page_as_pixmap(zoom_factor=zoom_level)
        self.view.show_document_page(pixmap)
        self.view.update_page_info(self.model.current_page_num, self.model.total_pages)
        self._update_annotations_view()

    def _update_annotations_view(self):
        raw_annotations = self.model.get_annotations_for_current_page()
        # Enviar al visor de página (PageViewer)
        self.view.page_label_reader.set_annotations(raw_annotations)

        # Preparar HTML para el panel lateral
        processed = []
        for ann in raw_annotations:
            text = ann['text']
            html_text = self.latex_renderer.replace_latex_in_text(text)
            # Si tiene coordenadas, añadir información
            if ann.get('x') is not None and ann.get('y') is not None:
                coords = f"<small>({ann['x']:.2f}, {ann['y']:.2f})</small> "
            else:
                coords = ""
            processed.append(f"{coords}{html_text}")
        self.view.update_annotations_list(processed)

    def back_to_library(self):
        """Cierra el documento actual y regresa a la biblioteca."""
        if hasattr(self.model, 'doc') and self.model.doc:
            self.model.doc.close()
            self.model.doc = None
            self.model.current_file_path = None
            self.model.current_page_num = 0
            self.model.total_pages = 0

        self.view.show_library_view()
        self.load_library()