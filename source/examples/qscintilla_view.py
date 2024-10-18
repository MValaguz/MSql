import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QPlainTextEdit, QVBoxLayout, QWidget

from PyQt5.Qsci import *

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Editor con QScintilla e Anteprima')
        self.setGeometry(100, 100, 800, 600)

        # Creazione dell'editor principale
        self.editor = QsciScintilla(self)
        self.editor.setUtf8(True)
        self.editor.SendScintilla(self.editor.SCI_SETMULTIPLESELECTION, True)
        #self.editor.SendScintilla(self.editor.SCI_SETMULTIPROCESSSELECTION, True)

        # Creazione dell'editor di anteprima
        self.preview = QPlainTextEdit(self)
        self.preview.setReadOnly(True)

        # Creazione del splitter
        splitter = QSplitter(self)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        self.setCentralWidget(splitter)

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainApp = MainApp()
    sys.exit(app.exec_())
