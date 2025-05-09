#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 02/11/2023
#  Descrizione...: Visualizza l'history dei comandi eseguiti in MSql

#Librerie sistema
import sys
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt6.QtCore import *
from history_ui import Ui_history_window
from utilita import message_error, message_question_yes_no, message_info
from utilita_database import purge_sql_history
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class history_class(QMainWindow, Ui_history_window):
    """
        Permette di visualizzare il contenuto della tabella history che contiene tutte le istruzioni di MSql
        p_nome_db --> contiene il nome del DB SQLite con l'intera pathname    
    """
    def __init__(self, p_nome_db):
        
        # incapsulo la classe grafica da qtdesigner
        super(history_class, self).__init__()        
        self.setupUi(self)    
        self.nome_db = p_nome_db
        self.v_sqlite_conn = None

        # richiamo la procedura di visualizzazione 
        self.slot_start()

        # imposto il focus sul campo di ricerca
        self.e_where_cond.setFocus()

    def slot_start(self):
        """
           carico a video la tabella
        """                             
        # apro il db attraverso gli strumenti librerie QT        
        self.v_sqlite_conn = QSqlDatabase.addDatabase("QSQLITE")
        self.v_sqlite_conn.setDatabaseName(self.nome_db)
        if not self.v_sqlite_conn.open():
            message_error(QCoreApplication.translate('history','Error to open database'))
            return 'ko'
     
        # controllo se indicata la where
        if self.e_where_cond.text() != '':
            v_where = " where strftime('%d/%m/%Y %H:%S',ORARIO) || UPPER(ISTRUZIONE) || ROUND(EXEC_TIME,2) like '%" + self.e_where_cond.text().upper() + "%'"
        else:
            v_where = ''

        # creo un modello di dati su query (per questioni di velocità dall'istruzione vengono prese solo i primi 1000 caratteri)
        v_modello = QSqlQueryModel()
        v_modello.setQuery("select strftime('%d/%m/%Y %H:%S',ORARIO) TIME, UPPER(SUBSTR(ISTRUZIONE,1,1000)) 'INSTRUCTION (Only first 1000 char)', ROUND(EXEC_TIME,2) 'SEC.TIME', ID from SQL_HISTORY " + v_where + " order by ORARIO desc"        )        

        # imposto l'oggetto di visualizzazione con il modello 
        self.o_lst1.setModel(v_modello)
        # larghezza delle colonne automatica
        #self.o_lst1.resizeColumnsToContents()        
        # larghezza delle colonne fissa
        self.o_lst1.setColumnWidth(0, 120)
        self.o_lst1.setColumnWidth(1, 440)        
        self.o_lst1.setColumnWidth(2, 70)                        
        self.o_lst1.setColumnWidth(3, 0)                                
        # intestazioni automatiche in base alla query
        v_horizontal_header = self.o_lst1.horizontalHeader()
        v_horizontal_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        # altezza della riga (sotto un certo numero non va) in base all'altezza del font
        v_vertical_header = self.o_lst1.verticalHeader()
        v_vertical_header.setDefaultSectionSize(8)   
        self.o_lst1.show()
        
    def closeEvent(self, event):
        """
           chiusura della connessione al db sqlite
        """                
        self.v_sqlite_conn.close()        

    def slot_purge(self):
        """
           elimino la tabella che contiene l'history
        """
        if message_question_yes_no(QCoreApplication.translate('history','Are you sure you want to delete your history?')) == 'Yes':
            purge_sql_history(self.nome_db)
            message_info(QCoreApplication.translate('history','History deleted!'))
            self.slot_start()

    def return_instruction(self, p_id):
        """
           dato un ID di riga, restituisce la rispettiva istruzione SQL
        """
        query = QSqlQuery()
        # Esecuzione della query per leggere il contenuto desiderato
        query.prepare("SELECT ISTRUZIONE from SQL_HISTORY WHERE ID = :id")
        query.bindValue(":id", p_id)

        if query.exec():
            while query.next():                
                # restituisco il valore della colonna
                return query.value(0)                  
        
        # altrimenti esco senza nulla        
        return ''
    
# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = history_class('C:\\Users\\MValaguz\\AppData\\Local\\MSql\\MSql.db') 
    application.show()    
    sys.exit(app.exec())      