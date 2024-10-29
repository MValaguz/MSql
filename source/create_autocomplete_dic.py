# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt6
 Data..........: 22/11/2023
 Descrizione...: Gestione e creazione del dizionario per l'autocomplete all'interno dell'editor
 
 Note..........: Il layout è stato creato utilizzando qtdesigner e il file create_autocomplete_dic_ui.py è ricavato partendo da create_autocomplete_dic_ui.ui 
"""

#Librerie sistema
import sys
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Definizioni interfaccia
from create_autocomplete_dic_ui import Ui_create_autocomplete_dic_window
#Librerie aggiuntive interne
from utilita import message_info, message_error
from avanzamento import avanzamento_infinito_class
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class create_autocomplete_dic_class(QMainWindow, Ui_create_autocomplete_dic_window):
    """
        Gestore per la creazione del file che contiene il dizionario che viene poi usato dall'autocomplete dell'editor
        p_connesso          = flag che indica se connesso a Oracle
        p_oracle_cursor     = oggetto cursore a Oracle
        p_user_name         = nome utente di connessione
        p_file_name_dic     = nome del file da scrivere        
    """
    def __init__(self, p_connesso, p_oracle_cursor, p_user_name, p_nome_file_dic):
        
        # incapsulo la classe grafica da qtdesigner
        super(create_autocomplete_dic_class, self).__init__()        
        self.setupUi(self)   

        # salvo i parametri ricevuti in input, per averli allo step di creazione
        self.connesso = p_connesso
        self.oracle_cursor = p_oracle_cursor
        self.nome_file_dic = p_nome_file_dic
        self.user_name = p_user_name

    def slot_b_create(self):
        """
           Creazione del file con i termini di dizionario per autocomplete
        """
        if not self.connesso:
            message_error('You must to connect to Oracle!')
            return 'ko'
        
        # creo una barra di avanzamento infinita
        v_progress = avanzamento_infinito_class("sql_editor.gif")            
        v_counter = 0
        # apro il file di testo che conterrà il risultato con tutti i nomi delle funzioni, procedure e package, ecc
        v_file = open(self.nome_file_dic,'w')
        # la funzione put_line viene inserita di default 
        v_file.write('dbms_output.put_line(text)' +'\n')

        # richiesto di analizzare procedure, funzioni e package
        if self.e_analyze_1.isChecked():
            # elenco di tutti gli oggetti funzioni, procedure e package
            self.oracle_cursor.execute("SELECT OBJECT_NAME, OBJECT_TYPE FROM ALL_OBJECTS WHERE OWNER='" + self.user_name + "' AND OBJECT_TYPE IN ('PACKAGE','PROCEDURE','FUNCTION') ORDER BY OBJECT_TYPE, OBJECT_NAME")
            v_elenco_oggetti = self.oracle_cursor.fetchall()
            # leggo il sorgente di ogni oggetto di cui sopra...
            for v_record in v_elenco_oggetti:                                
                # visualizzo barra di avanzamento e se richiesto interrompo
                v_counter += 1
                v_progress.avanza('Analizing ' + v_record[0] ,v_counter)
                if v_progress.richiesta_cancellazione:                        
                    break
                # leggo il sorgente
                self.oracle_cursor.execute("""SELECT UPPER(TEXT) FROM ALL_SOURCE WHERE OWNER='"""+self.user_name+"""' AND NAME='"""+v_record[0]+"""' AND TYPE='"""+v_record[1]+"""' ORDER BY LINE""")                
                v_start_sezione = False
                v_text_sezione = ''
                v_risultato = ''
                # processo tutte le righe del sorgente
                for result in self.oracle_cursor:                       
                    # dalla riga elimino gli spazi a sinistra e a destra
                    v_riga_raw = result[0]
                    v_riga = v_riga_raw.lstrip()
                    v_riga = v_riga.rstrip()                                        
                    v_riga = v_riga.replace('"','')
                    # individio riga di procedura-funzione
                    if v_riga[0:9] == 'PROCEDURE' or v_riga[0:8] == 'FUNCTION':
                        # il nome della procedura-funzione inizia dal primo carattere spazio fino ad apertura parentesi tonda                        
                        if v_riga.find('(') != -1:
                            v_nome = v_riga[v_riga.find(' ')+1:v_riga.find('(')]
                        else:
                            v_nome = v_riga[v_riga.find(' ')+1:len(v_riga)]
                        v_risultato = v_nome + '('    
                        # indico che sono all'interno di una nuova sezione, terminata la quale poi dovrò esplodere elenco parametri                       
                        v_start_sezione = True
                        v_text_sezione = v_riga
                    # ...continua la sezione di parametri....
                    elif v_start_sezione:
                        v_text_sezione += v_riga

                    # elaboro la sezione che contiene i parametri della procedura-funzione
                    if v_start_sezione and v_riga.find(')') != -1:                        
                        v_text_sezione = v_text_sezione[v_text_sezione.find('(')+1:v_text_sezione.find(')')]                        
                        v_elenco_parametri = v_text_sezione.split(',')                        
                        v_indice = 0                        
                        for v_txt_parametro in v_elenco_parametri:                                                        
                            v_stringa = v_txt_parametro.lstrip()
                            v_parametro = v_stringa[0:v_stringa.find(' ')]
                            # aggiungo la virgola tra un parametro e l'altro
                            v_indice += 1
                            if v_indice != len(v_elenco_parametri):
                                v_risultato += v_parametro + ','
                            else:
                                v_risultato += v_parametro
                            
                        v_text_sezione = ''
                        v_start_sezione = False
                        v_risultato += ')'
                        if v_record[1] == 'PACKAGE':
                            v_risultato = v_record[0] + '.' + v_risultato
                        v_file.write(v_risultato.lstrip() +'\n')

        # richiesto di analizzare tabelle e viste
        if self.e_analyze_2.isChecked():
            # elenco di tutti gli oggetti funzioni, procedure e package
            self.oracle_cursor.execute("SELECT TABLE_NAME || '.' || COLUMN_NAME AS TESTO FROM ALL_TAB_COLUMNS WHERE OWNER='" + self.user_name + "' ORDER BY TABLE_NAME, COLUMN_ID")
            v_elenco_campi = self.oracle_cursor.fetchall()
            # visualizzo barra di avanzamento e se richiesto interrompo
            v_counter += 1
            v_progress.avanza('Analizing tables and views...', v_counter)
            # leggo il sorgente di ogni oggetto di cui sopra...
            for v_record in v_elenco_campi:                                                
                v_file.write(v_record[0] +'\n')
                    
        v_file.close()
        message_info('The autocompletion dictionary has been created! Restart MSql to see the changes ;-)')
      
# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = create_autocomplete_dic_class(False, None, None, 'MSql_autocompletion.ini') 
    application.show()
    sys.exit(app.exec())     