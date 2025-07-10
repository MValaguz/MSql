#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13 con libreria pyqt6
#  Data..........: 30/06/2025
#  Descrizione...: Classe per l'esecuzione di un comando SQL/PL-SQL dove viene presentata una progressbar di avanzamento e viene 
#                  permessa l'interruzione del comando....il tutto avviene tramite utilizzo dei thread.
#                  La classe riceve in input sia l'istruzione che un oggetto cursore oracle già inizializzato.
#  Note..........: Come funziona? La classe di riferimento è SendCommandToOracle la quale crea la window con la progressbar.
#                  Dentro in questa classe viene creato un thread tramite la classe OracleWorker che lancia il comando Oracle vero e proprio.
#                  Quando il lavoro è terminato un segnale di END_JOB_OK viene emesso verso l'alto tra una classe e l'altra e tramite il metodo get_cursor si accede
#                  al cursore restituito da Oracle. Se il comando oracle ha dato errore, viene emesso comunque un segnale di END_JOB_KO (KO!) e tramite il 
#                  metodo get_error si accede alla struttura di errore.
#  Note..........: Questo oggetto ha avuto diverse versioni di sviluppo di cui ultima è stata riscritta tramite CoPilot, partendo da una versione dove i thread erano 2
#                  Onestamente...alcune logiche di questa versione mi sono sconosciute!

# Librerie di sistema
import sys
import datetime
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
# Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Libreria Oracle
import oracledb
# Librerie interne
import oracle_my_lib
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

class OracleWorker(QObject):
    """
       Invio del comando a Oracle
       Riceve in ingresso il cursore Oracle (già aperto), il comando da eseguire e eventuale lista delle bind 
    """
    finished = pyqtSignal(bool)     # True=OK, False=KO
    error    = pyqtSignal(object)   # emettiamo direttamente e.args

    def __init__(self, connection, cursor, command, bind_vars):
        """
           I parametri d'ingresso vengono salvati nell'oggetto, per eseguire istruzione e per restituirli
        """
        super().__init__()
        self._conn     = connection
        self._cur      = cursor
        self._cmd      = command
        self._binds    = bind_vars
        self._canceled = False

    @pyqtSlot()
    def doWork(self):
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
            if self._canceled:
                raise oracledb.DatabaseError("Operazione cancellata")
            self._cur.execute(self._cmd, self._binds)
            if self._canceled:
                raise oracledb.DatabaseError("Operazione cancellata")
            self.finished.emit(True)
        except oracledb.Error as e:
            v_oracle_error, = e.args
            self.error.emit(v_oracle_error)

    def cancel(self):
        """
           Interrompe il comando Oracle
        """     
        self._canceled = True
        try:
            self._conn.cancel()
        except Exception:
            pass

    def get_cursor(self):
        """
           Restituisce il cursore con i risultati
        """
        return self._cur

class SendCommandToOracle(QDialog):
    """
       Questa classe visualizza una dialog con una progressbar di avanzamento lavoro e lancia il comando Oracle 
       ricevuto in input. Questo meccanismo avviene tramite utilizzo dei thread (due nello specifico) che 
       comunicano tra loro tramite segnali.
       p_parent_geometry contiene le informazioni della dimensione della window chiamante
    """
    def __init__(self, conn, cursor, cmd, binds,
                 parent_geometry, anim_gif=''):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle("…please wait…")
        self.resize(200, 80)

        # inizializzo status & error
        self._status = None
        self._error  = None

        # icona
        self.setWindowIcon(QIcon("icons:MSql.ico"))

        # gif animata
        self.gears = QLabel(self)
        self.movie = QMovie(anim_gif or "icons:anim_wait1.gif")
        self.movie.frameChanged.connect(self._update_movie_frame)
        self.gears.setMovie(self.movie)
        self.movie.start()

        # label timer
        self.label_time = QLabel("Exec time: 00:00:00", self)

        # bottone Cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.buttonBox.rejected.connect(self._on_cancel)

        # layout 
        layout = QGridLayout(self)
        layout.addWidget(self.gears,      0, 0)
        layout.addWidget(self.label_time, 0, 1)
        layout.addWidget(self.buttonBox,  1, 1)

        # centriamo sul parent
        pc = parent_geometry.center()
        fg = self.frameGeometry()
        fg.moveCenter(pc)
        self.move(fg.topLeft())

        # preparo il worker in un suo thread
        self.worker = OracleWorker(conn, cursor, cmd, binds)
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.doWork)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)

        # timer per l’orologio di avanzamento
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_elapsed)

    def start(self):
        """
           Avvia thread + timer, forza subito l'update, poi exec()
        """
        # 1) imposto il punto di partenza del contatore
        self.start_time = QDateTime.currentDateTime()

        # 2) lancio il thread e il timer
        self.thread.start()
        self.timer.start()

        # 3) forzo subito il primo aggiornamento
        self._update_elapsed()

        # 4) mostro il dialog e resto in attesa di accept()/reject()
        return self.exec()

    def _update_movie_frame(self):
        pix    = self.movie.currentPixmap()
        scaled = pix.scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.gears.setPixmap(scaled)

    def _update_elapsed(self):
        secs = self.start_time.secsTo(QDateTime.currentDateTime())
        h, r = divmod(secs, 3600)
        m, s = divmod(r, 60)
        self.label_time.setText(f"Exec time: {h:02}:{m:02}:{s:02}")

    def _on_finished(self, ok: bool):
        """
           Chiusura ordinaria
        """
        self.timer.stop()
        self.thread.quit()
        self.thread.wait()

        if ok:
            self._status = "END_JOB_OK"
            self.accept()
        else:
            self._status = "END_JOB_KO"
            QMessageBox.warning(self, "Avviso", "Comando terminato con warning.")
            self.accept()

    def _on_error(self, error_args: object):
        """
           Gestione errore Oracle
        """
        self.timer.stop()
        self.thread.quit()
        self.thread.wait()

        self._status = "END_JOB_KO"
        self._error  = error_args
        self.reject()

    def _on_cancel(self):
        """
           L'utente ha cliccato Cancel
        """
        self.worker.cancel()
        # rimaniamo in exec() finché non arriva finished/error

    def get_status(self) -> str:
        """
           Ritorna 'END_JOB_OK' o 'END_JOB_KO'
        """
        return self._status
        
    def get_cursor(self):
        """
           Ritorna 'END_JOB_OK' o 'END_JOB_KO'
        """
        return self.worker.get_cursor()

    def get_error(self) -> object:
        """
           Se lo status è KO, restituisce e.args di oracledb.Error
        """
        return self._error

# ------------------------------------------------
# TEST APPLICAZIONE ESECUZIONE COMANDO ORACLE
# Il test produce un output sulla console!
# ------------------------------------------------
def slot_on_click():
    v_bind = []
    # esecuzione della funzione con creazione della classe ed esecuzione della medesima
    # in questo modo le classi di thread vedono i parametri ricevuti in input e la dialog blocca 
    # tutto il programma fino al termine del thread principale    
    for i in range(1,2):
        v_oracle_executer = SendCommandToOracle(v_connection, v_cursor, """select * from va_op_da_versare""", v_bind, v_win.frameGeometry())                                                                
        v_oracle_executer.start()        
        print(v_oracle_executer.get_status())
        if v_oracle_executer.get_status() == 'END_JOB_KO':
            print(v_oracle_executer.get_error())

if __name__ == "__main__":    
    # inizializzo libreria oracle    
    oracle_my_lib.inizializzo_client()                     
    # apro connessione
    v_connection = oracledb.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')                            
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