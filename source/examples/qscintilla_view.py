from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QPlainTextEdit
from PyQt6.Qsci import QsciScintilla

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QScintilla Split View Example")
        self.setGeometry(100, 100, 800, 600)

        # Creazione del primo editor
        self.editor1 = QsciScintilla(self)
        self.editor1.SendScintilla(QsciScintilla.SCI_SETMULTIPLESELECTION, True)
        #self.editor1.SendScintilla(QsciScintilla.SCI_SETADDITIONALSELECTION, True)
        self.editor1.SendScintilla(QsciScintilla.SCI_SETSELECTION, 0, 0, 100, 100)
        self.editor1.SendScintilla(QsciScintilla.SCI_SETSELECTION, 1, 200, 300, 300)

        # Creazione del secondo editor
        self.editor2 = QsciScintilla(self)
        self.editor2.SendScintilla(QsciScintilla.SCI_SETMULTIPLESELECTION, True)
        #self.editor2.SendScintilla(QsciScintilla.SCI_SETADDITIONALSELECTION, True)
        self.editor2.SendScintilla(QsciScintilla.SCI_SETSELECTION, 0, 0, 100, 100)
        self.editor2.SendScintilla(QsciScintilla.SCI_SETSELECTION, 1, 200, 300, 300)

        # Creazione del splitter
        splitter = QSplitter(self)
        splitter.addWidget(self.editor1)
        splitter.addWidget(self.editor2)
        self.setCentralWidget(splitter)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
