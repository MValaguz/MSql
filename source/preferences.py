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
import subprocess
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Definizioni interfaccia
from qtdesigner.preferences_ui import Ui_preferences_window
#Librerie aggiuntive interne
from utilita import message_info, message_question_yes_no, cripta_messaggio, decripta_messaggio, return_global_work_dir
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))
#Cartella di lavoro
v_global_work_dir = return_global_work_dir()

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
            # nome tema colori chiaro
            if 'clear_theme' in v_json:
                self.clear_theme = v_json['clear_theme']
            else:
                self.clear_theme = ''
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
            # refresh dictionary (frequenza con cui lanciare l'aggiornamento del dizionario)
            if 'app_language' in v_json:                        
                self.app_language = v_json['app_language']
            else:
                self.app_language = 'English'
            # nome gif animata da visualizzare durante esecuzione dei comandi
            if 'animated_gif' in v_json:                        
                self.animated_gif = v_json['animated_gif']
            else:
                self.animated_gif = ''
            # colore evidenziatore sia in formato letterale che in formato esadecimale (per poter gestire la combobox)
            # fare riferimento al file custom_widget, tabella colori contenuto in classe MyColorComboBox
            if 'highlight_color' in v_json:
                self.highlight_color = v_json['highlight_color']                
            else:
                self.highlight_color = 'Green'                
            if 'highlight_color_hex' in v_json:                
                self.highlight_color_hex = v_json['highlight_color_hex']
            else:            
                self.highlight_color_hex = '#43a047'
            # nome dell'autore-utilizzatore di MSql
            if 'author_name' in v_json:
                self.author_name = v_json['author_name']                
            else:
                self.author_name = ''
            # tipo di connessione Oracle
            if 'connection_mode' in v_json:
                self.connection_mode = v_json['connection_mode']
            else:
                self.connection_mode = 0  # 0=Thin 1=Thick
            # percorso di Oracle Client (se connection_mode=1)
            if 'oracleclient_path' in v_json:
                self.oracleclient_path = v_json['oracleclient_path']    
            else:
                self.oracleclient_path = ''
            # attivazione della mappa di procedure/funzioni dentro l'editor
            if "show_map_proc_func" in v_json:
                self.show_map_proc_func = v_json['show_map_proc_func']
            else:
                self.show_map_proc_func = True

        # imposto valori di default senza presenza dello specifico file
        else:
            self.remember_window_pos = True
            self.remember_text_pos = True
            self.dark_theme = False
            self.clear_theme = ''
            self.general_zoom = 100
            self.open_dir = ''
            self.save_dir = ''            
            self.end_of_line = False
            #self.font_editor = 'Cascadia Code, 12, BOLD'                                
            self.font_editor = 'Fira Code, 11'                                
            self.font_result = 'Segoe UI, 8'
            self.autosave_snapshoot_interval = 60            
            self.auto_column_resize = False
            self.indentation_guide = False
            self.auto_clear_output = True
            self.autocompletation = True
            self.date_format = '%d/%m/%Y %H:%M:%S'
            self.csv_separator = '|'
            self.tab_size = '2'
            self.open_new_editor = True
            self.refresh_dictionary = 15
            self.app_language = 'English'
            self.animated_gif = ''
            self.highlight_color = 'Green' # Fare riferimento al file custom_widget, tabella colori contenuto in classe MyColorComboBox
            self.highlight_color_hex = '#43a047' # Fare riferimento al file custom_widget, tabella colori contenuto in classe MyColorComboBox
            self.author_name = ''
            self.connection_mode = 0  # 0=Thin 1=Thick
            self.oracleclient_path = ''    
            self.show_map_proc_func = True        

        # Viene aggiunta alla classe la proprietà editable che gestisce la modalità di editazione delle tabelle (un tempo era anche una preferenza a video che poi è stata eliminata)
        self.editable = False
            
        # Se esiste il file delle connessioni...le carico nell'oggetto
        if os.path.isfile(p_nome_file_connections):
            v_dump = open(p_nome_file_connections, 'rb').read()
            v_dump = decripta_messaggio(v_dump)            
            v_json = json.loads(v_dump)
            # elenco server è composto da Titolo, TNS e Colore, Flag per la connessione di default, Flag per evidenzia colore e richiesta conferme in creazione pkg (es. ('Server Prod (SMILE_815)','SMILE_815','#aaffff','0','0','0') )
            self.elenco_server = v_json['server']
            # elenco users è composto da Titolo, User, Password, Flag per la connessione di default (es. ('USER_SMILE','SMILE','SMILE','1','') )
            self.elenco_user = v_json['users']            
        # ...se il file non esiste non carico nulla 
        else:            
            # elenco server è composto da Titolo, TNS e Colore, Flag per la connessione di default, Flag per evidenzia colore e richiesta conferme in creazione pkg (es. ('Server Prod (SMILE_815)','SMILE_815','#aaffff','0','0','0') )
            self.elenco_server = []
            # elenco users è composto da Titolo, User, Password, Flag per la connessione di default (es. ('USER_SMILE','SMILE','SMILE','1') )
            self.elenco_user = []
       
    def restore_default_preferences(self, p_nome_file_preferences, p_nome_file_connections):
        """
            Ripristina tutte preferenze di default
        """
        if message_question_yes_no(QCoreApplication.translate('Preferences','Do you want to restore default preferences?')) == 'Yes':
            # cancello il file delle preferenze
            if os.path.isfile(p_nome_file_preferences):
                os.remove(p_nome_file_preferences)

            if message_question_yes_no(QCoreApplication.translate('Preferences','Do you want to delete connections preferences too?')) == 'Yes':
                # cancello il file delle preferenze
                if os.path.isfile(p_nome_file_connections):
                    os.remove(p_nome_file_connections)

            # emetto messaggio di fine
            message_info(QCoreApplication.translate('Preferences','Preferences restored! Restart MSql to see the changes ;-)'))
    
    def save_preferences(self, p_nome_file_preferences):
        """
           Salvataggio di tutte le preferenze in un file json
        """		
		# scrivo primo file delle preferenze generiche 
        v_json ={'remember_window_pos': self.remember_window_pos,
                 'remember_text_pos': self.remember_text_pos,
                 'dark_theme': self.dark_theme,
                 'open_dir': self.open_dir,
		         'save_dir': self.save_dir,                 
                 'eol': self.end_of_line,
                 'autosave_snapshoot_interval':self.autosave_snapshoot_interval,
		         'font_editor' :self.font_editor,
		         'font_result' : self.font_result,                 
                 'auto_column_resize': self.auto_column_resize,
                 'indentation_guide': self.indentation_guide,
                 'csv_separator': self.csv_separator,
                 'tab_size': self.tab_size,
                 'auto_clear_output': self.auto_clear_output,
                 'date_format': self.date_format,
                 'general_zoom': self.general_zoom,
                 'autocompletation': self.autocompletation,
                 'open_new_editor': self.open_new_editor,
                 'refresh_dictionary': self.refresh_dictionary,
                 'app_language': self.app_language,
                 'animated_gif': self.animated_gif,
                 'highlight_color': self.highlight_color,
                 'highlight_color_hex': self.highlight_color_hex,
                 'author_name': self.author_name,
                 'connection_mode': self.connection_mode,
                 'oracleclient_path': self.oracleclient_path,
                 'clear_theme': self.clear_theme,
                 'show_map_proc_func': self.show_map_proc_func               
                }

		# scrittura nel file dell'oggetto json (notare come venga usata la funzione dump senza la s finale in quanto scrive byte)
        with open(p_nome_file_preferences, 'w') as outfile:json.dump(v_json, outfile)
        
        message_info(QCoreApplication.translate('Preferences','Preferences saved! Restart MSql to see the changes ;-)'))

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
        
        # carico elenco degli stili Clear in base al sistema operativo
        self.e_clear_theme.addItems(QStyleFactory.keys())
        
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
        self.e_default_auto_column_resize.setChecked(self.preferences.auto_column_resize)
        self.e_default_indentation_guide.setChecked(self.preferences.indentation_guide)
        self.e_default_auto_clear_output.setChecked(self.preferences.auto_clear_output)
        self.e_default_autocompletation.setChecked(self.preferences.autocompletation)
        self.e_default_date_format.setCurrentText(self.preferences.date_format)
        self.e_default_csv_separator.setText(self.preferences.csv_separator)
        self.e_tab_size.setText(self.preferences.tab_size)
        self.e_language.setCurrentText(self.preferences.app_language)
        self.e_default_animated_gif.setText(self.preferences.animated_gif)
        self.e_highlight_color.setCurrentText(self.preferences.highlight_color)
        self.e_author_name.setText(self.preferences.author_name)
        self.e_clear_theme.setCurrentText(self.preferences.clear_theme)
        self.e_default_map_proc_func.setChecked(self.preferences.show_map_proc_func)

        # Carico anteprima gif animata
        self.preview_gif_animata()

    def preview_gif_animata(self):
        """
           Carico antemprima della gif animata
        """
        if self.e_default_animated_gif.text() != '':                        
            self.movie = QMovie(self.e_default_animated_gif.text())                                
        else:
            self.movie = QMovie("icons:anim_wait1.gif")                                
        
        # segnale che si scatena ad ogni visualizzazione di frame e che serve solo per zoomare l'animazione
        self.movie.frameChanged.connect(self.update_movie_frame)
        self.l_default_animated_gif.setMovie(self.movie)
        self.movie.start()        

    def update_movie_frame(self):
        """
           Esegue lo zoom sulla gif animata degli ingranaggi
        """
        frame = self.movie.currentPixmap() 
        scaled_frame = frame.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) 
        self.l_default_animated_gif.setPixmap(QPixmap.fromImage(scaled_frame.toImage()))
    
    def slot_e_default_animated_gif(self):
        """
           Aggiorna la preview della gif animata
        """        
        self.preview_gif_animata()
        
    def slot_b_restore(self):
        """
           Ripristina tutte preferenze di default
        """
        self.preferences.restore_default_preferences(self.nome_file_preferences, self.nome_file_connections)
        # esco dal programma delle preferenze
        self.close()

    def slot_b_open_pref_dir(self):
        """
           Apre la cartella di lavoro di MSql 
        """
        if os.name == "posix":
            subprocess.Popen(["xdg-open", os.path.expanduser(v_global_work_dir)])            
        else:
            os.startfile(os.path.expanduser(v_global_work_dir))        
    
    def slot_b_default_open_dir(self):
        """
           Scelta della dir 
        """
        dirName = QFileDialog.getExistingDirectory(self, "Choose a directory")                  
        if dirName != "":
            self.e_default_open_dir.setText( dirName )       

    def slot_b_default_animated_gif(self):
        """
           apre la dialog box per selezionare un file contenente un DataBase SQLite
        """        
        fileName = QFileDialog.getOpenFileName(self, "Choose GIF file", '' ,"GIF files (*.gif);;All files (*.*)")       
        if fileName[0] != "":
            self.e_default_animated_gif.setText( fileName[0] )         

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
            
    def slot_b_save(self):
        """
           Salvataggio
        """	
        # il default per ricordare posizione della window
        if self.e_remember_window_pos.isChecked():
            self.preferences.remember_window_pos = 1
        else:
            self.preferences.remember_window_pos = 0

        # il default per ricordare posizione del testo nei file
        if self.e_remember_text_pos.isChecked():
            self.preferences.remember_text_pos = 1
        else:   
            self.preferences.remember_text_pos = 0

        # tema dei colori scuro
        if self.e_dark_theme.isChecked():
            self.preferences.dark_theme = 1
        else:
            self.preferences.dark_theme = 0

        # il default per end of line va convertito
        if self.e_default_end_of_line.isChecked():
            self.preferences.end_of_line = 1
        else:
            self.preferences.end_of_line = 0

        # il default per auto column resize va convertito
        if self.e_default_auto_column_resize.isChecked():
            self.preferences.auto_column_resize = 1
        else:
            self.preferences.auto_column_resize = 0

        # il default per indentation guide va convertito
        if self.e_default_indentation_guide.isChecked():
            self.preferences.indentation_guide = 1
        else:
            self.preferences.indentation_guide = 0
        
        # il default per clear output va convertito
        if self.e_default_auto_clear_output.isChecked():
            self.preferences.auto_clear_output = 1
        else:
            self.preferences.auto_clear_output = 0
                
        # il default per autocompletamento va convertito
        if self.e_default_autocompletation.isChecked():
            self.preferences.autocompletation = 1
        else:
            self.preferences.autocompletation = 0
                        
        # il default per apertura automatica di un nuovo editor all'apertura del programma, va convertito
        if self.e_open_new_editor.isChecked():
            self.preferences.open_new_editor = 1
        else:
            self.preferences.open_new_editor = 0

        # il default per attivare la mappa di procedure/funzioni dentro l'editor
        if self.e_default_map_proc_func.isChecked():
            self.preferences.show_map_proc_func = 1
        else:
            self.preferences.show_map_proc_func = 0
        
        # se il tabsize è vuoto --> imposto 2
        if self.e_tab_size.text() == '':
            self.e_tab_size.setText('2')

        # imposto tutte le altre preferenze
        self.preferences.open_dir = self.e_default_open_dir.text()
        self.preferences.save_dir = self.e_default_save_dir.text()                                  
        self.preferences.autosave_snapshoot_interval = self.e_autosave_snapshoot_interval.value()
        self.preferences.font_editor = self.e_default_font_editor.text()
        self.preferences.font_result = self.e_default_font_result.text()                 
        self.preferences.csv_separator = self.e_default_csv_separator.text()
        self.preferences.tab_size = self.e_tab_size.text()                 
        self.preferences.date_format = self.e_default_date_format.currentText()
        self.preferences.general_zoom = self.e_general_zoom.value()                 
        self.preferences.refresh_dictionary = self.e_refresh_dictionary.value()
        self.preferences.app_language = self.e_language.currentText()
        self.preferences.animated_gif = self.e_default_animated_gif.text()
        self.preferences.highlight_color = self.e_highlight_color.currentText()
        self.preferences.highlight_color_hex = self.e_highlight_color.currentData().name()
        self.preferences.author_name = self.e_author_name.text()
        self.preferences.connection_mode = self.preferences.connection_mode
        self.preferences.oracleclient_path = self.preferences.oracleclient_path
        self.preferences.clear_theme = self.e_clear_theme.currentText()
	
		# scrivo file delle preferenze generiche 
        self.preferences.save_preferences(self.nome_file_preferences)

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])
    application = win_preferences_class(v_global_work_dir+'/MSql.ini',v_global_work_dir+'/MSql_connections.ini')
    application.show()
    sys.exit(app.exec())        