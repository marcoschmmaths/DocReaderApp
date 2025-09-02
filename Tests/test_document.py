import unittest
from SourceCode.model import PdfDocument

class TestDocument(unittest.TestCase):
    def test_load_pdf(self):
        doc = PdfDocument("sample.pdf")
        self.assertIsNotNone(doc.doc)