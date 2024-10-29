import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QPushButton, QVBoxLayout, QWidget, QSplitter
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QDrag

class DraggableMdiSubWindow(QMdiSubWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            mime_data = QMimeData()
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MDI Area Drag and Drop Example")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Create the MDI areas
        self.mdi_area1 = QMdiArea()
        self.mdi_area1.setAcceptDrops(True)
        self.mdi_area2 = QMdiArea()
        self.mdi_area2.setAcceptDrops(True)

        # Create a splitter
        splitter = QSplitter()
        splitter.addWidget(self.mdi_area1)
        splitter.addWidget(self.mdi_area2)

        layout.addWidget(splitter)

        # Set layout to a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Add a test subwindow to the first MDI area
        sub_window = DraggableMdiSubWindow()
        sub_window.setWidget(QPushButton("Drag me"))
        self.mdi_area1.addSubWindow(sub_window)
        sub_window.show()

    def dragEnterEvent(self, event: QDragEnterEvent):
        event.accept()

    def dragMoveEvent(self, event: QDragMoveEvent):
        event.accept()

    def dropEvent(self, event: QDropEvent):
        source = event.source()
        if source:
            source.setParent(None)
            if event.source().parentWidget() is self.mdi_area1:
                self.mdi_area2.addSubWindow(source)
            else:
                self.mdi_area1.addSubWindow(source)
            source.show()
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
