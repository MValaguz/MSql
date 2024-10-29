from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QTextEdit
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        # Crea la subwindow senza titolo e senza bordi
        subwindow = QMdiSubWindow()
        subwindow.setWidget(QTextEdit("Questa subwindow non ha titolo né bordi"))
        subwindow.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.mdi.addSubWindow(subwindow)
        subwindow.show()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
