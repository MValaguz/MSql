import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QPushButton, QVBoxLayout, QWidget, QSplitter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MDI Area Example")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Create the MDI area
        self.mdi_area1 = QMdiArea()
        layout.addWidget(self.mdi_area1)

        # Create the button
        self.button = QPushButton("Add MDI Area")
        self.button.clicked.connect(self.add_mdi_area)
        layout.addWidget(self.button)

        # Set layout to a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def add_mdi_area(self):
        splitter = QSplitter()
        splitter.addWidget(self.mdi_area1)

        # Create a new MDI area
        self.mdi_area2 = QMdiArea()
        splitter.addWidget(self.mdi_area2)

        # Set splitter as the central widget
        self.setCentralWidget(splitter)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
