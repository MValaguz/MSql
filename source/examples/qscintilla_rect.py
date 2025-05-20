from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor QScintilla con Selezione Rettangolare")
        self.setGeometry(100, 100, 800, 600)

        # Creazione dell'editor
        self.editor = QsciScintilla()
        self.editor.setUtf8(True)

        # Impostazione del lexer per evidenziazione della sintassi Python
        lexer = QsciLexerPython()
        self.editor.setLexer(lexer)

        # Attivazione della selezione rettangolare
        self.editor.SendScintilla(QsciScintilla.SCI_SETSELECTIONMODE, 1)  # 1 = selezione rettangolare

        # attivo il multiediting (cioè la possibilità, una volta fatta una selezione verticale, di fare un edit multiplo)        
        self.editor.SendScintilla(self.editor.SCI_SETADDITIONALSELECTIONTYPING, 1)        
        v_offset = self.editor.positionFromLineIndex(0, 7) 
        self.editor.SendScintilla(self.editor.SCI_SETSELECTION, v_offset, v_offset)        
        v_offset = self.editor.positionFromLineIndex(1, 5)
        self.editor.SendScintilla(self.editor.SCI_ADDSELECTION, v_offset, v_offset)
        v_offset = self.editor.positionFromLineIndex(2, 5)
        self.editor.SendScintilla(self.editor.SCI_ADDSELECTION, v_offset, v_offset)    

        # Layout
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
