import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Librerie QScintilla
from PyQt6.Qsci import *

class Editor(QsciScintilla):
    def __init__(self):
        super().__init__()
        self.lexer = QsciLexerSQL()
        self.setLexer(self.lexer)
        self.keyPressEvent = self.custom_key_press_event

    def custom_key_press_event(self, event):
        if event.text() == '(':
            self.insert('()')
            self.setCursorPosition(self.getCursorPosition()[0], self.getCursorPosition()[1] - 1)
        elif event.text() == '"':
            self.insert('""')
            self.setCursorPosition(self.getCursorPosition()[0], self.getCursorPosition()[1] - 1)
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = Editor()
    editor.show()
    sys.exit(app.exec())
