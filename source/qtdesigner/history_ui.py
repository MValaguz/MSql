# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'history_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_history_window(object):
    def setupUi(self, history_window):
        history_window.setObjectName("history_window")
        history_window.resize(692, 775)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/MSql.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        history_window.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(history_window)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.l_label6 = QtWidgets.QLabel(self.centralwidget)
        self.l_label6.setObjectName("l_label6")
        self.horizontalLayout.addWidget(self.l_label6)
        self.e_where_cond = QtWidgets.QTextEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.e_where_cond.sizePolicy().hasHeightForWidth())
        self.e_where_cond.setSizePolicy(sizePolicy)
        self.e_where_cond.setMaximumSize(QtCore.QSize(16777215, 50))
        self.e_where_cond.setObjectName("e_where_cond")
        self.horizontalLayout.addWidget(self.e_where_cond)
        self.b_start = QtWidgets.QPushButton(self.centralwidget)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/go.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.b_start.setIcon(icon1)
        self.b_start.setObjectName("b_start")
        self.horizontalLayout.addWidget(self.b_start)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.o_lst1 = QtWidgets.QTableView(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.o_lst1.setFont(font)
        self.o_lst1.setAlternatingRowColors(True)
        self.o_lst1.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.o_lst1.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.o_lst1.setObjectName("o_lst1")
        self.gridLayout.addWidget(self.o_lst1, 2, 0, 1, 1)
        self.b_purge = QtWidgets.QPushButton(self.centralwidget)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/icons/failed.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.b_purge.setIcon(icon2)
        self.b_purge.setObjectName("b_purge")
        self.gridLayout.addWidget(self.b_purge, 3, 0, 1, 1)
        history_window.setCentralWidget(self.centralwidget)
        self.l_label6.setBuddy(self.e_where_cond)
        self.label.setBuddy(self.o_lst1)

        self.retranslateUi(history_window)
        self.b_start.clicked.connect(history_window.slot_start) # type: ignore
        self.b_purge.clicked.connect(history_window.slot_purge) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(history_window)

    def retranslateUi(self, history_window):
        _translate = QtCore.QCoreApplication.translate
        history_window.setWindowTitle(_translate("history_window", "History"))
        self.l_label6.setText(_translate("history_window", "Where condition (ex. INSTRUCTION like \'%VALUE%\'):"))
        self.b_start.setText(_translate("history_window", "Search"))
        self.label.setText(_translate("history_window", "Result (double click to import instruction into current editor:"))
        self.b_purge.setText(_translate("history_window", "Delete history"))
import resource_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    history_window = QtWidgets.QMainWindow()
    ui = Ui_history_window()
    ui.setupUi(history_window)
    history_window.show()
    sys.exit(app.exec_())