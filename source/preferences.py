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
            # posizione finestre        
            if v_json['remember_window_pos']==1:
                self.remember_window_pos = True
            else:
                self.remember_window_pos = False
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
            # colori
            self.color_dev = v_json['color_dev']
            self.color_prod = v_json['color_prod']
        # imposto valori di default senza presenza dello specifico file
        else:
            self.remember_window_pos = True
            self.open_dir = 'W:\\SQL'
            self.save_dir = 'W:\\SQL'
            self.utf_8 = False
            self.end_of_line = False
            self.font_editor = 'Cascadia Code SemiBold, 11'
            self.font_result = 'Segoe UI, 8'
            self.editable = False
            self.color_prod = '#aaffff'
            self.color_dev = '#ffffff'
       
class win_preferences_class(QMainWindow, Ui_preferences_window):
    """
        Gestione delle preferenze di MSql
    """                
    def __init__(self, p_nome_file_preferences):
        super(win_preferences_class, self).__init__()        
        self.setupUi(self)

        self.nome_file_preferences = p_nome_file_preferences
        
        # creo l'oggetto preferenze che automaticamente carica il file o le preferenze di default
        self.preferences = preferences_class(self.nome_file_preferences)        
        # le preferenze caricate vengono riportate a video
        self.e_remember_window_pos.setChecked(self.preferences.remember_window_pos)        
        self.e_default_open_dir.setText(self.preferences.open_dir)
        self.e_default_save_dir.setText(self.preferences.save_dir)        
        self.e_default_utf_8.setChecked(self.preferences.utf_8)        
        self.e_default_end_of_line.setChecked(self.preferences.end_of_line)        
        self.e_default_font_editor.setText(self.preferences.font_editor)
        self.e_default_font_result.setText(self.preferences.font_result)
        self.e_default_editable.setChecked(self.preferences.editable)   
        self.e_default_color_prod.setText(self.preferences.color_prod)
        self.e_default_color_dev.setText(self.preferences.color_dev)     

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
            self.e_default_font_editor.setText(font.family() + ', '+ str(font.pointSize()))            

    def slot_b_default_font_result(self):
        """
           Scelta del font
        """
        # apro la dialog di scelta del font partendo da quello eventualmente già settato
        v_split = self.e_default_font_result.text().split(',')        
        v_font_pref = QFont(str(v_split[0]),int(v_split[1]))
        
        font, ok = QFontDialog.getFont(v_font_pref)
        if ok:
            self.e_default_font_result.setText(font.family() + ','+ str(font.pointSize()))            

    def slot_b_default_color_prod(self):
        """
           Scelta del colore di base per server Prod (indicato da shortcut di tastiera F1)
        """
        color = QColorDialog.getColor()                
        self.e_default_color_prod.setText(color.name())            

    def slot_b_default_color_dev(self):
        """
           Scelta del colore di base per server Dev (indicato da shortcut di tastiera F2)
        """
        color = QColorDialog.getColor()                
        self.e_default_color_dev.setText(color.name())            

    def slot_b_save(self):
        """
           Salvataggio
        """	
        # il default per ricordare posizione della window
        if self.e_remember_window_pos.isChecked():
            v_remember_window_pos = 1
        else:
            v_remember_window_pos = 0
        
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
		
		# scrivo nel file un elemento json contenente le informazioni inseriti dell'utente
        v_json ={'remember_window_pos': v_remember_window_pos,
                 'open_dir': self.e_default_open_dir.text(),
		         'save_dir': self.e_default_save_dir.text(),
                 'utf_8': v_utf_8,
                 'eol': v_eol,
		         'font_editor' :self.e_default_font_editor.text(),
		         'font_result' : self.e_default_font_result.text(),
                 'editable' : v_editable,
                 'color_prod': self.e_default_color_prod.text(),
                 'color_dev': self.e_default_color_dev.text()}
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