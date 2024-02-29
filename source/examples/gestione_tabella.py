import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inserimento dati in SQLite")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.label_nome = QLabel("Nome:")
        self.line_edit_nome = QLineEdit()

        self.label_sql = QLabel("SQL:")
        self.line_edit_sql = QLineEdit()

        self.label_data = QLabel("Data:")
        self.line_edit_data = QLineEdit()

        self.button_inserisci = QPushButton("Inserisci")
        self.button_inserisci.clicked.connect(self.inserisci_dati)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["NOME", "SQL", "DATA"])

        self.layout.addWidget(self.label_nome)
        self.layout.addWidget(self.line_edit_nome)
        self.layout.addWidget(self.label_sql)
        self.layout.addWidget(self.line_edit_sql)
        self.layout.addWidget(self.label_data)
        self.layout.addWidget(self.line_edit_data)
        self.layout.addWidget(self.button_inserisci)
        self.layout.addWidget(self.table_widget)

        self.central_widget.setLayout(self.layout)

        self.conn = sqlite3.connect("pc_sql_preferred.db")
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS pc_sql_preferred
                          (NOME TEXT, SQL TEXT, DATA TEXT)''')
        self.conn.commit()

    def inserisci_dati(self):
        nome = self.line_edit_nome.text()
        sql = self.line_edit_sql.text()
        data = self.line_edit_data.text()

        self.c.execute("INSERT INTO pc_sql_preferred VALUES (?, ?, ?)", (nome, sql, data))
        self.conn.commit()

        self.aggiorna_tabella()

    def aggiorna_tabella(self):
        self.table_widget.setRowCount(0)
        self.c.execute("SELECT * FROM pc_sql_preferred")
        for row_number, row_data in enumerate(self.c.fetchall()):
            self.table_widget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table_widget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
