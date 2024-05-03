# -*- coding: utf-8 -*-

"""
 __  __ ____        _ 
|  \/  / ___|  __ _| |
| |\/| \___ \ / _` | |
| |  | |___) | (_| | |
|_|  |_|____/ \__, |_|
                 |_|  
                 
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 01/01/2023
 Descrizione...: Questo programma ha la "pretesa" di essere una sorta di piccolo editor SQL per ambiente Oracle....            
                 al momento si tratta più di un esperimento che di qualcosa di utilizzabile.
                 In questo programma sono state sperimentate diverse tecniche tra cui quelle per comprendere meglio la programmazione ad oggetti.
                 
 Note..........: La classe principale è MSql_win1_class che apre la window di menu e che contiene l'area mdi dove poi si raggrupperranno
                 le varie finestre dell'editor (gestito dalla classe MSql_win2_class). La window principale si collega con la 
                 secondaria dell'editor utilizzando un array che contiene i puntatori all'oggetto editor (MSql_win2_class). 
                 Quindi in MSql_win1_class vi è una continua ricerca all'oggetto editor di riferimento in modo da lavorare sull'editor corrente.
                 Tutta la parte di definizione grafica è stata creata tramite QtDesigner e i file da lui prodotti, convertiti tramite un'utilità, 
                 in classi Python da dare poi in pasto alla libreria QT.
"""

# Librerie di base
import sys 
import os 
import datetime 
import locale
import re
import traceback
# Librerie di data base
import cx_Oracle, oracle_my_lib
# Librerie grafiche QT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Librerie QScintilla
from PyQt5.Qsci import *
# Classe per la gestione delle preferenze
from preferences import preferences_class
# Definizione del solo tema dark
from dark_theme import dark_theme_definition
# Classi qtdesigner (win1 è la window principale, win2 la window dell'editor e win3 quella delle info di programma)
from MSql_editor_win1_ui import Ui_MSql_win1
from MSql_editor_win2_ui import Ui_MSql_win2
from MSql_editor_win3_ui import Ui_MSql_win3
# Classi qtdesigner per la ricerca e la sostituzione di stringhe di testo, per il posizionamento...
from goto_line_ui import Ui_GotoLineWindow
from history import history_class
from preferred_sql import preferred_sql_class
# Classe qtdesigner per la richiesta di connessione
from connect_ui import Ui_connect_window
# Classe per visualizzare la barra di avanzamento 
from avanzamento import avanzamento_infinito_class
# Utilità varie
from utilita import *
from utilita_database import *
from utilita_testo import *
# Libreria che permette, selezionata un'istruzione sql nell'editor di indentarla automaticamente
from sql_formatter.core import format_sql

# Tipi oggetti di database
Tipi_Oggetti_DB = { 'Tables':'TABLE',                    
                    'Packages body':'PACKAGE BODY',
                    'Packages': 'PACKAGE',                    
                    'Procedures':'PROCEDURE',
                    'Functions':'FUNCTION',
                    'Triggers':'TRIGGER',
                    'Views':'VIEW',
                    'Sequences':'SEQUENCE',
                    'Primary keys': 'PRIMARY_KEY',
                    'Unique keys': 'UNIQUE_KEY',
                    'Foreign keys': 'FOREIGN_KEY',
                    'Check keys': 'CHECK_KEY',
                    'Indexes': 'INDEXES',
                    'Synonyms': 'SYNONYM' }

###
# Var globali
###
# Oggetto connettore DB
v_global_connection = cx_Oracle
# Indica se si è connessi al DB
v_global_connesso = False
# Directory di lavoro del programma
v_global_work_dir = 'C:\\MSql\\'
# Lista di parole aggiuntive al lexer che evidenzia le parole nell'editor
v_global_my_lexer_keywords = []
# Oggetto che carica le preferenze tramite l'apposita classe (notare che già a questa istruzione le preferenze vengono caricate!)
o_global_preferences = preferences_class(v_global_work_dir + 'MSql.ini')
# Contiene le coordinate della main window
v_global_main_geometry = object

class My_MSql_Lexer(QsciLexerSQL):
    """
        Questa classe amplifica il dizionario di default del linguaggio SQL presente in QScintilla.
        In pratica aggiunge tutti i nomi di tabelle, viste, procedure, ecc. in modo vengano evidenziati
        Si basa sulla lista v_global_my_lexer_keywords che viene caricata quando ci si connette al DB
        In base al valore di index è possibile settare parole chiave di una determinata categoria
        1=parole primarie, 2=parole secondarie, 3=commenti, 4=classi, ecc.. usato 8 (boh!) 
    """
    def __init__(self, p_editor):        
        super(My_MSql_Lexer, self).__init__()  

        # salvo il puntatore all'editor all'interno del lexer
        self.p_editor = p_editor      

        # attivo le righe verticali che segnano le indentazioni
        self.p_editor.setIndentationGuides(o_global_preferences.indentation_guide)                
        # attivo i margini con + e - 
        self.p_editor.setFolding(p_editor.BoxedTreeFoldStyle, 2)
        # indentazione
        self.p_editor.setIndentationWidth(int(o_global_preferences.tab_size))
        self.p_editor.setAutoIndent(True)
        # tabulatore (in base alle preferenze...di base 2 caratteri)
        self.p_editor.setTabWidth(int(o_global_preferences.tab_size))   
        # evidenzia l'intera riga dove posizionato il cursore (grigio scuro e cursore bianco se il tema è dark)
        self.p_editor.setCaretLineVisible(True)
        if o_global_preferences.dark_theme:
            self.p_editor.setCaretLineBackgroundColor(QColor("#4a5157"))
            self.p_editor.setCaretForegroundColor(QColor("white"))
        else:
            self.p_editor.setCaretLineBackgroundColor(QColor("#FFFF99"))        
            self.p_editor.setCaretForegroundColor(QColor("black"))
        # attivo il margine 0 con la numerazione delle righe
        self.p_editor.setMarginType(0, QsciScintilla.NumberMargin)        
        self.p_editor.setMarginsFont(QFont("Courier New",9))                           
        # attivo il matching sulle parentesi con uno specifico colore
        self.p_editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.p_editor.setMatchedBraceBackgroundColor(QColor("#80ff9900"))
                        
        # attivo autocompletamento durante la digitazione 
        # (comprende sia le parole del documento corrente che quelle aggiunte da un elenco specifico)
        # attenzione! Da quanto ho capito, il fatto di avere attivo il lexer con linguaggio specifico (sql) questo prevale
        # sul funzionamento di alcuni aspetti dell'autocompletamento....quindi ad un certo punto mi sono arreso con quello che
        # sono riuscito a fare
        self.v_api_lexer = QsciAPIs(self)            
        # aggiungo tutti i termini di autocompletamento (si trovano all'interno di una tabella che viene generata a comando)
        self.p_editor.setAutoCompletionSource(QsciScintilla.AcsAll)                
        self.carica_dizionario_per_autocompletamento()                
        # indico dopo quanti caratteri che sono stati digitati dall'utente, si deve attivare l'autocompletamento
        self.p_editor.setAutoCompletionThreshold(3)  
        # attivo autocompletamento sia per la parte del contenuto del documento che per la parte di parole chiave specifiche
        self.p_editor.autoCompleteFromAll()

        # imposto il font dell'editor in base alle preferenze 
        if o_global_preferences.font_editor != '':
            v_split = o_global_preferences.font_editor.split(',')            
            v_font = QFont(str(v_split[0]),int(v_split[1]))
            if len(v_split) > 2 and v_split[2] == ' BOLD':
                v_font.setBold(True)
            self.setFont(v_font)    

        self.setFoldCompact(False)
        self.setFoldComments(True)
        self.setFoldAtElse(True)     

        # imposto gli elementi che servono all'interno dell'editor per attivare la funzione
        # tale per cui quando utente fa doppio click su una parola, vengono evidenziate tutte 
        # le parole uguali presenti nel testo!         
        self.p_editor.selectionChanged.connect(self.cambio_di_selezione_testo)        
        self.selection_lock = False
        self.SELECTION_INDICATOR = 4 

        # se è stato scelto il tema colori scuro --> reimposto i colori della sezione qscintilla
        # non sono riuscito a trovare altre strade per fare questa cosa
        if o_global_preferences.dark_theme:
            # colori di sfondo
            self.p_editor.setMarginsForegroundColor(QColor('white'))
            self.p_editor.setMarginsBackgroundColor(QColor('#242424'))
            self.p_editor.setFoldMarginColors(QColor('grey'),QColor('#242424'))
            self.setDefaultPaper(QColor('#242424'))
            self.setPaper(QColor('#242424'))  
            # colori delle parole
            self.setColor(QColor('white'), QsciLexerSQL.Default) 
            self.setColor(QColor('#608B4E'), QsciLexerSQL.Comment)
            self.setColor(QColor('#608B4E'), QsciLexerSQL.CommentLine)
            self.setColor(QColor('#608B4E'), QsciLexerSQL.CommentDoc) 
            self.setColor(QColor('#b5cea8'), QsciLexerSQL.Number)
            #self.setColor(QColor('#BA231E'), QsciLexerSQL.Keyword)            
            self.setColor(QColor('#00cb62'), QsciLexerSQL.Keyword)
            self.setColor(QColor('#00aaff'), QsciLexerSQL.DoubleQuotedString) 
            self.setColor(QColor('#ECBB76'), QsciLexerSQL.SingleQuotedString) 
            self.setColor(QColor('green'), QsciLexerSQL.PlusKeyword)
            self.setColor(QColor('green'), QsciLexerSQL.PlusPrompt) 
            self.setColor(QColor('cyan'), QsciLexerSQL.Operator) 
            self.setColor(QColor('#D4D4D4'), QsciLexerSQL.Identifier)
            self.setColor(QColor('green'), QsciLexerSQL.PlusComment) 
            self.setColor(QColor('green'), QsciLexerSQL.CommentLineHash) 
            self.setColor(QColor('green'), QsciLexerSQL.CommentDocKeyword)
            self.setColor(QColor('green'), QsciLexerSQL.CommentDocKeywordError) 
            self.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet5) 
            self.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet6)
            self.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet7) 
            self.setColor(QColor('#ac98ca'), QsciLexerSQL.KeywordSet8) 
            self.setColor(QColor('green'), QsciLexerSQL.QuotedIdentifier)
            self.setColor(QColor('green'), QsciLexerSQL.QuotedOperator)

    def keywords(self, index):
        """
           Funzione interna di QScintilla che viene automaticamente richiamata e carica le keyword di primo livello
           queste keyword sono le parole che QScintilla evidenzia con un colore specifico
        """
        global v_global_my_lexer_keywords        

        keywords = QsciLexerSQL.keywords(self, index) or ''        
        
        # l'indice 6 è stato messo dopo che sono iniziati gli esperimenti per evidenziare la parola selezionata con doppio click...prima era 8
        # anche se non compreso il significato di questa posizione!
        if index == 6:            
            if len(v_global_my_lexer_keywords) > 0:                                            
                v_new_keywords = ''
                for v_keyword in v_global_my_lexer_keywords:
                     v_new_keywords += v_keyword.lower() + ' '                                     
                return  v_new_keywords + keywords
        
        return keywords

    def carica_dizionario_per_autocompletamento(self):
        """
           Partendo dal file che contiene elenco termini di autocompletamento, ne leggo il contenuto e lo aggiungo all'editor
           Da notare come viene caricato di fatto un elenco sia con caratteri minuscoli che maiuscoli perché non sono riuscito
           a far funzionare la sua preferenza 
        """
        global v_global_my_lexer_keywords
                
        # come termini di autocompletamento prendo tutti gli oggetti che ho nella lista usata a sua volta per evidenziare le parole
        #for v_keywords in v_global_my_lexer_keywords:
        #    self.v_api_lexer.add(v_keywords.upper())                                    
        #    self.v_api_lexer.add(v_keywords.lower())                                    

        # carico il file con i termini per l'autocompletamento
        if os.path.isfile(v_global_work_dir + 'MSql_autocompletion.ini'):
            # carico i dati presenti nel file di testo (questo è stato creato con la voce di menu dello stesso MSql che si chiama "Create autocomplete dictonary")
            with open(v_global_work_dir + 'MSql_autocompletion.ini','r') as file:
                for v_riga in file:                                    
                    self.v_api_lexer.add(v_riga.upper())                                    
                    self.v_api_lexer.add(v_riga.lower())                                    
        
        self.v_api_lexer.prepare()        

    def autoCompletionWordSeparators(self):
        """
           Questa funzione è molto importante perché aggiunge al lexer il separatore delle parole (il punto) quando si usa l'autocompletamento!!!!!
           E' stato molto difficile trovare questa cosa!!!
        """
        return ['.']

    def cambio_di_selezione_testo(self):
        """
           Viene richiamata ogni volta che viene selezionato del testo
           E' usata per quando utente facendo doppio click su una parola, il programma evidenzia tutti i punti dove quella parola è presente nel testo
        """
        # la variabile lock viene usata per evitare problemi di ricorsione
        if self.selection_lock == False:
            self.selection_lock = True
            selected_text = self.p_editor.selectedText()
            self.clear_selection_highlights()
            if selected_text.isidentifier():
                self._highlight_selected_text(selected_text,case_sensitive=False,regular_expression=True)
            self.selection_lock = False        

    def clear_selection_highlights(self):
        """
           Pulisce gli indicatori delle parole 
        """        
        self.p_editor.clearIndicatorRange(0,0,self.p_editor.lines(),self.p_editor.lineLength(self.p_editor.lines()-1),self.SELECTION_INDICATOR)

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
        matches = self.find_all(highlight_text,case_sensitive,regular_expression,text_to_bytes=True,whole_words=True)
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
            self.p_editor.SendScintilla(scintilla_command,start,length)

    def _set_indicator(self,
                       indicator,
                       fore_color):
        """
           Set the indicator settings
        """
        self.p_editor.indicatorDefine(QsciScintilla.IndicatorStyle.StraightBoxIndicator,indicator)
        self.p_editor.setIndicatorForegroundColor(QColor(fore_color),indicator)
        self.p_editor.SendScintilla(QsciScintillaBase.SCI_SETINDICATORCURRENT,indicator)

    def set_indicator(self, indicator):
        """
          Select the indicator that will be used for use with
          Scintilla's indicator functionality
        """                
        if indicator == "selection":
            # indica il colore da dare alla selezione
            self._set_indicator(self.SELECTION_INDICATOR,'#643A93FF')        

    def find_all(self,
                 search_text,
                 case_sensitive=False,
                 regular_expression=False,
                 text_to_bytes=False,
                 whole_words=False):
        """
           Find all instances of a string and return a list of (line, index_start, index_end)
        """
        #Find all instances of the search string and return the list
        matches = self.index_strings_in_text(search_text,self.p_editor.text(),case_sensitive,regular_expression,text_to_bytes,whole_words)
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

def salvataggio_editor(p_save_as, p_nome, p_testo):
    """
        Salvataggio di p_testo dentro il file p_nome        
        Se p_save_as è True oppure il titolo dell'editor inizia con "!" --> viene richiesto di salvarlo come nuovo file
    """
    global o_global_preferences

    # se il primo carattere del titolo inizia con un punto esclamativo, significa che il file è stato creato partendo dall'object navigator
    # e quindi l'operazione di salva deve chiedere il nome del file e la posizione dove salvare
    if p_nome[0:1] == '!':
        p_save_as = True
        p_nome = p_nome[1:len(p_nome)]

    # se indicato il save as, oppure il file è nuovo e non è mai stato salvato --> richiedo un nuovo nome di file    
    if p_save_as or (not p_save_as and p_nome[0:8]=='Untitled'):
        # la dir di default è quella richiesta dall'utente o la Documenti        
        if o_global_preferences.save_dir == '':
            v_default_save_dir = QDir.homePath() + "\\Documents\\"
        else:
            v_default_save_dir = o_global_preferences.save_dir

        # propongo un nuovo nome di file dato dalla dir di default + il titolo ricevuto in input
        v_file_save_as = v_default_save_dir + '\\' + p_nome        
     
        p_nome = QtWidgets.QFileDialog.getSaveFileName(None, "Save a SQL file",v_file_save_as,"MSql files (*.msql);;SQL files (*.sql *.pls *.plb *.trg);;All files (*.*)") [0]                                  
        if not p_nome:
            message_error('Error saving')
            return 'ko'
        # se nel nome del file non è presente un suffisso --> imposto .msql            
        if p_nome.find('.') == -1:
            p_nome += '.msql'

    # procedo con il salvataggio
    try:
        if o_global_preferences.utf_8:
            # scrittura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                                            
            v_file = open(p_nome,'w',encoding='utf-8', newline='')
        else:
            # scrittura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
            v_file = open(p_nome,'w', newline='')
        v_file.write(p_testo)
        v_file.close()            
        return 'ok', p_nome
    except Exception as err:
        message_error('Error to write the file: ' + str(err))
        return 'ko', None

def titolo_window(p_titolo_file):
    """
       Partendo da p_titolo_file restituisce solo la parte di nome file da mettere come titolo della window
    """                       
    v_solo_nome_file = os.path.split(p_titolo_file)[1]
    v_solo_nome_file_senza_suffisso = os.path.splitext(v_solo_nome_file)[0]

    return v_solo_nome_file_senza_suffisso
    
