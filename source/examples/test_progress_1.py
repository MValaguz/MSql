# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 10/08/2024
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
import resource_rc
# Libreria Oracle
import cx_Oracle
# Librerie interne
import oracle_my_lib

class ClassAvanzamento(QDialog):
    """
       Questa classe visualizza una dialog con una progressbar di avanzamento lavoro e lancia il comando Oracle 
       ricevuto in input. Questo meccanismo avviene tramite utilizzo dei thread (due nello specifico) che 
       comunicano tra loro tramite segnali.
    """
    signalStatus = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # definizione layout della finestra di dialogo
        self.setWindowTitle("...please wait...")    
        self.resize(320, 81)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/icons/icons/MSql.ico"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)
        self.gridLayout = QGridLayout(self)        
        # progressbar (il testo è invisibile all'inizio per questioni estetiche ma poi diventerà visibile)
        self.progressbar = QProgressBar(self)        
        self.progressbar.setTextVisible(False)        
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)    
        self.gridLayout.addWidget(self.progressbar, 0, 0, 1, 1)
        # zona del bottone di interruzione dell'operazione
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)        
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)        
        # definizione del segnale di interruzione
        self.buttonBox.rejected.connect(self.cancel_worker) # type: ignore                
        
    def cancel_worker(self):
        """ 
           L'utente ha richiesto la cancellazione dell'operazione....
        """
        # lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress        
        self.signalStatus.emit('CANCEL_JOB') 

    def update_progress(self, status):
        """
           Si riceve il segnale di aggiornamento dell'interfaccia (o un segnale di fine lavoro)...
           la progressbar viene aggiornata nel tempo di esecuzione.
           Se il segnale contiene END_JOB_xx viene emesso e reinviato all'esterno!
        """        
        if not self.progressbar.isTextVisible():
            self.progressbar.setTextVisible(True)        
        v_value = self.progressbar.value()
        if v_value >= 99:
            v_value = 20
        else:
            v_value += 20
        print('valore progress ' + str(v_value))    
        self.progressbar.setValue(v_value)
        self.progressbar.setFormat(status)             
        self.progressbar.setAlignment(Qt.AlignCenter)           

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

    def run(self):
        """ 
           Esecuzione del thread...al primo giro viene creato il secondo thread che è quello che effettivamente
           esegue il comando Oracle....questo primo thread si occupa di aggiornare la progressbar
        """
        # inizio lavoro
        start_time = datetime.datetime.now()             
        v_1a_volta = True
        v_fine_lavoro = False
        # avvio un ciclo infinito
        while not v_fine_lavoro:
            # calcolo il tempo trascorso
            elapsed_time = datetime.datetime.now() - start_time        
            
            # se prima volta, avvio il lavoro sul server...
            if v_1a_volta:
                v_1a_volta = False
                self.avanzamento = ClassAvanzamento()                
                prec_elapsed_seconds = elapsed_time.total_seconds()

            # se è trascorso un secondo emetto segnale per aggiorare la progressbar
            if round(elapsed_time.total_seconds() - prec_elapsed_seconds) == 1:                                 
                minuti, secondi = divmod(elapsed_time.seconds + elapsed_time.days * 86400, 60)                                
                self.avanzamento.update_progress(f"Exec time: {minuti:02}:{secondi:02}")                
                print(f"Exec time: {minuti:02}:{secondi:02}")
                prec_elapsed_seconds = elapsed_time.total_seconds()
                #if self.server_thread.v_completato:                             
                #    v_fine_lavoro = True
            
            # attesa di 100 millisecondi per non impegnare troppo la cpu su questo ciclo
            self.msleep(100)  
            
    def cancel_job(self):
        """
           Forza la chiusura esecuzione comando
        """        
        self.terminate()        

    def end_of_job(self, status):                
        """
           Lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress
        """
        self.signalStatus.emit(status)


# ------------------------------------------------
# TEST APPLICAZIONE ESECUZIONE COMANDO ORACLE
# Il test produce un output sulla console!
# ------------------------------------------------

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

    print('Fine comando PL-SQL')

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