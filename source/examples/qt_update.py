import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton, QVBoxLayout, QWidget

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Inizializza la connessione al database SQLite
        self.conn = sqlite3.connect("my_database.db")
        self.c = self.conn.cursor()

        # Crea la tabella se non esiste già
        self.c.execute('''CREATE TABLE IF NOT EXISTS my_table (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, sql TEXT, data TEXT)''')
        self.conn.commit()

        # Crea la finestra principale
        self.setWindowTitle("Griglia con PyQt5 e SQLite")
        self.setGeometry(100, 100, 800, 600)

        # Crea il QTableWidget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["NOME", "SQL", "DATA"])

        # Aggiungi pulsanti per inserire e aggiornare i dati
        self.insert_button = QPushButton("Inserisci")
        self.update_button = QPushButton("Aggiorna")
        self.insert_button.clicked.connect(self.insert_data)
        self.update_button.clicked.connect(self.update_data)

        # Layout verticale per i widget
        layout = QVBoxLayout()
        layout.addWidget(self.tableWidget)
        layout.addWidget(self.insert_button)
        layout.addWidget(self.update_button)

        # Widget principale
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Carica i dati dal database nella griglia
        self.load_data()

    def load_data(self):
        self.tableWidget.setRowCount(0)
        self.c.execute('''SELECT * FROM my_table''')
        rows = self.c.fetchall()
        for row in rows:
            inx = rows.index(row)
            self.tableWidget.insertRow(inx)
            self.tableWidget.setItem(inx, 0, QTableWidgetItem(row[1]))
            self.tableWidget.setItem(inx, 1, QTableWidgetItem(row[2]))
            self.tableWidget.setItem(inx, 2, QTableWidgetItem(row[3]))

    def insert_data(self):
        nome = "Nuovo Nome"
        sql = "Nuovo SQL"
        data = "Nuova Data"
        self.c.execute('''INSERT INTO my_table (nome, sql, data) VALUES (?, ?, ?)''', (nome, sql, data))
        self.conn.commit()
        self.load_data()

    def update_data(self):
        selected_row = self.tableWidget.currentRow()
        if selected_row >= 0:
            nome = self.tableWidget.item(selected_row, 0).text()
            sql = self.tableWidget.item(selected_row, 1).text()
            data = self.tableWidget.item(selected_row, 2).text()
            self.c.execute('''UPDATE my_table SET nome=?, sql=?, data=? WHERE id=?''', (nome, sql, data, selected_row + 1))
            self.conn.commit()
            self.load_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
