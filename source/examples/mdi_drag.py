import sys
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QVBoxLayout, QWidget, QSplitter
from PyQt6.Qsci import QsciScintilla

class DraggableSubWindow(QMdiSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.editor = QsciScintilla()
        self.setWidget(self.editor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag_distance = (event.pos() - self.drag_start_position).manhattanLength()
            if drag_distance > QApplication.startDragDistance():
                print('ciao')
                drag = QDrag(self)
                mime_data = QMimeData()
                drag.setMimeData(mime_data)
                drag.exec(Qt.DropAction.MoveAction)

class MdiSplitter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mdi_area = QMdiArea()
        #self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        #self.mdi_area.setTabsClosable(True)
        #self.mdi_area.setTabsMovable(True)
        self.setCentralWidget(self.mdi_area)

        self.init_ui()

    def init_ui(self):
        self.splitter = QSplitter()

        subwindow1 = DraggableSubWindow("Editor 1")
        subwindow2 = DraggableSubWindow("Editor 2")

        self.mdi_area.addSubWindow(subwindow1)
        self.mdi_area.addSubWindow(subwindow2)

        subwindow1.show()
        subwindow2.show()

        self.setGeometry(200, 200, 800, 600)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MdiSplitter()
    main_win.show()
    sys.exit(app.exec())
