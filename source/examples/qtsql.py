# Write Python3 code here
import sys
from PyQt5.QtCore import * 
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        # Setting mainwindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(432, 813)
        MainWindow.setMinimumSize(QSize(432, 813))
        MainWindow.setMaximumSize(QSize(432, 813))

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.frame = QFrame(self.centralwidget)
        self.frame.setGeometry(QRect(0, 0, 781, 821))

        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setObjectName("frame")

        # setting up the output table
        self.tableWidget = QTableWidget(self.frame)
        self.tableWidget.setGeometry(QRect(0, 10, 431, 731))
        self.tableWidget.setRowCount(10)
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName("tableWidget")

        # initializing items to be added in the table
        item = QTableWidgetItem()
        item1 = QTableWidgetItem()
        # inserting above items to the table
        self.tableWidget.setHorizontalHeaderItem(0, item)
        self.tableWidget.setHorizontalHeaderItem(1, item1)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(185)
        self.tableWidget.verticalHeader().setMinimumSectionSize(50)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

        # connection to the database
        self.QSqlDatabase.addDatabase("QMYSQL")
        self.db.setHostName("geeksforgeeks")
        self.db.setDatabaseName("gfgdb")
        self.db.setUserName("geeks")
        self.db.setPassword("gfg")
        # executing MySql query
        self.qry = QString("SELECT * FROM employee")
        self.query = QSqlQuery()
        self.query.prepare(self.qry)
        self.query.exec()

        # displaying output of query in the table
        for row_number, row_data in enumerate(self.query.result()):
            for column_number, data in enumerate(row_data):
                self.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(data))
                
    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "List of All Employee(GFGdb)"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "NAME"))
        item1 = self.tableWidget.horizontalHeaderItem(1)
        item1.setText(_translate("MainWindow", "SALARY"))


if __name__ == "__main__":	
    import sys
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
