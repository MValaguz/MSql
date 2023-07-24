# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 01/01/2023
 Descrizione...: Questo programma ha la "pretesa" di essere una sorta di piccolo editor SQL per ambiente Oracle....            
                 al momento si tratta più di un esperimento che di qualcosa di utilizzabile.
                 In questo programma sono state sperimentate diverse tecniche!
"""

# Librerie sistema
import sys
import os
import datetime
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
# Librerie di data base
import cx_Oracle
import oracle_my_lib
# Librerie grafiche QT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Libreria per export in excel
from xlsxwriter.workbook import Workbook
# Classi qtdesigner (win1 è la window principale, win2 la window dell'editor e win3 quella delle info di programma)
from MSql_editor_win1_ui import Ui_MSql_win1
from MSql_editor_win2_ui import Ui_MSql_win2
from MSql_editor_win3_ui import Ui_MSql_win3
# Classi qtdesigner per la ricerca e la sostituzione di stringhe di testo
from find_ui import Ui_FindWindow
from find_e_replace_ui import Ui_Find_e_Replace_Window
# Classe per visualizzare la barra di avanzamento 
from avanzamento import avanzamento_infinito_class
# Classe per evidenziare il codice 
import highlighting_words_in_text_editor
from utilita import *
from utilita_database import *

# Tipi oggetti di database
Tipi_Oggetti_DB = { 'Tables':'TABLE',                    
                    'Package':'PACKAGE',
                    'Trigger':'TRIGGER',
                    'Procedures':'PROCEDURE',
                    'Functions':'FUNCTION',
                    'Views':'VIEW' }

# Siccome la voce di menu utf-8 è globale, con una variabile globale deve essere gestita
v_global_utf_8 = False                    

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
        Classe di gestione MDI
    """       
    def __init__(self):
        # incapsulo la classe grafica da qtdesigner
        super(MSql_win1_class, self).__init__()        
        self.setupUi(self)
        # forzo la dimensione della finestra. Mi sono accorto che questa funzione, nella gestione MDI
        # è importante in quanto permette poi al connettore dello smistamento menu di funzionare sulla
        # prima finestra aperta....rimane comunque un mistero questa cosa.....
        self.showNormal()
        # var che indica il numero di window2-editor 
        self.v_num_window2 = 0                
        # definisco la lista che contiene il link a tutti gli oggetti window2 degli editor aperti
        self.o_lst_window2 = []
        # per smistare i segnali che arrivano dal menù che non è collegato con le subwindow, utilizzo
        # un apposito connettore
        self.menuBar.triggered[QAction].connect(self.smistamento_voci_menu)        
        # collego l'apposita funzione di aggiornamento dei menù quando viene attivata una window
        self.mdiArea.subWindowActivated.connect(self.click_win2)
        # apro una nuova finestra di editor simulando il segnale che scatta quando utente sceglie "New"
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
                if self.o_lst_window2[i].v_titolo_window == v_window_attiva.windowTitle():
                    return self.o_lst_window2[i]
        return None                    

    def click_win2(self):
        """
            Evento che scatta ogni volta che si seleziona una window di editor
            Serve controllare questo evento in quanto andranno riaggiornati i menu in base alla window attiva
        """
        # Carico l'oggetto di classe MSql_win2_class attivo in questo momento
        o_MSql_win2 = self.oggetto_win2_attivo()
        # Eseguo il refresh del menu principale
        self.aggiorna_menu(o_MSql_win2)

    def smistamento_voci_menu(self, p_slot):
        """
            Contrariamente al solito, le voci di menù non sono pilotate da qtdesigner ma direttamente
            dal connettore al menu che riporta a questa funzione che poi si occupa di fare lo smistamento.
            Ci sono voci di menù che sono "generiche", altre invece devono agire sul contenuto della finestra
            attiva. Per questo è stata creata una lista che contiene tutti gli oggetti aperti e quindi,
            di volta in volta viene ricercata la window-oggetto attiva ed elaborata la voce di menu direttamente
            per quella window-oggetto
        """
        global v_global_utf_8

        #print('Voce di menù --> ' + p_slot.text())    

        # Carico l'oggetto di classe MSql_win2_class attivo in questo momento         
        o_MSql_win2 = self.oggetto_win2_attivo()
        
        # Apertura di un nuovo editor
        if p_slot.text() in ('New','Open'):
            # se richiesto Open...
            if p_slot.text() == 'Open':
                # apro un file
                v_titolo, v_contenuto_file = self.openfile()
                # se non è stato scelto alcun file --> esco da tutto!
                if v_titolo is None:
                    return None
            # se richiesto New, aumento il numeratore delle window
            else:
                self.v_num_window2 += 1
                v_titolo = 'Untitled' + str(self.v_num_window2)
                v_contenuto_file = None
            # creo una nuovo oggetto editor (gli passo il titolo e eventuale contenuto del file)
            o_MSql_win2 = MSql_win2_class(v_titolo, v_contenuto_file)
            # l'oggetto editor lo salvo all'interno di una lista in modo sia reperibile quando necessario
            self.o_lst_window2.append(o_MSql_win2)        
            # collego l'oggetto editor ad una nuova finestra del gestore mdi e la visualizzo, massimizzandola
            sub_window = self.mdiArea.addSubWindow(o_MSql_win2)                                    
            sub_window.show()  
            sub_window.showMaximized()  

        # Codifica utf-8
        elif p_slot.text() == 'UTF-8 Coding':
            if self.actionUTF_8_Coding.isChecked():
                v_global_utf_8 = True
            else:
                v_global_utf_8 = False
            # aggiorno la label sulla statusbar
            o_MSql_win2.slot_utf8()

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
        # Visualizzo program info
        elif p_slot.text() == 'Program info':            
            self.program_info = MSql_win3_class()
            self.program_info.show()
                
        # Queste voci di menu che agiscono sull'oggetto editor, sono valide solo se l'oggetto è attivo
        if o_MSql_win2 is not None:
            # Salvataggio del file
            if p_slot.text() == 'Save':
                o_MSql_win2.slot_savefile()
            # Salvataggio del file come...
            elif p_slot.text() == 'Save as':
                o_MSql_win2.slot_savefile_as()
            # Cambio server in ICOM_815
            elif p_slot.text() == 'ICOM_815':
                o_MSql_win2.cambio_server_user('server','ICOM_815')                        
            # Cambio server in BACKUP_815
            elif p_slot.text() == 'BACKUP_815':
                o_MSql_win2.cambio_server_user('server','BACKUP_815')
            # Cambio server in BACKUP_2_815
            elif p_slot.text() == 'BACKUP_2_815':
                o_MSql_win2.cambio_server_user('server','BACKUP_2_815')        
            # Cambio user in SMILE
            elif p_slot.text() == 'USER_SMILE':                
                o_MSql_win2.cambio_server_user('user','SMILE')
            # Cambio user in SMI
            elif p_slot.text() == 'USER_SMI':
                o_MSql_win2.cambio_server_user('user','SMI')
            # Ricerca di testo
            elif p_slot.text() == 'Find':
                o_MSql_win2.slot_find()
            # Sostituzione di testo
            elif p_slot.text() == 'Find and Replace':
                o_MSql_win2.slot_find_e_replace()
            # Esecuzione dell'sql
            elif p_slot.text() == 'Execute':
                o_MSql_win2.slot_esegui()
            # Commit
            elif p_slot.text() == 'Commit':
                o_MSql_win2.slot_commit_rollback('Commit')
            # Rollback
            elif p_slot.text() == 'Rollback':
                o_MSql_win2.slot_commit_rollback('Rollback')
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
                o_MSql_win2.slot_font_editor_selector()
            # Selezione del font per l'output di sql
            elif p_slot.text() == 'Font output selector':
                o_MSql_win2.slot_font_output_selector()
            # Rendo l'output dell'sql editabile
            elif p_slot.text() == 'Make table editable':
                if o_MSql_win2.v_tabella_editabile:
                    o_MSql_win2.v_tabella_editabile = False
                else:
                    o_MSql_win2.v_tabella_editabile = True
                o_MSql_win2.slot_editabile()
            # Creo lo script per la modifica dei dati
            elif p_slot.text() == 'Script the changed data':
                o_MSql_win2.slot_save_modified_data()
            # Indico che l'output sql ha le colonne con larghezza auto-adattabile
            elif p_slot.text() == 'Auto Column Resize':
                o_MSql_win2.slot_menu_auto_column_resize()
        
            # Eseguo il refresh del menu principale
            self.aggiorna_menu(o_MSql_win2)

    def aggiorna_menu(self, p_o_MSql_win2):
        """
           In base all'editor attivo, adegua le check nel menu principale
        """   
        # Se l'oggetto passato è "vuoto" esco senza aggiornare i menu
        if p_o_MSql_win2 is None:
            return None
        # Voci di menu relative al server
        if p_o_MSql_win2.e_server_name == 'ICOM_815':
            self.actionICOM_815.setChecked(True)
            self.actionBACKUP_815.setChecked(False)
            self.actionBACKUP_2_815.setChecked(False)            
        if p_o_MSql_win2.e_server_name == 'BACKUP_815':
            self.actionICOM_815.setChecked(False)
            self.actionBACKUP_815.setChecked(True)
            self.actionBACKUP_2_815.setChecked(False)            
        if p_o_MSql_win2.e_server_name == 'BACKUP_2_815':
            self.actionICOM_815.setChecked(False)
            self.actionBACKUP_815.setChecked(False)
            self.actionBACKUP_2_815.setChecked(True)
        # Voci di menu relative all'utente
        if p_o_MSql_win2.e_user_name == 'SMILE':
            self.actionUSER_SMILE.setChecked(True)
            self.actionUSER_SMI.setChecked(False)                            
        if p_o_MSql_win2.e_user_name == 'SMI':
            self.actionUSER_SMILE.setChecked(False)
            self.actionUSER_SMI.setChecked(True)   
        # Voce di menu che indica se la tabella sql è editabile
        if p_o_MSql_win2.v_tabella_editabile:
            self.actionMake_table_editable.setChecked(True)
        else:
            self.actionMake_table_editable.setChecked(False)

    def openfile(self):
        """
           Apertura di un file...restituisce il nome del file e il suo contenuto
        """      
        global v_global_utf_8

        v_fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Documents/","SQL Files (*.sql *.pls *.plb);;All Files (*.*)")                
        if v_fileName[0] != "":
            # controllo se il file è già aperto in altra finestra di editor
            for obj_win2 in self.o_lst_window2:
                if not obj_win2.v_editor_chiuso and  obj_win2.v_titolo_window == v_fileName[0]:
                    message_error('This file is already open!')
                    return None,None
            # procedo con apertura
            try:
                # apertura usando utf-8                                         
                if v_global_utf_8:                    
                    v_file = open(v_fileName[0],'r',encoding='utf-8')
                # apertura usando ansi
                else:                    
                    v_file = open(v_fileName[0],'r')
                # restituisco il nome e il contenuto del file
                return v_fileName[0], v_file.read()
            except Exception as err:
                message_error('Error to opened the file: ' + str(err))
                return None, None
        else:
            return None, None
    
    def closeEvent(self, e):
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
        # se tutte le window sono chiuse esco dell'applicazione
        if v_chiudi_app:
            self.close()
                        
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
    def __init__(self, p_titolo, p_contenuto_file):
        global v_global_utf_8

        # incapsulo la classe grafica da qtdesigner
        super(MSql_win2_class, self).__init__()        
        self.setupUi(self)
                
        # imposto il titolo della nuova window
        self.v_titolo_window = p_titolo
        self.setWindowTitle(self.v_titolo_window)

        # splitter che separa l'editor dall'output: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello di output
        self.splitter.setStyleSheet("QSplitter::handle {image: url(':/icons/icons/splitter.gif')}")
        self.splitter.setStretchFactor(0,1)
        # splitter che separa l'editor da elenco oggetti: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello degli oggetti        
        self.splitter_obj.setStretchFactor(0,1)        
        
        ###
        # Aggiunta della classe che permette all'editor di evidenziare le parole chiavi di PLSQL
        ###
        self.highlight = highlighting_words_in_text_editor.PLSQL_Highlighter(self.e_sql.document())
                                
        ###
        # DICHIARAZIONE VAR GENERALI
        ###

        # imposto la parte relativa al server/user a cui collegarsi
        self.e_server_name = 'BACKUP_815'        
        self.e_user_name = 'SMILE'                        
        # attivo la var che indica se si è connessi
        self.v_connesso = False                               
        # eseguo la connessione 
        self.slot_connetti()   

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

        ###
        # Precaricamento (se passato un contenuto di file) 
        ###
        if p_contenuto_file is not None:        
            # imposto editor con quello ricevuto in ingresso
            self.e_sql.setPlainText(p_contenuto_file)

        # imposto blocco editabilità della tabella (verrà attivata solo su richiesta specifica dell'utente)
        self.v_tabella_editabile = False        
        # var che indica che il testo è stato modificato
        self.v_testo_modificato = False        

        ###
        # Aggiunta di windget alla statusbar con: flag editabilità, numero di caratteri, indicatore di overwrite
        ###                                
        self.l_tabella_editabile = QLabel("Editable table: Disabled")
        self.l_tabella_editabile.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.l_tabella_editabile.setStyleSheet('color: black;')
        self.statusBar.addPermanentWidget(self.l_tabella_editabile)                

        self.l_numero_caratteri = QLabel()
        self.l_numero_caratteri.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_numero_caratteri)                
        # se siamo in apertura di un file, aggiorno immediatamente informazione numero caratteri
        if p_contenuto_file is not None:
            self.l_numero_caratteri.setText("Length: " + str(len(self.e_sql.toPlainText())))
        else:
            self.l_numero_caratteri.setText("Length: 0")
        
        self.l_overwrite_enabled = QLabel("INS")
        self.l_overwrite_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_overwrite_enabled)
        # var che indica che è attiva-disattiva la sovrascrittura (tasto insert della tastiera)
        self.v_overwrite_enabled = False
                
        self.l_utf8_enabled = QLabel()
        self.l_utf8_enabled.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusBar.addPermanentWidget(self.l_utf8_enabled)
        # se codifica utf-8 abilitata, la evidenzio
        if v_global_utf_8:
            self.l_utf8_enabled.setText('UTF-8')
        else:
            self.l_utf8_enabled.setText("ANSI")

        ###
        # Definizione della struttura per gestione elenco oggetti DB
        ###
        self.oggetti_db_lista = QtGui.QStandardItemModel()        
        self.oggetti_db_elenco.setModel(self.oggetti_db_lista)
                
        ###
        # Definizione di eventi aggiuntivi
        ###

        # sulla scrollbar imposto evento specifico
        self.o_table.verticalScrollBar().valueChanged.connect(self.slot_scrollbar_azionata)
        # sul cambio della cella imposto altro evento (vale solo quando abilitata la modifica)
        self.o_table.cellChanged.connect(self.slot_o_table_item_modificato)        
        # slot per controllare quando cambia il testo digitato dall'utente
        self.e_sql.textChanged.connect(self.slot_e_sql_modificato)        
            
        # attivo il drop sulla parte di editor
        self.e_sql.setAcceptDrops(True)    
        self.e_sql.installEventFilter(self)   

        # var che si attiva quando l'oggetto viene chiuso
        self.v_editor_chiuso = False
        
    def eventFilter(self, source, event):
        """
           Gestione di eventi personalizzati sull'editor (overwrite, drag&drop)
        """
        # individuo la pressione del stato Insert da parte dell'utente e attivo o meno l'overwrite sull'editor
        if event.type() == QEvent.KeyPress and source is self.e_sql and event.key() == Qt.Key_Insert:
            if self.v_overwrite_enabled:
                self.v_overwrite_enabled = False
                self.l_overwrite_enabled.setText('INS')
                self.e_sql.setOverwriteMode(False)
            else:
                self.v_overwrite_enabled = True
                self.l_overwrite_enabled.setText('OVR')
                self.e_sql.setOverwriteMode(True)
        
        # individuo il drag 
        if event.type() == QEvent.DragEnter and source is self.e_sql:
            event.accept()            
            return True
        
        # idividuo il drop
        if event.type() == QEvent.Drop and source is self.e_sql:
            if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
                data = event.mimeData()
                source_item = QtGui.QStandardItemModel()
                source_item.dropMimeData(data, Qt.CopyAction, 0,0, QModelIndex())                                                
                v_stringa = ''
                for v_indice in range(0,source_item.rowCount()):
                    if v_stringa != '':
                        v_stringa += ',' + source_item.item(v_indice, 0).text()
                    else:
                        v_stringa = source_item.item(v_indice, 0).text()                
                # inserisco nell'editor quanto selezionato dall'utente                
                self.e_sql.insertPlainText(v_stringa)
            
            return True        
        
        return False
        
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
        self.l_numero_caratteri.setText("Length: " + str(len(self.e_sql.toPlainText())))

    def slot_menu_auto_column_resize(self):
        """
           Imposta la var che indica se la tabella del risultato ha attiva la formattazione automatica della larghezza delle colonne
        """
        if self.v_auto_column_resize:
            self.v_auto_column_resize = False
        else:
            self.v_auto_column_resize = True
                                                       
    def slot_connetti(self):
        """
           Esegue connessione a Oracle
        """        
        try:
            # chiudo eventuale connessione già aperta 
            if self.v_connesso:
                self.v_cursor.close()
            oracle_my_lib.inizializzo_client()  
            # connessione al DB come smile
            self.v_connection = cx_Oracle.connect(user=self.e_user_name, 
                                                  password=self.e_user_name, 
                                                  dsn=self.e_server_name)            
            # apro cursore (quello che userà l'utente per i propri sql)
            self.v_cursor = self.v_connection.cursor()                
            # apro cursore (quello usato internamente per la ricerca degli oggetti)
            self.v_cursor_db_obj = self.v_connection.cursor()                
            # imposto var che indica la connesione a oracle
            self.v_connesso = True
        except:
            message_error('Error to oracle connection!')                                             

        # In base al tipo di connessione cambio il colore di sfondo dell'editor (azzurro=sistema reale, bianco=sistema di test)
        if self.e_server_name == 'ICOM_815':            
            v_color = '#aaffff'            
        else:
            v_color = '#ffffff'
        # Imposto il colore di sfondo su tutti gli oggetti principali
        self.e_sql.setStyleSheet("QPlainTextEdit {background-color: " + v_color + ";}")
        self.o_table.setStyleSheet("QTableWidget {background-color: " + v_color + ";}")
        self.o_output.setStyleSheet("QPlainTextEdit {background-color: " + v_color + ";}")
        self.oggetti_db_elenco.setStyleSheet("QListView {background-color: " + v_color + ";}")
                
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
        o_cursore = self.e_sql.textCursor()
        if o_cursore.selectedText() != '':                
            v_testo = o_cursore.selection().toPlainText()                
        else:
            v_testo = self.e_sql.toPlainText()            
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
            self.esegui_select(p_istruzione)
        elif p_istruzione[0:6].upper() in ('INSERT','UPDATE','DELETE'):
            self.esegui_script(p_istruzione, True)
        else:            
            message_error('No supported instruction!')                                 

    def esegui_script(self, p_plsql, p_rowcount):
        """
           Esegue script p_plsql. Se p_rowcount è true allora vengono conteggiate le righe processate (es. update)
        """
        if p_plsql != '':
            self.esegui_plsql(p_plsql, p_rowcount)
        else:
            message_error('No script!')

    def esegui_select(self, p_select):
        """
           Esegue p_select (solo il parser con carico della prima serie di record)
        """
        if self.v_connesso:
            # pulisco elenco
            self.slot_clear('RES')            
            # pulisco la matrice che conterrà elenco delle celle modificate
            self.v_matrice_dati_modificati = []
            
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))                    

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False
            # azzero le var di riga e colonna (serviranno per il carico della pagina)            
            self.y = 0

            # prendo solo il testo che eventualmente l'utente ha evidenziato a video
            self.v_select_corrente = p_select
            
            # se la tabella deve essere editabile
            # all'sql scritto dall'utente aggiungo una parte che mi permette di avere la colonna id riga
            # questa colonna mi servirà per tutte le operazioni di aggiornamento
            if self.v_tabella_editabile:
                v_select = 'SELECT ROWID, MY_SQL.* FROM (' + self.v_select_corrente + ') MY_SQL'    
            else:
                v_select = self.v_select_corrente

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
        if self.v_connesso:            
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))                    

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False

            # attivo output tramite dbms_output
            self.v_cursor.callproc("dbms_output.enable")

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
                # errori riscontrati --> li emetto
                if v_errori:
                    for info in v_errori:
                        self.scrive_output("Error at line " + str(info[0]) + " position " + str(info[1]) + " " + info[2], 'E')
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
                        v_dbms_ret += line + '\n'
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
                
    def carica_pagina(self):
        """
           Carica i dati del flusso record preparato da esegui_select
        """
        if self.v_connesso and self.v_esecuzione_ok:
            # indico che sto caricando la pagina
            self.v_carico_pagina_in_corso = True

            # carico la prossima riga del flusso dati
            v_riga_dati = self.v_cursor.fetchone()
            # se ero a fine flusso --> esco
            if v_riga_dati == None:
                return 'ko'

            # imposto la riga a 1
            self.o_table.setRowCount(1)                        
            # carico i dati presi dal db dentro il modello                        
            while True:
                x = 0                                            
                for field in v_riga_dati:                                                                                                                        
                    # campo stringa
                    if isinstance(field, str):                                                 
                        self.o_table.setItem(self.y, x, QTableWidgetItem( field ) )                                                                
                    # campo numerico (se non funziona provare con i cx_Oracle type
                    elif isinstance(field, float) or isinstance(field, int):                           
                        self.o_table.setItem(self.y, x, QTableWidgetItem( '{:10.0f}'.format(field) ) )                    
                    # campo nullo
                    elif field == None:                                 
                        self.o_table.setItem(self.y, x, QTableWidgetItem( "" ) )                
                    # campo data
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.DATETIME:                                                                            
                        self.o_table.setItem(self.y, x, QTableWidgetItem( str(field) ) )       
                    # se il contenuto è un blob...utilizzo il metodo read sul campo field, poi lo inserisco in una immagine
                    # che poi carico una label e finisce dentro la cella a video
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.BLOB:
                        qimg = QImage.fromData(field.read())
                        pixmap = QPixmap.fromImage(qimg)   
                        label = QLabel()
                        label.setPixmap(pixmap)                        
                        self.o_table.setCellWidget(self.y, x, label )                
                    # se il contenuto è un clob...leggo sempre tramite metodo read e lo carico in un widget di testo largo
                    elif self.tipi_intestazioni[x][1] == cx_Oracle.CLOB:                        
                        qtext = QtWidgets.QTextEdit(field.read())    
                        # da notare come prendeno qtext e trasformandolo in plaintext le prestazioni migliorino di molto                    
                        self.o_table.setItem(self.y, x, QTableWidgetItem( qtext.toPlainText() ) )                                                                                                                
                    x += 1
                # conto le righe (il numeratore è partito da 0, quindi è corretto che venga incrementato a questo punto)
                self.y += 1
                # aumento il numero di righe nella tabella a video
                self.o_table.setRowCount(self.y+1)                        
                # se raggiunto il numero di righe per pagina (100) --> esco dal ciclo
                if self.y % 100 == 0:                
                    break
                # carico la prossima riga del flusso dati
                v_riga_dati = self.v_cursor.fetchone()
                # se raggiunta ultima riga del flusso di dati --> esco dal ciclo
                if v_riga_dati == None:
                    # tolgo la riga che avevo aggiunto
                    self.o_table.setRowCount(self.y)                        
                    break
            
            # indico di calcolare automaticamente la larghezza delle colonne
            if self.v_auto_column_resize:
                self.o_table.resizeColumnsToContents()

            # indico che carico pagina terminato
            self.v_carico_pagina_in_corso = False

            # se è stato richiesto di permettere la modifica dei dati, vuol dire che è presente come prima colonna il rowid, che quindi va nascosta!
            if self.v_tabella_editabile:
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
        # se sono arrivato alla punto più basso della scrollbar, vuol dire che posso caricare gli altri dati
        if posizione == self.o_table.verticalScrollBar().maximum():            
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

        # mi posiziono in fondo (la var y contiene numero di righe...a cui tolgo 1 in quanto il widget parte da 0)
        v_item = QtWidgets.QTableWidgetItem()        
        v_item = self.o_table.item(self.y-1,1)        
        self.o_table.scrollToItem(v_item)
        self.o_table.selectRow(self.y-1)

    def slot_go_to_top(self):
        """
           Scorro fino all'inizio della tabella
        """        
        # mi posiziono in cima
        v_item = QtWidgets.QTableWidgetItem()        
        v_item = self.o_table.item(0,1)        
        self.o_table.scrollToItem(v_item)
        self.o_table.selectRow(0)

    def slot_editabile(self):
        """
           Questa funzione viene richiamata quando si agisce sulla checkbox di editing
        """        
        # se attivato...
        if self.v_tabella_editabile:
            # attivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
            # pulisco la tabella costringendo l'utente a ricaricare la query in quanto deve comparire il rowid
            self.slot_clear('RES')      
            # emetto messaggio sulla status bar
            self.l_tabella_editabile.setText("Editable table: Enabled")            
            self.l_tabella_editabile.setStyleSheet('color: red;')      
        # ...
        else:
            # disattivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)            
            # emetto messaggio sulla status bar
            self.l_tabella_editabile.setText("Editable table: Disabled")            
            self.l_tabella_editabile.setStyleSheet('color: black;')      

    def slot_commit_rollback(self, p_azione):
        """
           Esegue la commit o la rollback
        """
        if self.v_connesso:
            if p_azione == 'Commit':
                # eseguo la commit
                self.v_connection.commit()
                # emetto messaggio e mi sposto sul tab dei messaggi
                self.scrive_output('Commit!','I')            
            elif p_azione == 'Rollback':
                # eseguo la rollback
                self.v_connection.rollback()
                # emetto messaggio e mi sposto sul tab dei messaggi
                self.scrive_output('Rollback!','I')            

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
            self.e_sql.appendPlainText(v_update + ';')                

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
  
    def slot_oggetti_db_scelta(self):
        """
           In base alla voce scelta, viene caricata la lista con elenco degli oggetti pertinenti
        """                        
        # prendo il tipo di oggetto scelto dall'utente
        try:            
            v_tipo_oggetto = Tipi_Oggetti_DB[self.oggetti_db_scelta.currentText()]                
        except:
            v_tipo_oggetto = ''
        # pulisco elenco
        self.oggetti_db_lista.clear()
        # se utente ha scelto un oggetto e si è connessi, procedo con il carico dell'elenco 
        if v_tipo_oggetto != '' and self.v_connesso:
            # leggo elenco degli oggetti indicati
            v_select = "SELECT OBJECT_NAME FROM ALL_OBJECTS WHERE OWNER='" + self.e_user_name + "' AND OBJECT_TYPE='" + v_tipo_oggetto + "'"
            # se necessario applico il filtro di ricerca
            if self.oggetti_db_ricerca.text() != '':
                if self.oggetti_db_tipo_ricerca.currentText() == 'Start with':
                    v_select += " AND OBJECT_NAME LIKE '" + self.oggetti_db_ricerca.text().upper() + "%'"
                if self.oggetti_db_tipo_ricerca.currentText() == 'Like':
                    v_select += " AND OBJECT_NAME LIKE '%" + self.oggetti_db_ricerca.text().upper() + "%'"
            # aggiungo order by
            v_select += " ORDER BY OBJECT_NAME"            
            # eseguo la select
            self.v_cursor_db_obj.execute(v_select)            
            v_righe = self.v_cursor_db_obj.fetchall()            
            # carico elenco nel modello che è collegato alla lista
            for v_riga in v_righe:
                self.oggetti_db_lista.appendRow(QtGui.QStandardItem(v_riga[0]))        

    def slot_oggetti_db_doppio_click(self, p_index):
        """
           Carica la definizione dell'oggetto su cui si è fatto doppio click (es. il sorgente di un package o di una tabella...)           
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
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

            # lettura del sorgente
            if v_tipo_oggetto in ('PACKAGE'):                
                self.v_cursor_db_obj.execute("SELECT TEXT FROM USER_SOURCE WHERE NAME='"+v_nome_oggetto+"' ORDER BY TYPE, LINE")
            elif v_tipo_oggetto in ('PROCEDURE', 'FUNCTION', 'TRIGGER'):                
                self.v_cursor_db_obj.execute("SELECT TEXT FROM USER_SOURCE WHERE NAME='"+v_nome_oggetto+"' ORDER BY TYPE, LINE")
            elif v_tipo_oggetto == 'TABLE' or v_tipo_oggetto == 'VIEW':
                self.v_cursor_db_obj.execute("SELECT A.COLUMN_NAME, A.DATA_TYPE, A.DATA_LENGTH, A.DATA_PRECISION, A.DATA_SCALE, A.NULLABLE, B.COMMENTS FROM ALL_TAB_COLUMNS A, ALL_COL_COMMENTS B WHERE A.OWNER='SMILE' AND A.TABLE_NAME ='"+v_nome_oggetto+"' AND A.OWNER=B.OWNER AND A.TABLE_NAME=B.TABLE_NAME AND A.COLUMN_NAME=B.COLUMN_NAME ORDER BY A.COLUMN_ID")

            # commento iniziale
            self.e_sql.insertPlainText('/*-------------------------------------\n' + v_tipo_oggetto + ' ' + v_nome_oggetto + '\n-------------------------------------*/\n')
            
            # scrivo il sorgente nell'editor
            v_1a_riga = True
            v_count = 0 
            for result in self.v_cursor_db_obj:                                
                v_stringa = ''
                # sorgente di package
                if v_tipo_oggetto in ('PACKAGE'):
                    if v_1a_riga:
                        v_stringa = 'CREATE OR REPLACE ' + result[0]
                    else:                        
                        v_stringa = result[0]                    
                # sorgente di procedura, funzione, trigger
                elif v_tipo_oggetto in ('PROCEDURE', 'FUNCTION', 'TRIGGER'):
                    if v_1a_riga:
                        v_stringa = 'CREATE OR REPLACE ' + result[0]
                    else:
                        v_stringa = result[0]
                # sorgente di tabella
                elif v_tipo_oggetto in ('TABLE','VIEW'):
                    if v_1a_riga:
                        v_stringa = 'CREATE ' + v_tipo_oggetto + ' ' + v_nome_oggetto + '(' + '\n'
                    
                    if v_count > 0:
                        v_stringa += ',\n'

                    v_stringa += result[0] + ' ' 
                    
                    if result[1] in ('NUMBER'):
                        v_stringa += result[1] + '(' + str(result[3]) + ',' + str(result[4]) + ')'
                    else:
                        v_stringa += result[1] + '(' + str(result[2]) + ')'
                    if result[5] == 'N':
                        v_stringa += ' NOT NULL'
                    
                    if result[6] != None:
                        v_stringa += ' /* ' + result[6] + ' */' 
                else:
                    v_stringa = result[0] + '\n'
                
                v_1a_riga = False                
                v_count += 1

                # inserisco nell'editor quanto selezionato dall'utente                
                self.e_sql.insertPlainText(v_stringa)

            # per alcuni tipi di oggetti finalizzo 
            if v_tipo_oggetto in ('TABLE','VIEW'):                
                self.e_sql.insertPlainText(')\n')

            # commento finale
            self.e_sql.insertPlainText('\n/*-------------------------------------*/\n')
                                        
            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()    

    def slot_utf8(self):
        """
           Aggiorna la label nella statusbar relativa alla codifica utf-8
        """
        global v_global_utf_8
        
        # se codifica utf-8 abilitata, la evidenzio
        if v_global_utf_8:
            self.l_utf8_enabled.setText('UTF-8')
        else:
            self.l_utf8_enabled.setText("ANSI")
        
    def slot_savefile(self):
        """
           Salvataggio del testo in un file
        """
        global v_global_utf_8

        if self.v_titolo_window != "" and self.v_titolo_window[0:8] != 'Untitled':     
            try:
                if v_global_utf_8:
                    # scrittura usando utf-8                     
                    v_file = open(self.v_titolo_window,'w',encoding='utf-8')
                else:
                    # scrittura usando ansi
                    v_file = open(self.v_titolo_window,'w')
                v_file.write(self.e_sql.toPlainText())
                v_file.close()
                self.v_testo_modificato = False
                return 'ok'
            except Exception as err:
                message_error('Error to write the file: ' + str(err))
                return 'ko'
        # se il file è nuovo allora viene aperta la finestra di "salva come"
        else:
            self.slot_savefile_as()
        
    def slot_savefile_as(self):
        """
           Salva con nome (al termine richiama il salvataggio normale)
        """        
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save a SQL file","","SQL (*.sql)") [0]                          
        if not filename:
            message_error('Error saving')
            return False        
        if not filename.endswith('.sql'):
            filename += '.sql'

        self.v_titolo_window = filename
        self.setWindowTitle(self.v_titolo_window)

        # richiamo il salvataggio        
        return self.slot_savefile()        

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
                v_ok = self.slot_savefile_as()
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    return 'Yes'
            else:                      
                v_ok = self.slot_savefile()          
                if v_ok != 'ok':
                    return 'Cancel'
                else:
                    return 'Yes'
        # utente chiede di non salvare
        else:
             return 'No'

    def cambio_server_user(self, p_tipo, p_nome):
        """
           Gestione della voce di menu selezionata (server e utente)
        """
        # richiesto il cambio di server
        if p_tipo == 'server':            
            self.e_server_name = p_nome            
        # richiesto il cambio di user
        if p_tipo == 'user':            
            self.e_user_name = p_nome
            
        # connessione
        self.slot_connetti()        

    def slot_font_editor_selector(self):
        """
           Visualizza la scelta del font da usare nell'editor e lo reimposta nell'editor
        """
        font, ok = QFontDialog.getFont(QtGui.QFont("Courier New"))
        if ok:
            self.e_sql.setFont(font)            

    def slot_font_output_selector(self):
        """
           Visualizza la scelta del font da usare nell'output e lo reimposta nell'output
        """
        font, ok = QFontDialog.getFont(QtGui.QFont("Arial"))
        if ok:
            self.o_table.setFont(font)

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
            # da notare come il collegamento delle funzioni venga fatto in questo punto e non nella ui            
            self.win_find.b_next.clicked.connect(self.slot_find_next)                
            # visualizzo la finestra di ricerca
            self.dialog_find.show()

    def slot_find_next(self):
        """
           Ricerca la prossima ricorrenza verso il basso
        """        
        ft = self.win_find.e_find.currentText()
        if self.e_sql.find(ft):
            return
        else:
            self.e_sql.moveCursor(1)
            if self.e_sql.find(ft):
                self.e_sql.moveCursor(QTextCursor.Start, QTextCursor.MoveAnchor)

    def slot_find_e_replace(self):
        """
           Ricerca e sostituisci
        """
        try:
            # visualizzo la finestra di ricerca
            self.dialog_find_e_replace.show()
        except:
            # inizializzo le strutture grafiche e visualizzo la dialog per la ricerca del testo
            self.dialog_find_e_replace = QtWidgets.QDialog()
            self.win_find_e_replace = Ui_Find_e_Replace_Window()        
            self.win_find_e_replace.setupUi(self.dialog_find_e_replace)                
            # da notare come il collegamento delle funzioni venga fatto in questo punto e non nella ui                                    
            self.win_find_e_replace.b_replace_all.clicked.connect(self.slot_find_e_replace_all)                
            # visualizzo la finestra di ricerca
            self.dialog_find_e_replace.show()

    def slot_find_e_replace_all(self):        
        """
           Sostituisce tutte le ricorrenze (ignora differenze tra maiuscole e minuscole)
        """
        import re
        
        # testo da ricercare
        subString = self.win_find_e_replace.e_find.currentText().upper()
        # nuovo testo
        replaceString = self.win_find_e_replace.e_replace.currentText()
        # compilation step to escape the word for all cases
        # the re.IGNORECASE is used to ignore cases
        compileObj = re.compile(re.escape(subString), re.IGNORECASE)
        # substitute the substring with replacing a string using the regex sub() function
        resultantStr = compileObj.sub(replaceString, self.e_sql.document().toPlainText())        
        self.e_sql.setPlainText(resultantStr)

        self.v_testo_modificato = True        

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

        # stampo in blu l'ora di sistema
        v_time = datetime.datetime.now()        
        self.o_output.setCurrentCharFormat(v_pennello_blu)        
        self.o_output.appendPlainText(str(v_time.hour).rjust(2,'0') + ':' + str(v_time.minute).rjust(2,'0') + ':' + str(v_time.second).rjust(2,'0'))         
        # in base al tipo di messaggio stampo messaaggio di colore nero o di colore rosso
        if p_tipo_messaggio == 'E':
            self.o_output.setCurrentCharFormat(v_pennello_rosso)        
            self.o_output.appendPlainText(p_messaggio)                 
        else:
            self.o_output.setCurrentCharFormat(v_pennello_nero)        
            self.o_output.appendPlainText(p_messaggio)                 
        # porto in primo piano la visualizzazione del tab di output
        self.o_tab_widget.setCurrentIndex(1)                         
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
    app = QtWidgets.QApplication([])    
    application = MSql_win1_class()     
    application.show()
    sys.exit(app.exec())    