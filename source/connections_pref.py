#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11 con libreria pyqt6
#  Data..........: 23/10/2026
#  Descrizione...: Gestione delle connessioni-utenti MSql
 
#  Note..........: Il layout è stato creato utilizzando qtdesigner e il file connections_pref_ui.py è ricavato partendo da connections_pref_ui.ui 

#Librerie sistema
import sys
import os
import json
import subprocess
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Definizioni interfaccia
from qtdesigner.connections_pref_ui import Ui_connections_window
#Librerie aggiuntive interne
from utilita import message_info, message_question_yes_no, cripta_messaggio, decripta_messaggio, return_global_work_dir
from preferences import preferences_class
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))
#Cartella di lavoro
v_global_work_dir = return_global_work_dir()
       
class win_connections_class(QMainWindow, Ui_connections_window):
    """
        Gestione delle connessioni di MSql
    """                
    def __init__(self, p_nome_file_preferences, p_nome_file_connections):
        super(win_connections_class, self).__init__()        
        self.setupUi(self)

        # salvo nella classe i parametri ricevuti per usi successivi
        self.nome_file_preferences = p_nome_file_preferences
        self.nome_file_connections = p_nome_file_connections
        
        # creo l'oggetto preferenze che automaticamente carica il file o le preferenze di default
        self.preferences = preferences_class(self.nome_file_preferences, self.nome_file_connections)        
        # le preferenze caricate vengono riportate a video
        self.e_connection_mode.setCurrentIndex(self.preferences.connection_mode)
        self.e_oracleclient_path.setText(self.preferences.oracleclient_path)                

        ###
        # preparo elenco server        
        ###
        self.o_server.setColumnCount(7)
        self.o_server.setHorizontalHeaderLabels(['Server title (*)','TNS Name (*)','Color','','AutoConnection'+chr(10)+'at startup','Emphasis','CREATE'+chr(10)+'confirm'])           
        v_rig = 1                
        for record in self.preferences.elenco_server:                                    
            self.o_server.setRowCount(v_rig) 
            self.carico_riga_server(v_rig,record)

            # passo alla prossima riga
            v_rig += 1
        self.o_server.resizeColumnsToContents()
        self.o_server.setCurrentCell(0,0)

        ###
        # preparo elenco user        
        ###
        self.o_users.setColumnCount(7)
        self.o_users.setHorizontalHeaderLabels(['User title (*)','User name (*)','Password (*)','AutoConnection'+chr(10)+'at startup','As Proxy','As Schema','Mode'])   
        v_rig = 1                
        for record in self.preferences.elenco_user:                                    
            self.o_users.setRowCount(v_rig) 
            self.carico_riga_user(v_rig, record)

            # passo alla prossima riga
            v_rig += 1
        self.o_users.resizeColumnsToContents()
        self.o_users.setCurrentCell(0,0)

        # Attivo/disattivo la connection mode
        self.slot_e_connection_mode()
    
    def carico_riga_server(self, v_rig, record):
        """
           Carica una nuova riga nella tabella server
        """
        self.o_server.setItem(v_rig-1,0,QTableWidgetItem(record[0]))       
        self.o_server.setItem(v_rig-1,1,QTableWidgetItem(record[1]))                               
        self.o_server.setItem(v_rig-1,2,QTableWidgetItem(record[2]))                                           
        # come quarta colonna metto il pulsante per la scelta del colore
        v_color_button = QPushButton()            
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:color.png"), QIcon.Mode.Normal, QIcon.State.Off)
        v_color_button.setIcon(v_icon)
        v_color_button.clicked.connect(self.slot_set_color_server)
        self.o_server.setCellWidget(v_rig-1,3,v_color_button)                 
        # la quinta colonna è una check-box per la selezione del server di default
        # da notare come la checkbox viene inserita in un widget di layout in modo che si possa
        # attivare la centratura 
        v_checkbox = QCheckBox()          
        v_checkbox.setToolTip('When this flag is set, MSql automatically connects to this server at startup. Warning! Select only one preference!')
        v_widget = QWidget()      
        v_layout = QHBoxLayout(v_widget)
        v_layout.addWidget(v_checkbox)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.setContentsMargins(0,0,0,0)
        v_widget.setLayout(v_layout)
        try:
            if record[3] == '1':
                v_checkbox.setChecked(True)                                            
            else:
                v_checkbox.setChecked(False)                                                        
        except:
            v_checkbox.setChecked(False)                                                        
        self.o_server.setCellWidget(v_rig-1,4,v_widget)                                                      
        # la sesta colonna è una check-box per indicare che quando si è connessi a questo server deve essere attiva evidenziazione
        # da notare come la checkbox viene inserita in un widget di layout in modo che si possa
        # attivare la centratura 
        v_checkbox_e = QCheckBox()          
        v_checkbox_e.setToolTip('When this flag is set, the chosen color is also used for the data and results output sections.')
        v_widget_e = QWidget()      
        v_layout_e = QHBoxLayout(v_widget_e)
        v_layout_e.addWidget(v_checkbox_e)
        v_layout_e.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout_e.setContentsMargins(0,0,0,0)
        v_widget_e.setLayout(v_layout_e)
        try:
            if record[4] == '1':
                v_checkbox_e.setChecked(True)                                            
            else:
                v_checkbox_e.setChecked(False)                                                        
        except:
            v_checkbox_e.setChecked(False)                                                        
        self.o_server.setCellWidget(v_rig-1,5,v_widget_e)                                                      
        # la settima colonna è una check-box per indicare che quando si esegue un'istruzione di CREATE, prima di eseguirla viene richiesta una conferma
        # da notare come la checkbox viene inserita in un widget di layout in modo che si possa
        # attivare la centratura 
        v_checkbox_c = QCheckBox()          
        v_checkbox_c.setToolTip('When this flag is set, each CREATE statement requires confirmation.')
        v_widget_c = QWidget()      
        v_layout_c = QHBoxLayout(v_widget_c)
        v_layout_c.addWidget(v_checkbox_c)
        v_layout_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout_c.setContentsMargins(0,0,0,0)
        v_widget_c.setLayout(v_layout_c)
        try:
            if record[5] == '1':
                v_checkbox_c.setChecked(True)                                            
            else:
                v_checkbox_c.setChecked(False)                                                        
        except:
            v_checkbox_c.setChecked(False)                                                        
        self.o_server.setCellWidget(v_rig-1,6,v_widget_c)                                                      
    
    def carico_riga_user(self, v_rig, record):
        """
           Carica una nuova riga nella tabella user
        """
        self.o_users.setItem(v_rig-1,0,QTableWidgetItem(record[0]))       
        self.o_users.setItem(v_rig-1,1,QTableWidgetItem(record[1]))                               
        v_password = QLineEdit(record[2])
        v_password.setEchoMode(QLineEdit.EchoMode.Password) 
        self.o_users.setCellWidget(v_rig-1,2,v_password)                               
        # la quarta colonna è una check-box per la selezione dell'utente di default
        # da notare come la checkbox viene inserita in un widget di layout in modo che si possa
        # attivare la centratura 
        v_checkbox = QCheckBox() 
        v_checkbox.setToolTip('When this flag is set, MSql automatically connects with this user at startup. Warning! Select only one preference!')         
        v_widget = QWidget()      
        v_layout = QHBoxLayout(v_widget)
        v_layout.addWidget(v_checkbox)
        v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.setContentsMargins(0,0,0,0)
        v_widget.setLayout(v_layout)
        try:
            if record[3] == '1':
                v_checkbox.setChecked(True)                                            
            else:
                v_checkbox.setChecked(False)                                                        
        except:
            v_checkbox.setChecked(False)                                                        
        self.o_users.setCellWidget(v_rig-1,3,v_widget)                                                      
        # As proxy
        if len(record) > 4:
            self.o_users.setItem(v_rig-1,4,QTableWidgetItem(record[4]))                               
        else:
            self.o_users.setItem(v_rig-1,4,QTableWidgetItem())                               
        # Schema
        if len(record) > 5:
            self.o_users.setItem(v_rig-1,5,QTableWidgetItem(record[5]))                               
        else:
            self.o_users.setItem(v_rig-1,5,QTableWidgetItem())                               
        # Mode (normal, SYSDBA, SYSOPER)
        e_mode = QComboBox()        
        e_mode.addItems(["Normal", "SYSDBA", "SYSOPER"])        
        self.o_users.setCellWidget(v_rig-1,6,e_mode)                               
        if len(record) > 6:
            e_mode.setCurrentText(record[6])    
        else:
            e_mode.setCurrentText('Normal')    
    
    def slot_b_restore(self):
        """
           Ripristina tutte preferenze di default
        """
        self.preferences.restore_default_preferences(self.nome_file_preferences, self.nome_file_connections)
        # esco dal programma delle preferenze
        self.close()

    def slot_set_color_server(self):
        """
           Gestione della scelta dei colori sull'elenco dei server
        """
        # ottengo un oggetto index-qt della riga selezionata
        index = self.o_server.currentIndex()           
        # prendo la cella che contiene il colore in modo da aprire la selezione partendo dal colore corrente
        v_color_corrente = self.o_server.item( index.row(), 2).text()                        
        # apro la dialog color
        color = QColorDialog.getColor(QColor(v_color_corrente))                
        # imposto il colore
        if color.isValid():
            self.o_server.setItem( index.row(), 2, QTableWidgetItem(color.name()) )      

    def slot_e_connection_mode(self):
        """
           Gestione della modalità di editazione delle tabelle
        """
        if self.e_connection_mode.currentIndex() == 0:
           self.l_oracleclient_path.setVisible(False)
           self.e_oracleclient_path.setVisible(False)
           self.b_oracleclient_path.setVisible(False)
        else:         
           self.l_oracleclient_path.setVisible(True)
           self.e_oracleclient_path.setVisible(True)
           self.b_oracleclient_path.setVisible(True)
    
    def slot_b_oracleclient_path(self):
        """
           Scelta della dir di Oracle Client
        """
        dirName = QFileDialog.getExistingDirectory(self, "Choose Oracle Client directory")                  
        if dirName != "":
            self.e_oracleclient_path.setText( dirName )
    
    def slot_b_server_add(self):
        """
           Crea una riga vuota dove poter inserire informazioni connessioni al server
        """
        v_rig = self.o_server.rowCount()+1
        self.o_server.setRowCount(v_rig)
        self.carico_riga_server(v_rig, ['','','',0,0,0])

    def slot_b_server_remove(self):
        """
           Toglie la riga selezionata, da elenco server
        """
        self.o_server.removeRow(self.o_server.currentRow())

    def slot_b_user_add(self):
        """
           Crea una riga vuota dove poter inserire informazioni utente di connessione al server
        """
        v_rig = self.o_users.rowCount()+1
        self.o_users.setRowCount(v_rig)
        self.carico_riga_user(v_rig, ['','','',0,'','','Normal'])

    def slot_b_user_remove(self):
        """
           Toglie la riga selezionata, da elenco user
        """
        self.o_users.removeRow(self.o_users.currentRow())

    def slot_b_save(self):
        """
           Salvataggio di tutte le preferenze, sia generiche che di connessione
        """	
        ###
        # elenco dei server
        ###
        v_server = []
        for i in range(0,self.o_server.rowCount()):
            # controllo la checkbox del default (da notare come la checkbox è annegata in un oggetto di layout 
            # e quindi prima prendo l'oggetto che c'è annegato nella cella della tabella, poi in quell'oggetto
            # prendo tutti gli oggetti di tipo checkbox e poi prendo il primo checkbox (che è anche l'unico)
            # e da li prendo il suo stato!
            v_widget = self.o_server.cellWidget(i,4)
            v_checkbox = v_widget.findChildren(QCheckBox)
            if v_checkbox[0].isChecked():                
                v_default = '1'
            else:
                v_default = '0'
            # controllo la checkbox dell'evidenziare (da notare come la checkbox è annegata in un oggetto di layout 
            # e quindi prima prendo l'oggetto che c'è annegato nella cella della tabella, poi in quell'oggetto
            # prendo tutti gli oggetti di tipo checkbox e poi prendo il primo checkbox (che è anche l'unico)
            # e da li prendo il suo stato!
            v_widget = self.o_server.cellWidget(i,5)
            v_checkbox = v_widget.findChildren(QCheckBox)
            if v_checkbox[0].isChecked():                
                v_emphasis = '1'
            else:
                v_emphasis = '0'
            # controllo la checkbox della conferma su comandi di CREATE (da notare come la checkbox è annegata in un oggetto di layout 
            # e quindi prima prendo l'oggetto che c'è annegato nella cella della tabella, poi in quell'oggetto
            # prendo tutti gli oggetti di tipo checkbox e poi prendo il primo checkbox (che è anche l'unico)
            # e da li prendo il suo stato!
            v_widget = self.o_server.cellWidget(i,6)
            v_checkbox = v_widget.findChildren(QCheckBox)
            if v_checkbox[0].isChecked():                
                v_create_confirm = '1'
            else:
                v_create_confirm = '0'
            v_server.append( ( self.o_server.item(i,0).text(), self.o_server.item(i,1).text(), self.o_server.item(i,2).text(), v_default, v_emphasis, v_create_confirm ) )            

        ###
        # elenco degli users
        ###
        v_users = []
        for i in range(0,self.o_users.rowCount()):
            # controllo il campo della password che è annegato in un widget
            v_password = self.o_users.cellWidget(i,2)            
            # controllo la checkbox di autoconnection: da notare come la checkbox è annegata in un oggetto di layout 
            # e quindi prima prendo l'oggetto che c'è annegato nella cella della tabella, poi in quell'oggetto
            # prendo tutti gli oggetti di tipo checkbox e poi prendo il primo checkbox (che è anche l'unico)
            # e da li prendo il suo stato!
            v_widget = self.o_users.cellWidget(i,3)
            v_checkbox = v_widget.findChildren(QCheckBox)
            if v_checkbox[0].isChecked():                
                v_default = '1'
            else:
                v_default = '0'
            # dalla cella 6 prendo la combo box per prendere la modalità di connessione (normal, sysdba, sysoper)
            v_widget = self.o_users.cellWidget(i,6)            
            v_e_mode = v_widget.currentText()            
            v_users.append( ( self.o_users.item(i,0).text(), self.o_users.item(i,1).text() , v_password.text(), v_default, self.o_users.item(i,4).text(), self.o_users.item(i,5).text(), v_e_mode ) )            

        # scrivo secondo file con i dati user e server (separato in quanto nelle versione per GitHub non viene riportato!)
        v_json ={'server': v_server,
                 'users': v_users                 
                }

		# scrittura nel file dell'oggetto json (che viene criptato e notare come venga usata la funzione dumps con la s finale in quanto scrive stringhe)
        v_dump = cripta_messaggio(json.dumps(v_json))
        with open(self.nome_file_connections, 'wb') as outfile:
            outfile.write(v_dump)

		# scrivo file delle preferenze generiche 
        self.preferences.connection_mode = self.e_connection_mode.currentIndex()
        self.preferences.oracleclient_path = self.e_oracleclient_path.text()              
        self.preferences.save_preferences(self.nome_file_preferences)

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])
    application = win_connections_class(v_global_work_dir+'/MSql.ini',v_global_work_dir+'/MSql_connections.ini')
    application.show()
    sys.exit(app.exec())        