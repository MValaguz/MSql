import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget
from PyQt6.QtGui import QTextDocument
from PyQt6.Qsci import *
import difflib

class FileComparer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Comparer")
        self.setGeometry(100, 100, 800, 600)

        self.editor1 = QsciScintilla()
        self.editor2 = QsciScintilla()

        lexer = QsciLexerPython()
        self.editor1.setLexer(lexer)
        self.editor2.setLexer(lexer)

        layout = QVBoxLayout()
        layout.addWidget(self.editor1)
        layout.addWidget(self.editor2)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Definisci uno stile personalizzato 
        self.green_style = 11 # Puoi scegliere un numero qualsiasi che non sia già utilizzato 
        self.editor1.SendScintilla(QsciScintillaBase.SCI_STYLESETFORE, self.green_style, 0x008000) # Verde 
        self.editor1.SendScintilla(QsciScintillaBase.SCI_STYLESETBOLD, self.green_style, True) # grassetto
        self.editor1.SendScintilla(QsciScintillaBase.SCI_SETVIEWWS,QsciScintillaBase.SCWS_VISIBLEALWAYS)  

        #self.editor2.SendScintilla(self.editor2.SCI_STYLESETFORE, self.green_style, 0x008000) # Verde 
        #self.red_style = 12 # Puoi scegliere un numero qualsiasi che non sia già utilizzato 
        #self.editor1.SendScintilla(self.editor1.SCI_STYLESETFORE, self.red_style, 0x0000FF) # rosso 
        #self.editor2.SendScintilla(self.editor2.SCI_STYLESETFORE, self.red_style, 0x0000FF) # rosso

        #self.editor1.SendScintilla(self.editor1.SCI_STYLESETBOLD, self.red_style, True) # grassetto
        #self.editor2.SendScintilla(self.editor2.SCI_STYLESETBOLD, self.red_style, True) # grassetto
        #self.editor1.SendScintilla(self.editor1.SCI_STYLESETBOLD, self.green_style, True) # grassetto
        #self.editor2.SendScintilla(self.editor2.SCI_STYLESETBOLD, self.green_style, True) # grassetto

        self.open_files()

    def open_files(self):
        file1_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file1.txt'
        file2_path = 'C:\\Users\\MValaguz\\Documents\\GitHub\\MSql\\source\\examples\\file2.txt'
        
        with open(file1_path, 'r') as file1:
            file1_lines = file1.readlines()

        with open(file2_path, 'r') as file2:
            file2_lines = file2.readlines()

        differ = difflib.Differ()
        diff = list(differ.compare(file1_lines, file2_lines))        

        self.editor1.setText(''.join(file1_lines))
        self.editor2.setText(''.join(file2_lines))

        for line in diff:
            if line.startswith('-'):
                print(line)
                self.highlight_line(self.editor1, diff.index(line)-1,'-')
            elif line.startswith('+'):
                print(line)
                self.highlight_line(self.editor1, diff.index(line)-1,'+')

    def highlight_line(self, editor, line_number, p_type):            
        pos_start = editor.positionFromLineIndex(line_number, 0)
        #print(pos_start)                
        pos_end = editor.positionFromLineIndex(line_number, editor.lineLength(line_number))        
        editor.SendScintilla(QsciScintillaBase.SCI_STARTSTYLING, pos_start)
        if p_type == '+':
            #print(str(editor.lineLength(line_number)))
            editor.SendScintilla(QsciScintillaBase.SCI_SETSTYLING, pos_end - pos_start, self.green_style)
        #else:
        #    editor.SendScintilla(editor.SCI_SETSTYLING, 5, self.red_style)

app = QApplication(sys.argv)
window = FileComparer()
window.show()
sys.exit(app.exec())
