import model
class Controller:
    def load_document(self,file_path):
        if file_path.endswith(".pdf"):
            self.model = model.PdfDocument(file_path)
            page_data = self.model.get_page(0)
            self.view.viewer.setHtml(f"<img src = 'data:image/png;base64,{page_data}'/>")
        #elif file_path.endswith(".epub"):
            #self.model = model.EpubDocument(file_path)
            #self.view.viewer.setHtml(self.model.get_content())