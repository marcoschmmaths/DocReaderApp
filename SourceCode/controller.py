import model
import os 
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QFileDialog

class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # Conectar eventos de la vista al controlador
        self.view.open_button.clicked.connect(self.open_file)
        self.view.view_mode.currentIndexChanged.connect(self.update_library_view)
        self.view.library_list.itemDoubleClicked.connect(self.open_selected_document)
        self.view.zoom_slider.valueChanged.connect(self.view.update_zoom)
        self.view.annotate_button.clicked.connect(self.add_annotation)  # Placeholder

        # Cargar biblioteca inicial
        self.load_library()

    def load_library(self):
        documents = self.model.load_documents()
        thumbnails = [self.model.generate_thumbnail(doc) for doc in documents]
        self.view.update_library(documents, thumbnails)

    def update_library_view(self, index):
        if index == 0:  # Lista
            self.view.library_list.setViewMode(self.view.library_list.ListMode)
            self.view.library_list.setIconSize(QSize(50, 50))
        else:  # Grid
            self.view.library_list.setViewMode(self.view.library_list.IconMode)
            self.view.library_list.setIconSize(QSize(100, 150))

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Abrir Documento", "", "Documentos (*.pdf *.epub *.djvu)")
        if file_path:
            # Copiar a documents/ si no está (simplificado)
            import shutil
            dest = os.path.join(self.model.documents_dir, os.path.basename(file_path))
            shutil.copy(file_path, dest)
            self.load_library()  # Recargar biblioteca
            self.view.show_message(f"Archivo agregado: {file_path}")

    def open_selected_document(self, item):
        content = self.model.load_document(item.text())
        self.view.show_document(content)
        self.view.show_message(f"Abierto: {item.text()}")

    def add_annotation(self):
        self.view.show_message("Función de anotación en desarrollo (Fase 3)...")

