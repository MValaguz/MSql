#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 23/01/2023
#  Descrizione...: Scopo dello script è prendere un foglio di excel e caricarlo in un DB Oracle.
#  Note..........: Al momento la procedura non permette di personalizzare il tipo e il numero di colonne da importare.
#                  Si dà per scontato che alla prima riga siano presenti i nomi delle colonne.
#                  Il programma per ogni colonna ricerca la lunghezza massima del campo.
#                  Ricerca per ogni colonna il tipo predominante. Nel caso in cui i valori non predominanti risulteranno
#                  incopatibili con i valori dominanti, ci potrebbero essere degli errori.
                 
#  Modifiche 2020: Ho constatato che l'utilizzo della libreria openpyxl era molto impegnativo dal punto di vista dei moduli caricati a memoria.
#                  Inoltre alcuni fogli non venivano letti correttamente; laddove ad esempio c'erano dei valori, la libreria caricava celle vuote.
#                  Sono quindi passato alla libreria xlrd che poi è quella utilizzata anche da Pandas che è di fatto un must delle librerie python.                 
#  Note..........: Di seguito un estratto dalla documentazione xlrd riguardo al tipo di dato contenuto nelle celle; nel codice non ho usato la costante ma il numero
#                  Type symbol 	   Type number 	    Python value
#                  XL_CELL_EMPTY 	     0 	        empty string ''
#                  XL_CELL_TEXT 	     1 	        a Unicode string
#                  XL_CELL_NUMBER        2 	        float
#                  XL_CELL_DATE 	     3 	        float
#                  XL_CELL_BOOLEAN       4 	        int; 1 means TRUE, 0 means FALSE
#                  XL_CELL_ERROR 	     5 	        int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
#                  XL_CELL_BLANK 	     6 	        empty string ''. Note: this type will appear only when open_workbook(..., formatting_info=True) is used.

#Librerie sistema
import sys
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from import_export_excel_to_oracle_ui import Ui_import_export_window
#Librerie di data base
import oracledb
import oracle_my_lib
import utilita_database
#Import dei moduli interni
from utilita import message_error, message_info
# Libreria per la lettura e scrittura file di excel
from xlrd import open_workbook
from xlrd import xldate
# Liberia regular expression
import  re
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

def slugify(text, lower=1):
    """
        questa funzione, usando le regular expression, normalizza il nome di una colonna 
        togliendo caratteri indesiderati
    """
    if lower == 1:
        text = text.strip().lower()
    text = re.sub(r'[^\w _-]+', '', text)
    text = re.sub(r'[- ]+', '_', text)
    return text

class import_export_class(QMainWindow, Ui_import_export_window):
    """
        Copia i dati di un file di excel dentro una tabella di un database Oracle
    """
    def __init__(self, p_user, p_password, p_server):
        
        # incapsulo la classe grafica da qtdesigner
        super(import_export_class, self).__init__()        
        self.setupUi(self)    

        # salvo i parametri ricevuti in input, dentro l'oggetto
        self.user = p_user
        self.password = p_password
        self.server = p_server
        
        # carica elenco delle tabelle oracle                
        v_elenco_tabelle_oracle = utilita_database.estrae_elenco_tabelle_oracle( '1', self.user, self.password, self.server)
        # carica la combobox tabelle di oracle
        v_valore_corrente = self.e_table_name.currentText()
        self.e_table_name.clear()                
        self.e_table_name.addItems( v_elenco_tabelle_oracle )            
        self.e_table_name.setCurrentText( v_valore_corrente )            
    
    def slot_select_excel_file(self):
        """
           apre la dialog box per selezionare un file excel
        """
        fileName = QFileDialog.getOpenFileName(self, "Choose a file","","Excel Files (*.xls);;All Files (*.*)")                  
        if fileName[0] != "":
            self.e_excel.setText( fileName[0] )        

    def slot_start(self):
        """
           esegue l'operazione 
        """      
        # eseguo i controlli            
        if self.e_excel.displayText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Excel file'))
            return 'ko'
        if self.e_table_name.currentText() == '':
            message_error(QCoreApplication.translate('import_export','Please enter a Table Name'))
            return 'ko'
                             
        # indico tramite il cursore del mouse che è in corso un'elaborazione
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))       

        # creo l'oggetto, che in init esegue la procedura di trasferimento dati
        v_ok =excel_to_oracle_class(False,
                                    self.user,
                                    self.password,
                                    self.server,
                                    self.e_table_name.currentText(),                                         
                                    self.e_excel.displayText())       
        
        # riporto a "normale" l'icona del mouse
        QApplication.restoreOverrideCursor()        
        
        if v_ok.message_info != '':
            message_info(v_ok.message_info)                                    
        
        if v_ok.message_error != '':
            message_error(v_ok.message_error)                                    
        
