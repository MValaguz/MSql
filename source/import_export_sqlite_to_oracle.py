#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 23/01/2023
#  Descrizione...: Copia i dati di una tabella SQLite all'interno di una Oracle

#Librerie sistema
import sys
import os
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from import_export_sqlite_to_oracle_ui import Ui_import_export_window
#Librerie di data base
import sqlite3
import oracledb
import oracle_my_lib
import utilita_database
#Import dei moduli interni
from utilita import message_error, message_info
from copy_from_oracle_to_sqlite import copy_from_oracle_to_sqlite
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class import_export_class(QMainWindow, Ui_import_export_window):
    """
        Copia i dati di una tabella SQLite all'interno di una Oracle
    """
    def __init__(self, p_user, p_password, p_server, p_work_dir):
        
        # incapsulo la classe grafica da qtdesigner
        super(import_export_class, self).__init__()        
        self.setupUi(self)    

        # salvo i parametri ricevuti in input, dentro l'oggetto
        self.user = p_user
        self.password = p_password
        self.server = p_server
        self.work_dir = p_work_dir

        # carica elenco delle tabelle oracle                
        v_elenco_tabelle_oracle = utilita_database.estrae_elenco_tabelle_oracle( '1', self.user, self.password, self.server )
        # carica la combobox tabelle di oracle
        v_valore_corrente = self.e_table_name.currentText()
        self.e_table_name.clear()                
        self.e_table_name.addItems( v_elenco_tabelle_oracle )            
        self.e_table_name.setCurrentText( v_valore_corrente )            

    def slot_elenco_tabelle_sqlite(self):
        """
           carica elenco delle tabelle sqlite
        """
        if self.e_sqlite_db.displayText() != '':
            v_elenco_tabelle = utilita_database.estrae_elenco_tabelle_sqlite('1', self.e_sqlite_db.displayText() )
            # carica la combobox tabelle di oracle
            v_valore_corrente = self.e_sqlite_table.currentText()
            self.e_sqlite_table.clear()                
            self.e_sqlite_table.addItems( v_elenco_tabelle )            
            self.e_sqlite_table.setCurrentText( v_valore_corrente )            
    
    def slot_select_sqlite_db(self):
        """
           apre la dialog box per selezionare un file contenente un DataBase SQLite
        """
        fileName = QFileDialog.getOpenFileName(self, "Choose a file")                  
        if fileName[0] != "":
            self.e_sqlite_db.setText( fileName[0] )        

    def slot_start(self):
        """
           esegue l'operazione 
        """                  
        if self.e_sqlite_db.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite DB'))            
            return 'ko'
        if self.e_sqlite_table.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite Table'))            
            return 'ko'
        if self.e_sqlite_db.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite DB destination'))
            return 'ko'
        if self.e_table_name.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Table Name'))
            return 'ko'

         # indico tramite il cursore del mouse che è in corso un'elaborazione
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))       

        # Richiamo copia della tabella                  
        v_ok = sqlite_to_oracle_class(self.e_sqlite_table.currentText(),
                                      self.e_sqlite_db.displayText(),
                                      self.work_dir,                                             
                                      self.user,
                                      self.password,
                                      self.server,
                                      self.e_table_name.currentText(),
                                      self.e_where_cond.toPlainText()                                         
                                     )       

        # riporto a "normale" l'icona del mouse
        QApplication.restoreOverrideCursor()        
        
        if v_ok.message_info != '':
            message_info(v_ok.message_info)                                    
        
        if v_ok.message_error != '':
            message_error(v_ok.message_error)                

