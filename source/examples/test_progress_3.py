import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QProgressDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class MyThread(QThread):
    def run(self):
        # Simulate some work
        for i in range(101):
            self.msleep(50)
            self.progress.emit(i)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QProgressDialog Example")
        self.setGeometry(100, 100, 400, 200)

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_thread)
        self.setCentralWidget(self.start_button)

    def start_thread(self):
        self.thread = MyThread(self)
        self.thread.progress = pyqtSignal(int)
        self.thread.progress.connect(self.update_progress)
        self.thread.start()

    def update_progress(self, value):
        progress_dialog = QProgressDialog("Working...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setValue(value)
        if progress_dialog.wasCanceled():
            self.thread.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
