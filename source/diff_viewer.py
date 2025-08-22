#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13 con libreria pyqt6
#  Data..........: 28/07/2025
#  Descrizione...: Classe che visualizza le differenze tra due testi
#  Note..........: Creata utilizzando CoPilot

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.Qsci import *
import difflib
import sys
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class classDiffViewer(QWidget):
    """ 
       Questa classe crea una window con all'interno due editor qscintilla affiancati dove carica due testi ricevuti in input,
       li confronta e mette in evidenza le differenze
    """
    def __init__(self,
                dark_theme, # Se True indica che siamo in modalità tema scuro
                tabulator,  # Indica la larghezza del tabulatore
                window_pos, # Se True indica di salvare la posizione della window
                text1: str, # Testo1 
                text2: str, # Testo2
                title1: str = "Titolo 1", # Titolo di Testo1
                title2: str = "Titolo 2", # Titolo di Testo2
                font: QFont = QFont("Cascadia Code", 12, QFont.Weight.Bold)): # Font dell'editor
        super().__init__()  
        
        self.diff_positions = []
        self.current_diff   = 0
        self.window_pos = window_pos

        # creo oggetto settings per salvare posizione della window 
        self.settings = QSettings("Marco Valaguzza", "MSql_differ")

        # se utente ha richiesto di ricordare la posizione della window...
        if self.window_pos:
            # recupero dal registro di sistema (regedit) la posizione della window
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)                        

        # lexer SQL
        lexer = QsciLexerSQL()        
        lexer.setFont(font)

        # se è stato scelto il tema colori scuro --> reimposto i colori della sezione qscintilla
        # queste istruzioni sono presenti anche in MSql_editor.py
        if dark_theme:
            lexer.setDefaultPaper(QColor('#2D2D2D'))
            # colori delle parole
            lexer.setColor(QColor('white'), QsciLexerSQL.Default) 
            lexer.setColor(QColor('#608B4E'), QsciLexerSQL.Comment)
            lexer.setColor(QColor('#608B4E'), QsciLexerSQL.CommentLine)
            lexer.setColor(QColor('#608B4E'), QsciLexerSQL.CommentDoc) 
            lexer.setColor(QColor('#b5cea8'), QsciLexerSQL.Number)            
            lexer.setColor(QColor('#00cb62'), QsciLexerSQL.Keyword)
            lexer.setColor(QColor('#00aaff'), QsciLexerSQL.DoubleQuotedString) 
            lexer.setColor(QColor('#ECBB76'), QsciLexerSQL.SingleQuotedString) 
            lexer.setColor(QColor('green'), QsciLexerSQL.PlusKeyword)
            lexer.setColor(QColor('green'), QsciLexerSQL.PlusPrompt) 
            lexer.setColor(QColor('cyan'), QsciLexerSQL.Operator) 
            lexer.setColor(QColor('#D4D4D4'), QsciLexerSQL.Identifier)
            lexer.setColor(QColor('green'), QsciLexerSQL.PlusComment) 
            lexer.setColor(QColor('green'), QsciLexerSQL.CommentLineHash) 
            lexer.setColor(QColor('green'), QsciLexerSQL.CommentDocKeyword)
            lexer.setColor(QColor('green'), QsciLexerSQL.CommentDocKeywordError) 
            lexer.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet5) 
            lexer.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet6)
            lexer.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet7) 
            lexer.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet8) 
            lexer.setColor(QColor('green'), QsciLexerSQL.QuotedIdentifier)
            lexer.setColor(QColor('green'), QsciLexerSQL.QuotedOperator)
        
        # splitter orizzontale
        splitter = QSplitter(Qt.Orientation.Horizontal)        
        splitter.setStyleSheet("""QSplitter::handle {background-color: #444;width: 2px;}""")

        self.editors = []
        # crea i due oggetti qscintilla
        for txt, title in ((text1, title1), (text2, title2)):
            container = QWidget()
            vlay      = QVBoxLayout(container)
            lbl       = QLabel(title)
            lbl.setFont(QFont("Arial", 10, QFont.Weight.DemiBold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vlay.addWidget(lbl)

            ed = QsciScintilla()
            ed.setText(txt)
            ed.setLexer(lexer)
            ed.setFont(font)
            ed.setMarginsFont(font)            
            ed.setReadOnly(True)                        
            ed.setMarginsFont(QFont("Courier New" , 9))
            ed.setTabWidth(int(tabulator))            
            ed.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
            # margine 0 con i numeri di riga (la larghezza del margine viene stabilita in base al numero di righe caricate nell'oggetto qscintilla)
            ed.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            ed.setMarginLineNumbers(0, True)                        
            ed.setMarginWidth(0, '0' + str(ed.lines()))                           
            # margine 1 con i simboli
            ed.setMarginType(1, QsciScintilla.MarginType.SymbolMargin)         
            ed.setMarginWidth(1, '00')                                        
            # colori di sfondo
            # queste istruzioni sono presenti anche in MSql_editor.py
            if dark_theme:                
                ed.setMarginsForegroundColor(QColor('white'))
                ed.setMarginsBackgroundColor(QColor('#242424'))
                ed.setFoldMarginColors(QColor('grey'),QColor('#242424'))                
                ed.setPaper(QColor('#242424'))  

            vlay.addWidget(ed)
            splitter.addWidget(container)
            self.editors.append(ed)

        # definizione dei simboli + e - per i due editor
        self.editors[0].markerDefine(QImage("icons:minus_red.png"), 0)        
        self.editors[1].markerDefine(QImage("icons:plus_green.png"), 1)        

        # toolbar per navigare fra le differenze
        toolbar = QToolBar()        
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        act_prev = QAction(QIcon("icons:up.png"), QCoreApplication.translate('diffviewer','Previous Difference') + ' (F1)', self)                        
        act_prev.setShortcut(QKeySequence("F1"))
        act_next = QAction(QIcon("icons:down.png"), QCoreApplication.translate('diffviewer','Next Difference') + ' (F3)', self)        
        act_next.setShortcut(QKeySequence("F3"))
        act_prev.triggered.connect(lambda: self.goto_diff(-1))
        act_next.triggered.connect(lambda: self.goto_diff(1))
        toolbar.addAction(act_prev)
        toolbar.addAction(act_next)

        # layout principale
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(splitter)

        # forzo lo splitter alla metà dei due editor
        splitter.setStretchFactor(0,5)        
        splitter.setStretchFactor(1,5)        

        # scroll sincronizzato
        for i, ed in enumerate(self.editors):
            ed.verticalScrollBar().valueChanged.connect(lambda v, src=i: self._sync_scroll(src, v))

        # richiamo evidenza delle differenze
        self.highlight_diff(text1, text2)

    def _sync_scroll(self, src_idx, value):
        """
           Sincronizzazione delle scrollbar
        """
        for i, ed in enumerate(self.editors):
            if i != src_idx:
                ed.verticalScrollBar().setValue(value)

    def highlight_diff(self, t1: str, t2: str):
        """
           Evidenziazione delle differenze tra le righe, usando i marcatori + e -
        """
        lines1  = t1.splitlines()
        lines2  = t2.splitlines()
        matcher = difflib.SequenceMatcher(None, lines1, lines2)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('delete', 'replace'):
                for r in range(i1, i2):
                    self.editors[0].markerAdd(r, 0)
                    self.diff_positions.append((0, r))
            if tag in ('insert', 'replace'):
                for r in range(j1, j2):
                    self.editors[1].markerAdd(r, 1)
                    self.diff_positions.append((1, r))

    def goto_diff(self, direction: int):
        """
           Funzione per scorrere il cursore tra le differenze dei due testi
        """
        if not self.diff_positions:
            return
        self.current_diff = (self.current_diff + direction) % len(self.diff_positions)
        ed_idx, line = self.diff_positions[self.current_diff]
        ed = self.editors[ed_idx]
        ed.setCursorPosition(line, 0)
        ed.setFocus()
        ed.ensureLineVisible(line)        
        ed.setSelection(line, 0, line, ed.lineLength(line))

    def closeEvent(self, event):
        """
           Evento di chiusura della window
        """
        # se utente ha richiesto di salvare la posizione della window...
        if self.window_pos:
            print('salva pos window')
            # salvo nel registro di sistema (regedit) la posizione della window
            self.settings.setValue("geometry", self.saveGeometry())            

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    sql1 = """SELECT * FROM clienti WHERE paese = 'IT';
UPDATE clienti SET attivo = 1 WHERE id = 5;
prova"""
    sql2 = """SELECT * FROM clienti WHERE paese = 'FR';
UPDATE clienti SET attivo = 0 WHERE id = 5;
prova
prova3"""

    viewer = classDiffViewer(
        True,
        '2',
        True,
        sql1, sql2,
        title1="Testo Origine",
        title2="Testo Modificato"
    )
    
    viewer.show()
    sys.exit(app.exec())