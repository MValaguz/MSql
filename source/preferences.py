# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 06/09/2023
 Descrizione...: Gestione delle preferenze di MSql
 
 Note..........: Il layout è stato creato utilizzando qtdesigner e il file preferences.py è ricavato partendo da preferences_ui.ui 

 Note..........: Questo programma ha due funzioni. La prima di gestire a video le preferenze e la seconda di restituire una classe
                 che contiene le preferenze (preferences_class)
"""

#Librerie sistema
import sys
import os
import json
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
#Definizioni interfaccia
from preferences_ui import Ui_preferences_window
#Librerie aggiuntive interne
from utilita import message_info, message_question_yes_no

class preferences_class():
    """
        Classe che riporta tutte le preferenze
    """
    def __init__(self, p_nome_file_preferences):
        """
           Lettura del file delle preferenze e caricamento nella classe
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
            # utf-8
            if v_json['utf_8'] == 1:            
                self.utf_8 = True
            else:
                self.utf_8 = False
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
            # csv separator
            self.csv_separator = v_json['csv_separator']
            # tab size
            self.tab_size = v_json['tab_size']
            # server
            self.elenco_server = v_json['server']
            # users
            self.elenco_user = v_json['users']
        # imposto valori di default senza presenza dello specifico file
        else:
            self.remember_window_pos = True
            self.remember_text_pos = True
            self.dark_theme = False
            self.open_dir = 'W:\\SQL'
            self.save_dir = 'W:\\SQL'
            self.utf_8 = False
            self.end_of_line = False
            self.font_editor = 'Courier New, 12, BOLD'
            self.font_result = 'Segoe UI, 8'
            self.editable = False
            self.auto_column_resize = False
            self.indentation_guide = False
            self.auto_clear_output = True
            self.csv_separator = '|'
            self.tab_size = '2'
            # elenco server è composto da Titolo, TNS e Colore
            self.elenco_server = [('Server Prod (ICOM_815)','ICOM_815','#aaffff'),
                                  ('Server Dev (BACKUP_815)','BACKUP_815','#ffffff')]
            # elenco users è composto da Titolo, User, Password
            self.elenco_user = [('USER_SMILE','SMILE','SMILE'),
                                ('USER_SMI','SMI','SMI'),
                                ('USER_SMIPACK','SMIPACK','SMIPACK'),
                                ('USER_SMITEC','SMITEC','SMITEC'),
                                ('USER_SMIMEC','SMIMEC','SMIMEC'),
                                ('USER_SMIWRAP (SMIEnergia)','SMIWRAP','SMIWRAP'),
                                ('USER_ENOBERG','ENOBERG','ENOBERG'),
                                ('USER_FORM (SMILab)','SMIBLOW','SMIBLOW'),
                                ('USER_SARCO','SARCO','SARCO')]
       
