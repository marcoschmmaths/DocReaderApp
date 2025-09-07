import sys
from PySide6.QtWidgets import QApplication
from model import DocumentModel
from view import MainView
from controller import Controller

if __name__ == "__main__":
    app = QApplication(sys.argv)
    model = DocumentModel()  # Instancia del modelo
    view = MainView()  # Instancia de la vista
    controller = Controller(model, view)  # Controlador conecta modelo y vista
    view.show()  # Muestra la ventana
    sys.exit(app.exec())