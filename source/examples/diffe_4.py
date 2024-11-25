from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom
from PyQt6 import QtGui
import difflib

class CustomLexer(QsciLexerCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._styles = {
            'added': 1,
            'removed': 2,
            'normal': 0
        }
        self.setColor(QtGui.QColor('#00FF00'), self._styles['added'])
        self.setColor(QtGui.QColor('#FF0000'), self._styles['removed'])
        self.setColor(QtGui.QColor('#000000'), self._styles['normal'])

    def styleText(self, start, end):
        editor = self.editor()
        text = editor.text()
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            if line.startswith('+'):
                self.startStyling(editor.positionFromLineIndex(line_num, 0))
                self.setStyling(len(line), self._styles['added'])
            elif line.startswith('-'):
                self.startStyling(editor.positionFromLineIndex(line_num, 0))
                self.setStyling(len(line), self._styles['removed'])
            else:
                self.startStyling(editor.positionFromLineIndex(line_num, 0))
                self.setStyling(len(line), self._styles['normal'])

class DiffViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text File Comparator")
        
        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()
        lexer = CustomLexer()
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
                
                diff = difflib.unified_diff(file1_lines, file2_lines, fromfile='file1', tofile='file2')
                diff_text = ''.join(diff)
                
                self.editor1.setText(''.join(file1_lines))
                self.editor2.setText(''.join(file2_lines))
                
                self.highlight_differences(self.editor1, diff_text)
                self.highlight_differences(self.editor2, diff_text)
    
    def highlight_differences(self, editor, diff_text):
        lines = diff_text.split('\n')
        for line_num, line in enumerate(lines):
            if line.startswith('+'):
                print(line)
                editor.SendScintilla(editor.SCI_STARTSTYLING, editor.positionFromLineIndex(line_num, 0))
                editor.SendScintilla(editor.SCI_SETSTYLING, len(line), 1)
            elif line.startswith('-'):
                editor.SendScintilla(editor.SCI_STARTSTYLING, editor.positionFromLineIndex(line_num, 0))
                editor.SendScintilla(editor.SCI_SETSTYLING, len(line), 2)

if __name__ == '__main__':
    app = QApplication([])
    viewer = DiffViewer()
    viewer.show()
    app.exec()
