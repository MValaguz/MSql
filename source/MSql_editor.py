# 
#  __  __ ____        _ 
# |  \/  / ___|  __ _| |
# | |\/| \___ \ / _` | |
# | |  | |___) | (_| | |
# |_|  |_|____/ \__, |_|
#                  |_|  
                 
#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13 con libreria pyqt6
#  Data inizio...: 01/01/2023
#  Descrizione...: Questo programma ha la "pretesa" di essere editor SQL per ambiente Oracle....                             
#                  In questo programma sono state sperimentate diverse tecniche per la soluzione di particolari problemi...e quindi è di fatto una sorta
#                  di super esercizio....
                 
#  Funzionamento : La classe principale è MSql_win1_class che apre la window di menu e che contiene l'area mdi dove poi si raggrupperranno
#                  le varie finestre dell'editor (gestito dalla classe MSql_win2_class). La window principale si collega con la 
#                  secondaria dell'editor utilizzando un array che contiene i puntatori all'oggetto editor (MSql_win2_class). 
#                  Quindi in MSql_win1_class vi è una continua ricerca all'oggetto editor di riferimento in modo da lavorare sull'editor corrente.
#                  Tutta la parte di definizione grafica è stata creata tramite QtDesigner e i file da lui prodotti, convertiti tramite un'utilità, 
#                  in classi Python da dare poi in pasto alla libreria QT.                 
#                  Per quanto riguarda la parte di traduzione si è fatto uso di QtLinguist che sempre tramite un'utilità prende i file di programma
#                  e crea il dizionario di partenza che poi viene tradotto; la lingua di riferimento rimane l'inglese.

# Nota bene......: Alcuni widget di PyQt sono stati personalizzati; la relativa libreria si chiama custom_widget e vengono inclusi tramite promozione 
#                  dentro le definizioni di interfaccia di qtdesigner.

# Librerie di base
import sys 
import os 
import subprocess
import datetime 
import locale
import re
import traceback
import time
import psutil
# Librerie di data base Oracle
import oracledb, oracle_my_lib, oracle_executer
# Librerie grafiche QT
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Librerie QScintilla
from PyQt6.Qsci import *
# Libreria network usata per capire se MSql è già in esecuzione
from PyQt6.QtNetwork import *
# Libreria che permette di creare arte ascii grafica
from art import text2art, FONT_NAMES
# Classe per la gestione delle preferenze
from preferences import preferences_class
# Definizione del solo tema dark
from dark_theme import dark_theme_definition
# Classi qtdesigner (win1 è la window principale, win2 la window dell'editor)
from qtdesigner.MSql_editor_win1_ui import Ui_MSql_win1
from qtdesigner.MSql_editor_win2_ui import Ui_MSql_win2
# Classe qtdesigner per informazioni di programma
from qtdesigner.program_info_ui import Ui_program_info
# Classi qtdesigner per la ricerca e la sostituzione di stringhe di testo, per il posizionamento...
from qtdesigner.goto_line_ui import Ui_GotoLineWindow
from history import history_class
from preferred_sql import preferred_sql_class
# Classe qtdesigner per la richiesta di connessione e cambio di schema
from qtdesigner.connect_ui import Ui_connect_window
from qtdesigner.select_schema_ui import Ui_select_schema_window
# Classe per visualizzare la barra di avanzamento 
from avanzamento import avanzamento_infinito_class
# Utilità varie
from utilita import *
from utilita_database import *
from utilita_testo import *
# Libreria che permette, selezionata un'istruzione sql nell'editor di indentarla automaticamente
from sql_formatter.core import format_sql
# Visualizzatore delle differenze tra due testi
from diff_viewer import classDiffViewer

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
                    'Synonyms': 'SYNONYM',
                    'Others' : 'OTHERS'}

###
# Var globali
###
# Oggetto connettore DB
v_global_connection = oracledb
# Indica se si è connessi al DB
v_global_connesso = False
# Directory di lavoro del programma (diversa in base al sistema operativo)
# Attenzione! Questa dir è possibile aprirla dalla gestione delle preferenze e in quel programma è riportata ancora la stessa dir              
if os.name == "posix":
    v_global_work_dir = os.path.expanduser('~//.local//share//MSql//')
else:
    v_global_work_dir = os.path.expanduser('~\\AppData\\Local\\MSql\\')
# Lista di parole aggiuntive al lexer che evidenzia le parole nell'editor
v_global_my_lexer_keywords = []
# Oggetto che carica le preferenze tramite l'apposita classe (notare che già a questa istruzione le preferenze vengono caricate!)
o_global_preferences = preferences_class(v_global_work_dir + 'MSql.ini', v_global_work_dir + 'MSql_connections.ini')
# Contiene le coordinate della main window
v_global_main_geometry = object
# Contiene il tempo di esecuzione ultima istruzione
v_global_exec_time = 0
# Contiene il colore personalizzato del server
v_global_color = '#ffffff'
v_global_background = 'black'
# Indica se la connessione va evidenziata
v_global_emphasis = False
# Indica che sui comandi sql di CREATE, va richiesta una conferma
v_global_create_confirm = False
# Indica il font di ascii art selezionato
v_global_font_ascii_art = ''

def nome_file_backup(p_nome_file):
    """
       Calcola il nome file di backup
       Il nome riporta la pathname della dir di backup il PID (process ID) di MSql attualmente in esecuzione e il nome del file di origine
       Siccome non sono ammessi nel nome del file i caratteri : slash backslash, vengono sostituiti usando il punto
    """
    p_nome_file = p_nome_file.replace('/', '..')
    p_nome_file = p_nome_file.replace('\\', '..')
    p_nome_file = p_nome_file.replace(':','...')
    p_nome_file = v_global_work_dir + 'backup\\' + 'PID-'+ str(os.getpid()) + 'PID-' + p_nome_file

    return p_nome_file

def salvataggio_editor(p_save_as, p_nome, p_testo, p_codifica_utf8):
    """
        Salvataggio di p_testo dentro il file p_nome        
        Se p_save_as è True oppure il titolo dell'editor inizia con "!" --> viene richiesto di salvarlo come nuovo file
    """
    global o_global_preferences

    # salvo in var temporanea il nome ricevuto in input (lo userò per eliminare il vecchio backup)
    p_nome_originario = p_nome

    # se il primo carattere del titolo inizia con un punto esclamativo, significa che il file è stato creato partendo dall'object navigator
    # e quindi l'operazione di salva deve chiedere il nome del file e la posizione dove salvare
    if p_nome[0:1] == '!':
        p_save_as = True
        p_nome = p_nome.lstrip('!')

    # se indicato il save as, oppure il file è nuovo e non è mai stato salvato --> richiedo un nuovo nome di file    
    if p_save_as or (not p_save_as and p_nome[0:8]=='Untitled'):
        # la dir di default è quella richiesta dall'utente o la Documenti        
        if o_global_preferences.save_dir == '':
            v_default_save_dir = QDir.homePath() + "\\Documents\\"
        else:
            v_default_save_dir = o_global_preferences.save_dir

        # propongo un nuovo nome di file dato dalla dir di default + il titolo ricevuto in input
        v_file_save_as = v_default_save_dir + '\\' + p_nome        
     
        p_nome = QFileDialog.getSaveFileName(None, "Save a SQL file",v_file_save_as,"MSql files (*.msql);;SQL files (*.sql *.pls *.plb *.trg);;All files (*.*)") [0]                                  
        if not p_nome:
            message_error(QCoreApplication.translate('Save','Error saving'))
            return 'ko'
        # se nel nome del file non è presente un suffisso --> imposto .msql            
        if p_nome.find('.') == -1:
            p_nome += '.msql'
        # reimposto la dir di default in modo che in questa sessione del programma rimanga quella che l'utente ha scelto per salvare il file
        o_global_preferences.save_dir = os.path.split( p_nome )[0]

    # procedo con il salvataggio
    try:
        if p_codifica_utf8:
            # scrittura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                                            
            v_file = open(p_nome,'w',encoding='utf-8', newline='')
        else:
            # scrittura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
            v_file = open(p_nome,'w', newline='')
        v_file.write(p_testo)
        v_file.close()            
        # procedo con il cancellare eventuale file di backup precedente (si ripartirà con un nuovo salvataggio che conterrà il nuovo nome di file)                
        v_nome_file_backup = nome_file_backup(p_nome_originario)                
        if os.path.exists(v_nome_file_backup):
            os.remove(v_nome_file_backup)		
            print('Remove old backup --> ' + v_nome_file_backup)
        # esco con tutto ok
        return 'ok', p_nome
    except Exception as err:
        # esco con errore
        message_error(QCoreApplication.translate('Save','Error to write the file:') + ' ' + str(err))
        return 'ko', None

def titolo_window(p_titolo_file):
    """
       Partendo da p_titolo_file restituisce solo la parte di nome file da mettere come titolo della window
    """                       
    v_solo_nome_file = os.path.split(p_titolo_file)[1]
    v_solo_nome_file_senza_suffisso = os.path.splitext(v_solo_nome_file)[0]

    return v_solo_nome_file_senza_suffisso

class classChangeLog(QWidget):
    """
       Visualizza in una window specifica, il file di changelog
    """
    def __init__(self,p_window_padre):
        super().__init__()
        self.setWindowTitle("MSql-Changelog")
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(v_icon)
        self.setGeometry(0, 0, 600, 500)

        layout = QVBoxLayout()
        # creo un text edit di sola lettura dove visualizzo il contenuto del changelog
        self.text_edit = QTextEdit()
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setReadOnly(True)  
        # imposto font a larghezza fissa per migliore visualizzazione
        v_font = QFont()
        v_font.setFamily("Courier New")
        v_font.setPointSize(10)
        self.text_edit.setFont(v_font)

        # se sto eseguendo il programma da pyinstaller, vado in apposita cartella
        v_nome_file = "help/changelog.txt"
        if getattr(sys, 'frozen', False): 
            v_nome_file = "_internal/" + v_nome_file               

        # leggo il file di changelog
        try:            
            with open(v_nome_file, "r", encoding='UTF-8') as file:
                self.text_edit.setText(file.read())
        except:
            pass

        # imposto il layout
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        # centro la window rispetto alla window padre
        centra_window_figlia(p_window_padre, self)

class classFontArtViewer(QWidget):
    """
       Visualizza in una window specifica, elenco dei font che mette a disposizione la libreria ascii art 
    """
    def __init__(self, p_window_padre):
        global v_global_font_ascii_art
        global o_global_preferences

        super().__init__()        
        self.setWindowTitle("Ascii art Font Selector")
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(v_icon)
        self.setGeometry(0, 0, 400, 450)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        # creo la lista dei font dove il primo elemento è il vuoto che corrisponde al default
        v_lista = []
        v_lista.append('')
        for i in FONT_NAMES:            
            v_lista.append(i)
        self.list_widget.addItems(v_lista)
        layout.addWidget(self.list_widget)        
            
        # Label informativa
        info_label = QLabel(QCoreApplication.translate('MSql_win1',"Double-click to select the font"))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        layout.addWidget(info_label)
        
        # Area di anteprima dove il font è lo stesso impostato come preferenza dell'editor
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)        
        v_split = o_global_preferences.font_editor.split(',')                        
        v_font = QFont(str(v_split[0]),int(v_split[1]))
        self.preview.setFont(v_font)  
        layout.addWidget(self.preview)

        # Compongo il layout
        self.setLayout(layout)

        # mi posiziono sul font attualmente attivo 
        if v_global_font_ascii_art != '' and v_global_font_ascii_art in FONT_NAMES:
            index = self.list_widget.findItems(v_global_font_ascii_art, Qt.MatchFlag.MatchExactly)
            if index:
                self.list_widget.setCurrentItem(index[0])
                self.list_widget.scrollToItem(index[0])

        # Evento click per anteprima e doppio click per la scelta
        self.list_widget.currentItemChanged.connect(lambda item: self.update_preview(item.text()))
        self.list_widget.itemDoubleClicked.connect(self.show_font_name)

        # centro la window rispetto alla window padre
        centra_window_figlia(p_window_padre, self)

    def update_preview(self, font_name):        
        """
           Visualizza anteprima del font
        """
        art_text = text2art("art", font=font_name)
        self.preview.setPlainText(art_text)
        
    def show_font_name(self, item):
        """
            Il font selezionato viene caricato nella variabile globale
        """
        global v_global_font_ascii_art

        v_global_font_ascii_art = item.text()        
        self.close()

