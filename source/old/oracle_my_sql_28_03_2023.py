# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 01/01/2023
 Descrizione...: Questo programma ha la "pretesa" di essere una sorta di piccolo editor SQL, sia per Oracle che per SQLite....
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
#Librerie grafiche
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Classe qtdisegner
from oracle_my_sql_ui import Ui_oracle_my_sql_window
from find_ui import Ui_FindWindow
# Librerie interne 
from utilita import *
from utilita_database import *

# Classe principale       
class oracle_my_sql_class(QtWidgets.QMainWindow, Ui_oracle_my_sql_window):
    """
        Oracle My Sql
    """       
    def __init__(self):
        # incapsulo la classe grafica da qtdesigner
        super(oracle_my_sql_class, self).__init__()        
        self.setupUi(self)
        # massimizzo la finestra
        #self.showMaximized()
        # imposto l'immagine per indicare lo splitter
        self.splitter.setStyleSheet("QSplitter::handle {image: url(':/icons/icons/splitter.gif')}")
        
        # aggiungo alla toolbar la scelta del server
        #self.l_server_name = QLabel()                
        #self.l_server_name.setText("  Oracle name server: ")
        #self.l_user_name = QLabel()                
        #self.l_user_name.setText("  Oracle user name: ")
        #self.l_editable = QLabel()                
        #self.l_editable.setText("  Editable: ")
        
        # aggiungo alla toolbar elenco degli utenti (combobox editabile)
        #self.e_server_name = QComboBox()
        #self.e_user_name = QComboBox()
        #self.e_user_name.setEditable(True)
        
        # aggiungo alla toolbar checkbox che indica se il risultato della query deve essere editabile
        #self.e_editable = QCheckBox()        

        # aggiungo azione di commit ma nascosta (si visualizza solo quando il risultato della query è editabile)
        #self.b_save_table = QAction()
        #icon4 = QIcon()
        #icon4.addPixmap(QtGui.QPixmap(":/icons/icons/confirm.gif"), QIcon.Normal, QIcon.Off)
        #self.b_save_table.setIcon(icon4)        
        #self.b_save_table.setToolTip("Save the changes on table")                        
        #self.b_save_table.setEnabled(False)                        
                
        # porto gli oggetti sulla toolbar        
        #self.toolBar.addWidget(self.l_server_name)   
        #self.toolBar.addWidget(self.e_server_name)   
        #self.toolBar.addWidget(self.l_user_name)   
        #self.toolBar.addWidget(self.e_user_name)   
        #self.toolBar.addSeparator()
        #self.toolBar.addWidget(self.l_editable)   
        #self.toolBar.addWidget(self.e_editable)        
        #self.toolBar.addAction(self.b_save_table)
        #self.toolBar.addSeparator()
        
        # imposto la parte relativa al server/user a cui collegarsi
        self.actionBACKUP_815.setChecked(True)
        self.e_server_name = 'BACKUP_815'
        self.actionUSER_SMILE.setChecked(True)
        self.e_user_name = 'SMILE'                        
        # attivo la var che indica se si è connessi
        self.v_connesso = False                               
        # eseguo la connessione 
        self.slot_connetti()   

        ###
        # DICHIRAZIONE VAR GENERALI
        ###

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

        # sql di prova        
        self.e_sql.setPlainText("SELECT * FROM   DO_DCTIP WHERE  AZIEN_CO='SMI' AND TDOCU_CO = 'NCAF'")
                                
        # Contiene il nome del file in elaborazione
        self.filename = ''
        
        ###
        # Definizione della toolbar di trova e sostituisci
        ###
        """
        self.tbf = QToolBar(oracle_my_sql_window)
        oracle_my_sql_window.addToolBar(Qt.TopToolBarArea, self.tbf)
        self.tbf.setWindowTitle("Find Toolbar")   
        self.findfield = QLineEdit()
        self.findfield.addAction(QIcon.fromTheme("edit-find"), QLineEdit.LeadingPosition)
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(150)
        self.findfield.setPlaceholderText("find")
        self.findfield.setToolTip("press RETURN to find")
        self.findfield.setText("")
        ft = self.findfield.text()
        self.findfield.returnPressed.connect(self.findText)
        self.tbf.addWidget(self.findfield)
        self.replacefield = QLineEdit()
        self.replacefield.addAction(QIcon.fromTheme("edit-find-and-replace"), QLineEdit.LeadingPosition)
        self.replacefield.setClearButtonEnabled(True)
        self.replacefield.setFixedWidth(150)
        self.replacefield.setPlaceholderText("replace with")
        self.replacefield.setToolTip("press RETURN to replace the first")
        self.replacefield.returnPressed.connect(self.replaceOne)
        self.tbf.addSeparator() 
        self.tbf.addWidget(self.replacefield)
        self.tbf.addAction("replace all", self.replaceAll)
        self.tbf.addSeparator()
        """
        # sulla scrollbar imposto evento specifico
        self.o_table.verticalScrollBar().valueChanged.connect(self.slot_scrollbar_azionata)
        # sul cambio della cella imposto altro evento (vale solo quando abilitata la modidica)
        self.o_table.cellChanged.connect(self.slot_o_table_item_modificato)        
        #self.o_table.currentItemChanged()
        # collego alla combobox l'azione di riconnetti
        #self.e_server_name.currentIndexChanged['QString'].connect(self.slot_connetti)        
        # collego alla combobox l'azione di connessione (attenzione che se utente esce con il tab non funziona....problema da risolvere)
        #self.e_user_name.currentIndexChanged['QString'].connect(self.slot_connetti)                
        # collego lo slot per il salvataggio dei dati modificati in tabella
        #self.b_save_table.triggered.connect(self.slot_save_o_table)
        # azione di cambio flag per editazione tabella
        #self.e_editable.stateChanged.connect(self.slot_e_editable_cambiata)        
        # slot per controllare quando cambia il testo digitato dall'utente
        self.e_sql.textChanged.connect(self.slot_e_sql_modificato)
            
    """
    # Definizione interfaccia
    def setupUi(self, oracle_my_sql_window):        
        # Dimensioni della window e icona di riferimento
        oracle_my_sql_window.resize(1000, 800)
        self.titolo_window = "Oracle My Sql"
        oracle_my_sql_window.setWindowTitle(self.titolo_window)
        icon = QIcon()
        icon.addPixmap(QPixmap("qtdesigner/icons/MSql.gif"), QIcon.Normal, QIcon.Off)
        oracle_my_sql_window.setWindowIcon(icon)
        
        # Status bar (dove escono messaggi di errore sql)
        self.statusBar = QStatusBar(oracle_my_sql_window)
        self.statusBar.setEnabled(True)
        self.statusBar.setSizeGripEnabled(True)        
        oracle_my_sql_window.setStatusBar(self.statusBar)
                
        # Editor sql (definizione dell'oggetto con tipo di font, ecc)
        self.e_sql = QPlainTextEdit()
        font = QFont()
        font.setFamily("Courier")
        font.setPointSize(10)
        self.e_sql.setFont(font)
        
        # Editor --> definizione dell'oggetto che riporta i numeri di riga lateralmente
        self.e_sql_num_riga = NumberBar(self.e_sql)
        #layoutH = QtWidgets.QHBoxLayout()
        #layoutH.setSpacing(1.5)
        #layoutH.addWidget(self.e_sql_num_riga)
        #layoutH.addWidget(self.e_sql)
                
        # Oggetto dove escono i risultati dell'sql
        self.o_table = QTableWidget()
        #sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #sizePolicy.setHorizontalStretch(0)
        #sizePolicy.setVerticalStretch(20)
        #sizePolicy.setHeightForWidth(self.o_table.sizePolicy().hasHeightForWidth())
        #self.o_table.setSizePolicy(sizePolicy)
        self.o_table.setAlternatingRowColors(True)
        self.o_table.setGridStyle(Qt.SolidLine)        
        self.o_table.setColumnCount(0)
        self.o_table.setRowCount(0)
        self.o_table.horizontalHeader().setSortIndicatorShown(True)
        self.o_table.setSortingEnabled(True)
        # fin quando utente non indica volontà di modificare la tabella, ne blocco la modifica
        self.o_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # sulla scrollbar imposto evento specifico
        self.o_table.verticalScrollBar().valueChanged.connect(self.slot_scrollbar_azionata)
        # sul cambio della cella imposto altro evento (vale solo quando abilitata la modidica)
        self.o_table.cellChanged.connect(self.slot_o_table_item_modificato)        
        
        # Definizione della toolbar per caricamento e salvataggio
        self.toolBar = QToolBar(oracle_my_sql_window)        
        oracle_my_sql_window.addToolBar(Qt.TopToolBarArea, self.toolBar)        
        self.actionLoad_sql = QAction(oracle_my_sql_window)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap("qtdesigner/icons/folder.gif"), QIcon.Normal, QIcon.Off)
        self.actionLoad_sql.setIcon(icon1)
        self.actionLoad_sql.setText("Load sql")
        self.actionLoad_sql.setToolTip("Load a file sql")
        self.actionSave_sql = QAction(oracle_my_sql_window)
        icon2 = QIcon()
        icon2.addPixmap(QPixmap("qtdesigner/icons/disk.gif"), QIcon.Normal, QIcon.Off)
        self.actionSave_sql.setIcon(icon2)
        self.actionSave_sql.setText("Save sql")
        self.actionSave_sql.setToolTip("Save sql into a file")
        self.actionExecute_sql = QAction(oracle_my_sql_window)
        icon3 = QIcon()
        icon3.addPixmap(QPixmap("qtdesigner/icons/go.gif"), QIcon.Normal, QIcon.Off)
        self.actionExecute_sql.setIcon(icon3)
        self.actionExecute_sql.setText("Execute sql")
        self.actionExecute_sql.setToolTip("Execute de sql statement")
        self.actionExecute_sql.setShortcut("F5")
        self.toolBar.addAction(self.actionLoad_sql)
        self.toolBar.addAction(self.actionSave_sql)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionExecute_sql)
        
        self.actionLoad_sql.triggered.connect(self.openFile)
        self.actionSave_sql.triggered.connect(self.fileSave)
        self.actionExecute_sql.triggered.connect(self.slot_esegui)
        
        QMetaObject.connectSlotsByName(oracle_my_sql_window)
                
        # aggiungo alla toolbar le label e la combobox della scelta del server, del nome utente        
        self.l_server_name = QLabel()                
        self.l_server_name.setText("Oracle name server:")
        self.l_user_name = QLabel()                
        self.l_user_name.setText("Oracle user name:")
        self.l_editable = QLabel()                
        self.l_editable.setText("Editable:")

        self.b_save_table = QAction(oracle_my_sql_window)
        icon4 = QIcon()
        icon4.addPixmap(QPixmap("icons/confirm.gif"), QIcon.Normal, QIcon.Off)
        self.b_save_table.setIcon(icon4)
        self.b_save_table.setText("Save changes")
        self.b_save_table.setToolTip("Save the changes on table")                        
        self.b_save_table.setEnabled(False)
        self.b_save_table.triggered.connect(self.slot_save_o_table)
        
        # combobox con elenco dei server e elenco degli utenti (combobox editabile)
        self.e_server_name = QComboBox()
        self.e_user_name = QComboBox()
        self.e_user_name.setEditable(True)
        # checkbox che indica se la tabella deve essere editabile
        self.e_editable = QCheckBox()
        self.e_editable.stateChanged.connect(self.slot_e_editable_cambiata)
                
        # porto gli oggetti sulla toolbar
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.l_server_name)   
        self.toolBar.addWidget(self.e_server_name)   
        self.toolBar.addWidget(self.l_user_name)   
        self.toolBar.addWidget(self.e_user_name)   
        self.toolBar.addWidget(self.l_editable)   
        self.toolBar.addWidget(self.e_editable)
        self.toolBar.addAction(self.b_save_table)

        # attivo la var che indica se si è connessi
        self.v_connesso = False
                       
        # carico elenco dei server prendendolo dalle preferenze 
        # Attenzione! Verrà richiamato in automatico l'evento di connessione a oracle        
        self.e_server_name.addItem('ICOM_815')
        self.e_server_name.addItem('BACKUP_815')
        self.e_server_name.addItem('BACKUP_2_815')
        # imposto come server di default quello di test (che di solito si trova in seconda posizione)
        self.e_server_name.setCurrentIndex(1)            
        # collego alla combobox l'azione         
        self.e_server_name.currentIndexChanged['QString'].connect(self.slot_connetti)        

        # carico elenco degli user 
        self.e_user_name.addItem('SMILE')
        self.e_user_name.addItem('SMI')
        # collego alla combobox l'azione di connessione (attenzione che se utente esce con il tab non funziona....problema da risolvere)
        self.e_user_name.currentIndexChanged['QString'].connect(self.slot_connetti)                

        # eseguo la connessione 
        self.slot_connetti()   

        ###
        # DICHIRAZIONE VAR GENERALI
        ###

        # inizializzo var che contiene la select corrente
        self.v_select_corrente = ''
        # inizializzo var che indica che l'esecuzione è andata ok
        self.v_esecuzione_ok = False  
        # inizializzo var che indica che si è in fase di caricamento dei dati
        self.v_carico_pagina_in_corso = False   
        # inzializzo la var che conterrà eventuale matrice dei dati modificati
        self.v_matrice_dati_modificati = []
        
        ###
        # Definizione della toolbar di trova e sostituisci
        ###
        self.tbf = QToolBar(oracle_my_sql_window)
        oracle_my_sql_window.addToolBar(Qt.TopToolBarArea, self.tbf)
        self.tbf.setWindowTitle("Find Toolbar")   
        self.findfield = QLineEdit()
        self.findfield.addAction(QIcon.fromTheme("edit-find"), QLineEdit.LeadingPosition)
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(150)
        self.findfield.setPlaceholderText("find")
        self.findfield.setToolTip("press RETURN to find")
        self.findfield.setText("")
        ft = self.findfield.text()
        self.findfield.returnPressed.connect(self.findText)
        self.tbf.addWidget(self.findfield)
        self.replacefield = QLineEdit()
        self.replacefield.addAction(QIcon.fromTheme("edit-find-and-replace"), QLineEdit.LeadingPosition)
        self.replacefield.setClearButtonEnabled(True)
        self.replacefield.setFixedWidth(150)
        self.replacefield.setPlaceholderText("replace with")
        self.replacefield.setToolTip("press RETURN to replace the first")
        self.replacefield.returnPressed.connect(self.replaceOne)
        self.tbf.addSeparator() 
        self.tbf.addWidget(self.replacefield)
        self.tbf.addAction("replace all", self.replaceAll)
        self.tbf.addSeparator()
                
        #----------------------------------------
        # Inizio Impaginazione di tutti gli oggetti
        # In pratica creo un primo layout dove inserisco l'oggetto che visualizza il numero di riga
        # e l'editor sql. Questo layout lo inserisco in un frame (questo perché lo splitter può essere solo
        # tra due widget e non tra due layout)
        # Creo un secondo layout dove inserisco il risultato sql, lo inserisco in un altro frame
        # Inserisco i due frame dentro uno splitter indicando che deve essere visualizzato in verticale
        # con una proporzione 1-2 
        layoutH = QHBoxLayout()
        layoutH.setSpacing(1)
        layoutH.addWidget(self.e_sql_num_riga)
        layoutH.addWidget(self.e_sql)
        
        my_frame = QFrame()
        my_frame.setLayout(layoutH)
        
        layoutV = QVBoxLayout()
        layoutV.addWidget(self.o_table)
        
        my_frame1 = QFrame()
        my_frame1.setLayout(layoutV)
        
        sizePolicy = QSizePolicy()
        sizePolicy.setVerticalStretch(1)
        
        my_frame.setSizePolicy(sizePolicy)
        
        sizePolicy.setVerticalStretch(2)
        my_frame1.setSizePolicy(sizePolicy)
        
        #splitter = QtWidgets.QSplitter(Qt.Vertical)
        splitter = customSplitter(Qt.Vertical)
        splitter.addWidget(my_frame)
        splitter.addWidget(my_frame1)            

        oracle_my_sql_window.setCentralWidget(splitter)                
        # Fine Impaginazione di tutti gli oggetti
        #----------------------------------------
                            
        # sql di prova        
        self.e_sql.setPlainText("SELECT * FROM DO_DCTIP")
        
        #self.o_table.itemChanged.connect(self.log_change)
                        
        # Contiene il nome del file in elaborazione
        self.filename = ''
    """

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
        # sostituisce la freccia del mouse con icona "clessidra"
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))        

        # carico tutte le pagine fino ad arrivare in fondo
        while self.carica_pagina() != 'ko':
            pass

        # mi posiziono in fondo (la var y contiene numero di righe...a cui tolgo 1 in quanto il widget parte da 0)
        v_item = QtWidgets.QTableWidgetItem()        
        v_item = self.o_table.item(self.y-1,1)        
        self.o_table.scrollToItem(v_item)
        self.o_table.selectRow(self.y-1)
                
        # Ripristino icona freccia del mouse
        QApplication.restoreOverrideCursor()    

    def slot_go_to_top(self):
        """
           Scorro fino all'inizio della tabella
        """        
        # mi posiziono in cima
        v_item = QtWidgets.QTableWidgetItem()        
        v_item = self.o_table.item(0,1)        
        self.o_table.scrollToItem(v_item)
        self.o_table.selectRow(0)

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
            # apro cursore
            self.v_cursor = self.v_connection.cursor()                
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
            self.intestazioni = nomi_colonne_istruzione_sql(self.v_cursor)                                    
            self.o_table.setColumnCount(len(self.intestazioni))                                        
            # setto le intestazioni e imposto il numero di righe a 1
            self.o_table.setHorizontalHeaderLabels(self.intestazioni)            
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
                    # campo numerico (se non funziona provare con i cx_Oracle type
                    if isinstance(field, float) or isinstance(field, int):                           
                        self.o_table.setItem(self.y, x, QTableWidgetItem( '{:10.0f}'.format(field) ) )
                    # campo nullo
                    elif field == None:                                                
                        self.o_table.setItem(self.y, x, QTableWidgetItem( "" ) )                
                    # se il contenuto è un clob...utilizzo il metodo read sul campo field, poi lo inserisco in una immagine
                    # che poi carico una label e finisce dentro la cella a video
                    elif self.v_cursor.description[x][1] == cx_Oracle.BLOB:                                                                            
                        qimg = QImage.fromData(field.read())
                        pixmap = QPixmap.fromImage(qimg)   
                        label = QLabel()
                        label.setPixmap(pixmap)                        
                        self.o_table.setCellWidget(self.y, x, label )                
                    # campo data
                    elif self.v_cursor.description[x][1] == cx_Oracle.DATETIME:                                                                            
                        self.o_table.setItem(self.y, x, QTableWidgetItem( str(field) ) )       
                    # campo stringa
                    else:                                                 
                        self.o_table.setItem(self.y, x, QTableWidgetItem( field ) )                                            
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
            v_update = "UPDATE " + v_table_name + " SET " + self.intestazioni[yx[1]] + "='" + v_valore_cella + "' WHERE ROWID = '" + v_rowid + "'"
            self.e_sql.appendPlainText(v_update + ';')                
            
    def slot_openfile(self):
        """
           Apertura di un file
        """
        if self.maybeSave():            
            fileName = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Documents/","SQL Files (*.sql);;All Files (*.*)")                
            if fileName[0] != "":
                try:             
                    v_file = open(fileName[0],'r')
                    self.e_sql.clear()                        
                    self.e_sql.setPlainText( v_file.read() )
                    self.filename = fileName
                    self.v_testo_modificato = False
                    self.setWindowTitle(self.windowTitle() + ': ' + fileName[0])
                    self.document = self.e_sql.document()                        
                except:
                    message_error('Error to opened the file')

    def slot_savefile(self):
        """
           Salvataggio del testo in un file
        """
        if (self.filename != ""):            
            file = QFile(self.filename[0])            
            if not file.open( QFile.WriteOnly | QFile.Text):
                message_error("Cannot write file %s:\n%s." % (self.filename, file.errorString()))
                return

            outstr = QTextStream(file)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            outstr << self.e_sql.toPlainText()
            QApplication.restoreOverrideCursor()                
            self.v_testo_modificato = False
            self.fname = QFileInfo(self.filename[0]).fileName() 
            self.setWindowTitle(self.fname + "[*]")            
        # se il file è nuovo allora viene aperta la finestra di "salva come"
        else:
            self.fileSaveAs()
        
    def fileSaveAs(self):
        """
           Salva come
        """
        fn, _ = QFileDialog.getSaveFileName(self, "Save as...", self.filename,"SQL files (*.sql)")

        if not fn:
            message_error('Error saving')
            return False

        lfn = fn.lower()
        if not lfn.endswith('.sql'):
            fn += '.sql'

        self.filename = fn
        self.fname = os.path.splitext(str(fn))[0].split("/")[-1]
        return self.fileSave()

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
           all'uscita dal form controllo se chiedere di salvare o meno
        """
        if not self.v_testo_modificato:
            return True
                
        #if self.filename != '':
        #    return True

        ret = message_question_yes_no("The document was modified." + chr(13) + "Do you want to save changes?")

        if ret == 'Yes':
            if self.filename == "":
                self.fileSaveAs()
                return False
            else:
                self.fileSave()
                return True
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
        print('next')
        ft = self.win_find.e_find.text()
        if self.e_sql.find(ft):
            return
        else:
            self.e_sql.moveCursor(1)
            if self.e_sql.find(ft):
                self.e_sql.moveCursor(QTextCursor.Start, QTextCursor.MoveAnchor)
    """
    def match_left(self, block, character, start, found):
        map = {'{': '}', '(': ')', '[': ']'}

        while block.isValid():
            data = block.userData()
            if data is not None:
                braces = data.braces
                N = len(braces)

                for k in range(start, N):
                    if braces[k].character == character:
                        found += 1

                    if braces[k].character == map[character]:
                        if not found:
                            return braces[k].position + block.position()
                        else:
                            found -= 1

                block = block.next()
                start = 0

    def match_right(self, block, character, start, found):
        map = {'}': '{', ')': '(', ']': '['}

        while block.isValid():
            data = block.userData()

            if data is not None:
                braces = data.braces

                if start is None:
                    start = len(braces)
                for k in range(start - 1, -1, -1):
                    if braces[k].character == character:
                        found += 1
                    if braces[k].character == map[character]:
                        if found == 0:
                            return braces[k].position + block.position()
                        else:
                            found -= 1
            block = block.previous()
            start = None

        cursor = self.editor.textCursor()
        block = cursor.block()
        data = block.userData()
        previous, next = None, None

        if data is not None:
            position = cursor.position()
            block_position = cursor.block().position()
            braces = data.braces
            N = len(braces)

            for k in range(0, N):
                if braces[k].position == position - block_position or braces[k].position == position - block_position - 1:
                    previous = braces[k].position + block_position
                    if braces[k].character in ['{', '(', '[']:
                        next = self.match_left(block,
                                               braces[k].character,
                                               k + 1, 0)
                    elif braces[k].character in ['}', ')', ']']:
                        next = self.match_right(block,
                                                braces[k].character,
                                                k, 0)
                    if next is None:
                        next = -1

        if next is not None and next > 0:
            if next == 0 and next >= 0:
                format = QTextCharFormat()

            cursor.setPosition(previous)
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor)

            format.setBackground(QColor('white'))
            self.left_selected_bracket.format = format
            self.left_selected_bracket.cursor = cursor

            cursor.setPosition(next)
            cursor.movePosition(QTextCursor.NextCharacter,
                                QTextCursor.KeepAnchor)

            format.setBackground(QColor('white'))
            self.right_selected_bracket.format = format
            self.right_selected_bracket.cursor = cursor
    """
    """
    def paintEvent(self, event):
        highlighted_line = QTextEdit.ExtraSelection()
        highlighted_line.format.setBackground(lineHighlightColor)
        highlighted_line.format.setProperty(QTextFormat
                                            .FullWidthSelection,
                                                 QVariant(True))
        highlighted_line.cursor = self.editor.textCursor()
        highlighted_line.cursor.clearSelection()
        self.editor.setExtraSelections([highlighted_line,
                                        self.left_selected_bracket,
                                      self.right_selected_bracket])
    """
    """
    def document(self):
        return self.editor.document

    def setLineWrapMode(self, mode):
        self.e_sql.setLineWrapMode(mode)

    def setPlainText(self, *args, **kwargs):
        self.editor.setPlainText(*args, **kwargs)
    """
    def replaceAll(self):        
        oldtext = self.e_sql.document().toPlainText()
        newtext = oldtext.replace(self.findfield.text(), self.replacefield.text())
        self.e_sql.setPlainText(newtext)
        self.v_testo_modificato = True        

    def replaceOne(self):        
        oldtext = self.e_sql.document().toPlainText()
        newtext = oldtext.replace(self.findfield.text(), self.replacefield.text(), 1)
        self.e_sql.setPlainText(newtext)
        self.v_testo_modificato = True                

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":       
    app = QtWidgets.QApplication([])    
    application = oracle_my_sql_class()     
    application.show()
    sys.exit(app.exec())    