#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 02/11/2023
#  Descrizione...: Visualizza l'history dei comandi eseguiti in MSql

#Librerie sistema
import os
import sys
#Librerie grafiche
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt6.QtCore import *
from qtdesigner.history_ui import Ui_history_window
from utilita import message_error, message_question_yes_no, message_info
from utilita_database import purge_sql_history
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

class PurgeDateDialog(QDialog):
    """
       Visualizza una finestra di dialogo per selezionare un intervallo di date per la cancellazione della cronologia.
    """
    def __init__(self, min_date: QDate, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Purge history")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # --- Date ---
        form = QFormLayout()

        self.d_start = QDateEdit()
        self.d_start.setCalendarPopup(True)
        self.d_start.setDate(min_date)

        self.d_end = QDateEdit()
        self.d_end.setCalendarPopup(True)
        self.d_end.setDate(QDate.currentDate())

        form.addRow("Start date:", self.d_start)
        form.addRow("End date:", self.d_end)

        layout.addLayout(form)

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_dates(self):
        return self.d_start.date(), self.d_end.date()
    
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
        self.e_where_cond_instruction.setFocus()

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
        v_where = ''
        if self.e_where_cond_time.text() != '':
            v_where = " strftime('%d/%m/%Y %H:%M',ORARIO) like '%" + self.e_where_cond_time.text().upper() + "%'"
        if self.e_where_cond_instruction.text() != '':
            if v_where != '':
                v_where = v_where + " AND "
            v_where = v_where + " UPPER(ISTRUZIONE) like '%" + self.e_where_cond_instruction.text().upper() + "%'"
        if self.e_where_cond_connection.text() != '':
            if v_where != '':
                v_where = v_where + " AND "
            v_where = v_where + " UPPER(TIPO) like '%" + self.e_where_cond_connection.text().upper() + "%'"        
        if v_where != '':
            v_where = ' WHERE ' + v_where

        # creo un modello di dati su query (per questioni di velocità dall'istruzione vengono prese solo i primi 1000 caratteri)        
        v_modello = QSqlQueryModel()
        v_modello.setQuery("select strftime('%d/%m/%Y %H:%M',ORARIO) TIME, UPPER(SUBSTR(ISTRUZIONE,1,1000)) 'INSTRUCTION (Only first 1000 char)', ROUND(EXEC_TIME,2) 'SEC.TIME', TIPO AS CONNECTION, ID from SQL_HISTORY " + v_where + " order by ORARIO desc"        )        

        # imposto l'oggetto di visualizzazione con il modello 
        self.o_lst1.setModel(v_modello)
        # larghezza delle colonne automatica        
        # larghezza delle colonne fissa
        self.o_lst1.setColumnWidth(0, 120)
        self.o_lst1.setColumnWidth(1, 440)        
        self.o_lst1.setColumnWidth(2, 70)                        
        self.o_lst1.setColumnWidth(3, 150)                                
        self.o_lst1.setColumnWidth(4, 0)                                
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
            Pulizia della tabella da data a data
        """            
        # Ricavo la data minima presente nella tabella
        query = QSqlQuery()
        query.exec("SELECT MIN(date(ORARIO)) FROM SQL_HISTORY")

        min_date = QDate.currentDate().addYears(-10)
        if query.next() and query.value(0):
            min_date = QDate.fromString(query.value(0), "yyyy-MM-dd")

        # Visualizzo la finestra di dialogo per la selezione delle date
        dlg = PurgeDateDialog(min_date, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        d_start, d_end = dlg.get_dates()

        # Conferma dell'operazione
        if message_question_yes_no(QCoreApplication.translate('history',f"Delete history from {d_start.toString('dd/MM/yyyy')} " f"to {d_end.toString('dd/MM/yyyy')}?")) != 'Yes':
            return

        # Eseguo la pulizia della tabella (prima però chiudo il db)
        self.v_sqlite_conn.close()        
        purge_sql_history(self.nome_db, d_start.toString("yyyy-MM-dd"), d_end.toString("yyyy-MM-dd"))        

        # Avviso l'utente
        message_info(QCoreApplication.translate('history', 'History purged!'))
        
        # ricarico la tabella a video
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