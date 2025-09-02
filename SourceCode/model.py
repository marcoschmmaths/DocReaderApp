import fitz 

class Document:
    def __init__(self,file_path):
        self.file_path = file_path
        self.annotations = []
    def add_annotation(self, text, position):
        self.annotations.append({"text":text,"position":position})

class PdfDocument(Document):

    def __init__(self,file_path):
        super().__init__(file_path)
        self.doc = fitz.open(file_path)

    def get_page(self,page_num):
        page = self.doc[page_num]
        pix = page.get_pixmap()

        return pix.tobytes()