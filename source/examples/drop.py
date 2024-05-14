from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QTextEdit
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os

class MyMdiSubWindow(QMdiSubWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                filepath = url.toLocalFile()
                # Handle the dropped file (e.g., open it, display it, etc.)
                print(f"File dropped: {filepath}")

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        mdiArea = QMdiArea()
        self.setCentralWidget(mdiArea)

        subWindow = MyMdiSubWindow()
        textEdit = QTextEdit()
        subWindow.setWidget(textEdit)
        mdiArea.addSubWindow(subWindow)

if __name__ == "__main__":
    app = QApplication([])
    mainWindow = MyMainWindow()
    mainWindow.show()
    app.exec_()
