import fitz  # PyMuPDF
import os
import traceback
from PySide6.QtGui import QPixmap, QImage
import sqlite3

class DocumentModel:
    """
    Manages all data and business logic for the application.
    It handles loading documents, page navigation, and annotations.
    It is completely independent of the user interface.
    """

    def __init__(self):
        self.documents_dir = "documents/"
        if not os.path.exists(self.documents_dir):
            os.makedirs(self.documents_dir)
            
        self.db_path = "databases/annotations.db"
        self._init_database()
        self.doc = None
        self.current_file_path = None
        self.current_page_num = 0
        self.total_pages = 0
        self.annotations = {}  # Using a dict to store annotations per file

    def _init_database(self):
        """Inicializa la base de datos SQLite y crea la tabla si no existe."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                page INTEGER,
                text TEXT
            )
        """)

        """
        CODIGO PARA VER LA ESTRUCTURA Y CONTENIDO DE LA DB EN CONSOLA
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"\n=== Estructura de la tabla '{table_name}' ===")

             # Obtener información de las columnas
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = self.cursor.fetchall()
            print("Columnas:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Obtener el contenido de la tabla
            print(f"\nContenido de '{table_name}':")
            self.cursor.execute(f"SELECT * FROM {table_name};")
            rows = self.cursor.fetchall()
            
            if rows:
                # Mostrar nombres de columnas
                col_names = [description[0] for description in self.cursor.description]
                print(" | ".join(col_names))
                print("-" * 50)
                
                # Mostrar filas
                for row in rows:
                    print(" | ".join(str(value) for value in row))
            else:
                print("(La tabla está vacía)")
        """
        self.conn.commit()
        self.conn.close()

    def load_documents(self):
        """Returns a list of document filenames in the library directory."""
        return [f for f in os.listdir(self.documents_dir) if f.lower().endswith((".pdf", ".epub", ".djvu"))]

    def generate_thumbnail(self, file_name):
        """Generates a QPixmap thumbnail for the first page of a document."""
        file_path = os.path.join(self.documents_dir, file_name)
        try:
            if file_path.lower().endswith(".pdf"):
                doc = fitz.open(file_path)
                page = doc[0]
                # Render at a smaller size for performance
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                doc.close()
                return QPixmap.fromImage(img)
        except Exception as e:
            print(f"Error generating thumbnail for {file_name}: {e}")
        
        # Return a default cover for non-PDFs or on error
        return QPixmap("assets/default_cover.png")

    def open_document(self, file_name):
        """Loads a document into memory for reading."""
        file_path = os.path.join(self.documents_dir, file_name)
        self.annotations[file_name] = []
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return False

        try:
            # Close any previously opened document
            if self.doc:
                self.doc.close()

            if file_path.lower().endswith(".pdf"):
                self.doc = fitz.open(file_path)
                self.current_file_path = file_path
                self.total_pages = len(self.doc)
                self.current_page_num = 0
                return True
            # TODO: Add logic for EPUB and DJVU files here
            else:
                print(f"Unsupported file type: {file_name}")
                return False

        except Exception as e:
            traceback.print_exc()
            self.doc = None
            return False
    def _load_annotations(self, file_name):
        """Carga anotaciones desde la DB para el documento actual."""

        if not self.current_file_path:
            return
        file_name = os.path.basename(self.current_file_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT page, text FROM annotations 
            WHERE file_name = ? 
            ORDER BY page
        """, (file_name,))
        rows = cursor.fetchall()
        conn.close()

        self.annotations[file_name] = [{"page": page, "text": text} for page, text in rows]
        print(f"Cargadas {len(self.annotations[file_name])} anotaciones para {file_name}")
            
    def get_current_page_as_pixmap(self, zoom_factor=2.0):
        """
        Renders the current page of the loaded document as a QPixmap.
        Separates data retrieval (the page) from its presentation.
        """
        if not self.doc:
            return None
        try:
            page = self.doc.load_page(self.current_page_num)
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            return QPixmap.fromImage(img)
        except Exception as e:
            traceback.print_exc()
            return None

    def next_page(self):
        """Advances to the next page if possible."""
        if self.doc and self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            return True
        return False

    def prev_page(self):
        """Goes back to the previous page if possible."""
        if self.doc and self.current_page_num > 0:
            self.current_page_num -= 1
            return True
        return False

    def go_to_page(self, page_number):
        """Jumps to a specific page number (0-indexed)."""
        if self.doc and 0 <= page_number < self.total_pages:
            self.current_page_num = page_number
            return True
        return False

    def add_annotation(self, text):
        """Adds an annotation for the current page of the current file and saves to DB."""
        if not self.current_file_path:
            return False
        
        filename = os.path.basename(self.current_file_path)
        page = self.current_page_num
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO annotations (file_name, page, text) 
                VALUES (?, ?, ?)
            """, (filename, page, text))
            conn.commit()
            conn.close()
            
            # Actualizar cache local
            self.annotations[filename].append({"page": page, "text": text})
            print(f"Anotación agregada y guardada en DB para {filename} en página {page}: {text}")
            return True
        except Exception as e:
            print(f"Error guardando anotación: {e}")
            return False

    def get_annotations_for_current_page(self):
        """Retrieves all annotations for the current file and page."""
        if not self.current_file_path:
            return []
            
        file_name = os.path.basename(self.current_file_path)
        self._load_annotations(file_name)
        if file_name not in self.annotations:
            print(f"No hay anotaciones cargadas para {file_name}, cargando desde DB...")
            return []
        current_annotations = []
        for ann in self.annotations[file_name]:
            try:
                if ann['page'] == self.current_page_num:
                    current_annotations.append(ann['text'])
            except:
                print('an exception was made, ann = ',ann )
        
        return current_annotations


