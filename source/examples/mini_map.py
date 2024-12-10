import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.Qsci import *

import sys
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QScintilla Mini Map Example")
        self.resize(800, 600)

        self.editor = QsciScintilla()
        self.editor.setText("Inserisci qui il tuo testo\n" * 5)
        
        self.minimap = QsciScintilla()
        self.minimap.setReadOnly(True)
        #self.minimap.setMargins(0, 0, 0, 0)
        self.minimap.setFixedWidth(100)
        self.minimap.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.minimap.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Impostazione del carattere più piccolo per la minimappa
        font = QFont("Courier", 3)  # Usa un font ancora più piccolo
        self.minimap.setFont(font)
        
        self.sync_scroll_bars()
        self.sync_text_changes()

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.editor)
        layout.addWidget(self.minimap)
        container.setLayout(layout)

        self.setCentralWidget(container)
        
    def sync_scroll_bars(self):
        # Collegare la scrollbar verticale dell'editor principale alla minimappa
        self.editor.verticalScrollBar().valueChanged.connect(self.on_editor_scroll)
        # Collegare la scrollbar verticale della minimappa all'editor principale
        self.minimap.verticalScrollBar().valueChanged.connect(self.on_minimap_scroll)
        
        self.minimap.verticalScrollBar().setValue(self.editor.verticalScrollBar().value())
        
    def on_editor_scroll(self, value):
        # Impedire il loop di aggiornamento
        if self.minimap.verticalScrollBar().value() != value:
            minimap_max = self.minimap.verticalScrollBar().maximum()
            editor_max = self.editor.verticalScrollBar().maximum()
            scale_factor = minimap_max / editor_max if editor_max > 0 else 1
            self.minimap.verticalScrollBar().setValue(int(value * scale_factor))

    def on_minimap_scroll(self, value):
        # Impedire il loop di aggiornamento
        if self.editor.verticalScrollBar().value() != value:
            editor_max = self.editor.verticalScrollBar().maximum()
            minimap_max = self.minimap.verticalScrollBar().maximum()
            scale_factor = editor_max / minimap_max if minimap_max > 0 else 1
            self.editor.verticalScrollBar().setValue(int(value * scale_factor))

    def sync_text_changes(self):
        self.editor.textChanged.connect(self.on_text_change)
        
    def on_text_change(self):
        self.minimap.setText(self.editor.text())
        #self.minimap.setCursorPosition(self.editor.getCursorPosition())
        v_line, v_pos = self.editor.getCursorPosition()
        self.minimap.setCursorPosition(v_line, 0)       

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())