import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.Qsci import *

class MyLexer(QsciLexerSQL):
    def __init__(self, parent):
        super(MyLexer, self).__init__(parent)

    def autoCompletionWordSeparators(self):
        return ['.']

class MyScintilla(QsciScintilla):
    clicked = pyqtSignal()
    
    #def __init__(self, parent):
    #    super(MyScintilla, self).__init__(parent)

    def mouseDoubleClickEvent(self, event):
        print('doppio click')
        self.clicked.emit()
        QsciScintilla.mousePressEvent(self, event)

class CustomMainWindow(QMainWindow):
    def __init__(self):
        super(CustomMainWindow, self).__init__()

        # Window setup
        # --------------

        # 1. Define the geometry of the main window
        self.setGeometry(300, 300, 800, 400)
        self.setWindowTitle("QScintilla Test")

        # 2. Create frame and layout
        self.__frm = QFrame(self)
        self.__frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
        self.__lyt = QVBoxLayout()
        self.__frm.setLayout(self.__lyt)
        self.setCentralWidget(self.__frm)
        self.__myFont = QFont()
        self.__myFont.setPointSize(14)

        # 3. Place a button
        self.__btn = QPushButton("Qsci")
        self.__btn.setFixedWidth(50)
        self.__btn.setFixedHeight(50)
        self.__btn.clicked.connect(self.__btn_action)
        self.__btn.setFont(self.__myFont)
        self.__lyt.addWidget(self.__btn)

        # QScintilla editor setup
        # ------------------------

        # ! Make instance of QsciScintilla class!
        #self.__editor = QsciScintilla()                
        self.__editor = MyScintilla()
        self.__editor.setUtf8(True)  # Set encoding to UTF-8
        self.__editor.setFont(self.__myFont)  # Will be overridden by lexer!        
        
        # attivo il lexer per linguaggio C
        #self.__lexer = QsciLexerPython(self.__editor)        
        self.__lexer = MyLexer(self.__editor)                        
        self.__editor.setLexer(self.__lexer)                

        # aggiunta autocompletamento
        self.v_api_lexer = QsciAPIs(self.__lexer)                    
        self.__editor.setAutoCompletionSource(QsciScintilla.AcsAll)                
        self.__editor.setAutoCompletionThreshold(2)          
        self.__editor.autoCompleteFromAll()                  
        
        # aggiungo tutti i termini di autocompletamento (si trovanon all'interno di una tabella che viene generata a comando)
        self.v_api_lexer.add('descri.elemento(primo,secondo)')                                    
        self.v_api_lexer.add('descri.secondo(terzo,quarto)')                                    
        self.v_api_lexer.prepare()        
                        
        # attivo il filtro di eventi sull'oggetto editor; ogni evento passerà dalla funzione eventFilter
        self.__editor.installEventFilter(self)                   

        self.__editor.setText("""
        def pippo(p_parametro):
            print('ciao')            
            print('marco')
                """)

        # ! Add editor to layout !
        self.__lyt.addWidget(self.__editor)

        self.show()

    def __btn_action(self):
        print('ciao')


    def eventFilter(self, source, event):
        """
           Gestione di eventi personalizzati sull'editor (overwrite, drag&drop, F12) e sulla tabella dei risultati
           Da notare come un'istruzione di return False indirizza l'evento verso il suo svolgimento classico
        """      
        print(event.type())                        
        return True
      
if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    myGUI = CustomMainWindow()

    sys.exit(app.exec_())
