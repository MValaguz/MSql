# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 01/01/2023
 Descrizione...: Questo programma ha la "pretesa" di essere una sorta di piccolo editor SQL per ambiente Oracle....            
                 al momento si tratta più di un esperimento che di qualcosa di utilizzabile.
"""

# Librerie sistema
import sys
import os
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
# Librerie di data base
import cx_Oracle
import oracle_my_lib
# Librerie grafiche
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Libreria per export in excel
from xlsxwriter.workbook import Workbook
# Classe qtdisegner
from oracle_my_sql_ui import Ui_oracle_my_sql_window
from find_ui import Ui_FindWindow
from find_e_replace_ui import Ui_Find_e_Replace_Window
from avanzamento import avanzamento_infinito_class
# Classe per evidenziare il codice 
import highlighting_words_in_text_editor
# Librerie interne 
from preferenze import *
from utilita import *
from utilita_database import *

# Tipi oggetti di database
Tipi_Oggetti_DB = { 'Tables':'TABLE',                    
                    'Package':'PACKAGE',
                    'Trigger':'TRIGGER',
                    'Procedures':'PROCEDURE',
                    'Functions':'FUNCTION',
                    'Views':'VIEW' }

# Classe principale       
class oracle_my_sql_class(QtWidgets.QMainWindow, Ui_oracle_my_sql_window):
    """
        Oracle My Sql
    """       
    def __init__(self):
        # incapsulo la classe grafica da qtdesigner
        super(oracle_my_sql_class, self).__init__()        
        self.setupUi(self)
        self.titolo_window = 'Oracle MySql'
        self.setWindowTitle(self.titolo_window)
        
        # splitter che separa l'editor dall'output: imposto l'immagine per indicare lo splitter e il relativo rapporto tra il widget di editor e quello di output
        self.splitter.setStyleSheet("QSplitter::handle {image: url(':/icons/icons/splitter.gif')}")
        self.splitter.setStretchFactor(1,0)
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
        self.actionBACKUP_815.setChecked(True)
        self.e_server_name = 'BACKUP_815'
        self.actionUSER_SMILE.setChecked(True)
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
        # var che indica che il testo è stato modificato
        self.v_testo_modificato = False
        # var che indica se attivare l'auto column resize (incide sulle prestazioni del caricamento)
        self.v_auto_column_resize = False                                                        
        # Contiene il nome del file in elaborazione
        self.filename = ''     
        # Contiene la preferenza se caricare e salvare i file nel formato UTF-8
        self.utf8_coding = False   

        ###
        # Importo le preferenze di MGrep        
        ###

        self.o_preferenze = preferenze()
        self.o_preferenze.carica()
        
        # imposto un sql di prova                    
        self.e_sql.setPlainText("SELECT * FROM OC_ORTES WHERE AZIEN_CO='SMI' AND ESERC_CO='2023'")        
        
        # massimizzo la finestra        
        self.showMaximized()
        
        # imposto blocco editabilità della tabella (verrà attivata solo su richiesta specifica dell'utente)
        self.slot_editabile()

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

    def eventFilter(self, source, event):
        """
           Per la parte di editor, gestisco il drop (in arrivo solitamente dalla lista degli oggetti di database) 
        """
        if event.type() == QEvent.DragEnter and source is self.e_sql:
            event.accept()            
            return True
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
              
    def slot_menu_utf8(self):
        """
           Gestione dell'opzione che permette di indicare se caricare/salvare i file nel formato utf-8
        """
        if self.utf8_coding:
            self.actionUTF_8_Coding.setChecked(False)
            self.utf8_coding = False
        else:
            self.actionUTF_8_Coding.setChecked(True)
            self.utf8_coding = True
            
    def slot_e_sql_modificato(self):
        """
           Viene richiamato quando si modifica del testo dentro la parte di istruzione sql
        """        
        self.v_testo_modificato = True

    def slot_o_table_item_modificato(self, x, y):
        """
            Funzione che viene richiamata quando un item della tabella viene modificato (solo quando attiva la modifica)
        """        
        if not self.v_carico_pagina_in_corso:            
            print('ciao' + str(x) + str(y))
            # memorizzo nella matrice la coppia x,y della cella modificata
            self.v_matrice_dati_modificati.append((x,y))            

    def slot_editabile(self):
        """
           Questa funzione viene richiamata quando si agisce sulla checkbox di editing
        """        
        # se attivato...
        if self.actionMake_table_editable.isChecked():
            # attivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.AllEditTriggers)
            # pulisco la tabella costringendo l'utente a ricaricare la query in quanto deve comparire il rowid
            self.o_table.clearContents()
            self.o_table.setRowCount(0)
            # emetto messaggio sulla status bar
            self.statusBar.showMessage("The table is now editable!")                             
        # ...
        else:
            # disattivo le modifiche sulla tabella
            self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            # abilito bottone di salvataggio
            #self.b_save_table.setEnabled(False)
            # emetto messaggio sulla status bar
            self.statusBar.showMessage("Edit table disabled!")                             

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

    def slot_menu_auto_column_resize(self):
        """
           Imposta la var che indica se la tabella del risultato ha attiva la formattazione automatica della larghezza delle colonne
        """
        if self.v_auto_column_resize:
            self.v_auto_column_resize = False
        else:
            self.v_auto_column_resize = True

    def slot_menu_server_ICOM_815(self):
        """
           Cambio voce di menu inerenti il nome del server e il nome dell'utente
        """
        self.cambio_server_user('server','ICOM_815')

    def slot_menu_server_BACKUP_815(self):
        """
           Cambio voce di menu inerenti il nome del server e il nome dell'utente
        """
        self.cambio_server_user('server','BACKUP_815')
    
    def slot_menu_server_BACKUP_2_815(self):
        """
           Cambio voce di menu inerenti il nome del server e il nome dell'utente
        """
        self.cambio_server_user('server','BACKUP_2_815')
    
    def slot_menu_user_SMILE(self):
        """
           Cambio voce di menu inerenti il nome del server e il nome dell'utente
        """
        self.cambio_server_user('user','SMILE')

    def slot_menu_user_SMI(self):
        """
           Cambio voce di menu inerenti il nome del server e il nome dell'utente
        """
        self.cambio_server_user('user','SMI')

    def cambio_server_user(self, p_tipo, p_nome):
        """
           Gestione della voce di menu selezionata (server e utente)
        """
        # richiesto il cambio di server
        if p_tipo == 'server':
            if p_nome == 'ICOM_815':
                self.actionICOM_815.setChecked(True)
                self.actionBACKUP_815.setChecked(False)
                self.actionBACKUP_2_815.setChecked(False)
                self.e_server_name = 'ICOM_815'
            if p_nome == 'BACKUP_815':
                self.actionICOM_815.setChecked(False)
                self.actionBACKUP_815.setChecked(True)
                self.actionBACKUP_2_815.setChecked(False)
                self.e_server_name = 'BACKUP_815'
            if p_nome == 'BACKUP_2_815':
                self.actionICOM_815.setChecked(False)
                self.actionBACKUP_815.setChecked(False)
                self.actionBACKUP_2_815.setChecked(True)
                self.e_server_name = 'BACKUP_2_815'
        # richiesto il cambio di user
        if p_tipo == 'user':
            if p_nome == 'SMILE':
                self.actionUSER_SMILE.setChecked(True)
                self.actionUSER_SMI.setChecked(False)                
                self.e_user_name = 'SMILE'
            if p_nome == 'SMI':
                self.actionUSER_SMILE.setChecked(False)
                self.actionUSER_SMI.setChecked(True)                
                self.e_user_name = 'SMI'
        # connessione
        self.slot_connetti()        
                                        
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
                
    def slot_esegui(self):
        """
           Esegue statement sql (solo il parser con carico della prima serie di record)
        """
        if self.v_connesso:
            # pulisco elenco
            self.o_table.clear()
            # pulisco la status bar con un messaggio vuoto
            self.statusBar.showMessage("")                 
            # pulisco la matrice che conterrà elenco delle celle modificate
            self.v_matrice_dati_modificati = []
            
            # sostituisce la freccia del mouse con icona "clessidra"
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))                    

            # imposto indicatore di esecuzione a false --> nessuna esecuzione
            self.v_esecuzione_ok = False
            # azzero le var di riga e colonna (serviranno per il carico della pagina)            
            self.y = 0

            # prendo solo il testo che eventualmente l'utente ha evidenziato a video
            self.v_select_corrente = ''
            o_cursore = self.e_sql.textCursor()
            if o_cursore.selectedText() != '':                
                self.v_select_corrente = o_cursore.selection().toPlainText()                
            else:
                self.v_select_corrente = self.e_sql.toPlainText()            
            if self.v_select_corrente == '':
                # ripristino icona freccia del mouse
                QApplication.restoreOverrideCursor()                        
                # emetto errore sulla barra di stato 
                self.statusBar.showMessage('No instruction!')                                 
                return 'ko'

            # se la tabella deve essere editabile
            # all'sql scritto dall'utente aggiungo una parte che mi permette di avere la colonna id riga
            # questa colonna mi servirà per tutte le operazioni di aggiornamento
            if self.actionMake_table_editable.isChecked():
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
                self.statusBar.showMessage("Error: " + errorObj.message)                 
                return 'ko'
                        
            # lista contenente le intestazioni (tramite apposita funzione si ricavano i nomi delle colonne dall'sql che si intende eseguire)
            self.nomi_intestazioni = nomi_colonne_istruzione_sql(self.v_cursor)                                    
            self.o_table.setColumnCount(len(self.nomi_intestazioni))                                        
            # lista contenente i tipi delle colonne 
            self.tipi_intestazioni = self.v_cursor.description
            # setto le intestazioni e imposto il numero di righe a 1
            self.o_table.setHorizontalHeaderLabels(self.nomi_intestazioni)            
            self.o_table.setRowCount(1)                        

            # se tutto ok, posso procedere con il caricare la prima pagina
            self.carica_pagina()                            

            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()                        
                
    def carica_pagina(self):
        """
           Carica i dati del flusso record preparato da slot_esegui
        """
        if self.v_connesso and self.v_esecuzione_ok:
            # indico che sto caricando la pagina
            self.v_carico_pagina_in_corso = True

            # carico la prossima riga del flusso dati
            v_riga_dati = self.v_cursor.fetchone()
            # se ero a fine flusso --> esco
            if v_riga_dati == None:
                return 'ko'

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
            if self.actionMake_table_editable.isChecked():
                self.o_table.setColumnHidden(0, True)
            else:
                self.o_table.setColumnHidden(0, False)

            # se ero a fine flusso --> esco con codice specifico
            if v_riga_dati == None:
                return 'ko'

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
            self.e_sql.insertPlainText('/*-------------------------------------*/\n')
                                        
            # Ripristino icona freccia del mouse
            QApplication.restoreOverrideCursor()    

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
            
    def slot_openfile(self):
        """
           Apertura di un file
        """
        if self.maybeSave():            
            fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Documents/","SQL Files (*.sql *.pls *.plb);;All Files (*.*)")                
            if fileName[0] != "":
                try:
                    if self.utf8_coding:
                        # lettura usando utf-8                                         
                        v_file = open(fileName[0],'r',encoding='utf-8')
                    else:
                        # lettura usando ascii
                        v_file = open(fileName[0],'r')
                    self.e_sql.clear()                                    
                    self.e_sql.setPlainText( v_file.read())
                    self.filename = fileName[0]
                    self.v_testo_modificato = False
                    self.setWindowTitle(self.titolo_window + ': ' + self.filename)                    
                except Exception as err:
                    message_error('Error to opened the file: ' + str(err))

    def slot_savefile(self):
        """
           Salvataggio del testo in un file
        """
        if (self.filename != ""):     
            try:
                if self.utf8_coding:
                    # scrittura usando utf-8                     
                    v_file = open(self.filename,'w',encoding='utf-8')
                else:
                    # scrittura usando ascii
                    v_file = open(self.filename,'w')
                v_file.write(self.e_sql.toPlainText())
                v_file.close()
                self.v_testo_modificato = False
                self.setWindowTitle(self.titolo_window + ': ' + self.filename)                    
            except Exception as err:
                message_error('Error to write the file: ' + str(err))
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

        self.filename = filename

        # richiamo il salvataggio
        self.slot_savefile()

    def closeEvent(self, e):
        """
           Intercetto l'evento di chiusura del form e controllo se devo chiedere di salvare o meno
        """
        if self.maybeSave():
            e.accept()
        else:           
            self.close()            
    
    def maybeSave(self):
        """
           All'uscita dal form controllo se chiedere di salvare o meno
        """
        if not self.v_testo_modificato:
            return True

        if message_question_yes_no("The document was modified." + chr(13) + "Do you want to save changes?") == 'Yes':
            if self.filename == "":
                self.slot_savefile_as()
                return False
            else:      
                self.slot_savefile()          
                return False
        else:
             return True

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

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":       
    app = QtWidgets.QApplication([])    
    application = oracle_my_sql_class()     
    application.show()
    sys.exit(app.exec())    