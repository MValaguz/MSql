# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt5
 Data..........: 10/08/2024
 Descrizione...: Classe per l'esecuzione di un comando SQL/PL-SQL dove viene presentata una progressbar di avanzamento e viene 
                 permessa l'interruzione del comando....il tutto avviene tramite utilizzo dei thread.
                 La classe riceve in input sia l'istruzione che un oggetto cursore oracle già inizializzato.
 Note..........: Come funziona? La classe di riferimento è SendCommandToOracle la quale crea la window con la progressbar.
                 Dentro in questa classe viene creato un primo thread che ha il compito ogni 100millisecondi di aggiornare la progressbar di avanzamento.
                 Dentro in questo thread viene creato un secondo thread che si occupa di lanciare il comando Oracle.
                 Il tutto viene gestito tramite segnali tra una classe e l'altra.
                 Quando il lavoro è terminato un segnale di END_JOB_OK viene emesso verso l'alto tra una classe e l'altra e tramite il metodo get_cursor si accede
                 al cursore restituito da Oracle. Se il comando oracle ha dato errore, viene emesso comunque un segnale di END_JOB_KO (KO!) e tramite il 
                 metodo get_error si accede alla struttura di errore.
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

class SecondThread(QThread):
    """
       Invio del comando a Oracle
       Riceve in ingresso il cursore Oracle (già aperto), il comando da eseguire e eventuale lista delle bind 
    """
    signalStatus = pyqtSignal(str)

    def __init__(self, p_cursor, p_command, p_bind_variables):
        super(SecondThread, self).__init__()          
        """
           I parametri d'ingresso vengono salvati nell'oggetto, per eseguire istruzione e per restituirli
        """
        self.v_completato = False
        self.v_cursor = p_cursor
        self.v_command = p_command
        self.v_bind_variables = p_bind_variables

    def run(self):                        
        """
           Esecuzione del thread e quindi del comando Oracle
        """
        try:
            # _______  _______ ____     ___  ____      _    ____ _     _____ 
            # | ____\ \/ / ____/ ___|  / _ \|  _ \    / \  / ___| |   | ____|
            # |  _|  \  /|  _|| |     | | | | |_) |  / _ \| |   | |   |  _|  
            # | |___ /  \| |__| |___  | |_| |  _ <  / ___ \ |___| |___| |___ 
            # |_____/_/\_\_____\____|  \___/|_| \_\/_/   \_\____|_____|_____|                                                                        
            #   ____ ___  __  __ __  __    _    _   _ ____  
            #  / ___/ _ \|  \/  |  \/  |  / \  | \ | |  _ \ 
            # | |  | | | | |\/| | |\/| | / _ \ |  \| | | | |
            # | |__| |_| | |  | | |  | |/ ___ \| |\  | |_| |
            #  \____\___/|_|  |_|_|  |_/_/   \_\_| \_|____/                                                         
            self.v_cursor.execute(self.v_command,self.v_bind_variables)                
            # lavoro terminato ok --> emetto segnale di fine che verrà dal chiamante
            self.signalStatus.emit("END_JOB_OK")
        except cx_Oracle.Error as e:
            self.v_oracle_error, = e.args
            # lavoro terminato con errore --> emetto segnale di fine che verrà dal chiamante
            self.signalStatus.emit("END_JOB_KO")
        self.v_completato = True        

    def get_cursor(self):
        """
           Restituisce il cursore con i risultati
        """
        return self.v_cursor
    
    def get_error(self):
        """
           Restituisce oggetto errore
        """
        return self.v_oracle_error

    def cancel_job(self):
        """
           Interrompe il comando Oracle
        """                
        self.quit()

class FirstThread(QThread):
    """
       Thread che avvia il comando Oracle tramite altro thread e che nel ciclo aggiorna avanzamento progressbar
       Riceve in ingresso il cursore Oracle (già aperto), il comando da eseguire ed eventuali bind
    """
    signalStatus = pyqtSignal(str)

    def __init__(self, p_cursor, p_command, p_bind_variables):
        """
           I parametri d'ingresso vengono salvati nell'oggetto, per eseguire istruzione e per restituirli
        """
        super(FirstThread, self).__init__()          
        self.v_cursor = p_cursor
        self.v_command = p_command
        self.v_bind_variables = p_bind_variables

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
                self.server_thread = SecondThread(self.v_cursor, self.v_command, self.v_bind_variables)        
                self.server_thread.signalStatus.connect(self.end_of_job)
                self.server_thread.start()                
                prec_elapsed_seconds = elapsed_time.total_seconds()
                        
            # se è trascorso un secondo emetto segnale per aggiorare la progressbar
            if round(elapsed_time.total_seconds() - prec_elapsed_seconds) == 1:                                 
                minuti, secondi = divmod(elapsed_time.seconds + elapsed_time.days * 86400, 60)                                
                self.signalStatus.emit(f"Exec time: {minuti:02}:{secondi:02}")
                prec_elapsed_seconds = elapsed_time.total_seconds()
                if self.server_thread.v_completato:                             
                    v_fine_lavoro = True
            
            # attesa di 100 millisecondi per non impegnare troppo la cpu su questo ciclo
            self.msleep(100)  
            
    def get_cursor(self):
        """
           Restituisce il cursore con i risultati (notare come tale cursore venga preso nell'altra classe SecondThread)
        """
        return self.server_thread.get_cursor()           

    def get_error(self):
        """
           Restituisce il cursore con i risultati (notare come tale valore venga preso nell'altra classe SecondThread)
        """
        return self.server_thread.get_error()           

    def cancel_job(self):
        """
           Forza la chiusura esecuzione comando
        """
        self.server_thread.cancel_job()
        self.quit()        

    def end_of_job(self, status):                
        """
           Lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress
        """
        self.signalStatus.emit(status)