class excel_to_oracle_class():
    """
        Importa un foglio di excel dentro una tabella di Oracle
        Va indicato attraverso l'instanziazione della classe:
            p_debug          = Se True --> esegue le print del lavoro svolto
            p_user_db        = Nome utente del DB Oracle
            p_password_db    = Password utente del DB Oracle
            p_dsn_db         = Indirizzo IP del DB Oracle o dsn
            p_table_name     = Nome della tabella di destinazione Oracle
            p_excel_file     = Nome del file di excel (compresa di pathname)                            
        
        L'instanziazione comporta l'automatica esecuzione dell'importazione del file 
        dentro la tabella oracle.
        Al termine è necessario controllare i valori degli attributi message_error o message_info
        per capire se ci sono stati errori o se tutto ok ma con restrizioni
    """                 
    def __init__(self,
                 p_debug,
                 p_user_db,
                 p_password_db,
                 p_dsn_db,
                 p_table_name,
                 p_excel_file):
                        
        self.message_error = ''
        self.message_info = ''

        #Controllo se passato nome tabella
        if p_table_name == '':
            self.message_error = QCoreApplication.translate('import_export','Oracle table name is required!')
            return None
        
        #Apro il file di excel
        try:
            wb = open_workbook(filename=p_excel_file)
        except:
            self.message_error = QCoreApplication.translate('import_export','Format file invalid. Only xls file format!')
            #esco
            return None        
        
        #Se il file contiene più fogli, avverto che verrà preso solo il primo
        if len( wb.sheets() ) > 1:            
            self.message_info = QCoreApplication.translate('import_export','This file contains more than one sheet. It will be taken the first') + ' ' + wb.sheet_by_index(0).name + '!'
        
        #Mi posiziono sul primo foglio 
        v_foglio = wb.sheet_by_index(0)
        
        #Estraggo la struttura del foglio
        self.v_numero_totale_righe = 0
        self.v_debug = p_debug
        v_definizione_colonne = self.struttura_foglio(v_foglio) 
        
        #Collegamento a Oracle                
        try:
            oracle_my_lib.inizializzo_client()  
            self.v_oracle_db = oracledb.connect(user=p_user_db, password=p_password_db, dsn=p_dsn_db)
        except:
            self.message_error = QCoreApplication.translate('import_export','Connecting problems to Oracle DB!')
            #esco
            return None
        
        self.v_oracle_cursor = self.v_oracle_db.cursor()    
        
        #Creo la tabella                                 
        if self.creo_tabella(v_definizione_colonne, p_table_name) == 'ok':
            if self.importa_foglio(v_foglio, v_definizione_colonne, p_table_name) == 'ok':
                #Messaggio finale
                self.message_info = QCoreApplication.translate('import_export','Action completed with') + ' ' + str(self.v_numero_totale_righe) + ' ' + QCoreApplication.translate('import_export','records imported!')
        
        self.v_oracle_db.close()                
        return None        
    
    def struttura_foglio(self, p_foglio):        
        #Leggo il foglio per colonne, in questo modo ottengo come risultante la struttura della tabella da creare
        #tenendo conto della larghezza massima di ogni colonna. La lista "v_definizione_colonne" conterrà per ogni riga,
        #4 campi che saranno, il nome, il tipo, la lunghezza e eventuali decimali se tipo è numerico
        v_definizione_colonne = []  
        self.v_numero_totale_righe = 0      
        v_numero_colonna = 0
        for col_idx in range(0,p_foglio.ncols):    
            v_1a_riga = True
            v_numero_colonna += 1
            v_nome_colonna = ''
            #questa lista serve per determinare il tipo di campo "prevalente" che è presente nella colonna. 
            #non verrà preso il primo tipo campo che capita ma quello che risulta avere il risultato più alto tra tutti
            #i tipi campo trovati
            v_tipo_colonna = 'VARCHAR2'                
            v_varchar2 = 0
            v_number = 0
            v_date = 0
            v_other = 0
            v_larghezza_colonna = 1
            v_larghezza_decimali = 0            
            v_numero_righe_per_colonna = 0
            for row_idx in range(0,p_foglio.nrows):
                cell = p_foglio.cell(row_idx, col_idx)                
                #la prima riga contiene per standard il nome della colonna
                if v_1a_riga:
                    v_1a_riga = False
                    if cell.value is not None:
                        #Estraggo e normalizzo il nome della colonna 
                        v_nome_colonna = slugify(cell.value)
                        #Se nome della colonna supera i 30 caratteri --> lo tronco a 30
                        if len(v_nome_colonna) > 30:
                            v_nome_colonna = v_nome_colonna[0:30]
                    else:
                        v_nome_colonna = 'COL_' + str(v_numero_colonna)
                                
                #per le altre righe devo calcolare il tipo di dato e la larghezza massima 
                #il tipo di dato dipende dal primo valore che incontra....dovrà essere eventualmente perfezionata questa cosa 
                else:
                    #considero solo celle che contengono un valore (escludo anche quelle con una specie di spazio all'interno)
                    if cell.value is not None:                        
                        #la cella è di tipo testo (VARCHAR2)                        
                        if p_foglio.cell_type(row_idx, col_idx) == 1:                                                        
                            v_varchar2 += 1
                            if len(cell.value) > v_larghezza_colonna:
                                v_larghezza_colonna = len(cell.value)
                        #la cella è numerica (NUMBER)
                        elif p_foglio.cell_type(row_idx, col_idx) == 2:                            
                            v_number += 1
                            v_stringa = str(cell.value)                            
                            #normalizzo virgola con punto
                            v_stringa = v_stringa.replace(',','.')
                            #è presente la parte decimale (divido la parte intera dalla decimale)
                            if v_stringa.find('.') > 0:  
                                if len(v_stringa.split('.')[0]) > v_larghezza_colonna:
                                    v_larghezza_colonna = len(v_stringa.split('.')[0])
                                if len(v_stringa.split('.')[1]) > v_larghezza_decimali:
                                    v_larghezza_decimali = len(v_stringa.split('.')[1])
                             #è presente solo la parte intera
                            elif len(v_stringa) > v_larghezza_colonna:
                                v_larghezza_colonna = len(v_stringa)                            
                        #la cella è una data (DATE)
                        elif p_foglio.cell_type(row_idx, col_idx) == 3:
                            v_date += 1
                            v_larghezza_colonna = 20
                        #la cella non è riconoscibile (OTHER)
                        else:
                            v_other += 1
                #aggiorno numero righe trovate nella colonna
                v_numero_righe_per_colonna += 1
                                
                    
            #controllo qual'è il risultato del tipo colonna prevalente (di base varchar2)                        
            #una colonna viene definita numerica o di data solo se nella colonna non ci sono caratteri
            if v_varchar2 == 0:
                if v_number > 0:
                    v_tipo_colonna = 'NUMBER'
                elif v_date > 0:
                    v_tipo_colonna = 'DATE'                            
            
            #salvo la lista dei dati di definizione della colonna
            if self.v_debug:
                print("Definizione delle colonne Nome: " + v_nome_colonna + " tipo: " + v_tipo_colonna + " larghezza: " +  str(v_larghezza_colonna) + " decimali: " + str(v_larghezza_decimali))                

            v_definizione_colonne.append((v_nome_colonna, v_tipo_colonna, v_larghezza_colonna, v_larghezza_decimali))
            
            #aggiorno il numero delle righe contenuto del foglio (è il valore massimo delle righe trovate su tutte le colonne)
            if v_numero_righe_per_colonna > self.v_numero_totale_righe:
                self.v_numero_totale_righe = v_numero_righe_per_colonna
                                    
        return v_definizione_colonne
    
    def creo_tabella(self, 
                     p_definizione_colonne, 
                     p_table_name):
         
        #se siamo in modalità test --> cancello la tabella
        if self.v_debug:
            try:
                print("Cancellazione della tabella " + p_table_name)                
                v_query = 'DROP TABLE ' + p_table_name
                self.v_oracle_cursor.execute(v_query)
            except:
                pass
                        
        v_query = 'CREATE TABLE ' + p_table_name + '('
        v_1a_volta = True
        #definizione_colonne risulta così strutturata
        #1° campo = Nome
        #2° campo = Tipo (varchar2, number)
        #3° campo = Larghezza colonna (per numeri solo la parte intera)
        #4° campo = Larghezza decimali (solo per numeri con decimali)
        for valori in p_definizione_colonne:
            if v_1a_volta:
                v_1a_volta=False
            else:
                v_query += ','
            v_query += valori[0] + ' ' + valori[1]
            if valori[1] == 'VARCHAR2':
                #la colonna risulta varchar2 ma sono stati trovati all'interno dei numeri con decimali....per evitare
                #problemi aumento la grandezza della colonna aggiungendo anche i decimali + altri due caratteri per 
                #separatore decimali e eventuale segno meno
                if valori[3] > 0:
                    v_query += '(' + str(valori[2]+valori[3]+2) + ')'
                #altrimenti è puro char
                else:
                    v_query += '(' + str(valori[2]) + ')'
            elif valori[1] == 'NUMBER':
                v_query += '(' + str(valori[2]+valori[3]) + ',' + str(valori[3]) + ')'            
        v_query += ')'
        
        if self.v_debug:
            print("Creazione della tabella " + v_query)                
                    
        #Invio del comando di creazione tabella
        try:    
            self.v_oracle_cursor.execute(v_query)
        except:
            self.message_error = QCoreApplication.translate('import_export','Problem during create Oracle table!') + chr(10) + QCoreApplication.translate('import_export','The table') + ' ' + p_table_name + ' ' + QCoreApplication.translate('import_export', 'already exists?') + chr(10) + QCoreApplication.translate('import_export',"Remember that the excel file must be haven't formatting and filters activated!")
            #esco
            return 'ko'

        return 'ok'
    
    def importa_foglio(self,                        
                       p_foglio, 
                       p_definizione_colonne,
                       p_table_name):

        #Leggo il foglio per righe        
        v_1a_riga = True        
        for row_idx in range(0,p_foglio.nrows):      
            if not v_1a_riga:
                v_1a_volta = True
                v_insert = "INSERT INTO " + p_table_name + " VALUES("
                v_i = 0
                #Per ogni riga creo la relativa insert, tenendo conto del tipo di dato definito
                for col_idx in range(0,p_foglio.ncols):
                    if v_1a_volta:
                        v_1a_volta = False
                    else:
                        v_insert += ","
                    #se la cella è vuota o ti tipo formula --> null
                    cell = p_foglio.cell(row_idx, col_idx) 
                    if p_foglio.cell_value(row_idx, col_idx) == None or p_foglio.cell_type(row_idx, col_idx) > 4:
                        v_insert += "null"
                    elif p_definizione_colonne[v_i][1] == 'VARCHAR2':
                        v_valore_stringa = str(cell.value)
                        #sostituisce il carattere unicode "rombo con il ?" con un asterisco
                        v_valore_stringa = v_valore_stringa.replace(u"\ufffd", "*")
                        #sostituisco il carattere apice con il doppio apice
                        v_valore_stringa = v_valore_stringa.replace("'","''")
                        v_insert += "'" + v_valore_stringa + "'"
                    elif p_definizione_colonne[v_i][1] == 'NUMBER':
                        #v_insert += "'" + str(cell.value).replace(',','.') + "'"
                        v_str_number = str(cell.value).strip()
                        if v_str_number == '':
                            v_insert += "null"
                        else:
                            v_insert += v_str_number
                    elif p_definizione_colonne[v_i][1] == 'DATE':
                        #v_date è di tipo datetime
                        v_date = xldate.xldate_as_datetime(cell.value,0)                                                  
                        v_insert += "TO_DATE('" + str(v_date) + "','RRRR-MM-DD HH24:MI:SS')"
                    v_i += 1
                v_insert += ")"        
                #eseguo la insert
                if self.v_debug:
                    print(v_insert)                                        
                                
                self.v_oracle_cursor.execute(v_insert)                
                        
            else:
                v_1a_riga = False
                    
        self.v_oracle_db.commit()
        return 'ok'
       
# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = import_export_class('SMILE','SMILE','BACKUP_815') 
    application.show()
    sys.exit(app.exec())      