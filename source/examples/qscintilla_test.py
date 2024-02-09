import sys
import re
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
        self.__editor = QsciScintilla()                
        #self.__editor = MyScintilla()
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
        #self.__editor.installEventFilter(self)                   

        # Add a word to the keyword set
        #self.__editor.SetKeywords(0, "print")        

        # Enable keyword set highlighting
        #self.__editor.StyleSetForeground(QsciScintilla.SCE_H_KEYWORD, 0xFF0000) # Red color
        #self.__editor.SetKeywords(0, "print")
        #self.__editor.SetKeywords(1, "yourOtherKeyword")

        self.__editor.indicatorDefine(QsciScintilla.HiddenIndicator, 0)
        self.__editor.setIndicatorHoverStyle(QsciScintilla.ThickCompositionIndicator,0)
        self.__editor.setIndicatorForegroundColor(QColor("#00f"), 0)
        self.__editor.setIndicatorHoverForegroundColor(QColor("#00f"), 0)
        self.__editor.setIndicatorDrawUnder(True, 0)        

        # Attivo evento sulla selezione del testo e relative variabili
        # il tutto per quando l'utente seleziona con il doppio click una parola e si evidenziano
        # tutte le ricorrenze della parola in tutto l'editor
        self.__editor.selectionChanged.connect(self.__selection_changed)        
        self.selection_lock = False
        self.SELECTION_INDICATOR = 4

        self.__editor.setText("""
        def pippo(p_parametro):
            print('ciao')            
            print('marco')
            QUESTA VERSIONE FACENDO DOPPIO CLICK SU UNA PAROLA PERMETTE DI EVIDENZIARE LE RELATIVE RICORRENZE!!!
                """)

        # ! Add editor to layout !
        self.__lyt.addWidget(self.__editor)

        self.show()

    def __btn_action(self):
        print('ciao')

    def __selection_changed(self):
        """
        Signal that fires when selected text changes
        """
        # This function seems to be asynchronous so a lock
        # is required in order to prevent recursive access to
        # Python's objects
        print('selezione cambiata')   
        if self.selection_lock == False:
            self.selection_lock = True
            selected_text = self.__editor.selectedText()
            self.clear_selection_highlights()
            if selected_text.isidentifier():
                self._highlight_selected_text(
                    selected_text,
                    case_sensitive=False,
                    regular_expression=True
                )
            self.selection_lock = False

    def clear_selection_highlights(self):
        #Clear the selection indicators
        self.__editor.clearIndicatorRange(
            0,
            0,
            self.__editor.lines(),
            self.__editor.lineLength(self.__editor.lines()-1),
            self.SELECTION_INDICATOR
        )

    def _highlight_selected_text(self,
                        highlight_text,
                        case_sensitive=False,
                        regular_expression=False):
        """
        Same as the highlight_text function, but adapted for the use
        with the __selection_changed functionality.
        """
        # Setup the indicator style, the highlight indicator will be 0
        self.set_indicator("selection")
        # Get all instances of the text using list comprehension and the re module
        matches = self.find_all(
            highlight_text,
            case_sensitive,
            regular_expression,
            text_to_bytes=True,
            whole_words=True
        )
        # Check if the match list is empty
        if matches:
            # Use the raw highlight function to set the highlight indicators
            self.highlight_raw(matches)

    def highlight_raw(self, highlight_list):
        """
        Core highlight function that uses Scintilla messages to style indicators.
        QScintilla's fillIndicatorRange function is to slow for large numbers of
        highlights!
        INFO:   This is done using the scintilla "INDICATORS" described in the official
                scintilla API (http://www.scintilla.org/ScintillaDoc.html#Indicators)
        """
        scintilla_command = QsciScintillaBase.SCI_INDICATORFILLRANGE
        for highlight in highlight_list:
            start   = highlight[1]
            length  = highlight[3] - highlight[1]
            self.__editor.SendScintilla(
                scintilla_command,
                start,
                length
            )

    def _set_indicator(self,
                       indicator,
                       fore_color):
        """
        Set the indicator settings
        """
        self.__editor.indicatorDefine(
            QsciScintilla.IndicatorStyle.StraightBoxIndicator ,
            indicator
        )
        self.__editor.setIndicatorForegroundColor(
            QColor(fore_color),
            indicator
        )
        self.__editor.SendScintilla(
            QsciScintillaBase.SCI_SETINDICATORCURRENT,
            indicator
        )

    def set_indicator(self, indicator):
        """
        Select the indicator that will be used for use with
        Scintilla's indicator functionality
        """                
        if indicator == "selection":
            self._set_indicator(
                self.SELECTION_INDICATOR,
                '#643A93FF' # indica il colore da dare alla selezione
            )        

    def find_all(self,
                 search_text,
                 case_sensitive=False,
                 regular_expression=False,
                 text_to_bytes=False,
                 whole_words=False):
        """Find all instances of a string and return a list of (line, index_start, index_end)"""
        #Find all instances of the search string and return the list
        matches = self.index_strings_in_text(
            search_text,
            self.__editor.text(),
            case_sensitive,
            regular_expression,
            text_to_bytes,
            whole_words
        )
        return matches

    def index_strings_in_text(self,
                            search_text, 
                            text, 
                            case_sensitive=False, 
                            regular_expression=False, 
                            text_to_bytes=False,
                            whole_words=False):
        """ 
        Return all instances of the searched text in the text string
        as a list of tuples(0, match_start_position, 0, match_end_position).
        
        Parameters:
            - search_text:
                the text/expression to search for in the text parameter
            - text:
                the text that will be searched through
            - case_sensitive:
                case sensitivity of the performed search
            - regular_expression:
                selection of whether the search string is a regular expression or not
            - text_to_bytes:
                whether to transform the search_text and text parameters into byte objects
            - whole_words:
                match only whole words
        """
        # Check if whole words only should be matched
        if whole_words == True:
            search_text = r"\b(" + search_text + r")\b"
        # Convert text to bytes so that utf-8 characters will be parsed correctly
        if text_to_bytes == True:
            search_text = bytes(search_text, "utf-8")
            text = bytes(text, "utf-8")
        # Set the search text according to the regular expression selection
        if regular_expression == False:
            search_text = re.escape(search_text)
        # Compile expression according to case sensitivity flag
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        # Create the list with all of the matches
        list_of_matches = [(0, match.start(), 0, match.end()) for match in re.finditer(compiled_search_re, text)]
        return list_of_matches
     
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
