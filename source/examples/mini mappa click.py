from PyQt6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget, QMainWindow
import sys

class TextEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.editor = QTextEdit(self)
        self.editor.setPlainText("\n".join([f"Line {i}" for i in range(1500)]))  # Crea un testo con 1500 righe

        layout = QVBoxLayout()
        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Simula il clic del mouse sulla posizione y=40
        self.calculate_line_from_mouse_click(40, 100, 2000, 1500)

    def calculate_line_from_mouse_click(self, y, widget_height, scrollbar_offset, total_lines):
        # Calcola la proporzione del punto y rispetto all'altezza visibile del widget
        visible_proportion = y / widget_height

        # Calcola la posizione reale nel testo tenendo conto dello scroll
        max_scroll = self.editor.verticalScrollBar().maximum()
        total_content_height = max_scroll + widget_height
        relative_position = scrollbar_offset + visible_proportion * widget_height

        # Calcola il numero di riga corrispondente
        line_number = int((relative_position / total_content_height) * total_lines)

        # Assicurati che il numero di riga rientri nei limiti
        line_number = max(0, min(line_number, total_lines - 1))

        print(f"Posizione del mouse (y): {y}, Numero di riga: {line_number}")
        return line_number

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = TextEditor()
    editor.show()
    sys.exit(app.exec())
