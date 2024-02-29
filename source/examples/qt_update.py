# Ignore lazy imports
import sys
from typing import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
from PyQt5.QtWidgets import *

def createTable() -> QTableWidget:
    """Let's create a QTableWidget with the data you provided."""
    data = [
        ("Joe", "Senior Web Developer", "joe@example.com"),
        ("Lara", "Project Manager", "lara@example.com"),
        ("David", "Data Analyst", "david@example.com"),
        ("Jane", "Senior Python Developer", "jane@example.com"),
    ]
    table = QTableWidget()
    table.setRowCount(len(data))
    table.setColumnCount(len(data[0]))
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            table.setItem(i, j, QTableWidgetItem(val))
    return table


def getData(table: QTableWidget) -> List[Tuple[str]]:
    """Fetch the data from the QTableWidget and return it as `data`."""
    data = []
    for row in range(table.rowCount()):
        rowData = []
        for col in range(table.columnCount()):
            rowData.append(table.item(row, col).data(Qt.EditRole))
        data.append(tuple(rowData))
    return data

def insertData(data: List[Tuple[str]]) -> None:
    """Creating a query for later execution using .prepare()"""
    insertDataQuery = QSqlQuery()
    insertDataQuery.prepare(
        """
        INSERT INTO contacts (
            name,
            job,
            email
        )
        VALUES (?, ?, ?)
        """
    )
    # Use .addBindValue() to insert data
    for name, job, email in data:
        insertDataQuery.addBindValue(name)
        insertDataQuery.addBindValue(job)
        insertDataQuery.addBindValue(email)
        insertDataQuery.exec_()
    # Note that you need to run `QSqlDatabase().commit()`` if you want the data to be committed in the database.  

app = QApplication([sys.argv])
# Connect to sample database
sampleDb = QSqlDatabase.addDatabase("QSQLITE")
sampleDb.setDatabaseName("sample.sqlite")
sampleDb.open()
# Create table with sample data
table = createTable()
# Get data from table
data = getData(table)
# Insert data into the database
insertData(data)
sys.exit(app.exec_())	