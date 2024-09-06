import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

class ParallelEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()

        self.layout.addWidget(self.editor1)
        self.layout.addWidget(self.editor2)

        lexer = QsciLexerPython()
        self.editor1.setLexer(lexer)
        self.editor2.setLexer(lexer)

        self.editor1.verticalScrollBar().valueChanged.connect(self.sync_scroll)
        self.editor2.verticalScrollBar().valueChanged.connect(self.sync_scroll)

    def sync_scroll(self, value):
        sender = self.sender()
        if sender == self.editor1.verticalScrollBar():
            self.editor2.verticalScrollBar().setValue(value)
        else:
            self.editor1.verticalScrollBar().setValue(value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParallelEditor()
    window.show()
    sys.exit(app.exec_())
