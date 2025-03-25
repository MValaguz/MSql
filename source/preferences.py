#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11 con libreria pyqt6
#  Data..........: 06/09/2023
#  Descrizione...: Gestione delle preferenze di MSql
 
#  Note..........: Il layout è stato creato utilizzando qtdesigner e il file preferences.py è ricavato partendo da preferences_ui.ui 

#  Note..........: Questo programma ha due funzioni. La prima di gestire a video le preferenze e la seconda di restituire una classe
#                  che contiene le preferenze (preferences_class)

#Librerie sistema
import sys
import os
import json
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Definizioni interfaccia
from preferences_ui import Ui_preferences_window
#Librerie aggiuntive interne
from utilita import message_info, message_question_yes_no, cripta_messaggio, decripta_messaggio
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class preferences_class():
    """
        Classe che riporta tutte le preferenze
    """
    def __init__(self, p_nome_file_preferences, p_nome_file_connections):
        """
           Lettura del file delle preferenze e delle connessioni e caricamento nella classe
        """
        # Se esiste il file delle preferenze...le carico nell'oggetto
        if os.path.isfile(p_nome_file_preferences):
            v_json = json.load(open(p_nome_file_preferences, 'r'))
            # ricordarsi posizione finestre        
            if v_json['remember_window_pos']==1:
                self.remember_window_pos = True
            else:
                self.remember_window_pos = False
            # ricordarsi posizione testo nei files
            if v_json['remember_text_pos']==1:
                self.remember_text_pos = True
            else:
                self.remember_text_pos = False
            # tema dei colori scuro
            if v_json['dark_theme']==1:
                self.dark_theme = True
            else:
                self.dark_theme = False
            # directory apertura e salvataggio
            self.open_dir = v_json['open_dir']
            self.save_dir = v_json['save_dir']
            # end of line 
            if v_json['eol'] == 1:            
                self.end_of_line = True
            else:
                self.end_of_line = False
            # font
            self.font_editor = v_json['font_editor']
            self.font_result = v_json['font_result']
            # sql editabili
            if v_json['editable'] == 1:
                self.editable = True
            else:
                self.editable = False
            # auto column resize
            if v_json['auto_column_resize'] == 1:            
                self.auto_column_resize = True
            else:
                self.auto_column_resize = False
            # indentation guide
            if v_json['indentation_guide'] == 1:            
                self.indentation_guide = True
            else:
                self.indentation_guide = False
            # clear output result when run pl-sql command
            if 'auto_clear_output' in v_json and v_json['auto_clear_output'] == 1:            
                self.auto_clear_output = True
            else:
                self.auto_clear_output = False
            # autocompletamento del testo nell'editor
            if 'autocompletation' in v_json and v_json['autocompletation'] == 1:            
                self.autocompletation = True
            else:
                self.autocompletation = False
            # default format data
            if 'date_format' in v_json:                        
                self.date_format = v_json['date_format']
            else:
                self.date_format = '%d/%m/%Y %H:%M:%S'
            # csv separator
            self.csv_separator = v_json['csv_separator']
            # tab size
            self.tab_size = v_json['tab_size']
            # autosave snapshoot (salvataggio degli editor aperti nella cartella backup)
            if 'autosave_snapshoot_interval' in v_json:                        
                self.autosave_snapshoot_interval = v_json['autosave_snapshoot_interval']
            else:
                self.autosave_snapshoot_interval = 60
            # general zoom
            if 'general_zoom' in v_json:            
                self.general_zoom = v_json['general_zoom']            
            else:
                self.general_zoom = 100
            # open new editor at open 
            if 'open_new_editor' in v_json:            
                if v_json['open_new_editor'] == 1:       
                    self.open_new_editor = True
                else:
                    self.open_new_editor = False
            else:
                self.open_new_editor = True
            # refresh dictionary (frequenza con cui lanciare l'aggiornamento del dizionario)
            if 'refresh_dictionary' in v_json:                        
                self.refresh_dictionary = v_json['refresh_dictionary']
            else:
                self.refresh_dictionary= 15
        # imposto valori di default senza presenza dello specifico file
        else:
            self.remember_window_pos = True
            self.remember_text_pos = True
            self.dark_theme = False
            self.general_zoom = 100
            self.open_dir = ''
            self.save_dir = ''            
            self.end_of_line = False
            self.font_editor = 'Cascadia Code, 12, BOLD'                                
            self.font_result = 'Segoe UI, 8'
            self.autosave_snapshoot_interval = 60
            self.editable = False
            self.auto_column_resize = False
            self.indentation_guide = False
            self.auto_clear_output = True
            self.autocompletation = True
            self.date_format = '%d/%m/%Y %H:%M:%S'
            self.csv_separator = '|'
            self.tab_size = '2'
            self.open_new_editor = True
            self.refresh_dictionary = 15
            
        # Se esiste il file delle connessioni...le carico nell'oggetto
        if os.path.isfile(p_nome_file_connections):
            v_dump = open(p_nome_file_connections, 'rb').read()
            v_dump = decripta_messaggio(v_dump)            
            v_json = json.loads(v_dump)
            # elenco server è composto da Titolo, TNS e Colore, Flag per la connessione di default, Flag per evidenzia colore e richiesta conferme in creazione pkg (es. ('Server Prod (SMILE_815)','SMILE_815','#aaffff','0','0','0') )
            self.elenco_server = v_json['server']
            # elenco users è composto da Titolo, User, Password, Flag per la connessione di default (es. ('USER_SMILE','SMILE','SMILE','1') )
            self.elenco_user = v_json['users']            
        # ...se il file non esiste non carico nulla 
        else:            
            # elenco server è composto da Titolo, TNS e Colore, Flag per la connessione di default, Flag per evidenzia colore e richiesta conferme in creazione pkg (es. ('Server Prod (SMILE_815)','SMILE_815','#aaffff','0','0','0') )
            self.elenco_server = []
            # elenco users è composto da Titolo, User, Password, Flag per la connessione di default (es. ('USER_SMILE','SMILE','SMILE','1') )
            self.elenco_user = []
       
