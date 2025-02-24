from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Librerie QScintilla
from PyQt6.Qsci import *
import difflib

class DiffEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLexer(QsciLexerPython(self))  # Usa il lexer per Python
        self.setMarginWidth(1, "0000")  # Abilita margine numerico
        self.setReadOnly(True)  # Imposta il file come sola lettura
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)

        # Indicatori per evidenziare le differenze
        self.indicatorDefine(QsciScintilla.IndicatorStyle.BoxIndicator, 0)  # Rosso per eliminazioni
        self.setIndicatorForegroundColor(QColor("#ff0000"), 0)
        
        self.indicatorDefine(QsciScintilla.IndicatorStyle.BoxIndicator, 1)  # Verde per aggiunte
        self.setIndicatorForegroundColor(QColor("#00ff00"), 1)

    def highlight_differences(self, text1, text2):
        """Evidenzia le differenze tra il testo corrente e text2"""
        self.clearIndicators()

        d = difflib.SequenceMatcher(None, text1, text2)
        for tag, i1, i2, j1, j2 in d.get_opcodes():
            if tag == "replace":  # Testo modificato
                self.highlight_range(i1, i2, 0)  # Rosso
                self.highlight_range(j1, j2, 1)  # Verde
            elif tag == "delete":  # Testo rimosso
                self.highlight_range(i1, i2, 0)  # Rosso
            elif tag == "insert":  # Testo aggiunto
                self.highlight_range(j1, j2, 1)  # Verde

    def highlight_range(self, start, end, indicator):
        """Evidenzia un intervallo di testo con un indicatore"""        
        self.fillIndicatorRange(start, end - start, start, end - start, indicator)        

    def clearIndicators(self):
        """Rimuove tutte le evidenziazioni"""
        self.clearIndicatorRange(0, 0, self.lines(), 0, 0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diff Viewer")

        layout = QVBoxLayout()
        self.editor = DiffEditor()
        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Esempio di utilizzo
        text1 = "def hello():\n    print('Hello')\n    return 42\n"
        text2 = "def hello():\n    print('Hello, world!')\n    return 43\n"
        
        self.editor.setText(text1)
        self.editor.highlight_differences(text1, text2)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()