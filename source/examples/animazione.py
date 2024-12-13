import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QMovie

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GIF Animata con PyQt6")
        self.setGeometry(200, 200, 400, 400)

        self.label = QLabel(self)
        self.label.setGeometry(50, 50, 300, 300)        

        # Carica la GIF animata
        self.movie = QMovie("gears.gif")
        
        # Imposta la GIF animata nel QLabel
        self.label.setMovie(self.movie)
        
        # Avvia l'animazione
        self.movie.start()

print("La directory corrente è:", os.getcwd())
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
