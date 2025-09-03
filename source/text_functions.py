#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 29/08/2025
#  Descrizione...: Gestione delle funzioni di testo

#Librerie sistema
import sys
import re
#Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
#Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from text_functions_ui import Ui_text_functions_window
#Import dei moduli interni
from utilita import message_error
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class class_text_functions(QDialog, Ui_text_functions_window):
    """
        Permette di visualizzare il contenuto di una tabella presente in un database SQLite
    """
    def __init__(self, p_input_text):
        
        # incapsulo la classe grafica da qtdesigner
        super(class_text_functions, self).__init__()        
        self.setupUi(self)    

        # Imposta i flag per mostrare i bottoni di minimizza e massimizza
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)

        # rapporto di grandezza del primo splitter in modo che la parte di elenco delle funzioni occupi meno spazio delle altre 2
        self.splitter_2.setStretchFactor(0,4)        
        self.splitter_2.setStretchFactor(1,10)                
        
        # Carico elenco delle funzioni        
        self.e_list_functions.addItems(['Split','Compress','Align Columns','Matrix decorator'])

        # Imposto la funzione di default
        self.e_list_functions.setCurrentRow(0)                                
        self.slot_e_list_functions_clicked(self.e_list_functions.currentIndex())

        # Imposto il testo di input
        self.e_input_text.setText(p_input_text)

    def slot_b_copy_output(self):
        """
           Copia il contenuto del campo output negli appunti
        """
        # Copia nella clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.e_output_text.toPlainText())

    def slot_e_list_functions_clicked(self, p_index):
        """
           Evento che si scatena quando si sceglie una funzione
        """ 
        self.e_parameter1.setText('')               
        self.e_parameter2.setText('')               
        self.e_parameter3.setText('')               
        self.e_parameter4.setText('')               
        if p_index.data() == 'Split':            
            self.e_description.setText(QCoreApplication.translate('text_functions','Takes the selected text and splits it into multiple lines using the comma as the identifier'))            
            self.e_parameter1.setPlaceholderText(QCoreApplication.translate('text_functions','input:  indicate the delimiter char (default comma)'))
            self.e_parameter2.setPlaceholderText(QCoreApplication.translate('text_functions','effect: char to add at end of line'))
            self.e_parameter3.setPlaceholderText("")
            self.e_parameter4.setPlaceholderText("")
        elif p_index.data() == 'Compress':            
            self.e_description.setText(QCoreApplication.translate('text_functions','Takes the selected text, which must span multiple lines, and creates a single line with the starting lines, where the line break is a comma. Any commas preceding the line break in the starting text will be ignored'))
            self.e_parameter1.setPlaceholderText(QCoreApplication.translate('text_functions','input: indicate the separator char (ex. comma)'))
            self.e_parameter2.setPlaceholderText("")
            self.e_parameter3.setPlaceholderText("")
            self.e_parameter4.setPlaceholderText("")
        elif p_index.data() == 'Align Columns':            
            self.e_description.setText(QCoreApplication.translate('text_functions','Takes the selected text, which must have a columnar format and sorts its structure both visually and by row sorting. Ex. \n 7 8 9 \n 6 7 8 \n 5 6 7'))
            self.e_parameter1.setPlaceholderText(QCoreApplication.translate('text_functions','input:  column delimeter (blank space as default)'))
            self.e_parameter2.setPlaceholderText(QCoreApplication.translate('text_functions','effect: column width'))
            self.e_parameter3.setPlaceholderText(QCoreApplication.translate('text_functions','effect: add column separator (blank space as default)'))
            self.e_parameter4.setPlaceholderText(QCoreApplication.translate('text_functions','effect: number sort column (none for default)'))            
        elif p_index.data() == 'Matrix decorator':            
            self.e_description.setText(QCoreApplication.translate('text_functions','Takes the selected text, which must contain a text array. Adds the specified decorator to each cell element.. Ex. \n 7 8 9 \n 6 7 8 \n 5 6 7'))
            self.e_parameter1.setPlaceholderText(QCoreApplication.translate('text_functions','input:  column delimeter (blank space as default)'))
            self.e_parameter2.setPlaceholderText(QCoreApplication.translate('text_functions','effect: char decorator'))            
            self.e_parameter3.setPlaceholderText(QCoreApplication.translate('text_functions','effect: char to add at end of line'))
            self.e_parameter4.setPlaceholderText("")

    def slot_b_start_clicked(self):
        """
           Evento che si scatena quando si clicca bottone per eseguire la funzione
        """
        if self.e_list_functions.currentIndex().data() == 'Split':
            self.e_output_text.setText(self.splitta_il_testo(self.e_input_text.toPlainText(), self.e_parameter1.text(), self.e_parameter2.text()))
        elif self.e_list_functions.currentIndex().data() == 'Compress':           
            self.e_output_text.setText(self.comprime_il_testo(self.e_input_text.toPlainText(), self.e_parameter1.text()))
        elif self.e_list_functions.currentIndex().data() == 'Align Columns':
            self.e_output_text.setText(self.allinea_colonne(self.e_input_text.toPlainText(), self.e_parameter1.text(), self.e_parameter2.text(), self.e_parameter3.text(), self.e_parameter4.text()))
        elif self.e_list_functions.currentIndex().data() == 'Matrix decorator':
            self.e_output_text.setText(self.decora_matrice(self.e_input_text.toPlainText(), self.e_parameter1.text(), self.e_parameter2.text(), self.e_parameter3.text()))

    def splitta_il_testo(self, p_testo, p_parameter1, p_parameter2):
        """
           Viene preso il testo e diviso su più righe
           Parameter1: eventuale carattere delimitatore di parola (es. :)
           Parameter2: se indicato inserisce il carattere a fine riga
        """        
        if p_parameter1 == '':
            p_parameter1 = ','
        v_risultato = ''
        # splitto il testo usando eventuale parametro in input        
        v_split = p_testo.split(p_parameter1)                            
        # creo il risultato prendendo tutte le righe dello split        
        for riga in v_split:
            # viene pulita la stringa a destra             
            riga = riga.rstrip(p_parameter1+' ')            
            # metto la riga nel risultato nettificandola a sinistra
            v_risultato += riga.lstrip()            
            # aggiungo il delimitatore e il ritorno a capo
            if p_parameter2 != '':   
                v_risultato += p_parameter2
            v_risultato += '\n'

        return v_risultato
    
    def comprime_il_testo(self, p_testo, p_parameter1):
        """
           Viene preso il testo e lo comprime su unica riga
        """
        print(f"Parameter1: {p_parameter1}")        
        # Divide il testo in righe
        righe = p_testo.strip().split('\n')
    
        # Crea una lista pulita delle righe non vuote
        righe_pulite = []
        for riga in righe:
            riga_pulita = riga.strip()
            if riga_pulita != '':
                righe_pulite.append(riga_pulita)
    
        # Unisce le righe con il separatore
        return p_parameter1.join(righe_pulite)   
         
    def allinea_colonne(self, p_testo, p_delimitatore, p_larghezza, p_delimitatore_output, p_colonna_ordinamento):
        """
        Allinea le colonne di una stringa multilinea e le ordina opzionalmente.

        - p_testo: stringa con righe separate da newline (\n)
        - p_delimitatore: carattere che separa le colonne (es. "," o "\t" o None per split automatico)
        - p_larghezza: larghezza fissa da applicare a tutte le colonne (int)
        - p_delimitatore_output: carattere da usare per separare le celle in output (default: spazio)
        - p_colonna_ordinamento: indice della colonna su cui ordinare (1-based)        
        """
        # controllo che p_larghezza sia integer
        try:
            p_larghezza = int(p_larghezza)
        except:
            p_larghezza = 15

        # controllo che colonna ordinamento sia integer
        try:
            p_colonna_ordinamento = int(p_colonna_ordinamento) - 1
        except:
            p_colonna_ordinamento = ''

        # valore di default
        if p_delimitatore_output == '':
            p_delimitatore_output = ' '

        # Step 1: Converti la stringa in lista di righe
        righe = p_testo.strip().splitlines()

        # Step 2: Split righe in colonne
        colonne_split = []
        for riga in righe:
            if p_delimitatore:
                colonne = riga.strip().split(p_delimitatore)
            else:
                colonne = riga.strip().split()  # split su spazi multipli
            colonne_split.append(colonne)

        # Step 3: Ordina se richiesto
        if p_colonna_ordinamento != '':
            colonne_split.sort(key=lambda r: r[p_colonna_ordinamento] if p_colonna_ordinamento < len(r) else "")

        # Step 4: Ricostruisci righe allineate con larghezza uniforme
        num_colonne = max(len(r) for r in colonne_split)
        righe_allineate = []
        for riga in colonne_split:
            celle_formattate = []
            for i in range(num_colonne):
                valore = riga[i] if i < len(riga) else ""
                celle_formattate.append(valore.ljust(p_larghezza))
            riga_formattata = p_delimitatore_output.join(celle_formattate).rstrip()
            righe_allineate.append(riga_formattata)

        return "\n".join(righe_allineate)

    def decora_matrice(self, p_testo, p_delimitatore, p_decoratore, p_eol):
        """
        Funzione per decorare le celle di una matrice.

        - p_testo: stringa multilinea che rappresenta la matrice
        - p_delimitatore: carattere che separa le colonne (es. ' ', ',', '\t')
        - p_decoratore: carattere da mettere attorno a ogni cella (es. "'", '"')
        - p_eol: stringa da aggiungere alla fine di ogni riga (es. ',', ';', '')
        """
        # imposto valori di default
        if p_delimitatore == '':
            p_delimitatore = ' '
        if p_decoratore == '':
            p_decoratore = "'"

        righe = p_testo.strip().split('\n')
        matrice_decorata = []

        # Costruisce un pattern flessibile per delimitatori
        if p_delimitatore == ' ':
            pattern = r'[ \t]+'
        else:
            pattern = rf'\s*{re.escape(p_delimitatore)}\s*'

        for riga in righe:
            celle = re.split(pattern, riga.strip())
            celle_decorate = [f"{p_decoratore}{cella}{p_decoratore}" for cella in celle if cella]
            riga_decorata = p_delimitatore.join(celle_decorate) + p_eol
            matrice_decorata.append(riga_decorata)

        return '\n'.join(matrice_decorata)

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
    app = QApplication([])    
    application = class_text_functions("""MA_GEVD1_SEQ.NEXTVAL,P_IDELA_NU,r_ela_attuale_g.IDBDG_NU,r_ela_attuale_g.AZIEN_CO,r_ela_attuale_g.POSTA_NU,r_ela_attuale_g.ARTIC_CO,R_MA_GEVD1.REVPR_CO,r_ela_attuale_g.REVIS_CO,
          r_ela_attuale_g.PRELI_DO,r_ela_attuale_g.QTCAL_NU,R_MA_GEVD1.ARTI1_DE,R_MA_GEVD1.ARTI2_DE,R_MA_GEVD1.INOUT_CO,R_MA_GEVD1.STATO_DO ,P_LOGIN_CO,SYSDATE""") 
    application.show()
    sys.exit(app.exec())      