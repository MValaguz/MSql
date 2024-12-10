import sys
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.Qsci import *

class MouseEventFilter(QObject):
    def eventFilter(self, obj, event):
        return True
        print(event.type())
        if event.type() in (QEvent.Type.MouseButtonPress,
                            QEvent.Type.MouseButtonRelease,
                            QEvent.Type.MouseButtonDblClick,
                            QEvent.Type.MouseMove):
            return True  # Ignora l'evento di mouse
        return super().eventFilter(obj, event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Editor with Mini Map Example')

        # Crea un widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Crea un layout orizzontale
        layout = QHBoxLayout(central_widget)

        # Crea uno splitter
        splitter = QSplitter()

        # Crea il QsciScintilla principale (editor)
        self.main_editor = QsciScintilla()

        # Crea la mini mappa come QsciScintilla normale
        self.mini_map = QsciScintilla()
        self.mini_map.setReadOnly(True)
        self.mini_map.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mini_map.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mini_map.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        
        # Imposta la sincronizzazione della mini mappa con l'editor principale
        self.main_editor.textChanged.connect(self.sync_mini_map)
        self.main_editor.verticalScrollBar().valueChanged.connect(self.sync_scrollbar)

        # Aggiungi i QsciScintilla allo splitter
        splitter.addWidget(self.main_editor)
        splitter.addWidget(self.mini_map)

        # Imposta dimensioni iniziali per la mini mappa
        self.mini_map.setFixedWidth(150)

        # Aggiungi lo splitter al layout
        layout.addWidget(splitter)

        # Applica il filtro per eventi alla mini mappa
        #self.mouse_event_filter = MouseEventFilter()
        #self.mini_map.installEventFilter(self.mouse_event_filter)
        self.mini_map.setEnabled(False)

    def sync_mini_map(self):
        self.mini_map.setText(self.main_editor.text())

    def sync_scrollbar(self):
        self.mini_map.verticalScrollBar().setValue(self.main_editor.verticalScrollBar().value())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
