#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 20/01/2023
#  Descrizione...: Copia i dati di una tabella Oracle all'interno di un DB-SQLite

#Librerie sistema
import os
import sys
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from qtdesigner.import_export_oracle_to_sqlite_ui import Ui_import_export_window
#Librerie di data base
import utilita_database
#Import dei moduli interni
from utilita import message_error
from copy_from_oracle_to_sqlite import copy_from_oracle_to_sqlite
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

class import_export_class(QMainWindow, Ui_import_export_window):
    """
        Copia i dati di una tabella Oracle all'interno di un DB-SQLite
    """
    def __init__(self, p_user, p_password, p_server, p_work_dir):
        
        # incapsulo la classe grafica da qtdesigner
        super(import_export_class, self).__init__()        
        self.setupUi(self)    

        # salvo i parametri ricevuti in input dentro l'oggetto
        self.user = p_user
        self.password = p_password
        self.server = p_server
        self.work_dir = p_work_dir

        # carica elenco delle tabelle oracle
        v_elenco_tabelle_oracle = utilita_database.estrae_elenco_tabelle_oracle( '1', self.user, self.password, self.server)
        # carica la combobox tabelle di oracle
        v_valore_corrente = self.e_table_name.currentText()
        self.e_table_name.clear()                
        self.e_table_name.addItems( v_elenco_tabelle_oracle )            
        self.e_table_name.setCurrentText( v_valore_corrente )            
    
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
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite DB destination'))
            return 'ko'
        if self.e_table_name.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Table Name'))
            return 'ko'

        # Richiamo copia della tabella        
        app = copy_from_oracle_to_sqlite(self.user,
                                         self.password,
                                         self.server,
                                         self.e_table_name.currentText(),
                                         self.e_where_cond.toPlainText(), 
                                         self.e_sqlite_db.displayText(),
                                         self.work_dir,
                                         False)                

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = import_export_class('SMILE','SMILE','BACKUP_815', 'C:\\IMPORT-EXPORT') 
    application.show()
    sys.exit(app.exec())      