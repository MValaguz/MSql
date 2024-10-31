import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, QProgressBar
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

"""
In questa versione, utilizziamo QTimer per eseguire periodicamente il compito senza bloccare l'interfaccia utente. do_work viene chiamato ogni secondo, aggiornando la ProgressBar e simulando un lavoro lungo. Questo assicura che la ProgressBar continui ad aggiornarsi regolarmente.
"""

class Worker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.counter = 0
        self._running = True

    def start_work(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.do_work)
        self.timer.start(1000)  # Esegue ogni secondo

    def do_work(self):
        if self._running and self.counter <= 100:
            self.progress.emit(self.counter)
            self.counter += 1
        else:
            self.timer.stop()
            self.finished.emit()

    def stop(self):
        self._running = False

class ProgressDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Dialog")
        self.setGeometry(300, 300, 300, 100)

        self.layout = QVBoxLayout()
        self.progressBar = QProgressBar(self)
        self.cancelButton = QPushButton("Cancel", self)

        self.layout.addWidget(self.progressBar)
        self.layout.addWidget(self.cancelButton)
        self.setLayout(self.layout)

        self.worker = Worker()
        self.worker.progress.connect(self.progressBar.setValue)
        self.worker.finished.connect(self.close)

        self.cancelButton.clicked.connect(self.stop_task)

        self.worker.start_work()

    def stop_task(self):
        self.worker.stop()
        self.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, 400, 200)

        self.openButton = QPushButton("Open Progress Dialog", self)
        self.openButton.setGeometry(150, 80, 100, 30)
        self.openButton.clicked.connect(self.open_progress_dialog)

    def open_progress_dialog(self):
        self.progressDialog = ProgressDialog()
        self.progressDialog.exec()

app = QApplication(sys.argv)
mainWindow = MainWindow()
mainWindow.show()
sys.exit(app.exec())
