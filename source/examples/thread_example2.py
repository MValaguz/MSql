from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import datetime
import time

class ServerThread(QThread):
    signalStatus = pyqtSignal(str)

    def __init__(self):
        super(ServerThread, self).__init__()  
        print('init')
        self.completato = False

    def run(self):        
        print('invio comando al server')
        time.sleep(10)        
        print('comando al server completato')
        self.completato = True

class WorkerThread(QThread):
    signalStatus = pyqtSignal(str)

    def run(self):
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
                self.server_thread = ServerThread()        
                self.server_thread.start()                
                prec_elapsed_seconds = elapsed_time.total_seconds()
                        
            if round(elapsed_time.total_seconds() - prec_elapsed_seconds) == 1:                                 
                minuti, secondi = divmod(elapsed_time.seconds + elapsed_time.days * 86400, 60)                                
                self.signalStatus.emit(f"Exec time: {minuti:02}:{secondi:02} secs")
                prec_elapsed_seconds = elapsed_time.total_seconds()
                if self.server_thread.completato:
                    v_fine_lavoro = True
            
            # attesa di 100 millisecondi per non impegnare troppo la cpu su questo ciclo
            self.msleep(100)  
        
        # lavoro terminato emetto segnale di fine
        self.signalStatus.emit("END_JOB_OK")

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thread con Barra di Progressione e Label")
        self.setGeometry(100, 100, 400, 100)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)        
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)        
        #self.label_time = QLabel(self)
        # setting text 
        #self.progress_bar.setValue(70)
        

        #self.button_start = QPushButton("Avvia", self)
        self.button_cancel = QPushButton("Annulla", self)

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        #layout.addWidget(self.label_time)
        #layout.addWidget(self.button_start)
        layout.addWidget(self.button_cancel)
        self.setLayout(layout)

        self.worker_thread = WorkerThread()
        self.worker_thread.signalStatus.connect(self.update_progress)

        #self.button_start.clicked.connect(self.start_worker)
        self.button_cancel.clicked.connect(self.cancel_worker)

        #self.start_worker()
        self.worker_thread.start()

    #def start_worker(self):        
        
    def cancel_worker(self):
        self.worker_thread.terminate()
        self.progress_bar.setValue(0)
        self.close()
        #self.label_time.setText("Exec time: 0.00 secs")

    def update_progress(self, status):
        if status == 'END_JOB_OK':
            self.close()
        else:
            if not self.progress_bar.isTextVisible():
                self.progress_bar.setTextVisible(True)        
            v_value = self.progress_bar.value()
            if v_value >= 99:
                v_value = 10
            else:
                v_value += 10
            self.progress_bar.setValue(v_value)
            self.progress_bar.setFormat(status) 
            # setting alignment to centre
            self.progress_bar.setAlignment(Qt.AlignCenter)
            #self.label_time.setText(status)        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
