import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QMdiArea, QMdiSubWindow, QVBoxLayout, QWidget
from PyQt6.Qsci import QsciScintilla

class MdiSplitter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

        self.init_ui()

    def init_ui(self):
        splitter = QSplitter()

        subwindow1 = self.create_mdi_sub_window("Editor 1")
        subwindow2 = self.create_mdi_sub_window("Editor 2")

        splitter.addWidget(subwindow1)
        splitter.addWidget(subwindow2)

        widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        widget.setLayout(layout)

        sub_window = QMdiSubWindow()
        sub_window.setWidget(widget)
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()

    def create_mdi_sub_window(self, title):
        sub_window = QMdiSubWindow()
        editor = QsciScintilla()
        sub_window.setWidget(editor)
        sub_window.setWindowTitle(title)
        return sub_window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MdiSplitter()
    main_win.show()
    sys.exit(app.exec())
