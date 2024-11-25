from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.Qsci import QsciScintilla, QsciLexerDiff
import difflib

class DiffViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = QsciScintilla()
        self.setCentralWidget(self.editor)
        
        lexer = QsciLexerDiff()
        self.editor.setLexer(lexer)
        
        with open('diff_file.diff', 'r') as file:
            self.editor.setText(file.read())

def create_diff_file(file1_path, file2_path, diff_file_path): 
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2: 
        file1_lines = file1.readlines() 
        file2_lines = file2.readlines() 
        diff = difflib.unified_diff(file1_lines, file2_lines, fromfile='file1', tofile='file2') 
        with open(diff_file_path, 'w') as diff_file: 
            diff_file.writelines(diff) # Esempio di utilizzo 

if __name__ == '__main__':
    file1_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file1.txt'
    file2_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file2.txt'
        
    create_diff_file(file1_path, file2_path, 'diff_file.diff')            
    app = QApplication([])
    viewer = DiffViewer()
    viewer.show()
    app.exec()
