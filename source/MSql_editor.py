# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 01/01/2023
 Descrizione...: Questo programma ha la "pretesa" di essere una sorta di piccolo editor SQL per ambiente Oracle....            
                 al momento si tratta più di un esperimento che di qualcosa di utilizzabile.
                 In questo programma sono state sperimentate diverse tecniche!
"""

# Librerie di base
import sys, os, datetime
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
# Nota bene! Quando tramite pyinstaller verrà creato l'eseguibile, tutti i file della cartella qtdesigner verranno messi 
#            nella cartella principale e questa istruzione di cambio path di fatto non avrà alcun senso. Serve dunque solo
#            in fase di sviluppo. 
sys.path.append('qtdesigner')
# Librerie di data base
import cx_Oracle, oracle_my_lib
# Librerie grafiche QT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import Qsci
# Libreria per export in excel
from xlsxwriter.workbook import Workbook
# Classe per la gestione delle preferenze
from preferences import preferences_class
# Classi qtdesigner (win1 è la window principale, win2 la window dell'editor e win3 quella delle info di programma)
from MSql_editor_win1_ui import Ui_MSql_win1
from MSql_editor_win2_ui import Ui_MSql_win2
from MSql_editor_win3_ui import Ui_MSql_win3
# Classi qtdesigner per la ricerca e la sostituzione di stringhe di testo, e per il posizionamento
from find_ui import Ui_FindWindow
from find_e_replace_ui import Ui_Find_e_Replace_Window
from goto_line_ui import Ui_GotoLineWindow
# Classe qtdesigner per la richiesta di connessione
from connect_ui import Ui_connect_window
# Classe per visualizzare la barra di avanzamento 
from avanzamento import avanzamento_infinito_class
# Utilità varie
from utilita import *
from utilita_database import *

# Tipi oggetti di database
Tipi_Oggetti_DB = { 'Tables':'TABLE',                    
                    'Package body':'PACKAGE BODY',
                    'Package': 'PACKAGE',                    
                    'Procedures':'PROCEDURE',
                    'Functions':'FUNCTION',
                    'Trigger':'TRIGGER',
                    'Views':'VIEW',
                    'Sequences':'SEQUENCE' }

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
# Oggetto che carica le preferenze tramite l'apposita classe
o_global_preferences = preferences_class(v_global_work_dir + 'MSql.ini')
# Contiene le coordinate della main window
v_global_main_geometry = object

class My_MSql_Lexer(Qsci.QsciLexerSQL):
    """
        Questa classe amplifica il dizionario di default del linguaggio SQL presente in QScintilla.
        In pratica aggiunge tutti i nomi di tabelle, viste, procedure, ecc. in modo vengano evidenziati
        Si base sulla lista v_global_my_lexer_keywords che viene caricata quando ci si connette al DB
        In base al valore di index è possibile settare parole chiave di una determinata categoria
        1 = parole primarie ,2 = parole secondarie, 3 = commenti, 4 = classi, ecc.. usato 8 (boh!) 
    """
    def keywords(self, index):
        global v_global_my_lexer_keywords        

        keywords = Qsci.QsciLexerSQL.keywords(self, index) or ''
        
        if index == 8:            
            if len(v_global_my_lexer_keywords) > 0:                                            
                v_new_keywords = ''
                for v_keyword in v_global_my_lexer_keywords:
                     v_new_keywords += v_keyword.lower() + ' '                                     
                return  v_new_keywords + keywords
        
        return keywords

def salvataggio_editor(p_save_as, p_nome, p_testo):
    """
        Salvataggio di p_testo dentro il file p_nome        
        Se p_save_as è True --> viene salvato come nuovo file
    """
    global o_global_preferences

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
        p_nome_file_da_caricare indica eventuale da aprire all'avvio
    """       
    def __init__(self, p_nome_file_da_caricare):
        global o_global_preferences    
        global v_global_main_geometry    

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win1_class, self).__init__()        
        self.setupUi(self)
        # forzo la dimensione della finestra. Mi sono accorto che questa funzione, nella gestione MDI
        # è importante in quanto permette poi al connettore dello smistamento menu di funzionare sulla
        # prima finestra aperta....rimane comunque un mistero questa cosa.....
        self.showNormal()        

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
        self.l_numero_righe = QLabel()
        self.l_numero_righe.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_numero_righe)                
        self.l_numero_righe.setText("Lines: 0")
        # Numero totale di caratteri di testo
        self.l_numero_caratteri = QLabel()
        self.l_numero_caratteri.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_numero_caratteri)                
        self.l_numero_caratteri.setText("Length: 0")
        # Stato attivazione inserito di testo o overwrite
        self.l_overwrite_enabled = QLabel("INS")
        self.l_overwrite_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_overwrite_enabled)
        # Stato attivazione codifica utf-8
        self.l_utf8_enabled = QLabel()
        self.l_utf8_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_utf8_enabled)        
        # Informazioni sulla connessione
        self.l_connection = QLabel("Connection:")
        self.l_connection.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.l_connection.setStyleSheet('color: black;')
        self.statusBar.addPermanentWidget(self.l_connection)                

        ###
        # definizione della dimensioni dei dock laterali (sono 3, vengono raggruppati e definite le proporzioni)
        ###
        self.docks = self.dockWidget, self.dockWidget_2, self.dockWidget_3
        widths = 10, 10, 1
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
        # Definizione della struttura per gestione SQL History
        ###
        self.m_history = QtGui.QStandardItemModel()        
        self.o_history.setModel(self.m_history)        
            
        ###        
        # eseguo la connessione 
        ###
        self.e_user_name = 'SMILE'
        self.e_password = 'SMILE'
        self.e_server_name = 'BACKUP_815'
        self.e_user_mode = 'Normal'        
        self.slot_connetti()   

        ###
        # Definizione della struttura per gestione elenco oggetti DB        
        ###
        self.oggetti_db_lista = QtGui.QStandardItemModel()        
        self.oggetti_db_elenco.setModel(self.oggetti_db_lista)
        # per default carico l'elenco di tutte le tabelle (selezionando la voce Tables=1 nell'elenco)
        self.oggetti_db_scelta.setCurrentIndex(1)

        ###
        # Imposto default in base alle preferenze (setto anche le opzioni sulle voci di menu)
        ###                
        self.actionUTF_8_Coding.setChecked(o_global_preferences.utf_8)
        self.slot_utf8()                
        self.actionMake_table_editable.setChecked(o_global_preferences.editable)
        self.slot_editable()
        self.actionShow_end_of_line.setChecked(o_global_preferences.end_of_line)
        self.slot_end_of_file()
        
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

    def oggetto_win2_attivo(self):
        """
            Restituisce l'oggetto di classe MSql_win2_class riferito alla window di editor attiva
        """        
        # Ricavo quale sia la window di editor attiva in questo momento
        v_window_attiva = self.mdiArea.activeSubWindow()            
        if v_window_attiva is not None:                                             
            # scorro la lista-oggetti-editor fino a quando non trovo l'oggetto che ha lo stesso titolo della window attiva
            for i in range(0,len(self.o_lst_window2)):
                if self.o_lst_window2[i].v_titolo_window == v_window_attiva.windowTitle() and not self.o_lst_window2[i].v_editor_chiuso:
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
        
        # Apertura di un nuovo editor o di un file recente
        if p_slot.text() in ('New','Open','Open_db_obj') or str(p_slot.data()) == 'FILE_RECENTI':
            # se richiesto un file recente
            if str(p_slot.data()) == 'FILE_RECENTI':
                # apro il file richiesto
                v_titolo, v_contenuto_file = self.openfile(p_slot.text())
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
            sub_window = self.mdiArea.addSubWindow(o_MSql_win2)                  
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
        # visualizza dock dell'history
        elif p_slot.text() == 'History':
            self.dockWidget_3.show()
                
        # Queste voci di menu che agiscono sull'oggetto editor, sono valide solo se l'oggetto è attivo
        if o_MSql_win2 is not None:
            # Salvataggio del file
            if p_slot.text() == 'Save':
                v_ok, v_nome_file = salvataggio_editor(False, o_MSql_win2.v_titolo_window, o_MSql_win2.e_sql.text())
                if v_ok == 'ok':
                    o_MSql_win2.v_testo_modificato = False
                    o_MSql_win2.v_titolo_window = v_nome_file
                    o_MSql_win2.setWindowTitle(v_nome_file)
            # Salvataggio del file come... (semplicemente non gli passo il titolo)
            elif p_slot.text() == 'Save as':
                v_ok, v_nome_file = salvataggio_editor(True, o_MSql_win2.v_titolo_window, o_MSql_win2.e_sql.text())
                if v_ok == 'ok':
                    o_MSql_win2.v_testo_modificato = False
                    o_MSql_win2.v_titolo_window = v_nome_file
                    o_MSql_win2.setWindowTitle(v_nome_file)
            # Cambio server in ICOM_815
            elif p_slot.text() == 'Server Prod (ICOM_815)':
                self.e_server_name = 'ICOM_815'
                self.slot_connetti()                        
            # Cambio server in BACKUP_815
            elif p_slot.text() == 'Server Dev (BACKUP_815)':
                self.e_server_name = 'BACKUP_815'
                self.slot_connetti()
            # Cambio user in SMILE
            elif p_slot.text() == 'USER_SMILE':  
                self.e_user_name, self.e_password, self.e_user_mode = 'SMILE','SMILE','Normal'
                self.slot_connetti()
            # Cambio user in SMI
            elif p_slot.text() == 'USER_SMI':
                self.e_user_name, self.e_password, self.e_user_mode = 'SMI','SMI','Normal'                
                self.slot_connetti()
            # Cambio user in SMIPACK
            elif p_slot.text() == 'USER_SMIPACK':
                self.e_user_name, self.e_password, self.e_user_mode = 'SMIPACK','SMIPACK','Normal'                                
                self.slot_connetti()
            # Cambio user in SMITEC
            elif p_slot.text() == 'USER_SMITEC':                
                self.e_user_name, self.e_password, self.e_user_mode = 'SMITEC','SMITEC','Normal'                
                self.slot_connetti()
            # Cambio user in SMIMEC
            elif p_slot.text() == 'USER_SMIMEC':
                self.e_user_name, self.e_password, self.e_user_mode = 'SMIMEC','SMIMEC','Normal'                
                self.slot_connetti()
            # Cambio user in SMIWRAP
            elif p_slot.text() == 'USER_SMIWRAP (SmiEnergia)':
                self.e_user_name, self.e_password, self.e_user_mode = 'SMIWRAP','SMIWRAP','Normal'                
                self.slot_connetti()
            # Cambio user in ENOBERG
            elif p_slot.text() == 'USER_ENOBERG':
                self.e_user_name, self.e_password, self.e_user_mode = 'ENOBERG','ENOBERG','Normal'                
                self.slot_connetti()
            # Cambio user in SMIFORM
            elif p_slot.text() == 'USER_FORM (SmiLab)':
                self.e_user_name, self.e_password, self.e_user_mode = 'SMIBLOW','SMIBLOW','Normal'                
                self.slot_connetti()
            # Cambio user in SARCO
            elif p_slot.text() == 'USER_SARCO':
                self.e_user_name, self.e_password, self.e_user_mode = 'SARCO','SARCO','Normal'                
                self.slot_connetti()
            # Cambio user specificato da utente
            elif p_slot.text() == 'Connect to specific database':
                self.richiesta_connessione_specifica()
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
            # Selezione del testo rettangolare
            elif p_slot.text() == 'Rect selection':                
                message_info('Press the Alt key for the rectangular selection ;-)')                                
            # Uppercase del testo selezionato
            elif p_slot.text() == 'Uppercase':                
                o_MSql_win2.e_sql.SendScintilla(Qsci.QsciScintilla.SCI_UPPERCASE)
            # Lowercase del testo selezionato
            elif p_slot.text() == 'Lowercase':                
                o_MSql_win2.e_sql.SendScintilla(Qsci.QsciScintilla.SCI_LOWERCASE)
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
                o_MSql_win2.slot_esegui()
            # Commit
            elif p_slot.text() == 'Commit':
                o_MSql_win2.slot_commit_rollback('Commit')
            # Rollback
            elif p_slot.text() == 'Rollback':
                o_MSql_win2.slot_commit_rollback('Rollback')
            # Ricerca di un oggetto
            elif p_slot.text() == 'Find object':                
                message_info('Position yourself in the text-editor on the object and press F12')                                
            # Carico il risultato sql alla prima riga
            elif p_slot.text() == 'Go to Top':
                o_MSql_win2.slot_go_to_top()
            # Carico il risultato sql fino all'ultima riga
            elif p_slot.text() == 'Go to End':
                o_MSql_win2.slot_go_to_end()        
            # Esporto in formato Excel
            elif p_slot.text() == 'Export to Excel':
                o_MSql_win2.slot_export_to_excel()
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
            # Indico che l'output sql ha le colonne con larghezza auto-adattabile
            elif p_slot.text() == 'Auto Column Resize':
                o_MSql_win2.slot_menu_auto_column_resize()

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
        else:
            self.l_tabella_editabile.setText("Editable table: Disabled")            
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
            if os.path.isfile(v_global_work_dir + 'recent_files.ini'):
                with open(v_global_work_dir + 'recent_files.ini','r') as file:
                    for v_nome_file in file:                                        
                        v_nome_file = v_nome_file.rstrip('\n')
                        # il file viene aggiunto all'elenco solo se esiste!
                        if os.path.isfile(v_nome_file):                            
                            v_action = QAction(self)
                            v_action.setText(v_nome_file)
                            v_action.setData('FILE_RECENTI')
                            # aggiungo a video la voce di menu
                            self.menuRecent_file.addAction(v_action)
                            # allineo array interno con quanto presente a video
                            self.elenco_file_recenti.append(v_nome_file)
        # se elemento passato e non presente tra i files recenti...
        elif p_elemento not in self.elenco_file_recenti:
            # elimino tutte le voci dal menu dei recenti
            self.menuRecent_file.clear()
            # aggiungo nuova voce all'array interno
            self.elenco_file_recenti.append(p_elemento)
            # apro il file che contiene i recenti per salvare i dati (salverò solo gli ultimi 10 files)
            v_file_recenti = open(v_global_work_dir + 'recent_files.ini','w')
            v_num_file = 0
            # scorro array al contrario (così tengo il più recente in cima alla lista) e ricarico il menu a video            
            for v_index in range(len(self.elenco_file_recenti),0,-1):
                v_voce_menu = self.elenco_file_recenti[v_index-1]
                v_action = QAction(self)
                v_action.setText(v_voce_menu)
                v_action.setData('FILE_RECENTI')
                self.menuRecent_file.addAction(v_action)
                if v_num_file <= 10:
                    v_file_recenti.write(v_voce_menu+'\n')            
                    v_num_file += 1
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
                if not obj_win2.v_editor_chiuso and  obj_win2.v_titolo_window == v_fileName[0]:
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
            self.close()
        # altrimenti ignoro l'evento di chiusura
        else:
            event.ignore()

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
            v_cursore.execute(v_select)
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

        # aggiorno le voce di menu (schema)        
        self.actionICOM_815.setChecked(False)
        self.actionBACKUP_815.setChecked(False)

        if self.e_server_name == 'ICOM_815':            
            self.actionICOM_815.setChecked(True)            
        if self.e_server_name == 'BACKUP_815':                        
            self.actionBACKUP_815.setChecked(True)
        
        # aggiorno le voce di menu (user)        
        self.actionUSER_SMILE.setChecked(False)
        self.actionUSER_SMI.setChecked(False)
        self.actionUSER_SMIPACK.setChecked(False)
        self.actionUSER_TEC.setChecked(False)
        self.actionUSER_SMIMEC.setChecked(False)
        self.actionUSER_SMIWRAP.setChecked(False)
        self.actionUSER_ENOBERG.setChecked(False)
        self.actionUSER_SMIFORM.setChecked(False)
        self.actionUSER_SARCO.setChecked(False)        
        
        if self.e_user_name == 'SMILE':            
            self.actionUSER_SMILE.setChecked(True)        
        if self.e_user_name == 'SMI':                        
            self.actionUSER_SMI.setChecked(True)            
        if self.e_user_name == 'SMIPACK':      
            self.actionUSER_SMIPACK.setChecked(True)
        if self.e_user_name == 'SMITEC':           
            self.actionUSER_TEC.setChecked(True)
        if self.e_user_name == 'SMIMEC':       
            self.actionUSER_SMIMEC.setChecked(True)
        if self.e_user_name == 'SMIWRAP':         
            self.actionUSER_SMIWRAP.setChecked(True)
        if self.e_user_name == 'ENOBERG':          
            self.actionUSER_ENOBERG.setChecked(True)
        if self.e_user_name == 'SMIBLOW':          
            self.actionUSER_SMIFORM.setChecked(True)
        if self.e_user_name == 'SARCO':            
            self.actionUSER_SARCO.setChecked(True)        

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

        # In base al tipo di connessione cambio il colore di sfondo dell'editor (azzurro=sistema reale, bianco=sistema di test)        
        if self.e_server_name == 'ICOM_815':            
            v_color = o_global_preferences.color_prod            
            v_background = 'black'
        else:
            v_color = o_global_preferences.color_dev
            v_background = 'gray'
        if self.e_user_mode == 'SYSDBA':
            v_background = 'red'

        # sulla statusbar, aggiorno la label della connessione        
        self.l_connection.setText("Connection: " + self.e_server_name + "/" + self.e_user_name)                            
        self.l_connection.setStyleSheet('background-color: ' + v_background + ';color: "' + v_color + '";')              

        # se la connessione è andata a buon fine, richiedo elenco degli oggetti in modo da aggiornare il dizionario dell'editor con nuove parole chiave
        # in questa sezione viene caricata la lista v_global_my_lexer_keywords con tutti i nomi di tabelle, viste, procedure, ecc.
        # tale lista viene poi aggiornata quando viene aperto un nuovo editor o quando viene cambiata la connessione
        if v_global_connesso:
            v_global_my_lexer_keywords.clear()
            v_cursor = v_global_connection.cursor()
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
                obj_win2.o_table.setStyleSheet("QTableWidget {background-color: " + v_color + ";}")
                obj_win2.o_output.setStyleSheet("QPlainTextEdit {background-color: " + v_color + ";}")
                self.oggetti_db_elenco.setStyleSheet("QListView {background-color: " + v_color + ";}")
                self.db_oggetto_tree.setStyleSheet("QTreeView {background-color: " + v_color + ";}")
                self.o_history.setStyleSheet("QListView {background-color: " + v_color + ";}")
                # aggiorno il lexer aggiungendo tutte le nuove keywords
                if len(v_global_my_lexer_keywords) > 0:                                        
                    obj_win2.v_lexer = My_MSql_Lexer(obj_win2.e_sql)
                    # imposto carattere di default
                    obj_win2.v_lexer.setDefaultFont(QFont("Cascadia Code SemiBold",11))    
                    obj_win2.v_lexer.setFoldCompact(False)
                    obj_win2.v_lexer.setFoldComments(True)
                    obj_win2.v_lexer.setFoldAtElse(True)                
                    # attivo il lexer sull'editor
                    obj_win2.e_sql.setLexer(obj_win2.v_lexer)

    def slot_oggetti_db_scelta(self):
        """
           In base alla voce scelta, viene caricata la lista con elenco degli oggetti pertinenti
        """                        
        global v_global_connesso

        # prendo il tipo di oggetto scelto dall'utente
        try:            
            self.tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            self.tipo_oggetto = ''
        # pulisco elenco
        self.oggetti_db_lista.clear()
        # se utente ha scelto un oggetto e si è connessi, procedo con il carico dell'elenco 
        if self.tipo_oggetto != '' and v_global_connesso:
            # leggo elenco degli oggetti indicati
            v_select = """SELECT *
                          FROM (SELECT OBJECT_NAME,
                                       (SELECT COUNT(*) 
	                                    FROM   DBA_OBJECTS 
		                                WHERE  DBA_OBJECTS.OWNER=ALL_OBJECTS.OWNER AND 
		                                        DBA_OBJECTS.OBJECT_NAME=ALL_OBJECTS.OBJECT_NAME AND 
			                                    DBA_OBJECTS.STATUS != 'VALID') INVALID 
                                FROM   ALL_OBJECTS 
                                WHERE  OWNER='""" + self.e_user_name + """' AND 
                                       OBJECT_TYPE='""" + self.tipo_oggetto + """'
                               )"""
            # se necessario applico il filtro di ricerca
            if self.oggetti_db_ricerca.text() != '' or self.oggetti_db_tipo_ricerca.currentText() == 'Only invalid':
                if self.oggetti_db_tipo_ricerca.currentText() == 'Start with':
                    v_select += " WHERE OBJECT_NAME LIKE '" + self.oggetti_db_ricerca.text().upper() + "%'"
                elif self.oggetti_db_tipo_ricerca.currentText() == 'Like':
                    v_select += " WHERE OBJECT_NAME LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%'"
                elif self.oggetti_db_tipo_ricerca.currentText() == 'Only invalid': 
                    v_select += " WHERE OBJECT_NAME LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%' AND INVALID > 0"
            # aggiungo order by
            v_select += " ORDER BY OBJECT_NAME"            
            # eseguo la select
            self.v_cursor_db_obj.execute(v_select)            
            v_righe = self.v_cursor_db_obj.fetchall()            
            # carico elenco nel modello che è collegato alla lista
            for v_riga in v_righe:
                v_item = QtGui.QStandardItem()
                v_item.setText(v_riga[0]) 
                if v_riga[1] != 0: 
                    v_item.setBackground(QColor(Qt.red))
                self.oggetti_db_lista.appendRow(v_item)                        

    def slot_oggetti_db_doppio_click(self, p_index):
        """
           Carica la definizione dell'oggetto su cui si è fatto doppio click (es. il sorgente di un package o di una tabella...)           
        """                
        # prendo il tipo di oggetto scelto dall'utente
        try:            
            self.tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            self.tipo_oggetto = ''
        # prendo il nome dell'oggetto scelto dall'utente
        v_selindex = self.oggetti_db_lista.itemFromIndex(p_index)
        self.nome_oggetto = v_selindex.text()               
        if self.nome_oggetto != '':
            # imposto var che conterrà il testo dell'oggetto DB 
            v_testo_oggetto_db = ''
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

            # richiamo la procedura di oracle che mi restituisce la ddl dell'oggetto
            # se richiesto di aprire il package body, allora devo fare una chiamata specifica
            if self.tipo_oggetto == 'PACKAGE BODY':
                self.v_cursor_db_obj.execute("SELECT DBMS_METADATA.GET_DDL('PACKAGE_BODY','"+self.nome_oggetto+"') FROM DUAL")
            else:
                self.v_cursor_db_obj.execute("SELECT DBMS_METADATA.GET_DDL('"+self.tipo_oggetto+"','"+self.nome_oggetto+"') FROM DUAL")
            # prendo il primo campo, del primo record e lo trasformo in stringa
            v_testo_oggetto_db = str(self.v_cursor_db_obj.fetchone()[0])
            # sostituisco eol (end of line) da LF a CR-LF
            v_testo_oggetto_db = v_testo_oggetto_db.replace('\n','\r\n')

            # apro una nuova finestra di editor simulando il segnale che scatta quando utente sceglie "Open", passando il sorgente ddl
            v_azione = QtWidgets.QAction()
            v_azione.setText('Open_db_obj')
            self.smistamento_voci_menu(v_azione, self.nome_oggetto + '.msql', v_testo_oggetto_db)        
                                        
            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()    

    def slot_oggetti_db_click(self, p_index):
        """
           Carica nella sezione "object viewer" i dati dell'oggetto selezionato
        """
        # prendo il tipo di oggetto scelto dall'utente
        try:            
            v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            v_tipo_oggetto = ''
        # prendo il nome dell'oggetto scelto dall'utente
        v_selindex = self.oggetti_db_lista.itemFromIndex(p_index)
        v_nome_oggetto = v_selindex.text()               
        if v_nome_oggetto != '':
            self.carica_object_viewer(v_tipo_oggetto, v_nome_oggetto)

    def carica_object_viewer(self, p_tipo_oggetto, p_nome_oggetto):
        """
           Funzione che si occupa di caricare i dati dell'object viewer
        """        
        self.tipo_oggetto = p_tipo_oggetto
        self.nome_oggetto = p_nome_oggetto        
        # sostituisce la freccia del mouse con icona "clessidra"
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

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
            self.v_cursor_db_obj.execute("SELECT COMMENTS FROM all_tab_comments WHERE owner='"+self.owner_oggetto+"' AND TABLE_NAME='"+self.nome_oggetto+"'")
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
                                                   Decode(A.NULLABLE,'Y',' not null','') AS COLONNA_NULLA,
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
                v_campo_col3 = QStandardItem(result[3])
                v_root_campi.appendRow([v_campo_col0,v_campo_col1,v_campo_col2,v_campo_col3])                
            self.db_oggetto_tree_model.appendRow(v_root_campi)

            ###
            # seconda radice con le fk
            ###
            v_root_fk = QStandardItem('Constraints')

            self.v_cursor_db_obj.execute("""SELECT CONSTRAINT_NAME,
                                                   (SELECT LISTAGG(COLUMN_NAME,',') WITHIN GROUP (ORDER BY POSITION) FROM ALL_CONS_COLUMNS WHERE OWNER=ALL_CONSTRAINTS.OWNER AND CONSTRAINT_NAME=ALL_CONSTRAINTS.CONSTRAINT_NAME) COLONNE 
                                            FROM   ALL_CONSTRAINTS 
                                            WHERE  OWNER='"""+self.owner_oggetto+"""' AND 
                                                   TABLE_NAME='"""+self.nome_oggetto+"""'""")

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

        # se l'oggetto selezionato è una tabella o una vista --> preparo select per estrarre i nomi dei campi
        elif self.tipo_oggetto in ('PACKAGE','PACKAGE BODY','FUNCTION','PROCEDURE') :
            # ricerco il proprietario dell'oggetto
            self.v_cursor_db_obj.execute("SELECT OWNER FROM ALL_OBJECTS WHERE OBJECT_NAME='"+self.nome_oggetto+"' AND OBJECT_TYPE='"+self.tipo_oggetto+"'")            
            v_record = self.v_cursor_db_obj.fetchone()
            if v_record is not None:
                self.owner_oggetto = v_record[0]
            else:
                self.owner_oggetto = ''

            # creo un modello dati con 1 colonnA (dove nell'intestazione ci metto il nome dell'oggetto)
            self.db_oggetto_tree_model = QStandardItemModel()
            self.db_oggetto_tree_model.setHorizontalHeaderLabels([self.nome_oggetto])

            ###
            # prima radice con il nome dell'oggetto
            ###
            v_root_codice = QStandardItem('Code')

            self.v_cursor_db_obj.execute("""SELECT UPPER(TEXT) FROM ALL_SOURCE WHERE OWNER='"""+self.owner_oggetto+"""' AND NAME='"""+self.nome_oggetto+"""' AND TYPE='"""+self.tipo_oggetto+"""' ORDER BY LINE""")
    
            # analizzo il sorgente e ne estraggo il nome di funzioni e procedure
            v_start_sezione = False
            v_text_sezione = ''
            for result in self.v_cursor_db_obj:                       
                # dalla riga elimino gli spazi a sinistra e a destra
                v_riga_raw = result[0]
                v_riga = v_riga_raw.lstrip()
                v_riga = v_riga.rstrip()                    
                # individio riga di procedura-funzione
                if v_riga[0:9] == 'PROCEDURE' or v_riga[0:8] == 'FUNCTION':
                    # il nome della procedura-funzione inizia dal primo carattere spazio fino ad apertura parentesi tonda                        
                    if v_riga.find('(') != -1:
                        v_nome = v_riga[v_riga.find(' ')+1:v_riga.find('(')]
                    else:
                        v_nome = v_riga[v_riga.find(' ')+1:len(v_riga)]
                    # creo il nodo con il nome della procedura-funzione
                    v_int_proc_func = QStandardItem(v_nome)                        
                    v_root_codice.appendRow([v_int_proc_func])         
                    # indico che sono all'interno di una nuova sezione, terminata la quale poi dovrò esplodere elenco parametri                       
                    v_start_sezione = True
                    v_text_sezione = v_riga
                # ...continua la sezione di parametri....
                elif v_start_sezione:
                    v_text_sezione += v_riga

                # elaboro la sezione che contiene i parametri della procedura-funzione
                if v_start_sezione and v_riga.find(')') != -1:                        
                    v_text_sezione = v_text_sezione[v_text_sezione.find('(')+1:v_text_sezione.find(')')]                        
                    v_elenco_parametri = v_text_sezione.split(',')
                    for v_txt_parametro in v_elenco_parametri:                            
                        v_stringa = v_txt_parametro.lstrip()
                        v_parametro = v_stringa[0:v_stringa.find(' ')]
                        v_item_parametro = QStandardItem(v_parametro)                        
                        v_int_proc_func.appendRow(v_item_parametro)                        
                    v_text_sezione = ''
                    v_start_sezione = False
            
            self.db_oggetto_tree_model.appendRow(v_root_codice)
            
            ###                
            # attribuisco il modello dei dati all'albero
            ###
            self.db_oggetto_tree.setModel(self.db_oggetto_tree_model)                
            # mi posiziono sulla prima riga ed espando l'albero
            v_index = self.db_oggetto_tree_model.indexFromItem(v_root_codice)
            self.db_oggetto_tree.expand(v_index)
                                    
        # Ripristino icona freccia del mouse
        QApplication.restoreOverrideCursor()          

    def slot_db_oggetto_tree_expand(self, p_model):
        """
            Evento che si scatena quando viene selezionato un elemento sull'albero dell'object viever
            E' stato creato in quanto la ricerca della reference by è un po' lenta...
            p_model è del tipo QModelIndex
        """
        if p_model.data() == 'Referenced By':
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

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
            QApplication.restoreOverrideCursor()          

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
           Partendo dai sorgenti presenti nel DB, riferiti a package, funzioni e procedure, crea il file MSql_autocompletion.ini
           dove vengono riportati tutti i termini che poi verranno caricati all'avvio dell'editor per l'autocompletamento durante
           la digitazione delle parole
        """
        global v_global_connesso
        global v_global_work_dir
        
        if v_global_connesso and message_question_yes_no('Do you want create autocompletion dictionary?') == 'Yes':
            # creo una barra di avanzamento infinita
            v_progress = avanzamento_infinito_class("sql_editor.gif")            
            v_counter = 0
            # apro il file di testo che conterrà il risultato con tutti i nomi delle funzioni, procedure e package, ecc
            v_file = open(v_global_work_dir + 'MSql_autocompletion.ini','w')
            # la funzione put_line viene inserita di default 
            v_file.write('dbms_output.put_line(text)' +'\n')
            # elenco di tutti gli oggetti funzioni, procedure e package
            self.v_cursor_db_obj.execute("SELECT OBJECT_NAME, OBJECT_TYPE FROM ALL_OBJECTS WHERE OWNER='" + self.e_user_name + "' AND OBJECT_TYPE IN ('PACKAGE','PROCEDURE','FUNCTION') ORDER BY OBJECT_NAME")
            v_elenco_oggetti = self.v_cursor_db_obj.fetchall()
            # leggo il sorgente di ogni oggetto di cui sopra...
            for v_record in v_elenco_oggetti:                                
                # visualizzo barra di avanzamento e se richiesto interrompo
                v_counter += 1
                v_progress.avanza('Analizing ' + v_record[0] ,v_counter)
                if v_progress.richiesta_cancellazione:                        
                    break
                # leggo il sorgente
                self.v_cursor_db_obj.execute("""SELECT UPPER(TEXT) FROM ALL_SOURCE WHERE OWNER='"""+self.e_user_name+"""' AND NAME='"""+v_record[0]+"""' AND TYPE='"""+v_record[1]+"""' ORDER BY LINE""")                
                v_start_sezione = False
                v_text_sezione = ''
                v_risultato = ''
                # processo tutte le righe del sorgente
                for result in self.v_cursor_db_obj:                       
                    # dalla riga elimino gli spazi a sinistra e a destra
                    v_riga_raw = result[0]
                    v_riga = v_riga_raw.lstrip()
                    v_riga = v_riga.rstrip()                                        
                    v_riga = v_riga.replace('"','')
                    # individio riga di procedura-funzione
                    if v_riga[0:9] == 'PROCEDURE' or v_riga[0:8] == 'FUNCTION':
                        # il nome della procedura-funzione inizia dal primo carattere spazio fino ad apertura parentesi tonda                        
                        if v_riga.find('(') != -1:
                            v_nome = v_riga[v_riga.find(' ')+1:v_riga.find('(')]
                        else:
                            v_nome = v_riga[v_riga.find(' ')+1:len(v_riga)]
                        v_risultato = v_nome + '('    
                        # indico che sono all'interno di una nuova sezione, terminata la quale poi dovrò esplodere elenco parametri                       
                        v_start_sezione = True
                        v_text_sezione = v_riga
                    # ...continua la sezione di parametri....
                    elif v_start_sezione:
                        v_text_sezione += v_riga

                    # elaboro la sezione che contiene i parametri della procedura-funzione
                    if v_start_sezione and v_riga.find(')') != -1:                        
                        v_text_sezione = v_text_sezione[v_text_sezione.find('(')+1:v_text_sezione.find(')')]                        
                        v_elenco_parametri = v_text_sezione.split(',')                        
                        v_indice = 0                        
                        for v_txt_parametro in v_elenco_parametri:                                                        
                            v_stringa = v_txt_parametro.lstrip()
                            v_parametro = v_stringa[0:v_stringa.find(' ')]
                            # aggiungo la virgola tra un parametro e l'altro
                            v_indice += 1
                            if v_indice != len(v_elenco_parametri):
                                v_risultato += v_parametro + ','
                            else:
                                v_risultato += v_parametro
                            
                        v_text_sezione = ''
                        v_start_sezione = False
                        v_risultato += ')'
                        if v_record[1] == 'PACKAGE':
                            v_risultato = v_record[0] + '.' + v_risultato
                        v_file.write(v_risultato.lstrip() +'\n')
                    
            v_file.close()
            message_info('The autocompletion dictionary has been created! Restart MSql to see the changes ;-)')
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

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win2_class, self).__init__()        
        self.setupUi(self)
                
        # imposto il titolo della nuova window
        self.v_titolo_window = p_titolo
        self.setWindowTitle(self.v_titolo_window)

        # var che indica che è attiva-disattiva la sovrascrittura (tasto insert della tastiera)
        self.v_overwrite_enabled = False
        # mi salvo il puntatore alla classe principale (in questo modo posso accedere ai suoi oggetti e metodi)
        self.link_to_MSql_win1_class = o_MSql_win1_class

        # splitter che separa l'editor dall'output: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello di output
        #self.splitter.setStyleSheet("QSplitter::handle {text: url(':/icons/icons/splitter.gif')}")
        self.splitter.setStretchFactor(0,1)

        ###
        # IMPOSTAZIONI DELL'EDITOR SCINTILLA
        ###
        # attivo UTF-8 (se richiesto)
        if o_global_preferences.utf_8:
            self.e_sql.setUtf8(True)                                                        
        # evidenzia l'intera riga dove posizionato il cursore
        self.e_sql.setCaretLineVisible(True)
        self.e_sql.setCaretLineBackgroundColor(QColor("#FFFF99"))
        # attivo il margine 0 con la numerazione delle righe
        self.e_sql.setMarginType(0, Qsci.QsciScintilla.NumberMargin)        
        self.e_sql.setMarginsFont(QFont("Courier New",9))           
        # attivo il lexer per evidenziare il codice del linguaggio SQL. Notare come faccia riferimento ad un oggetto che a sua volta personalizza il 
        # dizionario del lexer SQL, aggiungendo (se sono state caricate) le parole chiave di: tabelle, viste, package, ecc.
        self.v_lexer = My_MSql_Lexer(self.e_sql)                
        # imposto carattere di default
        self.v_lexer.setDefaultFont(QFont("Cascadia Code SemiBold",11))    
        self.v_lexer.setFoldCompact(False)
        self.v_lexer.setFoldComments(True)
        self.v_lexer.setFoldAtElse(True)                                
        # attivo le righe verticali che segnano le indentazioni
        self.e_sql.setIndentationGuides(True)                
        # attivo i margini con + e - 
        self.e_sql.setFolding(self.e_sql.BoxedTreeFoldStyle, 2)
        # indentazione
        self.e_sql.setIndentationWidth(4)
        self.e_sql.setAutoIndent(True)
        # tabulatore a 4 caratteri
        self.e_sql.setTabWidth(4)   
                        
        # attivo autocompletamento durante la digitazione 
        # (comprende sia le parole del documento corrente che quelle aggiunte da un elenco specifico)
        # attenzione! Da quanto ho capito, il fatto di avere attivo il lexer con linguaggio specifico (sql) questo prevale
        # sul funzionamento di alcuni aspetti dell'autocompletamento....quindi ad un certo punto mi sono arreso con quello che
        # sono riuscito a fare
        self.v_api_lexer = Qsci.QsciAPIs(self.v_lexer)            
        # aggiungo tutti i termini di autocompletamento (si trovanon all'interno di una tabella che viene generata a comando)
        self.e_sql.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)                
        self.carica_dizionario_per_autocompletamento()                
        # indico dopo quanti caratteri che sono stati digitati dall'utente, si deve attivare l'autocompletamento
        self.e_sql.setAutoCompletionThreshold(2)  
        # attivo autocompletamento sia per la parte del contenuto del documento che per la parte di parole chiave specifiche
        self.e_sql.autoCompleteFromAll()

        # attivo il lexer sull'editor
        self.e_sql.setLexer(self.v_lexer)
        
        # imposto il ritorno a capo in formato Windows (CR-LF)
        # Attenzione! Questa impostazione non converte eventuale testo che viene caricato da file con eol diverso
        #             da quello considerato di default (Windows). Quindi, quando viene caricato un file, viene 
        #             fatta la conversione dei eol LF con CR-LF (vedi caricamento file)
        self.e_sql.setEolMode(Qsci.QsciScintilla.EolWindows)        

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
        # inzializzo la var che conterrà eventuale matrice dei dati modificati
        self.v_matrice_dati_modificati = []
        # var che indica se attivare l'auto column resize (incide sulle prestazioni del caricamento)
        self.v_auto_column_resize = False         
        # salva l'altezza del font usato nella sezione result e output e viene usata per modificare l'altezza della cella
        self.v_altezza_font_output = 9
        # settaggio dei font di editor e di risultato e output (il font è una stringa con il nome del font e separato da virgola l'altezza)
        if o_global_preferences.font_editor != '':
            v_split = o_global_preferences.font_editor.split(',')            
            v_font = QFont(str(v_split[0]),int(v_split[1]))
            self.slot_font_editor_selector(v_font)
        if o_global_preferences.font_result != '':
            v_split = o_global_preferences.font_result.split(',')
            v_font = QFont(str(v_split[0]),int(v_split[1]))
            self.slot_font_result_selector(v_font)

        ###
        # Precaricamento (se passato un contenuto di file) 
        ###
        if p_contenuto_file is not None:        
            # imposto editor con quello ricevuto in ingresso
            self.e_sql.setText(p_contenuto_file)
            # mi posiziono sulla prima riga
            self.e_sql.setCursorPosition(0,0)

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
        self.e_sql.cursorPositionChanged.connect(self.slot_e_sql_spostamento_cursore)            
            
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
            # tasto F12 premuto dall'utente --> richiamo l'object viewer            
            if event.key() == Qt.Key_F12:                 
                self.slot_f12()   
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
        
    def carica_dizionario_per_autocompletamento(self):
        """
           Partendo dal file che contiene elenco termini di autocompletamento, ne leggo il contenuto e lo aggiungo all'editor
           Da notare come viene caricato di fatto un elenco sia con caratteri minuscoli che maiuscoli perché non sono riuscito
           a far funzionare la sua preferenza 
        """
        global v_global_my_lexer_keywords
                
        # come termini di autocompletamento prendo tutti gli oggetti che ho nella lista usata a sua volta per evidenziare le parole
        for v_keywords in v_global_my_lexer_keywords:
            self.v_api_lexer.add(v_keywords.upper())                                    
            self.v_api_lexer.add(v_keywords.lower())                                    

        # Se esiste il file delle preferenze...le carico nell'oggetto
        if os.path.isfile(v_global_work_dir + 'MSql_autocompletion.ini'):
            # carico i dati presenti nel file di testo (questo è stato creato con la voce di menu dello stesso MSql che si chiama "Create autocomplete dictonary")
            with open(v_global_work_dir + 'MSql_autocompletion.ini','r') as file:
                for v_riga in file:                
                    self.v_api_lexer.add(v_riga.upper())                                    
                    self.v_api_lexer.add(v_riga.lower())                                    
        
        self.v_api_lexer.prepare()        
   
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
            icon1.addPixmap(QtGui.QPixmap(":/icons/icons/copy.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
            v_copia = QPushButton()
            v_copia.setText('Copy item')
            v_copia.setIcon(icon1)        
            v_copia.clicked.connect(self.o_table_copia_valore)
            v_action = QWidgetAction(self.o_table_cont_menu)
            v_action.setDefaultWidget(v_copia)        
            self.o_table_cont_menu.addAction(v_action)

            # bottone per aprire window dove viene visualizzato il contenuto della cella in modo amplificato
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap(":/icons/icons/zoom.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
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
        v_icon.addPixmap(QtGui.QPixmap(":/icons/icons/zoom.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
        self.win_dialog_zoom_item.setWindowIcon(v_icon)
        self.win_dialog_zoom_item_gl = QtWidgets.QGridLayout(self.win_dialog_zoom_item)
        self.win_dialog_zoom_lineEdit = QtWidgets.QPlainTextEdit(self.win_dialog_zoom_item)        
        self.win_dialog_zoom_item_gl.addWidget(self.win_dialog_zoom_lineEdit, 0, 0, 1, 1)
        self.win_dialog_zoom_lineEdit.setPlainText(self.v_o_table_current_item.text())
        self.win_dialog_zoom_item.show()

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
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/order_a_z.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
        v_sort_a_z = QPushButton()
        v_sort_a_z.setText('Sort asc')
        v_sort_a_z.setIcon(icon1)        
        v_sort_a_z.clicked.connect(self.slot_order_asc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_a_z)        
        self.o_table_popup.addAction(v_action)

        # bottone per ordinamento discendente
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/order_z_a.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        v_sort_z_a = QPushButton()
        v_sort_z_a.setText('Sort desc')
        v_sort_z_a.setIcon(icon2)
        v_sort_z_a.clicked.connect(self.slot_order_desc_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_sort_z_a)        
        self.o_table_popup.addAction(v_action)
        
        # bottone per raggruppamento su colonna
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/icons/group.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        v_group_by = QPushButton()
        v_group_by.setText('Group by')
        v_group_by.setIcon(icon3)
        v_group_by.clicked.connect(self.slot_group_by_popup)
        v_action = QWidgetAction(self.o_table_popup)
        v_action.setDefaultWidget(v_group_by)        
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
        v_new_select = 'SELECT DISTINCT ' + v_header_item.text() + ' FROM (' + self.v_select_corrente + ') ORDER BY ' + v_header_item.text()
                
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

    def slot_e_sql_spostamento_cursore(self):
        """
           Individia spostamenti del cursore nell'editor e aggiorna la label che riporta le coordinate sulla status bar
        """        
        v_y, v_x = self.e_sql.getCursorPosition()
        self.link_to_MSql_win1_class.l_cursor_pos.setText("Ln: " + str(v_y+1) + "  Col: " + str(v_x+1))
    
    def slot_menu_auto_column_resize(self):
        """
           Imposta la var che indica se la tabella del risultato ha attiva la formattazione automatica della larghezza delle colonne
        """
        if self.v_auto_column_resize:
            self.v_auto_column_resize = False
        else:
            self.v_auto_column_resize = True
                                                                       
    def slot_esegui(self):
        """
           Prende tutto il testo selezionato ed inizia ad eseguirlo step by step
           Se si attiva v_debug, variabile interna, verrà eseguito l'output di tutte le righe processate
        """
        # se metto a true v_debug usciranno tutti i messaggi di diagnostica della ricerca delle istruzioni
        v_debug = True
        def debug_interno(p_message):
            if v_debug:
                print(p_message)        

        # imposto la var di select corrente che serve in altre funzioni
        self.v_select_corrente = ''

        # prendo tutto il testo o solo quello evidenziato dall'utente
        if self.e_sql.selectedText():
            v_testo = self.e_sql.selectedText()            
        else:            
            v_testo = self.e_sql.text()
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
        v_plsql = False
        v_plsql_idx = 0
        for v_riga_raw in v_righe_testo:
            # dalla riga elimino gli spazi a sinistra e a destra
            v_riga = v_riga_raw.lstrip()
            v_riga = v_riga.rstrip()
            # riga vuota
            if v_riga == '':
                debug_interno('Riga vuota')
                pass            
            # continuazione riga plsql (da notare come lo script verrà composto con v_riga_raw)
            elif v_plsql:
                debug_interno('Continuo con script plsql ' + v_riga)
                # se trovo "aperture" aumento indice
                if v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE') != -1:
                    v_plsql_idx += 1
                # se trovo chiusure diminuisco indice
                elif v_riga.split()[0].upper() == 'END;' != -1:
                    v_plsql_idx -= 1
                # aggiungo riga
                v_plsql_str += chr(10) + v_riga_raw
                # la chiusura trovata era l'ultima --> quindi eseguo lo script
                if v_plsql_idx <= 0:                
                    self.esegui_script(v_plsql_str, False)
                    v_plsql = False
                    v_plsql_str = ''
                    v_plsql_idx = 0
            # se siamo all'interno di un commento multiplo, controllo se abbiamo raggiunto la fine
            elif v_commento_multi and v_riga.find('*/') == -1:
                pass
            elif v_commento_multi and v_riga.find('*/') != -1:        
                v_commento_multi = False
            # commento monoriga
            elif v_riga[0:2] == '--' or v_riga[0:6] == 'PROMPT':
                debug_interno('Commento! ' + v_riga)
            # commento multi ma monoriga
            elif v_riga[0:2] == '/*' and v_riga.find('*/') != -1:
                debug_interno('Commento multi monoriga ! ' + v_riga)
            # commento multi multiriga
            elif v_riga[0:2] == '/*':
                debug_interno('Commento multi multiriga ! ' + v_riga)
                v_commento_multi = True            
            # continuazione di una select, insert, update, delete....
            elif v_istruzione and v_riga.find(';') == -1:
                v_istruzione_str += chr(10) + v_riga
            # fine di una select, insert, update, delete.... con punto e virgola
            elif v_istruzione and v_riga[-1] == ';':
                v_istruzione = False
                v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]
                self.esegui_istruzione(v_istruzione_str)
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... monoriga
            elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE') and v_riga[-1] == ';':
                v_istruzione_str = v_riga[0:len(v_riga)-1]
                self.esegui_istruzione(v_istruzione_str)
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... multiriga
            elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE'):
                v_istruzione = True
                v_istruzione_str = v_riga
            # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)       
            elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
                debug_interno('Inizio plsql ')
                v_plsql = True
                v_plsql_idx += 1
                v_plsql_str = v_riga_raw
            else:
                message_error('Unknown command type: ' + v_riga_raw + '.....')
                return "ko"                

        # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
        if v_plsql and v_plsql_str != '':
            self.esegui_script(v_plsql_str, False)
        
        # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
        if v_istruzione and v_istruzione_str != '':
            self.esegui_istruzione(v_istruzione_str)  

    def esegui_istruzione(self, p_istruzione):
        """
           Esegue istruzione p_istruzione
        """
        if p_istruzione[0:6].upper() == 'SELECT':
            self.esegui_select(p_istruzione, True)
        elif p_istruzione[0:6].upper() in ('INSERT','UPDATE','DELETE'):
            self.esegui_script(p_istruzione, True)
        else:            
            message_error('No supported instruction!')                                 
            return "ko"
                
        # aggiungo l'istruzione all'history
        self.add_history(p_istruzione)            
        return None

    def esegui_script(self, p_plsql, p_rowcount):
        """
           Esegue script p_plsql. Se p_rowcount è true allora vengono conteggiate le righe processate (es. update)
        """
        if p_plsql != '':
            self.esegui_plsql(p_plsql, p_rowcount)
        else:
            message_error('No script!')

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
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))                    

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False

            # attivo output tramite dbms_output (1000000 è la dimensione del buffer)
            self.v_cursor.callproc("dbms_output.enable", [1000000])

            # eseguo lo script
            v_tot_record = 0
            try:                
                self.v_cursor.execute(p_plsql)
                v_tot_record = self.v_cursor.rowcount
                self.v_esecuzione_ok = True
            # se riscontrato errore di primo livello --> emetto sia codice che messaggio ed esco
            except cx_Oracle.Error as e:                                                                
                # ripristino icona freccia del mouse
                QApplication.restoreOverrideCursor()                        
                # emetto errore sulla barra di stato 
                errorObj, = e.args                                       
                self.scrive_output("Error: " + errorObj.message, "E")                 
                # per posizionarmi alla riga in errore ho solo la variabile offset che riporta il numero di carattere a cui l'errore si è verificato
                v_riga, v_colonna = x_y_from_offset_text(p_plsql, errorObj.offset)                
                self.e_sql.setCursorPosition(v_riga,v_colonna)
                return 'ko'

            # var che indica se siamo in uno script di "CREATE"
            v_create = False
            # controllo se eravamo di fronte ad uno script di "CREATE"...inizio con il cercare una parentesi tonda aperta
            v_pos = p_plsql.find('(')            
            # parentesi tonda aperta trovata!
            if v_pos != -1:
                # estraggo tutto il testo fino alla parentesi e lo nettifico, togliendo spazi e ritorni a capo
                v_testo = p_plsql[0:v_pos]
                v_testo = v_testo.upper().lstrip().replace('\n',' ')
                # prendo il testo fino alla parentesi tonda e ne estreggo le singole parole
                v_split = v_testo.split()
                # inizio a controllare se ci sono le parole che di solito so usano per creare oggetti di databse (procedure, view, ecc.)
                if v_split[0] == 'CREATE' and v_split[1] == 'OR' and v_split[2] == 'REPLACE':
                    v_tipo_script = v_split[3]
                    v_nome_script = v_split[4]
                    # trovato!
                    v_create = True 
                elif v_split[0] == 'CREATE' or v_split[0] == 'REPLACE':
                    v_tipo_script = v_split[1]
                    v_nome_script = v_split[2]
                    # trovato!
                    v_create = True

            # quindi...se lo script era di "CREATE"...controllo se in compilazione ci sono stati errori...
            if v_create:
                print('CREAZIONE DELLO SCRIPT --> ' + v_tipo_script + ' ' + v_nome_script)
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
                            self.e_sql.setCursorPosition(info[0]-1,info[1]-1)
                            v_1a_volta = False
                # tutto ok!
                else:
                    self.scrive_output('Created successfully','I')
            # altrimenti siamo di fronte ad uno script di pl-sql interno o di insert,update,delete che vanno gestiti con apposito output
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
                
                # se richiesto porto in output il numero di record elaborati (insert, update, delete...)
                if p_rowcount:
                    self.scrive_output(p_plsql.split()[0] + ' ' + str(v_tot_record) + ' row(s)', 'I')    
                else:
                    # porto l'output a video (tipico è quello di script che contengono dbms_output)
                    if v_dbms_ret != '':
                        self.scrive_output(v_dbms_ret, 'I')
                    else:
                        self.scrive_output('Script executed!', 'I')

            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()                            
                
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
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))                    

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
                self.v_cursor.execute(v_select)                            
                self.v_esecuzione_ok = True
            # se riscontrato errore --> emetto sia codice che messaggio
            except cx_Oracle.Error as e:                                                
                # ripristino icona freccia del mouse
                QApplication.restoreOverrideCursor()                        
                # emetto errore sulla barra di stato 
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

            # posizionamento sulla parte di output risultati select
            self.o_tab_widget.setCurrentIndex(0) 

            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()                        

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
            except:
                message_error('Error to fetch data!')
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
                    # campo numerico (se non funziona provare con i cx_Oracle type
                    elif isinstance(field, float) or isinstance(field, int):                           
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( '{:10.0f}'.format(field) ) )                    
                    # campo nullo
                    elif field == None:                                 
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( "" ) )                
                    # campo data
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.DATETIME:                                                                            
                        self.o_table.setItem(self.v_pos_y, x, QTableWidgetItem( str(field) ) )       
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
                        # da notare come prendeno qtext e trasformandolo in plaintext le prestazioni migliorino di molto                    
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
            if self.v_auto_column_resize:
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
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

            # carico prossima pagina
            self.carica_pagina()
                        
            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()    

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

    def slot_export_to_excel(self):
        """
           Prende i dati presenti in tabella e li esporta in excel....per prima cosa li carica tutti a video....
        """
        # Carico tutti i dati del cursore 
        self.slot_go_to_end()

        # Estraggo i dati dalla tableview (se errore la tabella è vuota e quindi esco)        
        v_model = self.o_table.model()
        if v_model == None:
            return None        

        # Richiedo il nome del file dove scrivere output
        v_xls_name = QtWidgets.QFileDialog.getSaveFileName(self, "Save a Excel file","export.xlsx","XLSX (*.xlsx)") [0]                  
        if v_xls_name == "":            
            message_error("Not a valid file name is selected")
            return None    
        
        # Creazione del file excel
        workbook = Workbook(v_xls_name)
        worksheet = workbook.add_worksheet()

        # Creazione della riga intestazioni
        v_y = 0
        v_x = 0
        for nome_colonna in self.nomi_intestazioni:            
            worksheet.write(v_y, v_x, nome_colonna)
            v_x += 1
                
        # Creazione di tutta la tabella        
        v_y += 1
        for row in range(v_model.rowCount()):
            v_x = 0
            for column in range(v_model.columnCount()):
                v_index = v_model.index(row, column)                
                v_campo = v_model.data(v_index)
                #if check_campo_numerico(v_campo):
                #    worksheet.write(v_y, v_x, campo_numerico(v_campo))
                #else:
                worksheet.write(v_y, v_x, v_campo)
                v_x += 1
            v_y += 1
                
        workbook.close()
        # Apro direttamente il file            
        try:
            os.startfile(v_xls_name)
        except:
            message_error('Error in file creation or file !')
      
    def closeEvent(self, e):
        """
           Intercetto l'evento di chiusura del form e controllo se devo chiedere di salvare o meno
           Questa funzione sovrascrive quella nativa di QT            
        """
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
        v_scelta = message_question_yes_no_cancel("The document " + self.v_titolo_window + " was modified." + chr(13) + "Do you want to save changes?")        
        # utente richiede di interrompere 
        if v_scelta == 'Cancel':
            return 'Cancel'
        # utente chiede di salvare
        elif v_scelta == 'Yes':            
            if self.v_titolo_window == "":                
                v_ok, v_nome_file = salvataggio_editor(True, self.v_titolo_window, self.e_sql.text())
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    self.v_testo_modificato = False
                    return 'Yes'
            else:                      
                v_ok, v_nome_file = salvataggio_editor(False, self.v_titolo_window, self.e_sql.text())                          
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

    def calcola_pos_win(self, p_QDialog):
        """
           Restituisce un oggetto QRect con la posizione e la dimensione della window ricevuta in input
           rispetto alla main window. Viene usata per le funzioni di trova e trova-sostituisci per posizionare
           la finestra a lato della main window.
           Il parametro p_QDialog è l'oggetto window che si vuole modificare
        """
        global v_global_main_geometry    
        
        v_dialog_dimension = p_QDialog.frameGeometry()                    
        o_rect = QRect()
        o_rect.setRect( v_global_main_geometry.x() + v_global_main_geometry.width() - v_dialog_dimension.width(), 
                        (v_global_main_geometry.y() + v_global_main_geometry.height() - v_dialog_dimension.height())//2, 
                        v_dialog_dimension.width(),
                        v_dialog_dimension.height())

        return o_rect                
    
    def slot_find(self):
        """
           Apre la window per la ricerca del testo (se già inizializzata la visualizzo e basta)           
        """            
        try:
            # visualizzo la finestra di ricerca
            self.dialog_find.show()
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog per la ricerca del testo
            self.dialog_find = QtWidgets.QDialog()            
            self.win_find = Ui_FindWindow()        
            self.win_find.setupUi(self.dialog_find)                                        
            # reimposto il titolo perché nel caso di più editor aperti non si capisce a chi faccia riferimento la window
            self.dialog_find.setWindowTitle('Find (' + self.v_titolo_window + ')')
            # da notare come il collegamento delle funzioni venga fatto in questo punto e non nella ui            
            self.win_find.b_next.clicked.connect(self.slot_find_next)                
            self.win_find.b_find_all.clicked.connect(self.slot_find_all)                
            self.win_find.o_find_all_result.doubleClicked.connect(self.slot_find_all_doppio_click)
            # visualizzo la finestra di ricerca
            self.dialog_find.show()
            # definizione della struttura per elenco dei risultati (valido solo per find all)       
            self.find_all_model = QtGui.QStandardItemModel()        
            self.win_find.o_find_all_result.setModel(self.find_all_model)

        # reimposto la posizione e le dimensioni della window 
        self.dialog_find.setGeometry(self.calcola_pos_win(self.dialog_find))                

    def slot_find_all(self):
        """
           Ricerca della stringa in tutto il testo
        """
        # pulisco elenco
        self.find_all_model.clear()

        # prelevo la stringa da ricercare
        v_string_to_search = self.win_find.e_find.currentText()
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
        
    def slot_find_all_doppio_click(self, p_index):
        """
           Partendo dalla selezione di find_all, si posiziona sulla specifica riga di testo dell'editor
        """
        # prelevo la stringa da ricercare
        v_string_to_search = self.win_find.e_find.currentText()
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
        v_string_to_search = self.win_find.e_find.currentText()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                       
            # lancio la ricerca dicendo di posizionarsi sulla prossima ricorrenza 
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, -1, -1, True, False, False)

    def slot_find_e_replace(self):
        """
           Ricerca e sostituisci
        """
        global v_global_main_geometry

        try:
            # visualizzo la finestra di ricerca
            self.dialog_find_e_replace.show()
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog per la ricerca del testo
            self.dialog_find_e_replace = QtWidgets.QDialog()
            self.win_find_e_replace = Ui_Find_e_Replace_Window()        
            self.win_find_e_replace.setupUi(self.dialog_find_e_replace)                
            # reimposto il titolo perché nel caso di più editor aperti non si capisce a chi faccia riferimento la window
            self.dialog_find_e_replace.setWindowTitle('Find and Replace (' + self.v_titolo_window + ')')
            # da notare come il collegamento delle funzioni venga fatto in questo punto e non nella ui                                    
            self.win_find_e_replace.b_find_next.clicked.connect(self.slot_find_e_replace_find)                
            self.win_find_e_replace.b_replace_next.clicked.connect(self.slot_find_e_replace_next)                
            self.win_find_e_replace.b_replace_all.clicked.connect(self.slot_find_e_replace_all)                            
            # visualizzo la finestra di ricerca
            self.dialog_find_e_replace.show()
        
        # reimposto la posizione e le dimensioni della window 
        self.dialog_find_e_replace.setGeometry(self.calcola_pos_win(self.dialog_find_e_replace))                

    def slot_find_e_replace_find(self):
        """
           Ricerca la prossima ricorrenza verso il basso
        """        
        v_string_to_search = self.win_find_e_replace.e_find.currentText()
        # se inserito una stringa di ricerca...
        if v_string_to_search != '':                       
            # lancio la ricerca dicendo di posizionarsi sulla prossima ricorrenza 
            v_found = self.e_sql.findFirst(v_string_to_search, False, False, False, False, True, -1, -1, True, False, False)
    
    def slot_find_e_replace_next(self):        
        """
           Sostituisce la ricorrenza attuale (ignora differenze tra maiuscole e minuscole)
        """
        # testo da ricercare
        v_string_to_search = self.win_find_e_replace.e_find.currentText().upper()
        # nuovo testo
        v_string_to_replace = self.win_find_e_replace.e_replace.currentText()

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
        v_string_to_search = self.win_find_e_replace.e_find.currentText().upper()
        # nuovo testo
        v_string_to_replace = self.win_find_e_replace.e_replace.currentText()

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

    def scrive_output(self, p_messaggio, p_tipo_messaggio):
        """
           Scrive p_messaggio nella sezione "output" precedendolo dall'ora di sistema
        """
        # definizione dei pennelli per scrivere il testo in diversi colori
        v_pennello_rosso = QtGui.QTextCharFormat()
        v_pennello_rosso.setForeground(Qt.red)
        v_pennello_blu = QtGui.QTextCharFormat()
        v_pennello_blu.setForeground(Qt.blue)
        v_pennello_nero = QtGui.QTextCharFormat()
        v_pennello_nero.setForeground(Qt.black)
        v_pennello_verde = QtGui.QTextCharFormat()
        v_pennello_verde.setForeground(Qt.darkGreen)

        # stampo in blu l'ora di sistema
        v_time = datetime.datetime.now()        
        self.o_output.setCurrentCharFormat(v_pennello_blu)        
        self.o_output.appendPlainText(str(v_time.hour).rjust(2,'0') + ':' + str(v_time.minute).rjust(2,'0') + ':' + str(v_time.second).rjust(2,'0'))         
        # in base al tipo di messaggio stampo messaaggio di colore nero o di colore rosso
        if p_tipo_messaggio == 'E':
            self.o_output.setCurrentCharFormat(v_pennello_rosso)        
            self.o_output.appendPlainText(p_messaggio)                 
        elif p_tipo_messaggio == 'S':
            self.o_output.setCurrentCharFormat(v_pennello_verde)        
            self.o_output.appendPlainText(p_messaggio)                 
        else:
            self.o_output.setCurrentCharFormat(v_pennello_nero)        
            self.o_output.appendPlainText(p_messaggio)                 
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

    def add_history(self, p_testo):
        """
           Aggiunge alla lista di history, il testo p_testo, solo se non già presente
        """
        v_found = False
        # scorro la lista e controllo se elemento già inserito
        for v_index in range( self.link_to_MSql_win1_class.m_history.rowCount() ):
            v_item = self.link_to_MSql_win1_class.m_history.item(v_index)
            if p_testo == v_item.text():
                v_found = True
        # se testo non trovato, aggiungo come nuovo elemento
        if not v_found:        
            self.link_to_MSql_win1_class.m_history.appendRow(QtGui.QStandardItem(p_testo))        

    def aggiorna_statusbar(self):
        """
           Aggiorna i dati della statusbar 
        """
        v_totale_righe = str(self.e_sql.lines())
        self.link_to_MSql_win1_class.l_numero_righe.setText("Lines: " + str(v_totale_righe))
        self.link_to_MSql_win1_class.l_numero_caratteri.setText("Length: " + str(self.e_sql.length()))

        # reimposta larghezza del margine numeri di riga...
        self.e_sql.setMarginWidth(0, '0' + v_totale_righe)        

        # label indicatore di overwrite
        if self.v_overwrite_enabled:
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText('Overwrite')
        else:                
            self.link_to_MSql_win1_class.l_overwrite_enabled.setText('Insert')

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

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":            
    # controllo se programma è stato richiamato da linea di comando passando il nome di un file    
    v_nome_file_da_caricare = ''
    try:
        if sys.argv[1] != '':                
            v_nome_file_da_caricare = sys.argv[1]    
    except:
        pass    

    # controllo se esiste dir di lavoro (servirà per salvare le preferenze...)        
    if not os.path.isdir(v_global_work_dir):
        os.makedirs(v_global_work_dir)
    
    # avvio del programma (aprendo eventuale file indicato su linea di comando)   
    app = QtWidgets.QApplication([])    
    application = MSql_win1_class(v_nome_file_da_caricare)     
    application.show()
    sys.exit(app.exec())    