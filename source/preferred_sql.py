# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt6
 Data..........: 23/02/2024
 Descrizione...: Gestione degli SQL preferiti
"""
#Librerie sistema
import sys
import datetime
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from PyQt6.QtCore import *
from preferred_sql_ui import Ui_preferred_sql_window
# Libreria sqlite
import sqlite3
# Librerie utilità
from utilita import message_question_yes_no_cancel, message_info
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class preferred_sql_class(QMainWindow, Ui_preferred_sql_window):
    """
        Permette di visualizzare il contenuto della tabella SQL_PREFERRED che contiene tutte le istruzioni SQL preferite
        p_nome_db --> contiene il nome del DB SQLite con l'intera pathname    
    """
    def __init__(self, p_nome_db, p_debug):
        
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
                                              UNIQUE (NOME))''')
        self.v_conn.commit()

        # creo la matrice ombra che replica la tabella da gestire con le seguenti colonne in più
        # 0) tipo di operazione INS=Insert, UPD=Update, DEL=Delete
        # 1) posizione riga a video!               
        self.matrice = []

        # se richiesto --> attivo il bottone di debug che fa le print della struttura
        if not p_debug:
            self.b_debug.setVisible(False)

        # richiamo la procedura di caricamento
        self.slot_start()

         # imposto il focus sul campo di ricerca
        self.e_where_cond.setFocus()

    def closeEvent(self, event):
        """
           alla chiusura controlla se ci sono delle modifiche in sospeso
        """
        if len(self.matrice) != 0:
            v_ok =message_question_yes_no_cancel('Save the records?') 
            if v_ok == 'Yes':
                self.slot_save()
            elif v_ok == 'No':        
                self.close()
            else:
                event.ignore()

    def slot_start(self):
        """
           carico a video la tabella
        """          
        # attivo il flag che indica che siamo in fase di carimento dei dati
        self.loading = True
        # pulisco la tabella ombra
        self.matrice.clear()

        # controllo se indicata la where
        if self.e_where_cond.text() != '':
            v_where = " where NOME || SQL || DATA like '%" + self.e_where_cond.text().upper() + "%'"
        else:
            v_where = ''

        # eseguo la query
        self.v_curs.execute("SELECT ROWID, NOME as NAME, SQL as SQL, DATA as DATE FROM SQL_PREFERRED"+v_where)            

        # pulisco graficamente la tabella
        self.o_tabella.clear()
        # creo una tabella con due colonne
        self.o_tabella.setColumnCount(3)
        # titoli delle colonne
        self.o_tabella.setHorizontalHeaderLabels(['ROWID','NAME','SQL'])                   
        # la colonna con l'id è nascosta
        self.o_tabella.setColumnHidden(0, True)
        # imposto larghezza delle colonne
        #self.o_tabella.setColumnWidth(0, 100)        
        self.o_tabella.setColumnWidth(1, 130)
        self.o_tabella.setColumnWidth(2, 480)                
        v_rig = 1                
        for record in self.v_curs.fetchall():                                    
            self.o_tabella.setRowCount(v_rig)             
            self.o_tabella.setItem(v_rig-1,0,QTableWidgetItem(str(record[0])))       
            self.o_tabella.setItem(v_rig-1,1,QTableWidgetItem(record[1]))       
            self.o_tabella.setItem(v_rig-1,2,QTableWidgetItem(record[2]))                                           
            # se il testo sql contiene dei ritorni a capo, allora alzo l'altezza della riga...
            if record[2].find('\n') != -1 or record[2].find('\r') != -1:
                self.o_tabella.setRowHeight(v_rig-1, 75)
            v_rig += 1
        #self.o_tabella.resizeColumnsToContents()

        # fine caricamento dati
        self.loading = False

    def slot_cell_changed(self,x,y):
        """
           controllo la cella modificata
        """               
        #print(str(x)+','+str(y))       
        if not self.loading:
            v_row = x
            v_col = y + 2 
            v_found = False
            # controllo se la cella indicata è cambiata rispetto alla cella in tabella ombra        
            for v_index in range(0,len(self.matrice)):
                v_riga = self.matrice[v_index]       
                if v_riga[1] == v_row and v_riga[0] != 'DEL':                                                        
                    v_found = True
                    # se cella cambiata allora la aggiorno
                    if v_riga[v_col] != self.o_tabella.item(x,y).text():
                        self.matrice[v_index][v_col]=self.o_tabella.item(x,y).text()                                            
                    break
            # se non ho trovato la cella allora sono in aggiornamento di un dato 
            if not v_found:
                # creo elemento in tabella ombra
                self.matrice.append(['UPD',v_row,self.o_tabella.item(x,0).text(),self.o_tabella.item(x,1).text(),self.o_tabella.item(x,2).text()])    

    def slot_insert_row(self):
        """
           creo nuova riga
        """               
        v_new_row = self.o_tabella.rowCount()+1
        self.o_tabella.setRowCount(v_new_row)                
        # mi posiziono sulla cella
        self.o_tabella.setCurrentCell(v_new_row-1,0)
        # creo elemento in tabella ombra
        self.matrice.append(['INS',v_new_row-1,'','',''])

    def slot_delete_row(self):
        """
           cancello la riga selezionata
        """                 
        v_row = self.o_tabella.currentIndex().row()
        v_found = False
        # ricerco la riga nella tabella ombra e la segno come da cancellare
        for v_index in range(0,len(self.matrice)):
            v_riga = self.matrice[v_index]
            if v_riga[1] == v_row:
                self.matrice[v_index][0]='DEL'     
                v_found = True
        
        # se non ho trovato in tabella ombra allor inserisco la richiesta di cancellazione
        if not v_found:
            # creo elemento in tabella ombra
            self.matrice.append(['DEL',v_row,self.o_tabella.item(v_row,0).text(),self.o_tabella.item(v_row,1).text(),self.o_tabella.item(v_row,2).text()])    

        # elimino la riga a video
        self.o_tabella.removeRow(v_row)
    
    def slot_debug(self):
        """
           stampa il contenuto della tabella ombra che di fatto contiene 
           il riepilogo di tutte le operazioni che vanno svolte in tabella
        """  
        print(self.matrice)

    def slot_save(self):
        """
           salvataggio dei dati. Viene letta la tabella ombra che è in forma di matrice e viene
           sincronizzata con la tabella fisica. La chiave è la prima colonna!                      
        """      
        try:                                               
            v_count = 0
            for v_riga in self.matrice:
                if v_riga[0] == 'INS':
                    v_count += 1
                    self.v_curs.execute("INSERT INTO SQL_PREFERRED (NOME, SQL, DATA) VALUES (?,?,?)",(v_riga[3], v_riga[4], datetime.datetime.now()))
                elif v_riga[0] == 'DEL':
                    v_count += 1                
                    self.v_curs.execute("DELETE FROM SQL_PREFERRED WHERE ROWID=?",(v_riga[2],))
                elif v_riga[0] == 'UPD':
                    v_count += 1
                    self.v_curs.execute("UPDATE SQL_PREFERRED SET NOME=?, SQL=?, DATA=? WHERE ROWID=?", (v_riga[3], v_riga[4], datetime.datetime.now(),v_riga[2]))
            # committo        
            self.v_conn.commit()            
            if v_count > 0:
                message_info('Processed ' + str(v_count) + ' record!')
            else:
                message_info('Nothing to save!')
            # eseguo il refresh e quindi la pulizia della tabella ombra
            self.slot_start()
        
        except sqlite3.IntegrityError as e:
            message_info('Unique key error! Check NAME column!')
            # rollback di tutta la transazione
            self.v_conn.rollback()  
                        
# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = preferred_sql_class('C:\\Users\\MValaguz\\AppData\\Local\\MSql\\MSql.db',True) 
    application.show()
    sys.exit(app.exec())      