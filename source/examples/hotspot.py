import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Editor con Hotspot")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Creazione dell'editor di testo QScintilla
        self.editor = QsciScintilla()
        self.editor.setUtf8(True)
        
        # Configurazione del lexer per Python
        lexer = QsciLexerPython()
        lexer.setDefaultFont(QFont("Courier", 12))
        self.editor.setLexer(lexer)

        # Abilita l'uso degli hotspot
        self.editor.SendScintilla(QsciScintilla.SCI_SETHOTSPOTSINGLELINE, True)
        self.editor.SendScintilla(QsciScintilla.SCI_SETHOTSPOTACTIVEFORE, True, 0xff0000)
        self.editor.SendScintilla(QsciScintilla.SCI_SETHOTSPOTACTIVEBACK, True, 0xffff00)

        # Testo di esempio con hotspot
        self.editor.setText("""def example_function():
    print("Hello, World!")

# Clicca su questo commento per eseguire l'azione
# HOTSPOT: Questo è un hotspot!
""")

        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connessione dell'evento di hotspot
        self.editor.hotspotClicked.connect(self.on_hotspot_clicked)

    def on_hotspot_clicked(self, position, modifiers):
        # Esegui azioni quando l'hotspot viene cliccato
        print("Hotspot cliccato alla posizione:", position)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
