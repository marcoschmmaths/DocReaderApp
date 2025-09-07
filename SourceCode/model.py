import fitz 
from epub import open_epub
import os
from PySide6.QtGui import QPixmap, QImage


class DocumentModel:
    """esta clase puede implementarse de 2 formas distintas, la primera pidiendo el path del archivo
    y la segunda haciendo una carpeta con los archivos como esta sugiriendo grok (la segunda
    permite interfaz estilo readera asi que la implemento asi)"""
    def __init__(self):
        self.documents_dir = "documents/"  # Carpeta para biblioteca
        if not os.path.exists(self.documents_dir):
            os.makedirs(self.documents_dir)
        self.current_file = None
        self.doc = None
        self.annotations = []

    def load_documents(self):
        """Retorna lista de documentos para la biblioteca"""
        return [f for f in os.listdir(self.documents_dir) if f.endswith((".pdf", ".epub", ".djvu"))]

    def generate_thumbnail(self, file_name):
        """Genera thumbnail de la primera página"""
        file_path = os.path.join(self.documents_dir, file_name)
        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2))  # Baja resolución
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            return QPixmap.fromImage(img)
        elif file_path.endswith(".epub"):
            # Simplificado: Placeholder o extrae cover si posible
            return QPixmap("assets/default_cover.png")
        return QPixmap("assets/default_cover.png")  # Para DJVU u otros

    def load_document(self, file_name):
        """Carga documento y retorna contenido para visor"""
        self.current_file = os.path.join(self.documents_dir, file_name)
        if self.current_file.endswith(".pdf"):
            self.doc = fitz.open(self.current_file)
            # Retorna primera página como HTML para visor (placeholder)
            return "<p>Cargando PDF... (Implementar páginas completas)</p>"
        elif self.current_file.endswith(".epub"):
            with open_epub(self.current_file) as doc:
                content = doc.read_item("chapter1.xhtml")  # Simplificado
                return content
        return "<p>Formato no soportado aún.</p>"


    def add_annotation(self, text, position):
        self.annotations.append({"text":text,"position":position})

class PdfDocument(DocumentModel):

    def __init__(self,file_path):
        super().__init__(file_path)
        self.doc = fitz.open(file_path)

    def get_page(self,page_num):
        page = self.doc[page_num]
        pix = page.get_pixmap()

        return pix.tobytes()
    
class EpubDocument(DocumentModel):
    def __init__(self,file_path):
        super().__init__(file_path)
        self.doc = open_epub.open(file_path)

    def get_content(self):
        return self.doc.read_item("chapter1.html") #esto no deberia depender del historial de lectura?