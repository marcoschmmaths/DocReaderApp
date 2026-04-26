import sys
from PySide6.QtWidgets import QApplication
from model import DocumentModel
from view import MainView
from controller import Controller

if __name__ == "__main__":
    # The main entry point for the application.
    # It follows a clean setup pattern:
    # 1. Create the application instance.
    # 2. Instantiate the Model, View, and Controller.
    # 3. Show the main window.
    # 4. Start the application's event loop.
    
    app = QApplication(sys.argv)
    
    # Instantiate the core components of the MVC architecture
    model = DocumentModel()
    view = MainView()
    controller = Controller(model, view)
    
    # Display the main window and start the application
    view.show()
    sys.exit(app.exec())
