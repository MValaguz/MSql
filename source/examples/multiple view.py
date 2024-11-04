import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.Qsci import QsciScintilla

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()

        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        layout = QVBoxLayout(centralWidget)
        layout.addWidget(self.editor1)
        layout.addWidget(self.editor2)

        self.setCentralWidget(centralWidget)

        self.editor1.setText("Testo del documento")
        self.editor2.setText("Testo del documento")

        # Sincronizzazione delle scrollbar verticali
        self.editor1.verticalScrollBar().valueChanged.connect(self.sync_scroll_1)
        self.editor2.verticalScrollBar().valueChanged.connect(self.sync_scroll_2)

        # Sincronizzazione delle modifiche del testo
        self.editor1.textChanged.connect(self.sync_text_1)
        self.editor2.textChanged.connect(self.sync_text_2)

    def sync_scroll_1(self, value):
        self.editor2.verticalScrollBar().setValue(value)

    def sync_scroll_2(self, value):
        self.editor1.verticalScrollBar().setValue(value)

    def sync_text_1(self):
        self.editor2.setText(self.editor1.text())

    def sync_text_2(self):
        self.editor1.setText(self.editor2.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