class SendCommandToOracle(QDialog):
    """
       Questa classe visualizza una dialog con una progressbar di avanzamento lavoro e lancia il comando Oracle 
       ricevuto in input. Questo meccanismo avviene tramite utilizzo dei thread (due nello specifico) che 
       comunicano tra loro tramite segnali.
    """
    signalStatus = pyqtSignal(str)

    def __init__(self, p_cursor, p_command, p_bind_variables):
        super().__init__()
        # definizione layout della finestra di dialogo
        self.setModal(True)
        self.v_status = ''
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
        # definizione del primo thread 
        self.worker_thread = FirstThread(p_cursor,p_command,p_bind_variables)
        self.worker_thread.signalStatus.connect(self.update_progress)
        # connessione dei segnali
        QMetaObject.connectSlotsByName(self)

    def start(self):
        """
           Avvia la progress con esecuzione del comando....e rimane in attesa fino a che non termina!
        """
        # lancio del primo thread al cui interno verrà lanciato il secondo thread che esegue il comando vero e proprio
        self.worker_thread.start()
        # ciclo di visualizzazione
        self.show()   

        # mi metto in attesa della fine del comando inviato a Oracle...questo perché non voglio accettare altri eventi nel frattempo se non la fine del comando
        v_loop = QEventLoop()
        self.signalStatus.connect(v_loop.quit)  # Aspetto l'evento che mi restituisce l'executer
        v_loop.exec_()  # Entra nel ciclo di attesa                        
        
    def cancel_worker(self):
        """ 
           L'utente ha richiesto la cancellazione dell'operazione....
        """
        # lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress
        self.worker_thread.cancel_job()
        self.v_status = 'CANCEL_JOB'
        self.signalStatus.emit('CANCEL_JOB') 

    def update_progress(self, status):
        """
           Si riceve il segnale di aggiornamento dell'interfaccia (o un segnale di fine lavoro)...
           la progressbar viene aggiornata nel tempo di esecuzione.
           Se il segnale contiene END_JOB_xx viene emesso e reinviato all'esterno!
        """
        if status in ('END_JOB_OK','END_JOB_KO'):
            self.v_status = status
            # lavoro terminato emetto segnale di fine che verrà catturato dalla funzione progress
            self.signalStatus.emit(status) 
        else:
            # lavoro non terminato --> faccio avanzare la progressbar
            if not self.progressbar.isTextVisible():
                self.progressbar.setTextVisible(True)        
            v_value = self.progressbar.value()
            if v_value >= 99:
                v_value = 20
            else:
                v_value += 20
            self.progressbar.setValue(v_value)
            self.progressbar.setFormat(status)             
            self.progressbar.setAlignment(Qt.AlignCenter)           

    def get_cursor(self):
        """
           Restituisce il cursore con i risultati (notare come tale cursore venga preso nell'altra classe FirstThread che a sua volta la prenderà da SecondThread)
        """
        return self.worker_thread.get_cursor()

    def get_error(self):
        """
           Restituisce il cursore con i risultati (notare come tale valore venga preso nell'altra classe FirstThread che a sua volta la prenderà da SecondThread)
        """        
        return self.worker_thread.get_error()

    def get_status(self):
        """
           Restituisce il valore della var status
        """
        return self.v_status

# ------------------------------------------------
# TEST APPLICAZIONE ESECUZIONE COMANDO ORACLE
# Il test produce un output sulla console!
# ------------------------------------------------
def slot_on_click():
    def endCommandToOracle(status):
        """
        Quando il comando Oracle è stato terminato viene richiamata
        questa funzione tramite segnale.
        Se tutto ok, visualizzo il risultato, altrimenti il messaggio di errore!
        """
        if status == 'CANCEL_JOB':                        
            print('Annullato!')            
            v_connection.cancel()                                                            

        elif status == 'END_JOB_OK':
            v_cursor = v_oracle_executer.get_cursor()    
            v_matrice = v_cursor.fetchall()
            """
            for row in v_matrice:
                print(row)    
            """
            # chiudo la progressbar
            v_oracle_executer.close()
        
        elif status == 'END_JOB_KO':
            v_oracle_error = v_oracle_executer.get_error()                    
            print(v_oracle_error.message)    
            # chiudo la progressbar
            v_oracle_executer.close()    
    
    v_bind = []
    # esecuzione della funzione con creazione della classe ed esecuzione della medesima
    # in questo modo le classi di thread vedono i parametri ricevuti in input e la dialog blocca 
    # tutto il programma fino al termine del thread principale    
    # v_oracle_executer = SendCommandToOracle(v_cursor, """begin
    #                                                      MW_MAGAZZINI.PREPARA_PRELIEVO_ORDINI('SMI','B1');
    #                                                      MW_MAGAZZINI.DISPONIBILE_PRELIEVO_ORDINI('SMI','B1');
    #                                                     end;""", v_bind)        
    #v_oracle_executer = SendCommandToOracle(v_cursor, """select * from va_op_da_versare""", v_bind)                                                                
    v_oracle_executer = SendCommandToOracle(v_cursor, """select * from dual""", v_bind)                                                                    
    v_oracle_executer.signalStatus.connect(endCommandToOracle)    
    v_oracle_executer.start()
    
    print('fine')

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
    button.setShortcut("F5")
    button.clicked.connect(slot_on_click)
    button.resize(100, 30)
    button.move(50, 50)
    v_win.show()    
    sys.exit(app.exec_())        