class classSingleInstanceManager(QObject):
    """
       Classe che avvia un server che controlla all'avvio di MSql, se ci sono altre istanze di MSql in esecuzione
       Questa classe è utilizzata per permettere di aprire un file, facendo doppio click da desktop, nella stessa
       istanza già in esecuzione di MSql. Il codice di chiamata è tutto concentrato nella sezione di Start.
    """
    # Adesso emettiamo un singolo percorso (str), non più lista
    messageReceived = pyqtSignal(str)    

    def __init__(self, server_name: str):
        super().__init__()
        self.server_name = server_name
        self.server = None

    def try_send_to_running_instance(self, file_path: str) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(200):
            socket.abort()
            return False

        try:
            # Invia il percorso come stringa UTF-8
            data = file_path.encode("utf-8")
            socket.write(data)
            socket.flush()
            socket.waitForBytesWritten(200)
        finally:
            socket.disconnectFromServer()
            socket.close()

        return True

    def start_listening(self) -> bool:
        QLocalServer.removeServer(self.server_name)
        self.server = QLocalServer(self)
        if not self.server.listen(self.server_name):
            return False
        self.server.newConnection.connect(self._handle_new_connection)
        return True

    def _handle_new_connection(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            sock.readyRead.connect(lambda s=sock: self._read_message(s))

    def _read_message(self, socket: QLocalSocket):
        raw = socket.readAll().data()
        try:
            # Decodifica semplice del path
            path = raw.decode("utf-8")            
            self.messageReceived.emit(path)
        except Exception as e:
            print(f"Errore da clasInstanceManager gestore SIM! Messaggio non valido: {e}")
        finally:
            socket.disconnectFromServer()
            socket.close()

class MyFileExtensionFilterProxyModel(QSortFilterProxyModel):
    """
       Filtra i file mostrati nel file system tree view:
        - Esclude file e cartelle nascoste
        - Mostra tutte le cartelle visibili per navigare
        - Mostra solo i file che NON hanno estensioni vietate
        - (Opzionale) Applica un filtro regex sui nomi dei file
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.not_allowed_extensions = ['.dat', '.rnd', '.dll', '.bat', '.exe', '.rhk']
        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        file_info = QFileInfo(model.filePath(index))

        # Escludi file e cartelle nascoste
        if file_info.isHidden() or file_info.fileName().startswith('.'):
            return False

        # Le cartelle visibili devono sempre comparire per la navigazione
        if file_info.isDir():
            return True

        # Escludi file con estensioni vietate
        file_name = file_info.fileName().lower()
        if any(file_name.endswith(ext) for ext in self.not_allowed_extensions):
            return False

        # Applica filtro regex (solo ai file)
        regex = self.filterRegularExpression()
        if regex and regex.pattern():
            return regex.match(file_name).hasMatch()

        return True

#
#  __  __    _    ___ _   _  __        _____ _   _ ____   _____        __
# |  \/  |  / \  |_ _| \ | | \ \      / /_ _| \ | |  _ \ / _ \ \      / /
# | |\/| | / _ \  | ||  \| |  \ \ /\ / / | ||  \| | | | | | | \ \ /\ / / 
# | |  | |/ ___ \ | || |\  |   \ V  V /  | || |\  | |_| | |_| |\ V  V /  
# |_|  |_/_/   \_\___|_| \_|    \_/\_/  |___|_| \_|____/ \___/  \_/\_/   
#                                                                       
# Classe principale       
class MSql_win1_class(QMainWindow, Ui_MSql_win1):    
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
        # creo oggetto settings per salvare posizione della window e delle dock
        self.settings = QSettings("Marco Valaguzza", "MSql")
        # carico interfaccia
        self.setupUi(self)        
        
        # attivo il drag&drop (viene gestito per quando da esplora risorse si trascina un file sull'app)
        self.setAcceptDrops(True)        

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
                v_qaction = QAction()
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
                v_qaction = QAction()
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
        # Da notare come l'allineamento a destra sia effettuato tramite un addPermanentWidget e a sinistra con il addWidget
        ###                                        
        # Bottone con icona per aprire la dock del file system
        self.fs_button = QPushButton()
        self.fs_button.setIcon(QIcon("icons:folder.png")) 
        self.fs_button.setIconSize(QSize(8,8))
        self.fs_button.setToolTip(QCoreApplication.translate('MSql_win1','Open file system dock'))        
        self.fs_button.clicked.connect(self.slot_mostra_file_system_dock)
        self.statusBar.addWidget(self.fs_button)  
        # Informazioni sul tempo di esecuzione dell'ultima istruzione
        self.l_exec_time = QLabel(QCoreApplication.translate('MSql_win1','Last execution time:'))
        self.l_exec_time.setFrameStyle(QFrame.Shape.NoFrame)        
        self.statusBar.addWidget(self.l_exec_time)                                
        # Informazioni sulla connessione
        self.l_connection = QLabel(QCoreApplication.translate('MSql_win1','Connection:'))
        self.l_connection.setFrameStyle(QFrame.Shape.NoFrame)
        self.l_connection.setStyleSheet('color: black;')
        self.statusBar.addWidget(self.l_connection)                                        
        # Coordinate cursore dell'editor di testo
        self.l_cursor_pos = QLabel()
        self.l_cursor_pos.setFrameStyle(QFrame.Shape.NoFrame)
        self.statusBar.addPermanentWidget(self.l_cursor_pos)                
        self.l_cursor_pos.setText("Ln: 1  Col: 1")
        # Numero totale di righe di testo
        self.l_num_righe_e_char = QLabel()
        self.l_num_righe_e_char.setFrameStyle(QFrame.Shape.NoFrame)
        self.statusBar.addPermanentWidget(self.l_num_righe_e_char)                
        self.l_num_righe_e_char.setText(QCoreApplication.translate('MSql_win1','Lines:') + ' 0 , ' + QCoreApplication.translate('MSql_win1','Length:') + ' 0')        
        # Stato attivazione inserito di testo o overwrite
        self.l_overwrite_enabled = QLabel("INS")
        self.l_overwrite_enabled.setFrameStyle(QFrame.Shape.NoFrame)
        self.statusBar.addPermanentWidget(self.l_overwrite_enabled)
        # Stato attivazione codifica utf-8
        self.l_utf8_enabled = QLabel()
        self.l_utf8_enabled.setFrameStyle(QFrame.Shape.NoFrame)
        self.statusBar.addPermanentWidget(self.l_utf8_enabled)        
        # Stato end of line
        self.l_eol = QLabel()
        self.l_eol.setFrameStyle(QFrame.Shape.NoFrame)
        self.statusBar.addPermanentWidget(self.l_eol)                
        # Indicatore editabilità
        self.l_tabella_editabile = QLabel(QCoreApplication.translate('MSql_win1','Editable table: Disabled'))
        self.l_tabella_editabile.setFrameStyle(QFrame.Shape.NoFrame)
        self.l_tabella_editabile.setStyleSheet('color: black;')
        self.statusBar.addPermanentWidget(self.l_tabella_editabile)      

        ###
        # Var per la gestione dei files recenti
        ###
        self.elenco_file_recenti = []            
        self.elenco_file_recenti_action = []

        ###
        # Var per la gestione degli editor
        ###

        # var che indica il numero di window2-editor 
        self.v_num_window2 = 0                
        # definisco la lista che contiene il link a tutti gli oggetti window2 degli editor aperti
        self.o_lst_window2 = []
        # per smistare i segnali che arrivano dal menù che non è collegato con le subwindow, utilizzo
        # un apposito connettore
        self.menuBar.triggered[QAction].connect(self.smistamento_voci_menu)        

        ###        
        # eseguo la connessione automatica di default (solo se richiesta tramite il default sulle preferenze di server e user)
        ###
        self.e_server_name = ''
        self.e_user_name = ''
        self.e_user_proxy = ''
        self.e_password = ''
        self.e_user_mode = 'Normal'        
        for rec in o_global_preferences.elenco_server:                
                try:
                    if rec[3] == '1':                                            
                        self.e_server_name = rec[1]
                except:
                    pass
        for rec in o_global_preferences.elenco_user:                
                try:
                    if rec[3] == '1':                                            
                        self.e_user_name = rec[1]
                        self.e_password = rec[2] 
                        self.e_user_proxy = rec[4]
                except:
                    pass

        # creo il modello che conterrà elenco degli schemi
        self.schema_model = QStringListModel()        
        self.current_schema = ''        

        # se trovato server e user di default --> eseguo la connessione        
        if self.e_server_name != '' and self.e_user_name != '':                
            self.slot_connetti()           

        ###
        # Definizione della struttura per gestione elenco oggetti DB (object navigator)       
        ###
        self.oggetti_db_lista = QStandardItemModel()        
        self.oggetti_db_elenco.setModel(self.oggetti_db_lista)
        # attivo la gestione del tasto destro e relativo richiamo menu popup
        self.oggetti_db_elenco.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) 
        self.oggetti_db_elenco.customContextMenuRequested.connect(self.slot_popup_menu_db_elenco)             
        # per default carico l'elenco di tutte le tabelle (selezionando la voce Tables=1 nell'elenco)
        self.oggetti_db_scelta.setCurrentIndex(1)
        # per object viewer e nel caso di package, riporta la struttura delle procedure-funzioni che il package contiene
        # per la struttura di questa var fare riferimento alla funzione estrai_procedure_function che si trova in utilita_testo.py
        self.oggetti_db_lista_proc_func = object       
        self.v_nome_oggetto = ''        
        self.v_tipo_oggetto = ''        
        self.v_nome_foglia = ''
        self.v_tipo_foglia = ''
        # attivo la gestione del tasto destro e relativo richiamo menu popup
        self.db_oggetto_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.db_oggetto_tree.customContextMenuRequested.connect(self.slot_popup_menu_oggetto_tree)
        # creo le variabili che serviranno come appoggio al menu popup (punto in cui il popup è stato attivato)
        self.v_popup_menu_zone = ''     
 
        ###
        # Imposto default in base alle preferenze (setto anche le opzioni sulle voci di menu)
        ###                        
        self.actionMake_table_editable.setChecked(o_global_preferences.editable)
        self.slot_editable()
        self.actionShow_end_of_line.setChecked(o_global_preferences.end_of_line)
        self.slot_end_of_file()
        self.actionAutoColumnResize.setChecked(o_global_preferences.auto_column_resize)        
        self.actionAuto_clear_output.setChecked(o_global_preferences.auto_clear_output)        
        
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
            v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(p_nome_file_da_caricare)        
            v_azione = QAction()
            v_azione.setText('Open_db_obj')            
            self.smistamento_voci_menu(v_azione, v_titolo, v_contenuto_file, v_codifica_utf8)        
        ###        
        # Altrimenti apro una nuova finestra di editor simulando il segnale che scatta quando utente sceglie "New"
        # Attenzione! L'apertura dell'editor è stata posta alla fine di tutto il procedimento di carico del main
        #             in quanto non veniva caricata elenco autocompletamento dell'editor. La cosa strana è che se
        #             dopo l'apertura si apriva un nuovo file, da quel momento l'autocompletamento partiva.
        ### 
        else:
            # il nuovo editor viene aperto solo in base a specifica preferenza
            if o_global_preferences.open_new_editor:
                v_azione = QAction()
                v_azione.setText(QCoreApplication.translate('MSql_win1','New'))
                self.smistamento_voci_menu(v_azione)      

        ###
        # Se è presente il file dei termini di dizionario, controllo se più vecchio di 2 settimane e avverto che andrebbe rigenerato
        ###        
        if o_global_preferences.refresh_dictionary > 0 and os.path.isfile(v_global_work_dir + 'MSql_autocompletion.ini'):  
            v_data_ultima_modifica = datetime.datetime.fromtimestamp(os.stat(v_global_work_dir + 'MSql_autocompletion.ini').st_mtime)
            if (datetime.datetime.now() - v_data_ultima_modifica) > datetime.timedelta(days=o_global_preferences.refresh_dictionary):
                message_info(QCoreApplication.translate('MSql_win1',"The dictionary is more than") + ' ' + str(o_global_preferences.refresh_dictionary) + QCoreApplication.translate('MSql_win1'," days old!")  + chr(10) + QCoreApplication.translate('MSql_win1',"Remember to regenerate it!") + chr(10) + QCoreApplication.translate('MSql_win1',"See the menu Tools/Autocomplete dictionary ;-)"))                    

        ###
        # Controllo se ci sono dei file di backup (alias snapshoot) aperti da sessioni interrotte e chiedo all'utente se li vuole ripristinare   
        ###
        if os.path.exists(v_global_work_dir + 'backup\\'):
            for v_nome_file_backup in os.listdir(v_global_work_dir + 'backup\\'):
                # estraggo dal nome del file il PID di processo
                v_pid = v_nome_file_backup.split('PID-')[1]
                # controllo se questo PID corrisponde ad un processo ancora attivo (vuol dire che lo snapshoot è creato da un'altra sessione di MSql ancora attiva!)
                if not psutil.pid_exists(int(v_pid)):  
                    # ricavo il nome del file originario
                    v_split = v_pid = v_nome_file_backup.split('PID-')                
                    v_nome_originario = v_split[2] 
                    v_nome_originario = v_nome_originario.replace('...',':').replace('..','/')                    
                    # chiedo se procedere o meno con il ripristino
                    if message_question_yes_no(QCoreApplication.translate('MSql_win1','Found file') + chr(10) + v_nome_originario + chr(10) + QCoreApplication.translate('MSql_win1','from interrupted session! Do you want to restore it?')) == 'Yes':            
                        # apro il file di backup
                        v_titolo_backup, v_contenuto_file_backup, v_codifica_utf8_backup = self.openfile(v_global_work_dir + 'backup\\' + v_nome_file_backup)                                                        
                        # richiamo l'azione di apertura dell'editor con il file di backup, mettendo nel titolo la parola RESTORED. Il file andrà salvato manualmente dall'utente. Ho usato questo approccio perché per me è più sicuro!
                        v_azione = QAction()
                        v_azione.setText('Open_db_obj')                                    
                        self.smistamento_voci_menu(v_azione, titolo_window(v_nome_originario) + ' RESTORED', v_contenuto_file_backup, v_codifica_utf8_backup)                        
                        # prendo la window appena creata che è l'ultima nella lista 
                        o_MSql_win2 = self.o_lst_window2[-1]
                        # e coloro lo sfondo di rosso per far capire che si tratta di un file ripristinato
                        o_MSql_win2.setStyleSheet("background-color: red;")
                    # il file di backup viene eliminato (sia che utente abbia risposto si che abbia risposto no!)                   
                    os.remove(v_global_work_dir + 'backup\\' + v_nome_file_backup)

        ###
        # imposto il timer che permette all'object navigator di attivare la ricerca automatica dopo 0,8 secondi dalla digitazione del testo
        ###
        self.object_navigator_search_timer = QTimer(self)
        self.object_navigator_search_timer.setSingleShot(True)
        self.object_navigator_search_timer.timeout.connect(self.slot_oggetti_db_scelta)

        ###
        # var per gestire la calcolatrice
        ###
        self.win_calculator = None

    def dragEnterEvent(self, event):
        """
           Sovrascrivo la funzione nativa e intercetto l'evento drag che proviene dall'esterno dell'app (es. da esplora risorse si trascina in MSql un file)
        """        
        # se il drag contiene un nome di file, allora lo accetto! Se non lo accettassi il conseguente drop non produrrebbe risultato
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
           Sovrascrivo la funzione nativa e intercetto l'evento di drop; se è stato accettato il nome di un file, apro un nuovo editor con il nome di quel file
        """
        # se il drop contiene un nome di file, allora lo accetto e apro un nuovo editor con quel file         
        for url in event.mimeData().urls():
            if url.isLocalFile():
                v_filepath = url.toLocalFile()
                if v_filepath is not None:
                    # apro un file            
                    v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(v_filepath)        
                    v_azione = QAction()
                    v_azione.setText('Open_db_obj')            
                    self.smistamento_voci_menu(v_azione, v_titolo, v_contenuto_file, v_codifica_utf8)        
    
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
    
    def smistamento_voci_menu(self, p_slot, p_oggetto_titolo_db=None, p_oggetto_testo_db=None, p_oggetto_codifica_utf8_db=None):
        """
            Contrariamente al solito, le voci di menù non sono pilotate da qtdesigner ma direttamente
            dal connettore al menu che riporta a questa funzione che poi si occupa di fare lo smistamento.
            Ci sono voci di menù che sono "generiche", altre invece devono agire sul contenuto della finestra
            attiva. Per questo è stata creata una lista che contiene tutti gli oggetti aperti e quindi,
            di volta in volta viene ricercata la window-oggetto attiva, ed elaborata la voce di menu direttamente
            per quella window-oggetto.
            Parametri: p_slot = Oggetto di tipo event che indica l'evento 
                       p_oggetto_titolo_db = Serve solo quando si vuole aprire un oggetto di testo db (titolo della window)
                       p_oggetto_testo_db = Serve solo quando si vuole aprire un oggetto di testo db (contenuto dell'editor)
                       p_oggetto_codifica_utf8_db = Serve solo quando si vuole aprire un oggetto di testo db (se T=UTF-8 dell'editor)
            Nota! In QtDesigner alcune voci di menu hanno il shortcut context attivo come WindowShortcut e altre come WidgetShortcut
                  La modalità WidgetShortcut va definita solo per fare in modo che a menu sia presente la scritta della shortcut ma poi lasci 
                  a qscintilla la gestione del medesimo (perché è un altro widget)
        """
        global o_global_preferences                
        global v_global_main_geometry
        
        #print('Dato di menù --> ' + str(p_slot.data()))                    
        #print('Nome menu    --> ' + p_slot.objectName())
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
                    self.e_user_proxy = rec[4]
                    self.e_user_mode = 'Normal'                    
            self.slot_connetti()            
        # Connessione a un data base specifico richiedendo tutti i parametri singolarmente
        elif p_slot.objectName() == 'actionConnect':
            self.richiesta_connessione_specifica()        
        # Disconnessione al database corrente
        elif p_slot.objectName() == 'actionDisconnect':
            self.slot_disconnect()        
        # Esplora i link di database
        elif p_slot.objectName() == 'actionExplore_database_link':
            self.slot_explore_database_link()
        # Apertura di un nuovo editor o di un file recente o di una chiamata esterna da parte di altra istanza MSql
        elif p_slot.text() in (QCoreApplication.translate('MSql_win1','New'),QCoreApplication.translate('MSql_win1','Open'),QCoreApplication.translate('MSql_win1','Open_db_obj')) or p_slot.text() in ('OPEN_FROM_SIM') or str(p_slot.data()) == 'FILE_RECENTI':            
            # se richiesto un file recente
            if str(p_slot.data()) == 'FILE_RECENTI':
                # apro il file richiesto
                v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(p_slot.text())
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto Open...
            elif p_slot.text() == QCoreApplication.translate('MSql_win1','Open'):
                # apro un file tramite dialog box
                v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(None)                
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto Open da altra istanza MSql...il nome del file da aprire è nella proprietà objectname dell'azione ricevuta in input
            elif p_slot.text() in 'OPEN_FROM_SIM':
                # apro il file il cui nome trovo nell'object name (v. funzione slot_open_file_from_SIM dove è stato caricato)
                v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(p_slot.objectName())                
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto Open_db_obj...
            elif p_slot.text() == QCoreApplication.translate('MSql_win1','Open_db_obj'):
                # apro un file
                v_titolo = p_oggetto_titolo_db
                v_contenuto_file = p_oggetto_testo_db 
                v_codifica_utf8 = p_oggetto_codifica_utf8_db
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto New, aumento il numeratore delle window
            else:
                self.v_num_window2 += 1
                v_titolo = 'Untitled' + str(self.v_num_window2)
                v_contenuto_file = None
                v_codifica_utf8 = True
            # creo una nuovo oggetto editor (gli passo il titolo, eventuale contenuto del file e relativa codifica e gli oggetti della statusbar)
            o_MSql_win2 = MSql_win2_class(v_titolo, 
                                          v_contenuto_file, 
                                          v_codifica_utf8,
                                          self)
            # l'oggetto editor lo salvo all'interno di una lista in modo sia reperibile quando necessario
            self.o_lst_window2.append(o_MSql_win2)        
            # collego l'oggetto editor ad una nuova finestra del gestore mdi e la visualizzo, massimizzandola (imposto icona vuota!)
            # da notare come il nome di file completo di fatto viaggia all'interno del nome degli oggetti
            sub_window = self.mdiArea.addSubWindow(o_MSql_win2)                  
            sub_window.setObjectName(o_MSql_win2.objectName())
            sub_window.setWindowIcon(QIcon("icons:database.png"))                              
            sub_window.show()  
            sub_window.showMaximized()  
        # Gestione preferenze
        elif p_slot.objectName() == 'actionPreferences':
            self.slot_preferences()
        # Rendo l'output dell'sql editabile
        elif p_slot.objectName() == 'actionMake_table_editable':
            if self.actionMake_table_editable.isChecked():
                o_global_preferences.editable = True
            else:                
                o_global_preferences.editable = False
            # aggiorno status bar e aggiorno oggetti
            self.slot_editable()
        # Uscita dal programma (invoco l'evento di chiusura della main window)
        elif p_slot.objectName() == 'actionExit':
            v_event_close = QCloseEvent()
            self.closeEvent(v_event_close)        
        # Riorganizzo le window in modalità cascata
        elif p_slot.objectName() == 'actionCascade':
            self.mdiArea.setViewMode(QMdiArea.ViewMode.SubWindowView)
            self.mdiArea.cascadeSubWindows()
        # Riorganizzo le window in modalità piastrelle
        elif p_slot.objectName() == 'actionTile':
            self.mdiArea.setViewMode(QMdiArea.ViewMode.SubWindowView)
            self.mdiArea.tileSubWindows()           
        # Riorganizzo le window in modalità tab
        elif p_slot.objectName() == 'actionTabbed':
            self.mdiArea.setViewMode(QMdiArea.ViewMode.TabbedView)            
        # Apro file di help (help che è stato costruito tramite la libreria Sphinx!)
        elif p_slot.objectName() == 'actionHelp':                          
            if getattr(sys, 'frozen', False): 
                os.system("start _internal/help/MSql_help.odt")
            else:
                os.system("start help/MSql_help.odt")
        # Apro file di della cronologia delle modifiche
        elif p_slot.objectName() == 'actionChange_log':                                      
            self.o_changelog = classChangeLog(self)
            self.o_changelog.show()
        # Visualizzo program info
        elif p_slot.objectName() == 'actionProgram_info':            
            self.slot_info()
        # visualizza l'objects navigator
        elif p_slot.objectName() == 'actionObjects_Navigator':
            self.dockWidget.show()
        # visualizza l'object viewer
        elif p_slot.objectName() == 'actionObject_Viewer':
            self.dockWidget_2.show()
        # visualizza il file system
        elif p_slot.objectName() == 'actionFile_system':
            self.slot_mostra_file_system_dock()
        # visualizza l'history
        elif p_slot.objectName() == 'actionHistory':
            self.slot_history()
        # visualizza la gestione degli sql preferiti
        elif p_slot.objectName() == 'actionMy_preferred_SQL':
            self.slot_preferred_sql()
        # Indico che l'output sql ha le colonne con larghezza auto-adattabile
        elif p_slot.objectName() == 'actionAutoColumnResize':
            self.slot_menu_auto_column_resize()
        # Attivo la comparazione tra i due ultimi file in elenco
        elif p_slot.objectName() == 'actionCompare_last_two_text_editor':
            self.slot_compare_last_two_text_editor()
        # Creazione del dizionario termini per autocompletamento dell'editor
        elif p_slot.objectName() == 'actionCreate_autocompletation_dictionary':
            self.crea_dizionario_per_autocompletamento()
        # Import-Export Oracle to SQLite
        elif p_slot.objectName() == 'actionOracle_to_SQLite':
            self.slot_import_export_oracle_to_sqlite()
        # Import-Export SQlite to Excel
        elif p_slot.objectName() == 'actionSQLite_to_Excel':
            self.slot_import_export_sqlite_to_excel()
        # Import-Export Excel to Oracle
        elif p_slot.objectName() == 'actionExcel_to_Oracle':
            self.slot_import_export_excel_to_oracle()
        # Import-Export SQLite to Oracle
        elif p_slot.objectName() == 'actionSQLite_to_Oracle':
            self.slot_import_export_sqlite_to_oracle()
        # SQLite viewer
        elif p_slot.objectName() == 'actionSQLite_viewer':
            self.slot_sqlite_viewer()
        # Calcolatrice
        elif p_slot.objectName() == 'actionCalculator':
            self.slot_calculator()
        # Modalità full screen (attiva/disattiva)
        elif p_slot.objectName() == 'actionFull_screen':
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
                
        # Queste voci di menu che agiscono sull'oggetto editor, sono valide solo se l'oggetto è attivo
        if o_MSql_win2 is not None:
            # Salvataggio del file
            if p_slot.objectName() == 'actionSave':
                v_ok, v_nome_file = salvataggio_editor(False, o_MSql_win2.objectName(), o_MSql_win2.e_sql.text(), o_MSql_win2.setting_utf8)
                if v_ok == 'ok':
                    o_MSql_win2.v_testo_modificato = False
                    o_MSql_win2.setObjectName(v_nome_file)
                    o_MSql_win2.setWindowTitle(titolo_window(v_nome_file))
                    self.aggiorna_elenco_file_recenti(v_nome_file)
                    self.window_attiva.setObjectName(v_nome_file) # notare come il nome della window va forzato anche sulla window attiva
            # Salvataggio del file come... (semplicemente non gli passo il titolo)
            elif p_slot.objectName() == 'actionSave_as':
                v_ok, v_nome_file = salvataggio_editor(True, o_MSql_win2.objectName(), o_MSql_win2.e_sql.text(), o_MSql_win2.setting_utf8)
                if v_ok == 'ok':                    
                    o_MSql_win2.v_testo_modificato = False                    
                    o_MSql_win2.setObjectName(v_nome_file)                    
                    o_MSql_win2.setWindowTitle(titolo_window(v_nome_file))
                    self.aggiorna_elenco_file_recenti(v_nome_file)                    
                    self.window_attiva.setObjectName(v_nome_file) # notare come il nome della window va forzato anche sulla window attiva
            # Chiusura dell'editor
            elif p_slot.objectName() == 'actionClose':
                self.mdiArea.closeActiveSubWindow()
            # Chiusura di tutti gli editor aperti 
            elif p_slot.objectName() == 'actionClose_all':
                self.mdiArea.closeAllSubWindows()
            # Visualizza il carattere di end of line, ritorno a capo
            elif p_slot.objectName() == 'actionShow_end_of_line':
                # riporto la preferenza di menu dentro l'oggetto delle preferenze 
                if self.actionShow_end_of_line.isChecked():
                    o_global_preferences.end_of_line = True
                else:
                    o_global_preferences.end_of_line = False
                # attivo la scelta su tutti gli editor aperti
                self.slot_end_of_file()
            # Ricerca di testo
            elif p_slot.objectName() == 'actionFind':
                v_global_main_geometry = self.frameGeometry()                                
                o_MSql_win2.slot_find()
            # Sostituzione di testo
            elif p_slot.objectName() == 'actionFind_and_Replace':
                v_global_main_geometry = self.frameGeometry()
                o_MSql_win2.slot_find_e_replace()
            # Mappa delle procedure/funzioni
            elif p_slot.objectName() == 'actionMaps_procedure_function':
                v_global_main_geometry = self.frameGeometry()
                o_MSql_win2.slot_map()
            # Mini mappa attiva/disattiva
            elif p_slot.objectName() == 'actionMini_map':                
                o_MSql_win2.slot_mini_map_visible()
            # Selezione del testo rettangolare
            elif p_slot.objectName() == 'actionRect_selection':                
                message_info(QCoreApplication.translate('MSql_win1','There are 2 ways to switch to rectangular selection mode') + chr(10) + chr(10) + QCoreApplication.translate('MSql_win1','1. (Keyboard and mouse) Hold down ALT while left clicking, then dragging') + chr(10) + chr(10) + QCoreApplication.translate('MSql_win1','2. (Keyboard only) Hold down ALT+Shift while using the arrow keys'))                                
            # Estrazione della chiave primaria
            elif p_slot.objectName() == 'actionExtract_primary_key':                
                message_info(QCoreApplication.translate('MSql_win1','To extract the primary key, position yourself on a table name and press CTRL+K. Otherwise, to join two tables, write the two tables separated by commas, select the text and press CTRL+K.'))                                
            # Ricerca prossimo ='
            elif p_slot.objectName() == 'actionNextF4':                
                message_info(QCoreApplication.translate('MSql_win1',"To search next = press F4"))                                
            elif p_slot.objectName() == 'actionAdd':                
                message_info(QCoreApplication.translate('MSql_win1','Click on the left margins of the editor and the bookmark will be highlighted with a green circle.'))                                
            elif p_slot.objectName() == 'actionRemove':                
                message_info(QCoreApplication.translate('MSql_win1','Click on the left margins of the editor, select a bookmark, and hold down the CTRL key.'))                                
            elif p_slot.objectName() == 'actionSearchNext':                
                message_info(QCoreApplication.translate('MSql_win1','With CTRL+B you can jump from one bookmark to another! When you reach the end, the search starts again from the beginning of the text.'))                                
            # Commenta il testo selezionato
            elif p_slot.objectName() == 'actionComment_selection':                
                o_MSql_win2.slot_commenta()
            # Decommenta il testo selezionato
            elif p_slot.objectName() == 'actionUncomment_selection':                
                o_MSql_win2.slot_scommenta()
            # Creazione di documentazione da intestazione di funzione-procedura PL-SQL
            elif p_slot.objectName() == 'actionComment_from_function':
                o_MSql_win2.slot_comment_from_function()
            # Uppercase del testo selezionato
            elif p_slot.objectName() == 'actionUppercase_current_selection':                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_UPPERCASE)
            # Lowercase del testo selezionato
            elif p_slot.objectName() == 'actionLowercase':                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_LOWERCASE)
            elif p_slot.objectName() == 'actionHighlight_selection':
                o_MSql_win2.slot_highligth_selection()            
            # Indenta la riga alla posizione del cursore
            elif p_slot.objectName() == 'actionIndent_to_cursor':
                o_MSql_win2.slot_indent_to_cursor()            
            # Prende il testo selezionato e lo trasforma in ASCII art testo
            elif p_slot.objectName() == 'actionText_to_Ascii_Art':
                o_MSql_win2.slot_text_to_ascii_art()
            # Apro la window per la selezione del font da utilizzare con ASCII art testo
            elif p_slot.objectName() == 'actionSet_font_Ascii_Art':                                
                self.o_fontartviewer = classFontArtViewer(self)
                self.o_fontartviewer.show()      
            # Apro la window con la gestione delle funzioni di testo
            elif p_slot.objectName() == 'actionText_functions':
                self.slot_text_functions(o_MSql_win2.e_sql.selectedText())
            # Compressione di tutti i livelli
            elif p_slot.objectName() == 'actionFold_All':
                o_MSql_win2.e_sql.foldAll()
            # Zoom In del testo
            elif p_slot.objectName() == 'actionZoom_In':
                o_MSql_win2.e_sql.zoomIn()
            # Zoom Out del testo
            elif p_slot.objectName() == 'actionZoom_Out':
                o_MSql_win2.e_sql.zoomOut()
            # Annulla il testo
            elif p_slot.objectName() == 'actionUndo':
                o_MSql_win2.e_sql.undo()
            # Ripristina il testo
            elif p_slot.objectName() == 'actionRedo':
                o_MSql_win2.e_sql.redo()
            # Taglia il testo
            elif p_slot.objectName() == 'actionCut':
                o_MSql_win2.e_sql.cut()
            # Copia il testo rispetto al widget che aveva il focus
            elif p_slot.objectName() == 'actionCopy':
                # Ricerco dove era il focus prima di selezionare la voce di menu
                focused_widget = QApplication.focusWidget()
                # Se il widget era di tipo testo, copio contenuto nella clipboard (nel caso del plaintext converto il separatore di paragrafo in ritorno a capo)
                if isinstance(focused_widget, QPlainTextEdit):                    
                    clipboard = QApplication.clipboard()
                    clipboard.setText(focused_widget.textCursor().selectedText().replace('\u2029','\n'))                                                        
                # Se il widget è la tabella dei risultati copio valore nella clipboard (ma solo se item è di testo)
                elif isinstance(focused_widget, QTableWidget):                    
                    v_item = focused_widget.currentItem()
                    if isinstance(v_item, QTableWidgetItem):                    
                        clipboard = QApplication.clipboard()
                        clipboard.setText(v_item.text())                                                        
            # Incolla il testo
            elif p_slot.objectName() == 'actionPaste':
                o_MSql_win2.e_sql.paste()                
            # Seleziona tutto
            elif p_slot.objectName() == 'actionSelectAll':
                o_MSql_win2.e_sql.selectAll()
            # Elimina riga
            elif p_slot.objectName() == 'actionLine_cut':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_LINEDELETE)
            # Traspone riga
            elif p_slot.objectName() == 'actionLine_transpose':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_LINETRANSPOSE)
            # Duplica riga/selezione
            elif p_slot.objectName() == 'actionLine_Selection_duplicate':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_LINEDUPLICATE)
            # Cancella parola a sinistra
            elif p_slot.objectName() == 'actionDelete_start_of_word':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDLEFT)
            # Cancella parola a destra
            elif p_slot.objectName() == 'actionDelete_end_of_word':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDRIGHT)
            # Cancella riga a sinistra
            elif p_slot.objectName() == 'actionDelete_start_of_line':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_DELLINELEFT)
            # Cancella riga a destra
            elif p_slot.objectName() == 'actionDelete_end_of_line':
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_DELLINERIGHT)                
            # Vai alla riga numero
            elif p_slot.objectName() == 'actionGo_To_Line':
                o_MSql_win2.slot_goto_line()
            # Vai all'inizio dell'editor
            elif p_slot.objectName() == 'actionGo_to_start':                                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_GOTOLINE,0)
            # Vai alla fine dell'editor
            elif p_slot.objectName() == 'actionGo_to_end':                
                o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_GOTOLINE,o_MSql_win2.e_sql.SendScintilla(QsciScintilla.SCI_GETLINECOUNT)-1)
            # Esecuzione dell'sql
            elif p_slot.objectName() == 'actionRun_selected_area':                 
                v_ok = o_MSql_win2.slot_esegui(False)                
                if v_ok == 'ko':
                    message_error(QCoreApplication.translate('MSql_win1','Script stopped for error!'))
            # Esecuzione della singola istruzione sql
            elif p_slot.objectName() == 'actionExecute_current':                 
                message_info(QCoreApplication.translate('MSql_win1','Position yourself on the instruction you want to execute and press CTRL+Enter'))                                
            # Esecuzione dell'sql in modalità piano di esecuzione
            elif p_slot.objectName() == 'actionExplain_Plan':                
                v_ok = o_MSql_win2.slot_esegui(True)
                if v_ok == 'ko':
                    message_error(QCoreApplication.translate('MSql_win1','Error to analyze query!'))
            # Commit
            elif p_slot.objectName() == 'actionCommit':
                o_MSql_win2.slot_commit_rollback('Commit')
            # Rollback
            elif p_slot.objectName() == 'actionRollback':
                o_MSql_win2.slot_commit_rollback('Rollback')
            # Ricerca di un oggetto
            elif p_slot.objectName() == 'actionFind_object':                
                message_info(QCoreApplication.translate('MSql_win1','Position yourself in the text-editor on the object and press F12'))                                
            # Query veloce sul nome di tabella
            elif p_slot.objectName() == 'actionQuick_query':                
                message_info(QCoreApplication.translate('MSql_win1','Position yourself in the text-editor on the table and press F11'))                                
            # Carico il risultato sql alla prima riga 
            elif p_slot.objectName() == 'actionGo_to_Top':                
                o_MSql_win2.slot_go_to_top()
            # Carico il risultato sql fino all'ultima riga
            elif p_slot.objectName() == 'actionGo_to_End':
                o_MSql_win2.slot_go_to_end()        
            # Esporto in formato Excel
            elif p_slot.objectName() == 'actionExport_to_Excel':
                o_MSql_win2.slot_export_to_excel_csv()
            # Pulizia di tutto l'output
            elif p_slot.objectName() == 'actionClear_output':                 
                o_MSql_win2.slot_clear('ALL')    
            # Attiva l'auto pulizia ad ogni esecuzione di codice pl-sql
            elif p_slot.objectName() == 'actionAuto_clear_output':
                # riporto la preferenza di menu dentro l'oggetto delle preferenze 
                if self.actionAuto_clear_output.isChecked():                
                    o_global_preferences.auto_clear_output = True
                else:
                    o_global_preferences.auto_clear_output = False
            # Selezione del font per l'editor
            elif p_slot.objectName() == 'actionFont_editor_selector':
                o_MSql_win2.slot_font_editor_selector(None)
            # Selezione del font per l'output di sql
            elif p_slot.objectName() == 'actionFont_output_selector':
                o_MSql_win2.slot_font_result_selector(None)
            # Creo lo script per la modifica dei dati
            elif p_slot.objectName() == 'actionSave_modified_data':
                o_MSql_win2.slot_save_modified_data()
            # Prendo il testo selezionato e lo riformatto (esempio istruzione SQL che viene reindentata)
            elif p_slot.objectName() == 'actionFormat_SQL_instruction':
                o_MSql_win2.slot_format_sql_statement()
            # Estraggo dall'output una nuova select e la inserisco nell'editor (questo ha senso se utente ha inserito parametri usando il popup menu sulle colonne)
            elif p_slot.objectName() == 'actionExtract_sql_from_output':
                o_MSql_win2.slot_extract_sql_from_output()
            # Attivo/disattivo indentation guide sull'editor
            elif p_slot.objectName() == 'actionIndentation_guide':
                o_MSql_win2.slot_indentation_guide()
            # Creo una view laterale per l'editor attivo    
            elif p_slot.objectName() == 'actionEditor_view':                
                o_MSql_win2.slot_editor_view()            

    def slot_editable(self):
        """
           Gestione della modifica dei risultati di una query
        """
        global o_global_preferences
        
        # se edit abilitato, la evidenzio
        if o_global_preferences.editable:            
            self.l_tabella_editabile.setText(QCoreApplication.translate('MSql_win1','Editable table: Enabled'))                        
            self.l_tabella_editabile.setStyleSheet('color: red;')      
            self.l_tabella_editabile.setStyleSheet('background-color: red ;color: white;')             
        else:
            self.l_tabella_editabile.setText(QCoreApplication.translate('MSql_win1','Editable table: Disabled'))            
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

           Nota! Per permettere alla funzione di smistamento delle voci di menu di capire che siamo in presenza di un file recente,
                 quando viene creata la action della voce di menu, viene impostato il dato 'FILE_RECENTI'.
                 Inoltre vengono usati due array a livello di oggetto main dove il primo contiene elenco dei pathname dei files e l'altro
                 contiene elenco degli oggetti action che sono propri della struttura di menu (questo semplicemente per permettere il ripulisti)
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
                            self.menuFiles.insertAction(self.actionExit,v_action)
                            # l'oggetto action lo aggiungo all'array che tiene traccia delle voci di menu
                            self.elenco_file_recenti_action.append(v_action)                            
                            # carico array
                            v_elenco_file_recenti.append(v_nome_file)
                    self.menuFiles.insertSeparator(self.actionExit)
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
            
            # elimino tutte le voci dal menu dei recenti (usando il relativo array con i puntatori agli oggetti action)
            for v_action in self.elenco_file_recenti_action:                
                self.menuFiles.removeAction(v_action)            
            self.elenco_file_recenti_action.clear()

            # apro il file che contiene i recenti per salvare i dati (salverò solo gli ultimi 10 files)
            v_file_recenti = open(v_global_work_dir + 'MSql_recent_files.ini','w')            
            # scorro array al contrario (così tengo il più recente in cima alla lista) e ricarico il menu a video            
            v_conta_righe = 0
            for v_index in range(len(self.elenco_file_recenti),0,-1):                
                if v_conta_righe < 10:                    
                    v_action = QAction(self)
                    v_action.setText(self.elenco_file_recenti[v_index-1])
                    v_action.setData('FILE_RECENTI')                    
                    # aggiungo a video la voce di menu
                    self.menuFiles.insertAction(self.actionExit,v_action)
                    # l'oggetto action lo aggiungo all'array che tiene traccia delle voci di menu
                    self.elenco_file_recenti_action.append(v_action)                    
                    v_file_recenti.write(self.elenco_file_recenti[v_index-1]+'\n')                                            
                    v_conta_righe += 1
            # chiudo il file
            v_file_recenti.close()    
                     
    def openfile(self, p_nome_file):
        """
           Apertura di un file...
           Se p_nome_file viene passato allora viene letto direttamente il file indicato

           Questa funzione restituisce:
              - nome del file 
              - contenuto del file
              - tipo di codifica del file (ANSI-UTF_8)
        """      
        global o_global_preferences

        def formato_file_utf8(p_filename):
            """ 
               Restituisce true se il file è nel formato UTF-8
            """
            try:
                with open(p_filename, 'rb') as f:
                    f.read().decode('utf-8')
                return True
            except UnicodeDecodeError:
                return False

        # se richiesto di aprire file passando dalla dialog box di file requester
        if p_nome_file is None:
            # la dir di default è quella richiesta dall'utente o la Documenti        
            if o_global_preferences.open_dir == '':
                v_default_open_dir = QDir.homePath() + "\\Documents\\"
            else:
                v_default_open_dir = o_global_preferences.open_dir

            # dialog box per richiesta file
            v_tupla_filename = QFileDialog.getOpenFileName(self, "Open File", v_default_open_dir ,"SQL files (*.msql *.sql *.pls *.plb *.trg);;All files (*.*)")                            
			# prendo il nome del file e lo normalizzo
            v_filename = os.path.normpath(v_tupla_filename[0])
            # reimposto la dir di default in modo che in questa sessione del programma rimanga quella che l'utente ha scelto per aprire il file                        
            if v_filename != '':                               
                o_global_preferences.open_dir = os.path.split( v_tupla_filename[0] )[0]

        # .. altrimenti ricevuto in input un file specifico
        else:
            v_tupla_filename = []
            v_filename = p_nome_file

        # è richiesto di aprire un file...
        if v_filename != "" and v_filename != ".":
            # controllo se il file è già aperto in altra finestra di editor
            for obj_win2 in self.o_lst_window2:
                if not obj_win2.v_editor_chiuso and  obj_win2.objectName() == v_filename:
                    message_error(QCoreApplication.translate('Open','This file is already open!'))
                    return None, None, None                        
            # procedo con apertura
            try:
                # controllo se il file ha la codifica utf-8
                v_file_is_uft_8 = formato_file_utf8(v_filename)
                # apertura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                         
                if v_file_is_uft_8:                    
                    v_file = open(v_filename,'r',encoding='utf-8',newline='')
                # apertura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
                else:                    
                    v_file = open(v_filename,'r',newline='')
                # aggiungo il nome del file ai file recenti                
                self.aggiorna_elenco_file_recenti(v_filename)
                # restituisco il nome e il contenuto del file                
                return v_filename, v_file.read(), v_file_is_uft_8
            except Exception as err:
                message_error(QCoreApplication.translate('Open','Error to opened the file:') + ' ' + str(err))
                return None, None, None
        else:
            return None, None, None
    
    def closeEvent(self, event):
        """
           Intercetto l'evento di chiusura e chiudo tutte le istanze del/i editor aperto/i
           Questa funzione sovrascrive quella nativa di QT 
        """     
        # scorro la lista-oggetti-editor e richiamo l'evento di chiusura del singolo oggetto 
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso:
                v_event_close = QCloseEvent()
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
                
        # se utente ha richiesto di ricordare la posizione della window...
        if o_global_preferences.remember_window_pos:
            # recupero dal registro di sistema (regedit) la posizione della window
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)                        
            # recupero dal registro di sistema (regedit) la posizione delle dock                
            windowstate = self.settings.value("windowstate")
            if windowstate:
                self.restoreState(windowstate)      
            # la dock del file system parte sempre nascosta
            self.dockWidget_3.hide()                  
                        
    def salvo_posizione_window(self):
        """
           Salvo in un file la posizione della window (se richiesto dalle preferenze)
           Questo salvataggio avviene automaticamente alla chiusura di MSql
        """
        global o_global_preferences        
                
        # se utente ha richiesto di salvare la posizione della window...
        if o_global_preferences.remember_window_pos:
            # salvo nel registro di sistema (regedit) la posizione della window
            self.settings.setValue("geometry", self.saveGeometry())            
            # salvo nel registro di sistema (regedit) la posizione delle dock
            self.settings.setValue("windowstate", self.saveState())                        
    
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
            except oracledb.Error as e:                                                            
                errorObj, = e.args    
                message_error(QCoreApplication.translate('MSql_win1',"Error:") + ' ' + errorObj.message)                                            
                return 'ko'

            v_conta = v_cursore.fetchone()[0]            
            # se ci sono transazioni in sospeso richiedo come procedere
            if v_conta != 0:
                # in caso affermativo --> eseguo la commit
                if message_warning_yes_no(QCoreApplication.translate('MSql_win1','MSql detected that the current session has an open transaction. Do you want to perform commit before closing the session?')) == 'Yes':
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
        global v_global_color
        global v_global_background
        global v_global_emphasis
        global v_global_create_confirm
        global o_global_preferences                   
        
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
                        # colore usato per evidenziare il nome del server...
                        v_global_color = rec[2]                                                      
                        # alla posizione 4 è presente la preferenza di evidenziare il server con colore specifico
                        if len(rec) >= 5 and rec[4] == '1':
                            v_global_emphasis = True
                        else:
                            v_global_emphasis = False
                        # alla posizione 5 è presente la preferenza se chiedere conferma quando viene lanciato un comando CREATE
                        if len(rec) >= 6 and rec[5] == '1':
                            v_global_create_confirm = True
                        else:
                            v_global_create_confirm = False

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
            # imposto la stringa di connessione utente con modalità proxy se indicata
            v_user_connect = f"{self.e_user_name}"
            if self.e_user_proxy != '':
                v_user_connect += f"[{self.e_user_proxy}]"            
            # connessione al DB (eventualmente come dba)            
            if self.e_user_mode == 'SYSDBA':               
                v_global_connection = oracledb.connect(user=v_user_connect, password=self.e_password, dsn=self.e_server_name, mode=oracledb.SYSDBA)                        
            else:
                v_global_connection = oracledb.connect(user=v_user_connect, password=self.e_password, dsn=self.e_server_name)                        
            # imposto var che indica la connessione a oracle
            v_global_connesso = True
            # apro un cursore finalizzato alla gestione degli oggettiDB
            self.v_cursor_db_obj = v_global_connection.cursor()            
        except:
            message_error(QCoreApplication.translate('MSql_win1','Error to oracle connection!'))    
            if self.e_user_proxy != '':
                message_error(QCoreApplication.translate('MSql_win1','For via proxy connection remember to activate this using command')+chr(10)+'"ALTER USER proxy_user GRANT CONNECT THROUGH main_user;"'+chr(10)+QCoreApplication.translate('MSql_win1','using user SYS!'))    
            v_global_connesso = False

        # Se mi collego come SYSDBA coloro di rosso
        if self.e_user_mode == 'SYSDBA':
            v_global_background = 'red'

        # sulla statusbar, aggiorno la label della connessione        
        self.l_connection.setText(QCoreApplication.translate('MSql_win1','Connection:') + ' ' + self.e_server_name + "/" + v_user_connect)     
        self.l_connection.setStyleSheet('background-color: ' + v_global_color + ';color: "' + v_global_background + '";')              

        # imposto la proprietà di schema corrente con lo user
        if self.e_user_proxy != '':
            self.current_schema = self.e_user_proxy
        else:
            self.current_schema = self.e_user_name

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

            # se siamo nella situazione di riconnessione --> faccio il refresh dell'object navigator
            try:
                self.oggetti_db_lista
            except:
                v_esiste = False
            else:
                v_esiste = True
            if v_esiste:
                self.slot_oggetti_db_scelta()

            # pulisco l'object viewer
            try:
                self.db_oggetto_tree_model
            except:
                v_esiste = False
            else:
                v_esiste = True
            if v_esiste:
                self.db_oggetto_tree_model.clear()
             
        # scorro la lista-oggetti-editor...        
        for obj_win2 in self.o_lst_window2:
            if not obj_win2.v_editor_chiuso and v_global_connesso:        
                # l'oggetto che contiene i risultati delle query viene pulito, in modo che se c'era qualcosa in canna da connessione precedente, non rimanga a video                                
                obj_win2.o_table.verticalScrollBar().blockSignals(True)      
                obj_win2.o_table.clearContents()
                obj_win2.o_table.setRowCount(0)                    
                obj_win2.o_table.setColumnCount(0)                    
                obj_win2.o_table.verticalScrollBar().blockSignals(False)      
                
                # ...e apro un cursore ad uso di quell'oggetto-editor                
                obj_win2.v_cursor = v_global_connection.cursor()
                
                # evidenzio i colori se richiesto
                obj_win2.set_emphasis()
                                
                # aggiorno il lexer aggiungendo tutte le nuove keywords                
                if len(v_global_my_lexer_keywords) > 0:                          
                    obj_win2.v_lexer.keywords(6)
                    obj_win2.v_lexer.carica_dizionario_per_autocompletamento()
                
                # aggiorno la statusbar
                obj_win2.aggiorna_statusbar()
        
    def slot_disconnect(self):
        """
           Esegue disconnessione a Oracle
        """
        global v_global_connesso   
        global v_global_connection        
        global v_global_color
        global v_global_background        
        global v_global_create_confirm        
        
        ###
        # Refresh del menu
        ###
        # disattivo la check sulla parte server e user (preferiti)
        for action in self.action_elenco_server:            
            action.setChecked(False)
        for action in self.action_elenco_user:
            action.setChecked(False)

        ###
        # Disconnessione
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
                                    
        # chiudo connessione
        try:
            # se c'è già una connessione --> la chiudo
            if v_global_connesso:
                v_global_connection.close()            
        except:
            message_error(QCoreApplication.translate('MSql_win1','Error to oracle disconnection!'))                
        
        # imposto var che indica la connessione a oracle
        v_global_connesso = False

        # sulla statusbar, aggiorno la label della connessione        
        self.l_connection.setText("No connect to Oracle Database!")     
        self.l_connection.setStyleSheet('background-color: red ;color: "' + v_global_background + '";')                      
    
    def slot_object_navigator_start_timer(self):
        """
           Attiva il timer che attende 0,8 secondi prima di richiamare effettivamente la ricerca
        """
        self.object_navigator_search_timer.start(800)  
            
    def slot_oggetti_db_scelta(self):
        """
           Carica elenco oggetti
        """                     
        # viene usato lo schema corrente
        self.carica_oggetti_db_scelta()   

    def carica_oggetti_db_scelta(self):
        """
           In base alla voce scelta, viene caricata la lista con elenco degli oggetti pertinenti
           Come owner viene usata la proprietà current_schema 
        """                        
        global v_global_connesso

        # se non connesso --> esco
        if not v_global_connesso:
            return 'ko'
        
        # imposto il titolo della window inserendo lo schema
        self.dockWidget.setWindowTitle(QCoreApplication.translate('MSql_win1','Objects Navigator') + ' (' + self.current_schema + ')')

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
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.current_schema+"""' AND CONSTRAINT_TYPE='P' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""
            # chiavi univoche
            elif v_tipo_oggetto == 'UNIQUE_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.current_schema+"""' AND CONSTRAINT_TYPE='U' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""    
            # relazioni
            elif v_tipo_oggetto == 'FOREIGN_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.current_schema+"""' AND CONSTRAINT_TYPE='R' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$'"""    
            # check
            elif v_tipo_oggetto == 'CHECK_KEY':
                v_select = """SELECT CONSTRAINT_NAME OBJECT_NAME, DECODE(INVALID,NULL,0,1) INVALID, STATUS FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.current_schema+"""' AND CONSTRAINT_TYPE='C' AND SUBSTR(CONSTRAINT_NAME,1,4) != 'BIN$' AND GENERATED != 'GENERATED NAME'"""    
            # indici
            elif v_tipo_oggetto == 'INDEXES':                
                v_select = """SELECT INDEX_NAME OBJECT_NAME, 0 INVALID, 'ENABLED' STATUS FROM ALL_INDEXES WHERE OWNER='"""+self.current_schema+"""'"""
            # sinonimi
            elif v_tipo_oggetto == 'SYNONYM':                
                v_select = """SELECT SYNONYM_NAME OBJECT_NAME, 0 INVALID, 'ENABLED' STATUS FROM ALL_SYNONYMS WHERE OWNER='"""+self.current_schema+"""'"""
            # altri oggetti (type, java, ecc.)
            elif v_tipo_oggetto == 'OTHERS':
                v_select = """SELECT OBJECT_NAME || ' - ' || OBJECT_TYPE AS OBJECT_NAME,                                        
                                 (SELECT COUNT(*) 
                                  FROM   ALL_OBJECTS ABJ
                                  WHERE  ABJ.OWNER=ALL_OBJECTS.OWNER AND 
                                         ABJ.OBJECT_NAME=ALL_OBJECTS.OBJECT_NAME AND 
                                         ABJ.STATUS != 'VALID') INVALID,
                                 'ENABLED' STATUS                                 
                              FROM   ALL_OBJECTS 
                              WHERE  OWNER='""" + self.current_schema + """' AND
                                     OBJECT_TYPE NOT IN ('TABLE','VIEW','PACKAGE','PROCEDURE','FUNCTION','TRIGGER','SEQUENCE','INDEX','SYNONYM','PACKAGE BODY','JAVA CLASS','LOB') AND 
                                     SECONDARY = 'N'"""
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
                                  WHERE  OWNER='""" + self.current_schema + """' AND 
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
                                          WHERE  OWNER='""" + self.current_schema + """' AND 
                                                 OBJECT_TYPE='""" + v_tipo_oggetto + """' AND
                                                 SECONDARY = 'N'"""                          
        # l'utente non ha scelto nessun tipo di oggetto....si carica tutta la tabella ALL_OBJECTS (notare come alcuni tipi di oggetti come le foreign key non siano presenti)
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
                          WHERE  OWNER='""" + self.current_schema + """' AND
                                 OBJECT_TYPE IN ('TABLE','VIEW','PACKAGE','PROCEDURE','FUNCTION','TRIGGER','SEQUENCE') AND                                      
                                 SECONDARY = 'N'"""

        # inserisco la select creata in una di livello superiore per poter poi applicare filtri e ordinamento
        v_select = 'SELECT * FROM ( ' + v_select + ' ) '

        # se necessario applico il filtro di ricerca
        if self.oggetti_db_ricerca.text() != '' or self.oggetti_db_tipo_ricerca.currentText() in ('Only invalid','Only disabled'):
            if self.oggetti_db_tipo_ricerca.currentText() == 'Start with':
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '" + self.oggetti_db_ricerca.text().upper().rstrip() + "%'"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Like':
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper().rstrip() + "%'"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Only invalid': 
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper().rstrip() + "%' AND INVALID > 0"
            elif self.oggetti_db_tipo_ricerca.currentText() == 'Only disabled': 
                v_select += " WHERE UPPER(OBJECT_NAME) LIKE '%" + self.oggetti_db_ricerca.text().upper().rstrip() + "%' AND STATUS = 'DISABLED'"
        # aggiungo order by
        v_select += " ORDER BY OBJECT_NAME"                                
                
        # eseguo la select                
        try:            
            self.v_cursor_db_obj.execute(v_select)                    
        except oracledb.Error as e:                                                                
            # ripristino icona freccia del mouse
            Freccia_Mouse(False)
            # emetto errore 
            errorObj, = e.args                     
            message_error(QCoreApplication.translate('MSql_win1',"Error:") + ' ' + errorObj.message)       
            return "ko"                  
        # carico il risultato     
        v_righe = self.v_cursor_db_obj.fetchall()                    
        # carico elenco nel modello che è collegato alla lista
        for v_riga in v_righe:
            v_item = QStandardItem()                        
            # nell'item inserisco nome oggetto e commento
            v_item.setText(v_riga[0]) 
            # oggetto invalido imposto icona errore
            if v_riga[1] != 0: 
                v_icon = QIcon()
                v_icon.addPixmap(QPixmap("icons:error.png"), QIcon.Mode.Normal, QIcon.State.Off)
                v_item.setIcon(v_icon)                
            # oggetto disabilitato imposto icona disabled
            if v_riga[2] == 'DISABLED': 
                v_icon = QIcon()
                v_icon.addPixmap(QPixmap("icons:disabled.png"), QIcon.Mode.Normal, QIcon.State.Off)
                v_item.setIcon(v_icon)                

            self.oggetti_db_lista.appendRow(v_item)                                   

        # Ripristino icona freccia del mouse
        Freccia_Mouse(False)        
    
    def slot_popup_menu_db_elenco(self,p_position):
        """
           Visualizza popup menu quando si preme il tasto destro del mouse sulla riga elenco oggetti
        """
        # imposto var che identifica in che zona ci troviamo
        self.v_popup_menu_zone = 'LISTA_OGGETTI'
        # prendo il nome dell'oggetto scelto dall'utente dalla lista degli oggetti       
        v_selindex = self.oggetti_db_elenco.selectedIndexes()[0]        
        self.v_nome_oggetto = v_selindex.data()
        # prendo il tipo di oggetto scelto dall'utente        
        if self.oggetti_db_scelta.currentText() != '':
            self.v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                        
        # se siamo nella modalità di visulizzazione di tutti gli oggetti, ne ricavo il nome e il tipo dalla riga selezionata
        # dove il nomer e il tipo sono separati da spazio+meno+spazio
        else:
            self.v_tipo_oggetto = self.v_nome_oggetto.split(' - ')[1]
            self.v_nome_oggetto = self.v_nome_oggetto.split(' - ')[0]
        # richiamo la creazione del popup menu
        self.popup_menu_object(p_position,'RAMO')

    def popup_menu_object(self,p_position,p_tipo_ela):
        """
           Visualizza popup menu quando si preme il tasto destro del mouse.
           Nel caso si sia premuto il tasto destro sull'object viewer e il sottostante sia un package,
           viene visualizzata solo la voce "Insert function in editor"
        """        
        if p_tipo_ela == 'RAMO':            
            v_tipo_obj = self.v_tipo_oggetto
        elif p_tipo_ela == 'FOGLIA':            
            v_tipo_obj = self.v_tipo_foglia
        elif p_tipo_ela == 'CAMPO_TABELLA':            
            v_tipo_obj = self.v_nome_foglia
        else:
            message_error(QCoreApplication.translate('MSql_win1','Error to create popupmenu!'))

        v_menu = QMenu(self)        
        if self.v_popup_menu_zone == 'FOGLIA_ALBERO' and v_tipo_obj == 'FUNCTION':            
            # azione insert function in editor
            v_azione_insert_in_editor = QAction('Insert in editor') 
            v_azione_insert_in_editor.triggered.connect(self.slot_popup_menu_insert_in_editor)
            v_menu.addAction(v_azione_insert_in_editor)
        elif self.v_popup_menu_zone == 'CAMPO_TABELLA':            
            # azione modify field
            v_azione_modify_field = QAction('Modify')
            v_azione_modify_field.triggered.connect(self.slot_popup_menu_modify_field)
            v_menu.addAction(v_azione_modify_field)
            # azione drop field 
            v_azione_drop_field = QAction('Drop')
            v_azione_drop_field.triggered.connect(self.slot_popup_menu_drop_field)
            v_menu.addAction(v_azione_drop_field)            
            # azione drop field 
            v_azione_comment = QAction('Extract comment')
            v_azione_comment.triggered.connect(self.slot_popup_menu_comment_field)
            v_menu.addAction(v_azione_comment)            
        elif v_tipo_obj == 'OTHERS':            
            # azione load ddl
            v_azione_load_ddl = QAction('Load DDL')
            v_azione_load_ddl.triggered.connect(self.slot_popup_menu_load_ddl)
            v_menu.addAction(v_azione_load_ddl)
        else:
            # azione load ddl
            v_azione_load_ddl = QAction('Load DDL')
            v_azione_load_ddl.triggered.connect(self.slot_popup_menu_load_ddl)
            v_menu.addAction(v_azione_load_ddl)
            # separatore
            v_menu.addSeparator()
            # azione enable
            v_azione_enable = QAction('Enable')
            v_azione_enable.triggered.connect(self.slot_popup_menu_enable)
            v_menu.addAction(v_azione_enable)
            # azione disable
            v_azione_disable = QAction('Disable')
            v_azione_disable.triggered.connect(self.slot_popup_menu_disable)
            v_menu.addAction(v_azione_disable)
            # separatore
            v_menu.addSeparator()
            # azione drop
            v_azione_drop = QAction('Drop')
            v_azione_drop.triggered.connect(self.slot_popup_menu_drop)
            v_menu.addAction(v_azione_drop)
            # aggiungo info
            v_menu.addSeparator()
            # azione info
            v_azione_info = QAction('Info')
            v_azione_info.triggered.connect(self.slot_popup_menu_info)
            v_menu.addAction(v_azione_info)
        # visualizzo il menu sopra la riga selezionata (della lista oggetti)
        if self.v_popup_menu_zone == 'LISTA_OGGETTI':
            v_menu.exec(self.oggetti_db_elenco.viewport().mapToGlobal(p_position))    
        # oppure sopra un elmento dell'albero dell'object viewer
        elif self.v_popup_menu_zone in ('FOGLIA_ALBERO','CAMPO_TABELLA'):
            v_menu.exec(self.db_oggetto_tree.viewport().mapToGlobal(p_position))    

    def slot_popup_menu_modify_field(self):
        """
           Crea il comando di modifica del campo di tabella lo inserisce nell'editor
        """                
        self.oggetti_db_elenco_esegui_voce_menu('MODIFY_FIELD')

    def slot_popup_menu_drop_field(self):
        """
           Crea il comando di eliminazione del campo di tabella lo inserisce nell'editor
        """                
        self.oggetti_db_elenco_esegui_voce_menu('DROP_FIELD')

    def slot_popup_menu_comment_field(self):
        """
           Crea il comando di estrazione del commento del campo di tabella
        """                
        self.oggetti_db_elenco_esegui_voce_menu('COMMENT_FIELD')
    
    def slot_popup_menu_load_ddl(self):
        """
           Carica il sorgente dell'oggetto selezionato (menu popup sull'elenco) dentro l'editor
           Viene usata la variabile generale self.v_nome_oggetto che contiene il nome dell'oggetto corrente           
        """ 
        def nuovo_nome_file(p_nome_oggetto):
            """
               Controlla se già aperta una finestra con lo stesso nome di oggetto e se la trova cambia il nome aggiungendo un !
            """
            def window_attiva_con_nome_oggetto(p_nome):              
                # scorro la lista-oggetti-editor e controllo se esiste una window con lo stesso nome ricevuto in input
                for i in range(0,len(self.o_lst_window2)):                    
                    if not self.o_lst_window2[i].v_editor_chiuso and self.o_lst_window2[i].objectName() == p_nome:       
                        return True
                return False
            
            # ciclo di creazione del nuovo nome (si continua ad aggiungere un ! fino a quando si non si trova che nome non usato)
            p_nome_oggetto = '!' + p_nome_oggetto
            while window_attiva_con_nome_oggetto(p_nome_oggetto):
                p_nome_oggetto = '!' + p_nome_oggetto

            return p_nome_oggetto

        # imposto var interna per select 
        v_select = ''
        
        # se c'è un oggetto da elaborare...
        if self.v_nome_oggetto != '' and self.v_tipo_oggetto != '':
            # imposto var che conterrà il testo dell'oggetto DB 
            v_testo_oggetto_db = ''
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(True)

            # richiamo la procedura di oracle che mi restituisce la ddl dell'oggetto
            # se richiesto di aprire il o il package body, allora devo fare una chiamata specifica
            if self.v_tipo_oggetto == 'PACKAGE BODY': 
                v_select = "SELECT DBMS_METADATA.GET_DDL('PACKAGE_BODY','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto == 'PACKAGE':
                v_select = """SELECT DBMS_METADATA.GET_DDL('PACKAGE_SPEC','"""+self.v_nome_oggetto+"""') FROM DUAL 
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL
                              SELECT DBMS_METADATA.GET_DDL('PACKAGE_BODY','"""+self.v_nome_oggetto+"""') FROM DUAL
                           """
            elif self.v_tipo_oggetto in ('TABLE'):
                v_select = """SELECT DBMS_METADATA.GET_DDL('"""+self.v_tipo_oggetto+"""','"""+self.v_nome_oggetto+"""') FROM DUAL
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('INDEX','"""+self.v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_INDEXES WHERE OWNER='"""+self.current_schema+"""' AND TABLE_NAME='"""+self.v_nome_oggetto+"""') > 0													   
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL                                                
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('CONSTRAINT','"""+self.v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_CONSTRAINTS WHERE OWNER='"""+self.current_schema+"""' AND TABLE_NAME='"""+self.v_nome_oggetto+"""' AND R_CONSTRAINT_NAME IS NULL) > 0													   
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL
                              UNION ALL                              
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('TRIGGER','"""+self.v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_TRIGGERS WHERE OWNER='"""+self.current_schema+"""' AND TABLE_NAME='"""+self.v_nome_oggetto+"""') > 0													                                 
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL
                              SELECT TO_CLOB('COMMENT ON TABLE ' || TABLE_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';')
                              FROM   ALL_TAB_COMMENTS
                              WHERE  ALL_TAB_COMMENTS.OWNER = '"""+self.current_schema+"""'
                                AND  ALL_TAB_COMMENTS.TABLE_NAME = '"""+self.v_nome_oggetto+"""'   
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL                              
                              SELECT TO_CLOB('COMMENT ON COLUMN '|| TABLE_NAME || '.' || COLUMN_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';\n')
                              FROM   (
                                      SELECT ALL_COL_COMMENTS.TABLE_NAME,
									         ALL_COL_COMMENTS.COLUMN_NAME,
											 ALL_COL_COMMENTS.COMMENTS
                                      FROM   ALL_COL_COMMENTS,
                                             ALL_TAB_COLUMNS
                                      WHERE  ALL_COL_COMMENTS.OWNER = '"""+self.current_schema+"""'
                                        AND  ALL_COL_COMMENTS.TABLE_NAME = '"""+self.v_nome_oggetto+"""'   
                                        AND  ALL_TAB_COLUMNS.OWNER = ALL_COL_COMMENTS.OWNER
                                        AND  ALL_TAB_COLUMNS.TABLE_NAME = ALL_COL_COMMENTS.TABLE_NAME
                                        AND  ALL_TAB_COLUMNS.COLUMN_NAME = ALL_COL_COMMENTS.COLUMN_NAME
                                      ORDER BY ALL_TAB_COLUMNS.COLUMN_ID
                                     )
                           """                
            elif self.v_tipo_oggetto in ('VIEW'):
                v_select = """SELECT DBMS_METADATA.GET_DDL('"""+self.v_tipo_oggetto+"""','"""+self.v_nome_oggetto+"""') FROM DUAL
                              UNION ALL
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL                              
                              SELECT DBMS_METADATA.GET_DEPENDENT_DDL('TRIGGER','"""+self.v_nome_oggetto+"""') FROM DUAL
                              WHERE (SELECT COUNT(*) FROM ALL_TRIGGERS WHERE OWNER='"""+self.current_schema+"""' AND TABLE_NAME='"""+self.v_nome_oggetto+"""') > 0													                                 
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL
                              SELECT TO_CLOB('COMMENT ON TABLE ' || TABLE_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';')
                              FROM   ALL_TAB_COMMENTS
                              WHERE  ALL_TAB_COMMENTS.OWNER = '"""+self.current_schema+"""'
                                AND  ALL_TAB_COMMENTS.TABLE_NAME = '"""+self.v_nome_oggetto+"""'   
                              UNION ALL 
                              SELECT TO_CLOB('\n/\n') FROM DUAL                              
                              UNION ALL
                              SELECT TO_CLOB('COMMENT ON COLUMN '|| TABLE_NAME || '.' || COLUMN_NAME || ' IS ''' || REPLACE(COMMENTS,'''','''''') || ''';\n')
                              FROM   ALL_COL_COMMENTS
                              WHERE  ALL_COL_COMMENTS.OWNER = '"""+self.current_schema+"""'
                                AND  ALL_COL_COMMENTS.TABLE_NAME = '"""+self.v_nome_oggetto+"""'   
                           """
            elif self.v_tipo_oggetto in ('PRIMARY_KEY','UNIQUE_KEY','CHECK_KEY'):
                v_select = "SELECT DBMS_METADATA.GET_DDL('CONSTRAINT','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto == 'FOREIGN_KEY':
                v_select = "SELECT DBMS_METADATA.GET_DDL('REF_CONSTRAINT','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto == 'INDEXES':
                v_select = "SELECT DBMS_METADATA.GET_DDL('INDEX','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto == 'SYNONYM':
                v_select = "SELECT DBMS_METADATA.GET_DDL('SYNONYM','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto in ('PROCEDURE','FUNCTION','TRIGGER','SEQUENCE'):                    
                v_select = "SELECT DBMS_METADATA.GET_DDL('"+self.v_tipo_oggetto+"','"+self.v_nome_oggetto+"') FROM DUAL"
            elif self.v_tipo_oggetto == 'OTHERS': 
                self.v_tipo_oggetto = self.v_nome_oggetto.split(' - ')[1]
                self.v_nome_oggetto = self.v_nome_oggetto.split(' - ')[0]        
                if self.v_tipo_oggetto == 'JOB':
                    v_select = "SELECT DBMS_METADATA.GET_DDL('PROCOBJ','"+self.v_nome_oggetto+"') FROM DUAL"            
                elif self.v_tipo_oggetto == 'JAVA SOURCE':                    
                    v_select = "SELECT DBMS_METADATA.GET_DDL('JAVA_SOURCE','"+self.v_nome_oggetto+"') FROM DUAL"            
                elif self.v_tipo_oggetto == 'TYPE BODY':                    
                    v_select = "SELECT DBMS_METADATA.GET_DDL('TYPE_BODY','"+self.v_nome_oggetto+"') FROM DUAL"            
                elif self.v_tipo_oggetto == 'TYPE':                    
                    v_select = "SELECT DBMS_METADATA.GET_DDL('TYPE','"+self.v_nome_oggetto+"') FROM DUAL"            
                else:
                    Freccia_Mouse(False)
                    message_error(QCoreApplication.translate('MSql_win1','Invalid object!'))
                    return 'ko'
            else:
                Freccia_Mouse(False)
                message_error(QCoreApplication.translate('MSql_win1','Invalid object!'))
                return 'ko'
            
            try:                            
                # prendo il primo campo, del primo record e lo trasformo in stringa ricavandone tutto il sorgente                
                self.v_cursor_db_obj.execute(v_select)
                v_testo_oggetto_db = ''
                for v_record in self.v_cursor_db_obj:
                    v_testo_oggetto_db += str(v_record[0])
                # in presenza di trigger si controlla se alla fine c'è l'istruzione di alter. Viene tolta perché manca di separatore istruzione
                if "ALTER TRIGGER" in v_testo_oggetto_db.splitlines()[-1]:
                    v_testo_oggetto_db = "\n".join(v_testo_oggetto_db.splitlines()[0:-1])
            except:
                Freccia_Mouse(False)
                message_error(QCoreApplication.translate('MSql_win1','Error to retrive metadata information!'))
                return 'ko'
            
            ###
            # aggiungo la parte dei grant
            ###            
            try:
                v_select = """SELECT GRANTEE, 
                                     LISTAGG(PRIVILEGE, ',') WITHIN GROUP (ORDER BY PRIVILEGE) AS PRIVILEGE,
                                     GRANTABLE
                              FROM   ALL_TAB_PRIVS 
                              WHERE  TABLE_NAME = '"""+self.v_nome_oggetto+"""' 
                                 AND GRANTOR='"""+self.current_schema+"""'
                              GROUP BY GRANTEE, GRANTABLE
                              ORDER BY GRANTEE
                           """
                self.v_cursor_db_obj.execute(v_select)
                            
                # aggiungo la parte di grant solo se presente
                v_testo_grant_db = ''
                for v_record in self.v_cursor_db_obj:
                    v_testo_grant_db += 'GRANT ' + str(v_record[1]) + ' ON ' + self.v_nome_oggetto + ' TO ' + str(v_record[0]) 
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
            # Attenzione! I file caricati da Oracle hanno come eol solo LF => formato Unix e viene impostato UTF-8
            v_azione = QAction()
            v_azione.setText('Open_db_obj')
            self.smistamento_voci_menu(v_azione, nuovo_nome_file(self.v_nome_oggetto + '.msql'), v_testo_oggetto_db, True)        
                                        
            # Ripristino icona freccia del mouse
            Freccia_Mouse(False)

    def slot_popup_menu_enable(self):
        """
           Crea il comando di attivazione dell'oggetto selezionato e lo inserisce nell'editor
        """                
        self.oggetti_db_elenco_esegui_voce_menu('ENABLE')

    def slot_popup_menu_disable(self):
        """
           Crea il comando di disattivazione dell'oggetto selezionato e lo inserisce nell'editor
        """                
        self.oggetti_db_elenco_esegui_voce_menu('DISABLE')

    def slot_popup_menu_drop(self):
        """
           Crea il comando di drop dell'oggetto selezionato e lo inserisce nell'editor
        """                
        self.oggetti_db_elenco_esegui_voce_menu('DROP')

    def slot_popup_menu_info(self):
        """
           Visualizza la window con le informazioni dell'oggetto
        """        
        from object_info_ui import Ui_object_info_window
        
        self.win_object_info = QDialog()
        self.ui_object_info = Ui_object_info_window()
        self.ui_object_info.setupUi(self.win_object_info)
        centra_window_figlia(self, self.win_object_info)

        # se siamo su oggetto di database...
        if self.v_popup_menu_zone not in ('FOGLIA_ALBERO','CAMPO_TABELLA'):            
            #estrazione delle info dalla tabella degli oggetti
            try:
                v_select = """SELECT OBJECT_NAME,
                                        OWNER,
                                        OBJECT_TYPE,
                                        CREATED,
                                        LAST_DDL_TIME,
                                        STATUS
                                FROM   ALL_OBJECTS
                                WHERE  OBJECT_NAME = '"""+self.v_nome_oggetto+"""' 
                                    AND OBJECT_TYPE = '"""+self.v_tipo_oggetto+"""'                              
                            """
                # esecuzione della select
                self.v_cursor_db_obj.execute(v_select)                            
                # lettura dei dati
                for v_record in self.v_cursor_db_obj:                    
                    self.ui_object_info.e_object_name.setText(v_record[0])
                    self.ui_object_info.e_owner.setText(v_record[1])
                    self.ui_object_info.e_object_type.setText(v_record[2])
                    self.ui_object_info.e_created.setText(v_record[3].strftime('%d/%m/%Y %H:%M:%S'))
                    self.ui_object_info.e_modified.setText(v_record[4].strftime('%d/%m/%Y %H:%M:%S'))
                    self.ui_object_info.e_status.setText(v_record[5])
                    # esco dopo la lettura del primo record
                    break            
            except:
                message_error(QCoreApplication.translate('MSql_win1','No valid object!'))

        # mostro la window
        self.win_object_info.show()                        

    def oggetti_db_elenco_esegui_voce_menu(self, p_function):
        """
           Crea il comando dell'oggetto selezionato e lo inserisce nell'editor (es. alter table...)                     
           Apposite variabili fanno comprendere in che contesto ci si trova per capire come comporre il comando
        """                
        # se siamo su una foglia, prendo il nome della foglia, altrimenti dell'oggetto principale
        if self.v_popup_menu_zone == 'FOGLIA_ALBERO':
            v_nome_obj = self.v_nome_foglia
            v_tipo_obj = self.v_tipo_foglia
        elif self.v_popup_menu_zone == 'CAMPO_TABELLA':
            v_nome_obj = self.v_nome_oggetto
            v_tipo_obj = self.v_nome_foglia
        else:
            v_nome_obj = self.v_nome_oggetto
            v_tipo_obj = self.v_tipo_oggetto
            
        # prendo editor corrente
        o_MSql_win2 = self.oggetto_win2_attivo()
        if o_MSql_win2 == None:            
            message_error(QCoreApplication.translate('MSql_win1','Open a editor!'))
            return 'ko'
                                
        # preparo comando da inserire in editor; in pratica inserisco un ritorno a capo
        # va convertito in Windows (a seconda dell'impostazione dell'editor di destinazione)
        if o_MSql_win2.setting_eol == 'W':
            v_comando = '\r\n'
        else:
            v_comando = '\n'                                   
                    
        # operazioni di abilitazione-disabilitazione
        if v_nome_obj != '' and self.v_tipo_oggetto != '' and p_function in ('ENABLE','DISABLE'):
            if v_tipo_obj == 'PRIMARY_KEY':
                v_comando += "ALTER TABLE "+v_nome_obj+" "+p_function+" PRIMARY KEY;"                    
            elif v_tipo_obj in ('FOREIGN_KEY','UNIQUE_KEY','CHECK_KEY'):
                try:                            
                    # prendo il primo campo, del primo record e lo trasformo in stringa ricavandone il nome della tabella di riferimento
                    v_nome_tabella = self.v_cursor_db_obj.execute("SELECT TABLE_NAME FROM ALL_CONSTRAINTS WHERE OWNER='"+self.e_user_name+"' AND CONSTRAINT_NAME='"+v_nome_obj+"'").fetchone()[0]                                                            
                    v_comando += "ALTER TABLE "+v_nome_tabella+" "+p_function+" CONSTRAINT "+v_nome_obj+";"                
                except:                    
                    message_error(QCoreApplication.translate('MSql_win1','Error to retrive referenced table name!'))                                
                    return 'ko'
            elif v_tipo_obj == 'INDEXES':
                try:                            
                    # prendo il primo campo, del primo record e lo trasformo in stringa ricavandone il nome della tabella di riferimento
                    v_nome_tabella = self.v_cursor_db_obj.execute("SELECT TABLE_NAME FROM ALL_INDEXES WHERE OWNER='"+self.e_user_name+"' AND INDEX_NAME='"+v_nome_obj+"'").fetchone()[0]                                                                                
                    v_comando += "ALTER INDEX "+v_nome_obj+" ON "+v_nome_tabella+" "+p_function+";"            
                except:                    
                    message_error(QCoreApplication.translate('MSql_win1','Error to retrive referenced table name!'))                                
                    return 'ko'
            elif v_tipo_obj == 'TRIGGER':                    
                v_comando += "ALTER TRIGGER "+v_nome_obj+" "+p_function+";"            
            else:
                message_error(QCoreApplication.translate('MSql_win1','Invalid object!'))
                return 'ko'

        # operazione di cancellazione
        if v_nome_obj != '' and v_tipo_obj != '' and p_function in ('DROP'):                
            if v_tipo_obj in ('TABLE','FUNCTION','PROCEDURE','PACKAGE','PACKAGE BODY','SYNONYM','INDEXES','TRIGGER','VIEW','SEQUENCE'):
                if v_tipo_obj == 'INDEXES':
                    v_comando += "DROP INDEX "+v_nome_obj+";"            
                else:
                    v_comando += "DROP "+v_tipo_obj+" "+v_nome_obj+";"            
            elif v_tipo_obj in ('PRIMARY_KEY','FOREIGN_KEY','UNIQUE_KEY','CHECK_KEY'):
                try:                            
                    # prendo il primo campo, del primo record e lo trasformo in stringa ricavandone il nome della tabella di riferimento
                    v_nome_tabella = self.v_cursor_db_obj.execute("SELECT TABLE_NAME FROM ALL_CONSTRAINTS WHERE OWNER='"+self.e_user_name+"' AND CONSTRAINT_NAME='"+v_nome_obj+"'").fetchone()[0]                                                            
                    v_comando += "ALTER TABLE "+v_nome_tabella+" DROP CONSTRAINT "+v_nome_obj+";"                
                except:                    
                    message_error(QCoreApplication.translate('MSql_win1','Error to retrive referenced table name!'))                                
                    return 'ko'            
            else:
                message_error(QCoreApplication.translate('MSql_win1','Invalid object!'))
                return 'ko'

        # operazioni sui campi di tabella 
        # Attenzione! Alcune variabili sono state usate impropriamente 
        #             v_tipo_obj = contiene il nome del campo
        #             v_tipo_foglia = contiene tipo+check+chr(10)+commento 
        if v_nome_obj != '' and self.v_tipo_oggetto != '' and p_function in ('MODIFY_FIELD','DROP_FIELD','COMMENT_FIELD'):
            v_campi = self.v_tipo_foglia.split(chr(10))            
            if p_function == 'MODIFY_FIELD':
                v_comando += "ALTER TABLE "+v_nome_obj+" MODIFY ("+v_tipo_obj+" "+v_campi[0]+");"                
            elif p_function == 'DROP_FIELD':
                v_comando += "ALTER TABLE "+v_nome_obj+" DROP ("+v_tipo_obj+");"                
            elif p_function == 'COMMENT_FIELD':
                v_comando += "COMMENT ON COLUMN "+v_nome_obj+"."+v_tipo_obj+" IS '"+v_campi[1]+"';"                
            else:
                message_error(QCoreApplication.translate('MSql_win1','Invalid field!'))
                return 'ko'
            
        # inserisco il comando nell'editor corrente
        o_MSql_win2.e_sql.append(v_comando)            
        
    def slot_oggetti_db_click(self, p_index):
        """
           Carica nella sezione "object viewer" i dati dell'oggetto selezionato
        """
        # pulisco il campo di ricerca dell'object viewer
        self.e_object_viewer_find.setText('')
        # prendo il nome dell'oggetto scelto dall'utente
        v_selindex = self.oggetti_db_lista.itemFromIndex(p_index)
        self.v_nome_oggetto = v_selindex.text()  
        # prendo il tipo di oggetto scelto dall'utente        
        if self.oggetti_db_scelta.currentText() != '':
            self.v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                        
        # se siamo nella modalità di visulizzazione di tutti gli oggetti, ne ricavo il nome e il tipo dalla riga selezionata
        # dove il nome e il tipo sono separati da spazio+meno+spazio
        else:
            self.v_tipo_oggetto = self.v_nome_oggetto.split(' - ')[1]
            self.v_nome_oggetto = self.v_nome_oggetto.split(' - ')[0]        
        
        # se attivo il flag del descrittore tabelle, pulisco il nome oggetto della sua descrizione
        if self.e_view_description.isChecked():
            self.v_nome_oggetto = self.v_nome_oggetto.split(' - ')[0]        
                
        # se tutto ok, richiamo la visualizzazione
        if self.v_nome_oggetto != '':
            self.carica_object_viewer(self.current_schema, self.v_tipo_oggetto, self.v_nome_oggetto, '')

    def slot_select_schema(self):    
        """
            Apre finestra per richiedere il cambio di schema
        """            
        # inizializzo le strutture grafice e visualizzo la dialog per richiedere il cambio di schema
        self.dialog_select_schema = QDialog()
        self.win_dialog_select_schema = Ui_select_schema_window()
        self.win_dialog_select_schema.setupUi(self.dialog_select_schema)       
        centra_window_figlia(self, self.dialog_select_schema)

        # carico elenco schemi
        self.slot_carica_elenco_schemi()

        # creo evento riferito al bottone di scelta dello schema
        self.win_dialog_select_schema.b_confirm_schema.clicked.connect(self.slot_confirm_schema)                
        # creo evento riferito al bottone di ricerca di uno schema
        self.win_dialog_select_schema.b_start.clicked.connect(self.slot_carica_elenco_schemi)        

        self.dialog_select_schema.show()        
        
    def slot_carica_elenco_schemi(self):
        """
           Esegue il carico elenco schemi per il relativo form
        """        
        global v_global_connesso
        
        # se non connesso --> esco
        if not v_global_connesso:
            return 'ko'

        # associo il modello degli schemi, creato dalla init, all'oggetto di elenco presente nel form
        self.win_dialog_select_schema.e_schema_list.setModel(self.schema_model)
                
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)        
                        
        # eseguo la select che restituisce elenco degli schemi
        v_select = "SELECT USERNAME FROM ALL_USERS"
        if self.win_dialog_select_schema.e_find_schema.text() != '':
            v_select += " WHERE USERNAME LIKE '%" + self.win_dialog_select_schema.e_find_schema.text().upper() + "%'"
        v_select += " ORDER BY USERNAME"
        try:            
            self.v_cursor_db_obj.execute(v_select)                    
        except oracledb.Error as e:                                                                
            # ripristino icona freccia del mouse
            Freccia_Mouse(False)
            # emetto errore 
            errorObj, = e.args                     
            message_error(QCoreApplication.translate('MSql_win1',"Error:") + ' ' + errorObj.message)       
            return "ko"                  
        # ottengo un array di stringa contenente elenco degli schemi
        v_risultato = []
        for righe in self.v_cursor_db_obj.fetchall():
            v_risultato.append(righe[0])                
        # carico il risultato nel modello che essendo a sua volta collegato all'oggetto di form, farà comparire elenco
        self.schema_model.setStringList(v_risultato)

        # Ripristino icona freccia del mouse
        Freccia_Mouse(False)      
    
    def slot_confirm_schema(self):
        """
            Conferma del nuovo schema e caricamento dell'object navigator
        """
        # ricerco la posizione dell'indice selezionato e ne ricavo il contenuto 
        v_index = self.win_dialog_select_schema.e_schema_list.selectedIndexes()[0]                    
        self.current_schema = self.schema_model.data(v_index)
        
        # carico l'object viewer usando lo schema scelto
        if self.current_schema != '':
            # cambio lo schema corrente a livello di database
            try:            
                self.v_cursor_db_obj.execute("ALTER SESSION SET CURRENT_SCHEMA = " + self.current_schema)                    
            except oracledb.Error as e:                                                                
                # emetto errore 
                errorObj, = e.args                     
                message_error(QCoreApplication.translate('MSql_win1',"Error:") + ' ' + errorObj.message)                   
            # ricarico elenco degli oggetti
            self.carica_oggetti_db_scelta()        
        
        # chiudo la window
        self.dialog_select_schema.close()
    
    def carica_object_viewer(self, p_owner, p_tipo_oggetto, p_nome_oggetto, p_link):
        """
           Funzione che si occupa di caricare i dati dell'object viewer
        """        
        # queste due variabili che sono comuni all'oggetto main permettono di contenere i dati principali dell'oggetto
        # che è in visualizzazione nell'object viewer        
        self.v_tipo_oggetto = p_tipo_oggetto
        self.v_nome_oggetto = p_nome_oggetto                
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)

        # pulisco la var che contiene eventuale elenco di procedure-funzioni (solo se si stanno analizzando: procedure-funzioni e package)
        self.oggetti_db_lista_proc_func = ''

        # se l'oggetto selezionato è una tabella o una vista --> preparo select per estrarre i nomi dei campi
        if self.v_tipo_oggetto == 'TABLE' or self.v_tipo_oggetto == 'VIEW':
            print('Start loading object viewer of --> ' + p_owner + '.' + self.v_nome_oggetto + ' - ' + self.v_tipo_oggetto)
            # ricerco la descrizione dell'oggetto
            self.v_cursor_db_obj.execute("SELECT COMMENTS FROM ALL_TAB_COMMENTS"+p_link+" WHERE owner='"+p_owner+"' AND TABLE_NAME='"+self.v_nome_oggetto+"'")
            v_record = self.v_cursor_db_obj.fetchone()
            if v_record is not None:
                self.v_tipo_oggetto_commento = v_record[0]
            else:
                self.v_tipo_oggetto_commento = ''
            # creo un modello dati con 4 colonne (dove nell'intestazione ci metto il nome della tabella e la sua descrizione)
            self.db_oggetto_tree_model = QStandardItemModel()
            self.db_oggetto_tree_model.setHorizontalHeaderLabels([self.v_nome_oggetto, p_owner, '', self.v_tipo_oggetto_commento])

            ###
            # prima radice con il nome della tabella
            ###
            v_root_campi = QStandardItem('Fields')            

            self.v_cursor_db_obj.execute("""SELECT A.COLUMN_NAME AS NOME,
                                                   CASE WHEN A.DATA_TYPE = 'NUMBER' THEN
                                                        CASE WHEN A.DATA_PRECISION IS NULL THEN
	                                                         'INTEGER'
	                                                    ELSE
                                                             A.DATA_TYPE|| '(' || A.DATA_PRECISION || ',' || A.DATA_SCALE || ')'
	                                                    END 
                                                   WHEN A.DATA_TYPE IN ('VARCHAR2','CHAR') THEN
                                                        A.DATA_TYPE || '(' || A.CHAR_LENGTH || ')'
                                                   ELSE
                                                         A.DATA_TYPE
                                                   END AS TIPO,
                                                   UPPER(Decode(A.NULLABLE,'N',' NOT NULL','')) AS COLONNA_NULLA,
                                                   DATA_DEFAULT AS VALORE_DEFAULT,
                                                   B.COMMENTS AS COMMENTO
                                            FROM   ALL_TAB_COLUMNS"""+p_link+""" A, ALL_COL_COMMENTS"""+p_link+""" B 
                                            WHERE  A.OWNER='"""+p_owner+"""' AND 
                                                   A.TABLE_NAME ='"""+self.v_nome_oggetto+"""' AND 
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
                    v_campo_col2.setText( v_campo_col2.text() + ' DEFAULT ' + str(result[3]).rstrip() )                                    
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
                                            FROM   ALL_CONSTRAINTS"""+p_link+"""
                                            WHERE  OWNER='"""+p_owner+"""' AND 
                                                   TABLE_NAME='"""+self.v_nome_oggetto+"""' AND
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
                                            FROM   ALL_INDEXES"""+p_link+"""
                                            WHERE  OWNER='"""+p_owner+"""' AND 
                                                    TABLE_NAME='"""+self.v_nome_oggetto+"""'
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
                                            FROM   ALL_TRIGGERS"""+p_link+""" 
                                            WHERE  OWNER='"""+p_owner+"""' AND 
                                                   TABLE_NAME='"""+self.v_nome_oggetto+"""'
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
        elif self.v_tipo_oggetto in ('PACKAGE','PACKAGE BODY','FUNCTION','PROCEDURE') :
            # creo un modello dati con 1 colonna (dove nell'intestazione ci metto il nome dell'oggetto)
            self.db_oggetto_tree_model = QStandardItemModel()
            self.db_oggetto_tree_model.setHorizontalHeaderLabels([self.v_nome_oggetto])            

            ###
            # prima radice con il nome dell'oggetto
            ###
            v_root_codice = QStandardItem('Code')

            # leggo il sorgente e lo metto dentro una lista!
            self.v_cursor_db_obj.execute("""SELECT UPPER(TEXT) as TEXT, LINE FROM ALL_SOURCE"""+p_link+""" WHERE OWNER='"""+p_owner+"""' AND NAME='"""+self.v_nome_oggetto+"""' AND TYPE='"""+self.v_tipo_oggetto+"""' ORDER BY LINE""")
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
                                        self.db_oggetto_tree.selectionModel().select(v_item1.index(), QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)                                    
                                        v_1a_volta = False
                                    # ...altrimenti aggiungo la riga alla selezione corrente
                                    else:                                        
                                        self.db_oggetto_tree.selectionModel().select(v_item1.index(), QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)                                                                        
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
                                                    self.db_oggetto_tree.selectionModel().select(v_item2.index(), QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)                                    
                                                    v_1a_volta = False
                                                # ...altrimenti aggiungo la riga alla selezione corrente
                                                else:                                        
                                                    self.db_oggetto_tree.selectionModel().select(v_item2.index(), QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)                                                                        
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
                                            WHERE  OWNER = '"""+self.e_user_name+"""' AND
                                                   CONSTRAINT_TYPE='R' AND 
                                                   R_CONSTRAINT_NAME IN (SELECT CONSTRAINT_NAME
                                                                         FROM   ALL_CONSTRAINTS
                                                                         WHERE  TABLE_NAME='"""+self.v_nome_oggetto+"""' AND 
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

    def slot_popup_menu_insert_in_editor(self):
        """
           Evento che si scatena quando sull'albero dell'object viewer si preme il tasto destro su una funzione di package e si seleziona la voce "Insert in editor".
           Se il tipo di oggetto presente in object viewer è del tipo procedura-funzione e package, viene presa la procedura-funzione
           selezionata e viene riportata all'interno dell'editor attivo, scrivendo il nome del package, seguito dal nome della procedura-funzione
           e dall'elenco dei parametri
           Attenzione! Se la stessa procedura-funzione è presente più volte all'interno del package, ne verrà presa solo la prima ricorrenza
        """        
        if self.v_tipo_oggetto not in ('PACKAGE BODY','PACKAGE','PROCEDURE','FUNCTION'):            
            return 'ko'

        # carico l'oggetto di classe MSql_win2_class attivo in questo momento (così ho tutte le sue proprietà)        
        o_MSql_win2 = self.oggetto_win2_attivo()        

        if self.v_nome_oggetto != '' and o_MSql_win2 != None:                        
            # imposto le var di lavoro (nel caso di funzione-procedura che viene presa da un package, nel risultato ci metto il nome del package)
            if self.v_tipo_oggetto in ('PACKAGE BODY','PACKAGE'):
                v_risultato = self.v_nome_oggetto + '.'
            else:
                v_risultato = ''
            v_spazi = 0
            # leggo l'oggetto che contiene procedure-funzioni alla ricerca dell'elemento che ha selezionato l'utente
            for ele in self.oggetti_db_lista_proc_func:                                
                # se trovo l'elemento selezionato....inizio a caricarlo nella stringa di risultato
                if ele.nome_definizione == self.v_nome_foglia:                                        
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
    
    def slot_popup_menu_oggetto_tree(self, p_position):
        """
           Apre il menu popup sulle righe del tree dell'object viewer
        """
        v_indexes = self.db_oggetto_tree.selectedIndexes()
        
        if len(v_indexes) > 0:                    
            v_current_index = v_indexes[0]            
            v_parent_index = v_current_index.parent()            
            if v_parent_index.data() is None:                                
                pass
            # l'apertura del menu avviene solo se siamo sotto una determinata serie di rami
            # e viene riciclato il codice già scritto per il la sezione dell'elenco oggetti            
            elif v_parent_index.data() in ('Constraints','Triggers','Indexes'):                                
                self.v_popup_menu_zone = 'FOGLIA_ALBERO'
                self.v_nome_foglia = v_current_index.data()
                # determino il tipo dell'oggetto
                if v_parent_index.data() == 'Constraints':
                    self.v_tipo_foglia = 'CHECK_KEY'
                elif v_parent_index.data() == 'Triggers':
                    self.v_tipo_foglia = 'TRIGGER'
                elif v_parent_index.data() == 'Indexes':
                    self.v_tipo_foglia = 'INDEXES'
                else:
                    message_error(QCoreApplication.translate('MSql_win1','Error during decode object type!'))
                # richiamo la creazione e gestione del popup menu
                # notare come all'interno di questa gestione verranno usate le var di nome e tipo oggetto                
                self.popup_menu_object(p_position,'FOGLIA')
            # in questo caso siamo nell'object viewer del package
            elif v_parent_index.data() in ('Code'):
                self.v_popup_menu_zone = 'FOGLIA_ALBERO'
                self.v_nome_foglia = v_current_index.data()
                self.v_tipo_foglia = 'FUNCTION'                
                # richiamo la creazione e gestione del popup menu
                # notare come all'interno di questa gestione verranno usate le var di nome e tipo oggetto                
                self.popup_menu_object(p_position,'FOGLIA')                                
            # in questo caso siamo nell'object viewer di una tabella e si è selezionato un campo
            elif v_parent_index.data() in ('Fields'):
                self.v_popup_menu_zone = 'CAMPO_TABELLA'
                self.v_nome_foglia = v_current_index.data()
                self.v_tipo_foglia = v_indexes[1].data() + v_indexes[2].data() + chr(10) + v_indexes[3].data()                                                                                                                  
                # richiamo la creazione e gestione del popup menu
                # notare come all'interno di questa gestione verranno usate le var di nome e tipo oggetto                
                self.popup_menu_object(p_position,'CAMPO_TABELLA')                                
    
    def richiesta_connessione_specifica(self):    
        """
            Apre finestra per richiedere una connessione specifica
        """            
        # inizializzo le strutture grafice e visualizzo la dialog per richiedere una password di conferma prima di procedere
        self.dialog_connect = QDialog()
        self.win_dialog_connect = Ui_connect_window()
        self.win_dialog_connect.setupUi(self.dialog_connect)       
        centra_window_figlia(self, self.dialog_connect)
        
        # imposto la maschera di editazione sul campo user in modo sia maiuscolo                        
        self.win_dialog_connect.e_user.textEdited.connect(self.slot_e_user_to_upper) 
        self.win_dialog_connect.e_proxy.textEdited.connect(self.slot_e_proxy_to_upper) 

        # creo evento riferito al bottone di connessione
        self.win_dialog_connect.b_connect.clicked.connect(self.richiesta_connessione_specifica_accept)                
        self.dialog_connect.show()        

    def slot_e_user_to_upper(self):
        """
           Il nome utente viene impostato sempre maiuscolo
        """
        self.win_dialog_connect.e_user.setText(self.win_dialog_connect.e_user.text().upper())
    
    def slot_e_proxy_to_upper(self):
        """
           Il nome proxy viene impostato sempre maiuscolo
        """
        self.win_dialog_connect.e_proxy.setText(self.win_dialog_connect.e_proxy.text().upper())

    def richiesta_connessione_specifica_accept(self):
        """
           Eseguo connessione specifica
        """           
        # controllo che tutte le info siano state inserite
        if self.win_dialog_connect.e_user.displayText() == '' or self.win_dialog_connect.e_password.displayText() == '' or self.win_dialog_connect.e_tns.displayText() == '':
            message_error(QCoreApplication.translate('MSql_win1','Not all the requested data has been entered!'))            
            return 'ko'

        # eseguo la connessione
        self.e_user_name = self.win_dialog_connect.e_user.displayText()
        self.e_user_proxy = self.win_dialog_connect.e_proxy.displayText()
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
        self.my_app = win_preferences_class(v_global_work_dir + 'MSql.ini', v_global_work_dir + 'MSql_connections.ini')        
        centra_window_figlia(self, self.my_app)
        self.my_app.show()   

    def slot_info(self):
        """
           Apre la window delle info
        """           
        global v_global_work_dir         

        self.win_program_info = QDialog()
        self.ui_program_info = Ui_program_info()
        self.ui_program_info.setupUi(self.win_program_info)
        centra_window_figlia(self, self.win_program_info)

        # Se il programma è in esecuzione da pyinstaller...cerco la data di creazione dell'eseguibile MSql.exe e la imposta nel titolo
        if getattr(sys, 'frozen', False):             
            v_build_timestamp = time.strftime("%Y-%m-%d",time.localtime(os.path.getmtime(sys.executable)))        
            self.win_program_info.setWindowTitle(f"MSql Info. Build time: {v_build_timestamp}")

        self.win_program_info.show()                        
        
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
        centra_window_figlia(self, self.my_app)
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
            centra_window_figlia(self, self.win_history)
            self.win_history.show()     

    def slot_history_insert_in_editor(self):
        """
           Prende la riga selezionata nell'history e la porta dentro l'editor corrente
        """       
        # prendo indice dalla tabella (in pratica la cella che contiene l'id della riga dell'history)
        try:
            index = self.win_history.o_lst1.selectedIndexes()[3]           
        except:
            message_error(QCoreApplication.translate('MSql_win1','Select a row!'))
            return 'ko'
        # ricerco il valore dell'istruzione corrispondente e lo carico nell'editor
        o_MSql_win2 = self.oggetto_win2_attivo()
        if o_MSql_win2 != None:
            v_risultato = self.win_history.return_instruction(self.win_history.o_lst1.model().data(index))                        
            # il testo che prendo dall'history ha formato eol Linux, e se necessario
            # va convertito in Windows (a seconda dell'impostazione dell'editor di destinazione)
            if o_MSql_win2.setting_eol == 'W' and '\r\n' not in v_risultato:
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
            centra_window_figlia(self, self.win_preferred_sql)
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

    def slot_compare_last_two_text_editor(self):        
        """
           Esegue la comparazione dei testi contenuti nei due ultimi text editor aperti
           e apre un nuovo text editor con il lexer delle differenze (sola lettura)
        """
        global o_global_preferences        

        # se non ci sono più di 2 window aperte, il compare non va eseguito
        if len(self.mdiArea.subWindowList()) < 2:
            message_error(QCoreApplication.translate('MSql_win1','For compare you must have two editor open or more!'))
            return 'ko'

        # prendo le ultime due finestre aperte 
        sub_windows = self.mdiArea.subWindowList()                 
        v_ultima_windows = sub_windows[-1] 
        v_ultimo_titolo = ''
        v_penultima_windows = sub_windows[-2] 
        v_penultimo_titolo = ''
        
        # scorro la lista-oggetti-editor fino a quando non trovo l'oggetto che ha lo stesso titolo dell'ultima window
        # di fatto ricerco l'oggetto e_sql che contiene l'editor
        for i in range(0,len(self.o_lst_window2)):
            if not self.o_lst_window2[i].v_editor_chiuso:
                if self.o_lst_window2[i].objectName() ==v_ultima_windows.objectName():                        
                    v_ultimo_editor = self.o_lst_window2[i].e_sql
                    v_ultimo_titolo = self.o_lst_window2[i].windowTitle()

        # scorro la lista-oggetti-editor fino a quando non trovo l'oggetto che ha lo stesso titolo della penultima window
        # di fatto ricerco l'oggetto e_sql che contiene l'editor
        for i in range(0,len(self.o_lst_window2)):
            if not self.o_lst_window2[i].v_editor_chiuso:
                if self.o_lst_window2[i].objectName() ==v_penultima_windows.objectName():                        
                    v_penultimo_editor = self.o_lst_window2[i].e_sql
                    v_penultimo_titolo = self.o_lst_window2[i].windowTitle()
        
        # imposto il font
        v_split = o_global_preferences.font_editor.split(',')                        
        v_font = QFont(str(v_split[0]),int(v_split[1]))
        
        # apro il differ 
        viewer = classDiffViewer(o_global_preferences.dark_theme,
                                 o_global_preferences.tab_size,
                                 o_global_preferences.remember_window_pos,
                                 v_ultimo_editor.text(), 
                                 v_penultimo_editor.text(), 
                                 v_ultimo_titolo, 
                                 v_penultimo_titolo,
                                 v_font)                            
        viewer.setWindowTitle(QCoreApplication.translate('MSql_win1','Editor Compare'))
        viewer.setWindowIcon(QIcon("icons:MSql.ico"))        
        viewer.show()

    def slot_import_export_oracle_to_sqlite(self):
        """
           Apre la window per eseguire import dati da Oracle verso SQLite
        """        
        global v_global_connesso, v_global_work_dir
        from import_export_oracle_to_sqlite import import_export_class
        
        if not v_global_connesso:
            message_error(QCoreApplication.translate('MSql_win1','No connection!'))
            return 'ko'
        
        # apertura della window di import-export
        self.o_import_export = import_export_class(self.e_user_name, self.e_password, self.e_server_name, v_global_work_dir)        
        centra_window_figlia(self, self.o_import_export)
        self.o_import_export.show()

    def slot_import_export_sqlite_to_excel(self):
        """
           Apre la window per eseguire export dei dati da SQLite a Excel
        """        
        from import_export_sqlite_to_excel import import_export_class
        
        # apertura della window di import-export
        self.o_import_export = import_export_class()        
        centra_window_figlia(self, self.o_import_export)
        self.o_import_export.show()

    def slot_import_export_excel_to_oracle(self):
        """
           Apre la window per eseguire import dei dati da Excel a Oracle
        """        
        global v_global_connesso
        from import_export_excel_to_oracle import import_export_class
        
        if not v_global_connesso:
            message_error(QCoreApplication.translate('MSql_win1','No connection!'))
            return 'ko'
        
        # apertura della window di import-export
        self.o_import_export = import_export_class(self.e_user_name, self.e_password, self.e_server_name)        
        centra_window_figlia(self, self.o_import_export)
        self.o_import_export.show()        

    def slot_import_export_sqlite_to_oracle(self):
        """
           Apre la window per eseguire import dei dati da SQLite a Oracle
        """        
        global v_global_connesso, v_global_work_dir
        from import_export_sqlite_to_oracle import import_export_class
        
        if not v_global_connesso:
            message_error(QCoreApplication.translate('MSql_win1','No connection!'))
            return 'ko'
        
        # apertura della window di import-export
        self.o_import_export = import_export_class(self.e_user_name, self.e_password, self.e_server_name, v_global_work_dir)        
        centra_window_figlia(self, self.o_import_export)
        self.o_import_export.show()        

    def slot_sqlite_viewer(self):
        """
           Apre la window visualizzatore contenuto di un database-file SQLite
        """        
        global v_global_connesso, v_global_work_dir
        from sqlite_viewer import sqlite_viewer_class
                
        self.o_sqlite_viewer = sqlite_viewer_class()        
        centra_window_figlia(self, self.o_sqlite_viewer)
        self.o_sqlite_viewer.show()                

    def slot_explore_database_link(self):
        """
           Apre la window per esplorare i database link           
        """
        global v_global_connesso, v_global_connection
        from dblink_viewer import classDBLinkExplorer

        if not v_global_connesso:
            message_error(QCoreApplication.translate('MSql_win1','No connection!'))
            return 'ko'
        
        self.o_dblink_viewer = classDBLinkExplorer(v_global_connection)
        self.o_dblink_viewer.object_selected.connect(self.slot_explore_database_link_double_click)
        centra_window_figlia(self, self.o_dblink_viewer)
        self.o_dblink_viewer.show()

    def slot_explore_database_link_double_click(self, p_current_link, p_current_obj_type, p_current_obj_name):
        """
           Intercetta il click di scelta sulla window di navigazione dei database link e scrive dentro l'editor l'oggetto scelto
        """
        # ricerco l'editor attivo e inserisco quanto è stato selezionato con doppio click
        o_MSql_win2 = self.oggetto_win2_attivo()
        if o_MSql_win2 != None:            
            o_MSql_win2.e_sql.insert(p_current_obj_name+'@'+p_current_link)        

    def slot_text_functions(self,p_testo):
        """
           Apre la window per la gestione delle funzioni di testo
        """
        from text_functions import class_text_functions

        self.o_text_funtions = class_text_functions(p_testo)        
        centra_window_figlia(self, self.o_text_funtions)
        self.o_text_funtions.show()

    def slot_mostra_file_system_dock(self):
        """
           Mostra/nasconde il dock del file system
        """
        if self.dockWidget_3.isVisible():
            self.dockWidget_3.hide()
        # quando viene mostrato, esegue il refresh del file system
        else:
            self.slot_file_system_refresh()
            self.dockWidget_3.show()

    def slot_file_system_double_click(self, p_index):
        """
            Evento che si scatena quando viene fatto doppio click su un file all'interno del file system
        """
        # mappo l'indice dal proxy al modello sorgente
        source_index = self.file_system_proxy_model.mapToSource(p_index)
        # uso l'indice sorgente per ottenere il percorso del file
        v_file_name = self.file_system_model.filePath(source_index)    
        # se è un file, lo apro nell'editor
        if v_file_name != '':
            # apro il file di testo con MSql
            if v_file_name.lower().endswith(('.msql', '.sql', '.txt', '.pls', '.plb', '.csv', '.json','.trg')):
                v_titolo, v_contenuto_file, v_codifica_utf8 = self.openfile(v_file_name)
                v_azione = QAction()
                v_azione.setText('Open_db_obj')
                self.smistamento_voci_menu(v_azione, v_titolo, v_contenuto_file, v_codifica_utf8)            
            # ... altrimenti apro un file che non è di testo con applicazione predefinita di windows
            else:
                if os.name == "posix":
                    subprocess.Popen(["xdg-open", v_file_name])    
                else:
                    os.startfile(v_file_name)          

    def slot_file_system_refresh(self):
        """
           Esegue il refresh del file system con filtro regex opzionale.
           Chiamata dal bottone b_refresh.
        """
        # Crea il modello del file system
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())

        # Crea il proxy model personalizzato
        self.file_system_proxy_model = MyFileExtensionFilterProxyModel()
        self.file_system_proxy_model.setSourceModel(self.file_system_model)

        # Legge l'eventuale testo di ricerca
        search_text = ""
        if hasattr(self, 'e_file_system_search'):
            search_text = self.e_file_system_search.text().strip()

        # Applica il filtro se presente
        if search_text:
            try:
                regex = QRegularExpression(search_text, QRegularExpression.PatternOption.CaseInsensitiveOption)
                self.file_system_proxy_model.setFilterRegularExpression(regex)
            except Exception as e:
                print(f"Regex non valida: {e}")
                self.file_system_proxy_model.setFilterRegularExpression(QRegularExpression(""))
        else:
            self.file_system_proxy_model.setFilterRegularExpression(QRegularExpression(""))

        # Collega il modello alla vista e indica di ordinare in ordine crescente per nome file
        self.o_file_system.setModel(self.file_system_proxy_model)
        self.o_file_system.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # Imposta la cartella iniziale (desktop o quella salvata)
        if o_global_preferences.open_dir != '':
            v_path = o_global_preferences.open_dir
        else:
            v_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation)

        # Ottieni l'indice dal modello di origine
        source_index = self.file_system_model.index(v_path)
        proxy_index = self.file_system_proxy_model.mapFromSource(source_index)

        # Mostra la cartella e imposta larghezza colonne
        self.o_file_system.expand(proxy_index)
        self.o_file_system.scrollTo(proxy_index)
        self.o_file_system.setCurrentIndex(proxy_index)
        self.o_file_system.setColumnWidth(0, 250)

    def slot_calculator(self):
        """
           Apre la calcolatrice di sistema
        """        
        from calculator import run_calculator

        self.win_calculator = run_calculator()        
        self.win_calculator.closed.connect(self.slot_calculator_close)
        centra_window_figlia(self, self.win_calculator)

    def slot_calculator_close(self):
        """
           Evento che si scatena quando la calcolatrice viene chiusa
        """        
        self.win_calculator = None
        
#  _     _______  _______ ____  
# | |   | ____\ \/ / ____|  _ \ 
# | |   |  _|  \  /|  _| | |_) |
# | |___| |___ /  \| |___|  _ < 
# |_____|_____/_/\_\_____|_| \_\
#                              
# Classe che personalizza il comportamento del lexer di qscintilla 
class My_MSql_Lexer(QsciLexerSQL):
    """
        Questa classe amplifica il dizionario di default del linguaggio SQL presente in QScintilla.
        In pratica aggiunge tutti i nomi di tabelle, viste, procedure, ecc. in modo vengano evidenziati
        Si basa sulla lista v_global_my_lexer_keywords che viene caricata quando ci si connette al DB
        In base al valore di index è possibile settare parole chiave di una determinata categoria
        1=parole primarie, 2=parole secondarie, 3=commenti, 4=classi, ecc.. usato 8 (boh!) 

        Il parametro p_mini_map, se passato a True indica che il lexer è quello della mini mappa
    """
    def __init__(self, p_editor, p_mini_map):        
        super(My_MSql_Lexer, self).__init__()  

        # salvo il puntatore all'editor all'interno del lexer
        self.p_editor = p_editor      

        # editor normale...
        if not p_mini_map:
            # attivo le righe verticali che segnano le indentazioni (questa è anche una voce nel menu view)
            self.p_editor.setIndentationGuides(o_global_preferences.indentation_guide)                            
        
            # attivo i margini con + e - 
            self.p_editor.setFolding(p_editor.FoldStyle.BoxedTreeFoldStyle, 2) 
        
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
        
            # imposto i numeri di riga
            self.p_editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)        
            self.p_editor.setMarginsFont(QFont("Courier New",9))                                               
            self.p_editor.setMarginLineNumbers(0, True)
            self.p_editor.setMarginWidth(0, "00000")  # 5 cifre max
        
            # attivo il matching sulle parentesi con uno specifico colore
            self.p_editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)            
            self.p_editor.setMatchedBraceBackgroundColor(QColor("#80ff9900"))
        
            # attivo il multiediting (cioè la possibilità, una volta fatta una selezione verticale, di fare un edit multiplo)        
            self.p_editor.SendScintilla(self.p_editor.SCI_SETADDITIONALSELECTIONTYPING, 1)        
            v_offset = self.p_editor.positionFromLineIndex(0, 7) 
            self.p_editor.SendScintilla(self.p_editor.SCI_SETSELECTION, v_offset, v_offset)        
            v_offset = self.p_editor.positionFromLineIndex(1, 5)
            self.p_editor.SendScintilla(self.p_editor.SCI_ADDSELECTION, v_offset, v_offset)
            v_offset = self.p_editor.positionFromLineIndex(2, 5)
            self.p_editor.SendScintilla(self.p_editor.SCI_ADDSELECTION, v_offset, v_offset)    

            # attivo autocompletamento durante la digitazione 
            # (comprende sia le parole del documento corrente che quelle aggiunte da un elenco specifico)
            # attenzione! Da quanto ho capito, il fatto di avere attivo il lexer con linguaggio specifico (sql) questo prevale
            # sul funzionamento di alcuni aspetti dell'autocompletamento....quindi ad un certo punto mi sono arreso con quello che
            # sono riuscito a fare
            self.v_api_lexer = QsciAPIs(self)            
            # aggiungo tutti i termini di autocompletamento (si trovano all'interno di una tabella che viene generata a comando)
            self.p_editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)                
            self.carica_dizionario_per_autocompletamento()                
            # indico dopo quanti caratteri che sono stati digitati dall'utente, si deve attivare l'autocompletamento
            # se è stato richiesto di disattivarlo alzo la soglia in modo che di fatto risulta disattivato
            if o_global_preferences.autocompletation:
                self.p_editor.setAutoCompletionThreshold(3)  
            else:
                self.p_editor.setAutoCompletionThreshold(1000)  
            # attivo autocompletamento sia per la parte del contenuto del documento che per la parte di parole chiave specifiche
            self.p_editor.autoCompleteFromAll()                        

            # attivo il folding (+ e - sul margine sinistro)
            self.setFoldCompact(False)
            self.setFoldComments(True)
            self.setFoldAtElse(True)     

            # attivo i segnalibri dentro il margine tra i numeri di riga e il folding (scalo la dimensione dell'icona a 16px)                    
            # riferirsi eventualmente alla documentazione https://qscintilla.com/#margins/margin_basics/symbol_margin
            self.p_editor.markerDefine(QImage("icons:green_dot.png").scaled(QSize(16, 16)), 0)  
            
            # imposto gli elementi che servono all'interno dell'editor per attivare la funzione
            # tale per cui quando utente fa doppio click su una parola, vengono evidenziate tutte 
            # le parole uguali presenti nel testo!         
            #self.p_editor.MouseButtonDblClick.connect(self.cambio_di_selezione_testo)        
            #self.selection_lock = False
            #self.SELECTION_INDICATOR = 4    
        # se siamo in apertura della mini mappa...
        else:
            # nascondo il margine del folding e numeri di riga
            self.p_editor.setMarginWidth(1, 0)
            # imposto a sola lettura
            self.p_editor.setReadOnly(True)
            # disattivo la possibilità di selezionare del testo
            self.p_editor.SendScintilla(QsciScintilla.SCI_SETSEL, -1, -1)
            # disattivo la scrollbar orizzontale inferiore
            self.p_editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # imposto no wrapmode che significa non fare andare a capo le righe di testo in modo automatico
            self.p_editor.setWrapMode(QsciScintilla.WrapMode.WrapNone)
            # tabulatore (in base alle preferenze...di base 2 caratteri)
            self.p_editor.setTabWidth(int(o_global_preferences.tab_size))   
            
        # imposto il font dell'editor in base alle preferenze 
        if o_global_preferences.font_editor != '':
            v_split = o_global_preferences.font_editor.split(',')            
            if not p_mini_map:
                v_font = QFont(str(v_split[0]),int(v_split[1]))
            else:
                v_font = QFont(str(v_split[0]),3)
            if len(v_split) > 2 and v_split[2] == ' BOLD':
                v_font.setBold(True)
            self.setFont(v_font)    
        
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


