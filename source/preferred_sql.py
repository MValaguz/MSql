# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11
 Data..........: 23/02/2024
 Descrizione...: Gestione degli SQL preferiti
"""
#Librerie sistema
import sys
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *
from PyQt5.QtCore import *
from preferred_sql_ui import Ui_preferred_sql_window
# Libreria sqlite
import sqlite3
# Librerie utilità
from utilita import message_error, message_question_yes_no, message_info

class preferred_sql_class(QMainWindow, Ui_preferred_sql_window):
    """
        Permette di visualizzare il contenuto della tabella SQL_PREFERRED che contiene tutte le istruzioni SQL preferite
        p_nome_db --> contiene il nome del DB SQLite con l'intera pathname    
    """
    def __init__(self, p_nome_db):
        
        # incapsulo la classe grafica da qtdesigner
        super(preferred_sql_class, self).__init__()        
        self.setupUi(self)    
        self.nome_db = p_nome_db
        self.v_sqlite_conn = None

        # se necessario creo la tabella SQL_PREFERRED
        self.v_conn = sqlite3.connect(database=self.nome_db)
        self.v_curs = self.v_conn.cursor()
        self.v_curs.execute('''CREATE TABLE IF NOT EXISTS 
                               SQL_PREFERRED (NOME TEXT NOT NULL, 
                                              SQL  TEXT NOT NULL, 
                                              DATA DATETIME NOT NULL,
                                              PRIMARY KEY(NOME))''')
        self.v_conn.commit()

        # richiamo la procedura di caricamento
        self.slot_start()

    def slot_start(self):
        """
           carico a video la tabella
        """                             
        # controllo se indicata la where
        if self.e_where_cond.toPlainText() != '':
            v_where = ' where ' + self.e_where_cond.toPlainText()
        else:
            v_where = ''

        # eseguo la query
        self.v_curs.execute("select NOME as NAME, SQL as SQL, DATA as DATE from SQL_PREFERRED"+v_where)            

        # carico la tabella a video
        self.o_tabella.setColumnCount(3)
        self.o_tabella.setHorizontalHeaderLabels(['Name','Sql','Date'])                   
        v_rig = 1                
        for record in self.v_curs.fetchall():                                    
            self.o_tabella.setRowCount(v_rig) 
            self.o_tabella.setItem(v_rig-1,0,QTableWidgetItem(record[0]))       
            self.o_tabella.setItem(v_rig-1,1,QTableWidgetItem(record[1]))                               
            self.o_tabella.setItem(v_rig-1,2,QTableWidgetItem(record[2]))                                           
            v_rig += 1
        self.o_tabella.resizeColumnsToContents()

    def slot_insert_row(self):
        """
           creo nuova riga
        """               
        self.o_tabella.setRowCount(self.o_tabella.rowCount()+1)

    def slot_delete_row(self):
        """
           cancello la riga selezionata
        """                            
        self.o_tabella.removeRow(self.o_tabella.currentRow())

    def slot_cell_changed(self, x, y):
        """
           controllo la cella che è stata modificata
        """                            
        print(str(x) + str(y))

    def slot_save(self):
        """
           salva le modifiche
        """                             
        pass
                          
# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = preferred_sql_class('C:\MSql\MSql.db') 
    application.show()
    sys.exit(app.exec())      