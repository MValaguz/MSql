import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit
from PyQt5.Qsci import QsciScintilla
import hunspell

class SpellCheckEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spell_checker = hunspell.HunSpell('/path/to/it_IT.dic', '/path/to/it_IT.aff')
        self.textChanged.connect(self.check_spelling)

    def check_spelling(self):
        text = self.text()
        words = text.split()
        for word in words:
            if not self.spell_checker.spell(word):
                # Evidenzia la parola errata
                self.setIndicatorCurrent(0)
                self.indicatorFillRange(text.index(word), len(word))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = SpellCheckEditor()
        self.setCentralWidget(self.editor)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())