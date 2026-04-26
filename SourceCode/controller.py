import os
import shutil
from PySide6.QtWidgets import QFileDialog
from Services.latex_render import LatexRenderer # Placeholder for your LaTeX service

class Controller:
    """
    The controller connects the View and the Model.
    It handles user input from the View, processes it (using the Model
    if necessary), and updates the View with the results.
    """
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.latex_renderer = LatexRenderer()

        # Connect signals from the view to controller slots
        self._connect_signals()

        # Initial state setup
        self.view.show_library_view()
        self.load_library()

    def _connect_signals(self):
        """Central place to connect all UI signals to controller methods."""
        # Library controls
        self.view.open_button.clicked.connect(self.add_file_to_library)
        self.view.library_list.itemDoubleClicked.connect(self.open_selected_document)
        self.view.view_mode.currentIndexChanged.connect(self.view.set_library_view_mode)
        
        # Reader controls
        self.view.next_action.triggered.connect(self.go_to_next_page)
        self.view.prev_action.triggered.connect(self.go_to_prev_page)
        self.view.page_spin.valueChanged.connect(self.go_to_specific_page)
        self.view.back_action.triggered.connect(self.back_to_library)
        self.view.zoom_slider.valueChanged.connect(self._update_document_view)

        # Annotation controls
        self.view.add_annotation_btn.clicked.connect(self.add_annotation)

    def load_library(self):
        """Loads all documents from the model and updates the library view."""
        documents = self.model.load_documents()
        thumbnails = [self.model.generate_thumbnail(doc) for doc in documents]
        self.view.update_library(documents, thumbnails)
        self.view.show_message(f"{len(documents)} documents in library.")

    def add_file_to_library(self):
        """Opens a file dialog to add a new document to the library."""
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
        """Opens the document that the user double-clicked in the library."""
        file_name = item.text()
        if self.model.open_document(file_name):
            self.view.show_reader_view()
            self._update_document_view()
            self._update_annotations_view()
            self.view.show_message(f"Opened: {file_name}")
            
        else:
            self.view.show_message(f"Error opening {file_name}")

    def go_to_next_page(self):
        """Handles the 'next page' action."""
        if self.model.next_page():
            self._update_document_view()

    def go_to_prev_page(self):
        """Handles the 'previous page' action."""
        if self.model.prev_page():
            self._update_document_view()
    
    def go_to_specific_page(self, page_value):
        """Handles jumping to a page from the spinbox."""
        # QSpinBox value is 1-based, model is 0-based
        if self.model.go_to_page(page_value - 1):
            self._update_document_view()

    def add_annotation(self):
        """Handles adding a new annotation."""
        if not self.model.doc:
            self.view.show_message("No document open.")
            return

        text = self.view.get_annotation_text()
        if text.strip():
            # Here you could parse the text for LaTeX and render it
            # For now, we just add the raw text.
            if self.model.add_annotation(text):
                self.view.clear_annotation_input()
                self._update_annotations_view()
                self.view.show_message("Annotation added.")
            else:
                self.view.show_message("Failed to add annotation.")
        else:
            self.view.show_message("Annotation cannot be empty.")

    def _update_document_view(self):
        """
        A helper function to refresh the entire reader view.
        It's called after any action that changes the current page or zoom.
        """
        if not self.model.doc:
            return

        zoom_level = self.view.zoom_slider.value() / 100.0
        pixmap = self.model.get_current_page_as_pixmap(zoom_factor=zoom_level)
        
        self.view.show_document_page(pixmap)
        self.view.update_page_info(self.model.current_page_num, self.model.total_pages)
        self._update_annotations_view()

    def _update_annotations_view(self):
        """Refreshes the list of annotations for the current page."""
        annotations = self.model.get_annotations_for_current_page()
        self.view.update_annotations_list(annotations)
    
    def back_to_library(self):
        """Regresa a la vista de biblioteca"""
        # Cerrar el documento actual si está abierto
        if hasattr(self.model, 'doc') and self.model.doc:
            self.model.doc.close()
            self.model.doc = None
            self.model.current_file = None
    
        # Mostrar la vista de biblioteca
        self.view.show_library_view()
    
        # Recargar la biblioteca por si se añadieron nuevos documentos
        self.load_library()