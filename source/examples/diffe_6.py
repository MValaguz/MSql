from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.Qsci import QsciScintilla, QsciLexerDiff
from diff_match_patch import diff_match_patch

class DiffViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diff Viewer Bidirezionale")
        self.setGeometry(100, 100, 1000, 600)

        # Layout principale
        layout = QVBoxLayout()

        # Editor per il testo originale e il modificato
        editor_layout = QHBoxLayout()
        self.text1 = QTextEdit()
        self.text2 = QTextEdit()
        self.text1.setPlaceholderText("Inserisci il primo testo qui...")
        self.text2.setPlaceholderText("Inserisci il secondo testo qui...")
        editor_layout.addWidget(self.text1)
        editor_layout.addWidget(self.text2)
        layout.addLayout(editor_layout)

        # Pulsante per confrontare i testi
        compare_button = QPushButton("Confronta")
        compare_button.clicked.connect(self.compare_texts)
        layout.addWidget(compare_button)

        # Layout per gli editor delle differenze
        diff_layout = QHBoxLayout()
        self.diff_editor1 = QsciScintilla()
        self.diff_editor2 = QsciScintilla()
        self.lexer = QsciLexerDiff()  # Lexer per evidenziare le differenze
        self.diff_editor1.setLexer(self.lexer)
        self.diff_editor2.setLexer(self.lexer)
        diff_layout.addWidget(self.diff_editor1)
        diff_layout.addWidget(self.diff_editor2)
        layout.addLayout(diff_layout)

        # Container principale
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def compare_texts(self):
        # Ottieni i testi dai QTextEdit
        text1 = self.text1.toPlainText()
        text2 = self.text2.toPlainText()

        # Usa diff-match-patch per calcolare le differenze
        dmp = diff_match_patch()
        diffs1 = dmp.diff_main(text1, text2)
        diffs2 = dmp.diff_main(text2, text1)
        dmp.diff_cleanupSemantic(diffs1)
        dmp.diff_cleanupSemantic(diffs2)

        # Crea stringhe con le differenze per ciascun editor
        diff_result1 = self.generate_diff_string(diffs1)
        diff_result2 = self.generate_diff_string(diffs2)

        # Mostra le differenze nei rispettivi editor
        self.diff_editor1.setText(diff_result1)
        self.diff_editor2.setText(diff_result2)

    def generate_diff_string(self, diffs):
        diff_result = ""
        for diff in diffs:
            if diff[0] == -1:
                diff_result += f"- {diff[1]}\n"  # Rimosso
            elif diff[0] == 1:
                diff_result += f"+ {diff[1]}\n"  # Aggiunto
            else:
                diff_result += f"  {diff[1]}\n"  # Inalterato
        return diff_result


# Avvia l'applicazione PyQt6
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = DiffViewer()
    window.show()
    sys.exit(app.exec())