#
#  __  __    _    ___ _   _  __        _____ _   _ ____   _____        __
# |  \/  |  / \  |_ _| \ | | \ \      / /_ _| \ | |  _ \ / _ \ \      / /
# | |\/| | / _ \  | ||  \| |  \ \ /\ / / | ||  \| | | | | | | \ \ /\ / / 
# | |  | |/ ___ \ | || |\  |   \ V  V /  | || |\  | |_| | |_| |\ V  V /  
# |_|  |_/_/   \_\___|_| \_|    \_/\_/  |___|_| \_|____/ \___/  \_/\_/   
#                                                                       
# Classe principale       
class MSql_win1_class(QtWidgets.QMainWindow, Ui_MSql_win1):    
    """
        Classe di gestione MDI principale 
        p_nome_file_da_caricare indica eventuale file da aprire all'avvio (capita quando da desktop si fa doppio click su icona di un file .msql)
    """       
    def __init__(self, p_nome_file_da_caricare):
        global o_global_preferences    
        global v_global_main_geometry   
        global v_global_work_dir 

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win1_class, self).__init__()        
        self.setupUi(self)
        # forzo la dimensione della finestra. Mi sono accorto che questa funzione, nella gestione MDI
        # è importante in quanto permette poi al connettore dello smistamento menu di funzionare sulla
        # prima finestra aperta....rimane comunque un mistero questa cosa.....
        self.showNormal()      
        # dimensioni della window
        self.carico_posizione_window()  

        ###
        # Dalle preferenze carico il menu con elenco dei server e degli user
        # Per i primi due server collego lo shortcut F1 e F2
        ###
        self.action_elenco_server = []
        self.action_elenco_user = []
        if len(o_global_preferences.elenco_server) > 0:
            v_i = 1
            self.menuServer.addSeparator()
            self.action_elenco_server = []
            for rec in o_global_preferences.elenco_server:
                v_qaction = QtWidgets.QAction()
                v_qaction.setCheckable(True)
                v_qaction.setText(rec[0])
                v_qaction.setData('MENU_SERVER')
                if v_i == 1:
                    v_qaction.setShortcut('F1')
                elif v_i == 2:
                    v_qaction.setShortcut('F2')
                v_i += 1            
                self.action_elenco_server.append(v_qaction)
                self.menuServer.addAction(v_qaction)               

        if len(o_global_preferences.elenco_user) > 0:
            self.menuServer.addSeparator()
            self.action_elenco_user = []
            for rec in o_global_preferences.elenco_user:
                v_qaction = QtWidgets.QAction()
                v_qaction.setCheckable(True)
                v_qaction.setText(rec[0])
                v_qaction.setData('MENU_USER')
                self.action_elenco_user.append(v_qaction)
                self.menuServer.addAction(v_qaction)  

        ###
        # Se richiesto il tema scuro forzo il colore scuro sull'area Mdi (non sono riuscito a farlo usando il tema!)             
        ###
        if o_global_preferences.dark_theme:
            self.mdiArea.setBackground(QColor('#242424'))                                    

        ###
        # Aggiunta di windget alla statusbar con: flag editabilità, numero di caratteri, indicatore di overwrite, ecc..
        ###                                        
        # Coordinate cursore dell'editor di testo
        self.l_cursor_pos = QLabel()
        self.l_cursor_pos.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_cursor_pos)                
        self.l_cursor_pos.setText("Ln: 1  Col: 1")
        # Indicatore editabilità
        self.l_tabella_editabile = QLabel("Editable table: Disabled")
        self.l_tabella_editabile.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.l_tabella_editabile.setStyleSheet('color: black;')
        self.statusBar.addPermanentWidget(self.l_tabella_editabile)                
        # Numero totale di righe di testo
        self.l_num_righe_e_char = QLabel()
        self.l_num_righe_e_char.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_num_righe_e_char)                
        self.l_num_righe_e_char.setText("Lines: 0 , Length: 0")        
        # Stato attivazione inserito di testo o overwrite
        self.l_overwrite_enabled = QLabel("INS")
        self.l_overwrite_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_overwrite_enabled)
        # Stato attivazione codifica utf-8
        self.l_utf8_enabled = QLabel()
        self.l_utf8_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_utf8_enabled)        
        # Stato end of line
        self.l_eol = QLabel()
        self.l_eol.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_eol)        
        # Informazioni sulla connessione
        self.l_connection = QLabel("Connection:")
        self.l_connection.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.l_connection.setStyleSheet('color: black;')
        self.statusBar.addPermanentWidget(self.l_connection)                

        ###
        # definizione della dimensioni dei dock laterali (sono 3, vengono raggruppati e definite le proporzioni)
        ###
        self.docks = self.dockWidget, self.dockWidget_2
        widths = 10, 10
        self.resizeDocks(self.docks, widths, Qt.Vertical)        

        ###
        # Var per la gestione degli editor
        ###

        # array interno che tiene traccia elenco file recenti
        self.elenco_file_recenti = []            
        # var che indica il numero di window2-editor 
        self.v_num_window2 = 0                
        # definisco la lista che contiene il link a tutti gli oggetti window2 degli editor aperti
        self.o_lst_window2 = []
        # per smistare i segnali che arrivano dal menù che non è collegato con le subwindow, utilizzo
        # un apposito connettore
        self.menuBar.triggered[QAction].connect(self.smistamento_voci_menu)        

        ###        
        # eseguo la connessione automatica di default (questa cosa va rivista perché ora l'elenco è dinamico!)
        ###
        self.e_server_name = 'BACKUP_815'
        self.e_user_name = 'SMILE'
        self.e_password = 'SMILE'        
        self.e_user_mode = 'Normal'        
        self.slot_connetti()           

        ###
        # Definizione della struttura per gestione elenco oggetti DB (object navigator)       
        ###
        self.oggetti_db_lista = QtGui.QStandardItemModel()        
        self.oggetti_db_elenco.setModel(self.oggetti_db_lista)
        # per default carico l'elenco di tutte le tabelle (selezionando la voce Tables=1 nell'elenco)
        self.oggetti_db_scelta.setCurrentIndex(1)
        # per object viewer e nel caso di package, riporta la struttura delle procedure-funzioni che il package contiene
        # per la struttura di questa var fare riferimento alla funzione estrai_procedure_function che si trova in utilita_testo.py
        self.oggetti_db_lista_proc_func = object        

        ###
        # Imposto default in base alle preferenze (setto anche le opzioni sulle voci di menu)
        ###                
        self.actionUTF_8_Coding.setChecked(o_global_preferences.utf_8)
        self.slot_utf8()                
        self.actionMake_table_editable.setChecked(o_global_preferences.editable)
        self.slot_editable()
        self.actionShow_end_of_line.setChecked(o_global_preferences.end_of_line)
        self.slot_end_of_file()
        self.actionAutoColumnResize.setChecked(o_global_preferences.auto_column_resize)        
        
        ###
        # Imposto var con la geometria della window principale
        ###
        v_global_main_geometry = self.frameGeometry()

        ###
        # Carico elenco dei file recenti
        ###
        self.aggiorna_elenco_file_recenti(None)
        
        ###
        # Se è stato indicato un nome di file da caricare all'avvio
        ###
        if p_nome_file_da_caricare != '':        
            # apro un file            
            v_titolo, v_contenuto_file = self.openfile(p_nome_file_da_caricare)        
            v_azione = QtWidgets.QAction()
            v_azione.setText('Open_db_obj')            
            self.smistamento_voci_menu(v_azione, v_titolo, v_contenuto_file)        
        ###        
        # Altrimenti apro una nuova finestra di editor simulando il segnale che scatta quando utente sceglie "New"
        # Attenzione! L'apertura dell'editor è stata posta alla fine di tutto il procedimento di carico del main
        #             in quanto non veniva caricata elenco autocompletamento dell'editor. La cosa strana è che se
        #             dopo l'apertura si apriva un nuovo file, da quel momento l'autocompletamento partiva.
        ### 
        else:
            v_azione = QtWidgets.QAction()
            v_azione.setText('New')
            self.smistamento_voci_menu(v_azione)      

        ###
        # Se è presente il file dei termini di dizionario, controllo se più vecchio di 2 settimane e avverto che andrebbe rigenerato
        ###        
        if os.path.isfile(v_global_work_dir + 'MSql_autocompletion.ini'):  
            v_data_ultima_modifica = datetime.datetime.fromtimestamp(os.stat(v_global_work_dir + 'MSql_autocompletion.ini').st_mtime)
            if (datetime.datetime.now() - v_data_ultima_modifica) > datetime.timedelta(days=14):
                message_info("The dictionary is more than two weeks old!" + chr(10) + "Remember to regenerate it!" + chr(10) + "See the menu Tools/Autocomplete dictionary ;-)")            

    def oggetto_win2_attivo(self):
        """
            Restituisce l'oggetto di classe MSql_win2_class riferito alla window di editor attiva
        """        
        # Ricavo quale sia la window di editor attiva in questo momento
        self.window_attiva = self.mdiArea.activeSubWindow()            
        if self.window_attiva is not None:                                             
            # scorro la lista-oggetti-editor fino a quando non trovo l'oggetto che ha lo stesso titolo della window attiva
            for i in range(0,len(self.o_lst_window2)):
                if not self.o_lst_window2[i].v_editor_chiuso:
                    if self.o_lst_window2[i].objectName() == self.window_attiva.objectName():
                        return self.o_lst_window2[i]
        return None                    

    def smistamento_voci_menu(self, p_slot, p_oggetto_titolo_db=None, p_oggetto_testo_db=None):
        """
            Contrariamente al solito, le voci di menù non sono pilotate da qtdesigner ma direttamente
            dal connettore al menu che riporta a questa funzione che poi si occupa di fare lo smistamento.
            Ci sono voci di menù che sono "generiche", altre invece devono agire sul contenuto della finestra
            attiva. Per questo è stata creata una lista che contiene tutti gli oggetti aperti e quindi,
            di volta in volta viene ricercata la window-oggetto attiva ed elaborata la voce di menu direttamente
            per quella window-oggetto
            Parametri: p_slot = Oggetto di tipo event che indica l'evento 
                       p_oggetto_titolo_db = Serve solo quando si vuole aprire un oggetto di testo db (titolo della window)
                       p_oggetto_testo_db = Serve solo quando si vuole aprire un oggetto di testo db (contenuto dell'editor)
        """
        global o_global_preferences                
        global v_global_main_geometry
        
        #print('Voce di menù --> ' + str(p_slot.data()))    
        #print('Voce di menù --> ' + p_slot.text())    

        # Carico l'oggetto di classe MSql_win2_class attivo in questo momento         
        o_MSql_win2 = self.oggetto_win2_attivo()
        
        # Cambio di connessione
        if str(p_slot.data()) == 'MENU_SERVER':
            for rec in o_global_preferences.elenco_server:
                if rec[0] == p_slot.text():                    
                    self.e_server_name = rec[1]                    
            self.slot_connetti()               
        elif str(p_slot.data()) == 'MENU_USER':         
            for rec in o_global_preferences.elenco_user:
                if rec[0] == p_slot.text():
                    self.e_user_name = rec[1]
                    self.e_password = rec[2]
                    self.e_user_mode = 'Normal'                    
            self.slot_connetti()            
        # Cambio user specificato da utente
        elif p_slot.text() == 'Connect to specific database':
                self.richiesta_connessione_specifica()        
        # Apertura di un nuovo editor o di un file recente
        elif p_slot.text() in ('New','Open','Open_db_obj') or str(p_slot.data()) == 'FILE_RECENTI':
            # se richiesto un file recente
            if str(p_slot.data()) == 'FILE_RECENTI':
                # apro il file richiesto
                v_titolo, v_contenuto_file = self.openfile(p_slot.text())
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto Open...
            elif p_slot.text() == 'Open':
                # apro un file tramite dialog box
                v_titolo, v_contenuto_file = self.openfile(None)                
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto Open_db_obj...
            elif p_slot.text() == 'Open_db_obj':
                # apro un file
                v_titolo = p_oggetto_titolo_db
                v_contenuto_file = p_oggetto_testo_db 
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto New, aumento il numeratore delle window
            else:
                self.v_num_window2 += 1
                v_titolo = 'Untitled' + str(self.v_num_window2)
                v_contenuto_file = None
            # creo una nuovo oggetto editor (gli passo il titolo e eventuale contenuto del file e gli oggetti della statusbar)
            o_MSql_win2 = MSql_win2_class(v_titolo, 
                                          v_contenuto_file, 
                                          self)
            # l'oggetto editor lo salvo all'interno di una lista in modo sia reperibile quando necessario
            self.o_lst_window2.append(o_MSql_win2)        
            # collego l'oggetto editor ad una nuova finestra del gestore mdi e la visualizzo, massimizzandola (imposto icona vuota!)
            # da notare come il nome di file completo di fatto viaggia all'interno del nome degli oggetti
            sub_window = self.mdiArea.addSubWindow(o_MSql_win2)                  
            sub_window.setObjectName(o_MSql_win2.objectName())
            sub_window.setWindowIcon(QtGui.QIcon())                              
            sub_window.show()  
            sub_window.showMaximized()  
        # Codifica utf-8
        elif p_slot.text() == 'UTF-8 Coding':
            if self.actionUTF_8_Coding.isChecked():
                o_global_preferences.utf_8 = True
            else:
                o_global_preferences.utf_8 = False
            # aggiorno la label sulla statusbar
            self.slot_utf8()        
        # Gestione preferenze
        elif p_slot.text() == 'Preferences':
            self.slot_preferences()
        # Rendo l'output dell'sql editabile
        elif p_slot.text() == 'Make table editable':
            if self.actionMake_table_editable.isChecked():
                o_global_preferences.editable = True
            else:                
                o_global_preferences.editable = False
            # aggiorno status bar e aggiorno oggetti
            self.slot_editable()
        # Uscita dal programma (invoco l'evento di chiusura della main window)
        elif p_slot.text() == 'Exit':
            v_event_close = QtGui.QCloseEvent()
            self.closeEvent(v_event_close)        
        # Riorganizzo le window in modalità cascata
        elif p_slot.text() == 'Cascade':
            self.mdiArea.cascadeSubWindows()
        # Riorganizzo le window in modalità piastrelle
        elif p_slot.text() == 'Tile':
            self.mdiArea.tileSubWindows()           
        # Apro file di help
        elif p_slot.text() == 'Help':
            os.system("start help\\MSql_help.html")
        # Visualizzo program info
        elif p_slot.text() == 'Program info':            
            self.program_info = MSql_win3_class()
            self.program_info.show()
        # visualizza l'objects navigator
        elif p_slot.text() == 'Objects Navigator':
            self.dockWidget.show()
        # visualizza l'object viewer
        elif p_slot.text() == 'Object Viewer':
            self.dockWidget_2.show()
        # visualizza l'history
        elif p_slot.text() == 'History':
            self.slot_history()
        # visualizza la gestione degli sql preferiti
        elif p_slot.text() == 'My preferred SQL':
            self.slot_preferred_sql()
        # Indico che l'output sql ha le colonne con larghezza auto-adattabile
        elif p_slot.text() == 'Auto Column Resize':
            self.slot_menu_auto_column_resize()
                
        # Queste voci di menu che agiscono sull'oggetto editor, sono valide solo se l'oggetto è attivo
        if o_MSql_win2 is not None:
            # Salvataggio del file
            if p_slot.text() == 'Save':
                v_ok, v_nome_file = salvataggio_editor(False, o_MSql_win2.objectName(), o_MSql_win2.e_sql.text())
                if v_ok == 'ok':
                    o_MSql_win2.v_testo_modificato = False
                    o_MSql_win2.setObjectName(v_nome_file)
                    o_MSql_win2.setWindowTitle(titolo_window(v_nome_file))
                    self.aggiorna_elenco_file_recenti(v_nome_file)
                    self.window_attiva.setObjectName(v_nome_file) # notare come il nome della window va forzato anche sulla window attiva
            # Salvataggio del file come... (semplicemente non gli passo il titolo)
            elif p_slot.text() == 'Save as':
                v_ok, v_nome_file = salvataggio_editor(True, o_MSql_win2.objectName(), o_MSql_win2.e_sql.text())
                if v_ok == 'ok':                    
                    o_MSql_win2.v_testo_modificato = False                    
                    o_MSql_win2.setObjectName(v_nome_file)                    
                    o_MSql_win2.setWindowTitle(titolo_window(v_nome_file))
                    self.aggiorna_elenco_file_recenti(v_nome_file)                    
                    self.window_attiva.setObjectName(v_nome_file) # notare come il nome della window va forzato anche sulla window attiva
            # Creazione del dizionario termini per autocompletamento dell'editor
            elif p_slot.text() == 'Autocomplete dictionary':
                self.crea_dizionario_per_autocompletamento()
            # Visualizza il carattere di end of line, ritorno a capo
            elif p_slot.text() == 'Show end of line':
                # riporto la preferenza di menu dentro l'oggetto delle preferenze 
                if self.actionShow_end_of_line.isChecked():
                    o_global_preferences.end_of_line = True
                else:
                    o_global_preferences.end_of_line = False
                # attivo la scelta su tutti gli editor aperti
                self.slot_end_of_file()
            # Ricerca di testo
            elif p_slot.text() == 'Find':
                v_global_main_geometry = self.frameGeometry()                                
                o_MSql_win2.slot_find()
            # Sostituzione di testo
            elif p_slot.text() == 'Find and Replace':
                v_global_main_geometry = self.frameGeometry()
                o_MSql_win2.slot_find_e_replace()
            # Mappa delle procedure/funzioni
            elif p_slot.text() == 'Map procedures/functions':
                v_global_main_geometry = self.frameGeometry()
                o_MSql_win2.slot_map()
            # Selezione del testo rettangolare
            elif p_slot.text() == 'Rect selection':                
                message_info('There are 2 ways to switch to rectangular selection mode' + chr(10) + chr(10) + '1. (Keyboard and mouse) Hold down ALT while left clicking, then dragging' + chr(10) + chr(10) + '2. (Keyboard only) Hold down ALT+Shift while using the arrow keys')                                
            # Commenta il testo selezionato
            elif p_slot.text() == 'Comment selection':                
                o_MSql_win2.slot_commenta()
            # Decommenta il testo selezionato
            elif p_slot.text() == 'Uncomment selection':                
                o_MSql_win2.slot_scommenta()
            # Uppercase del testo selezionato
            elif p_slot.text() == 'Uppercase':                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_UPPERCASE)
            # Lowercase del testo selezionato
            elif p_slot.text() == 'Lowercase':                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_LOWERCASE)
            # Compressione di tutti i livelli
            elif p_slot.text() == 'Fold/Unfold All':
                o_MSql_win2.e_sql.foldAll()
            # Zoom In del testo
            elif p_slot.text() == 'Zoom In':
                o_MSql_win2.e_sql.zoomIn()
            # Zoom Out del testo
            elif p_slot.text() == 'Zoom Out':
                o_MSql_win2.e_sql.zoomOut()
            # Annulla il testo
            elif p_slot.text() == 'Undo':
                o_MSql_win2.e_sql.undo()
            # Ripristina il testo
            elif p_slot.text() == 'Redo':
                o_MSql_win2.e_sql.redo()
            # Taglia il testo
            elif p_slot.text() == 'Cut':
                o_MSql_win2.e_sql.cut()
            # Copia il testo
            elif p_slot.text() == 'Copy':
                o_MSql_win2.e_sql.copy()
            # Incolla il testo
            elif p_slot.text() == 'Paste':
                o_MSql_win2.e_sql.paste()
            # Seleziona tutto
            elif p_slot.text() == 'Select All':
                o_MSql_win2.e_sql.selectAll()
            # Vai alla riga numero
            elif p_slot.text() == 'Go To Line':
                o_MSql_win2.slot_goto_line()
            # Esecuzione dell'sql
            elif p_slot.text() == 'Execute':                
                v_ok = o_MSql_win2.slot_esegui()
                if v_ok == 'ko':
                    message_error('Script stopped for error!')
            # Commit
            elif p_slot.text() == 'Commit':
                o_MSql_win2.slot_commit_rollback('Commit')
            # Rollback
            elif p_slot.text() == 'Rollback':
                o_MSql_win2.slot_commit_rollback('Rollback')
            # Ricerca di un oggetto
            elif p_slot.text() == 'Find object':                
                message_info('Position yourself in the text-editor on the object and press F12')                                
            # Query veloce sul nome di tabella
            elif p_slot.text() == 'Quick query':                
                message_info('Position yourself in the text-editor on the table and press F11')                                
            # Carico il risultato sql alla prima riga
            elif p_slot.text() == 'Go to Top':
                o_MSql_win2.slot_go_to_top()
            # Carico il risultato sql fino all'ultima riga
            elif p_slot.text() == 'Go to End':
                o_MSql_win2.slot_go_to_end()        
            # Esporto in formato Excel
            elif p_slot.text() == 'Export to Excel-CSV':
                o_MSql_win2.slot_export_to_excel_csv()
            # Pulizia di tutto l'output
            elif p_slot.text() == 'Clear result,output':                 
                o_MSql_win2.slot_clear('ALL')                               
            # Selezione del font per l'editor
            elif p_slot.text() == 'Font editor selector':
                o_MSql_win2.slot_font_editor_selector(None)
            # Selezione del font per l'output di sql
            elif p_slot.text() == 'Font output selector':
                o_MSql_win2.slot_font_result_selector(None)
            # Creo lo script per la modifica dei dati
            elif p_slot.text() == 'Script the changed data':
                o_MSql_win2.slot_save_modified_data()
            # Prendo il testo selezionato e lo riformatto (esempio istruzione SQL che viene reindentata)
            elif p_slot.text() == 'Format SQL statement':
                o_MSql_win2.slot_format_sql_statement()

    def slot_utf8(self):
        """
           Aggiorna la label nella statusbar relativa alla codifica utf-8
        """
        global o_global_preferences
        
        # se codifica utf-8 abilitata, la evidenzio
        if o_global_preferences.utf_8:
            self.l_utf8_enabled.setText('UTF-8')
        else:
            self.l_utf8_enabled.setText("ANSI")

    def slot_editable(self):
        """
           Gestione della modifica dei risultati di una query
        """
        global o_global_preferences
        
        # se edit abilitato, la evidenzio
        if o_global_preferences.editable:            
            self.l_tabella_editabile.setText("Editable table: Enabled")                        
            self.l_tabella_editabile.setStyleSheet('color: red;')      
            self.l_tabella_editabile.setStyleSheet('background-color: red ;color: white;')             
        else:
            self.l_tabella_editabile.setText("Editable table: Disabled")            
            if o_global_preferences.dark_theme:                
                self.l_tabella_editabile.setStyleSheet('color: white;')      
            else:
                self.l_tabella_editabile.setStyleSheet('color: black;')      

        # scorro la lista-oggetti-editor e modifico lo stato edit di ognuno
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso:
                obj_win2.set_editable()

    def slot_end_of_file(self):
        """
           Gestione visualizzazione del carattere di fine riga
        """
        global o_global_preferences

        # scorro la lista-oggetti-editor e modifico tutti gli editor aperti
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso:
                obj_win2.set_show_end_of_line()

    def aggiorna_elenco_file_recenti(self, p_elemento):
        """
           Carica elenco dei file recenti all'interno dell'apposito menu
           Se p_elemento è passato allora non viene caricato elenco da file ma viene aggiunto
           all'elenco p_elemento. Questa modalità viene usata mano a mano che si aprono i file

           Nota! La gestione dei file recenti si basa sul fatto di attaccare alla voce di menu dei recenti
                 altre voci. Ho usato il meccanismo per cui come testo viene indicato il nome del file e 
                 viene impostata una sorta di label interna dal nome 'FILE_RECENTI'; questa label verrà
                 usata durante lo smistamento delle voci di menu per capire che la voce selezionata appartiene
                 all'elenco dei file recenti
        """
        global v_global_work_dir

        # se elemento non passato --> carico elenco dei files recenti da disco        
        if p_elemento is None:
            if os.path.isfile(v_global_work_dir + 'MSql_recent_files.ini'):
                with open(v_global_work_dir + 'MSql_recent_files.ini','r') as file:
                    v_elenco_file_recenti = []
                    for v_nome_file in file:                                        
                        v_nome_file = v_nome_file.rstrip('\n')
                        # il file viene aggiunto all'elenco solo se esiste!
                        if os.path.isfile(v_nome_file):                            
                            v_action = QAction(self)
                            v_action.setText(v_nome_file)
                            v_action.setData('FILE_RECENTI')
                            # aggiungo a video la voce di menu
                            self.menuRecent_file.addAction(v_action)
                            # carico array
                            v_elenco_file_recenti.append(v_nome_file)
                    
                    # prendo la lista con elenco appena caricato e lo inserisco al contrario nella struttura effettiva dei file recenti
                    for v_index in range(len(v_elenco_file_recenti),0,-1):                           
                            self.elenco_file_recenti.append(v_elenco_file_recenti[v_index-1])        
        # se elemento passato ...        
        else:
            # elemento è presente in elenco...
            if p_elemento in self.elenco_file_recenti:                            
                # lo elimino dalla posizione attuale in quanto deve andare in fondo alla lista
                self.elenco_file_recenti.remove(p_elemento)
            
            # aggiungo nuova voce all'array interno (viene posto in fondo!)
            self.elenco_file_recenti.append(p_elemento)
            
            # elimino tutte le voci dal menu dei recenti
            self.menuRecent_file.clear()            
            # apro il file che contiene i recenti per salvare i dati (salverò solo gli ultimi 10 files)
            v_file_recenti = open(v_global_work_dir + 'MSql_recent_files.ini','w')            
            # scorro array al contrario (così tengo il più recente in cima alla lista) e ricarico il menu a video            
            v_conta_righe = 0
            for v_index in range(len(self.elenco_file_recenti),0,-1):                
                if v_conta_righe < 10:                    
                    v_action = QAction(self)
                    v_action.setText(self.elenco_file_recenti[v_index-1])
                    v_action.setData('FILE_RECENTI')
                    self.menuRecent_file.addAction(v_action)                                    
                    v_file_recenti.write(self.elenco_file_recenti[v_index-1]+'\n')                                            
                    v_conta_righe += 1
            # chiudo il file
            v_file_recenti.close()    
                     
    def openfile(self, p_nome_file):
        """
           Apertura di un file...restituisce il nome del file e il suo contenuto
           Se p_nome_file viene passato allora viene letto direttamente il file indicato

           Questa funzione restituisce il nome del file e il suo contenuto
        """      
        global o_global_preferences

        # se richiesto di aprire file passando dalla dialog box di file requester
        if p_nome_file is None:
            # la dir di default è quella richiesta dall'utente o la Documenti        
            if o_global_preferences.open_dir == '':
                v_default_open_dir = QDir.homePath() + "\\Documents\\"
            else:
                v_default_open_dir = o_global_preferences.open_dir

            # dialog box per richiesta file
            v_fileName = QFileDialog.getOpenFileName(self, "Open File", v_default_open_dir ,"MSql files (*.msql);;SQL files (*.sql *.pls *.plb *.trg);;All files (*.*)")                
        # .. altrimenti ricevuto in input un file specifico
        else:
            v_fileName = []
            v_fileName.append(p_nome_file)

        # è richiesto di aprire un file...
        if v_fileName[0] != "":
            # controllo se il file è già aperto in altra finestra di editor
            for obj_win2 in self.o_lst_window2:
                if not obj_win2.v_editor_chiuso and  obj_win2.objectName() == v_fileName[0]:
                    message_error('This file is already open!')
                    return None,None
            # procedo con apertura
            try:
                # apertura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
                if o_global_preferences.utf_8 :                    
                    v_file = open(v_fileName[0],'r',encoding='utf-8',newline='')
                # apertura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
                else:                    
                    v_file = open(v_fileName[0],'r',newline='')
                # aggiungo il nome del file ai file recenti                
                self.aggiorna_elenco_file_recenti(v_fileName[0])
                # restituisco il nome e il contenuto del file
                return v_fileName[0], v_file.read()
            except Exception as err:
                message_error('Error to opened the file: ' + str(err))
                return None, None
        else:
            return None, None
    
    def closeEvent(self, event):
        """
           Intercetto l'evento di chiusura e chiudo tutte le istanze del/i editor aperto/i
           Questa funzione sovrascrive quella nativa di QT 
        """     
        # scorro la lista-oggetti-editor e richiamo l'evento di chiusura del singolo oggetto 
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso:
                v_event_close = QtGui.QCloseEvent()
                obj_win2.closeEvent(v_event_close)        
        # controllo se tutte le window sono state chiuse
        v_chiudi_app = True
        for obj_win2 in self.o_lst_window2:        
            if not obj_win2.v_editor_chiuso:                
                v_chiudi_app = False
        # se tutte le window sono chiuse, controllo se ci sono ancora transazioni aperte e poi chiudo il programma
        if v_chiudi_app:            
            self.controllo_transazioni_aperte()            
            self.salvo_posizione_window()
            # chiudo tutto (anche eventuali window di ricerca, ecc.)
            QApplication.closeAllWindows()
        # altrimenti ignoro l'evento di chiusura
        else:
            event.ignore()

    def carico_posizione_window(self):
        """
           Leggo dal file la posizione della window (se richiesto dalle preferenze)
        """
        global o_global_preferences
        global v_global_work_dir

        # se utente ha richiesto di salvare la posizione della window...
        if o_global_preferences.remember_window_pos:
            if os.path.isfile(v_global_work_dir + 'Msql_window_pos.ini'):
                v_file = open(v_global_work_dir + 'Msql_window_pos.ini','r')
                # al momento leggo solo la prima riga che contiene la dimensione della mainwindow
                v_my_window_pos = v_file.readline().rstrip('\n').split()                                
                if v_my_window_pos[0] == 'MainWindow':
                    # finestra massimizzata
                    if v_my_window_pos[1] == 'MAXIMIZED':
                        self.showMaximized()
                    # finestra a dimensione specifica
                    else:
                        self.setGeometry(int(v_my_window_pos[1]), int(v_my_window_pos[2]), int(v_my_window_pos[3]), int(v_my_window_pos[4]))    
                v_file.close()
                        
    def salvo_posizione_window(self):
        """
           Salvo in un file la posizione della window (se richiesto dalle preferenze)
           Questo salvataggio avviene automaticamente alla chiusura di MSql
        """
        global o_global_preferences
        global v_global_work_dir

        # se utente ha richiesto di salvare la posizione della window...
        if o_global_preferences.remember_window_pos:
            v_file = open(v_global_work_dir + 'Msql_window_pos.ini','w')
            if self.isMaximized():
                v_file.write("MainWindow MAXIMIZED")
            else:
                o_pos = self.geometry()            
                o_rect = o_pos.getRect()                        
                v_file.write("MainWindow " + str(o_rect[0]) + " " + str(o_rect[1]) + " " +  str(o_rect[2]) + " " + str(o_rect[3]))
            v_file.close()
    
    def controllo_transazioni_aperte(self):
        """
           Controllo se per la connessione corrente ci sono delle transazioni aperte 
           e richiesto all'utente se vuole salvarle
        """        
        global v_global_connection
        global v_global_connesso

        # se c'è una connessione aperta al DB
        if v_global_connesso:
            # controllo se ci sono delle transazioni in sospeso
            v_cursore = v_global_connection.cursor()
            v_select = 'SELECT COUNT(*) CONTA FROM (SELECT DBMS_TRANSACTION.STEP_ID STEP_ID FROM DUAL) WHERE STEP_ID IS NOT NULL'
            try:
                v_cursore.execute(v_select)
            # se riscontrato errore (persa connessione al db) --> emetto sia codice che messaggio
            except cx_Oracle.Error as e:                                                            
                errorObj, = e.args    
                message_error("Error: " + errorObj.message)                                            
                return 'ko'

            v_conta = v_cursore.fetchone()[0]            
            # se ci sono transazioni in sospeso richiedo come procedere
            if v_conta != 0:
                # in caso affermativo --> eseguo la commit
                if message_warning_yes_no('MSql detected that the current session has an open transaction. Do you want to perform commit before closing the session?') == 'Yes':
                    v_cursore.execute('COMMIT')
            # chiusura del cursore            
            v_cursore.close()

    def slot_connetti(self):
        """
           Esegue connessione a Oracle
        """
        global v_global_connesso   
        global v_global_connection
        global v_global_my_lexer_keywords
        global o_global_preferences   

        # Default del colore (viene poi superato da eventuali preferenze)
        v_color = '#ffffff'
        v_background = 'black'
        
        ###
        # Refresh del menu
        ###
        # disattivo la check sulla parte server e user (preferiti)
        for action in self.action_elenco_server:            
            action.setChecked(False)
        for action in self.action_elenco_user:
            action.setChecked(False)

        # ricerco posizione nei preferiti e attivo la corrispondente voce di menu (elenco server)
        # notare come attraverso una triangolazione trovo quale voce attivare (usando quanto contenuto nelle preferenze)
        for rec in o_global_preferences.elenco_server:
            if rec[1] == self.e_server_name:
                for action in self.action_elenco_server:            
                    if action.text() == rec[0]:
                        action.setChecked(True)            
                        v_color = rec[2]                                                      

        # ricerco posizione nei preferiti e attivo la corrispondente voce di menu (elenco user)
        # notare come attraverso una triangolazione trovo quale voce attivare (usando quanto contenuto nelle preferenze)
        for rec in o_global_preferences.elenco_user:
            if rec[1] == self.e_user_name:
                for action in self.action_elenco_user:            
                    if action.text() == rec[0]:
                        action.setChecked(True)            

        ###
        # Connessione
        ###

        # se c'è una connessione aperta, controllo se ci sono transazioni aperte
        # verrà evetualmente richiesto se effettuare la commit
        self.controllo_transazioni_aperte()
            
        # scorro la lista-oggetti-editor...
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso and v_global_connesso:        
                # ...e chiudo eventuale cursore attualmente presente
                if obj_win2.v_cursor is not None:
                    obj_win2.v_cursor.close()
                                    
        # apro connessione
        try:
            # se c'è già una connessione --> la chiudo
            if v_global_connesso:
                v_global_connection.close()
            # inizializzo libreria oracle    
            oracle_my_lib.inizializzo_client()              
            # connessione al DB (eventualmente come dba)
            if self.e_user_mode == 'SYSDBA':               
                v_global_connection = cx_Oracle.connect(user=self.e_user_name, password=self.e_password, dsn=self.e_server_name, mode=cx_Oracle.SYSDBA)                        
            else:
                v_global_connection = cx_Oracle.connect(user=self.e_user_name, password=self.e_password, dsn=self.e_server_name)                        
            # imposto var che indica la connessione a oracle
            v_global_connesso = True
            # apro un cursore finalizzato alla gestione degli oggettiDB
            self.v_cursor_db_obj = v_global_connection.cursor()            
        except:
            message_error('Error to oracle connection!')    
            v_global_connesso = False

        # Se mi collego come SYSDBA coloro di rosso
        if self.e_user_mode == 'SYSDBA':
            v_background = 'red'

        # sulla statusbar, aggiorno la label della connessione        
        self.l_connection.setText("Connection: " + self.e_server_name + "/" + self.e_user_name)     
        if o_global_preferences.dark_theme:                       
            self.l_connection.setStyleSheet('background-color: ' + v_color + ';color: "' + v_background + '";')              
        else:
            self.l_connection.setStyleSheet('background-color: ' + v_background + ';color: "' + v_color + '";')              

        # se la connessione è andata a buon fine, richiedo elenco degli oggetti in modo da aggiornare il dizionario dell'editor con nuove parole chiave
        # in questa sezione viene caricata la lista v_global_my_lexer_keywords con tutti i nomi di tabelle, viste, procedure, ecc.
        # tale lista viene poi aggiornata quando viene aperto un nuovo editor o quando viene cambiata la connessione
        if v_global_connesso:
            v_global_my_lexer_keywords.clear()
            v_cursor = v_global_connection.cursor()            
            # carico elenco delle parole chiave per evidenziarle (in questo caso i nomi degli oggetti)
            v_select = """SELECT OBJECT_NAME
                          FROM   ALL_OBJECTS 
                          WHERE  OWNER='""" + self.e_user_name + """' AND 
                                 STATUS='VALID' AND
                                 OBJECT_TYPE IN ('SEQUENCE','PROCEDURE','PACKAGE','TABLE','VIEW','FUNCTION')"""                                                         
            v_risultati = v_cursor.execute(v_select)            
            for v_riga in v_risultati:
                v_global_my_lexer_keywords.append(v_riga[0])       
             
        # scorro la lista-oggetti-editor...        
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso and v_global_connesso:        
                # ...e apro un cursore ad uso di quell'oggetto-editor                
                obj_win2.v_cursor = v_global_connection.cursor()
                # Imposto il colore di sfondo su tutti gli oggetti principali (l'editor è stato tolto volutamente per un effetto grafico non piacevole)                               
                # Questa reimpostazione vale solo per il tema di colori chiaro e non per il tema scuro
                if not o_global_preferences.dark_theme:
                    obj_win2.o_table.setStyleSheet("QTableWidget {background-color: " + v_color + ";}")
                    obj_win2.o_output.setStyleSheet("QPlainTextEdit {background-color: " + v_color + ";}")
                    obj_win2.o_map.setStyleSheet("QTableView {background-color: " + v_color + ";}")
                    self.oggetti_db_elenco.setStyleSheet("QListView {background-color: " + v_color + ";}")
                    self.db_oggetto_tree.setStyleSheet("QTreeView {background-color: " + v_color + ";}")                
                                
                # aggiorno il lexer aggiungendo tutte le nuove keywords                
                if len(v_global_my_lexer_keywords) > 0:                          
                    obj_win2.v_lexer.keywords(6)
                    obj_win2.v_lexer.carica_dizionario_per_autocompletamento()
        
    def slot_oggetti_db_scelta(self):
        """
           In base alla voce scelta, viene caricata la lista con elenco degli oggetti pertinenti
        """                        
        global v_global_connesso

        # se non connesso --> esco
        if not v_global_connesso:
            return 'ko'

        # prendo il tipo di oggetto scelto dall'utente
        try:            
            v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            v_tipo_oggetto = ''
        
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)        

        # pulisco elenco
        self.oggetti_db_lista.clear()
        # se utente ha scelto un oggetto e si è connessi, procedo con il carico dell'elenco         
        if v_tipo_oggetto != '':            
            # chiavi primarie
            if v_tipo_oggetto == 'PRIMARY_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND CONSTRAINT_TYPE='P' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""
            # chiavi univoche
            elif v_tipo_oggetto == 'UNIQUE_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND CONSTRAINT_TYPE='U' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""    
            # relazioni
            elif v_tipo_oggetto == 'FOREIGN_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND CONSTRAINT_TYPE='R' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""    
            # check
            elif v_tipo_oggetto == 'CHECK_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND CONSTRAINT_TYPE='C' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""    
            # indici
            elif v_tipo_oggetto == 'INDEXES':                
                v_select = """SELECT INDEX_NAME OBJECT_NAME, 0 INVALID, 'ENABLED' STATUS FROM ALL_INDEXES WHERE OWNER='"""+self.e_user_name+"""'"""
            # sinonimi
            elif v_tipo_oggetto == 'SYNONYM':                
                v_select = """SELECT SYNONYM_NAME OBJECT_NAME, 0 INVALID, 'ENABLED' STATUS FROM ALL_SYNONYMS WHERE OWNER='"""+self.e_user_name+"""'"""
            # il tipo oggetto rientra nella tabella ALL_OBJECT
            else:
                # leggo elenco degli oggetti indicati (con o senza descrizione)
                if self.e_view_description.isChecked():
                    v_select = """SELECT OBJECT_NAME || 
                                         CASE WHEN OBJECT_TYPE IN ('TABLE','VIEW') THEN
                                               ' - ' || (SELECT COMMENTS FROM ALL_TAB_COMMENTS WHERE ALL_TAB_COMMENTS.OWNER=ALL_OBJECTS.OWNER AND ALL_TAB_COMMENTS.TABLE_NAME=ALL_OBJECTS.OBJECT_NAME)                                
                                         ELSE 
                                             NULL
                                         END AS OBJECT_NAME,
                                         (SELECT COUNT(*) 
                                          FROM   ALL_OBJECTS ABJ
                                          WHERE  ABJ.OWNER=ALL_OBJECTS.OWNER AND 
                                                 ABJ.OBJECT_NAME=ALL_OBJECTS.OBJECT_NAME AND 
                                                 ABJ.STATUS != 'VALID') INVALID,
                                         CASE WHEN OBJECT_TYPE IN ('TRIGGER') THEN
                                              (SELECT STATUS FROM ALL_TRIGGERS WHERE OWNER=ALL_OBJECTS.OWNER AND TRIGGER_NAME=ALL_OBJECTS.OBJECT_NAME) 
                                         ELSE
                                             'ENABLED'
                                         END STATUS                                          
                                  FROM   ALL_OBJECTS 
                                  WHERE  OWNER='""" + self.e_user_name + """' AND 
                                         OBJECT_TYPE='""" + v_tipo_oggetto + """' AND
                                         SECONDARY = 'N'"""
                else:
                    v_select = """SELECT OBJECT_NAME,
                                         (SELECT COUNT(*) 
                                          FROM   ALL_OBJECTS ABJ
                                          WHERE  ABJ.OWNER=ALL_OBJECTS.OWNER AND 
                                                 ABJ.OBJECT_NAME=ALL_OBJECTS.OBJECT_NAME AND 
                                                 ABJ.STATUS != 'VALID') INVALID,
                                                 CASE WHEN OBJECT_TYPE IN ('TRIGGER') THEN
                                                    (SELECT STATUS FROM ALL_TRIGGERS WHERE OWNER=ALL_OBJECTS.OWNER AND TRIGGER_NAME=ALL_OBJECTS.OBJECT_NAME) 
                                                 ELSE
                                                    'ENABLED'
                                                 END STATUS                                          
                                          FROM   ALL_OBJECTS 
                                          WHERE  OWNER='""" + self.e_user_name + """' AND 
                                                 OBJECT_TYPE='""" + v_tipo_oggetto + """' AND
                                                 SECONDARY = 'N'"""                          
        # l'utente non ha scelto nessun tipo di oggetto....si carica tutta la tabella all_objects (notare come alcuni tipi di oggetti come le foreign key non siano presenti)
        else:
            v_select = """SELECT OBJECT_NAME || ' - ' || OBJECT_TYPE AS OBJECT_NAME,                                        
                                 (SELECT COUNT(*) 
                                  FROM   ALL_OBJECTS ABJ
                                  WHERE  ABJ.OWNER=ALL_OBJECTS.OWNER AND 
                                         ABJ.OBJECT_NAME=ALL_OBJECTS.OBJECT_NAME AND 
                                         ABJ.STATUS != 'VALID') INVALID,
                                 CASE WHEN OBJECT_TYPE IN ('TRIGGER') THEN
                                      (SELECT STATUS FROM ALL_TRIGGERS WHERE OWNER=ALL_OBJECTS.OWNER AND TRIGGER_NAME=ALL_OBJECTS.OBJECT_NAME)
                                 ELSE
                                     'ENABLED'
                                 END STATUS                                          
                          FROM   ALL_OBJECTS 
                          WHERE  OWNER='""" + self.e_user_name + """' AND
                                 OBJECT_TYPE IN ('TABLE','VIEW','PACKAGE','PROCEDURE','FUNCTION','TRIGGER','SEQUENCE') AND                                      
                                 SECONDARY = 'N'"""

        # inserisco la select creata in una di livello superiore per poter poi applicare filtri e ordinamento
        v_select = 'SELECT * FROM ( ' + v_select + ' ) '

        # se necessario applico il filtro di ricerca
        if self.oggetti_db_ricerca.text() != '' or self.oggetti_db_tipo_ricerca.currentText() in ('Only invalid','Only disabled'):
            if self.oggetti_db_tipo_ricerca.currentText() == 'Start with':
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '" + self.oggetti_db_ricerca.text().upper() + "%'"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Like':
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%'"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Only invalid': 
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%' AND INVALID > 0"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Only disabled': 
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%' AND STATUS = 'DISABLED'"
        # aggiungo order by
        v_select += " ORDER BY OBJECT_NAME"                                
                
        # eseguo la select                
        try:            
            self.v_cursor_db_obj.execute(v_select)                    
        except cx_Oracle.Error as e:                                                                
            # ripristino icona freccia del mouse
            Freccia_Mouse(False)
            # emetto errore 
            errorObj, = e.args                     
            message_error("Error: " + errorObj.message)       
            return "ko"                  
        # carico il risultato     
        v_righe = self.v_cursor_db_obj.fetchall()                    
        # carico elenco nel modello che è collegato alla lista
        for v_riga in v_righe:
            v_item = QtGui.QStandardItem()                        
            # nell'item inserisco nome oggetto e commento
            v_item.setText(v_riga[0]) 
            # oggetto invalido imposto icona errore
            if v_riga[1] != 0: 
                v_icon = QtGui.QIcon()
                v_icon.addPixmap(QtGui.QPixmap(":/icons/icons/error.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                v_item.setIcon(v_icon)                
            # oggetto disabilitato imposto icona disabled
            if v_riga[2] == 'DISABLED': 
                v_icon = QtGui.QIcon()
                v_icon.addPixmap(QtGui.QPixmap(":/icons/icons/disabled.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                v_item.setIcon(v_icon)                

            self.oggetti_db_lista.appendRow(v_item)                        

        # Ripristino icona freccia del mouse
        Freccia_Mouse(False)        

    def slot_oggetti_db_doppio_click(self, p_index):
        """
           Carica il sorgente dell'oggetto selezionato (facendo doppio click), dentro l'editor
        """                
        # prendo il tipo di oggetto scelto dall'utente
        try:            
            v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            v_tipo_oggetto = ''
        # prendo il nome dell'oggetto scelto dall'utente
        v_selindex = self.oggetti_db_lista.itemFromIndex(p_index)
        v_nome_oggetto = v_selindex.text()               
        v_select = ''
        if v_nome_oggetto != '' and v_tipo_oggetto != '':
            # imposto var che conterrà il testo dell'oggetto DB 
            v_testo_oggetto_db = ''
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # richiamo la procedura di oracle che mi restituisce la ddl dell'oggetto
            # se richiesto di aprire il o il package body, allora devo fare una chiamata specifica
            if v_tipo_oggetto == 'PACKAGE BODY': 
                v_select = "SELECT DBMS_METADATA.GET_DDL('PACKAGE_BODY','"+v_nome_oggetto+"') FROM DUAL"
            elif v_tipo_oggetto == 'PACKAGE':
                v_select = """SELECT DBMS_METADATA.GET_DDL('PACKAGE_SPEC','"""+v_nome_oggetto+"""') FROM DUAL 
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL
                              SELECT DBMS_METADATA.GET_DDL('PACKAGE_BODY','"""+v_nome_oggetto+"""') FROM DUAL
                           """
            elif v_tipo_oggetto == 'TABLE':
                v_select = """SELECT DBMS_METADATA.GET_DDL('"""+v_tipo_oggetto+"""','"""+v_nome_oggetto+"""') FROM DUAL
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('INDEX','"""+v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_INDEXES WHERE OWNER='"""+self.e_user_name+"""' AND TABLE_NAME='"""+v_nome_oggetto+"""') > 0													   
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL                                                
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('CONSTRAINT','"""+v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND TABLE_NAME='"""+v_nome_oggetto+"""' AND R_CONSTRAINT_NAME IS NULL) > 0													   
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL
                              /*
                               SELECT DBMS_METADATA.GET_DEPENDENT_DDL('REF_CONSTRAINT','"""+v_nome_oggetto+"""') FROM DUAL
                               WHERE (SELECT COUNT(*) FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.e_user_name+"""' AND TABLE_NAME='"""+v_nome_oggetto+"""' AND R_CONSTRAINT_NAME IS NOT NULL) > 0													   
                               UNION ALL
                               SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL*/
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('TRIGGER','"""+v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_TRIGGERS WHERE OWNER='"""+self.e_user_name+"""' AND TABLE_NAME='"""+v_nome_oggetto+"""') > 0													                                 
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL
                              SELECT TO_CLOB('COMMENT ON TABLE ' || TABLE_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';')
                              FROM   ALL_TAB_COMMENTS
                              WHERE  ALL_TAB_COMMENTS.OWNER = '"""+self.e_user_name+"""'
                                AND  ALL_TAB_COMMENTS.TABLE_NAME = '"""+v_nome_oggetto+"""'   
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL
                              SELECT TO_CLOB('COMMENT ON COLUMN '|| TABLE_NAME || '.' || COLUMN_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';\n')
                              FROM   ALL_COL_COMMENTS
                              WHERE  ALL_COL_COMMENTS.OWNER = '"""+self.e_user_name+"""'
                                AND  ALL_COL_COMMENTS.TABLE_NAME = '"""+v_nome_oggetto+"""'   
                           """
            elif v_tipo_oggetto in ('PRIMARY_KEY','UNIQUE_KEY','CHECK_KEY'):
                v_select = "SELECT DBMS_METADATA.GET_DDL('CONSTRAINT','"+v_nome_oggetto+"') FROM DUAL"
            elif v_tipo_oggetto == 'FOREIGN_KEY':
                v_select = "SELECT DBMS_METADATA.GET_DDL('REF_CONSTRAINT','"+v_nome_oggetto+"') FROM DUAL"
            elif v_tipo_oggetto == 'INDEXES':
                v_select = "SELECT DBMS_METADATA.GET_DDL('INDEX','"+v_nome_oggetto+"') FROM DUAL"
            elif v_tipo_oggetto == 'SYNONYM':
                v_select = "SELECT DBMS_METADATA.GET_DDL('SYNONYM','"+v_nome_oggetto+"') FROM DUAL"
            elif v_tipo_oggetto in ('PROCEDURE','FUNCTION','TRIGGER','VIEW','SEQUENCE'):                    
                v_select = "SELECT DBMS_METADATA.GET_DDL('"+v_tipo_oggetto+"','"+v_nome_oggetto+"') FROM DUAL"
            else:
                message_error('Invalid object!')
                return 'ko'
            
            try:                            
                # prendo il primo campo, del primo record e lo trasformo in stringa ricavandone tutto il sorgente
                self.v_cursor_db_obj.execute(v_select)
                v_testo_oggetto_db = ''
                for v_record in self.v_cursor_db_obj:
                    v_testo_oggetto_db += str(v_record[0])
            except:
                Freccia_Mouse(False)
                message_error('Error to retrive metadata information!')
                return 'ko'
            
            ###
            # aggiungo la parte dei grant
            ###            
            try:
                v_select = """SELECT GRANTEE, 
                                     LISTAGG(PRIVILEGE, ',') WITHIN GROUP (ORDER BY PRIVILEGE) AS PRIVILEGE,
                                     GRANTABLE
                              FROM   ALL_TAB_PRIVS 
                              WHERE  TABLE_NAME = '"""+v_nome_oggetto+"""' 
                                 AND GRANTOR='"""+self.e_user_name+"""'
                              GROUP BY GRANTEE, GRANTABLE
                              ORDER BY GRANTEE
                           """
                self.v_cursor_db_obj.execute(v_select)
                            
                # aggiungo la parte di grant solo se presente
                v_testo_grant_db = ''
                for v_record in self.v_cursor_db_obj:
                    v_testo_grant_db += 'GRANT ' + str(v_record[1]) + ' ON ' + v_nome_oggetto + ' TO ' + str(v_record[0]) 
                    if v_record[2] == 'YES':
                        v_testo_grant_db += ' WITH GRANT OPTION; \n'
                    else:
                        v_testo_grant_db += ';\n'
            except:
                v_testo_grant_db = '--ERROR TO RETRIEVE GRANT INFORMATION!!!!!!!'
            
            # aggiungo al testo la parte dei grant    
            if v_testo_grant_db != '':
                v_testo_oggetto_db += '\n' + '/\n' + v_testo_grant_db    

            # apro una nuova finestra di editor simulando il segnale che scatta quando utente sceglie "Open", passando il sorgente ddl
            # Attenzione! I file caricati da Oracle hanno come eol solo LF => formato Unix
            v_azione = QtWidgets.QAction()
            v_azione.setText('Open_db_obj')
            self.smistamento_voci_menu(v_azione, '!' + v_nome_oggetto + '.msql', v_testo_oggetto_db)        
                                        
            # Ripristino icona freccia del mouse
            Freccia_Mouse(False)

    def slot_oggetti_db_click(self, p_index):
        """
           Carica nella sezione "object viewer" i dati dell'oggetto selezionato
        """
        # pulisco il campo di ricerca dell'object viewer
        self.e_object_viewer_find.setText('')
        # prendo il tipo di oggetto scelto dall'utente
        try:            
            v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            v_tipo_oggetto = ''
        # prendo il nome dell'oggetto scelto dall'utente
        v_selindex = self.oggetti_db_lista.itemFromIndex(p_index)
        v_nome_oggetto = v_selindex.text()  
        # se ho attivato la descrizione degli oggi, la devo nettificare
        if self.e_view_description.isChecked():
            v_nome_oggetto = v_nome_oggetto.split(' - ')[0]
        # se tutto ok, richiamo la visualizzazione
        if v_nome_oggetto != '':
            self.carica_object_viewer(v_tipo_oggetto, v_nome_oggetto)

    def carica_object_viewer(self, p_tipo_oggetto, p_nome_oggetto):
        """
           Funzione che si occupa di caricare i dati dell'object viewer
        """        
        # queste due variabili che sono comuni all'oggetto main permettono di contenere i dati principali dell'oggetto
        # che è in visualizzazione nell'object viewer
        self.tipo_oggetto = p_tipo_oggetto
        self.nome_oggetto = p_nome_oggetto        
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)

        # pulisco la var che contiene eventuale elenco di procedure-funzioni (solo se si stanno analizzando: procedure-funzioni e package)
        self.oggetti_db_lista_proc_func = ''

        # se l'oggetto selezionato è una tabella o una vista --> preparo select per estrarre i nomi dei campi
        if self.tipo_oggetto == 'TABLE' or self.tipo_oggetto == 'VIEW':
            print('Start loading object viewer of --> ' + self.nome_oggetto + ' - ' + self.tipo_oggetto)
            # ricerco il proprietario dell'oggetto
            self.v_cursor_db_obj.execute("SELECT OWNER FROM ALL_OBJECTS WHERE OBJECT_NAME='"+self.nome_oggetto+"' AND OBJECT_TYPE='"+self.tipo_oggetto+"'")            
            v_record = self.v_cursor_db_obj.fetchone()
            if v_record is not None:
                self.owner_oggetto = v_record[0]
            else:
                self.owner_oggetto = ''
            # ricerco la descrizione dell'oggetto
            self.v_cursor_db_obj.execute("SELECT COMMENTS FROM ALL_TAB_COMMENTS WHERE owner='"+self.owner_oggetto+"' AND TABLE_NAME='"+self.nome_oggetto+"'")
            v_record = self.v_cursor_db_obj.fetchone()
            if v_record is not None:
                self.tipo_oggetto_commento = v_record[0]
            else:
                self.tipo_oggetto_commento = ''
            # creo un modello dati con 4 colonne (dove nell'intestazione ci metto il nome della tabella e la sua descrizione)
            self.db_oggetto_tree_model = QStandardItemModel()
            self.db_oggetto_tree_model.setHorizontalHeaderLabels([self.nome_oggetto, self.owner_oggetto, '', self.tipo_oggetto_commento])

            ###
            # prima radice con il nome della tabella
            ###
            v_root_campi = QStandardItem('Fields')

            self.v_cursor_db_obj.execute("""SELECT A.COLUMN_NAME AS NOME,
                                                   Decode(A.DATA_TYPE,'NUMBER',Lower(A.DATA_TYPE) || '(' || A.DATA_PRECISION || ',' || A.DATA_SCALE || ')',Lower(A.DATA_TYPE) || '(' || A.CHAR_LENGTH || ')')  AS TIPO,
                                                   Decode(A.NULLABLE,'N',' not null','') AS COLONNA_NULLA,
                                                   DATA_DEFAULT AS VALORE_DEFAULT,
                                                   B.COMMENTS AS COMMENTO
                                            FROM   ALL_TAB_COLUMNS A, ALL_COL_COMMENTS B 
                                            WHERE  A.OWNER='"""+self.owner_oggetto+"""' AND 
                                                   A.TABLE_NAME ='"""+self.nome_oggetto+"""' AND 
                                                   A.OWNER=B.OWNER AND 
                                                   A.TABLE_NAME=B.TABLE_NAME AND 
                                                   A.COLUMN_NAME=B.COLUMN_NAME 
                                            ORDER BY A.COLUMN_ID""")
    
            # prendo i vari campi della tabella o vista e li carico nel modello di dati
            for result in self.v_cursor_db_obj:                       
                v_campo_col0 = QStandardItem(result[0])
                v_campo_col1 = QStandardItem(result[1])
                v_campo_col2 = QStandardItem(result[2])
                if result[3] != None:
                    v_campo_col2.setText( v_campo_col2.text() + ' default ' + str(result[3]) )                                    
                v_campo_col3 = QStandardItem(result[4])
                v_root_campi.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                
            self.db_oggetto_tree_model.appendRow(v_root_campi)

            ###
            # seconda radice con le fk
            ###
            v_root_fk = QStandardItem('Constraints')

            self.v_cursor_db_obj.execute("""SELECT CONSTRAINT_NAME,                                                   
                                                   CASE WHEN SEARCH_CONDITION_VC IS NOT NULL THEN
                                                        LTrim(REPLACE(SEARCH_CONDITION_VC,Chr(10),NULL))
                                                   ELSE
                                                        (SELECT LISTAGG(COLUMN_NAME,',') WITHIN GROUP (ORDER BY POSITION) 
                                                         FROM   ALL_CONS_COLUMNS 
                                                         WHERE  OWNER=ALL_CONSTRAINTS.OWNER AND 
                                                                CONSTRAINT_NAME=ALL_CONSTRAINTS.CONSTRAINT_NAME) 
                                                   END AS REGOLA
                                            FROM   ALL_CONSTRAINTS 
                                            WHERE  OWNER='"""+self.owner_oggetto+"""' AND 
                                                   TABLE_NAME='"""+self.nome_oggetto+"""' AND
                                                   CONSTRAINT_NAME NOT LIKE 'SYS%'
                                            ORDER BY Decode(CONSTRAINT_TYPE,'P','1','R','2','3'), CONSTRAINT_NAME""")

            # carico elenco constraints
            for result in self.v_cursor_db_obj:                       
                v_campo_col0 = QStandardItem(result[0])
                v_campo_col1 = None 
                v_campo_col2 = None
                v_campo_col3 = QStandardItem(result[1])
                v_root_fk.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                
            self.db_oggetto_tree_model.appendRow(v_root_fk)

            ###
            # terza radice con gli indici
            ###
            v_root_idx = QStandardItem('Indexes')

            self.v_cursor_db_obj.execute("""SELECT INDEX_NAME,
                                                   CASE WHEN InStr(INDEX_TYPE,'FUNCTION') != 0 THEN 'function' END TIPO, 
                                                   CASE WHEN UNIQUENESS='UNIQUE' THEN 'unique' END UNICO, 
                                                   (SELECT LISTAGG(COLUMN_NAME,',') WITHIN GROUP (ORDER BY COLUMN_POSITION) COLONNE FROM ALL_IND_COLUMNS WHERE INDEX_OWNER=ALL_INDEXES.OWNER AND INDEX_NAME=ALL_INDEXES.INDEX_NAME) COLONNE
                                            FROM   ALL_INDEXES 
                                            WHERE  OWNER='"""+self.owner_oggetto+"""' AND 
                                                    TABLE_NAME='"""+self.nome_oggetto+"""'
                                                    ORDER BY INDEX_NAME""")

            # carico elenco indici
            for result in self.v_cursor_db_obj:                       
                v_campo_col0 = QStandardItem(result[0])
                v_campo_col1 = QStandardItem(result[1])
                v_campo_col2 = QStandardItem(result[2])
                v_campo_col3 = QStandardItem(result[3])
                v_root_idx.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                
            self.db_oggetto_tree_model.appendRow(v_root_idx)                

            ###
            # quarta radice con i trigger
            ###
            v_root_trg = QStandardItem('Triggers')

            self.v_cursor_db_obj.execute("""SELECT TRIGGER_NAME, 
                                                   TRIGGER_TYPE, 
                                                   TRIGGERING_EVENT 
                                            FROM   ALL_TRIGGERS 
                                            WHERE  OWNER='"""+self.owner_oggetto+"""' AND 
                                                   TABLE_NAME='"""+self.nome_oggetto+"""'
                                            ORDER BY TRIGGER_NAME""")

            # carico elenco indici
            for result in self.v_cursor_db_obj:                       
                v_campo_col0 = QStandardItem(result[0])
                v_campo_col1 = QStandardItem(result[1])
                v_campo_col2 = QStandardItem(result[2])
                v_campo_col3 = None
                v_root_trg.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                
            self.db_oggetto_tree_model.appendRow(v_root_trg)                

            ###
            # quinta radice con le tabelle referenziate (non viene caricato nulla fino a quando l'utente non clicca sulla relativa voce)
            # il caricamento verrà eseguito dalla procedura slot_db_oggetto_tree_expand
            ###
            v_root_ref = QStandardItem('Referenced By')
            v_root_ref.appendRow([None,None,None,None])                
            self.db_oggetto_tree_model.appendRow(v_root_ref)   
    
            ###                
            # attribuisco il modello dei dati all'albero
            ###
            self.db_oggetto_tree.setModel(self.db_oggetto_tree_model)
            # forzo la larghezza delle colonne
            self.db_oggetto_tree.setColumnWidth(0, 130)
            self.db_oggetto_tree.setColumnWidth(1, 110)
            self.db_oggetto_tree.setColumnWidth(2, 80)
            self.db_oggetto_tree.setColumnWidth(3, 1000)
            # mi posiziono sulla prima riga ed espando l'albero
            v_index = self.db_oggetto_tree_model.indexFromItem(v_root_campi)
            self.db_oggetto_tree.expand(v_index)

        # se l'oggetto selezionato è un package, funzioni e procedure ...
        elif self.tipo_oggetto in ('PACKAGE','PACKAGE BODY','FUNCTION','PROCEDURE') :
            # ricerco il proprietario dell'oggetto
            self.v_cursor_db_obj.execute("SELECT OWNER FROM ALL_OBJECTS WHERE OBJECT_NAME='"+self.nome_oggetto+"' AND OBJECT_TYPE='"+self.tipo_oggetto+"'")            
            v_record = self.v_cursor_db_obj.fetchone()
            if v_record is not None:
                self.owner_oggetto = v_record[0]
            else:
                self.owner_oggetto = ''

            # creo un modello dati con 1 colonna (dove nell'intestazione ci metto il nome dell'oggetto)
            self.db_oggetto_tree_model = QStandardItemModel()
            self.db_oggetto_tree_model.setHorizontalHeaderLabels([self.nome_oggetto])            

            ###
            # prima radice con il nome dell'oggetto
            ###
            v_root_codice = QStandardItem('Code')

            # leggo il sorgente e lo metto dentro una lista!
            self.v_cursor_db_obj.execute("""SELECT UPPER(TEXT) as TEXT, LINE FROM ALL_SOURCE WHERE OWNER='"""+self.owner_oggetto+"""' AND NAME='"""+self.nome_oggetto+"""' AND TYPE='"""+self.tipo_oggetto+"""' ORDER BY LINE""")
            v_lista_testo = []
            for result in self.v_cursor_db_obj:                       
                v_lista_testo.append(result[0])
            # partendo dalla lista che contiene il testo, creo un oggetto che contiene la lista di tutte le procedure-funzioni!
            self.oggetti_db_lista_proc_func = estrai_procedure_function(v_lista_testo)            
            # leggo l'oggetto che contiene procedure-funzioni e lo carico nell'albero a video            
            for ele in self.oggetti_db_lista_proc_func:                
                # creo il nodo con il nome della procedura-funzione
                v_int_proc_func = QStandardItem(ele.nome_definizione)                                                            
                # carico intestazione della procedura-funzione
                v_root_codice.appendRow([v_int_proc_func])                         
                # scorro tutti i parametri e li carico
                for par in ele.lista_parametri:
                    # carico le foglie con i nomi dei parametri
                    v_item_parametro = QStandardItem(par)                        
                    v_int_proc_func.appendRow([v_item_parametro])                        
            
            self.db_oggetto_tree_model.appendRow(v_root_codice)
            
            ###                
            # attribuisco il modello dei dati all'albero
            ###            
            self.db_oggetto_tree.setModel(self.db_oggetto_tree_model)    
            # forzo la larghezza delle colonne
            self.db_oggetto_tree.setColumnWidth(0, 180)
            self.db_oggetto_tree.setColumnWidth(1, 40)
                        
            # mi posiziono sulla prima riga ed espando l'albero
            v_index = self.db_oggetto_tree_model.indexFromItem(v_root_codice)
            self.db_oggetto_tree.expand(v_index)
                                    
        # Ripristino icona freccia del mouse
        Freccia_Mouse(False)

    def slot_object_viewer_find(self):
        """
           Ricerca nell'albero object viewer la stringa indicata a partire dalla posizione selezionata
        """
        # se non è stato digitato alcun testo --> esco
        if self.e_object_viewer_find.text() == '':            
            return 'ko'
        
        v_1a_volta = True
        v_1a_posizione = None
        # scorro l'object viewer tramite il suo modello di dati...costituito da una matrice di item e da item con sottomatrici!
        for r in range(self.db_oggetto_tree_model.rowCount()):
            for c in range(self.db_oggetto_tree_model.columnCount()):            
                v_item = self.db_oggetto_tree_model.item(r,c)                
                if v_item is not None:
                    #print('Matrice -> ' + v_item.text())
                    # scorro la sottomatrice
                    for r1 in range(v_item.rowCount()):
                        for c1 in range(v_item.columnCount()):
                            v_item1 = v_item.child(r1,c1)
                            if v_item1 is not None:
                                #print('Sottomatrice -> ' + v_item1.text())
                                # se l'elemento dell'albero contiene il testo di ricerca --> mi posiziono
                                if self.e_object_viewer_find.text().upper() in v_item1.text().upper():                                                                         
                                    # se è la prima volta memorizzo la posizione tramite il suo oggetto indice e seleziono la riga dicendo di pulire eventuale selezione precedente
                                    if v_1a_volta:
                                        v_1a_posizione = v_item1.index()                                        
                                        self.db_oggetto_tree.selectionModel().select(v_item1.index(), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)                                    
                                        v_1a_volta = False
                                    # ...altrimenti aggiungo la riga alla selezione corrente
                                    else:                                        
                                        self.db_oggetto_tree.selectionModel().select(v_item1.index(), QItemSelectionModel.Select | QItemSelectionModel.Rows)                                                                        
                                    # mi posiziono sulla riga (questo serve esclusivamente per quando la stringa viene trovata nei sottorami in modo che venga esploso l'albero automaticamente...è solo un effetto grafico)
                                    self.db_oggetto_tree.scrollTo(v_item1.index())                                                                                   
                                # scorro la sottomatrice2 (es. nei package)
                                for r2 in range(v_item1.rowCount()):
                                    for c2 in range(v_item1.columnCount()):
                                        v_item2 = v_item1.child(r2,c2)
                                        if v_item2 is not None:
                                            #print('Sottomatrice2 -> ' + v_item2.text())
                                            # se l'elemento dell'albero contiene il testo di ricerca --> mi posiziono
                                            if self.e_object_viewer_find.text().upper() in v_item2.text().upper():                                                                         
                                                # se è la prima volta memorizzo la posizione tramite il suo oggetto indice e seleziono la riga dicendo di pulire eventuale selezione precedente
                                                if v_1a_volta:
                                                    v_1a_posizione = v_item2.index()                                        
                                                    self.db_oggetto_tree.selectionModel().select(v_item2.index(), QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)                                    
                                                    v_1a_volta = False
                                                # ...altrimenti aggiungo la riga alla selezione corrente
                                                else:                                        
                                                    self.db_oggetto_tree.selectionModel().select(v_item2.index(), QItemSelectionModel.Select | QItemSelectionModel.Rows)                                                                        
                                                # mi posiziono sulla riga (questo serve esclusivamente per quando la stringa viene trovata nei sottorami in modo che venga esploso l'albero automaticamente...è solo un effetto grafico)
                                                self.db_oggetto_tree.scrollTo(v_item2.index())                                                                                   
                    

        # se trovato corrispondenze, mi posiziono sulla prima
        if v_1a_posizione is not None:
            self.db_oggetto_tree.scrollTo(v_1a_posizione)                                                                                   

    def slot_db_oggetto_tree_expand(self, p_model):
        """
            Evento che si scatena quando viene selezionato un elemento sull'albero dell'object viever
            E' stato creato in quanto la ricerca della reference by è un po' lenta...
            p_model è del tipo QModelIndex
        """
        if p_model.data() == 'Referenced By':
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # preparo la select per ricerca tutte le tabelle referenziate
            self.v_cursor_db_obj.execute("""SELECT DISTINCT TABLE_NAME
                                            FROM   ALL_CONSTRAINTS
                                            WHERE  OWNER = '"""+self.owner_oggetto+"""' AND
                                                   CONSTRAINT_TYPE='R' AND 
                                                   R_CONSTRAINT_NAME IN (SELECT CONSTRAINT_NAME
                                                                         FROM   ALL_CONSTRAINTS
                                                                         WHERE  TABLE_NAME='"""+self.nome_oggetto+"""' AND 
                                                                                CONSTRAINT_TYPE IN ('U', 'P') )
                                            ORDER BY TABLE_NAME""")

            # prendo la posizione dell'oggetto corrente nell'albero
            v_root_ref = self.db_oggetto_tree_model.itemFromIndex(p_model)                               
            # pulisco tutti i figli sottostanti            
            v_root_ref.removeRows(0,v_root_ref.rowCount())
            # carico sotto il ramo "Referenced By" tutti gli elementi
            for result in self.v_cursor_db_obj:                       
                v_campo_col0 = QStandardItem(result[0])
                v_campo_col1 = None
                v_campo_col2 = None
                v_campo_col3 = None
                v_root_ref.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                            

            # Ripristino icona freccia del mouse
            Freccia_Mouse(False)

    def slot_db_oggetto_tree_doppio_click(self, p_model):
        """
           Evento che si scatena quando faccio doppio click sull'albero.
           Se il tipo di oggetto presente in object viewer è del tipo procedura-funzione e package, viene presa la procedura-funzione
           selezionata e viene riportata all'interno dell'editor attivo, scrivendo il nome del package, seguito dal nome della procedura-funzione
           e dall'elenco dei parametri
           Attenzione! Se la stessa procedura-funzione è presente più volte all'interno del package, ne verrà presa solo la prima ricorrenza
        """        
        if self.tipo_oggetto not in ('PACKAGE BODY','PACKAGE','PROCEDURE','FUNCTION'):            
            return 'ko'

        # carico l'oggetto di classe MSql_win2_class attivo in questo momento (così ho tutte le sue proprietà)        
        o_MSql_win2 = self.oggetto_win2_attivo()

        if p_model.data() != '' and o_MSql_win2 != None:                        
            # imposto le var di lavoro
            v_risultato = self.nome_oggetto + '.'
            v_spazi = 0
            # leggo l'oggetto che contiene procedure-funzioni alla ricerca dell'elemento che ha selezionato l'utente
            for ele in self.oggetti_db_lista_proc_func:                                
                # se trovo l'elemento selezionato....inizio a caricarlo nella stringa di risultato
                if ele.nome_definizione == p_model.data():                                        
                    v_risultato += ele.nome_definizione 
                    v_1a_volta = True
                    # scorro tutti i parametri e li carico (per i parametri successivi al primo, cerco di fare indentazione)
                    for par in ele.lista_parametri:
                        if v_1a_volta:
                            v_1a_volta = False
                            v_risultato += '('
                            v_spazi = len(v_risultato)
                            v_risultato += par + ' => '
                        else:
                            # in base al settaggio di eol aggiungo il ritorno a capo
                            if o_MSql_win2.setting_eol == 'W':
                                v_risultato += ', \r\n'                        
                            else:
                                v_risultato += ', \n'                        
                            v_risultato += ' ' * v_spazi
                            v_risultato += par + ' => '
                    if not v_1a_volta:
                        v_risultato += ')'
                        break # esco dal ciclo --> se infatti ci fossero più procedure-funzioni con lo stesso nome esco alla prima
            # se caricato il risultato, prendo l'editor corrente e nella posizione del cursore ci metto il risultato (preceduto da un ritorno a capo)           
            if v_risultato != '':                
                # in base al settaggio di eol aggiungo il ritorno a capo
                if o_MSql_win2.setting_eol == 'W':                            
                    o_MSql_win2.e_sql.insert('\r\n' + v_risultato)
                else:
                    o_MSql_win2.e_sql.insert('\n' + v_risultato)
    
    def richiesta_connessione_specifica(self):    
        """
            Apre finestra per richiedere una connessione specifica
        """            
        # inizializzo le strutture grafice e visualizzo la dialog per richiedere una password di conferma prima di procedere
        self.dialog_connect = QtWidgets.QDialog()
        self.win_dialog_connect = Ui_connect_window()
        self.win_dialog_connect.setupUi(self.dialog_connect)        
        self.win_dialog_connect.b_connect.clicked.connect(self.richiesta_connessione_specifica_accept)                
        self.dialog_connect.show()        

    def richiesta_connessione_specifica_accept(self):
        """
           Eseguo connessione specifica
        """           
        # controllo che tutte le info siano state inserite
        if self.win_dialog_connect.e_user.displayText() == '' or self.win_dialog_connect.e_password.displayText() == '' or self.win_dialog_connect.e_tns.displayText() == '':
            message_error('Not all the requested data has been entered!')            
            return 'ko'

        # eseguo la connessione
        self.e_user_name = self.win_dialog_connect.e_user.displayText()
        self.e_password = self.win_dialog_connect.e_password.text()
        self.e_server_name = self.win_dialog_connect.e_tns.displayText()
        self.e_user_mode = self.win_dialog_connect.e_mode.currentText()

        self.slot_connetti()
                
        # chiudo window di connessione
        self.dialog_connect.close()

    def slot_preferences(self):
        """
           Apre la window di gestione delle preferenze
        """   
        global v_global_work_dir         
        from preferences import win_preferences_class
        self.my_app = win_preferences_class(v_global_work_dir + 'MSql.ini')        
        self.my_app.show()   

    def crea_dizionario_per_autocompletamento(self):
        """
           Apre la window per la creazione del dizionario
        """
        global v_global_work_dir  
        global v_global_connesso
        
        from create_autocomplete_dic import create_autocomplete_dic_class
        
        self.my_app = create_autocomplete_dic_class(v_global_connesso,
                                                    self.v_cursor_db_obj, 
                                                    self.e_user_name, 
                                                    v_global_work_dir + 'MSql_autocompletion.ini')        
        self.my_app.show()   
    
    def slot_menu_auto_column_resize(self):
        """
           Imposta la var che indica se la tabella del risultato ha attiva la formattazione automatica della larghezza delle colonne
        """
        global o_global_preferences

        if o_global_preferences.auto_column_resize:
            o_global_preferences.auto_column_resize = False
        else:
            o_global_preferences.auto_column_resize = True

    def slot_history(self):
        """
           Apre la window per la ricerca delle istruzioni MSql storicizzate
        """    
        global v_global_work_dir, o_global_preferences

        try:
            # visualizzo la finestra di ricerca
            self.dialog_history.show()            
            self.dialog_history.activateWindow()             
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog 
            self.win_history = history_class(v_global_work_dir+'MSql.db')        
            # aggiungo l'evento click per l'import dell'istruzione nell'editor
            self.win_history.b_insert_in_editor.clicked.connect(self.slot_history_insert_in_editor)
            self.win_history.show()     

    def slot_history_insert_in_editor(self):
        """
           Prende la riga selezionata nell'history e la porta dentro l'editor corrente
        """       
        # prendo indice dalla tabella
        try:
            index = self.win_history.o_lst1.selectedIndexes()[2]           
        except:
            message_error('Select a row!')
            return 'ko'
        # il valore della colonna istruction viene caricato nell'editor corrente
        o_MSql_win2 = self.oggetto_win2_attivo()
        if o_MSql_win2 != None:            
            v_risultato = self.win_history.o_lst1.model().data(index)
            # il testo che prendo dall'history ha formato eol Linux, e se necessario
            # va convertito in Windows (a seconda dell'impostazione dell'editor di destinazione)
            if o_MSql_win2.setting_eol == 'W':
                v_risultato = v_risultato.replace('\n', '\r\n')                                    

            o_MSql_win2.e_sql.insert(v_risultato)        

    def slot_preferred_sql(self):
        """
           Apre la window per la gestione delle istruzioni sql preferite
        """    
        global v_global_work_dir, o_global_preferences

        try:
            # visualizzo la finestra di ricerca
            self.dialog_preferred_sql.show()            
            self.dialog_preferred_sql.activateWindow()             
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog 
            self.win_preferred_sql = preferred_sql_class(v_global_work_dir+'MSql.db',False)        
            # aggiungo l'evento doppio click per l'import dell'istruzione nell'editor
            self.win_preferred_sql.b_insert_in_editor.clicked.connect(self.slot_preferred_sql_insert_in_editor)
            self.win_preferred_sql.show()     

    def slot_preferred_sql_insert_in_editor(self):
        """
           Prende la riga selezionata nell'elenco dei preferiti e la porta dentro l'editor corrente
        """       
        # prendo indice dalla tabella
        #index = self.win_preferred_sql.o_tabella.selectedIndexes()[2]           
        index = self.win_preferred_sql.o_tabella.currentRow()           
        # il valore della colonna istruction viene caricato nell'editor corrente        
        o_MSql_win2 = self.oggetto_win2_attivo()
        if o_MSql_win2 != None and index != -1:            
            v_risultato = self.win_preferred_sql.o_tabella.item(index,2).text()            
            # converto l'eol se editor è in modalità Unix
            if o_MSql_win2.setting_eol == 'U':
                v_risultato = v_risultato.replace('\r\n','\n')                                    

            o_MSql_win2.e_sql.insert(v_risultato)        

#
#  _____ ____ ___ _____ ___  ____  
# | ____|  _ \_ _|_   _/ _ \|  _ \ 
# |  _| | | | | |  | || | | | |_) |
# | |___| |_| | |  | || |_| |  _ < 
# |_____|____/___| |_| \___/|_| \_\
#                                 
# Classe che contiene tutti i componenti dell'editor
class MSql_win2_class(QtWidgets.QMainWindow, Ui_MSql_win2):
    """
        Editor SQL
    """       
    def __init__(self, 
                 p_titolo, # Titolo della window-editor
                 p_contenuto_file,  # Eventuale contenuto da inserire direttamente nella parte di editor
                 o_MSql_win1_class): # Puntatore alla classe principale (window1)                                  
        global o_global_preferences  
        global v_global_work_dir      

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win2_class, self).__init__()        
        self.setupUi(self)
                
        # imposto il titolo della nuova window (da notare come il nome completo dal file-editor sia annegato nel nome dell'oggetto!)        
        self.setObjectName(p_titolo)
        self.setWindowTitle(titolo_window(self.objectName()))

        # i widget della mappa, del find stringa e del replace stringa, li nascondo
        self.dockMapWidget.hide()
        self.dockFindWidget.hide()
        self.dockReplaceWidget.hide()

        # var che indica che è attiva-disattiva la sovrascrittura (tasto insert della tastiera)
        self.v_overwrite_enabled = False
        # mi salvo il puntatore alla classe principale (in questo modo posso accedere ai suoi oggetti e metodi)
        self.link_to_MSql_win1_class = o_MSql_win1_class

        # splitter che separa l'editor dall'output: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello di output
        #self.splitter.setStyleSheet("QSplitter::handle {text: url(':/icons/icons/splitter.gif')}")
        self.splitter.setStretchFactor(0,1)

        ###
        # IMPOSTAZIONI DELL'EDITOR SCINTILLA (Notare come le impostazioni delle proprietà siano stato postate nella definizione del lexer)
        ###
        # attivo UTF-8 (se richiesto)
        if o_global_preferences.utf_8:
            self.e_sql.setUtf8(True)                                                        
        # attivo il lexer per evidenziare il codice del linguaggio SQL. Notare come faccia riferimento ad un oggetto che a sua volta personalizza il 
        # dizionario del lexer SQL, aggiungendo (se sono state caricate) le parole chiave di: tabelle, viste, package, ecc.
        self.v_lexer = My_MSql_Lexer(self.e_sql)                
        # attivo il lexer sull'editor
        self.e_sql.setLexer(self.v_lexer)
                
        # imposto il ritorno a capo in formato Windows (CR-LF) o Unix (LF)
        # Attenzione! Nel caso di nuovo file il formato è Windows, mentre se viene aperto un file, va analizzata la prima riga
        #             e ricercato che formato ha....quello sarà poi il formato da utilizzare!
        #             Questo è stato fatto per rendere l'editor più flessibile
        #             Ho poi scoperto che ci sono in giro file misti tra (CR-LF) e (LF) e quindi limitato l'analisi ai primi 1000 caratteri....
        if p_contenuto_file is not None:
            if p_contenuto_file[0:1000].find('\r\n') != -1:                
                self.setting_eol = 'W'
            else:                
                self.setting_eol = 'U'
        else:
            self.setting_eol = 'W'

        # controllo quale formato di eol ha il file e imposto tale opzione in Scintilla 
        if self.setting_eol == 'W':
            self.e_sql.setEolMode(QsciScintilla.EolWindows)                
        else:
            self.e_sql.setEolMode(QsciScintilla.EolUnix)                
        # aggiorno la statusbar con l'impostazione di eol
        self.aggiorna_statusbar()

        # visualizzo o meno il carattere di end of line in base alla preferenza
        self.set_show_end_of_line()        

        ###
        # DICHIARAZIONE VAR GENERALI
        ###

        # inizializzo var che contiene la select corrente
        self.v_select_corrente = ''
        # inizializzo var che indica che l'esecuzione è andata ok
        self.v_esecuzione_ok = False  
        # inizializzo var che indica che si è in fase di caricamento dei dati
        self.v_carico_pagina_in_corso = False   
        # inizializzo la var che conterrà eventuale matrice dei dati modificati
        self.v_matrice_dati_modificati = []
        # inizializzo la var che contiene le intestazioni dell'output in tabella
        self.nomi_intestazioni = []
        # salva l'altezza del font usato nella sezione result e output e viene usata per modificare l'altezza della cella
        self.v_altezza_font_output = 9
        # inizializzo la struttura che conterrà eventuali variabili bind. Attenzione! La struttura che verrà passata a Oracle è self.v_variabili_bind_dizionario
        self.v_variabili_bind_nome = []
        self.v_variabili_bind_tipo = []
        self.v_variabili_bind_valore = []        
        self.v_variabili_bind_dizionario = {}
        # settaggio dei font di risultato e output (il font è una stringa con il nome del font e separato da virgola l'altezza)
        if o_global_preferences.font_result != '':
            v_split = o_global_preferences.font_result.split(',')
            v_font = QFont(str(v_split[0]),int(v_split[1]))
            if len(v_split) > 2 and v_split[2] == ' BOLD':
                v_font.bold(True)
            self.slot_font_result_selector(v_font)
        # imposto editabile o meno sulla parte di risultato
        self.set_editable()            

        ###
        # Precaricamento (se passato un contenuto di file) 
        ###
        v_cur_y, v_cur_x = 0,0
        if p_contenuto_file is not None:        
            # imposto editor con quello ricevuto in ingresso
            self.e_sql.setText(p_contenuto_file)
            # chiedo allo storico di darmi eventuale posizione di dove si trovava il cursore ultima volta
            if o_global_preferences.remember_text_pos:
                v_cur_y, v_cur_x = read_files_history(v_global_work_dir+'MSql.db', p_titolo)            
                
        # mi posiziono sulla prima riga (la posizione X viene al momento forzata a zero!)
        self.e_sql.setCursorPosition(v_cur_y,0)

        # var che indica che il testo è stato modificato
        #self.e_sql.insert('SELECT * FROM MS_UTN')
        self.v_testo_modificato = False                

        ###
        # Definizione di eventi aggiuntivi
        ###
        # sulla scrollbar imposto evento specifico
        self.o_table.verticalScrollBar().valueChanged.connect(self.slot_scrollbar_azionata)
        # sul cambio della cella imposto altro evento (vale solo quando abilitata la modifica)
        self.o_table.cellChanged.connect(self.slot_o_table_item_modificato)                
        # attivo il filtro di eventi sull'oggetto dei risultati, in modo da visualizzare il menu contestuale sulle celle
        self.o_table.viewport().installEventFilter(self)   
        # slot per controllare quando cambia il testo digitato dall'utente
        self.e_sql.textChanged.connect(self.slot_e_sql_modificato)    
        self.e_sql.cursorPositionChanged.connect(self.aggiorna_statusbar)            
            
        # attivo il drop sulla parte di editor        
        self.e_sql.setAcceptDrops(True)    
        # attivo il filtro di eventi sull'oggetto editor; ogni evento passerà dalla funzione eventFilter
        self.e_sql.installEventFilter(self)   

        # var che si attiva quando l'oggetto viene chiuso
        self.v_editor_chiuso = False

        # se connessione aperta, collego un nuovo cursore
        if v_global_connesso:
            self.v_cursor = v_global_connection.cursor()
        else:
            self.v_cursor = None

        # definizione del menu di ricerca sulle colonne dei risultati
        self.o_table_hH = self.o_table.horizontalHeader()
        self.o_table_hH.sectionClicked.connect(self.slot_click_colonna_risultati)        

    def eventFilter(self, source, event):
        """
           Gestione di eventi personalizzati sull'editor (overwrite, drag&drop, F12) e sulla tabella dei risultati
           Da notare come un'istruzione di return False indirizza l'evento verso il suo svolgimento classico
        """      
        global v_global_connection

        # individuo tasto destro del muose sulla tabella dei risultati        
        if event.type() == QEvent.MouseButtonPress and event.buttons() == Qt.RightButton and source is self.o_table.viewport():
            self.tasto_desto_o_table(event)      
            return True      

        # individuo la pressione di un tasto sull'editor
        if event.type() == QEvent.KeyPress and source is self.e_sql:
            # tasto Insert premuto da parte dell'utente --> cambio la label sulla statusbar
            if event.key() == Qt.Key_Insert:
                if self.v_overwrite_enabled:
                    self.v_overwrite_enabled = False                
                else:
                    self.v_overwrite_enabled = True                
                # aggiorno la status bar con relative label
                self.aggiorna_statusbar()
            # tasto F11 premuto dall'utente --> eseguo la quick query
            if event.key() == Qt.Key_F11:                 
                self.slot_f11()   
                return True
            # tasto F12 premuto dall'utente --> richiamo l'object viewer            
            if event.key() == Qt.Key_F12:                 
                self.slot_f12()   
                return True
            # tasto F3 premuto dall'utente --> richiamo la ricerca
            if event.key() == Qt.Key_F3:                                 
                self.slot_find_next()   
                return True

        # individuo il drag sull'editor e...
        if event.type() == QEvent.DragEnter and source is self.e_sql:                  
            # il drag contiene elenco di item...
            # se il drag non contiene elenco di item, quindi ad esempio del semplice testo, lascio le cose cosi come sono            
            if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
                # estraggo gli item e li trasformo in stringa
                v_mime_data = event.mimeData()
                source_item = QtGui.QStandardItemModel()
                source_item.dropMimeData(v_mime_data, Qt.CopyAction, 0,0, QModelIndex())                                                
                v_stringa = ''
                for v_indice in range(0,source_item.rowCount()):
                    if v_stringa != '':
                        v_stringa += ',' + source_item.item(v_indice, 0).text()
                    else:
                        v_stringa = source_item.item(v_indice, 0).text()                                
                # reimposto la stringa dentro l'oggetto mimedata
                # da notare come l'oggetto v_mime_data punta direttamente all'oggetto event.mimeData!
                v_mime_data.setText(v_stringa)                
            # accetto il drag
            event.accept()                        
            return True                                            
        
        # individuo il drop sull'editor               
        if event.type() == QEvent.Drop and source is self.e_sql:            
            # e richiamo direttamente la funzione che accetta il drop di QScintilla
            # da notare come durante il drag siano stato cambiato il contenuto dei dati nel caso 
            # la sorgente fossero degli item (in questo caso l'object viewer)
            self.e_sql.dropEvent(event)                
            return True        
        
        # individuo l'attivazione della subwindow dell'editor...
        if event.type() == QEvent.FocusIn:                  
            # aggiorno i dati della statusbar
            self.aggiorna_statusbar()
                            
        # fine senza alcuna elaborazione e quindi si procede con esecuzione dei segnali nativi del framework       
        return False
           
    def tasto_desto_o_table(self, event):
        """
           Gestione del menu contestuale con tasto destro su tabella dei risultati
        """                    
        self.v_o_table_current_item = self.o_table.itemAt(event.pos())        
        if self.v_o_table_current_item is not None:
            # creazione del menu popup
            self.o_table_cont_menu = QMenu(self)            
            
            # bottone per copia valore
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(":/icons/icons/copy.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
            v_copia = QPushButton()
            v_copia.setText('Copy item')
            v_copia.setIcon(icon1)        
            v_copia.clicked.connect(self.o_table_copia_valore)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_copia)        
            self.o_table_cont_menu.addAction(v_action)

            # bottone per aprire window dove viene visualizzato il contenuto della cella in modo amplificato
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap(":/icons/icons/zoom_avanti.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
            v_zoom = QPushButton()
            v_zoom.setText('Zoom item')
            v_zoom.setIcon(icon2)        
            v_zoom.clicked.connect(self.o_table_zoom_item)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_zoom)        
            self.o_table_cont_menu.addAction(v_action)

            # visualizzo il menu alla posizione del cursore
            self.o_table_cont_menu.exec_(event.globalPos())            
    
    def o_table_copia_valore(self):
        """
            Copia il valore dell'item dentro la clipboard
        """
        #print('Table Item:', v_item.row(), v_item.column())
        #print('Table Item:', v_item.text())
        QGuiApplication.clipboard().setText(self.v_o_table_current_item.text())            
        self.o_table_cont_menu.close()
    
    def o_table_zoom_item(self):
        """
            Apre la window e visualizza il contenuto del dato di partenza
        """                        
        # inizializzo le strutture grafiche e visualizzo la dialog per la ricerca del testo
        self.win_dialog_zoom_item = QtWidgets.QDialog()                        
        self.win_dialog_zoom_item.resize(300, 200)
        self.win_dialog_zoom_item.setWindowTitle('Zoom item')
        v_icon = QtGui.QIcon()
        v_icon.addPixmap(QtGui.QPixmap(":/icons/icons/MSql.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
        self.win_dialog_zoom_item.setWindowIcon(v_icon)
        self.win_dialog_zoom_item_gl = QtWidgets.QGridLayout(self.win_dialog_zoom_item)
        self.win_dialog_zoom_lineEdit = QtWidgets.QPlainTextEdit(self.win_dialog_zoom_item)        
        self.win_dialog_zoom_item_gl.addWidget(self.win_dialog_zoom_lineEdit, 0, 0, 1, 1)
        self.win_dialog_zoom_lineEdit.setPlainText(self.v_o_table_current_item.text())
        self.win_dialog_zoom_item.show()

    def slot_f11(self):
        """
           Premendo F11 viene estratto dalla posizione del cursore dell'editor, il nome dell'oggetto
           e da li viene eseguita una query

           Note: Ho provato a vedere se esiste possibilità di chiedere a qscintilla se mi può dare la parola su cui il cursore è posizionato
                 ma no trovato. Quindi fatto una cosa semiinterna creando una funzione in package utilita
        """
        # ricavo numero riga e posizione del cursore
        v_num_line, v_num_pos = self.e_sql.getCursorPosition()                
        # estraggo l'intera riga dove è posizionato il cursore
        self.e_sql.setSelection(v_num_line, 0, v_num_line+1, -1)
        v_line = self.e_sql.selectedText()
        # riposiziono il cursore allo stato originario
        self.e_sql.setSelection(v_num_line, v_num_pos, v_num_line, v_num_pos)
        # utilizzando la posizione del cursore sulla riga, estraggo la parola più prossima al cursore stesso                
        v_oggetto = extract_word_from_cursor_pos(v_line.upper(), v_num_pos)                
        if v_oggetto != '':
            print('F11-Quick query on --> ' + v_oggetto)      
            # tento di eseguire la query dell'oggetto selezionato (dovrebbe essere una tabella)
            v_select = 'SELECT * FROM ' + v_oggetto
            self.esegui_select(v_select, v_select)
        
    def slot_f12(self):
        """
           Premendo F12 viene estratto dalla posizione del cursore dell'editor, il nome dell'oggetto
           e da li viene aperto l'object viewer

           Note: Ho provato a vedere se esiste possibilità di chiedere a qscintilla se mi può dare la parola su cui il cursore è posizionato
                 ma no trovato. Quindi fatto una cosa semiinterna creando una funzione in package utilita
        """
        # ricavo numero riga e posizione del cursore
        v_num_line, v_num_pos = self.e_sql.getCursorPosition()                
        # estraggo l'intera riga dove è posizionato il cursore
        self.e_sql.setSelection(v_num_line, 0, v_num_line+1, -1)
        v_line = self.e_sql.selectedText()
        # riposiziono il cursore allo stato originario
        self.e_sql.setSelection(v_num_line, v_num_pos, v_num_line, v_num_pos)
        # utilizzando la posizione del cursore sulla riga, estraggo la parola più prossima al cursore stesso                
        v_oggetto = extract_word_from_cursor_pos(v_line.upper(), v_num_pos)                
        if v_oggetto != '':
            print('F12-Call Object viewer of --> ' + v_oggetto)
            # richiamo la procedura di oracle che mi restituisce la ddl dell'oggetto (apro un cursore locale a questa funzione)
            v_temp_cursor = v_global_connection.cursor()
            try:
                v_temp_cursor.execute("SELECT OBJECT_NAME, OBJECT_TYPE FROM ALL_OBJECTS WHERE OBJECT_NAME = '" + v_oggetto + "' AND OBJECT_TYPE IN ('TABLE','VIEW','PACKAGE','PROCEDURE','FUNCTION')")
            except:
                return 'ko'
            # prendo il risultato
            v_record = v_temp_cursor.fetchone()
            # se il risultato è presente ottengo nome e tipo dell'oggetto che dovrò passare all'object viewer
            if v_record != None:                    
                v_nome_oggetto = v_record[0]
                v_tipo_oggetto = v_record[1]                                   
                # carico l'object viewer passando come parametro iniziale il puntatore all'oggetto main
                MSql_win1_class.carica_object_viewer(self.link_to_MSql_win1_class,v_tipo_oggetto,v_nome_oggetto)                                        
            else:
                print('Not found ' + v_oggetto)
    
    def slot_click_colonna_risultati(self, index):       
        """
            Gestione menu popup all'interno dei risultati        
            Al click su una delle intestazioni di colonna della sezione "risultati" viene presentato un menu popup che permette di
            ordinare i risultati su quella colonna e di effettuare delle ricerche parziali
        """ 
        # creazione del menu popup
        self.o_table_popup = QMenu(self)
        self.o_table_popup_index = index        
        
        # creazione del campo di input per la where
        self.e_popup_where = QLineEdit()
        self.e_popup_where.setPlaceholderText('where...')
        self.e_popup_where.editingFinished.connect(self.slot_where_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(self.e_popup_where)        
        self.o_table_popup.addAction(v_action)
                
        # bottone per ordinamento ascendente
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/order_a_z.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
        v_sort_a_z = QPushButton()
        v_sort_a_z.setText('Sort asc')
        v_sort_a_z.setIcon(icon1)        
        v_sort_a_z.clicked.connect(self.slot_order_asc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_a_z)        
        self.o_table_popup.addAction(v_action)

        # bottone per ordinamento discendente
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/order_z_a.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        v_sort_z_a = QPushButton()
        v_sort_z_a.setText('Sort desc')
        v_sort_z_a.setIcon(icon2)
        v_sort_z_a.clicked.connect(self.slot_order_desc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_z_a)        
        self.o_table_popup.addAction(v_action)
        
        # bottone per raggruppamento su colonna
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/group.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        v_group_by = QPushButton()
        v_group_by.setText('Group by')
        v_group_by.setIcon(icon3)
        v_group_by.clicked.connect(self.slot_group_by_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_group_by)        
        self.o_table_popup.addAction(v_action)
                
        # bottone per il count numero record
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/icons/sequence.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        v_count = QPushButton()
        v_count.setText('Count')
        v_count.setIcon(icon4)
        v_count.clicked.connect(self.slot_count_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_count)        
        self.o_table_popup.addAction(v_action)

        # calcolo la posizione dove deve essere visualizzato il menu popup in base alle proprietà dell'header di tabella
        headerPos = self.o_table.mapToGlobal(self.o_table_hH.pos())
        posY = headerPos.y() + self.o_table_hH.height()
        posX = headerPos.x() + self.o_table_hH.sectionPosition(index) - self.o_table_hH.offset()
        self.o_table_popup.exec_(QPoint(posX, posY))        

    def slot_where_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Esecuzione della where specifica
        """
        if self.e_popup_where.text() != '':
            # prendo l'item dell'header di tabella             
            v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)
        
            # wrap dell'attuale select con altra order by
            v_new_select = "SELECT * FROM (" + self.v_select_corrente + ") WHERE (UPPER(" + v_header_item.text() + ") LIKE '%" + self.e_popup_where.text().upper() + "%')"
        
            # rieseguo la select
            self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_order_asc_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Ordinamento dei risultati sulla colonna attiva
        """
        self.select_corrente_order_by('ASC')

    def slot_order_desc_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Ordinamento dei risultati sulla colonna attiva
        """
        self.select_corrente_order_by('DESC')

    def select_corrente_order_by(self, p_tipo_ordinamento):
        """
           Gestione menu popup all'interno dei risultati
           Riesegue la select corrente con il tipo di ordinamento richiesto
        """
        # prendo l'item dell'header di tabella 
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)
        
        # wrap dell'attuale select con altra order by
        v_new_select = 'SELECT * FROM (' + self.v_select_corrente + ') ORDER BY ' + v_header_item.text() + ' ' + p_tipo_ordinamento
                
        # rieseguo la select
        self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_group_by_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Riesegue la select corrente con la group by sul campo scelto
        """
        # prendo l'item dell'header di tabella 
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)
        
        # wrap dell'attuale select con altra order by
        v_new_select = 'SELECT ' + v_header_item.text() + ', COUNT(*) FROM (' + self.v_select_corrente + ') GROUP BY ' +  v_header_item.text() + ' ORDER BY ' + v_header_item.text()
                
        # rieseguo la select
        self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_count_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Riesegue la select corrente con la count numero totale di record
        """
        # prendo l'item dell'header di tabella 
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)
        
        # wrap dell'attuale select con altra order by
        v_new_select = 'SELECT COUNT(*) FROM (' + self.v_select_corrente + ')'
                
        # rieseguo la select
        self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_clear(self, p_type):
        """
           Pulisce risultati e output se p_type = 'ALL'
           altrimenti solo risultati se p_type = 'RES'
           o output se p_type = 'OUT'
        """        
        if p_type == 'ALL' or p_type == 'RES':
            self.o_table.clear()
            self.o_table.setColumnCount(0)                                                                
            self.o_table.setRowCount(0)                        
        
        if p_type == 'ALL' or p_type == 'OUT':
            self.o_output.clear()
    
    def slot_e_sql_modificato(self):
        """
           Viene richiamato quando si modifica del testo dentro la parte di istruzione sql
        """                
        self.v_testo_modificato = True
        # aggiorno i dati della statusbar
        self.aggiorna_statusbar()
                                                                       
    def slot_esegui(self):
        """
           Prende tutto il testo selezionato ed inizia ad eseguirlo step by step
           Nota Bene! Nell'editor sql l'utente può aver scritto PL-SQL, SQL o entrambe le cose, intervvallati
                      da segni di separazione come / e ;
           Se si attiva v_debug, variabile interna, verrà eseguito l'output di tutte le righe processate
        """
        # se metto a true v_debug usciranno tutti i messaggi di diagnostica della ricerca delle istruzioni
        v_debug = False
        def debug_interno(p_message):
            if v_debug:
                print(p_message)        

        # imposto la var di select corrente che serve in altre funzioni
        self.v_select_corrente = ''

        # prendo tutto il testo o solo quello evidenziato dall'utente
        if self.e_sql.selectedText():
            v_testo = self.e_sql.selectedText()            
            # imposto la var che in caso di script che contiene più istruzioni separate da / tenga conto delle righe
            # delle sezioni precedenti (in questo caso parto dalla riga relativa! ad esempio ho spezzoni di script e non parto dall'inizio....)
            self.v_offset_numero_di_riga, v_start_pos = self.e_sql.getCursorPosition()
        else:                        
            v_testo = self.e_sql.text()
            # imposto la var che in caso di script che contiene più istruzioni separate da / tenga conto delle righe
            # delle sezioni precedenti
            self.v_offset_numero_di_riga = 0

        if v_testo == '':
            # emetto errore sulla barra di stato 
            message_error('No instruction!')                                 
            return 'ko'
        
        # prendo il testo e inizio ad eseguire le istruzioni
        # divido il testo ricevuto in input riga per riga (ritorno a capo è il divisore)
        v_righe_testo = v_testo.split(chr(10))
        # leggo riga per riga
        v_commento_multi = False
        v_istruzione = False
        v_istruzione_str = ''
        v_plsql = False
        v_plsql_idx = 0
        v_ok = ""
        for v_riga_raw in v_righe_testo:
            # dalla riga elimino gli spazi a sinistra e a destra
            v_riga = v_riga_raw.lstrip()
            v_riga = v_riga.rstrip()            
            # continuazione plsql (da notare come lo script verrà composto con v_riga_raw)
            if v_plsql:            
                debug_interno('Continuo con script plsql ' + v_riga)
                if v_riga != '':
                    # se trovo "aperture" aumento indice
                    if v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE') != -1:
                        v_plsql_idx += 1
                    # se trovo chiusure diminuisco indice
                    elif v_riga.split()[0].upper() == 'END;' != -1:
                        v_plsql_idx -= 1
                # aggiungo riga
                if v_riga != '/':
                    v_plsql_str += chr(10) + v_riga_raw
                else:
                    self.v_offset_numero_di_riga += 1
                # la chiusura trovata era l'ultima (oppure trovato chiusura dello script tramite slash) --> quindi eseguo lo script
                if v_plsql_idx <= 0 or v_riga == '/':                           
                    v_ok = self.esegui_script(v_plsql_str, False)
                    if v_ok == 'ko':                        
                        return 'ko'
                    v_plsql = False
                    v_plsql_str = ''
                    v_plsql_idx = 0
            # riga vuota (ma esterna a plsql)
            elif v_riga == '':            
                self.v_offset_numero_di_riga += 1
            # se siamo all'interno di un commento multiplo, controllo se abbiamo raggiunto la fine (se è un'istruzione non faccio pulizia dei commenti)
            elif v_commento_multi and v_riga.find('*/') == -1 and v_istruzione_str == '':
                self.v_offset_numero_di_riga += 1
            elif v_commento_multi and v_riga.find('*/') != -1 and v_istruzione_str == '':        
                self.v_offset_numero_di_riga += 1
                v_commento_multi = False
            # commenti monoriga (se è un'istruzione non faccio pulizia dei commenti)
            elif (v_riga[0:2] == '--' or v_riga[0:6] == 'PROMPT' or (v_riga[0:2] == '/*' and v_riga.find('*/') != -1)) and v_istruzione_str == '':                
                self.v_offset_numero_di_riga += 1
            # commento multi multiriga (se è un'istruzione non faccio pulizia dei commenti)
            elif v_riga[0:2] == '/*' and v_istruzione_str == '':
                self.v_offset_numero_di_riga += 1
                v_commento_multi = True            
            # continuazione di una select, insert, update, delete....
            elif v_istruzione and v_riga.find(';') == -1:
                 v_istruzione_str += chr(10) + v_riga
            # continuazione di una select dove la riga inizia con una costante
            elif v_istruzione and v_riga[0] == "'":
                v_istruzione_str += v_riga
            # fine di una select, insert, update, delete.... con punto e virgola
            elif v_istruzione and v_riga[-1] == ';':
                v_istruzione = False
                v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]
                v_ok = self.esegui_istruzione(v_istruzione_str)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... monoriga
            elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','ALTER','DROP','COMMENT') and v_riga[-1] == ';':
                v_istruzione_str = v_riga[0:len(v_riga)-1]
                v_ok = self.esegui_istruzione(v_istruzione_str)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... multiriga
            elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','ALTER','DROP','COMMENT'):
                v_istruzione = True
                v_istruzione_str = v_riga
            # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)       
            elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
                debug_interno('Inizio plsql ')
                v_plsql = True
                v_plsql_idx += 1
                v_plsql_str = v_riga_raw
            # dichiarazione di una bind variabile (secondo lo standard definito da sql developer es. VARIABLE v_nome_var VARCHAR2(100))
            # sono accettati solo i tipi VARCHAR2, NUMBER e DATE
            elif v_riga.split()[0].upper() in ('VARIABLE','VAR'):                                
                v_split = v_riga.split()
                # chiamo la procedura che si occupa di aggiornare la lista delle bind, passando il nome della var e il suo tipo
                # e ne visualizzo il contenuto
                self.bind_variable(p_function='ADD', p_variabile_nome=v_split[1].upper(), p_variabile_tipo=v_split[2].upper())
            else:
                message_error('Unknown command type: ' + v_riga_raw + '.....')
                return 'ko'                

        # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
        if v_plsql and v_plsql_str != '':
            v_ok = self.esegui_script(v_plsql_str, False)            
        
        # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
        if v_istruzione and v_istruzione_str != '':
            v_ok = self.esegui_istruzione(v_istruzione_str)  

        return v_ok

    def esegui_istruzione(self, p_istruzione):
        """
           Esegue istruzione p_istruzione
        """
        global v_global_work_dir        

        v_ok = ''                
        # se trovo select eseguo select
        if p_istruzione[0:6].upper() == 'SELECT':
            v_tipo = 'SELECT'
            v_ok = self.esegui_select(p_istruzione, True)
        # ..altrimenti esegue come script
        else: 
            v_tipo = 'SCRIPT'
            v_ok = self.esegui_script(p_istruzione, True)        
                
        # aggiungo l'istruzione all'history
        write_sql_history(v_global_work_dir+'MSql.db',v_tipo,p_istruzione)

        return v_ok

    def esegui_script(self, p_plsql, p_rowcount):
        """
           Esegue script p_plsql. Se p_rowcount è true allora vengono conteggiate le righe processate (es. update)
        """              
        if p_plsql != '':
            return self.esegui_plsql(p_plsql, p_rowcount)
        else:
            message_error('No script!')
            return None

    def esegui_plsql(self, p_plsql, p_rowcount):
        """
            Eseguo il plsql che è stato passato 
            Se p_rowcount è true allora vengono conteggiate le righe processate (es. update)
            Attenzione! Esistono diversi tipi di script
                        Al momento vengono gestiti quelli che contengono:
                         - INSERT, UPDATE, DELETE (..di solito a singola istruzione)
                         - Codice PL-SQL per la creazione di oggetti (es. package, procedure, funzioni, ecc.)
                         - Codice PL-SQL puro che va eseguito e basta (al limite contiene istruzioni dbms_output)                         
                        Queste tre macro categorie vengono quindi interpretate ed eseguite da questa funzione;
                        il risultato al di fuori di queste tre casistiche è imprevedibile!
        """
        global v_global_connesso

        if v_global_connesso:            
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False

            # attivo output tramite dbms_output (1000000 è la dimensione del buffer)
            self.v_cursor.callproc("dbms_output.enable", [1000000])

            ###
            # eseguo lo script così come è stato indicato!
            ###
            v_tot_record = 0
            try:                
                self.bind_variable(p_function='DIC',p_testo_sql=p_plsql)
                self.v_cursor.execute(p_plsql,self.v_variabili_bind_dizionario)
                v_tot_record = self.v_cursor.rowcount
                self.v_esecuzione_ok = True
            # se riscontrato errore di primo livello --> emetto sia codice che messaggio ed esco
            except cx_Oracle.Error as e:                                                                                            
                # ripristino icona freccia del mouse
                Freccia_Mouse(False)
                # emetto errore 
                errorObj, = e.args                     
                self.scrive_output("Error: " + errorObj.message, "E")                                 
                # per posizionarmi alla riga in errore ho solo la variabile offset che riporta il numero di carattere a cui l'errore si è verificato
                v_riga, v_colonna = x_y_from_offset_text(p_plsql, errorObj.offset, self.setting_eol)                
                v_riga += self.v_offset_numero_di_riga
                self.e_sql.setCursorPosition(v_riga,v_colonna)                
                # ripristino icona freccia del mouse    
                Freccia_Mouse(False)
                # esco con errore
                return 'ko'

            ###
            # da qui in poi vado alla ricerca di eventuali errori 
            # var che indica se siamo in uno script di "CREATE"
            v_create = False
            # controllo se eravamo di fronte ad uno script di "CREATE"...inizio con il prendere i primi 500 caratteri (è una cifra aleatoria!)
            v_testo = p_plsql[0:500].upper()            
            if 'CREATE' in v_testo or 'REPLACE' in v_testo or 'ALTER' in v_testo or 'DROP' in v_testo:
                v_create = True
                # nettifica del testo, togliendo spazi e ritorni a capo
                v_testo = v_testo.upper().lstrip().replace('\n',' ')                
                # cerco che tipo di oggetto è stato richiesto di creare                
                if 'PACKAGEBODY' in v_testo.replace(' ',''):
                    v_tipo_script = 'PACKAGE BODY' 
                elif 'PACKAGE' in v_testo:
                    v_tipo_script = 'PACKAGE' 
                elif 'PROCEDURE' in v_testo:
                    v_tipo_script = 'PROCEDURE' 
                elif 'FUNCTION' in v_testo:
                    v_tipo_script = 'FUNCTION' 
                elif 'TABLE' in v_testo:
                    v_tipo_script = 'TABLE'
                elif 'VIEW' in v_testo:
                    v_tipo_script = 'VIEW' 
                elif 'TRIGGER' in v_testo:
                    v_tipo_script = 'TRIGGER' 
                elif 'SEQUENCE' in v_testo:
                    v_tipo_script = 'SEQUENCE' 
                else:
                    v_tipo_script = ''                        
                # ora devo cercare il nome del testo che è stato richiesto di creare....e quindi splitto il testo in parole
                v_split = v_testo.split()
                v_nome_script = ''
                # inizio a scorrere le parole presenti in questa parte di testo...
                for v_parola in v_split:                                        
                    if v_parola not in ('CREATE','OR','REPLACE','ALTER','DROP','PACKAGE','BODY','EDITIONABLE','NONEDITIONABLE','TABLE','PROCEDURE','FUNCTION','TRIGGER','VIEW','SEQUENCE','PUBLIC','SYNONYM','TYPE'):
                        v_nome_script = v_parola
                        break
                # nettifico il nome dell'oggetto che potrebbe essere nel formato "SMILE"."NOME_OGGETTO"                
                v_nome_script = v_nome_script.replace('"','')
                if '.' in v_nome_script:
                    v_nome_script = v_nome_script.split('.')[1]

            # quindi...se lo script era di "CREATE"...controllo se in compilazione ci sono stati errori...
            if v_create:
                print('CREAZIONE DELLO SCRIPT --> Tipo: ' + v_tipo_script + ' Nome: ' + v_nome_script)
                # con questa select dico a Oracle di darmi eventuali errori presenti su un oggetto                  
                self.v_cursor.execute("SELECT LINE,POSITION,TEXT FROM USER_ERRORS WHERE NAME = '" + v_nome_script + "' and TYPE = '" + v_tipo_script + "' ORDER BY NAME, TYPE, LINE, POSITION")
                v_errori = self.v_cursor.fetchall()
                # errori riscontrati --> li emetto nella parte di output e mi posiziono sull'editor alla riga e colonna indicate
                if v_errori:
                    v_1a_volta = True
                    for info in v_errori:
                        # emetto gli errori riscontrati
                        self.scrive_output("Error at line " + str(info[0]) + " position " + str(info[1]) + " " + info[2], 'E')                        
                        # solo per il primo errore mi posiziono sull'editor alle coordinate indicate
                        if v_1a_volta:                            
                            v_riga = info[0]-1 + self.v_offset_numero_di_riga
                            v_colonna = info[1]-1                            
                            self.e_sql.setCursorPosition(v_riga,v_colonna)
                            v_1a_volta = False
                    # ripristino icona freccia del mouse    
                    Freccia_Mouse(False)
                    # esco con errore
                    return 'ko'
                # tutto ok! --> scrivo nell'output messaggio di buona riuscita operazione
                else:
                    self.scrive_output(extract_word_from_cursor_pos(v_testo,1)  + ' ' + v_tipo_script + ' ' + v_nome_script + ' SUCCESSFULLY!','I')
            
            # altrimenti siamo di fronte ad uno script di pl-sql interno o di insert,update,delete,grant che vanno gestiti con apposito output
            else:
                # preparo le var per leggere l'output dello script
                v_chunk = 100
                v_dbms_ret = ''            
                v_m_line = self.v_cursor.arrayvar(str, v_chunk)
                v_m_num_lines = self.v_cursor.var(int)
                v_m_num_lines.setvalue(0, v_chunk)

                # leggo output dello script
                while True:
                    self.v_cursor.callproc("dbms_output.get_lines", (v_m_line, v_m_num_lines))    
                    v_num_lines = int(v_m_num_lines.getvalue())
                    v_lines = v_m_line.getvalue()[:v_num_lines]
                    for line in v_lines:
                        v_dbms_ret += str(line) + '\n'
                    if v_num_lines < v_chunk:
                        break
                
                # se richiesto output del numero di record...
                if p_rowcount:
                    # il numero lo riporto solo per (insert, update, delete...)
                    if p_plsql.split()[0].upper() in ('INSERT','UPDATE','DELETE'):
                        self.scrive_output(p_plsql.split()[0] + ' ' + str(v_tot_record) + ' row(s)', 'I')    
                    # altrimenti (es. comment on table) emetto semplice messaggio di esecuzione
                    else:
                        self.scrive_output(p_plsql.split()[0] + ' EXECUTED!', 'I')    
                else:
                    # porto l'output a video (tipico è quello di script che contengono dbms_output)
                    if v_dbms_ret != '':
                        self.scrive_output(v_dbms_ret, 'I')
                    else:
                        self.scrive_output('Script executed!', 'I')

            # ripristino icona freccia del mouse
            Freccia_Mouse(False)
            # aumento il numero di riga di offset (serve per eventuale script successivo di questo gruppo di esecuzione)            
            self.v_offset_numero_di_riga += len(p_plsql.split(chr(10)))
        
        # tutto ok ... aggiungo istruzione all'history
        write_sql_history(v_global_work_dir+'MSql.db','SCRIPT',p_plsql)

        # refresh della sezione variabili bind
        if len(self.v_variabili_bind_nome) != 0:            
            self.bind_variable(p_function='SHOW')

        # esco con tutto ok
        return None
                
    def esegui_select(self, p_select, p_corrente):
        """
           Esegue p_select (solo il parser con carico della prima serie di record)
               se p_corrente è True la var v_select_corrente verrà rimpiazzata
        """
        global v_global_connesso
        global o_global_preferences

        if v_global_connesso:                        
            # pulisco elenco
            self.slot_clear('RES')            
            # pulisco la matrice che conterrà elenco delle celle modificate
            self.v_matrice_dati_modificati = []
            
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False
            # azzero le var di riga e colonna (serviranno per il carico della pagina)            
            self.v_pos_y = 0

            # prendo solo il testo che eventualmente l'utente ha evidenziato a video
            if p_corrente:
                self.v_select_corrente = p_select
            
            # se la tabella deve essere editabile
            # all'sql scritto dall'utente aggiungo una parte che mi permette di avere la colonna id riga
            # questa colonna mi servirà per tutte le operazioni di aggiornamento
            if o_global_preferences.editable:
                v_select = 'SELECT ROWID, MY_SQL.* FROM (' + p_select + ') MY_SQL'    
            else:
                v_select = p_select

            # esegue sql contenuto nel campo a video                    
            try:                
                self.bind_variable(p_function='DIC',p_testo_sql=v_select)
                self.v_cursor.execute(v_select, self.v_variabili_bind_dizionario)                            
                self.v_esecuzione_ok = True
            # se riscontrato errore --> emetto sia codice che messaggio
            except cx_Oracle.Error as e:                                                
                # ripristino icona freccia del mouse
                Freccia_Mouse(False)
                # emetto errore nella sezione di output
                errorObj, = e.args    
                self.scrive_output("Error: " + errorObj.message, "E")                                            
                return 'ko'
                        
            # lista contenente le intestazioni (tramite apposita funzione si ricavano i nomi delle colonne dall'sql che si intende eseguire)
            self.nomi_intestazioni = nomi_colonne_istruzione_sql(self.v_cursor)                                    
            self.o_table.setColumnCount(len(self.nomi_intestazioni))                                                    
            # lista contenente i tipi delle colonne 
            self.tipi_intestazioni = self.v_cursor.description                        
            # setto le intestazioni e imposto il numero di righe a 1
            self.o_table.setHorizontalHeaderLabels(self.nomi_intestazioni)                                    

            # se tutto ok, posso procedere con il caricare la prima pagina            
            self.carica_pagina()   

            # refresh della sezione variabili bind
            if len(self.v_variabili_bind_nome) != 0:
                self.bind_variable(p_function='SHOW')

            # posizionamento sulla parte di output risultati select
            self.o_tab_widget.setCurrentIndex(0) 

            # Ripristino icona freccia del mouse
            Freccia_Mouse(False)
            return None                     

    def carica_pagina(self):
        """
           Carica i dati del flusso record preparato da esegui_select
        """
        global v_global_connesso
        global o_global_preferences

        if v_global_connesso and self.v_esecuzione_ok:
            # indico che sto caricando la pagina
            self.v_carico_pagina_in_corso = True

            # carico la prossima riga del flusso dati
            try:
                v_riga_dati = self.v_cursor.fetchone()
            except cx_Oracle.DatabaseError as e: 
                 # ripristino icona freccia del mouse
                Freccia_Mouse(False)
                # emetto errore sulla barra di stato 
                errorObj, = e.args    
                message_error("Error to fetch data: " + errorObj.message)                                            
                return 'ko'
            except cx_Oracle.InterfaceError as e: 
                # ripristino icona freccia del mouse
                Freccia_Mouse(False)
                # emetto errore sulla barra di stato 
                errorObj, = e.args    
                message_error("Error to fetch data: " + errorObj.message)                                            
                return 'ko'
            
            # se ero a fine flusso --> esco
            if v_riga_dati == None:
                return 'ko'

            # imposto la riga a 1 (inizio caricamento prima riga del flusso dati)
            if self.v_pos_y == 0:
                self.o_table.setRowCount(1)                        
            # carico i dati presi dal db dentro il modello                        
            while True:
                x = 0   
                # imposto altezza della riga (sotto un certo numero non va)
                self.o_table.setRowHeight(self.v_pos_y, self.v_altezza_font_output)                                         
                for field in v_riga_dati:                                                                                                                        
                    # campo stringa
                    if isinstance(field, str):                                                 
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( field ) )                                                                
                    # campo numerico intero (se non funziona provare con i cx_Oracle type)
                    elif isinstance(field, int):                           
                        # per dare coerenza a tutte le operazioni svolte sui dati il formato di base viene definito Italiano                                
                        v_item = QTableWidgetItem('{:d}'.format(field))                        
                        v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)   
                        self.o_table.setItem(self.v_pos_y, x, v_item)                    
                    # campo numerico reale (se non funziona provare con i cx_Oracle type)
                    elif isinstance(field, float):   
                        # per dare coerenza a tutte le operazioni svolte sui dati il formato di base viene definito Italiano        
                        locale.setlocale(locale.LC_ALL, 'it_IT')                                             
                        v_item = QTableWidgetItem(locale.str(field))                        
                        v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)   
                        self.o_table.setItem(self.v_pos_y, x, v_item)                    
                    # campo nullo
                    elif field == None:                                 
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( "" ) )                
                    # campo data
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.DATETIME:                                                                            
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( str(field) ) )       
                    # campo raw (si tratta di byte che vengono convertiti in stringa in formato hex)
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.DB_TYPE_RAW:                          
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( field.hex().upper() ) )       
                    # se il contenuto è un blob...utilizzo il metodo read sul campo field, poi lo inserisco in una immagine
                    # che poi carico una label e finisce dentro la cella a video
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.BLOB:
                        qimg = QImage.fromData(field.read())
                        pixmap = QPixmap.fromImage(qimg)   
                        label = QLabel()
                        label.setPixmap(pixmap)                        
                        self.o_table.setCellWidget(self.v_pos_y, x, label )                
                    # se il contenuto è un clob...leggo sempre tramite metodo read e lo carico in un widget di testo largo
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.CLOB:                        
                        qtext = QtWidgets.QTextEdit(field.read())    
                        # da notare come prendendo qtext e trasformandolo in plaintext le prestazioni migliorino di molto                    
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( qtext.toPlainText() ) )                                                                                                                
                    x += 1
                # conto le righe (il numeratore è partito da 0, quindi è corretto che venga incrementato a questo punto)
                self.v_pos_y += 1                
                # aumento il numero di righe nella tabella a video
                self.o_table.setRowCount(self.v_pos_y + 1)                   
                # se raggiunto il numero di righe per pagina (100) --> esco dal ciclo
                if self.v_pos_y % 100 == 0:                
                    break
                # carico la prossima riga del flusso dati
                v_riga_dati = self.v_cursor.fetchone()
                # se raggiunta ultima riga del flusso di dati --> esco dal ciclo
                if v_riga_dati == None:
                    # tolgo la riga che avevo aggiunto
                    self.o_table.setRowCount(self.v_pos_y)                        
                    break
            
            # indico di calcolare automaticamente la larghezza delle colonne
            if o_global_preferences.auto_column_resize:                
                self.o_table.resizeColumnsToContents()

            # indico che carico pagina terminato
            self.v_carico_pagina_in_corso = False

            # se è stato richiesto di permettere la modifica dei dati, vuol dire che è presente come prima colonna il rowid, che quindi va nascosta!
            if o_global_preferences.editable:
                self.o_table.setColumnHidden(0, True)
            else:
                self.o_table.setColumnHidden(0, False)

            # se ero a fine flusso --> esco con codice specifico
            if v_riga_dati == None:
                return 'ko'
    
    def slot_scrollbar_azionata(self, posizione):
        """
            Controllo avanzamento della scrollbar per tenere sotto controllo elenchi di grandi dimensioni
        """
        # se esecuzione ok
        if not self.v_esecuzione_ok:
            return 'ko'

        # se sono arrivato alla punto più basso della scrollbar, vuol dire che posso caricare gli altri dati
        if posizione == self.o_table.verticalScrollBar().maximum() and self.v_pos_y > 0:            
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # carico prossima pagina
            self.carica_pagina()
                        
            # Ripristino icona freccia del mouse
            Freccia_Mouse(False)

    def slot_go_to_end(self):
        """
           Scorro fino alla fine della tabella           
        """            
        # se esecuzione ok
        if not self.v_esecuzione_ok:
            return 'ko'

        # creo una barra di avanzamento infinita
        v_progress = avanzamento_infinito_class("sql_editor.gif")

        # carico tutte le pagine fino ad arrivare in fondo (siccome vengono caricati 100 record per pagina....)
        v_counter = 0 
        while self.carica_pagina() != 'ko':
            v_counter += 1            
            # visualizzo barra di avanzamento e se richiesto interrompo
            v_progress.avanza('Loading progress of ' + str(v_counter*100) + ' records',v_counter)
            if v_progress.richiesta_cancellazione:                        
               break
        
        # chiudo la barra di avanzamento
        v_progress.chiudi()

        # mi posiziono ultimo record di tabella
        self.o_table.scrollToBottom()

    def slot_go_to_top(self):
        """
           Scorro fino all'inizio della tabella
        """        
        # mi posiziono in cima
        self.o_table.scrollToTop()

    def slot_commit_rollback(self, p_azione):
        """
           Esegue la commit o la rollback
        """
        global v_global_connesso
        global v_global_connection

        if v_global_connesso:
            if p_azione == 'Commit':
                # eseguo la commit
                v_global_connection.commit()
                # emetto messaggio e mi sposto sul tab dei messaggi
                self.scrive_output('COMMIT!','S')            
            elif p_azione == 'Rollback':
                # eseguo la rollback
                v_global_connection.rollback()
                # emetto messaggio e mi sposto sul tab dei messaggi
                self.scrive_output('ROLLBACK!','I')            

    def slot_o_table_item_modificato(self, x, y):
        """
            Funzione che viene richiamata quando un item della tabella viene modificato (solo quando attiva la modifica)
        """        
        if not self.v_carico_pagina_in_corso:            
            print('ciao' + str(x) + str(y))
            # memorizzo nella matrice la coppia x,y della cella modificata
            self.v_matrice_dati_modificati.append((x,y))            

    def slot_save_modified_data(self):
        """
           Prende tutti gli item modificati nella tabella ed esegue gli aggiornamenti!
           Attenzione! Siccome alla fine viene fatta una commit, vengono salvate anche tutte istruzioni sql che l'utente ha eseguito in precedenza!
        """        
        # se il focus è rimasto nella cella, allora prendo il valore della cella e lo carico nella matrice degli item modificati
        #self.slot_o_table_item_modificato(self.o_table.currentRow(),self.o_table.currentColumn())        

        # sposto il focus così che se utente rimasto nella cella, scatta il cambio di stato
        #QTimer.singleShot(0, self.e_sql.setFocus)

        # dalla select_corrente ricavo il nome della tabella
        v_table_name = ''
        v_elementi = self.v_select_corrente.split()        
        for i in range(1,len(v_elementi)):
            if v_elementi[i].upper()=='FROM':
                v_table_name = v_elementi[i+1]
                break
                
        # gli item modificati sono all'interno della matrice
        for yx in self.v_matrice_dati_modificati:            
            # creo l'update (nella matrice ho la riga e la colonna corrispondente (ricordarsi che le righe partono da 0 e che la colonna 0 contiene il rowid))            
            v_valore_cella = self.o_table.item(yx[0],yx[1]).text()
            v_rowid = self.o_table.item(yx[0],0).text()
            v_update = "UPDATE " + v_table_name + " SET " + self.nomi_intestazioni[yx[1]] + "='" + v_valore_cella + "' WHERE ROWID = '" + v_rowid + "'"
            self.e_sql.append(chr(10) + v_update + ';')                

    def slot_export_to_excel_csv(self):
        """
           Prende i dati presenti in tabella e li esporta in excel....viene usato il formato csv anche se in un primo momento
           era stato predisposto per scrivere in modo nativo excel....ma non avendo (al momento) la possibilità di capire differenza
           tra colonne numeriche e carattere, sono tornato al csv
        """
        global v_global_work_dir
        global o_global_preferences

        # carico tutti i dati del cursore 
        self.slot_go_to_end()

        # estraggo i dati dalla tableview (se errore la tabella è vuota e quindi esco)        
        v_model = self.o_table.model()
        if v_model == None:
            return None        

        # creo file fisso in directory di lavoro
        v_csv_file = open(v_global_work_dir + 'Export_data.csv','w', newline='', encoding='utf-8')

        # creazione della riga intestazioni
        v_intestazioni = ''
        v_1a_volta = True
        for nome_colonna in self.nomi_intestazioni:                        
            if v_1a_volta:
                v_intestazioni += nome_colonna            
                v_1a_volta = False
            else:
                v_intestazioni += o_global_preferences.csv_separator + nome_colonna            

        v_csv_file.write(v_intestazioni+'\n')
                
        # Creazione di tutta la tabella                
        for row in range(v_model.rowCount()):            
            v_riga = ''        
            v_1a_volta = True
            for column in range(v_model.columnCount()):
                v_index = v_model.index(row, column)                
                v_campo = v_model.data(v_index)
                # normalizzo il campo se vuoto
                if v_campo is None:
                    v_campo = ''
                # aggiungo il campo alla riga
                if v_1a_volta:
                    v_riga += v_campo
                    v_1a_volta = False
                else:
                    v_riga += o_global_preferences.csv_separator + v_campo            
            v_csv_file.write(v_riga+'\n')

        v_csv_file.close()
        
        # Apro direttamente il file            
        try:
            os.startfile(v_global_work_dir + 'Export_data.csv')
        except:
            message_error('Error in file creation!')
      
    def closeEvent(self, e):
        """
           Intercetto l'evento di chiusura del form e controllo se devo chiedere di salvare o meno
           Questa funzione sovrascrive quella nativa di QT            
        """
        global o_global_preferences
        global v_global_work_dir

        v_salvare = self.check_to_save_file()                    
        # richiesto di salvare e poi di chiudere
        if v_salvare == 'Yes':        
            self.v_editor_chiuso = True            
            e.accept() 
        # interrompere la chiusura
        elif v_salvare == 'Cancel':            
            self.v_editor_chiuso = False            
            e.ignore()            
        # chiudere
        else:   
            # alla chiusura salvo in uno storico la posizione del testo in modo si riposizioni alla prossima riapertura         
            v_num_line, v_num_pos = self.e_sql.getCursorPosition()                
            if o_global_preferences.remember_text_pos:
                 write_files_history(v_global_work_dir+'MSql.db', self.objectName(), v_num_line, v_num_pos)          
            # imposto indicatore di chiusura e chiudo
            self.v_editor_chiuso = True            
            self.close()    
    
    def check_to_save_file(self):
        """
           Controllo se ci sono dati da salvare...
        """
        # se non ci sono dati modificati o siamo in presenza di un editor chiuso...esco senza salvare
        if not self.v_testo_modificato or self.v_editor_chiuso:            
            return 'No'

        # ci sono dati modificati e quindi chiedo come procedere ...
        v_scelta = message_question_yes_no_cancel("The document " + self.objectName() + " was modified." + chr(13) + "Do you want to save changes?")        
        # utente richiede di interrompere 
        if v_scelta == 'Cancel':
            return 'Cancel'
        # utente chiede di salvare
        elif v_scelta == 'Yes':            
            if self.objectName() == "":                
                v_ok, v_nome_file = salvataggio_editor(True, self.objectName(), self.e_sql.text())
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    self.v_testo_modificato = False
                    return 'Yes'
            else:                      
                v_ok, v_nome_file = salvataggio_editor(False, self.objectName(), self.e_sql.text())                          
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    self.v_testo_modificato = False
                    return 'Yes'
        # utente chiede di non salvare
        else:
             return 'No'

    def slot_font_editor_selector(self, p_font):
        """
           Visualizza la scelta del font da usare nell'editor e lo reimposta nell'editor
           Se p_font viene ricevuto in input, non apre la dialog ma lo setta
        """
        if p_font is None:
            font, ok = QFontDialog.getFont(QtGui.QFont("Courier New"))
        else:
            font = p_font
            ok = True
        
        if ok:
            self.v_lexer.setFont(font)            

    def slot_font_result_selector(self, p_font):
        """
           Visualizza la scelta del font da usare nell'output e lo reimposta nell'output
           Se p_font viene ricevuto in input, non apre la dialog ma lo setta
        """
        if p_font is None:
            font, ok = QFontDialog.getFont(QtGui.QFont("Arial"))
        else:
            font = p_font
            ok = True

        if ok:
            self.o_table.setFont(font)
            self.o_output.setFont(font)
            # imposto var generale che indica l'altezza del font
            self.v_altezza_font_output = font.pointSize()
    
    def slot_find(self):
        """
           Apre la dock per la ricerca del testo 
        """            
        self.dockFindWidget.show()
        self.e_find.setFocus()  
        # mi è risultato più comodo pulire il campo di ricerca quando riaccedo alla finestra passando dal menu
        self.e_find.clear()                 
                
        # definizione della struttura per elenco dei risultati (valido solo per find all)       
        self.find_all_model = QtGui.QStandardItemModel()        
        self.o_find_all_result.setModel(self.find_all_model)

    def slot_find_all(self):
        """
           Ricerca della stringa in tutto il testo
        """
        # pulisco elenco
        self.find_all_model.clear()

        # prelevo la stringa da ricercare
        v_string_to_search = self.e_find.text()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                        
            # lancio la ricerca su tutto e senza effetti a video (da notare come findFirst è un metodo di QScintilla)...
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, 0, 0, False, False, False)
            # ciclo alla ricerca di tutte le ricorrenze            
            v_num = 1
            while v_found:
                # ricavo la posizione in coordinate dove è stata trovata la stringa
                v_start_line, v_start_pos, v_end_line, v_end_pos = self.e_sql.getSelection()
                # inizio a costruire la riga di risultato che riporta il numero della riga dove stringa trovata + il suo testo 
                v_risultato = str(v_start_line + 1) + ' - '
                # per prendere la riga devo fare una selezione di tutta riga... (fino all'inizio della riga successiva visto che non conosco il fine riga...)
                self.e_sql.setSelection(v_start_line, 0, v_start_line + 1, -1)
                # aggiungo al numero di riga il testo completo della riga (vado ad eliminare spazi a sinistra e ritorni a capo)
                v_risultato = v_risultato + self.e_sql.selectedText().lstrip()
                v_risultato = v_risultato.replace('\n','')
                # aggiungo il risultato all'elenco
                self.find_all_model.appendRow(QtGui.QStandardItem(v_risultato))        
                # lancio la ricerca alla riga successiva
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, v_start_line + 1, -1, False, False, False)                        
                # conto le ricorrenze
                v_num += 1
            # se trovate più ricorrenze ... mi posiziono sulla prima rilanciando la ricerca dall'inizio...
            if v_num > 1:
                # lancio la ricerca su tutto e senza effetti a video (da notare come findFirst è un metodo di QScintilla)...
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, 0, 0, False, False, False)
        
    def slot_find_all_click(self, p_index):
        """
           Partendo dalla selezione di find_all, si posiziona sulla specifica riga di testo dell'editor
        """
        # prelevo la stringa da ricercare
        v_string_to_search = self.e_find.text()
        # prendo elemento dell'elenco selezionato
        v_selindex = self.find_all_model.itemFromIndex(p_index)
        v_stringa = v_selindex.text()               
        if v_stringa != '':
            # dalla stringa dell'elenco, estraggo il numero di riga e mi posiziono sull'editor
            v_goto_line = v_stringa[0:v_stringa.find('-')]
            if v_goto_line != '':
                # mi posiziono alla riga richiesta sull'editor
                self.e_sql.setCursorPosition(int(v_goto_line)-1,0)    
                # eseguo la ricerca in modo da evidenziare il contenuto            
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, int(v_goto_line)-1, 0, True, False, False)
                                
    def slot_find_next(self):
        """
           Ricerca la prossima ricorrenza verso il basso
        """        
        v_string_to_search = self.e_find.text()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                       
            # lancio la ricerca dicendo di posizionarsi sulla prossima ricorrenza 
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, -1, -1, True, False, False)
            # se sono arrivato alla fine, chiedo se si desidera ripartire dall'inizio...da notare come viene poi richiamata questa stessa funzione!
            if not v_found:
                if message_question_yes_no('Passed the end of file!'+chr(10)+'Move to the beginnig?') == 'Yes':                    
                    self.e_sql.setCursorPosition(1,0)
                    self.slot_find_next()

    def slot_find_e_replace(self):
        """
           Ricerca e sostituisci
        """
        self.dockReplaceWidget.show()
        # posiziono il cursore sul campo di trova
        self.e_replace_search.setFocus()

    def slot_find_e_replace_find(self):
        """
           Ricerca la prossima ricorrenza verso il basso
        """        
        v_string_to_search = self.e_replace_search.text()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                       
            # lancio la ricerca dicendo di posizionarsi sulla prossima ricorrenza 
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, -1, -1, True, False, False)
    
    def slot_find_e_replace_next(self):        
        """
           Sostituisce la ricorrenza attuale (ignora differenze tra maiuscole e minuscole)
        """
        # testo da ricercare
        v_string_to_search = self.e_replace_search.text().upper()
        # nuovo testo
        v_string_to_replace = self.e_replace.text()

        # se inserito una stringa di ricerca...
        if v_string_to_search != '' and v_string_to_replace != '':    
            # se il testo selezionato è esattamente ciò che si sta cercando, faccio la replace 
            if self.e_sql.selectedText() == v_string_to_search:                    
                # eseguo la replace
                self.e_sql.replace(v_string_to_replace)                
            # ... altrimenti continuo come se fosse una ricerca next
            else:
                # ricavo la posizione dove è posizionato il cursore 
                v_start_line, v_start_pos = self.e_sql.getCursorPosition()
                # lancio la ricerca a partire da quella posizione
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, v_start_line, v_start_pos, False, False, False)            

    def slot_find_e_replace_all(self):        
        """
           Sostituisce tutte le ricorrenze (ignora differenze tra maiuscole e minuscole)
        """
        # testo da ricercare
        v_string_to_search = self.e_replace_search.text().upper()
        # nuovo testo
        v_string_to_replace = self.e_replace.text()

        # se inserito una stringa di ricerca...
        if v_string_to_search != '' and v_string_to_replace != '':                        
            # lancio la ricerca su tutto e senza effetti a video (da notare come findFirst è un metodo di QScintilla)...
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, 0, 0, False, False, False)
            while v_found:
                # ricavo la posizione in coordinate dove è stata trovata la stringa
                v_start_line, v_start_pos, v_end_line, v_end_pos = self.e_sql.getSelection()
                # eseguo la replace
                self.e_sql.replace(v_string_to_replace)
                # proseguo la ricerca alla posizione successiva
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, v_start_line, v_start_pos + 1, False, False, False)                        

    def slot_goto_line(self):
        """
           Visualizza window per richiedere a che riga dell'editor posizionarsi e poi si posiziona
        """
        try:
            # visualizzo la finestra di richiesta numero riga
            self.dialog_goto_line.show()
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog per chiedere i dati
            self.dialog_goto_line = QtWidgets.QDialog()
            self.win_goto_line = Ui_GotoLineWindow()        
            self.win_goto_line.setupUi(self.dialog_goto_line)                
            # da notare come il collegamento delle funzioni venga fatto in questo punto e non nella ui            
            self.win_goto_line.b_goto_line.clicked.connect(self.slot_goto_line_exec)                
            # visualizzo la finestra di ricerca
            self.dialog_goto_line.show()

    def slot_goto_line_exec(self):
        """
           Esegue il posizionamento sull'editor, alla riga richiesta
        """
        # converto in numero il campo inserito dall'utente
        try:
            v_line = int( self.win_goto_line.e_goto_line.currentText() )
        except:
            message_error('Insert a valid number!')
            return 'ko'
        
        # normalizzo il numero di riga a inizio o fine documento
        if v_line == 0 or v_line < 0:
            v_line = 0
        elif v_line > self.e_sql.lines():
            v_line = self.e_sql.lines() - 1
        else:
            v_line -= 1 

        # mi posiziono alla riga richiesta sull'editor
        self.e_sql.setCursorPosition(v_line,0)

        # nascondo la window di posizionamento cursore
        self.dialog_goto_line.close()

    def slot_map(self):
        """
           Apre la window che visualizza la mappa di procedure-funzioni all'interno dell'editor
           Da li, l'utente, può navigare facendo click sugli elementi della lista
        """ 
        # visualizzo il widget della mappa
        self.dockMapWidget.show()
                   
        # carico la mappa
        self.slot_refresh_map()

        # posiziono il focus nel campo di ricerca
        self.e_map_search.setFocus()

    def slot_refresh_map(self):
        """
           Carica la mappa delle procedure-funzioni rispetto al contenuto dell'editor
           Se è stato indicato un parametro di ricerca, estraggo solo quanto corrispondente
        """
        # imposto il modello per la visualizzazione dati                   
        self.map_model = QtGui.QStandardItemModel()        
        # pulisco l'oggetto che a video riporta i risultati
        self.map_model.clear()
        # carico nel modello la lista delle intestazioni
        self.map_model.setHorizontalHeaderLabels(['Name','Pos.'])        
        # creo le colonne per contenere i dati
        self.map_model.setColumnCount(2)        
        # creo le righe per contenere i dati
        self.map_model.setRowCount(0)                       
        # prendo il testo presente nell'editor e lo inserisco in una var di tipo lista (ogni riga un record)
        v_lista_testo = self.e_sql.text().split('\n')
        # partendo dalla lista che contiene il testo, creo un oggetto che contiene la lista di tutte le procedure-funzioni!
        v_lista_def = estrai_procedure_function(v_lista_testo)
        # controllo se inserito un testo di ricerca
        v_ricerca = self.e_map_search.text().upper()
        # leggo l'oggetto che contiene procedure-funzioni e lo carico nel modello da visualizzare a video
        v_y = 0        
        for ele in v_lista_def:          
            # l'elemento è sempre valido
            v_elemento_valido = True                              
            # se chiesta ricerca e se elemento che sto analizzando contiene la stringa del testo di ricerca, allora ok
            if v_ricerca != "":
                if ele.nome_definizione.find(v_ricerca) == -1:
                    v_elemento_valido = False
            # se elemento è valido...
            if v_elemento_valido:
                # aumento la riga 
                v_y += 1
                self.map_model.setRowCount(v_y)
                # campo che contiene il titolo della procedura-funzione
                v_item = QStandardItem(ele.nome_definizione)                        
                self.map_model.setItem(v_y-1, 0, v_item)                                                                
                # campo che contiene il numero di riga                                    
                v_item = QStandardItem('{:d}'.format(ele.numero_riga_testo))                        
                v_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)   
                self.map_model.setItem(v_y-1, 1, v_item)                                            
        # carico il modello nel widget        
        self.o_map.setModel(self.map_model)                                   
        # indico che la larghezza delle colonne si deve adattare al contenuto
        self.o_map.resizeColumnsToContents()        
        # forzo altezza delle righe (automatica in base al contenuto)
        self.o_map.verticalHeader().setDefaultSectionSize(QHeaderView.ResizeToContents)
    
    def slot_o_map_selected(self):
        """
           Mi posiziono sull'editor in base alla posizione indicata sulla mappa
        """
        # ottengo un oggetto index-qt della riga selezionata
        index = self.o_map.currentIndex()                
        # devo prendere la cella numero 1 che contiene il numero di riga a cui mi devo posizionare
        v_item_1 = self.map_model.itemFromIndex( index.sibling(index.row(), 1) )                
        # se è stata selezionata una riga, mi posiziono sull'editor
        if v_item_1 != None:                        
            # sull'editor, mi posiziono alla riga richiesta dalla mappa (meno 1 perché nel testo la prima riga è la 0)
            self.e_sql.setCursorPosition(int(v_item_1.text())-1,0)            
            # forzo il fuoco sull'editor attraverso un timer!
            QTimer.singleShot(0, self.e_sql.setFocus)
    
    def slot_format_sql_statement(self):
        """
           Prende il testo selezionato sull'editor e lo reindenta 
        """        
        # prendo il testo selezionato        
        #v_start_line, v_start_pos, v_end_line, v_end_pos = self.e_sql.getSelection()
        v_testo_sel = self.e_sql.selectedText()        
        if v_testo_sel is None or v_testo_sel == '':
            message_info("Please select a text with SQL statement!")
            return 'ko'

        # elimino il testo selezionato 
        self.e_sql.cut()
        # chiamo la reindentazione del testo (trasformando tutto in mauiscolo)
        v_testo_sel = format_sql(v_testo_sel).upper()
        # inserisco il nuovo testo al posto di quello eliminato
        self.e_sql.insert(v_testo_sel)      

    def slot_commenta(self):
        """
           Commenta la riga selezionata
        """
        v_testo_sel = self.e_sql.selectedText()        
        if v_testo_sel is None or v_testo_sel == '':        
            return 'ko'

        # elimino il testo selezionato 
        self.e_sql.cut()
        # devo capire quali carattersi sono stati usati per il ritorno a capo                
        if self.setting_eol == 'W':                        
            v_eol = '\r\n'
        else:
            v_eol = '\n'
        v_new_text = ''
        # prendo il testo selezionato e ne estraggo le righe in base al ritorno a capo
        for v_line in v_testo_sel.split(v_eol):                                    
            v_new_text += '--' + v_line + v_eol
        
        # inserisco il nuovo testo al posto di quello eliminato
        self.e_sql.insert(v_new_text)        

    def slot_scommenta(self):
        """
           Scommenta la riga selezionata
        """        
        v_testo_sel = self.e_sql.selectedText()        
        if v_testo_sel is None or v_testo_sel == '':        
            return 'ko'

        # elimino il testo selezionato 
        # vedere di sostituire la cut con altra istruzione perché la cut la segna nell'undo e quindi se successivamente utente fa
        # ctrl-z si vede che c'è stata la cut
        self.e_sql.cut()
        # devo capire quali carattersi sono stati usati per il ritorno a capo
        if self.setting_eol == 'W':                        
            v_eol = '\r\n'
        else:
            v_eol = '\n'
        v_new_text = ''
        # prendo il testo selezionato e ne estraggo le righe in base al ritorno a capo
        for v_line in v_testo_sel.split(v_eol):                                                
            if v_line[0:2]=='--':                
                v_new_text += v_line[2:] + v_eol
            else:
                v_new_text += v_line + v_eol
        
        # inserisco il nuovo testo al posto di quello eliminato
        self.e_sql.insert(v_new_text)        
    
    def scrive_output(self, p_messaggio, p_tipo_messaggio):
        """
           Scrive p_messaggio nella sezione "output" precedendolo dall'ora di sistema
        """
        global o_global_preferences
        
        # definizione dei pennelli per scrivere il testo in diversi colori (i nomi fanno riferimento al tema chiaro)
        v_pennello_rosso = QtGui.QTextCharFormat()
        v_pennello_blu = QtGui.QTextCharFormat()
        v_pennello_nero = QtGui.QTextCharFormat()
        v_pennello_verde = QtGui.QTextCharFormat()
        if o_global_preferences.dark_theme:            
            v_pennello_rosso.setForeground(Qt.red)            
            v_pennello_blu.setForeground(Qt.cyan)            
            v_pennello_nero.setForeground(Qt.white)            
            v_pennello_verde.setForeground(Qt.green)
        else:            
            v_pennello_rosso.setForeground(Qt.red)            
            v_pennello_blu.setForeground(Qt.blue)            
            v_pennello_nero.setForeground(Qt.black)            
            v_pennello_verde.setForeground(Qt.darkGreen)

        # stampo in blu l'ora di sistema
        v_time = datetime.datetime.now()        
        self.o_output.setCurrentCharFormat(v_pennello_blu)        
        self.o_output.appendPlainText(str(v_time.hour).rjust(2,'0') + ':' + str(v_time.minute).rjust(2,'0') + ':' + str(v_time.second).rjust(2,'0'))         
        # in base al tipo di messaggio stampo messaggio di colore nero o di colore rosso
        if p_tipo_messaggio == 'E':
            self.o_output.setCurrentCharFormat(v_pennello_rosso)        
            self.o_output.appendPlainText(p_messaggio)                 
        elif p_tipo_messaggio == 'S':
            self.o_output.setCurrentCharFormat(v_pennello_verde)        
            self.o_output.appendPlainText(p_messaggio)                 
        else:
            self.o_output.setCurrentCharFormat(v_pennello_nero)        
            self.o_output.appendPlainText(p_messaggio)                         
        # forzo il posizionamento in fondo all'item di risultato
        self.o_output.moveCursor(QTextCursor.End)                
        # porto in primo piano la visualizzazione del tab di output
        self.o_tab_widget.setCurrentIndex(1)                         
        
    def set_editable(self):
        """
           Questa funzione viene richiamata quando si agisce sulla checkbox di editing
        """     
        global o_global_preferences

        # se attivato...
        if o_global_preferences.editable:
            # attivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
            # pulisco la tabella costringendo l'utente a ricaricare la query in quanto deve comparire il rowid
            self.slot_clear('RES')      
        # ...
        else:
            # disattivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)            

    def set_show_end_of_line(self):
        """
           Rende visibile o meno il carattere di end of line
        """
        global o_global_preferences                
        
        # visualizzo il segnale di ritorno a capo in base alle preferenze
        self.e_sql.setEolVisibility(o_global_preferences.end_of_line)        
        # visualizzo anche i caratteri invisibili (spazi e tabulazioni)
        if o_global_preferences.end_of_line:            
            self.e_sql.SendScintilla(QsciScintillaBase.SCI_SETVIEWWS,QsciScintillaBase.SCWS_VISIBLEALWAYS)           
        else:
            self.e_sql.SendScintilla(QsciScintillaBase.SCI_SETVIEWWS,QsciScintillaBase.SCWS_INVISIBLE)           

    def bind_variable(self, p_function, p_variabile_nome=None, p_variabile_tipo=None, p_testo_sql=None):
        """
           Gestione delle struttura delle variabili bind
           La gestione delle variabili bind si avvale di diverse strutture di cui le principali solo le liste:
             - v_variabili_bind_nome
             - v_variabili_bind_nome
             - v_variabili_bind_valore
             queste liste sono passate al codice PL-SQL e servono da supporto per la visualizzazione a video
           
           Se p_function = 'ADD'  aggiunge alla struttura la variabile p_variable_name del tipo p_variabile_type; al termine esegue la funzione SHOW
              p_function = 'SHOW' esegue solo il refresh a video              
              p_function = 'DIC'  crea-ricrea il dizionario da passare alle istruzioni SQL che è contenuto nella proprietà self.v_variabili_bind_dizionario
                                  Attenzione! Lato esecuzione istruzioni SQL e PL-SQL si farà riferimento solo e unicamente al contenuto di self.v_variabili_bind_dizionario!!!!           
        """        
        # Aggiornamento delle strutture interne per la gestione delle variabili bind
        if p_function == 'ADD':
            if p_variabile_tipo.find('VARCHAR2') == -1 and p_variabile_tipo.find('NUMBER') == -1 and p_variabile_tipo.find('DATE') == -1:
                message_error(p_variabile_tipo + ' - Unrecognized type')
                return 'ko'
            # Se la var bind non esiste la aggiungo e siccome non esco dalla procedura, eseguo il refresh a video
            if p_variabile_nome not in self.v_variabili_bind_nome:
                self.v_variabili_bind_nome.append(p_variabile_nome)
                self.v_variabili_bind_tipo.append(p_variabile_tipo)
                self.v_variabili_bind_valore.append(None)

        # Crea-aggiorna la struttura dizionario self.v_variabili_bind_dizionario che verrà utilizzata per il richiamo delle istruzioni sql e pl-sql
        # Il funzionamento delle bind è particolare perché all'istruzione execute del motore di database è possibile passare una struttura dizionario con nome-valore
        # Ad esempio se ho due bind di nome V_AZIENDA e V_DIPENDENTE con valori 'TEC' e '00035' viene creato il dizionario con {'V_AZIENDA':'TEC','V_DIPENDENTE':'00035'}
        # Il motore di database ricevendo in input tale dizionario, cercherà di accoppiare per nome (e non per riferimento) le var dichiarate e inoltre gli passerà in input-output il valore
        if p_function == 'DIC':                        
            # se il dizionario non è vuoto prendo solo i valori del dizionario e li porto nelle strutture di appoggio (da notare la getvalue...è un metodo che appartiene all'oggetto var di cx_Oracle)
            if len(self.v_variabili_bind_dizionario) != 0:                
                for chiave, valore in self.v_variabili_bind_dizionario.items():                    
                    v_index = self.v_variabili_bind_nome.index(chiave)                    
                    self.v_variabili_bind_valore[v_index] = valore.getvalue(0)                    
            # pulisco il dizionario        
            self.v_variabili_bind_dizionario.clear()
            # creo il dizionario con le bind da passare al comando sql (il comando è una execute che si trova fuori da questa procedura)
            # per problemi tecnici il dizionario deve contenere solo la coppia chiave-valori delle variabili bind effettivamente presenti nel codice sql...quindi
            # bisogna scansionare l'istruzione p_testo_sql e creare il dizionario solo delle var bind effettive
            for i in range(0,len(self.v_variabili_bind_nome)):                
                v_nome_bind = ':' + self.v_variabili_bind_nome[i]
                if v_nome_bind in p_testo_sql.upper():
                    if self.v_variabili_bind_tipo[i].find('VARCHAR2') != -1: 
                        # creo una var di cx_Oracle! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(str)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto cx_Oracle.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )
                    if self.v_variabili_bind_tipo[i].find('NUMBER') != -1: 
                        # creo una var di cx_Oracle! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(int)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto cx_Oracle.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )
                    if self.v_variabili_bind_tipo[i].find('DATE') != -1:                         
                        # creo una var di cx_Oracle! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(datetime.date)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto cx_Oracle.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )            
                print('Creazione dizionario variabili bind...')
                print(self.v_variabili_bind_dizionario)
                print('-'*50)
            # esco --> tutto ok
            return 'ok'
                                    
        # Aggiornamento a video variabili bind
        # lista contenente le intestazioni
        if p_function in ('SHOW','ADD'):
            # se il dizionario non è vuoto prendo solo i valori del dizionario e li porto nelle strutture di appoggio (da notare la getvalue...è un metodo che appartiene all'oggetto var di cx_Oracle)
            if len(self.v_variabili_bind_dizionario) != 0:                
                for chiave, valore in self.v_variabili_bind_dizionario.items():                    
                    v_index = self.v_variabili_bind_nome.index(chiave)                    
                    self.v_variabili_bind_valore[v_index] = valore.getvalue(0)                    

            # preparo la struttura della tabella che visualizza l'oggetto :binds
            intestazioni = ['Name','Type','Value' ]                                
            self.bind_risultati = QtGui.QStandardItemModel()        
            self.bind_risultati.setHorizontalHeaderLabels(intestazioni)                
            self.bind_risultati.setColumnCount(len(intestazioni))                
            self.bind_risultati.setRowCount(0)                        

            for y in range(0,len(self.v_variabili_bind_nome)):            
                # colonna Name
                v_item = QtGui.QStandardItem()                
                v_item.setText(str(self.v_variabili_bind_nome[y]))            
                self.bind_risultati.setItem(y, 0, v_item )  
                # colonna Tipo di dato
                v_item = QtGui.QStandardItem()                
                v_item.setText(str(self.v_variabili_bind_tipo[y]))            
                self.bind_risultati.setItem(y, 1, v_item )  
                # colonna Valore
                v_item = QtGui.QStandardItem()                
                v_item.setText(str(self.v_variabili_bind_valore[y]))            
                self.bind_risultati.setItem(y, 2, v_item )  

            # carico il modello nel widget        
            self.o_bind.setModel(self.bind_risultati)                                           
            self.o_bind.resizeColumnsToContents()

        # porto in primo piano la visualizzazione del tab variabili bind (operazione forzata ogni volta si aggiunge una variabile)
        if p_function == 'ADD':
            self.o_tab_widget.setCurrentIndex(2)                 

        # esco --> tutto ok
        return 'ok'

    def aggiorna_statusbar(self):
        """
           Aggiorna i dati della statusbar 
        """
        v_totale_righe = str(self.e_sql.lines())        
        self.link_to_MSql_win1_class.l_num_righe_e_char.setText("Lines: " + str(v_totale_righe) + ", Length: " + str(self.e_sql.length()))        

        # reimposta larghezza del margine numeri di riga...
        self.e_sql.setMarginWidth(0, '0' + v_totale_righe)        

        # label indicatore di overwrite
        if self.v_overwrite_enabled:
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText('Overwrite')
        else:                
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText('Insert')

        # label che indica il tipo di eol 
        if self.setting_eol == 'W':        
            self.link_to_MSql_win1_class.l_eol.setText("Windows (CRLF)")         
        else:            
            self.link_to_MSql_win1_class.l_eol.setText("Unix (LF)")         

        # posizione del cursore
        v_y, v_x = self.e_sql.getCursorPosition()
        self.link_to_MSql_win1_class.l_cursor_pos.setText("Ln: " + str(v_y+1) + "  Col: " + str(v_x+1))

