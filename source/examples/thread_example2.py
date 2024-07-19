import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar
from PyQt5.QtCore import QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot
import time
from PyThreadKiller import PyThreadKiller

def lancio_processo():
    print(f"Thread inizio")
    for i in range(1,5):
        time.sleep(1)
        print(f"{i}")    
    print(f"Thread fine")

class MainWindow(QMainWindow):
    work_requested = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setGeometry(100, 100, 300, 50)
        self.setWindowTitle('QThread Demo')

        # setup widget
        self.widget = QWidget()
        layout = QVBoxLayout()
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)       

        self.etichetta = QLabel(self)
        self.etichetta.setText('')

        self.btn_start = QPushButton('Start', clicked=self.start)
        self.btn_stop = QPushButton('Stop', clicked=self.stop)

        layout.addWidget(self.etichetta)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)

        # show the window
        self.show()

    def start(self):
        self.btn_start.setEnabled(False)                
        self.my_thread = PyThreadKiller(target=lancio_processo)
        self.my_thread.start()        

    def stop(self):      
        self.my_thread.kill()        
        self.btn_start.setEnabled(True)
        self.etichetta.setText('')

    def complete(self, v):
        self.etichetta.setText('Finish!')
        self.btn_start.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())