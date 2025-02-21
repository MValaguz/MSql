from PyQt6.QtWidgets import QApplication
from PyQt6.Qsci import QsciScintilla, QsciLexerPython
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt

class MyEditor(QsciScintilla):
    def __init__(self):
        super().__init__()

        # Imposta il lexer (esempio Python)
        lexer = QsciLexerPython()
        self.setLexer(lexer)

        # Configura l'autocompletamento
        self.setAutoCompletionThreshold(1)  # Suggerisce dopo 1 carattere
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)  # Usa tutte le parole disponibili
        self.setAutoCompletionCaseSensitivity(False)  # Non case-sensitive

    def keyPressEvent(self, event: QKeyEvent):
        if self.autoCompletionVisible():  # Controlla se l'autocompletamento è aperto
            if event.key() == Qt.Key.Key_Return:
                self.cancelAutoCompletion()  # Chiude la lista di autocompletamento
                super().keyPressEvent(event)  # Continua normalmente con Invio (va a capo)
                return
            elif event.key() == Qt.Key.Key_Tab:
                self.acceptAutoCompletion()  # Conferma il suggerimento con Tab
                return
        
        super().keyPressEvent(event)

    def autoCompletionVisible(self):
        """Verifica se l'autocompletamento è visibile."""
        return self.SendScintilla(QsciScintilla.SCI_AUTOCGETCURRENT) != -1

    def acceptAutoCompletion(self):
        """Accetta il suggerimento attuale della lista di autocompletamento."""
        self.SendScintilla(QsciScintilla.SCI_AUTOCCOMPLETE)

    def cancelAutoCompletion(self):
        """Chiude la lista di autocompletamento."""
        # chiudo eventuale popup di autocompletation inviando a qscintilla il tasto Esc
        v_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier) 
        QApplication.postEvent(self, v_event)

if __name__ == "__main__":
    app = QApplication([])
    editor = MyEditor()
    editor.show()
    app.exec()
