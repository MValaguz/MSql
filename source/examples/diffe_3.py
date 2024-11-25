from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
from PyQt6.Qsci import QsciScintilla, QsciLexerDiff
import difflib

class DiffViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text File Comparator")
        
        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()
        lexer = QsciLexerDiff()
        self.editor1.setLexer(lexer)
        self.editor2.setLexer(lexer)
        
        self.load_button = QPushButton("Load Files and Compare")
        self.load_button.clicked.connect(self.load_and_compare_files)
        
        layout = QVBoxLayout()
        editors_layout = QHBoxLayout()
        editors_layout.addWidget(self.editor1)
        editors_layout.addWidget(self.editor2)
        
        layout.addLayout(editors_layout)
        layout.addWidget(self.load_button)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    def load_and_compare_files(self):
        file1_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file1.txt'
        file2_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file2.txt'
                
        if file1_path and file2_path:
            with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
                file1_lines = file1.readlines()
                file2_lines = file2.readlines()
                
                diff1 = difflib.unified_diff(file1_lines, file2_lines, fromfile='file1', tofile='file2')
                diff2 = difflib.unified_diff(file2_lines, file1_lines, fromfile='file2', tofile='file1')
                
                self.editor1.setText(''.join(diff1))
                self.editor2.setText(''.join(diff2))

if __name__ == '__main__':
    app = QApplication([])
    viewer = DiffViewer()
    viewer.show()
    app.exec()
