#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 23/01/2023
#  Descrizione...: Permette di visualizzare il contenuto di una tabella presente in un database SQLite

#Librerie sistema
import os
import sys
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtSql import *
from qtdesigner.sqlite_viewer_ui import Ui_sqlite_viewer_window
#Librerie di data base
import utilita_database
#Import dei moduli interni
from utilita import message_error
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

class sqlite_viewer_class(QMainWindow, Ui_sqlite_viewer_window):
    """
        Permette di visualizzare il contenuto di una tabella presente in un database SQLite
    """
    def __init__(self):
        
        # incapsulo la classe grafica da qtdesigner
        super(sqlite_viewer_class, self).__init__()        
        self.setupUi(self)    

    def slot_elenco_tabelle_sqlite(self):
        """
           carica elenco delle tabelle presenti in db SQLite
        """
        if self.e_sqlite_db.displayText() != '':
            try:
                v_elenco_tabelle_sqlite = utilita_database.estrae_elenco_tabelle_sqlite('1',self.e_sqlite_db.displayText())            
            except:
                message_error(QCoreApplication.translate('import_export','Invalid SQLite DB!'))
                return 'ko'
            # carica la combobox tabelle
            v_valore_corrente = self.e_table_name.currentText()
            self.e_table_name.clear()                
            self.e_table_name.addItems( v_elenco_tabelle_sqlite )            
            self.e_table_name.setCurrentText( v_valore_corrente )            
    
    def slot_select_sqlite_db(self):
        """
           apre la dialog box per selezionare un file contenente un DataBase SQLite
        """
        fileName = QFileDialog.getOpenFileName(self, QCoreApplication.translate('import_export',"Choose a file"))                  
        if fileName[0] != "":
            self.e_sqlite_db.setText( fileName[0] )        

    def slot_start(self):
        """
           carico a video la tabella
        """          
        if self.e_sqlite_db.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a SQLite DB'))
            return 'ko'
        if self.e_table_name.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Table Name'))
            return 'ko'
        
        # indico tramite il cursore del mouse che è in corso un'elaborazione
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))       
                
        # utilizzo gli oggetti database delle librerie qt e apro il database
        v_sqlite_conn = QSqlDatabase.addDatabase("QSQLITE")
        v_sqlite_conn.setDatabaseName(self.e_sqlite_db.displayText())
        if not v_sqlite_conn.open():
            message_error(QCoreApplication.translate('import_export','Error to open database'))
            return 'ko'

        # controllo se indicata la where
        if self.e_where_cond.toPlainText() != '':
            v_where = ' where ' + self.e_where_cond.toPlainText()
        else:
            v_where = ''

        # creo un modello di dati su query
        v_modello = QSqlQueryModel()
        v_modello.setQuery('select * from '+ self.e_table_name.currentText() + v_where)

        # imposto l'oggetto di visualizzazione con il modello 
        self.o_lst1.setModel(v_modello)
        self.o_lst1.show()

        # riporto a "normale" l'icona del mouse
        QApplication.restoreOverrideCursor()        

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = sqlite_viewer_class() 
    application.show()
    sys.exit(app.exec())      