class win_preferences_class(QMainWindow, Ui_preferences_window):
    """
        Gestione delle preferenze di MSql
    """                
    def __init__(self, p_nome_file_preferences):
        super(win_preferences_class, self).__init__()        
        self.setupUi(self)

        self.nome_file_preferences = p_nome_file_preferences

        # forzo il posizionamento sul primo tab
        self.o_tab_widget.setCurrentIndex(0)
        
        # creo l'oggetto preferenze che automaticamente carica il file o le preferenze di default
        self.preferences = preferences_class(self.nome_file_preferences)        
        # le preferenze caricate vengono riportate a video
        self.e_remember_window_pos.setChecked(self.preferences.remember_window_pos)        
        self.e_remember_text_pos.setChecked(self.preferences.remember_text_pos)        
        self.e_dark_theme.setChecked(self.preferences.dark_theme)        
        self.e_default_open_dir.setText(self.preferences.open_dir)
        self.e_default_save_dir.setText(self.preferences.save_dir)        
        self.e_default_utf_8.setChecked(self.preferences.utf_8)        
        self.e_default_end_of_line.setChecked(self.preferences.end_of_line)        
        self.e_default_font_editor.setText(self.preferences.font_editor)
        self.e_default_font_result.setText(self.preferences.font_result)
        self.e_default_editable.setChecked(self.preferences.editable)   
        self.e_default_auto_column_resize.setChecked(self.preferences.auto_column_resize)
        self.e_default_indentation_guide.setChecked(self.preferences.indentation_guide)
        self.e_default_auto_clear_output.setChecked(self.preferences.auto_clear_output)
        self.e_default_csv_separator.setText(self.preferences.csv_separator)
        self.e_tab_size.setText(self.preferences.tab_size)

        # preparo elenco server        
        self.o_server.setColumnCount(4)
        self.o_server.setHorizontalHeaderLabels(['Server title','TNS Name','Color',''])           
        v_rig = 1                
        for record in self.preferences.elenco_server:                                    
            self.o_server.setRowCount(v_rig) 
            self.o_server.setItem(v_rig-1,0,QTableWidgetItem(record[0]))       
            self.o_server.setItem(v_rig-1,1,QTableWidgetItem(record[1]))                               
            self.o_server.setItem(v_rig-1,2,QTableWidgetItem(record[2]))                                           
            # come quarta colonna metto il pulsante per la scelta del colore
            v_color_button = QPushButton()            
            v_icon = QIcon()
            v_icon.addPixmap(QPixmap(":/icons/icons/color.png"), QIcon.Normal, QIcon.Off)
            v_color_button.setIcon(v_icon)
            v_color_button.clicked.connect(self.slot_set_color_server)

            self.o_server.setCellWidget(v_rig-1,3,v_color_button)                               
            v_rig += 1
        self.o_server.resizeColumnsToContents()

        # preparo elenco user        
        self.o_users.setColumnCount(3)
        self.o_users.setHorizontalHeaderLabels(['User title','User name','Password'])   
        v_rig = 1                
        for record in self.preferences.elenco_user:                                    
            self.o_users.setRowCount(v_rig) 
            self.o_users.setItem(v_rig-1,0,QTableWidgetItem(record[0]))       
            self.o_users.setItem(v_rig-1,1,QTableWidgetItem(record[1]))                               
            self.o_users.setItem(v_rig-1,2,QTableWidgetItem(record[2]))                               
            v_rig += 1
        self.o_users.resizeColumnsToContents()

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
        self.o_server.setItem( index.row(), 2, QTableWidgetItem(color.name()) )            
    
    def slot_b_restore(self):
        """
           Ripristina tutte preferenze di default
        """
        if message_question_yes_no('Do you want to restore default preferences?') == 'Yes':
            # cancello il file delle preferenze
            if os.path.isfile(self.nome_file_preferences):
                os.remove(self.nome_file_preferences)

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
        self.o_server.setRowCount(self.o_server.rowCount()+1)

    def slot_b_server_remove(self):
        """
           Toglie la riga selezionata, da elenco server
        """
        self.o_server.removeRow(self.o_server.currentRow())

    def slot_b_user_add(self):
        """
           Crea una riga vuota dove poter inserire informazioni utente di connessione al server
        """
        self.o_users.setRowCount(self.o_users.rowCount()+1)

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
        
        # il default per utf-8 va convertito 
        if self.e_default_utf_8.isChecked():
            v_utf_8 = 1
        else:
            v_utf_8 = 0

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

        # elenco dei server
        v_server = []
        for i in range(0,self.o_server.rowCount()):
            v_server.append( ( self.o_server.item(i,0).text(), self.o_server.item(i,1).text(), self.o_server.item(i,2).text() ) )            

        # elenco dei users
        v_users = []
        for i in range(0,self.o_users.rowCount()):
            v_users.append( ( self.o_users.item(i,0).text(), self.o_users.item(i,1).text() , self.o_users.item(i,2).text()) )            

        # se il tabsize è vuoto --> imposto 2
        if self.e_tab_size.text() == '':
            self.e_tab_size.setText('2')
	
		# scrivo nel file un elemento json contenente le informazioni inseriti dell'utente
        v_json ={'remember_window_pos': v_remember_window_pos,
                 'remember_text_pos': v_remember_text_pos,
                 'dark_theme': v_dark_theme,
                 'open_dir': self.e_default_open_dir.text(),
		         'save_dir': self.e_default_save_dir.text(),
                 'utf_8': v_utf_8,
                 'eol': v_eol,
		         'font_editor' :self.e_default_font_editor.text(),
		         'font_result' : self.e_default_font_result.text(),
                 'editable' : v_editable,
                 'auto_column_resize': v_auto_column_resize,
                 'indentation_guide': v_indentation_guide,
                 'csv_separator': self.e_default_csv_separator.text(),
                 'tab_size': self.e_tab_size.text(),
                 'auto_clear_output': v_auto_clear_output,
                 'server': v_server,
                 'users': v_users
                }

		# scrittura nel file dell'oggetto json
        with open(self.nome_file_preferences, 'w') as outfile:json.dump(v_json, outfile)
        
        message_info('Preferences saved! Restart MSql to see the changes ;-)')

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])
    application = win_preferences_class('MSql.ini')
    application.show()
    sys.exit(app.exec())        