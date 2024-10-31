# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.13 con libreria pyqt6
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
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Libreria Oracle
import cx_Oracle
# Librerie interne
import oracle_my_lib
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, p_cursor, p_command, p_bind_variables):
        """
           I parametri d'ingresso vengono salvati nell'oggetto, per eseguire istruzione e per restituirli
        """
        super().__init__()
        self._running = True
        self.v_completato = False
        self.v_cursor = p_cursor
        self.v_command = p_command
        self.v_bind_variables = p_bind_variables

    def run(self):
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
            self.finished.emit("END_JOB_OK")
        except cx_Oracle.Error as e:
            self.v_oracle_error, = e.args
            # lavoro terminato con errore --> emetto segnale di fine che verrà dal chiamante
            self.finished.emit("END_JOB_KO")
        for i in range(101):
            if not self._running:
                break
            time.sleep(1)  # Simulazione di un compito lungo
            self.progress.emit(i)
        self.finished.emit()

    def stop(self):
        self._running = False

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


class SendCommandToOracle(QDialog):
    def __init__(self, p_cursor, p_command, p_bind_variables):
        super().__init__()
        self.setWindowTitle("Progress Dialog")
        self.setGeometry(300, 300, 300, 100)

        self.layout = QVBoxLayout()
        self.progressBar = QProgressBar(self)
        self.cancelButton = QPushButton("Cancel", self)

        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)

        self.worker = Worker(p_cursor, p_command, p_bind_variables)
        self.worker.progress.connect(self.progressBar.setValue)
        self.worker.finished.connect(self.close)

        self.cancelButton.clicked.connect(self.stop_task)

        self.worker.start()

    def stop_task(self):
        self.worker.stop()
        self.close()
    
    def get_cursor(self):
        """
           Restituisce il cursore con i risultati (notare come tale cursore venga preso nell'altra classe FirstThread che a sua volta la prenderà da SecondThread)
        """
        return self.worker.get_cursor()

    def get_error(self):
        """
           Restituisce il cursore con i risultati (notare come tale valore venga preso nell'altra classe FirstThread che a sua volta la prenderà da SecondThread)
        """        
        return self.worker.get_error()

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
    v_oracle_executer = SendCommandToOracle(v_cursor, """select * from va_op_da_versare""", v_bind)                                                                    
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
    sys.exit(app.exec())        