#
#  ___ _   _ _____ ___  
# |_ _| \ | |  ___/ _ \ 
#  | ||  \| | |_ | | | |
#  | || |\  |  _|| |_| |
# |___|_| \_|_|   \___/ 
# 
# Classe che contiene finestra info di programma                      
class MSql_win3_class(QtWidgets.QDialog, Ui_MSql_win3):
    """
        Visualizza le info del programma
    """                
    def __init__(self):
        super(MSql_win3_class, self).__init__()        
        self.setupUi(self)

#
#  _______  ______ _____ ____ _____ 
# | ____\ \/ / ___| ____|  _ \_   _|
# |  _|  \  / |   |  _| | |_) || |  
# | |___ /  \ |___| |___|  __/ | |  
# |_____/_/\_\____|_____|_|    |_|  
#                                                              
def excepthook(exc_type, exc_value, exc_tb):
    """
       Intercetta errori-eccezioni imprevisti (es. divisione per zero, e cose del genere....) e li emette come messaggio...
       in questo modo si evita la maggior parte dei fastidiosi crash di programma di cui non si capisce cosa sia successo!
    """   
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    message_error(tb)    

#
#  ____ _____  _    ____ _____ 
# / ___|_   _|/ \  |  _ \_   _|
# \___ \ | | / _ \ | |_) || |  
#  ___) || |/ ___ \|  _ < | |  
# |____/ |_/_/   \_\_| \_\|_|  
#
if __name__ == "__main__":    
    # Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
    # Nota bene! Quando tramite pyinstaller verrà creato l'eseguibile, tutti i file della cartella qtdesigner verranno messi 
    #            nella cartella principale e questa istruzione di cambio path di fatto non avrà alcun senso. Serve dunque solo
    #            in fase di sviluppo. 
    sys.path.append('qtdesigner')
        
    # controllo se programma è stato richiamato da linea di comando passando il nome di un file    
    v_nome_file_da_caricare = ''
    try:
        if sys.argv[1] != '':                
            v_nome_file_da_caricare = sys.argv[1]    
    except:
        pass    

    # controllo se esiste dir di lavoro (servirà per salvare le preferenze, ecc....)        
    if not os.path.isdir(v_global_work_dir):
        os.makedirs(v_global_work_dir)

    # sovrascrive l'hook delle eccezioni; in pratica se avverrà un errore imprevisto, dovrebbe uscire un messaggio a video...
    sys.excepthook = excepthook

    # inizializzazione ambiente grafico
    app = QtWidgets.QApplication([])    

    # se è stato scelto di avere il tema dei colori scuro, lo carico
    # Attenzione! La parte principale del tema colori rispetta il meccanismo di QT library
    #             Mentre per la parte di QScintilla ho dovuto fare le impostazioni manuali (v. definizione del lexer)
    if o_global_preferences.dark_theme:        
        app.setStyleSheet(dark_theme_definition())                    

    # avvio del programma (aprendo eventuale file indicato su linea di comando)   
    application = MSql_win1_class(v_nome_file_da_caricare)     
    application.show()
            
    # attivazione degli eventi
    sys.exit(app.exec())    