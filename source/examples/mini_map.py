import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class MiniMapEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Mini Map Editor")
        self.setGeometry(100, 100, 800, 600)

        self.main_editor = QsciScintilla()
        self.mini_map = QsciScintilla()

        lexer = QsciLexerPython()
        self.main_editor.setLexer(lexer)
        self.mini_map.setLexer(lexer)

        # Configura le proprietà della mini mappa
        self.mini_map.setReadOnly(True)
        self.mini_map.SendScintilla(self.mini_map.SCI_STYLESETFONT, 0, 'Courier')
        self.mini_map.SendScintilla(self.mini_map.SCI_STYLESETSIZE, 0, 5)  # Imposta una dimensione del testo più piccola

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.main_editor)
        layout.addWidget(self.mini_map)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Sincronizza il contenuto tra main_editor e mini_map
        self.main_editor.textChanged.connect(self.sync_with_mini_map)
        self.sync_with_mini_map()

    def sync_with_mini_map(self):
        self.mini_map.setText(self.main_editor.text())

app = QApplication(sys.argv)
window = MiniMapEditor()
window.show()
sys.exit(app.exec())