class win_preferences_class(QMainWindow, Ui_preferences_window):
    """
        Gestione delle preferenze di MSql
    """                
    def __init__(self, p_nome_file_preferences, p_nome_file_connections):
        super(win_preferences_class, self).__init__()        
        self.setupUi(self)

        # salvo nella classe i parametri ricevuti per usi successivi
        self.nome_file_preferences = p_nome_file_preferences
        self.nome_file_connections = p_nome_file_connections

        # forzo il posizionamento sul primo tab
        self.o_tab_widget.setCurrentIndex(0)
        
        # creo l'oggetto preferenze che automaticamente carica il file o le preferenze di default
        self.preferences = preferences_class(self.nome_file_preferences, self.nome_file_connections)        
        # le preferenze caricate vengono riportate a video
        self.e_remember_window_pos.setChecked(self.preferences.remember_window_pos)        
        self.e_remember_text_pos.setChecked(self.preferences.remember_text_pos)        
        self.e_dark_theme.setChecked(self.preferences.dark_theme)        
        self.e_general_zoom.setValue(self.preferences.general_zoom)
        self.e_default_open_dir.setText(self.preferences.open_dir)
        self.e_default_save_dir.setText(self.preferences.save_dir)                
        self.e_default_end_of_line.setChecked(self.preferences.end_of_line)                
        self.e_autosave_snapshoot_interval.setValue(self.preferences.autosave_snapshoot_interval)
        self.e_refresh_dictionary.setValue(self.preferences.refresh_dictionary)
        self.e_open_new_editor.setChecked(self.preferences.open_new_editor)
        self.e_default_font_editor.setText(self.preferences.font_editor)
        self.e_default_font_result.setText(self.preferences.font_result)
        self.e_default_editable.setChecked(self.preferences.editable)   
        self.e_default_auto_column_resize.setChecked(self.preferences.auto_column_resize)
        self.e_default_indentation_guide.setChecked(self.preferences.indentation_guide)
        self.e_default_auto_clear_output.setChecked(self.preferences.auto_clear_output)
        self.e_default_autocompletation.setChecked(self.preferences.autocompletation)
        self.e_default_date_format.setCurrentText(self.preferences.date_format)
        self.e_default_csv_separator.setText(self.preferences.csv_separator)
        self.e_tab_size.setText(self.preferences.tab_size)

        ###
        # preparo elenco server        
        ###
        self.o_server.setColumnCount(7)
        self.o_server.setHorizontalHeaderLabels(['Server title','TNS Name','Color','','AutoConnection','Emphasis','CREATE'+chr(10)+'confirm'])           
        v_rig = 1                
        for record in self.preferences.elenco_server:                                    
            self.o_server.setRowCount(v_rig) 
            self.carico_riga_server(v_rig,record)

            # passo alla prossima riga
            v_rig += 1
        self.o_server.resizeColumnsToContents()

        ###
        # preparo elenco user        
        ###
        self.o_users.setColumnCount(4)
        self.o_users.setHorizontalHeaderLabels(['User title','User name','Password','AutoConnection'])   
        v_rig = 1                
        for record in self.preferences.elenco_user:                                    
            self.o_users.setRowCount(v_rig) 
            self.carico_riga_user(v_rig, record)

            # passo alla prossima riga
            v_rig += 1
        self.o_users.resizeColumnsToContents()

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
    
    def slot_b_restore(self):
        """
           Ripristina tutte preferenze di default
        """
        if message_question_yes_no('Do you want to restore default preferences?') == 'Yes':
            # cancello il file delle preferenze
            if os.path.isfile(self.nome_file_preferences):
                os.remove(self.nome_file_preferences)

            if message_question_yes_no('Do you want to delete connections preferences too?') == 'Yes':
                # cancello il file delle preferenze
                if os.path.isfile(self.nome_file_connections):
                    os.remove(self.nome_file_connections)

            # emetto messaggio di fine
            message_info('Preferences restored! Restart MSql to see the changes ;-)')
            # esco dal programma delle preferenze
            self.close()

    def slot_b_open_pref_dir(self):
        """
           Apre la cartella di lavoro di MSql 
        """
        os.startfile(os.path.expanduser('~\\AppData\\Local\\MSql\\'))        
    
    def slot_b_default_open_dir(self):
        """
           Scelta della dir 
        """
        dirName = QFileDialog.getExistingDirectory(self, "Choose a directory")                  
        if dirName != "":
            self.e_default_open_dir.setText( dirName )        

    def slot_b_default_save_dir(self):
        """
           Scelta della dir 
        """
        dirName = QFileDialog.getExistingDirectory(self, "Choose a directory")                  
        if dirName != "":
            self.e_default_save_dir.setText( dirName )        

    def slot_b_default_font_editor(self):
        """
           Scelta del font
        """
        # apro la dialog di scelta del font partendo da quello eventualmente già settato
        v_split = self.e_default_font_editor.text().split(',')
        v_font_pref = QFont(str(v_split[0]),int(v_split[1]))

        font, ok = QFontDialog.getFont(v_font_pref)
        if ok:
            v_text = font.family() + ', '+ str(font.pointSize())            
            if font.bold():
                v_text += ', BOLD'
            self.e_default_font_editor.setText(v_text)            

    def slot_b_default_font_result(self):
        """
           Scelta del font
        """
        # apro la dialog di scelta del font partendo da quello eventualmente già settato
        v_split = self.e_default_font_result.text().split(',')        
        v_font_pref = QFont(str(v_split[0]),int(v_split[1]))
        
        font, ok = QFontDialog.getFont(v_font_pref)
        if ok:
            v_text = font.family() + ','+ str(font.pointSize())
            if font.bold():
                v_text += ', BOLD'
            self.e_default_font_result.setText(v_text)            

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
        self.carico_riga_user(v_rig, ['','','',0])

    def slot_b_user_remove(self):
        """
           Toglie la riga selezionata, da elenco user
        """
        self.o_users.removeRow(self.o_users.currentRow())

    def slot_b_save(self):
        """
           Salvataggio
        """	
        # il default per ricordare posizione della window
        if self.e_remember_window_pos.isChecked():
            v_remember_window_pos = 1
        else:
            v_remember_window_pos = 0

        # il default per ricordare posizione del testo nei file
        if self.e_remember_text_pos.isChecked():
            v_remember_text_pos = 1
        else:
            v_remember_text_pos = 0

        # tema dei colori scuro
        if self.e_dark_theme.isChecked():
            v_dark_theme = 1
        else:
            v_dark_theme = 0

        # il default per risultato editabile va convertito
        if self.e_default_editable.isChecked():
            v_editable = 1
        else:
            v_editable = 0

        # il default per end of line va convertito
        if self.e_default_end_of_line.isChecked():
            v_eol = 1
        else:
            v_eol = 0
            
        # il default per auto column resize va convertito
        if self.e_default_auto_column_resize.isChecked():
            v_auto_column_resize = 1
        else:
            v_auto_column_resize = 0

        # il default per indentation guide va convertito
        if self.e_default_indentation_guide.isChecked():
            v_indentation_guide = 1
        else:
            v_indentation_guide = 0
        
        # il default per clear output va convertito
        if self.e_default_auto_clear_output.isChecked():
            v_auto_clear_output = 1
        else:
            v_auto_clear_output = 0
                
        # il default per autocompletamento va convertito
        if self.e_default_autocompletation.isChecked():
            v_autocompletation = 1
        else:
            v_autocompletation = 0
                        
        # il default per apertura automatica di un nuovo editor all'apertura del programma, va convertito
        if self.e_open_new_editor.isChecked():
            v_open_new_editor = 1
        else:
            v_open_new_editor = 0

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
        # elenco dei users
        ###
        v_users = []
        for i in range(0,self.o_users.rowCount()):
            # controllo il campo della password che è annegato in un widget
            v_password = self.o_users.cellWidget(i,2)            
            # controllo la checkbox del default (da notare come la checkbox è annegata in un oggetto di layout 
            # e quindi prima prendo l'oggetto che c'è annegato nella cella della tabella, poi in quell'oggetto
            # prendo tutti gli oggetti di tipo checkbox e poi prendo il primo checkbox (che è anche l'unico)
            # e da li prendo il suo stato!
            v_widget = self.o_users.cellWidget(i,3)
            v_checkbox = v_widget.findChildren(QCheckBox)
            if v_checkbox[0].isChecked():                
                v_default = '1'
            else:
                v_default = '0'
            v_users.append( ( self.o_users.item(i,0).text(), self.o_users.item(i,1).text() , v_password.text(), v_default) )            

        # se il tabsize è vuoto --> imposto 2
        if self.e_tab_size.text() == '':
            self.e_tab_size.setText('2')
	
		# scrivo primo file delle preferenze generiche 
        v_json ={'remember_window_pos': v_remember_window_pos,
                 'remember_text_pos': v_remember_text_pos,
                 'dark_theme': v_dark_theme,
                 'open_dir': self.e_default_open_dir.text(),
		         'save_dir': self.e_default_save_dir.text(),                 
                 'eol': v_eol,
                 'autosave_snapshoot_interval':self.e_autosave_snapshoot_interval.value(),
		         'font_editor' :self.e_default_font_editor.text(),
		         'font_result' : self.e_default_font_result.text(),
                 'editable' : v_editable,
                 'auto_column_resize': v_auto_column_resize,
                 'indentation_guide': v_indentation_guide,
                 'csv_separator': self.e_default_csv_separator.text(),
                 'tab_size': self.e_tab_size.text(),
                 'auto_clear_output': v_auto_clear_output,
                 'date_format': self.e_default_date_format.currentText(),
                 'general_zoom':self.e_general_zoom.value(),
                 'autocompletation':v_autocompletation,
                 'open_new_editor':v_open_new_editor,
                 'refresh_dictionary':self.e_refresh_dictionary.value(),
                }

		# scrittura nel file dell'oggetto json (notare come venga usata la funzione dump senza la s finale in quanto scrive byte)
        with open(self.nome_file_preferences, 'w') as outfile:json.dump(v_json, outfile)

        # scrivo secondo file con i dati user e server (separato in quanto nelle versione per GitHub non viene riportato!)
        v_json ={'server': v_server,
                 'users': v_users                 
                }

		# scrittura nel file dell'oggetto json (che viene criptato e notare come venga usata la funzione dumps con la s finale in quanto scrive stringhe)
        v_dump = cripta_messaggio(json.dumps(v_json))
        with open(self.nome_file_connections, 'wb') as outfile:
            outfile.write(v_dump)
        
        message_info('Preferences saved! Restart MSql to see the changes ;-)')

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])
    application = win_preferences_class('MSql.ini','MSql_connections.ini')
    application.show()
    sys.exit(app.exec())        