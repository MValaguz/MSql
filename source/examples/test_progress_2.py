# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 11/04/2023
 Descrizione...: Classe per la gestione di una progressbar (è ad esempio utilizzato in oracle_my_sql.py)
"""
# Librerie di sistema
import sys
import time
import datetime
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
# Librerie grafiche
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# Libreria icone
import resource_rc
# Libreria Oracle
import cx_Oracle
# Librerie interne
import oracle_my_lib

# Classe per la visualizzazione della progressbar
class avanzamento_infinito_class(QProgressDialog):
    """
        Visualizzo una progress bar senza fine...
    """       
    def __init__(self, p_icon_name):                 
        # creazione della wait window        
        QProgressDialog.__init__(self)        
        self.setMinimumDuration(0)        
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Wait...")    
        self.setMinimumWidth(400)            
        # icona del titolo
        self.icon = QIcon()
        self.icon.addPixmap(QPixmap(":/icons/icons/"+p_icon_name), QIcon.Normal, QIcon.Off)        
        self.setWindowIcon(self.icon)        
        # creo un campo label che viene impostato con 100 caratteri in modo venga data una dimensione di base standard
        self.progress_label = QLabel()            
        self.progress_label.setText('...')
        # collego la label già presente nell'oggetto progress bar con la mia label 
        self.setLabel(self.progress_label)                                                        
        # creo una progress personalizzata
        self.progress_bar = QProgressBar()
        # imposto valore minimo e massimo a 0 in modo venga considerata una progress a tempo indefinito
        # Attenzione! dentro nel ciclo deve essere usata la funzione setvalue altrimenti non visualizza e non avanza nulla!
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)        
        self.setBar(self.progress_bar)                
        # imposto il flag che si valorizza se richiesta interruzione da parte dell'utente
        self.richiesta_cancellazione = False        
    
    def avanza(self, p_testo, p_valore):        
        self.progress_label.setText(p_testo)                
        self.setValue(p_valore)        
        # intercetto richiesta di cancellazione
        if self.wasCanceled():
            self.richiesta_cancellazione = True        

    def chiudi(self):
        self.close()

class FirstThread(QThread):
    """
       Thread che avvia il comando Oracle tramite altro thread e che nel ciclo aggiorna avanzamento progressbar
       Riceve in ingresso il cursore Oracle (già aperto), il comando da eseguire ed eventuali bind
    """
    signalStatus = pyqtSignal(str)

    def __init__(self):
        """
           I parametri d'ingresso vengono salvati nell'oggetto, per eseguire istruzione e per restituirli
        """
        super(FirstThread, self).__init__()          
        self.v_fine_lavoro = False          

    def run(self):
        """ 
           Esecuzione del thread...al primo giro viene creato il secondo thread che è quello che effettivamente
           esegue il comando Oracle....questo primo thread si occupa di aggiornare la progressbar
        """    
        app = QApplication(sys.argv)
        v_win = QMainWindow()            
        # creo la classe di progressbar        
        v_avanzamento = avanzamento_infinito_class("sql_editor.gif")                
        # avvio un ciclo infinito
        start_time = datetime.datetime.now()                     
        v_1a_volta = True
        v_counter = 0 
        while not self.v_fine_lavoro:
            # calcolo il tempo trascorso
            elapsed_time = datetime.datetime.now() - start_time        
            
            # se prima volta, avvio il lavoro sul server...
            if v_1a_volta:
                v_1a_volta = False            
                prec_elapsed_seconds = elapsed_time.total_seconds()

            # ogni 2 decimi di secondo, aggiorlo la progress
            if (elapsed_time.total_seconds() - prec_elapsed_seconds) > 0.2:                                 
                minuti, secondi = divmod(elapsed_time.seconds + elapsed_time.days * 86400, 60)                                
                v_counter += 1
                self.signalStatus.emit('UPDATE')
                v_avanzamento.avanza(f"Exec time: {minuti:02}:{secondi:02}", v_counter)                            
                prec_elapsed_seconds = elapsed_time.total_seconds()
                if v_avanzamento.richiesta_cancellazione:                        
                    print('Richiesta interruzione!')
                    self.v_fine_lavoro = True
            
            # attesa di 100 millisecondi per non impegnare troppo la cpu su questo ciclo
            time.sleep(0.1)         
        print('fine thread')

    def cancel_job(self):
        """
           Forza la chiusura esecuzione comando
        """        
        self.v_fine_lavoro=True
        self.quit()        

    def end_of_job(self, status):                
        """
           Lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress
        """
        self.signalStatus.emit(status)

def slot_on_click():
    signalStatus = pyqtSignal(str)

    # definizione del primo thread 
    worker_thread = FirstThread()
    #worker_thread.signalStatus.connect(update_progress)
    # connessione dei segnali
    #QMetaObject.connectSlotsByName(self)
    # lancio del primo thread al cui interno verrà lanciato il secondo thread che esegue il comando vero e proprio
    worker_thread.start()

    print('Avviato thread e ora avvio comando PL-SQL')
        
    # v_result = v_cursor.execute("""begin
    #                                  MW_MAGAZZINI.PREPARA_PRELIEVO_ORDINI('SMI','B1');
    #                                  MW_MAGAZZINI.DISPONIBILE_PRELIEVO_ORDINI('SMI','B1');
    #                             end;""")        

    v_result = v_cursor.execute("""SELECT * FROM VA_OP_DA_VERSARE""")            
    
    print('Fine comando PL-SQL')    
    worker_thread.cancel_job()

# ------------------------------------------------
# TEST APPLICAZIONE BARRA DI AVANZAMENTO INFINITO
# ------------------------------------------------
if __name__ == "__main__":    
    # inizializzo libreria oracle    
    oracle_my_lib.inizializzo_client()                     
    # apro connessione
    v_connection = cx_Oracle.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')                            
    # apro un cursore
    v_cursor = v_connection.cursor()        
    # creo window principale con bottone per richiamare il test
    app = QApplication(sys.argv)
    v_win = QMainWindow()        
    button = QPushButton('Test Oracle', v_win)
    button.clicked.connect(slot_on_click)
    button.resize(100, 30)
    button.move(50, 50)
    v_win.show()    
    sys.exit(app.exec_())        