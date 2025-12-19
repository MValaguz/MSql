from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.Qsci import QsciScintilla, QsciDocument

#esempio di gestione minimappa con qscidocument

class EditorWithMinimap(QWidget):
    def __init__(self):
        super().__init__()

        self.document = QsciDocument()
        #self.document.setText("\n".join([f"Linea {i}" for i in range(1, 500)]))

        layout = QHBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor principale
        self.editor = QsciScintilla()
        self.editor.setDocument(self.document)

        # Minimappa (seconda Scintilla)
        self.minimap = QsciScintilla()
        self.minimap.setDocument(self.document)

        # Config minimappa
        self.minimap.setReadOnly(True)
        self.minimap.setMargins(0)
        self.minimap.setCaretLineVisible(False)
        self.minimap.setCaretForegroundColor(Qt.GlobalColor.transparent)
        self.minimap.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.minimap.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.minimap.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self.minimap.SendScintilla(QsciScintilla.SCI_SETCARETSTYLE, 0)  # caret hidden

        # Font minuscolo
        #self.minimap.setZoom(-10)

        splitter.addWidget(self.editor)
        splitter.addWidget(self.minimap)
        splitter.setSizes([800, 120])

        layout.addWidget(splitter)

        # Collegamento fra click nella minimappa e scroll dell'editor principale
        self.editor.cursorPositionChanged.connect(self.sync_scroll)
        self.editor.setText("\n".join([f"Linea {i}" for i in range(1, 500)]))

    def sync_scroll(self):
        line, index = self.minimap.getCursorPosition()
        self.editor.setCursorPosition(line, 0)
        self.editor.ensureLineVisible(line)


app = QApplication([])
w = EditorWithMinimap()
w.resize(1000, 700)
w.show()
app.exec()
