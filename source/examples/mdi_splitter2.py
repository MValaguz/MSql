import sys
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QTextEdit, QVBoxLayout, QWidget

class DraggableSubWindow(QMdiSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.editor = QTextEdit()
        self.setWidget(self.editor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

class MdiDragAndDrop(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mdi_area1 = QMdiArea()
        self.mdi_area2 = QMdiArea()

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.mdi_area1)
        main_layout.addWidget(self.mdi_area2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        subwindow1 = self.create_sub_window("Editor 1")
        subwindow2 = self.create_sub_window("Editor 2")

        self.mdi_area1.addSubWindow(subwindow1)
        self.mdi_area1.addSubWindow(subwindow2)

        subwindow1.show()
        subwindow2.show()

        self.mdi_area2.setAcceptDrops(True)
        self.mdi_area2.dragEnterEvent = self.drag_enter_event
        self.mdi_area2.dropEvent = self.drop_event

    def create_sub_window(self, title):
        return DraggableSubWindow(title)

    def drag_enter_event(self, event):
        event.acceptProposedAction()

    def drop_event(self, event):
        #position = event.pos()
        sub_window = event.source()
        sub_window.setParent(None)
        self.mdi_area2.addSubWindow(sub_window)
        #sub_window.move(position)
        sub_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MdiDragAndDrop()
    main_win.show()
    sys.exit(app.exec())
