# minimal_qscintilla_example.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class SafeQsci(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Basic configuration
        lexer = QsciLexerPython(self)
        self.setLexer(lexer)
        self.setUtf8(True)
        self.setMarginsFont(self.font())
        self.setMarginWidth(0, "0000")
        self.setBraceMatching(QsciScintilla.BraceMatch.StrictBraceMatch)
        self.setAutoIndent(True)
        self.setTabWidth(4)
        # Fill with sample text
        sample = "\n".join(f"line {i}: print('hello world {i}')" for i in range(1, 201))
        self.setText(sample)

    def _collapse_selection_to_caret(self):
        # Get current caret (cursor) position and collapse selection there
        try:
            line, index = self.getCursorPosition()
            # setSelection(startLine, startIndex, endLine, endIndex)
            self.setSelection(line, index, line, index)
        except Exception:
            # don't let Python exceptions propagate; this is best-effort safety
            pass

    # Workaround: quando il mouse lascia il widget, chiudi la selezione
    def leaveEvent(self, event):
        self._collapse_selection_to_caret()
        super().leaveEvent(event)

    # Workaround aggiuntivo: se il bottone viene rilasciato fuori, assicurati che la selezione sia chiusa
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._collapse_selection_to_caret()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qsci Safe Example")
        central = QWidget()
        layout = QVBoxLayout(central)
        self.editor = SafeQsci(self)
        layout.addWidget(self.editor)
        self.setCentralWidget(central)
        self.resize(900, 700)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())