# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'map_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MapWindow(object):
    def setupUi(self, MapWindow):
        MapWindow.setObjectName("MapWindow")
        MapWindow.resize(259, 664)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/map.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MapWindow.setWindowIcon(icon)
        self.gridLayout_2 = QtWidgets.QGridLayout(MapWindow)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.b_refresh = QtWidgets.QPushButton(MapWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/icons/refresh.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.b_refresh.setIcon(icon1)
        self.b_refresh.setObjectName("b_refresh")
        self.gridLayout_2.addWidget(self.b_refresh, 0, 0, 1, 1)
        self.o_map = QtWidgets.QTableView(MapWindow)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.o_map.setFont(font)
        self.o_map.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.o_map.setAlternatingRowColors(True)
        self.o_map.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.o_map.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.o_map.setSortingEnabled(True)
        self.o_map.setObjectName("o_map")
        self.gridLayout_2.addWidget(self.o_map, 1, 0, 1, 1)

        self.retranslateUi(MapWindow)
        QtCore.QMetaObject.connectSlotsByName(MapWindow)
        MapWindow.setTabOrder(self.b_refresh, self.o_map)

    def retranslateUi(self, MapWindow):
        _translate = QtCore.QCoreApplication.translate
        MapWindow.setWindowTitle(_translate("MapWindow", "Map procedure/function"))
        self.b_refresh.setText(_translate("MapWindow", "Refresh"))
import resource_rc


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MapWindow = QtWidgets.QDialog()
    ui = Ui_MapWindow()
    ui.setupUi(MapWindow)
    MapWindow.show()
    sys.exit(app.exec_())