#
#  _____ ____ ___ _____ ___  ____  
# | ____|  _ \_ _|_   _/ _ \|  _ \ 
# |  _| | | | | |  | || | | | |_) |
# | |___| |_| | |  | || |_| |  _ < 
# |_____|____/___| |_| \___/|_| \_\
#                                 
# Classe che contiene tutti i componenti dell'editor
class MSql_win2_class(QMainWindow, Ui_MSql_win2):
    """
        Editor SQL
    """       
    def __init__(self, 
                 p_titolo, # Titolo della window-editor
                 p_contenuto_file,  # Eventuale contenuto da inserire direttamente nella parte di editor
                 p_codifica_file,  # Eventuale codifica del file (se T=UTF-8)
                 o_MSql_win1_class): # Puntatore alla classe principale (window1)                                  
        global o_global_preferences  
        global v_global_work_dir      

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win2_class, self).__init__()        
        # includo tutte le componenti grafiche definite nel file ui
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

        # splitter che separa l'editor dalla mini mappa (rapporto 15-1)                
        self.splitter_2.setStretchFactor(0,15)        
        self.splitter_2.setStretchFactor(1,1)        
        # splitter che separa verticalmente l'editor dall'output: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello di output
        self.splitter.setStretchFactor(0,8)        
        self.splitter.setStretchFactor(1,2)    
        # splitter che separa orizzontalmente l'output all'interno del tab con la sezione di ricerca stringa dell'apposita sezione
        self.splitter_3.setStretchFactor(0,9)        
        self.splitter_3.setStretchFactor(1,1)    
        # imposto visivamente la maniglia degli splitter con una linea grigia
        self.splitter.setStyleSheet(""" QSplitter::handle { background-color: #667078; width: 1px; /* Larghezza della maniglia */ } """)

        ###
        # IMPOSTAZIONI DELL'EDITOR SCINTILLA (Notare come le impostazioni delle proprietà siano stato postate nella definizione del lexer)
        ###
        # attivo UTF-8 (se richiesto)
        if p_codifica_file:
            self.e_sql.setUtf8(True)                                                        
            self.setting_utf8 = True
        else:
            self.setting_utf8 = False
        # attivo il lexer per evidenziare il codice del linguaggio SQL. Notare come faccia riferimento ad un oggetto che a sua volta personalizza il 
        # dizionario del lexer SQL, aggiungendo (se sono state caricate) le parole chiave di: tabelle, viste, package, ecc.
        self.v_lexer = My_MSql_Lexer(self.e_sql, False)                
        # attivo il lexer sull'editor
        self.e_sql.setLexer(self.v_lexer)
        
        # attivo il lexer sulla mini mappa 
        self.v_lexer_mini_map = My_MSql_Lexer(self.e_sql_mini_map, True)                
        self.e_sql_mini_map.setLexer(self.v_lexer_mini_map)
                
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
            self.e_sql.setEolMode(QsciScintilla.EolMode.EolWindows)                
        else:
            self.e_sql.setEolMode(QsciScintilla.EolMode.EolUnix)                
        # aggiorno la statusbar con l'impostazione di eol
        self.aggiorna_statusbar()

        # visualizzo o meno il carattere di end of line in base alla preferenza
        self.set_show_end_of_line()      
        # imposto la var della indentation guide
        self.v_indentation_guide = o_global_preferences.indentation_guide  

        ###
        # DICHIARAZIONE VAR GENERALI
        ###

        # inizializzo var che contiene la select corrente
        # la select corrente è quella che l'utente seleziona nell'editor e da cui si parte per aggiungere 
        # altre caratteristiche tramite i popup menu sulle colonne
        self.v_select_corrente = ''
        self.v_plsql_corrente = ''        
        # select effettivamente eseguita dal motore Oracle
        self.v_select_eseguita = ''
        self.v_set_rowcount = False
        # inizializzo var che indica che l'esecuzione è andata ok
        self.v_esecuzione_ok = False          
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
        # array degli highlights (usato nell'ambito delle ricerche di stringhe)     
        self.v_array_indicator = []

        ###
        # Precaricamento (se passato un contenuto di file) 
        ###
        v_cur_y, v_cur_x = 0,0
        if p_contenuto_file is not None:        
            # imposto editor con quello ricevuto in ingresso
            self.e_sql.setText(p_contenuto_file)            
            self.e_sql_mini_map.setText(p_contenuto_file)            
            # chiedo allo storico di darmi eventuale posizione di dove si trovava il cursore ultima volta
            if o_global_preferences.remember_text_pos:
                v_cur_y, v_cur_x = read_files_history(v_global_work_dir+'MSql.db', p_titolo)            
                
        # mi posiziono sulla prima riga (la posizione X viene al momento forzata a zero!)
        self.e_sql.setCursorPosition(v_cur_y,0)
        self.e_sql_mini_map.setCursorPosition(v_cur_y,0)
        self.v_mini_map_visible = True

        # var che indica che il testo è stato modificato
        #self.e_sql.insert("begin dbms_output.put_line('ciao'); end;")
        self.v_testo_modificato = False         

        # evidenzio i colori se richiesto
        self.set_emphasis()
       
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
        # Attenzione! L'attivazione del drop delega la gestione a QScintilla che non è per niente bella!
        #             Per cui il drag&drop dall'object navigator o altri elementi interni viene gestita tramite
        #             la funzione sottostante eventFilter.
        #             Il drag&drop di qualcosa che viene dall'esterno (tipicamente l'apertura di un file da esplora risorse)
        #             avviene disattivando il drop sull'editor quando si disattiva la finestra per poi riattivarlo quando si attiva....
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

        # se richiesto dalle preferenze, creazione di un timer per la creazione di un backup del testo 
        if o_global_preferences.autosave_snapshoot_interval != 0:             
            self.autosave_snapshoot_timer = QTimer(self)
            self.autosave_snapshoot_timer.timeout.connect(self.slot_save_snapshoot)
            self.autosave_snapshoot_timer.start(o_global_preferences.autosave_snapshoot_interval*1000) 

        # attivo slot sul cambiamento di testo (es. digitazione di testo)
        self.e_sql.textChanged.connect(self.slot_mini_map_copy_text)
        # attivo slot che dal margine, segna i segnalibri
        self.e_sql.setMarginSensitivity(1, True)
        self.e_sql.marginClicked.connect(self.slot_add_bookmark)
        # attivo slot che tiene sincronizzato l'editor con la mini mappa tramite le scrollbar
        self.e_sql.verticalScrollBar().valueChanged.connect(self.slot_mini_map_sync_scrollbars) 
        self.e_sql_mini_map.verticalScrollBar().valueChanged.connect(self.slot_mini_map_sync_scrollbars) 
        # attivo slot che quando viene cliccata la mini mappa riposiziona il testo 
        self.e_sql_mini_map.selectionChanged.connect(self.slot_mini_map_click)   
        # variabile per controllare il loop sulle scrollbar tra editor e minimappa
        self.v_scrollbar_loop = False        

    def slot_mini_map_click(self):
        """
           Quando viene cliccato il testo sulla mini mappa riposiziona il cursore sull'editor
           Attenzione! Se il testo cliccato in mini mappa è già visualizzato nell'editor, non si sposta nulla
        """
        if self.v_mini_map_visible:
            # prendo coordinate cursore della mini mappa
            v_line, v_pos = self.e_sql_mini_map.getCursorPosition()        
            # riposiziono cursore nell'editor
            self.e_sql.setCursorPosition(v_line,v_pos)
            # blocco i segnali sulla mini mappa
            self.e_sql_mini_map.blockSignals(True)                        
            # pulisco eventuale selezione sulla mini mappa
            self.e_sql_mini_map.setSelection(v_line,0,v_line,1)
            # posiziono il focus sull'editor
            self.e_sql.setFocus()
            # riattivo i segnali sulla mini mappa
            self.e_sql_mini_map.blockSignals(False)                        
    
    def slot_mini_map_copy_text(self): 
        """
           Copia il testo dell'editor nella mini mappa
           Notare come vengono bloccati gli eventi perché altrimenti si creano riposizionamenti indesiderati!
        """         
        if self.v_mini_map_visible:
            # blocco i segnali sugli oggetti
            self.e_sql.blockSignals(True)                        
            self.e_sql_mini_map.blockSignals(True)      
            self.e_sql.verticalScrollBar().blockSignals(True)                        
            self.e_sql_mini_map.verticalScrollBar().blockSignals(True)      
            
            # sincronizzo il testo tra l'editor e la mini mappa e posiziono il cursore correttamente sulla mini mappa
            self.e_sql_mini_map.setText(self.e_sql.text()) 
            v_line, v_pos = self.e_sql.getCursorPosition()
            self.e_sql_mini_map.setCursorPosition(v_line, 0)                        
            
            # sincronizzo la posizione delle scrollbar tra editor e mini mappa
            self.e_sql_mini_map.verticalScrollBar().setValue( self.e_sql.verticalScrollBar().value() )
            
            # riattivo i segnali sulle scrollbar
            self.e_sql.blockSignals(False)                        
            self.e_sql_mini_map.blockSignals(False)          
            self.e_sql.verticalScrollBar().blockSignals(False)                        
            self.e_sql_mini_map.verticalScrollBar().blockSignals(False)      
        
    def slot_mini_map_sync_scrollbars(self, value): 
        """
           Quando si agisce sulla scrollbar dell'editor o della mini mappa, sposta il testo.           
           Da notare che è stato adottato un meccanismo per impedire che ci sia il ping-pong tra le due scrollbar
        """            
        if self.v_mini_map_visible:                   
            if self.sender() == self.e_sql.verticalScrollBar():                                             
                if not self.v_scrollbar_loop:
                    self.v_scrollbar_loop = True                 
                    self.e_sql_mini_map.verticalScrollBar().setValue(value)
                    self.v_scrollbar_loop = False
            elif self.sender() == self.e_sql_mini_map.verticalScrollBar():                                                         
                if not self.v_scrollbar_loop:
                    self.v_scrollbar_loop = True                 
                    self.e_sql.verticalScrollBar().setValue(value)                                                        
                    self.v_scrollbar_loop = False
        
    def slot_mini_map_visible(self):
        """
           Attiva o disattiva la mini mappa
        """
        if self.v_mini_map_visible:
            self.v_mini_map_visible = False
            self.e_sql_mini_map.setText('')
            self.e_sql_mini_map.setVisible(False)
        else:
            self.v_mini_map_visible = True
            self.e_sql_mini_map.setText(self.e_sql.text())
            self.e_sql_mini_map.setVisible(True)

    def eventFilter(self, source, event):
        """
           Gestione di eventi personalizzati sull'editor (overwrite, drag&drop, F12) e sulla tabella dei risultati
           Da notare come un'istruzione di return False indirizza l'evento verso il suo svolgimento classico
        """      
        global v_global_connection
        
        # controllo se l'autocompletamento è aperto (poplist con i suggerimenti...)
        if event.type() == QEvent.Type.KeyPress and source is self.e_sql and self.e_sql.SendScintilla(QsciScintilla.SCI_AUTOCGETCURRENT) != -1:  
            # se premuto invio, non lo accetto come conferma della voce proposta e chiudo l'autocompletamento
            if event.key() == Qt.Key.Key_Return:                                                
                self.e_sql.SendScintilla(QsciScintilla.SCI_AUTOCCANCEL)
                return True
            # altrimenti se premuto il tab, accetto quanto proposto da autocompletamento
            elif event.key() == Qt.Key.Key_Tab:                
                self.e_sql.SendScintilla(QsciScintilla.SCI_AUTOCCOMPLETE)
                return True

        # intercetto il cambio di focus e cambio il titolo della window principale di MSql così che sulla barra di Windows risulti 
        # il titolo dell'editor corrente
        if event.type() == QEvent.Type.FocusIn and source is self.e_sql:
            self.link_to_MSql_win1_class.setWindowTitle(titolo_window(self.objectName()))

        # individio la disattivazione della window e disattivo il drop sulla parte di editor in modo possa gestire 
        # i drop di un file che viene trascinato sull'app. Il drop del file viene gestito tramite il controllo dell'evento sulla window principale
        if event.type() == QEvent.Type.WindowDeactivate:
            self.e_sql.setAcceptDrops(False)                     

        # individio l'attivazione della window e riattivo la gestione del drop sulla parte di editor in modo possa gestire         
        if event.type() == QEvent.Type.WindowActivate:
            self.e_sql.setAcceptDrops(True)                     
        
        # individuo tasto destro del mouse sulla tabella dei risultati        
        if event.type() == QEvent.Type.MouseButtonPress and event.buttons() == Qt.MouseButton.RightButton and source is self.o_table.viewport():            
            self.tasto_destro_o_table(event)      
            return True      

        # individuo la pressione di un tasto sull'editor
        if event.type() == QEvent.Type.KeyPress and source is self.e_sql:
            # premuta parentesi aperta....inserisco parentesi chiusa
            if event.key() == Qt.Key.Key_ParenLeft:
                self.auto_insert('(')                
            # premuta parentesi chiusa....valuto se passare al prossimo carattere
            if event.key() == Qt.Key.Key_ParenRight:
                self.auto_insert(')')                
            # premuta parentesi aperta....inserisco parentesi chiusa
            if event.key() == Qt.Key.Key_BracketLeft:
                self.auto_insert('[')                
            # premuta parentesi chiusa....valuto se passare al prossimo carattere
            if event.key() == Qt.Key.Key_BracketRight:
                self.auto_insert(']')                
            # premuta parentesi aperta....inserisco parentesi chiusa
            if event.key() == Qt.Key.Key_BraceLeft:
                self.auto_insert('{')                
            # premuta parentesi chiusa....valuto se passare al prossimo carattere
            if event.key() == Qt.Key.Key_BraceRight:
                self.auto_insert('}')                
            # premuto doppio apice...inserisco altro doppio apice
            elif event.key() == Qt.Key.Key_QuoteDbl:
                self.auto_insert('"')                
            # premuto apice...inserisco altro apice
            elif event.key() == Qt.Key.Key_Apostrophe:
                self.auto_insert("'")                
            # premuta combinazione CTRL+B passa da un segnalibro all'altro
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_B:                                
                self.slot_ctrl_b()
                return True
            # premuta combinazione CTRL+K (se premuto su un nome di tabella crea la select con i campi chiave)
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_K:                                
                self.slot_ctrl_k()
                return True
            # premuta combinazione CTRL+Invio e CTRL+Enter (esecuzione dell'istruzine corrente)
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier and (event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return):                
                self.slot_ctrl_invio()
                return True
            # tasto Insert premuto da parte dell'utente --> cambio la label sulla statusbar
            if event.key() == Qt.Key.Key_Insert:
                if self.v_overwrite_enabled:
                    self.v_overwrite_enabled = False                
                else:
                    self.v_overwrite_enabled = True                
                # aggiorno la status bar con relative label
                self.aggiorna_statusbar()
            # tasto F4 premuto dall'utente --> mi posiziono sulla prossima ricorrenza =
            # questa funzione risulta utile quando devo valorizzare dei campi di una select e voglio passare velocemente da uno all'altro
            if event.key() == Qt.Key.Key_F4:                 
                self.slot_f4()   
                return True
            # tasto F11 premuto dall'utente --> eseguo la quick query
            if event.key() == Qt.Key.Key_F11:                 
                self.slot_f11()   
                return True
            # tasto F12 premuto dall'utente --> richiamo l'object viewer            
            if event.key() == Qt.Key.Key_F12:                 
                self.slot_f12()   
                return True
            # tasto F3 premuto dall'utente --> richiamo la ricerca
            if event.key() == Qt.Key.Key_F3:                                 
                self.slot_find_next()   
                return True
            
        # if event.type() == QEvent.Type.DragEnter and source is self.e_sql:                                          
        #     # il drag contiene elenco di item...
        #     # se il drag non contiene elenco di item, quindi ad esempio del semplice testo, lascio le cose cosi come sono            
        #     if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):                
        #         # estraggo gli item e li trasformo in stringa
        #         v_mime_data = event.mimeData()
        #         source_item = QStandardItemModel()
        #         source_item.dropMimeData(v_mime_data, Qt.DropAction.CopyAction, 0,0, QModelIndex())                                                
        #         v_stringa = ''
        #         for v_indice in range(0,source_item.rowCount()):
        #             if v_stringa != '':
        #                 v_stringa += ',' + source_item.item(v_indice, 0).text()
        #             else:
        #                 v_stringa = source_item.item(v_indice, 0).text()                                
        #         # reimposto la stringa dentro l'oggetto mimedata
        #         # da notare come l'oggetto v_mime_data punta direttamente all'oggetto event.mimeData!
        #         v_mime_data.setText(v_stringa)                
        #     # accetto il drag
        #     event.accept()                        
        #     return True                                            
        
        # # individuo il drop sull'editor               
        # if event.type() == QEvent.Type.Drop and source is self.e_sql:                                                    
        #     # e richiamo direttamente la funzione che accetta il drop di QScintilla
        #     # da notare come durante il drag sia stato cambiato il contenuto dei dati nel caso 
        #     # la sorgente fossero degli item (in questo caso l'object viewer)
        #     self.e_sql.dropEvent(event)                
        #     return True        
        
        # individuo l'attivazione della subwindow dell'editor...
        if event.type() == QEvent.Type.FocusIn:                  
            # aggiorno i dati della statusbar
            self.aggiorna_statusbar()

        # individuo movimento della rotella del mouse sulla parte dei risultati e se combinata con il tasto shift allora effettuo lo scroll orizzontale destra-sinistra
        if event.type() == QEvent.Type.Wheel and source.parent() is self.o_table:
            wheel_event: QWheelEvent = event
            if wheel_event.modifiers() == Qt.KeyboardModifier.ShiftModifier:                
                if self.o_table.columnCount() > 0:
                    delta = wheel_event.angleDelta().y()                
                    step = delta // self.o_table.columnCount()
                    self.o_table.horizontalScrollBar().setValue(self.o_table.horizontalScrollBar().value() - step)                
                    return True  
                                            
        # fine senza alcuna elaborazione e quindi si procede con esecuzione dei segnali nativi del framework       
        return False
    
    def auto_insert(self, p_char):
        """
           Se utente sta scrivendo un carattere speciale (es. parentesi aperta, apice, ecc.) 
           automaticamente viene scritta la corrispondente parentesi chiusa.           
        """
        # ricavo numero riga e posizione del cursore
        v_num_line, v_num_pos = self.e_sql.getCursorPosition()                                            
        # estraggo il carattere corrente, precedente e successivo        
        if v_num_pos > 1:            
            v_char_left = self.e_sql.text(v_num_line)[v_num_pos-1]                             
            try:
                v_char_curr = self.e_sql.text(v_num_line)[v_num_pos]                             
            except:
                v_char_curr = ' '
            try:
                v_char_right = self.e_sql.text(v_num_line)[v_num_pos]                             
            except:
                v_char_right = ' '
        else:
            v_char_curr = ' '
            v_char_left = ' '   
            v_char_right = ' '   
        
        # se il carattere di destra è un ritorno a capo lo normalizzo a spazio
        if ord(v_char_right) in (13,10):
            v_char_right = ' '   
        
        # se sto scrivendo un carattere speciale sopra un testo selezionato, il testo selezionato viene prima eliminato        
        if self.e_sql.selectedText() != '':               
            self.e_sql.cut()                

        # se il carattere corrente è uguale al carattere ricevuto in input non faccio nulla; quindi cancello il carattere appena inserito e mi sposto a destra
        if v_char_curr == p_char:            
            self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
            self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)     
            return None
        
        # gestione singolo apice 
        if p_char == "'":            
            # inserisco apice se a destra e sinistra ho degli spazi oppure sono tra due parentesi            
            if (v_char_left == " " and v_char_right == " ") or (v_char_left in '(,[,{' and v_char_right in '),],}') or (v_char_left == '=' and v_char_right == ' '):       
                self.e_sql.insert("'")
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1])
            # se sto inserendo lo stesso carattere speciale tra altri due uguali, allora non inserisco nulla e mi posiziono al carattere successivo
            elif v_char_left == "'" and v_char_right == "'":        
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)            
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
            # esco
            return None 
                        
        # gestione doppio apice 
        if p_char == '"':
            # inserisco doppio apice se a destra e sinistra ho degli spazi oppure sono tra due parentesi
            if (v_char_left == " " and v_char_right == " ") or (v_char_left in '(,[,{' and v_char_right in '),],}') or (v_char_left == '=' and v_char_right == ' '):              
                self.e_sql.insert('"')
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1])
            # se sto inserendo lo stesso carattere speciale tra altri due uguali, allora non inserisco nulla e mi posiziono al carattere successivo
            elif v_char_left == '"' and v_char_right == '"':        
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)            
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
            # esco
            return None
                                
        # gestione parentesi tonda aperta
        if p_char == '(':
            # inserisco apice se a destra ho uno spazio
            if v_char_right == " ":       
                self.e_sql.insert(')')
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1])
            # esco
            return None        
        # gestione parentesi tonda chiusa
        if p_char == ')':                                    
            # se sto inserendo lo stesso carattere speciale tra altri due uguali, allora non inserisco nulla e mi posiziono al carattere successivo
            if v_char_left == '(' and v_char_right == ')':        
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)                            
            # esco
            return None        
                                                
        # gestione parentesi quadra aperta
        if p_char == '[':
            # inserisco apice se a destra ho uno spazio
            if v_char_right == " ":       
                self.e_sql.insert(']')
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1])
            # esco
            return None        
        # gestione parentesi quadra chiusa
        if p_char == ']':                                    
            # se sto inserendo lo stesso carattere speciale tra altri due uguali, allora non inserisco nulla e mi posiziono al carattere successivo
            if v_char_left == '[' and v_char_right == ']':        
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)                            
            # esco
            return None        
                                                        
        # gestione parentesi graffa aperta
        if p_char == '{':
            # inserisco apice se a destra ho uno spazio
            if v_char_right == " ":       
                self.e_sql.insert('}')
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1])
            # esco
            return None        
        # gestione parentesi graffa chiusa
        if p_char == '}':                                    
            # se sto inserendo lo stesso carattere speciale tra altri due uguali, allora non inserisco nulla e mi posiziono al carattere successivo
            if v_char_left == '{' and v_char_right == '}':        
                self.e_sql.setCursorPosition(self.e_sql.getCursorPosition()[0], self.e_sql.getCursorPosition()[1]+1)    
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELETEBACK)                            
            # esco
            return None        
    
    def tasto_destro_o_table(self, event):
        """
           Gestione del menu contestuale con tasto destro su tabella dei risultati
        """          
        self.v_o_table_current_item = self.o_table.itemAt(event.pos())                        
        # item di tipo testo
        # viene creato un menu popup con le voci di copia, zoom...
        if self.v_o_table_current_item is not None:            
            # creazione del menu popup
            self.o_table_cont_menu = QMenu(self)            
            
            # voce per copia valore
            icon1 = QIcon()
            icon1.addPixmap(QPixmap("icons:copy.png"), QIcon.Mode.Normal, QIcon.State.Off)        
            v_copia = QPushButton()
            v_copia.setText('Copy item')
            v_copia.setIcon(icon1)                    
            v_copia.clicked.connect(self.o_table_copia_valore)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_copia)        
            self.o_table_cont_menu.addAction(v_action)

            # voce per aprire window dove viene visualizzato il contenuto della cella in modo amplificato
            icon2 = QIcon()
            icon2.addPixmap(QPixmap("icons:zoom_avanti.png"), QIcon.Mode.Normal, QIcon.State.Off)        
            v_zoom = QPushButton()
            v_zoom.setText('Zoom item')
            v_zoom.setIcon(icon2)        
            v_zoom.clicked.connect(self.o_table_zoom_item)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_zoom)        
            self.o_table_cont_menu.addAction(v_action)

            # voce per copiare il valore nella calcolatrice (se è aperta)
            if self.link_to_MSql_win1_class.win_calculator != None:                
                icon3 = QIcon()
                icon3.addPixmap(QPixmap("icons:calculator.png"), QIcon.Mode.Normal, QIcon.State.Off)        
                v_zoom = QPushButton()
                v_zoom.setText('Copy to calc')
                v_zoom.setIcon(icon3)        
                v_zoom.clicked.connect(self.slot_copy_to_calculator)
                v_action = QWidgetAction(self.o_table_cont_menu)
                v_action.setDefaultWidget(v_zoom)        
                self.o_table_cont_menu.addAction(v_action)

            # visualizzo il menu alla posizione del cursore
            self.o_table_cont_menu.exec(event.globalPosition().toPoint())    
        # item non è di tipo testo...si presume sia un blob...cosa non certa...ma al momento non trovato modo per capirlo
        # viene creato il menu popup con la voce per il download
        else:
            # creazione del menu popup
            self.o_table_cont_menu = QMenu(self)            
            
            # voce per download
            icon1 = QIcon()
            icon1.addPixmap(QPixmap("icons:download.png"), QIcon.Mode.Normal, QIcon.State.Off)        
            v_download = QPushButton()
            v_download.setText('Download blob')
            v_download.setIcon(icon1)        
            v_download.clicked.connect(self.o_table_download_blob)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_download)        
            self.o_table_cont_menu.addAction(v_action)

            # visualizzo il menu alla posizione del cursore
            self.o_table_cont_menu.exec(event.globalPosition().toPoint())    
    
    def o_table_download_blob(self):
        """
            Download del blob 
            Il download viene determinato creando una select della colonna blob e usando come chiave di ricerca
            tutti i valori delle colonne a video (quelle che si trovano a sinistra della colonna blob selezionata)...
            se la select restituisce più di un record, viene emesso errore perché la "chiave" così creata non è univoca
        """
        # chiudo il menu popup
        self.o_table_cont_menu.close()
        # ricerco le coordinate dell'item selezionato
        v_x = self.o_table.currentRow()        
        v_y = self.o_table.currentColumn()        
        # imposto var di partenza
        v_where = ''        
        v_1a_volta = True
        v_nome_file = ''
        # costruisco la select che mi permetterà di effettuare la ricerca e il download dell'item
        # in pratica prendo i valori del contenuto di tutte le celle della riga selezionata, e le mixo con i relativi nomi di colonna 
        # prendendo però solo le colonne che hanno tipo stringa e numero
        # la "chiave" viene determinata dalle colonne a sinistra della colonna blob 
        # (es. SELECT FILEN_NU, FILES_FI, BYTE FROM TA_FILES, dove FILES_FI è il blob considera solo la colonna prima di FILES_FI)
        for v_i in range(0,len(self.tipi_intestazioni)):
            if v_i > v_y:
                break
            if self.tipi_intestazioni[v_i][1] not in (oracledb.DATETIME,oracledb.DB_TYPE_RAW,oracledb.BLOB,oracledb.CLOB):                
                if v_1a_volta:
                    v_1a_volta = False
                    v_where = self.nomi_intestazioni[v_i]
                else:
                    v_where += ' AND ' + self.nomi_intestazioni[v_i]
                v_valore_item = self.o_table.item(v_x,v_i).text()                
                if v_valore_item != '':
                    v_nome_file += v_valore_item
                    v_where += "='" + v_valore_item + "'"
                else:
                    v_where += " IS NULL"
        # estrae il nome della tabella dalla select corrente
        v_nome_tabella = extract_table_name_from_select(self.v_select_corrente)
        # creo la select che estrae il campo blob selezionato a video, con il nome della tabella e la where composta dai campi della riga
        v_select = 'SELECT ' + self.nomi_intestazioni[v_y] + ' FROM ' + v_nome_tabella + ' WHERE ' + v_where
        print(v_select)
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)
        # apro nuovo cursore
        v_cursor = v_global_connection.cursor()            
        # eseguo la select che va ad estrarre il blob (se errore --> esco)        
        try:
            v_cursor.execute(v_select)
        except:         
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(False)   
            message_error(QCoreApplication.translate('MSql_win2','Error blob fetching using the statement:') + chr(10) + v_select)                    
            return ''
        
        # controllo che sia estratta solo una riga!
        v_count = 0
        for row in v_cursor:
            v_count += 1        
        # se la select restituisce + di un risultato o nessun risultato --> errore        
        if v_count != 1:
            # sostituisce la freccia del mouse con icona "clessidra"
            Freccia_Mouse(False)
            message_error(QCoreApplication.translate('MSql_win2','Error blob fetching using the statement:') + chr(10) + v_select)            
        else:
            # eseguo la select che va ad estrarre il blob
            v_cursor.execute(v_select)    
            v_desc_intestazioni = v_cursor.description   
            # controllo che effettivamente sia stato selezionato un blob (siccome è una select monocolonna uso le coordinate 0 e 1)
            print(v_desc_intestazioni[0][1])
            if v_desc_intestazioni[0][1] != oracledb.BLOB:
                Freccia_Mouse(False)
                message_error(QCoreApplication.translate('MSql_win2','You must select a blob cell!'))
            else:                
                for row in v_cursor:                  
                    for count, column in enumerate(row):                   
                        # stabilisco il nome del file di destinazione che andrà nella dir dei downloads con nome del file composto dal nome della tabella + i primi 20 caratteri della "chiave"
                        v_file_download = os.path.join(os.path.expanduser("~"), "Downloads") + '\\' + v_nome_tabella.upper() + '_' + v_nome_file[0:20].replace('.','_')
                        # apro il file in scrittura
                        v_file_allegato = open(v_file_download,'wb')
                        # leggo e scrivo il blob
                        v_file_allegato.write(column.read())
                        # chiudo il file
                        v_file_allegato.close()                                                            
                        # sostituisce la freccia del mouse con icona "clessidra"
                        Freccia_Mouse(False)
                        # messaggio di fine
                        message_info(QCoreApplication.translate('MSql_win2','Blob downloaded in Downloads directory of your PC!'))
            
        # chiudo il cursore
        v_cursor.close()
    
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
        self.win_dialog_zoom_item = QDialog()                        
        self.win_dialog_zoom_item.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint)
        self.win_dialog_zoom_item.resize(300, 200)
        self.win_dialog_zoom_item.setWindowTitle('Zoom item')
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
        self.win_dialog_zoom_item.setWindowIcon(v_icon)
        self.win_dialog_zoom_item_gl = QGridLayout(self.win_dialog_zoom_item)
        self.win_dialog_zoom_lineEdit = QPlainTextEdit(self.win_dialog_zoom_item)        
        self.win_dialog_zoom_lineEdit.setReadOnly(True)
        self.win_dialog_zoom_item_gl.addWidget(self.win_dialog_zoom_lineEdit, 0, 0, 1, 1)
        # siccome mi posso trovare di fronte ad un clob di grandi dimensioni...nella parte di caricamento ho caricato il clob completo dentro
        # la parte data dell'item e una preview nella parte per il video, quindi quando sono nello zoom, se prensente la parte data, prendo quella    
        if self.v_o_table_current_item.data(Qt.ItemDataRole.UserRole) == None:
            self.win_dialog_zoom_lineEdit.setPlainText(self.v_o_table_current_item.text())
        else:
            self.win_dialog_zoom_lineEdit.setPlainText(self.v_o_table_current_item.data(Qt.ItemDataRole.UserRole))
        self.win_dialog_zoom_item.show()

    def slot_copy_to_calculator(self):
        """
           Copia il valore dell'item dentro la calcolatrice di MSql (se aperta)
        """                        
        self.link_to_MSql_win1_class.win_calculator.append_value(self.v_o_table_current_item.text())                    
        self.o_table_cont_menu.close()

    def slot_save_snapshoot(self):
        """
           Esegue il backup del testo presente nell'editor corrente all'interno della cartella backup
        """        
        global v_global_work_dir

        print('Auto backup of --> ' + self.objectName())

        # se la directory backup non esiste la creo
        if not os.path.isdir(v_global_work_dir + 'backup'):
            os.mkdir(v_global_work_dir + 'backup')
        
        # ricavo il nome del file da scrivere nella cartella di backup...i caratteri che identificano il disco e la cartella vengono rimpiazzati con .. e ...
        v_nome_file = nome_file_backup(self.objectName())        
        # creo il backup dell'editor corrente (Attenzione! Ogni editor aperto avrà il suo timer di salvataggio!)
        if self.setting_utf8:
            # scrittura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                                            
            v_file = open(v_nome_file ,'w',encoding='utf-8', newline='')
        else:
            # scrittura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
            v_file = open(v_nome_file, 'w', newline='')
        v_file.write(self.e_sql.text())
        v_file.close()                                
    
    def slot_f4(self):
        """
           Se premuto F4 eseguo la ricerca della prossima ricorrenza =
           Questo comando si rivela utile quando voglio passare da un campo all'altra di una select e sono in fase di editing
           es. SELECT * FROM OC_ORTES WHERE AZIEN_CO='' AND ESERC_CO='' AND DEPOS_CO='' AND TORDI_CO='' AND ORDIN_NU=''
           premendo F4 passo da un campo all'altro...
        """        
        # ricerco la stringa
        v_found = self.e_sql.findFirst("=", False, False, False, False, True, -1, -1, True, False, False)        
        # se trovato --> posiziono il cursore 
        if v_found:
            v_line, v_pos = self.e_sql.getCursorPosition() 
            v_text_line = self.e_sql.text(v_line)                        
            v_new_pos = v_text_line[v_pos:].find("'")            
            if v_new_pos != -1:
                self.e_sql.setCursorPosition(v_line, v_pos + v_new_pos + 1)
                self.e_sql.setFocus()
        # se non trovato --> vado all'inizio del testo
        else:                
            self.e_sql.setCursorPosition(0,0)            
    
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
        # utilizzando la posizione del cursore sulla riga, estraggo il nome dell'oggetto che sta sotto il cursore (es. TA_AZIEN oppure SMILE.TA_AZIEN)        
        v_owner, v_oggetto = extract_object_name_from_cursor_pos(v_line.upper(), v_num_pos-1)                                
        if v_oggetto != '':
            # se owner non trovato allora uso lo schema corrente
            if v_owner is None:                
                v_owner = self.link_to_MSql_win1_class.current_schema                              
            # pulisco il nome dell'oggetto da eventuali caratteri speciali come ritorno a capo, tab e spazi
            v_oggetto = v_oggetto.rstrip().lstrip()                            
            # messaggio di debug
            print('F11-Quick query on --> ' + v_owner + '.' + v_oggetto)      
            # tento di eseguire la query dell'oggetto selezionato (dovrebbe essere una tabella)
            v_select = 'SELECT * FROM ' + v_owner + '.' + v_oggetto
            self.esegui_select(v_select, True)
        
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
        # utilizzando la posizione del cursore sulla riga, estraggo il nome dell'oggetto che sta sotto il cursore (es. TA_AZIEN oppure SMILE.TA_AZIEN)
        v_owner, v_oggetto = extract_object_name_from_cursor_pos(v_line.upper(), v_num_pos-1)                        
        if v_oggetto != '':
            # se owner non trovato allora uso lo schema corrente
            if v_owner is None:                
                v_owner = self.link_to_MSql_win1_class.current_schema                              
            # pulisco il nome dell'oggetto da eventuali caratteri speciali come ritorno a capo, tab e spazi
            v_oggetto = v_oggetto.rstrip().lstrip()                            
            # messaggio di debug
            print('F12-Call Object viewer of --> ' + v_owner + '.' + v_oggetto)            
            v_temp_cursor = v_global_connection.cursor()                        
            # controllo se nel nome dell'oggetto c'è il carattere @ che indica il link verso altro database
            if '@' in v_oggetto:
                v_link = v_oggetto[v_oggetto.find('@'):]
                v_oggetto = v_oggetto[:v_oggetto.find('@')]                
            else:
                v_link = ''
            # estraggo 
            try:
                v_temp_cursor.execute("""SELECT OBJECT_NAME, OBJECT_TYPE FROM ALL_OBJECTS"""+v_link+""" WHERE OWNER = '""" + v_owner + """' AND OBJECT_NAME = '""" + v_oggetto + """' AND OBJECT_TYPE IN ('TABLE','VIEW','PACKAGE','PROCEDURE','FUNCTION')""")
            except:
                return 'ko'
            # prendo il risultato
            v_record = v_temp_cursor.fetchone()
            # se il risultato è presente ottengo nome e tipo dell'oggetto che dovrò passare all'object viewer
            if v_record != None:                    
                v_nome_oggetto = v_record[0]
                v_tipo_oggetto = v_record[1]                                   
                # carico l'object viewer passando come parametro iniziale il puntatore all'oggetto main
                MSql_win1_class.carica_object_viewer(self.link_to_MSql_win1_class, v_owner, v_tipo_oggetto, v_nome_oggetto, v_link)                                        
            else:
                print('Not found ' + v_oggetto)
    
    def slot_ctrl_k(self):
        """
           Se premuta la combinazione CTRL-K si individua se cursore è sul nome di una tabella
           A quel punto viene cercata la chiave primaria, e viene creata una select con il nome della tabella e con i campi
           della chiave primaria
        """    
        # imposto end of line
        if self.setting_eol == 'W':                        
            v_eol = '\r\n'
        else:
            v_eol = '\n'

        v_oggetto  = ''
        v_oggetto2 = ''        
        v_trovato_punto = False
        # se non è stata fatta alcuna selezione multipla di testo....vuol dire che è stato richiesto di ricercare la primary key di un'unica tabella
        if self.e_sql.selectedText() == '':              
            # ricavo numero riga e posizione del cursore
            v_num_line, v_num_pos = self.e_sql.getCursorPosition()                
            # estraggo l'intera riga dove è posizionato il cursore
            self.e_sql.setSelection(v_num_line, 0, v_num_line+1, -1)
            v_line = self.e_sql.selectedText()
            if '\r\n' in v_line:
                v_line = v_line.replace('\r\n','')
            else:
                v_line = v_line.replace('\n','')                        
            # riposiziono il cursore allo stato originario
            self.e_sql.setSelection(v_num_line, v_num_pos, v_num_line, v_num_pos)            
            # utilizzando la posizione del cursore sulla riga, estraggo il nome dell'oggetto che sta sotto il cursore (es. TA_AZIEN oppure SMILE.TA_AZIEN)            
            v_owner, v_oggetto = extract_object_name_from_cursor_pos(v_line.upper(), v_num_pos-1)                                                    
            # se owner non trovato allora uso il nome utente di connessione
            if v_owner is None:
                v_owner = self.link_to_MSql_win1_class.e_user_name               
            else:
                v_trovato_punto = True
        # altrimenti è stato selezionato del testo e devo capire se l'utente ha scritto due tabella su cui vuole fare la join
        else:
            # ricavo numero riga e posizione del cursore
            v_num_line, v_num_pos = self.e_sql.getCursorPosition()                
            # estraggo il testo selezionato e lo depuro da eventuali ritorni a capo e spazi            
            v_testo = self.e_sql.selectedText()            
            if '\r\n' in v_testo:
                v_testo = v_testo.replace('\r\n','')
            else:
                v_testo = v_testo.replace('\n','')            
            v_testo = v_testo.strip().upper()                        
            # dal testo selezionato ricavo il nome delle due tabelle 
            v_oggetti = v_testo.split(',')            
            if len(v_oggetti) > 0:
                v_oggetto = v_oggetti[0]
            if len(v_oggetti) > 1:
                v_oggetto2 = v_oggetti[1]
            # imposto owner sempre come nome utente
            v_owner = self.link_to_MSql_win1_class.e_user_name               

        print('CTRL_K-Key of --> ' + v_owner + '.' + v_oggetto2 + ',' + v_oggetto)
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)
        # richiamo la procedura di oracle che mi restituisce la ddl dell'oggetto (apro un cursore locale a questa funzione)
        v_temp_cursor = v_global_connection.cursor()

        # si è richiesto di fare la chiave di una sola tabella...
        if v_oggetto != '' and v_oggetto2 == '':            
            try:
                v_temp_cursor.execute("""SELECT ALL_TAB_COLUMNS.COLUMN_NAME, ALL_TAB_COLUMNS.DATA_TYPE
                                         FROM   ALL_CONSTRAINTS,
                                                ALL_CONS_COLUMNS,
                                                ALL_TAB_COLUMNS																					
                                         WHERE  ALL_CONSTRAINTS.OWNER           = '""" + v_owner + """'
                                           AND  ALL_CONSTRAINTS.TABLE_NAME      = '""" + v_oggetto + """'
                                           AND  ALL_CONSTRAINTS.CONSTRAINT_TYPE = 'P'
                                           AND  ALL_CONSTRAINTS.OWNER           = ALL_CONS_COLUMNS.OWNER
                                           AND  ALL_CONSTRAINTS.CONSTRAINT_NAME = ALL_CONS_COLUMNS.CONSTRAINT_NAME
                                           AND  ALL_CONSTRAINTS.TABLE_NAME      = ALL_CONS_COLUMNS.TABLE_NAME
                                           AND  ALL_CONS_COLUMNS.OWNER          = ALL_TAB_COLUMNS.OWNER
                                           AND  ALL_CONS_COLUMNS.TABLE_NAME     = ALL_TAB_COLUMNS.TABLE_NAME
                                           AND  ALL_CONS_COLUMNS.COLUMN_NAME    = ALL_TAB_COLUMNS.COLUMN_NAME
                                        ORDER BY ALL_CONS_COLUMNS.POSITION""")
            except:
                return 'ko'
            # prendo il risultato e inizio a costruire una nuova select con tutti i campi che compongono la chiave primaria
            v_record = v_temp_cursor.fetchall()
            # se trovati dei record....inizio a comporre la select, mettendo nella where campo per campo
            if len(v_record) > 0:
                v_risultato = 'SELECT *' + v_eol + 'FROM   ' + v_owner + '.' + v_oggetto + v_eol + 'WHERE  '
                v_1a_volta = True
                for campi in v_record:                
                    if v_1a_volta:
                        v_1a_volta = False
                    else:
                        v_risultato += v_eol + '  AND  '
                    v_risultato += campi[0] + '='
                    if campi[1] == 'DATE':
                        v_risultato += "TO_DATE('','DD/MM/YYYY')"                
                    else:
                        v_risultato += "''"            
                v_risultato += v_eol                    
                # cancello la parola dove presente il cursore (sia a destra che a sinistra)
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDLEFT)
                self.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDRIGHT)                
                # se l'utente aveva scritto il nome di tabella preceduto dal punto, allora devo cancellare a sinistra anche il punto e owner
                if v_trovato_punto:
                    self.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDLEFT)
                    self.e_sql.SendScintilla(QsciScintilla.SCI_DELWORDLEFT)
                # ed inserisco il risultato 
                self.e_sql.insert(v_risultato)
                # chiudo eventuale popup di autocompletation inviando a qscintilla il tasto Esc
                v_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier) 
                QApplication.postEvent(self.e_sql, v_event)
                # mi posiziono sul primo campo tramite la ricerca offerta dalla funzione F4
                self.slot_f4()
            else:
                message_info(QCoreApplication.translate('MSql_win2','No PK found!'))        
        # altrimenti si è richiesto di fare la chiave di due tabelle
        else:                
            try:
                # nota che per alcune situazioni si ottengono dei campi "doppi" sia come chiave primaria che come chiave univoca...un questi casi viene tolta successivamente la chiave univoca
                v_temp_cursor.execute("""SELECT FK.TABLE_NAME AS TABLE2,
                                                FKC.COLUMN_NAME AS TABLE2_COLUMN,
                                                PK.TABLE_NAME AS TABLE1,
                                                PKC.COLUMN_NAME AS TABLE1_COLUMN,
                                                (SELECT DATA_TYPE FROM ALL_TAB_COLUMNS WHERE ALL_TAB_COLUMNS.TABLE_NAME=FK.TABLE_NAME  AND ALL_TAB_COLUMNS.COLUMN_NAME=FKC.COLUMN_NAME) AS DATA_TYPE,
                                                PK.CONSTRAINT_TYPE 
                                         FROM   USER_CONSTRAINTS  FK,
                                                USER_CONS_COLUMNS FKC,
                                                USER_CONSTRAINTS  PK,
                                                USER_CONS_COLUMNS PKC
                                         WHERE  FK.OWNER           = '""" + v_owner + """'
                                           AND  FK.CONSTRAINT_TYPE = 'R'
                                           AND  FK.TABLE_NAME      = '""" + v_oggetto2 + """'
                                           AND  PK.TABLE_NAME      = '""" + v_oggetto + """'
                                           AND  FK.OWNER = FKC.OWNER AND FK.CONSTRAINT_NAME   = FKC.CONSTRAINT_NAME
                                           AND  FK.OWNER = PK.OWNER  AND FK.R_CONSTRAINT_NAME = PK.CONSTRAINT_NAME
                                           AND  PK.OWNER = PKC.OWNER AND PK.CONSTRAINT_NAME   = PKC.CONSTRAINT_NAME AND PKC.POSITION = FKC.POSITION
                                         ORDER BY FKC.POSITION""")
            except:
                return 'ko'
            # prendo il risultato e inizio a costruire una nuova select con tutti i campi che compongono la join
            v_record = v_temp_cursor.fetchall()            
            # se trovati dei record....inizio a comporre la select, mettendo nella where campo per campo
            if len(v_record) > 0:
                # se presente sia chiave primaria che univoca
                # faccio una pulizia dei dati in modo che in v_record rimanga solo la chiave primaria        
                v_p = 0
                v_u = 0
                for campi in v_record:
                    if campi[5] == 'U':
                        v_u = 1
                    elif campi[5] == 'P':
                        v_p = 1
                if v_p == 1 and v_u == 1:
                    v_record_new = []
                    for campi in v_record:
                        if campi[5] == 'P':
                            v_record_new.append(campi)
                    v_record = v_record_new                        
                
                # inizio la costruzione del risultato
                v_risultato = 'SELECT * ' + v_eol + 'FROM   ' + v_owner + '.' + v_oggetto + ',' + v_eol + '       ' + v_owner + '.' + v_oggetto2 + v_eol + 'WHERE  '
                # primary key
                v_1a_volta = True
                for campi in v_record:                
                    if v_1a_volta:
                        v_1a_volta = False
                    else:
                        v_risultato += '  AND  '
                    v_risultato += campi[2] + '.' + campi[3] + '='
                    if campi[1] == 'DATE':
                        v_risultato += "TO_DATE('','DD/MM/YYYY')"                
                    else:
                        v_risultato += "''"            
                    v_risultato += v_eol                                     
                # aggiunta della join
                for campi in v_record:                
                    v_risultato += '  AND  '
                    v_risultato += campi[2] + '.' + campi[3] + ' = ' + campi[0] + '.' + campi[1] + v_eol                                                            
                # cancello la selezione                    
                self.e_sql.removeSelectedText()
                # ed inserisco il risultato 
                self.e_sql.insert(v_risultato)                    
                # mi posiziono sul primo campo tramite la ricerca offerta dalla funzione F4
                self.slot_f4()
            else:
                message_info(QCoreApplication.translate('MSql_win2','No FK found!'))
            
        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(False)                
    
    def slot_click_colonna_risultati(self, p_index):       
        """
            Gestione menu popup all'interno dei risultati        
            Al click su una delle intestazioni di colonna della sezione "risultati" viene presentato un menu popup che permette di
            ordinare i risultati su quella colonna e di effettuare delle ricerche parziali
        """ 
        # prendo l'item dell'header di tabella             
        v_header_item = self.o_table.horizontalHeaderItem(p_index)

        # controllo se per questo item è già presente un filtro
        v_pos = -1
        v_where_filter = ''
        for nome_colonna in self.nomi_intestazioni:
            v_pos += 1
            if nome_colonna == v_header_item.text():
                v_where_filter = self.valori_intestazioni[v_pos]
                break
            
        # creazione del menu popup
        self.o_table_popup = QMenu(self)
        self.o_table_popup_index = p_index        

        # creazione del campo di input per la where
        self.e_popup_where = QLineEdit()        
        self.e_popup_where.setPlaceholderText('where...')
        if v_where_filter != '':
            self.e_popup_where.setText(v_where_filter)
        self.e_popup_where.editingFinished.connect(self.slot_where_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(self.e_popup_where)        
        self.o_table_popup.addAction(v_action)

        # definizione dello stile dei bottoni di menu
        v_button_style = "QPushButton { text-align: left; padding: 5px 5px; padding-left: 10px; }"
                
        # bottone per ordinamento ascendente
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("icons:order_a_z.png"), QIcon.Mode.Normal, QIcon.State.Off)        
        v_sort_a_z = QPushButton()
        v_sort_a_z.setText('Sort asc')
        v_sort_a_z.setIcon(icon1)        
        v_sort_a_z.setStyleSheet(v_button_style)
        v_sort_a_z.clicked.connect(self.slot_order_asc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_a_z)        
        self.o_table_popup.addAction(v_action)

        # bottone per ordinamento discendente
        icon2 = QIcon()
        icon2.addPixmap(QPixmap("icons:order_z_a.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_sort_z_a = QPushButton()
        v_sort_z_a.setText('Sort desc')
        v_sort_z_a.setIcon(icon2)
        v_sort_z_a.setStyleSheet(v_button_style)
        v_sort_z_a.clicked.connect(self.slot_order_desc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_z_a)        
        self.o_table_popup.addAction(v_action)
        
        # bottone per raggruppamento su colonna
        icon3 = QIcon()
        icon3.addPixmap(QPixmap("icons:group.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_group_by = QPushButton()
        v_group_by.setText('Group by')
        v_group_by.setIcon(icon3)
        v_group_by.setStyleSheet(v_button_style)
        v_group_by.clicked.connect(self.slot_group_by_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_group_by)        
        self.o_table_popup.addAction(v_action)
                
        # bottone per il count numero record
        icon4 = QIcon()
        icon4.addPixmap(QPixmap("icons:sequence.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_count = QPushButton()
        v_count.setText('Count')
        v_count.setIcon(icon4)
        v_count.setStyleSheet(v_button_style)
        v_count.clicked.connect(self.slot_count_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_count)        
        self.o_table_popup.addAction(v_action)
                        
        # bottone per la somma di colonna
        icon5 = QIcon()
        icon5.addPixmap(QPixmap("icons:sum.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_sum = QPushButton()
        v_sum.setText('Sum')
        v_sum.setIcon(icon5)
        v_sum.setStyleSheet(v_button_style)
        v_sum.clicked.connect(self.slot_sum_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sum)        
        self.o_table_popup.addAction(v_action)
                                
        # bottone per inserire il nome della colonna nell'editor
        icon6 = QIcon()
        icon6.addPixmap(QPixmap("icons:new.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_add = QPushButton()
        v_add.setText('Add to editor')
        v_add.setIcon(icon6)
        v_add.setStyleSheet(v_button_style)
        v_add.clicked.connect(self.slot_add_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_add)        
        self.o_table_popup.addAction(v_action)

        # calcolo la posizione dove deve essere visualizzato il menu popup in base alle proprietà dell'header di tabella
        headerPos = self.o_table.mapToGlobal(self.o_table_hH.pos())
        posY = headerPos.y() + self.o_table_hH.height()
        posX = headerPos.x() + self.o_table_hH.sectionPosition(p_index) - self.o_table_hH.offset()
        self.o_table_popup.exec(QPoint(posX, posY))        

    def get_where_filtri_colonne(self):
        """
           Restituisce la where in base ai filtri che sono presenti in questo momento sulle colonne (tramite il menu popup di colonna)
           Vengono considerate IS NULL e IS NOT NULL come istruzioni a se stanti
        """        
        v_pos = -1
        v_where = ''
        for nome_colonna in self.nomi_intestazioni:
            v_pos += 1
            # estraggo il testo che utente ha inserito nell'item della where e lo metto tutto maiuscolo
            v_where_item_value = self.valori_intestazioni[v_pos].upper()
            if v_where_item_value != '':
                if v_where != '':
                    v_where += ' AND '
                if v_where_item_value.lstrip().rstrip() == 'IS NULL':
                    v_where += "(" + nome_colonna + " IS NULL)"
                elif v_where_item_value.lstrip().rstrip() == 'IS NOT NULL':
                    v_where += "(" + nome_colonna + " IS NOT NULL)"
                else:
                    v_where += "(UPPER(" + nome_colonna + ") LIKE '%" + v_where_item_value + "%')"
                
        return v_where
    
    def slot_where_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Esecuzione della where specifica
        """             
        # prendo l'item dell'header di tabella             
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)        

        # se item esiste
        if v_header_item != None:
        
            # salvo il valore nella rispettiva lista (per poterlo riprende in visualizzazione) e anche per creare la select con tutti i filtri
            v_pos = -1
            for nome_colonna in self.nomi_intestazioni:
                v_pos += 1
                if nome_colonna == v_header_item.text():
                    self.valori_intestazioni[v_pos] = self.e_popup_where.text()
                    break                
                
            # wrap dell'attuale select aggiungendo specifica where
            v_where = self.get_where_filtri_colonne()
            if v_where != '':            
                v_new_select = "SELECT * FROM (" + self.v_select_corrente + ") WHERE " + v_where            

                # rieseguo la select
                self.esegui_select(v_new_select, False)
            # se non ci sono filtri, eseguo la select di partenza
            else:
                self.esegui_select(self.v_select_corrente, False)
                    
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
        
        # compongo eventuale where con i filtri attivi in questo momento
        v_where = self.get_where_filtri_colonne()
        if v_where != '':
            v_where = 'WHERE ' + v_where
        
        # nuova select che wrappa quella di partenza
        v_new_select = 'SELECT * FROM (' + self.v_select_corrente + ') ' + v_where + ' ORDER BY ' + v_header_item.text() + ' ' + p_tipo_ordinamento
                
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

        # compongo eventuale where con i filtri attivi in questo momento
        v_where = self.get_where_filtri_colonne()
        if v_where != '':
            v_where = 'WHERE ' + v_where
        
        # nuova select che wrappa quella di partenza
        v_new_select = 'SELECT ' + v_header_item.text() + ', COUNT(*) FROM (' + self.v_select_corrente + ') ' + v_where + ' GROUP BY ' +  v_header_item.text() + ' ORDER BY ' + v_header_item.text()
                
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
        
        # compongo eventuale where con i filtri attivi in questo momento
        v_where = self.get_where_filtri_colonne()
        if v_where != '':
            v_where = 'WHERE ' + v_where
        
        # wrap dell'attuale select con altra order by
        v_new_select = 'SELECT COUNT(*) FROM (' + self.v_select_corrente + ')' + v_where
                
        # rieseguo la select
        self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_sum_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Riesegue la select corrente con la sum della colonna selezionata
        """
        # prendo l'item dell'header di tabella 
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)
        
        # compongo eventuale where con i filtri attivi in questo momento
        v_where = self.get_where_filtri_colonne()
        if v_where != '':
            v_where = 'WHERE ' + v_where
        
        # wrap dell'attuale select con altra order by
        v_new_select = 'SELECT SUM(' + v_header_item.text() + ') FROM (' + self.v_select_corrente + ')' + v_where
                
        # rieseguo la select
        self.esegui_select(v_new_select, False)
        
        # chiudo il menu popup
        self.o_table_popup.close()

    def slot_add_popup(self):
        """
           Gestione menu popup all'interno dei risultati
           Prende il nome della colonna e lo inserisce nell'editor nel punto dove posizionato il cursore
        """
        # prendo l'item dell'header di tabella 
        v_header_item = self.o_table.horizontalHeaderItem(self.o_table_popup_index)

        # e lo inserisco nell'editor e sposto il cursore alla fine della parola
        if v_header_item.text() != '':
            self.e_sql.insert(' ' + v_header_item.text() + ',')
            # prendo posizione cursore in riga e colonna aggiungo alla colonna la lunghezza della parola e mi posiziono alla fine
            v_riga,v_colonna = self.e_sql.getCursorPosition()
            v_colonna = v_colonna + len(v_header_item.text()) + 2
            self.e_sql.setCursorPosition(v_riga,v_colonna)                
        
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
            self.v_output_lista_posizioni = []
            self.v_output_posizione_corrente = 0
    
    def slot_e_sql_modificato(self):
        """
           Viene richiamato quando si modifica del testo dentro la parte di istruzione sql
        """                
        self.v_testo_modificato = True
        # aggiorno i dati della statusbar
        self.aggiorna_statusbar()
    
    def slot_esegui(self, p_explain=False):
        """
           Interprete delle istruzioni SQL e PL-SQL           
           
           Nota Bene! Nell'editor sql l'utente può aver scritto PL-SQL, SQL o entrambe le cose, intervvallati
                      da segni di separazione come / e ;           
           
           Se si attiva p_explain la select verrà eseguita come se fosse uno script che crea il "piano di esecuzione"
        """
        global o_global_preferences  

        def fine_istruzione(p_stringa):
            """
               Funzione interna per controllare se la riga ha un termine di istruzione '/' oppure ;
            """
            # se istruzione è / --> allora termine istruzione
            if p_stringa == '/':
                return True
            # se istruzione finisce con ; e il punto e virgola però non è tra apici 
            v_reg = "^(?!.*(['\"].*;\1)).*;$"
            if re.match(v_reg, p_stringa):
                return True        

            return False
                
        # imposto la var di select corrente che serve in altre funzioni
        self.v_select_corrente = ''

        # prendo solo il testo evidenziato dall'utente 
        if self.e_sql.selectedText():
            v_testo = self.e_sql.selectedText()            
            # imposto la var che in caso di script che contiene più istruzioni separate da / tenga conto delle righe
            # delle sezioni precedenti (in questo caso parto dalla riga relativa! ad esempio ho spezzoni di script e non parto dall'inizio....)
            self.v_offset_numero_di_riga, v_start_pos = self.e_sql.getCursorPosition()
        # ... altrimenti prendo tutto il testo 
        else:                        
            v_testo = self.e_sql.text()
            # imposto la var che in caso di script che contiene più istruzioni separate da / tenga conto delle righe
            # delle sezioni precedenti
            self.v_offset_numero_di_riga = 0

        if v_testo == '':
            # emetto errore sulla barra di stato 
            message_error(QCoreApplication.translate('MSql_win2','No instruction!'))                                 
            return 'ko'

        # se indicato dalla preferenza, prima di partire ad eseguire, pulisco l'output
        if o_global_preferences.auto_clear_output:
            self.slot_clear('OUT')
        
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
                print('Continuo con script plsql ' + v_riga)
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
                    v_ok = self.esegui_plsql(v_plsql_str, False)                    
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
            # continuazione di una select dove la riga inizia con una costante
            elif v_istruzione and v_riga[0] == "'":
                v_istruzione_str += v_riga
            # fine di una select, insert, update, delete.... con punto e virgola o /
            elif v_istruzione and fine_istruzione(v_riga):
                v_istruzione = False
                v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]
                v_ok = self.esegui_istruzione(v_istruzione_str, p_explain)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # continuazione di una select, insert, update, delete....
            elif v_istruzione and not fine_istruzione(v_riga):
                 v_istruzione_str += chr(10) + v_riga
            # inizio select, insert, update, delete.... monoriga
            elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','REVOKE','ALTER','DROP','COMMENT','TRUNCATE','WITH','RENAME') and v_riga[-1] == ';':
                v_istruzione_str = v_riga[0:len(v_riga)-1]
                v_ok = self.esegui_istruzione(v_istruzione_str, p_explain)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # comando connect di tipo monoriga 
            # viene usata la funzione che ricava dalla stringa i parametri di connessione
            # poi vengono impostati i parametri di connessione dell'oggetto principale!
            # e quindi richiamata la funzione connetti che è presente in quell'oggetto!
            elif not v_istruzione and v_riga.split()[0].upper() == 'CONNECT':
                v_parametri = extract_connect_info_from_string(v_riga)                
                self.link_to_MSql_win1_class.e_user_name = v_parametri["e_user_name"]
                self.link_to_MSql_win1_class.e_user_proxy = v_parametri["e_user_proxy"]
                self.link_to_MSql_win1_class.e_password = v_parametri["e_password"]
                self.link_to_MSql_win1_class.e_server_name = v_parametri["e_server_name"]
                self.link_to_MSql_win1_class.e_user_mode = v_parametri["e_user_mode"]
                self.link_to_MSql_win1_class.slot_connetti()
            # inizio select, insert, update, delete.... multiriga            
            elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','ALTER','WITH'):
                v_istruzione = True
                v_istruzione_str = v_riga
            # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)             
            elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE','DROP'):
                print('Inizio plsql ')
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
                message_error(QCoreApplication.translate('MSql_win2','Unknown command type:' + ' ' + v_riga_raw + '.....'))
                return 'ko'                

        # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
        if v_plsql and v_plsql_str != '':
            v_ok = self.esegui_plsql(v_plsql_str, False)            
        
        # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
        if v_istruzione and v_istruzione_str != '':
            v_ok = self.esegui_istruzione(v_istruzione_str, p_explain)  

        return v_ok
                                                                       
    def slot_ctrl_invio(self):
        """
           L'utente ha premuto CTRL+Invio: viene ricercata l'istruzione dove il cursore di testo è attualmente posizionato
           e viene inviata all'esecutore. Se l'utente ha selezionato del testo, viene eseguito il testo selezionato; questo
           per mantenere un comportamento coerente con l'esecuzione tramite F5.
        """
        # se indicato dalla preferenza, prima di partire ad eseguire, pulisco l'output
        if o_global_preferences.auto_clear_output:
            self.slot_clear('OUT')
        
        # controllo se utente ha selezionato del testo specifico che vuole eseguire
        v_istruzione = self.e_sql.selectedText()                
        if v_istruzione is not None and v_istruzione != '':            
            # eseguo l'istruzione selezionata                          
            self.esegui_istruzione(v_istruzione, False)        
        # ... altrimenti....
        else:
            # imposto var generali
            self.v_offset_numero_di_riga = 0
            # prendo posizione attuale del cursore (relativa!)
            v_pos_relativa_cursore = self.e_sql.SendScintilla(self.e_sql.SCI_GETCURRENTPOS)
            # richiamo funzione interna per estrazione dell'istruzione sql o pl-sql 
            #v_istruzione, v_tipo_istruzione, v_start_pos, v_end_pos = extract_sql_under_cursor(self.e_sql.text(), v_pos_relativa_cursore + 1)                                        
            #v_istruzione, v_start_pos, v_end_pos = extract_sql_under_cursor(self.e_sql.text(), v_pos_relativa_cursore)                                        
            v_start_pos, v_end_pos = extract_section_under_cursor(self.e_sql.text(), v_pos_relativa_cursore)
            v_istruzione = self.e_sql.text()[v_start_pos:v_end_pos]
            # l'istruzione viene ripulita anche dai commenti iniziali
            v_istruzione = pulisci_commenti_inizio_riga(v_istruzione)
            # se trovata istruzione
            if v_istruzione != '' and v_end_pos > 0:                
                # per capire se puro codice pl-sql controllo inizio (stessa stringa che viene controllata nella funzione slot_esegui)
                if v_istruzione.upper().startswith(('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE')):
                    self.esegui_plsql(v_istruzione, False)        
                else:                
                    self.esegui_istruzione(v_istruzione, False)
                # seleziono il testo per evidenziare l'istruzione che è stata eseguita                                                                                            
                self.e_sql.SendScintilla(self.e_sql.SCI_SETSELECTION, v_start_pos, v_end_pos)        
            else:
                # altrimenti errore
                message_error(QCoreApplication.translate('MSql_win2','No statement found!'))
                return 'ko'                                       

    def esegui_istruzione(self, p_istruzione, p_explain):
        """
           Esegue istruzione p_istruzione
           Se p_explain è attivo, vuol dire che è stata richiesta la explain plan (tasto F9 da menu)...
        """
        v_ok = ''              
        # esecuzione normale...
        if not p_explain:    
            # se trovo select eseguo select
            if p_istruzione[0:6].upper() == 'SELECT' or p_istruzione[0:4].upper() == 'WITH':                
                v_ok = self.esegui_select(p_istruzione, True)
            # ..altrimenti esegue come script
            else:                 
                v_ok = self.esegui_plsql(p_istruzione, True)        

        # è stato richiesto di fare l'analisi del piano di esecuzione
        else:            
            # l'istruzione viene eseguita come script pl-sql e non viene registrata nel log
            v_ok = self.esegui_plsql('EXPLAIN PLAN FOR ' + p_istruzione, False)        
            if v_ok is None:
                # leggo il risultato dell'analisi, usando un altro cursore                
                v_cursor_db_plan = v_global_connection.cursor()            
                v_cursor_db_plan.execute("SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE',NULL,'TYPICAL'))")                
                # pulisco l'oggetto a video che contiene l'output
                self.o_plan.clear()                
                # carico a video il risultato dell'analisi
                for result in v_cursor_db_plan:                       
                    self.o_plan.appendPlainText(result[0])
                # mi posiziono all'inizio del testo
                self.o_plan.moveCursor(QTextCursor.MoveOperation.Start)                    
                # porto in primo piano la visualizzazione del tab di plan
                self.o_tab_widget.setCurrentIndex(3)          

        # esco
        return v_ok 

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
                        Inoltre va tenuto conto che la libreria oracledb ha delle sue classi specifiche per la gestione dei vari aspetti
        """
        global v_global_connesso
        global v_global_create_confirm
        global v_global_exec_time
        
        # Eccezione! il ritorno a capo finale viene tolto se ultima istruzione non è una end e stessa cosa per il punto e virgola
        if p_plsql.splitlines()[-1].upper().find('END') == -1:
            if p_plsql[-1] == '\r' or p_plsql[-1] == '\n':            
                p_plsql = p_plsql[0:-1]                                    
            if p_plsql[-1] == ';':            
                p_plsql = p_plsql[0:-1]                                    
    
        def get_dbms_output_flow():
            """
               Funzione interna che restituisce il flusso generato dal package dbms_output, durante l'esecuzione dello script pl-sql
            """
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
                for i, line in enumerate(v_lines):                    
                    # if i < len(v_lines) - 1:
                    #     v_dbms_ret += str(line) + '\n'                    
                    # else:                        
                    #     v_dbms_ret += str(line) + '\n'
                    v_dbms_ret += str(line) + '\n'                                        
                if v_num_lines < v_chunk:
                    break
            # restituisco la lista delle righe di dbms_output (elimino ultimo ritorno a capo)
            return v_dbms_ret.removesuffix('\n')

        # verifico che mi sia stato passato del testo
        if p_plsql == '':
            message_error(QCoreApplication.translate('MSql_win2','No script!'))
            return 'ko'

        # solo se sono connesso al DB....
        if v_global_connesso:                                    
            # imposto la var che conterrà il comando corrente
            self.v_plsql_corrente = p_plsql
            # var che indica se siamo in uno script di "CREATE"            
            v_create = False
            v_testo = self.v_plsql_corrente[0:500].upper()               
            # controllo se siamo in presenza di un comando che altera il DB...
            if 'CREATE ' in v_testo or 'REPLACE ' in v_testo or 'ALTER ' in v_testo or 'DROP ' in v_testo:
                v_create = True
                # l'utente ha richiesto di chiedere conferma prima di procedere con questo tipo di comandi....
                # quindi faccio comparire messaggio di conferma e se risponde di no --> interrompo
                if v_global_create_confirm and message_question_yes_no(QCoreApplication.translate('MSql_win2','Are you sure to confirm this command?') + chr(10) + v_testo[0:100].rstrip()) == 'No':
                    return 'ko'

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
            # esegue comando sql in modo asincrono!!! Al termine viene invocato un segnale e richiamata la funzione endSelectCommandToOracle
            self.bind_variable(p_function='DIC',p_testo_sql=p_plsql)                                                        
            v_start_time = datetime.datetime.now()            
            self.v_set_rowcount = p_rowcount      
            self.v_oracle_executer = oracle_executer.SendCommandToOracle(v_global_connection, self.v_cursor, p_plsql, self.v_variabili_bind_dizionario, self.link_to_MSql_win1_class.frameGeometry(), o_global_preferences.animated_gif)                                                                        
            self.v_oracle_executer.start()
        
            # riattivo la freccia del mouse
            Freccia_Mouse(False)       
                                        
            # chiudo la progressbar di esecuzione del comando
            self.v_oracle_executer.close()                
            
            if self.v_oracle_executer.get_status() == 'CANCEL_JOB':               
                # comando abortito --> scrivo apposito errore
                self.scrive_output("Error: command aborted", "E")                                                            

            if self.v_oracle_executer.get_status() == 'END_JOB_KO':                                
                # comando terminato con errore --> emetto errore nella sezione di output
                v_oracle_error = self.v_oracle_executer.get_error()                         
                # leggo la parte di dbms_output
                v_dbms_ret = get_dbms_output_flow()                
                # per prima cosa porto l'output a video (tipico è quello di script che contengono dbms_output e che vanno in errore durante l'esecuzione)
                if v_dbms_ret != '':
                    self.scrive_output(v_dbms_ret, 'I')
                # output dell'errore
                self.scrive_output("Error: " + v_oracle_error.message, "E")                                 
                # per posizionarmi alla riga in errore ho solo la variabile offset che riporta il numero di carattere a cui l'errore si è verificato                
                v_riga, v_colonna = x_y_from_offset_text(p_plsql, v_oracle_error.offset)                                                                
                v_riga += self.v_offset_numero_di_riga
                self.e_sql.setCursorPosition(v_riga,v_colonna)                
                # esco con errore
                return 'ko'

            if self.v_oracle_executer.get_status() == 'END_JOB_OK':                   
                # calcolo tempo esecuzione e aggiorno a video            
                v_global_exec_time = (datetime.datetime.now() - v_start_time).total_seconds()
                self.aggiorna_statusbar()
                # aggiungo l'istruzione all'history                            
                write_sql_history(v_global_work_dir+'MSql.db',self.v_plsql_corrente,v_global_exec_time)                   
                # conto record
                v_tot_record = self.v_cursor.rowcount
                self.v_esecuzione_ok = True            
                ###
                # controllo se eravamo di fronte ad uno script di "CREATE"...inizio con il prendere i primi 500 caratteri (è una cifra aleatoria!)
                # da notare come la stringa che si ricerca abbia uno spazio finale in modo non venga confusa con altro (ad esempio la funzione replace())                
                if v_create:                    
                    # nettifica del testo, togliendo spazi e ritorni a capo
                    v_testo = v_testo[:50000]
                    v_testo = v_testo.upper().lstrip().replace('\n',' ')                
                    v_testo = v_testo.replace('PACKAGE BODY','PACKAGEBODY')                    
                    # ora devo cercare il tipo oggetto che è stato richiesto di creare....e quindi splitto il testo in parole
                    v_split = v_testo.split()
                    v_tipo_script = ''
                    # inizio a scorrere le parole presenti in questa parte di testo...
                    for v_parola in v_split:                                        
                        if v_parola in ('PACKAGEBODY','PACKAGE','PROCEDURE','FUNCTION','TABLE','VIEW','TRIGGER','SEQUENCE'):
                            v_tipo_script = v_parola
                            break
                    # ripristo il tipo script in un formato più "standard" (es. PACKAGE BODY invece di PACKAGEBODY)
                    if v_tipo_script == 'PACKAGEBODY':
                        v_tipo_script = 'PACKAGE BODY'
                    # ora devo cercare il nome del testo che è stato richiesto di creare....e quindi splitto il testo in parole
                    v_split = v_testo.split()
                    v_nome_script = ''
                    # inizio a scorrere le parole presenti in questa parte di testo...
                    for v_parola in v_split:                                        
                        if v_parola not in ('CREATE','OR','REPLACE','ALTER','DROP','PACKAGE','PACKAGEBODY','EDITIONABLE','NONEDITIONABLE','TABLE','PROCEDURE','FUNCTION','TRIGGER','VIEW','SEQUENCE','PUBLIC','SYNONYM','TYPE'):
                            v_nome_script = v_parola
                            break
                    # nettifico il nome dell'oggetto che potrebbe essere nel formato "SMILE"."NOME_OGGETTO"                
                    v_nome_script = v_nome_script.replace('"','')                    
                    if '.' in v_nome_script:
                        v_nome_script = v_nome_script.split('.')[1]
                    # oppure nel formato che termina con una parentesi (es. CREATE FUNCTION PROVA(P_PARAMETER VARCHAR2) )
                    elif '(' in v_nome_script:
                        v_nome_script = v_nome_script.split('(')[0]

                # quindi...se lo script era di "CREATE"...controllo se in compilazione ci sono stati errori...
                # attenzione! per certi tipi di oggetto (es. trigger) il numero di riga a cui viene segnalato l'errore è a contare dalla riga di DECLARE!
                if v_create:
                    if v_tipo_script == 'TRIGGER':
                        # ricerco a che riga si trova la prima DECLARE e questo è un ulteriore offset da sommare alla riga di errore
                        v_other_offset = search_first_string_in_text(p_plsql, r'\bDECLARE\b')
                    else:
                        v_other_offset = 0
                    print(f"CREAZIONE DELLO SCRIPT --> Tipo: {v_tipo_script} Nome: {v_nome_script} Riga offset: {self.v_offset_numero_di_riga} Altra riga offset: {v_other_offset}")                                        
                    # con questa select dico a Oracle di darmi eventuali errori presenti su un oggetto                 
                    self.v_cursor.execute("SELECT LINE,POSITION,TEXT FROM USER_ERRORS WHERE NAME = '" + v_nome_script + "' and TYPE = '" + v_tipo_script + "'")
                    v_errori = self.v_cursor.fetchall()
                    # errori riscontrati --> li emetto nella parte di output e mi posiziono sull'editor alla riga e colonna indicate
                    if v_errori:
                        v_1a_volta = True
                        for info in v_errori:
                            # emetto gli errori riscontrati
                            self.scrive_output(f"Error at line {info[0] + v_other_offset} position {info[1]} {info[2]}", 'E')                                                
                            # solo per il primo errore mi posiziono sull'editor alle coordinate indicate
                            if v_1a_volta:                                                            
                                v_riga = info[0]-1 + self.v_offset_numero_di_riga + v_other_offset
                                v_colonna = info[1]-1                                                        
                                self.e_sql.setCursorPosition(v_riga,v_colonna)                            
                                v_1a_volta = False
                        # esco con errore
                        return 'ko'
                    # tutto ok! --> scrivo nell'output messaggio di buona riuscita operazione
                    else:
                        self.scrive_output(extract_word_from_cursor_pos(v_testo,1)  + ' ' + v_tipo_script + ' ' + v_nome_script + ' SUCCESSFULLY!','I')
                
                # altrimenti siamo di fronte ad uno script di pl-sql interno o di insert,update,delete,grant che vanno gestiti con apposito output
                else:                           
                    # leggo la parte di dbms_output
                    v_dbms_ret = get_dbms_output_flow()

                    # se richiesto output del numero di record...
                    if self.v_set_rowcount:
                        # il numero lo riporto solo per (insert, update, delete...)
                        if p_plsql.split()[0].upper() in ('INSERT','UPDATE','DELETE'):
                            self.scrive_output(self.v_plsql_corrente.split()[0] + ' ' + str(v_tot_record) + ' row(s)', 'I')    
                        # altrimenti (es. comment on table) emetto semplice messaggio di esecuzione
                        else:
                            self.scrive_output(self.v_plsql_corrente.split()[0] + ' EXECUTED!', 'I')    
                    else:
                        # porto l'output a video (tipico è quello di script che contengono dbms_output)
                        if v_dbms_ret != '':                            
                            self.scrive_output(v_dbms_ret, 'I')
                        else:
                            self.scrive_output('Script executed!', 'I')

                # aumento il numero di riga di offset (serve per eventuale script successivo di questo gruppo di esecuzione)            
                self.v_offset_numero_di_riga += len(self.v_plsql_corrente.split(chr(10)))
            
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
        global v_global_exec_time        

        self.v_flag_testo_corrente = p_corrente        
                
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
            if self.v_flag_testo_corrente:
                self.v_select_corrente = p_select
            
            # se la tabella deve essere editabile
            # all'sql scritto dall'utente aggiungo una parte che mi permette di avere la colonna id riga
            # questa colonna mi servirà per tutte le operazioni di aggiornamento
            if o_global_preferences.editable:
                v_select = 'SELECT ROWID, MY_SQL.* FROM (' + p_select + ') MY_SQL'    
            else:
                v_select = p_select
            
            # per la funzionalità "extract sql from output" mi salvo la select effettivamente eseguita
            self.v_select_eseguita = v_select
            
            # esegue comando sql in modo asincrono!!! Al termine viene invocato un segnale e richiamata la funzione endSelectCommandToOracle
            self.bind_variable(p_function='DIC',p_testo_sql=v_select)                                                        
            v_start_time = datetime.datetime.now()
            self.v_oracle_executer = oracle_executer.SendCommandToOracle(v_global_connection, self.v_cursor, v_select, self.v_variabili_bind_dizionario, self.link_to_MSql_win1_class.frameGeometry(), o_global_preferences.animated_gif)                                                                        
            self.v_oracle_executer.start()

            # riattivo la freccia del mouse
            Freccia_Mouse(False)        

            # controllo cosa mi ha restituito l'oggetto executer
            if self.v_oracle_executer.get_status() == 'CANCEL_JOB':               
                # comando abortito --> scrivo apposito errore
                self.scrive_output("Error: command aborted", "E")                                                            

            if self.v_oracle_executer.get_status() == 'END_JOB_KO':                
                # comando terminato con errore --> emetto errore nella sezione di output
                v_oracle_error = self.v_oracle_executer.get_error()             
                self.scrive_output("Error: " + v_oracle_error.message, "E")                                                            

            if self.v_oracle_executer.get_status() == 'END_JOB_OK':   
                # calcolo tempo esecuzione e aggiorno a video            
                v_global_exec_time = (datetime.datetime.now() - v_start_time).total_seconds()
                self.aggiorna_statusbar()
                # aggiungo l'istruzione all'history            
                write_sql_history(v_global_work_dir+'MSql.db',self.v_select_corrente,v_global_exec_time)                   
                # comando eseguito correttamente --> imposto flag
                self.v_esecuzione_ok = True
                # prendo il cursore!
                self.v_cursor = self.v_oracle_executer.get_cursor()                    
                # lista contenente le intestazioni (tramite apposita funzione si ricavano i nomi delle colonne dall'sql che si intende eseguire)
                self.nomi_intestazioni = nomi_colonne_istruzione_sql(self.v_cursor)                                    
                self.o_table.setColumnCount(len(self.nomi_intestazioni))                                                    
                # lista contenente i tipi delle colonne 
                self.tipi_intestazioni = self.v_cursor.description   
                # setto le intestazioni con i nomi restituiti dalla select
                self.o_table.setHorizontalHeaderLabels(self.nomi_intestazioni)                                    
                # se la select è eseguita partendo da editor...
                if self.v_flag_testo_corrente:                                
                    # pulisco la lista che contiene i valori dei filtri di intestazione 
                    self.valori_intestazioni = []
                    for i in range(0,len(self.nomi_intestazioni)):                
                        self.valori_intestazioni.append('')
                # se la select è eseguita partendo dal menu popup sulla intestazione di colonna...
                # faccio in modo che tutte le colonne dove è stato impostato un filtro, abbiano l'icona dell'imbuto accanto al rispettivo titolo
                else:
                    v_pos = -1
                    for nome_colonna in self.nomi_intestazioni:
                        v_pos += 1
                        # è presente un filtro...
                        if self.valori_intestazioni[v_pos] != '':                        
                            # creo un item che contiene icona imbuto e nome colonna corrente e rigenero la rispettiva intestazione
                            v_new_header_item = QTableWidgetItem()
                            v_new_header_item.setIcon(QIcon(QPixmap("icons:filter.png")))
                            v_new_header_item.setText(nome_colonna)
                            self.o_table.setHorizontalHeaderItem(v_pos,v_new_header_item)
                                
                # se tutto ok, posso procedere con il caricare la prima pagina                                            
                self.carica_pagina(p_wait_window=True)                   

                # refresh della sezione variabili bind
                if len(self.v_variabili_bind_nome) != 0:
                    self.bind_variable(p_function='SHOW')

                # posizionamento sulla parte di output risultati select
                self.o_tab_widget.setCurrentIndex(0) 
                                            
        # chiudo la progressbar di esecuzione del comando        
        self.v_oracle_executer.close()             

        # esco con tutto ok
        return None
    
    def carica_pagina(self, p_wait_window=False):
        """
            Carica i dati del flusso record preparato da esegui_select.
            Se p_wait_window è True viene mostrata una finestra di attesa durante il caricamento (con la scritta "Rendering..").
            La funzione ritorna solo quando il caricamento è completato, restituendo 'ok' o 'ko'.
        """
        global v_global_connesso
        global o_global_preferences

        # prerequisiti
        if not (v_global_connesso and self.v_esecuzione_ok):
            return 'ko'

        v_ok = 'ok'          # valore di ritorno predefinito
        v_local_loop = None  # variabile che conterrà il QEventLoop locale

        # funzione interna che esegue il caricamento vero e proprio
        def _do_load():
            nonlocal v_ok, v_local_loop
            try:
                self.o_table.setUpdatesEnabled(False)
                self.o_table.blockSignals(True)

                try:
                    v_riga_dati = self.v_cursor.fetchone()
                except (oracledb.DatabaseError, oracledb.InterfaceError) as e:
                    errorObj, = e.args
                    message_error(QCoreApplication.translate('MSql_win2', "Error to fetch data:") + ' ' + errorObj.message)
                    v_ok = 'ko'
                    return

                if v_riga_dati is None:
                    v_ok = 'ko'
                    return

                if self.v_pos_y == 0:
                    self.o_table.setRowCount(1)

                while True:
                    x = 0
                    self.o_table.setRowHeight(self.v_pos_y, self.v_altezza_font_output)

                    for field in v_riga_dati:
                        if isinstance(field, str):
                            self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem(field))
                        elif isinstance(field, int):
                            v_item = QTableWidgetItem(f"{field:d}")
                            v_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            self.o_table.setItem(self.v_pos_y, x, v_item)
                        elif isinstance(field, float):
                            try:
                                locale.setlocale(locale.LC_ALL, 'it_IT')
                                v_item = QTableWidgetItem(locale.str(field))
                            except Exception:
                                v_item = QTableWidgetItem(str(field))
                            v_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            self.o_table.setItem(self.v_pos_y, x, v_item)
                        elif field is None:
                            self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem(""))
                        elif self.tipi_intestazioni[x][1] == oracledb.DATETIME:
                            self.o_table.setItem(
                                self.v_pos_y, x,
                                QTableWidgetItem(f"{field:{o_global_preferences.date_format}}")
                            )
                        elif self.tipi_intestazioni[x][1] == oracledb.DB_TYPE_RAW:
                            self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem(field.hex().upper()))
                        elif self.tipi_intestazioni[x][1] == oracledb.BLOB:
                            qimg = QImage.fromData(field.read())
                            pixmap = QPixmap.fromImage(qimg) if qimg.depth() > 0 else QPixmap("icons:no_image.png")
                            label = QLabel()
                            label.setPixmap(pixmap)
                            if o_global_preferences.dark_theme:
                                label.setStyleSheet('background-color:white')
                            self.o_table.setCellWidget(self.v_pos_y, x, label)
                        elif self.tipi_intestazioni[x][1] == oracledb.CLOB:
                            text = field.read()
                            preview = text[:1000] + ' !!! DATA TRUNCATED !!!' if len(text) > 1000 else text
                            item = QTableWidgetItem(preview)
                            item.setData(Qt.ItemDataRole.UserRole, text)
                            self.o_table.setItem(self.v_pos_y, x, item)
                        x += 1

                    self.v_pos_y += 1
                    self.o_table.setRowCount(self.v_pos_y + 1)

                    if self.v_pos_y % 100 == 0:
                        if p_wait_window and self.v_wait_window:
                            QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
                        break

                    v_riga_dati = self.v_cursor.fetchone()
                    if v_riga_dati is None:
                        self.o_table.setRowCount(self.v_pos_y)
                        break

                if o_global_preferences.auto_column_resize:
                    self.o_table.resizeColumnsToContents()

                self.o_table.setColumnHidden(0, o_global_preferences.editable)

            finally:
                # ripristino interfaccia
                self.o_table.blockSignals(False)
                self.o_table.setUpdatesEnabled(True)
                self.o_table.viewport().update()

                # chiusura finestra di attesa
                if p_wait_window and getattr(self, "v_wait_window", None):
                    self.v_wait_window.close()
                    self.v_wait_window = None

                # 🔓 sblocca il loop locale se attivo
                if v_local_loop is not None and v_local_loop.isRunning():
                    v_local_loop.quit()

        # --- parte principale ---
        if p_wait_window:
            self.v_wait_window = oracle_executer.WaitRenderingDialog(self.o_table)
            self.v_wait_window.show()
            QApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)

            # Crea e avvia il loop di attesa locale
            v_local_loop = QEventLoop()
            QTimer.singleShot(50, _do_load)

            # blocca fino al completamento di _do_load()
            v_local_loop.exec()
        else:
            _do_load()

        return v_ok

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
        print(f"Updated cell {x},{y}")
        # memorizzo nella matrice la coppia x,y della cella modificata
        self.v_matrice_dati_modificati.append((x,y))            

    def slot_save_modified_data(self):
        """
           Prende tutti gli item modificati nella tabella e crea lo script per l'aggiornamento
        """
        # Siccome questa funzione viene richiamta da menu, può essere che il focus sia rimasto nella cella e non sia scattato il relativo change che 
        # ha caricato la matrice dei dati modificati (di quella cella); per questo motivo si valuta se caricare anche la cella dove era il focus        
        focused_widget = QApplication.focusWidget()                
        # se l'elemento su cui era il focus era un item...
        if isinstance(focused_widget, QLineEdit):                                            
            # forzo uscita del cursore che fa automaticamente scattare la funzione di change dell'item
            focused_widget.clearFocus()
        
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
            if self.tipi_intestazioni[yx[1]][1] == oracledb.DATETIME:                                     
                v_valore_cella = "TO_DATE('" + v_valore_cella + "','" + da_qt_a_formato_data_oracle(o_global_preferences.date_format) + "')"            
            else:
                v_valore_cella = "'" + v_valore_cella + "'"
            v_update = "UPDATE " + v_table_name + " SET " + self.nomi_intestazioni[yx[1]] + "=" + v_valore_cella + " WHERE ROWID = '" + v_rowid + "'"
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
            if os.name == "posix":
                subprocess.Popen(["xdg-open", v_global_work_dir + 'Export_data.csv'])    
            else:
                os.startfile(v_global_work_dir + 'Export_data.csv')
        except:
            message_error(QCoreApplication.translate('MSql_win2','Error in file creation!'))
      
    def closeEvent(self, e):
        """
           Intercetto l'evento di chiusura del form e controllo se devo chiedere di salvare o meno
           Questa funzione sovrascrive quella nativa di QT            
        """
        global o_global_preferences
        global v_global_work_dir

        def delete_snapshoot():                
            """
               Cancello il file di backup
            """
            # ricavo il nome del file da scrivere nella cartella di backup...i caratteri che identificano il disco e la cartella vengono rimpiazzati con .. e ...
            v_nome_file = nome_file_backup(self.objectName())            
            if os.path.exists(v_nome_file):
                os.remove(v_nome_file)				
                print('Removed backup of --> ' + v_nome_file)

        v_salvare = self.check_to_save_file()                    
        # richiesto di salvare e poi di chiudere
        if v_salvare == 'Yes':        
            self.v_editor_chiuso = True            
            delete_snapshoot()
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
            delete_snapshoot()
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
        v_scelta = message_question_yes_no_cancel(QCoreApplication.translate('MSql_win2',"The document") + ' ' + self.objectName() + ' ' + QCoreApplication.translate('MSql_win2',"was modified.") + chr(13) + QCoreApplication.translate('MSql_win2',"Do you want to save changes?"))        
        # utente richiede di interrompere 
        if v_scelta == 'Cancel':
            return 'Cancel'
        # utente chiede di salvare
        elif v_scelta == 'Yes':            
            if self.objectName() == "":                
                v_ok, v_nome_file = salvataggio_editor(True, self.objectName(), self.e_sql.text(), self.setting_utf8)
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    self.v_testo_modificato = False
                    return 'Yes'
            else:                      
                v_ok, v_nome_file = salvataggio_editor(False, self.objectName(), self.e_sql.text(), self.setting_utf8)                          
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
            font, ok = QFontDialog.getFont(QFont("Courier New"))
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
            font, ok = QFontDialog.getFont(QFont("Arial"))
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
        # apro la sezione di ricerca e posiziono il fuoco del cursore
        self.dockFindWidget.show()
        self.e_find.setFocus()  
        # se è stato selezionato del testo lo utilizzo come base per la ricerca e lo seleziono
        v_testo_selezionato = self.e_sql.selectedText()
        if len(v_testo_selezionato) > 0:            
            self.e_find.setText(v_testo_selezionato)        
            self.e_find.selectAll()
        else:
            self.e_find.setText('')        
                        
        # definizione della struttura per elenco dei risultati (valido solo per find all)       
        self.find_all_model = QStandardItemModel()        
        self.o_find_all_result.setModel(self.find_all_model)
        # attivo la checkbox per la ricerca anche nella view (se aperta)
        self.set_find_in_view_visible()        

    def slot_find_all(self):
        """
           Ricerca della stringa in tutto il testo
        """
        # pulisco elenco
        self.find_all_model.clear()     
        
        # individuo se lavorare sull'editor o sulla view
        if self.e_find_into_view.isChecked() and self.view_is_visible():
            v_editor = self.e_sql_view
        else:
            v_editor = self.e_sql   
        
        # creo la mappa delle procedure-function presenti nel testo per aggiungere il loro nome ai risultati
        v_lista_def = estrai_procedure_function(v_editor.text().split('\n'))            

        # prelevo la stringa da ricercare
        v_string_to_search = self.e_find.text()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                        
            # lancio la ricerca su tutto e senza effetti a video (da notare come findFirst è un metodo di QScintilla)...
            v_found = v_editor.findFirst(v_string_to_search, False, False, False, False, True, 0, 0, False, False, False)
            # ciclo alla ricerca di tutte le ricorrenze            
            v_num = 1
            while v_found:
                # ricavo la posizione in coordinate dove è stata trovata la stringa
                v_start_line, v_start_pos, v_end_line, v_end_pos = v_editor.getSelection()
                # inizio a costruire la riga di risultato che riporta il numero della riga dove stringa trovata + il suo testo 
                v_risultato = str(v_start_line + 1) + ' - '
                
                # aggiunta del nome della procedure-function se presente                
                v_index = -1
                for v_def in v_lista_def:                
                    # controllo in quale procedure-function è stata trovata la stringa
                    v_index += 1
                    if v_start_line > v_lista_def[0].numero_riga_testo:                        
                        if v_def.numero_riga_testo == (v_start_line + 1):
                            v_risultato = v_risultato + ' [' + v_def.nome_definizione.upper() + '] ' 
                            break
                        elif v_def.numero_riga_testo > v_start_line and (v_index - 1) > -1:
                            v_risultato = v_risultato + ' [' + v_lista_def[v_index-1].nome_definizione.upper() + '] ' 
                            break
                        elif v_index == (len(v_lista_def) -1):
                            v_risultato = v_risultato + ' [' + v_def.nome_definizione.upper() + '] ' 
                            break

                # per prendere la riga devo fare una selezione di tutta riga... (fino all'inizio della riga successiva visto che non conosco il fine riga...)
                v_editor.setSelection(v_start_line, 0, v_start_line + 1, -1)
                # aggiungo al numero di riga il testo completo della riga (vado ad eliminare spazi a sinistra e ritorni a capo)
                v_risultato = v_risultato + v_editor.selectedText().lstrip()
                v_risultato = v_risultato.replace('\n','')
                # aggiungo il risultato all'elenco
                self.find_all_model.appendRow(QStandardItem(v_risultato))        
                # lancio la ricerca alla riga successiva
                v_found = v_editor.findFirst(v_string_to_search, False, False, False, False, True, v_start_line + 1, -1, False, False, False)                        
                # conto le ricorrenze
                v_num += 1
            
            # se trovate più ricorrenze ... mi posiziono sulla prima rilanciando la ricerca dall'inizio...
            if v_num > 1:
                # lancio la ricerca su tutto e senza effetti a video (da notare come findFirst è un metodo di QScintilla)...
                v_found = v_editor.findFirst(v_string_to_search, False, False, False, False, True, 0, 0, False, False, False)

            # se richiesto di evidenziare il testo, richiamo specifica funzione che ricerca il testo e lo fissa con colore specificato 
            if self.e_highlight_check.isChecked():                                                
                v_qcolor = self.e_highlight_color.currentData()                
                self.slot_find_all_highlight(v_string_to_search, v_qcolor)
     
    def slot_e_highlight_check(self):
        """
           Evento che si attiva sul cambio della checkbox e_highlight_check e che attiva/disattiva la combobox per la scelta del colore 
        """
        if self.e_highlight_check.isChecked():
            self.e_highlight_color.setEnabled(True)
        else:
            self.e_highlight_color.setEnabled(False)

    def slot_clear_all_highlights(self):
        """
           Evento che si attiva sul click del bottone b_clear_all_highlights e svolge la pulizia di tutte le evidenziazioni
        """
        doc_len = self.e_sql.length()
        # scorro l'array che contiene gli indicatori attivi e li cancello dal testo
        for v_indicator in self.v_array_indicator:            
            self.e_sql.SendScintilla(self.e_sql.SCI_SETINDICATORCURRENT,v_indicator)
            self.e_sql.SendScintilla(self.e_sql.SCI_INDICATORCLEARRANGE,0, doc_len)
        # pulisco array con elenco degli indicatori
        self.v_array_indicator.clear()

    def slot_find_all_highlight(self, p_stringa: str, color: QColor):
        """
           Nell'ambito della ricerca di tutte le ricorrenze, evidenzia con il colore scelto le stringhe corrispondenti
        """
        if not p_stringa:
            return

        # calcolo un nuovo indicatore (tra 0 e 31) ma per sicurezza mi tengo tra il 10 e il 31                
        v_indicator = len(self.v_array_indicator) + 11
        if v_indicator > 31:
            return
        else:
            self.v_array_indicator.append(v_indicator)

        # definisco lo stile “straight box” per evidenziare la parola e il rispettivo colore scelto dall'utente
        self.e_sql.indicatorDefine(QsciScintilla.IndicatorStyle.StraightBoxIndicator,v_indicator)
        self.e_sql.setIndicatorDrawUnder(True, v_indicator)        
        self.e_sql.setIndicatorForegroundColor(color, v_indicator)

        # ciclo di ricerca della stringa indicata...
        v_found = self.e_sql.findFirst(p_stringa, False, False, False, False, True, 0, 0, False, False, False)
        while v_found:
            # prendo la selezione
            sl, si, el, ei = self.e_sql.getSelection()
            # converto in offset assoluti
            start  = self.e_sql.positionFromLineIndex(sl, si)
            end    = self.e_sql.positionFromLineIndex(el, ei)
            length = end - start
            # applico l’indicatore 
            self.e_sql.SendScintilla(self.e_sql.SCI_SETINDICATORCURRENT,v_indicator)
            self.e_sql.SendScintilla(self.e_sql.SCI_INDICATORFILLRANGE,start, length)
            # prossimo match                            
            v_found = self.e_sql.findFirst(p_stringa, False, False, False, False, True, sl + 1, -1, False, False, False)                        
        
    def slot_find_all_click(self, p_index):
        """
           Partendo dalla selezione di find_all, si posiziona sulla specifica riga di testo dell'editor
        """
        # individuo se lavorare sull'editor o sulla view
        if self.e_find_into_view.isChecked() and self.view_is_visible():
            v_editor = self.e_sql_view
        else:
            v_editor = self.e_sql   

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
                v_editor.setCursorPosition(int(v_goto_line)-1,0)    
                # eseguo la ricerca in modo da evidenziare il contenuto            
                v_found = v_editor.findFirst(v_string_to_search, False, False, False, False, True, int(v_goto_line)-1, 0, True, False, False)
                                
    def slot_find_next(self):
        """
           Ricerca la prossima ricorrenza verso il basso
        """     
        # individuo se lavorare sull'editor o sulla view
        if self.e_find_into_view.isChecked() and self.view_is_visible():
            v_editor = self.e_sql_view
        else:
            v_editor = self.e_sql   

        v_string_to_search = self.e_find.text()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                       
            # lancio la ricerca dicendo di posizionarsi sulla prossima ricorrenza 
            v_found = v_editor.findFirst(v_string_to_search, False, False, False, False, True, -1, -1, True, False, False)
            # se sono arrivato alla fine, chiedo se si desidera ripartire dall'inizio...da notare come viene poi richiamata questa stessa funzione!
            if not v_found:
                if message_question_yes_no(QCoreApplication.translate('MSql_win2','Passed the end of file!')+chr(10)+QCoreApplication.translate('MSql_win2','Move to the beginnig?')) == 'Yes':                    
                    v_editor.setCursorPosition(0,0)
                    self.slot_find_next()

    def slot_find_e_replace(self):
        """
           Ricerca e sostituisci
        """
        # se è stato selezionato del testo lo utilizzo come base per la ricerca
        v_testo_selezionato = self.e_sql.selectedText()
        if len(v_testo_selezionato) > 0:            
            self.e_replace_search.setText(v_testo_selezionato)        
            self.e_replace_search.selectAll()
        else:
            self.e_replace_search.setText('')        
        
        # apro la sezione di ricerca e posiziono il fuoco del cursore
        self.dockReplaceWidget.show()        
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
            # se sono arrivato alla fine, chiedo se si desidera ripartire dall'inizio...da notare come viene poi richiamata questa stessa funzione!
            if not v_found:
                if message_question_yes_no(QCoreApplication.translate('MSql_win2','Passed the end of file!')+chr(10)+QCoreApplication.translate('MSql_win2','Move to the beginnig?')) == 'Yes':                    
                    self.e_sql.setCursorPosition(0,0)
                    self.slot_find_e_replace_find()
    
    def slot_find_e_replace_next(self):        
        """
           Sostituisce la ricorrenza attuale (ignora differenze tra maiuscole e minuscole)
        """
        # testo da ricercare
        v_string_to_search = self.e_replace_search.text().upper()
        # testo da sostituire
        v_string_to_replace = self.e_replace.text()

        # se inserito una stringa di ricerca...e di sostituzione
        if v_string_to_search != '' and v_string_to_replace != '':    
            # se il testo selezionato è esattamente ciò che si sta cercando, faccio la replace 
            if self.e_sql.selectedText() == v_string_to_search:                    
                # eseguo la replace
                self.e_sql.replace(v_string_to_replace)                
                # ricerco la prossima ricorrenza
                self.slot_find_e_replace_next()
            # ... altrimenti continuo come se fosse una ricerca next
            else:
                # ricavo la posizione dove è posizionato il cursore 
                v_start_line, v_start_pos = self.e_sql.getCursorPosition()
                # lancio la ricerca a partire da quella posizione
                v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, v_start_line, v_start_pos, False, False, False)            
                # se sono arrivato alla fine, chiedo se si desidera ripartire dall'inizio...da notare come viene poi richiamata questa stessa funzione!
                if not v_found:
                    if message_question_yes_no(QCoreApplication.translate('MSql_win2','Passed the end of file!')+chr(10)+QCoreApplication.translate('MSql_win2','Move to the beginnig?')) == 'Yes':                    
                        self.e_sql.setCursorPosition(0,0)
                        self.slot_find_e_replace_next()

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
                # sostituito con findnext in quanto se la stringa da ricercare conteneva un pezzo della stringa da sostituire, poi andava in loop
                # v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, v_start_line, v_start_pos + 1, False, False, False)                        
                v_found = self.e_sql.findNext()

    def slot_goto_line(self):
        """
           Visualizza window per richiedere a che riga dell'editor posizionarsi e poi si posiziona
        """
        try:
            # visualizzo la finestra di richiesta numero riga
            self.dialog_goto_line.show()
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog per chiedere i dati
            self.dialog_goto_line = QDialog()
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
            message_error(QCoreApplication.translate('MSql_win2','Insert a valid number!'))
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
        self.map_model = QStandardItemModel()        
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
                v_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)   
                self.map_model.setItem(v_y-1, 1, v_item)                                            
        # carico il modello nel widget        
        self.o_map.setModel(self.map_model)                                   
        # indico che la larghezza delle colonne si deve adattare al contenuto
        self.o_map.resizeColumnsToContents()        
        
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
            message_info(QCoreApplication.translate('MSql_win2',"Please select a text with SQL statement!"))
            return 'ko'

        # elimino il testo selezionato 
        self.e_sql.cut()
        # chiamo la reindentazione del testo (trasformando tutto in mauiscolo)
        v_testo_sel = format_sql(v_testo_sel).upper()
        # inserisco il nuovo testo al posto di quello eliminato
        self.e_sql.insert(v_testo_sel)      

    def slot_extract_sql_from_output(self):
        """
           Creo una nuova select partendo dall'output. Questa cosa ha un senso solo quando
           l'utente inserisce dei filtri a livello di colonne di output
        """        
        self.e_sql.insert(self.v_select_eseguita)      

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
    
    def slot_comment_from_function(self):
        """
           Partendo dalla selezione di testo dove presente la parte dichiarativa di una funzione-procedura PL-SQL,
           crea il commento di documentazione iniziale con Autore, Data creazione, Descrizione, Parametri input-output
        """
        global o_global_preferences

        if self.e_sql.selectedText() == '':     
            message_info(QCoreApplication.translate('MSql_win1','Select the text that includes the declaration of a PL-SQL function-procedure to obtain a comment reporting: Author, Creation date, Description and input-output parameters'))
            return 'ko'
                
        # partendo dal testo selezionato che deve avere una dichiarazione di PROCEDURE-FUNCTION e relativi parametri, apro un window dove ci sarà 
        # riportato commento con intestazione e documentazione della stessa 
        v_commento = commenta_una_procedura_funzione(self.e_sql.selectedText(), o_global_preferences.author_name)

        # creazione della window
        self.o_win_commento = QWidget()
        self.o_win_commento.setWindowTitle("MSql-Create procedure-function comment")
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.o_win_commento.setWindowIcon(v_icon)
        self.o_win_commento.setGeometry(0, 0, 900, 300)

        # nella window inserisco un item di testo dove andrà visualizzato il commento che è stato creato
        layout = QVBoxLayout()        
        v_text_edit = QTextEdit()
        v_text_edit.setFont(QFont("Courier New",11))        
        v_text_edit.setPlainText(v_commento)

        # visualizzo la window
        layout.addWidget(v_text_edit)
        self.o_win_commento.setLayout(layout)
        self.o_win_commento.show()
        # centro la window rispetto alla window padre
        centra_window_figlia(self, self.o_win_commento)
        
    def slot_indent_to_cursor(self):
        """
           Indenta la riga dove è presente il cursore, alla posizione del cursore (in pratica inserisce spazi bianchi)
        """
        # prendo coordinate cursore 
        v_num_line, v_pos = self.e_sql.getCursorPosition()                     
        if v_pos > 1:            
            # estraggo l'intera riga dove è posizionato il cursore ed elmino gli spazi e i tab a sinistra
            # attenzione! se ci sono dei tab, il cursore avrà un numero di colonna inferiore e quindi l'indentazione risulterà sporca
            #             in questi casi, l'utente deve riposizionarsi e dare di nuovo il comando
            self.e_sql.setSelection(v_num_line, 0, v_num_line+1, -1)                        
            v_line = self.e_sql.selectedText().lstrip()            
            # aggiungo tanti spazi quanto è la posizione in colonna del cursore                        
            v_line = (' ' * v_pos) + v_line            
            # elimino la riga
            self.e_sql.removeSelectedText()
            # inserisco la riga
            self.e_sql.insert(v_line)
            # posiziono il cursore
            self.e_sql.setCursorPosition(v_num_line,v_pos)

    def slot_text_to_ascii_art(self):
        """
           Trasforma il testo selezionato in arte grafica ascii
        """
        global v_global_font_ascii_art

        # estraggo il testo selezionato        
        v_text = self.e_sql.selectedText().lstrip().rstrip()            
        # se non è stato selezionato alcun testo --> errore
        if v_text == '':
            message_error(QCoreApplication.translate('MSql_win1','No text selected!'))
            return 'ko'
        # elimino il testo selezionato
        self.e_sql.removeSelectedText()
        # trasformo il testo in formato grafico ascii e lo inserisco nell'editor
        if v_global_font_ascii_art == '':
            self.e_sql.insert(text2art(v_text))        
        else:
            self.e_sql.insert(text2art(v_text, v_global_font_ascii_art))        
    
    def slot_indentation_guide(self):
        """
           Attiva/disattiva indentation guide sull'editor
        """        
        if self.v_indentation_guide:
            self.v_indentation_guide = False
        else:
            self.v_indentation_guide = True
        
        self.e_sql.setIndentationGuides(self.v_indentation_guide)                       
    
    def slot_add_bookmark(self, margin_nr, line_nr, state):
        """
           Aggiunge o toglie un segnalibro. Sarà possibile scorrere tra i segnalibri premendo CTRL+B
        """
        # se premuto il tasto CTRL --> tolgo il segnalibro
        if state == Qt.KeyboardModifier.ControlModifier:                                
            # controllo se esiste un segnalibro alla riga indicata in input e se esiste lo elimino
            if self.e_sql.markersAtLine(line_nr) != -1:                                 
                self.e_sql.markerDelete(line_nr)            
        # se premuto solo il tasto sinistro del mouse --> aggiungo il segnalibro
        else:            
            self.v_segnalibro = self.e_sql.markerAdd(line_nr, 0)        

    def slot_ctrl_b(self):
        """
           Passa da un segnalibro all'altro partendo dall'attuale posizione del cursore
        """        
        # prendo attuale posizione del cursore
        v_pos_line, v_pos_column = self.e_sql.getCursorPosition()
        # passo al prossimo segnalibro
        v_new_pos = self.e_sql.markerFindNext(v_pos_line+1, 1 << 0)
        # se arrivato in fondo all'ultimo segnalibro, la funzione di cui sopra mi restituisce -1...
        if v_new_pos == -1:        
            # riparto da capo con la ricerca (riga 0)
            v_new_pos = self.e_sql.markerFindNext(0, 1 << 0)        
        # se ottenuto la riga su cui posizionarmi --> riposiziono il cursore
        if v_new_pos != -1:
            # posiziono il cursore sulla riga indicata
            self.e_sql.setCursorPosition(v_new_pos,0)        
            # se la mimimappa è visualizzata, devo sincronizzare anche quella
            if self.v_mini_map_visible:
                self.e_sql_mini_map.setCursorPosition(v_new_pos,0)        

    def scrive_output(self, p_messaggio, p_tipo_messaggio):
        """
           Scrive p_messaggio nella sezione "output" precedendolo dall'ora di sistema
        """
        global o_global_preferences
        
        # definizione dei pennelli per scrivere il testo in diversi colori (i nomi fanno riferimento al tema chiaro)
        v_pennello_rosso = QTextCharFormat()
        v_pennello_blu = QTextCharFormat()
        v_pennello_nero = QTextCharFormat()
        v_pennello_verde = QTextCharFormat()
        if o_global_preferences.dark_theme:            
            v_pennello_rosso.setForeground(Qt.GlobalColor.red)            
            v_pennello_blu.setForeground(Qt.GlobalColor.cyan)            
            v_pennello_nero.setForeground(Qt.GlobalColor.white)            
            v_pennello_verde.setForeground(Qt.GlobalColor.green)
        else:            
            v_pennello_rosso.setForeground(Qt.GlobalColor.red)            
            v_pennello_blu.setForeground(Qt.GlobalColor.blue)            
            v_pennello_nero.setForeground(Qt.GlobalColor.black)            
            v_pennello_verde.setForeground(Qt.GlobalColor.darkGreen)

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
        self.o_output.moveCursor(QTextCursor.MoveOperation.End)                
        # porto in primo piano la visualizzazione del tab di output
        self.o_tab_widget.setCurrentIndex(1)                         
        
    def slot_output_find_all(self):
        """
           Ricerca della stringa in tutto il testo della sezione output pl-sql! 
           Attenzione! Questa è la ricerca nell'output del testo pl-sql e non della ricerca nell'editor
           Attenzione! La ricerca di fatto avviene due volte...la prima volta per caricare la lista laterale dove vengono riportate le righe dove la stringa presente
                       Poi un secondo passaggio con cui si evidenziano tutte le ricorrenze e si salvano all'interno di un array le varie posizioni per poi poter fare F3
                       La cosa è uscita un po' pasticciata per quanto riguarda anche l'uso di variabili d'oggetto.
        """        
        # definizione della struttura-modello per elenco dei risultati (valido solo per find all)       
        self.output_find_all_model = QStandardItemModel()        
        self.o_output_lst_result.setModel(self.output_find_all_model)

        # prelevo la stringa da ricercare
        v_string_to_search = self.e_output_find.text()
        
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                        
            # lancio la ricerca sul testo (la funzione richiamata si trova nel file utilita_testo.py)
            v_founds = search_string_in_text(self.o_output.toPlainText(),v_string_to_search)
            # ciclo di caricamento di tutte le ricorrenze
            for i in v_founds:
                # aggiungo il risultato al modello sotto forma di numero riga + testo della riga
                # l'elenco delle ricorrenze a fianco dell'output si aggiorna automaticamente a video                
                self.output_find_all_model.appendRow( QStandardItem(str(i[0]) + ' - ' + str(i[3])) )        

            # cancello le var di appoggio che servono per scorrere nel testo con F3
            self.v_output_posizione_corrente = 0
            self.v_output_lista_posizioni = []
            
            # prendo il cursore della sezione di output            
            v_cursor = self.o_output.textCursor()        
            v_format = QTextCharFormat()  
            # pulisco eventuali evidenziazioni precedenti
            v_cursor.select(QTextCursor.SelectionType.Document)              
            v_cursor.setCharFormat(v_format)  
            # imposto il colore del pennello per successive evidenziazioni
            v_format.setBackground(QBrush(QColor("green")))
            
            # creo una regular expression e l'associo al testo per la ricerca della stringa indicata
            re = QRegularExpression(self.e_output_find.text().upper())
            i = re.globalMatch(self.o_output.toPlainText().upper()) 

            # ricerco all'interno del testo la stringa indicata ed evidenzio il testo 
            while i.hasNext():
                match = i.next() #QRegularExpressionMatch
                # select the matched text and apply the desired format
                v_cursor.setPosition(match.capturedStart(), QTextCursor.MoveMode.MoveAnchor)
                v_cursor.setPosition(match.capturedEnd(), QTextCursor.MoveMode.KeepAnchor)
                v_cursor.mergeCharFormat(v_format)
                # salvo la posizione della stringa trovata per poter poi dare 
                # la possibilità di scorrere sulle varie posizioni del testo
                self.v_output_lista_posizioni.append(match.capturedStart())
        
    def slot_output_find_all_click(self, p_index):
        """
           Partendo dalla selezione di output_find_all, si posiziona sulla specifica riga di testo della sezione output pl-sql
           Attenzione! Questa è la ricerca nell'output del testo pl-sql e non della ricerca nell'editor
        """
        # prelevo la stringa da ricercare
        v_string_to_search = self.e_output_find.text()
        # prendo elemento dell'elenco selezionato
        v_selindex = self.output_find_all_model.itemFromIndex(p_index)
        v_stringa = v_selindex.text()               
        if v_stringa != '':
            # dalla stringa dell'elenco, estraggo il numero di riga e mi posiziono sulla riga corretta dell'output
            v_goto_line = v_stringa[0:v_stringa.find('-')]
            if v_goto_line != '':                 
                v_goto_line = int(v_goto_line)
                # riprendo il testo che è presente nell'oggetto di output e lo suddivido in righe                
                v_text = self.o_output.toPlainText()
                v_linee = v_text.split("\n")                  
                if v_goto_line <= len(v_linee):  
                    # calcolo posizione della riga
                    v_start_pos = sum(len(v_linee[i]) + 1 for i in range(v_goto_line - 1))  
                    # posiziono il cursore alla riga indicata
                    v_cursor = self.o_output.textCursor()
                    v_cursor.setPosition(v_start_pos)
                    self.o_output.setTextCursor(v_cursor)
                                                        
    def slot_output_find_next(self):
        """
           Ricerca la prossima ricorrenza verso il basso della sezione output pl-sql
           Attenzione! Questa è la ricerca nell'output del testo pl-sql e non della ricerca nell'editor
        """        
        try:
            v_ok = len(self.v_output_lista_posizioni)
        except:
            v_ok = 0
        
        # se elenco delle ricerche è vuoto, eseguo la ricerca su tutto il testo....
        # questo succede se sto facendo una nuova ricerca dopo che è cambiato l'output
        if v_ok == 0:
            self.slot_output_find_all()
            try:
                v_ok = len(self.v_output_lista_posizioni)
            except:
                v_ok = 0

        if v_ok > 0:
            # se sono arrivato alla fine delle posizioni, ricomincio da capo, tornando in cima
            if self.v_output_posizione_corrente >= len(self.v_output_lista_posizioni):
                message_info(QCoreApplication.translate('MSql_win2',"End of file! Move to beginning!"))
                self.v_output_posizione_corrente = 0
            # ricerco la posizione del testo (contenuta nella lista della posizioni precedentemente salvate)
            v_posizione = self.v_output_lista_posizioni[self.v_output_posizione_corrente]            
            # visivamente prendo il cursore dell'oggetto testo e ne reimposto la posizione
            v_cursor = self.o_output.textCursor()                                                        
            v_cursor.setPosition(v_posizione)                                                
            self.o_output.setTextCursor(v_cursor)            
            # forzo il focus 
            QTimer.singleShot(0, self.o_output.setFocus)
            # passo alla prossima posizione dell'indice
            self.v_output_posizione_corrente += 1										
    
    def set_editable(self):
        """
           Questa funzione viene richiamata quando si agisce sulla checkbox di editing
        """     
        global o_global_preferences

        # se attivato...
        if o_global_preferences.editable:
            # attivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            # pulisco la tabella costringendo l'utente a ricaricare la query in quanto deve comparire il rowid
            self.slot_clear('RES')      
        # ...
        else:
            # disattivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)            
    
    def set_emphasis(self):
        """
           Evidenzio i colori del tab risultati e output
        """
        global v_global_color
        global v_global_emphasis

        if v_global_emphasis:            
            self.o_table.setStyleSheet("QTableWidget {background-color: " + v_global_color + ";}")
            self.o_output.setStyleSheet("QPlainTextEdit {background-color: " + v_global_color + ";}")            
            self.o_bind.setStyleSheet("QTableView {background-color: " + v_global_color + ";}")
            self.o_plan.setStyleSheet("QPlainTextEdit {background-color: " + v_global_color + ";}")
            self.o_output_frame.setStyleSheet("QFrame {background-color: " + v_global_color + ";}")
        else:
            self.o_table.setStyleSheet("")
            self.o_output.setStyleSheet("")            
            self.o_bind.setStyleSheet("")
            self.o_plan.setStyleSheet("")
            self.o_output_frame.setStyleSheet("")
    
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

    def slot_highligth_selection(self):
        """
           Richiamata tramite voce del menu edit o tramite CTRL+SHIFT+H, evidenzia con il colore giallo il testo evidenziato
           Attenzione! Viene usato l'indicatore-evidenziatore nr.5 di qscintilla.                       
        """
        global o_global_preferences

        # viene usato indicatore fisso numero 5!
        v_indicator = 5
        # definisco lo stile “straight box” per evidenziare la parola 
        self.e_sql.indicatorDefine(QsciScintilla.IndicatorStyle.StraightBoxIndicator,v_indicator)
        self.e_sql.setIndicatorDrawUnder(True, v_indicator)        
        # come colore utilizzo quello impostato nell'apposita preferenza
        self.e_sql.setIndicatorForegroundColor(QColor(o_global_preferences.highlight_color_hex), v_indicator)        
        # prendo la selezione
        sl, si, el, ei = self.e_sql.getSelection()
        # converto in offset assoluti
        start  = self.e_sql.positionFromLineIndex(sl, si)
        end    = self.e_sql.positionFromLineIndex(el, ei)
        length = end - start
        # applico l’indicatore 
        self.e_sql.SendScintilla(self.e_sql.SCI_SETINDICATORCURRENT,v_indicator)
        self.e_sql.SendScintilla(self.e_sql.SCI_INDICATORFILLRANGE,start, length)
    
    def slot_editor_view(self):
        """
           Crea a fianco dell'editor principale, una view di sola lettura che replica il contenuto dell'editor principale   
           Se la funzione viene richiamata e la view è già presente, la toglie
        """
        if self.view_is_visible():
            # tolgo la view
            self.view_splitter.deleteLater()
            del self.view_splitter
            return 'ok'
        # creo la view            
        self.view_splitter = QSplitter(parent=self.splitter_2)
        self.view_splitter.setOrientation(Qt.Orientation.Vertical)
        self.view_splitter.setObjectName("view_splitter")
        self.e_sql_view = QsciScintilla(parent=self.view_splitter)
        self.e_sql_view.setObjectName("e_sql_view")
        # attivo il lexer sulla view        
        self.v_lexer_view = My_MSql_Lexer(self.e_sql_view, False)                
        self.e_sql_view.setLexer(self.v_lexer_view)
        # imposto la view come sola lettura
        self.e_sql_view.setReadOnly(True)        
        # imposto il testo della view uguale a quello dell'editor
        self.e_sql_view.setText(self.e_sql.text())
        # modifico il rapporto di divisione tra editor e view   
        self.splitter_2.setStretchFactor(0,10)                
        self.splitter_2.setStretchFactor(2,10)       
        # attivo la checkbox per la ricerca anche nella view
        self.set_find_in_view_visible()        

    def set_find_in_view_visible(self):        
        """ 
           In base al fatto che la view sia aperta, nella sezione di ricerca testo, viene attivata la checkbox per la ricerca anche nella view
        """        
        self.label_find_into_view.setVisible(self.view_is_visible())
        self.e_find_into_view.setVisible(self.view_is_visible())

    def slot_find_in_view_click(self):
        """
           Evento richiamato quando viene attivata/disattivata la checkbox di ricerca anche nella view
        """
        if self.e_find_into_view.isChecked() and self.view_is_visible():
            v_visible = False
        else:       
            v_visible = True
        # sezione degli highlight che nel caso della ricerca nella view vengono disattivati perché altrimenti un po' un casino attivarli anche li
        self.e_highlight_check.setVisible(v_visible)  
        self.label_highlight.setVisible(v_visible)         
        self.b_clear_all_highlights.setVisible(v_visible)        
        self.e_highlight_color.setVisible(v_visible)        

    def view_is_visible(self):
        """
           Restituisce True se la view è visibile, False altrimenti
        """
        if hasattr(self, 'view_splitter'):
            return True
        else:   
            return False
        
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
                message_error(p_variabile_tipo + ' - ' + QCoreApplication.translate('MSql_win2','Unrecognized type'))
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
            # se il dizionario non è vuoto prendo solo i valori del dizionario e li porto nelle strutture di appoggio (da notare la getvalue...è un metodo che appartiene all'oggetto var di oracledb)
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
                        # creo una var di oracledb! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(str)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto oracledb.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )
                    if self.v_variabili_bind_tipo[i].find('NUMBER') != -1: 
                        # creo una var di oracledb! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(int)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto oracledb.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )
                    if self.v_variabili_bind_tipo[i].find('DATE') != -1:                         
                        # creo una var di oracledb! e gli assegno il valore della bind che sto copiando nel dizionario
                        v_valore = self.v_cursor.var(datetime.date)
                        v_valore.setvalue(0,self.v_variabili_bind_valore[i])
                        # carico elemento del dizionario composto da nome della bind e dal suo valore che è espresso con un oggetto oracledb.var
                        self.v_variabili_bind_dizionario.update( {self.v_variabili_bind_nome[i] : v_valore } )            
                print('Creazione dizionario variabili bind...')
                print(self.v_variabili_bind_dizionario)
                print('-'*50)
            # esco --> tutto ok
            return 'ok'
                                    
        # Aggiornamento a video variabili bind
        # lista contenente le intestazioni
        if p_function in ('SHOW','ADD'):
            # se il dizionario non è vuoto prendo solo i valori del dizionario e li porto nelle strutture di appoggio (da notare la getvalue...è un metodo che appartiene all'oggetto var di oracledb)
            if len(self.v_variabili_bind_dizionario) != 0:                
                for chiave, valore in self.v_variabili_bind_dizionario.items():                    
                    v_index = self.v_variabili_bind_nome.index(chiave)                    
                    self.v_variabili_bind_valore[v_index] = valore.getvalue(0)                    

            # preparo la struttura della tabella che visualizza l'oggetto :binds
            intestazioni = ['Name','Type','Value' ]                                
            self.bind_risultati = QStandardItemModel()        
            self.bind_risultati.setHorizontalHeaderLabels(intestazioni)                
            self.bind_risultati.setColumnCount(len(intestazioni))                
            self.bind_risultati.setRowCount(0)                        

            for y in range(0,len(self.v_variabili_bind_nome)):            
                # colonna Name
                v_item = QStandardItem()                
                v_item.setText(str(self.v_variabili_bind_nome[y]))            
                self.bind_risultati.setItem(y, 0, v_item )  
                # colonna Tipo di dato
                v_item = QStandardItem()                
                v_item.setText(str(self.v_variabili_bind_tipo[y]))            
                self.bind_risultati.setItem(y, 1, v_item )  
                # colonna Valore
                v_item = QStandardItem()                
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
        v_string_lines_and_length = QCoreApplication.translate('MSql_win1','Lines:') + ' ' + str(v_totale_righe) + ', ' + QCoreApplication.translate('MSql_win1','Length:') + ' ' + str(self.e_sql.length())
        self.link_to_MSql_win1_class.l_num_righe_e_char.setText(v_string_lines_and_length)        

        # reimposta larghezza del margine numeri di riga...
        self.e_sql.setMarginWidth(0, '0' + v_totale_righe)        

        # label indicatore di overwrite
        if self.v_overwrite_enabled:
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText(QCoreApplication.translate('MSql_win1','Overwrite'))
        else:                
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText(QCoreApplication.translate('MSql_win1','Insert'))

        # label che indica il tipo di codifica                
        if self.setting_utf8:            
            self.link_to_MSql_win1_class.l_utf8_enabled.setText('UTF-8')
            self.link_to_MSql_win1_class.l_utf8_enabled.setStyleSheet('background-color: ' + v_global_color + ';color: "' + v_global_background + '";')              
        else:
            self.link_to_MSql_win1_class.l_utf8_enabled.setText("ANSI")
            self.link_to_MSql_win1_class.l_utf8_enabled.setStyleSheet('')              

        # label che indica il tipo di eol 
        if self.setting_eol == 'W':        
            self.link_to_MSql_win1_class.l_eol.setText("Windows (CRLF)")         
        else:            
            self.link_to_MSql_win1_class.l_eol.setText("Unix (LF)")         

        # posizione del cursore (i tab vengono conteggiati per il numero di spazi che occupano!)
        v_y, v_x = self.e_sql.getCursorPosition()
        v_line = self.e_sql.text(v_y)
        v_tab_larghezza = self.e_sql.tabWidth()
        v_visual_col = 1
        for i in range(v_x):
            if v_line[i] == '\t':
                v_visual_col += v_tab_larghezza
            else:
                v_visual_col += 1
        self.link_to_MSql_win1_class.l_cursor_pos.setText("Ln: " + str(v_y+1) + "  Col: " + str(v_visual_col))

        # tempo di esecuzione ultima istruzione                
        v_total_seconds = datetime.timedelta(seconds=v_global_exec_time).total_seconds()
        v_hours, v_remainder = divmod(v_total_seconds, 3600)
        v_minutes, v_remainder = divmod(v_remainder, 60)
        v_seconds, v_microseconds = divmod(v_remainder, 1)
        v_tenths_of_second = int(v_microseconds * 100)
        v_tempo_formattato = f"{int(v_hours):02}:{int(v_minutes):02}:{int(v_seconds):02}.{v_tenths_of_second:02}"
        self.link_to_MSql_win1_class.l_exec_time.setText(QCoreApplication.translate('MSql_win1','Last execution time:') + ' ' + v_tempo_formattato)

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

#  ____   ___  __  __ 
# / ___| |_ _||  \/  |
# \___ \  | | | |\/| |
#  ___) | | | | |  | |
# |____/ |___||_|  |_|
# Single Instance Manager                    
def slot_open_file_from_SIM(p_path):
    """
       Gestione richiesta di apertura file da altra istanza di MSql (v. definizione della classe classSingleInstanceManager)
    """
    print('Ricevuto richiesta di apertura file da parte di altre istanza MSql del file: '+p_path)
    # creo un'azione che fa scattare lo smistamento delle voci di menu indicando che si richiede un open ma specifico da istanza esterna
    v_azione = QAction()
    v_azione.setText(QCoreApplication.translate('MSql_win1','OPEN_FROM_SIM'))
    # nel none dell'oggetto azione, ci metto il nome del file da aprire...per comodità di smistamento voce di menu
    v_azione.setObjectName(p_path)
    application.smistamento_voci_menu(v_azione)      

#
#  ____ _____  _    ____ _____ 
# / ___|_   _|/ \  |  _ \_   _|
# \___ \ | | / _ \ | |_) || |  
#  ___) || |/ ___ \|  _ < | |  
# |____/ |_/_/   \_\_| \_\|_|  
#
if __name__ == "__main__":    
    # nome programma
    QCoreApplication.setApplicationName("MSql")    
    # se il programma è eseguito da pyinstaller, cambio la dir di riferimento passando a dove si trova l'eseguibile
    # in questo modo dovrebbe riuscire a trovare tutte le risorse
    if getattr(sys, 'frozen', False): 
        v_dir_eseguibile = os.path.dirname(sys.executable)
        os.chdir(v_dir_eseguibile)
        QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons'))
        QDir.addSearchPath('logos', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logos'))
        v_view_splash = True
    else:
        v_view_splash = False
                
    # controllo se programma è stato richiamato da linea di comando passando il nome di un file    
    v_nome_file_da_caricare = ''
    try:
        if sys.argv[1] != '':                
            v_nome_file_da_caricare = sys.argv[1]    
            # la pathname viene normalizzata
            v_nome_file_da_caricare = os.path.normpath(v_nome_file_da_caricare)
    except:
        pass    

    # controllo se esiste dir di lavoro (servirà per salvare le preferenze, ecc....)        
    if not os.path.isdir(v_global_work_dir):
        os.makedirs(v_global_work_dir)

    # sovrascrive l'hook delle eccezioni; in pratica se avverrà un errore imprevisto, 
    # uscirà messaggio a video e il programma non andrà in crash...
    sys.excepthook = excepthook

    # creazione del servizio che serve per capire se MSql è già in esecuzione in altra istanza
    v_MSql_SIM = classSingleInstanceManager('MSql_SIM')  
    # se esiste un'istanza, invia i file ed esce-termina
    if v_nome_file_da_caricare != '' and v_MSql_SIM.try_send_to_running_instance(v_nome_file_da_caricare):
        print('MSql già attivo --> apro il file in quella istanza e termino questa!')
        sys.exit()
    # altrimenti avvia come istanza primaria
    if not v_MSql_SIM.start_listening():
        # non sono riuscito a mettermi in ascolto: termina        
        print('Non riesco a capire se MSql è già attivo!')
        sys.exit()

    # eventuale preferenza di zoom di tutto il programma (introdotto a partire PyQt6)    
    os.environ['QT_SCALE_FACTOR'] = str(o_global_preferences.general_zoom / 100)

    # creazione dell'applicazione interfaccia QT
    app = QApplication(sys.argv)     
    
    # carica l'immagine dello splash screen e lo mantiene visualizzato per 3 secondi
    if v_view_splash:
        v_pixmap = QPixmap("logos:MSql.png").scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio) 
        v_splash = QSplashScreen(v_pixmap) 
        v_splash.show()         
    
    # se è stato scelto di avere il tema dei colori scuro, lo carico
    # Attenzione! La parte principale del tema colori rispetta il meccanismo di QT library
    #             Mentre per la parte di QScintilla ho dovuto fare le impostazioni manuali (v. definizione del lexer)
    if o_global_preferences.dark_theme:        
        app.setStyleSheet(dark_theme_definition())                    
            
    # carico eventuali traduzioni se la lingua è diversa rispetto all'inglese        
    # se il programma è eseguito da pyinstaller, cambio la dir di riferimento passando a dove si trova l'eseguibile
    if getattr(sys, 'frozen', False):         
        v_dir_qtlinguist = "_internal/qtlinguist/"
    else:
        v_dir_qtlinguist = "qtlinguist"
    if o_global_preferences.app_language == 'Italian':
        translate = QTranslator()
        if translate.load("02 - MSql_linguist_it.qm",v_dir_qtlinguist):            
            app.installTranslator(translate)          

    ##
    # AVVIO DEL PROGRAMMA con creazione dell'oggetto della window1 (aprendo eventuale file indicato su linea di comando)   
    ##
    application = MSql_win1_class(v_nome_file_da_caricare)             
    # collego il segnale per i futuri file inviati    
    v_MSql_SIM.messageReceived.connect(slot_open_file_from_SIM)
    # dimensioni della window
    application.carico_posizione_window()      
    # mostro la window principale    
    application.show()

    # nascondo la splash screen
    if v_view_splash:
        v_splash.close()
    
    # se il programma è in esecuzione da pyinstaller...controllo se c'è una nuova versione del programma disponibile, e avverto di installarla    
    # viene controllata solo la data perché controllando anche ore e minuti, finisce che passa il minuto rispetto a quando viene pacchettizzato e gli orari non coincidono
    if getattr(sys, 'frozen', False):     
        try:        
            v_build_timestamp = time.strftime("%Y-%m-%d",time.localtime(os.path.getmtime(sys.executable)))                        
            v_setup_timestamp = time.strftime("%Y-%m-%d",time.localtime(os.path.getmtime("O:/Install/MSql_setup/MSql_setup.exe")))                
            if v_build_timestamp < v_setup_timestamp:
                message_info(QCoreApplication.translate('MSql_win1',"A new version of MSql Editor is aviable! Please go to O:\\Install\\MSql_setup and install it! Once installed, don't forget to check the changelog to see what's new!"))
        except:
            pass
            
    # attivazione e gestione degli eventi
    sys.exit(app.exec())    