class sqlite_to_oracle_class():
    """
        Esegue la copia di una tabella SQLite dentro una tabella Oracle che NON deve esistere
        Va indicato attraverso l'instanziazione della classe:
            p_table_name     = Nome della tabella SQLite da copiare                        
            p_sqlite_db_name = Nome del DB SQLite, se non esiste verrà creato automaticamente
            p_blob_pathname  = Pathname dove verranno pescate le cartelle contenenti i blob della tabella copiata
            p_user_db        = Nome utente del DB Oracle
            p_password_db    = Password utente del DB Oracle
            p_dsn_db         = Indirizzo IP del DB Oracle o dsn
            p_oracle_table   = Nome della tabella Oracle di destinazione (NON deve esistere)             
            p_where          = Condizione where

        L'instanziazione comporta l'automatica esecuzione dell'importazione del file 
        dentro la tabella oracle.
        Al termine è necessario controllare i valori degli attributi message_error o message_info
        per capire se ci sono stati errori o se tutto ok ma con restrizioni
    """
    def __init__(self,                  
                 p_table_name,                 
                 p_sqlite_db_name,
                 p_blob_pathname,
                 p_user_db,
                 p_password_db,
                 p_dsn_db,
                 p_oracle_table,
                 p_where):

        #Variabili che contengono stato esecuzione della procedura
        self.message_error = ''
        self.message_info = ''
                        
        #Avvio la copia della tabella        
        if self.copia_tabella(p_table_name, p_sqlite_db_name, p_blob_pathname, p_user_db, p_password_db, p_dsn_db, p_oracle_table, p_where) == 'ok':
            #Messaggio finale            
            self.message_info = QCoreApplication.translate('import_export','Table copy completed!')
        
        return None                

    def copia_tabella(self,
                      v_table_name,                      
                      v_sqlite_db_name,
                      v_blob_pathname,
                      v_user_db,
                      v_password_db,
                      v_dsn_db,
                      v_oracle_table,
                      v_where): 
                        
        #Controllo se esiste una directory con il nome della tabella e al cui interno sia presente il file di definizione dei blob    
        #Eventualmente preparo una lista con le posizioni dei campi di blob che userò solo dopo aver fatto le insert
        v_posizioni_blob = []
        if os.path.isfile(v_blob_pathname + v_table_name + '\\blob_fields_position.ini'):            
            v_file_blob = open(v_blob_pathname + v_table_name + '\\blob_fields_position.ini')            
            v_linea = v_file_blob.readline()
            v_linea = v_linea.replace(' ','')
            v_linea = v_linea.replace('[','')
            v_linea = v_linea.replace(']','')
            v_posizioni_blob = v_linea.split(',')            
            v_file_blob.close()                
                      
        #Collegamento a Oracle
        try:
            oracle_my_lib.inizializzo_client()  
            v_oracle_db = oracledb.connect(user=v_user_db, password=v_password_db, dsn=v_dsn_db)        
        except:
            self.message_error = QCoreApplication.translate('import_export',"Connecting problems to Oracle DB!")
            #esco
            return 'ko'            
        v_oracle_cursor = v_oracle_db.cursor()    
        #Apre il DB sqlite    
        v_sqlite_conn = sqlite3.connect(database=v_sqlite_db_name)
        #Indico al db di funzionare in modalità stringa
        v_sqlite_conn.text_factory = str
        v_sqlite_cur = v_sqlite_conn.cursor()
        
        #Conto i record della tabella Oracle (se non esiste --> errore)
        try:
            v_oracle_cursor.execute("SELECT COUNT(*) FROM ALL_TABLES WHERE TABLE_NAME='" + v_oracle_table + "'")                        
        except:
            self.message_error = QCoreApplication.translate('import_export',"Table in Oracle DB not exists!")
            #esco
            return 'ko'
        #Se la tabella esiste errore ed esco
        if v_oracle_cursor.fetchone()[0] > 0:
            self.message_error = QCoreApplication.translate('import_export',"Table in Oracle DB already exist!")
            #esco
            return 'ko'
            
        #Conto i record della tabella di partenza        
        query = 'SELECT COUNT(*) FROM ' + v_table_name                
        #Aggiungo la where (solo se caricata)        
        try:    
            v_sqlite_cur.execute(query)
        except:
            self.message_error = QCoreApplication.translate('import_export',"SQLite table do not exists!")
            #esco
            return 'ko'
                
        v_total_rows = 0
        for row in v_sqlite_cur:                  
            v_total_rows = row[0]
    
        #Chiedo a db SQLite di restituirmi la struttura della tabella di partenza
        query = utilita_database.estrae_struttura_tabella_sqlite('c', v_sqlite_cur, v_table_name)                             
        #Sostituisco il nome della tabella SQLite con la tabella di arrivo che deve essere creata in Oracle
        query = query.replace(v_table_name,v_oracle_table)        
        #Eseguo la creazione della tabella in DB Oracle
        v_oracle_cursor.execute(query)
        
        ##
        #Inizio copia dei dati
        ##
        
        #Estraggo da db SQLite una struttura "select ..." dalla tabella di partenza
        query = utilita_database.estrae_struttura_tabella_sqlite('s', v_sqlite_cur, v_table_name)                         
        #Se è stata definita una where, la aggiungo
        if v_where != '':
            query += ' WHERE ' + v_where
        #Estraggo da db SQLite una struttura "insert into nome_tabella(campo1, campo2...) values(:1,:2,....)" dalla tabella di partenza
        v_insert_base = utilita_database.estrae_struttura_tabella_sqlite('h', v_sqlite_cur, v_table_name) 
                
        #Nell'istruzione insert appena ricavata, sostituisco il nome della tabella di partenza con la tabella di arrivo
        v_insert_base = v_insert_base.replace(v_table_name,v_oracle_table)        
        
        #Eseguo la query
        v_sqlite_cur.execute(query)                
        #Leggo tutte le righe
        for row in v_sqlite_cur:                              
            #Azzero lista che conterrà tutti campi della riga
            v_insert_row = []            
            #Leggo tutte le colonne-campi di una singola riga
            for v_i in range(0,len(row)):                                
                v_blob_caricato = False
                #Se la colonna appartiene a un blob, carico il file corrispondente all'indice
                if len(v_posizioni_blob) > 0:                
                    for v_j in range(0,len(v_posizioni_blob)):
                        if int(v_posizioni_blob[v_j]) == (v_i+1):                            
                            #apro il file
                            v_file_blob = open(v_blob_pathname + v_table_name + '\\' + str(row[v_i]) + '.zzz', 'rb')                                                                                            
                            #leggo il file indicando che deve finire in un blob formato oracle
                            v_blob_value = v_oracle_cursor.var(oracledb.BLOB)                            
                            v_blob_value.setvalue(0,v_file_blob.read())                            
                            #aggiungo il file alla lista delle colonne
                            v_insert_row.append(v_blob_value)                            
                            #elimino il blob come var e chiudo il file
                            del v_blob_value                            
                            v_file_blob.close()                
                            v_blob_caricato = True
                #Carico la colonna normale (tutti i tipi di campi diversi da blob)
                if not v_blob_caricato:
                    v_insert_row.append(row[v_i])                
            
            #Apro di nuovo il cursore (si sono verificati problemi di memoria)
            v_oracle_cursor = v_oracle_db.cursor()    
            #Eseguo la insert dove v_insert_base contiene la parte di testo INSERT INTO ...., mentre v_insert_row contiene i dati dei campi
            v_oracle_cursor.execute(v_insert_base,v_insert_row)                                    
            #Committo
            v_oracle_db.commit()                                
            #Chiudo il cursore 
            v_oracle_cursor.close()    
                
        #chiusura dei db
        v_sqlite_conn.close()                    
        v_oracle_db.close()        
        return 'ok'                                                      

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = import_export_class('SMILE','SMILE','BACKUP_815','C:\\TEMP') 
    application.show()
    sys.exit(app.exec())      