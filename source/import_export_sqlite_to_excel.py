#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 23/01/2023
#  Descrizione...: Copia i dati di una tabella SQLite in un file excel

#Librerie sistema
import sys
import os
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from import_export_sqlite_to_excel_ui import Ui_import_export_window
#Librerie di data base
import sqlite3 
import utilita_database
from utilita import message_error,message_info,message_question_yes_no
from copy_from_oracle_to_sqlite import copy_from_oracle_to_sqlite
#Libreria per export in excel
from xlsxwriter.workbook import Workbook
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class import_export_class(QMainWindow, Ui_import_export_window):
    """
        Copia i dati di una tabella Oracle all'interno di un DB-SQLite
    """
    def __init__(self):
        
        # incapsulo la classe grafica da qtdesigner
        super(import_export_class, self).__init__()        
        self.setupUi(self)    

    def slot_elenco_tabelle_sqlite(self):
        """
           carica elenco delle tabelle 
        """
        if self.e_sqlite_db.displayText() != '':
            v_elenco_tabelle = utilita_database.estrae_elenco_tabelle_sqlite( '1', self.e_sqlite_db.displayText() )
            # carica la combobox tabelle di oracle
            v_valore_corrente = self.e_table_name.currentText()
            self.e_table_name.clear()                
            self.e_table_name.addItems( v_elenco_tabelle )            
            self.e_table_name.setCurrentText( v_valore_corrente )            
    
    def slot_select_sqlite_db(self):
        """
           apre la dialog box per selezionare un file contenente un DataBase SQLite
        """
        fileName = QFileDialog.getOpenFileName(self, "Choose a file")                  
        if fileName[0] != "":
            self.e_sqlite_db.setText( fileName[0] )        
    
    def slot_select_excel_file(self):
        """
           apre la dialog box per selezionare un file excel
        """
        fileName = QFileDialog.getOpenFileName(self, "Choose a file","","Excel Files (*.xlsx);;All Files (*.*)")                  
        if fileName[0] != "":
            self.e_excel.setText( fileName[0] )        

    def slot_start(self):
        """
            copia una tabella sqlite dentro un file di excel
        """        
        if self.e_sqlite_db.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite DB'))            
            return 'ko'
        if self.e_table_name.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Table Name'))
            return 'ko'
        if self.e_excel.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Excel file name'))            
            return 'ko'
        # controllo se file esiste
        if os.path.isfile(self.e_excel.displayText()):
            if message_question_yes_no(QCoreApplication.translate('import_export',"Destination file already exists. Do you to replace it?")) == 'No':
                # esco dalla procedura perché utente ha deciso di non preseguire
                return 'ko'
                     
        # indico tramite il cursore del mouse che è in corso un'elaborazione
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))       
        
        # apre il DB sqlite (lo apro in modalità classica....non dovrei avere problemi con utf-8)
        v_sqlite_conn = sqlite3.connect(database=self.e_sqlite_db.displayText())
        v_sqlite_cur = v_sqlite_conn.cursor()        
                                
        # creazione del file excel
        workbook = Workbook(self.e_excel.displayText())
        worksheet = workbook.add_worksheet()

        # estraggo elenco dei campi
        v_struttura = utilita_database.estrae_struttura_tabella_sqlite('1',v_sqlite_cur,self.e_table_name.currentText())

        # carico elenco dei campi nella prima riga del foglio        
        pos = 0
        for i in v_struttura:
            worksheet.write(0, pos, i)
            pos += 1

        # carico tutte le altre righe della tabella                    
        if self.e_where_cond.toPlainText() != '':
            where = ' WHERE ' + self.e_where_cond.toPlainText()
        else:
            where = ''

        query = 'SELECT * FROM ' + self.e_table_name.currentText() + where
        v_sqlite_cur.execute(query)
        for i, row in enumerate(v_sqlite_cur):            
            for j,value in enumerate(row):
                worksheet.write(i+1, j, row[j])        
                
        # chiusura del file e del db
        workbook.close()
        v_sqlite_conn.close()                  

        # riporto a "normale" l'icona del mouse
        QApplication.restoreOverrideCursor()        
  
        # messaggio finale        
        message_info(QCoreApplication.translate('import_export','Table export completed!'))

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = import_export_class() 
    application.show()
    sys.exit(app.exec())      