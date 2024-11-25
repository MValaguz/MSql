import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt6.Qsci import QsciScintilla, QsciLexerDiff
import difflib

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diff Viewer")
        self.setGeometry(300, 100, 800, 600)

        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()
        self.diffEditor = QsciScintilla()
        self.diffEditor.setReadOnly(True)
        self.diffButton = QPushButton("Show Differences")
        
        layout = QVBoxLayout()
        layout.addWidget(self.editor1)
        layout.addWidget(self.editor2)
        layout.addWidget(self.diffEditor)
        layout.addWidget(self.diffButton)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.diffButton.clicked.connect(self.show_differences)
        self.load_files()
        self.setup_editor(self.editor1)
        self.setup_editor(self.editor2)
        self.setup_editor(self.diffEditor)
        
    def setup_editor(self, editor):
        lexer = QsciLexerDiff()
        editor.setLexer(lexer)
        editor.setMarginLineNumbers(1, True)
        editor.setMarginWidth(1, "0000")

    def load_files(self):
        file1_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file1.txt'
        file2_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file2.txt'
        
        if file1_path and file2_path:
            with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
                self.file1_lines = file1.readlines()
                self.file2_lines = file2.readlines()
                
                self.editor1.setText(''.join(self.file1_lines))
                self.editor2.setText(''.join(self.file2_lines))
                
    def show_differences(self):
        diff = list(difflib.unified_diff(self.file1_lines, self.file2_lines, lineterm=''))
        
        # Create unified diff text 
        diff_text = diff[0] + '\n' + diff[1] + '\n' + diff[2] + '\n' + ''.join(diff[3:])                
        
        # Apply diff text to the diffEditor
        self.diffEditor.setText(diff_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
