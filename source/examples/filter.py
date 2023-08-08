import csv
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Widget(QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent=parent)
        self.verticalLayout = QVBoxLayout(self)
        self.filterall = QTableWidget(self)
        self.filterall.setColumnCount(0)
        self.filterall.setRowCount(0)
        self.verticalLayout.addWidget(self.filterall)

        self.loadAll()
        self.horizontalHeader = self.filterall.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(self.on_view_horizontalHeader_sectionClicked)
        self.keywords = dict([(i, []) for i in range(self.filterall.columnCount())])
        self.checkBoxs = []
        self.col = None

    def slotSelect(self, state):

        for checkbox in self.checkBoxs:
            checkbox.setChecked(QtCore.Qt.Checked == state)

    def on_view_horizontalHeader_sectionClicked(self, index):
        # self.clearFilter()
        self.menu = QMenu(self)
        self.col = index

        data_unique = []

        self.checkBoxs = []

        checkBox = QCheckBox("Select all", self.menu)
        checkableAction = QWidgetAction(self.menu)
        checkableAction.setDefaultWidget(checkBox)
        self.menu.addAction(checkableAction)
        checkBox.setChecked(True)
        checkBox.stateChanged.connect(self.slotSelect)

        for i in range(self.filterall.rowCount()):
            if not self.filterall.isRowHidden(i):
                item = self.filterall.item(i, index)
                if item.text() not in data_unique:
                    data_unique.append(item.text())
                    checkBox = QCheckBox(item.text(), self.menu)
                    checkBox.setChecked(True)
                    checkableAction = QWidgetAction(self.menu)
                    checkableAction.setDefaultWidget(checkBox)
                    self.menu.addAction(checkableAction)
                    self.checkBoxs.append(checkBox)

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self.menu)
        btn.accepted.connect(self.menuClose)
        btn.rejected.connect(self.menu.close)
        checkableAction = QWidgetAction(self.menu)
        checkableAction.setDefaultWidget(btn)
        self.menu.addAction(checkableAction)

        headerPos = self.filterall.mapToGlobal(self.horizontalHeader.pos())

        posY = headerPos.y() + self.horizontalHeader.height()
        posX = headerPos.x() + self.horizontalHeader.sectionPosition(index)
        self.menu.exec_(QPoint(posX, posY))

    def menuClose(self):
        self.keywords[self.col] = []
        for element in self.checkBoxs:
            if element.isChecked():
                self.keywords[self.col].append(element.text())
        self.filterdata()
        self.menu.close()

    def loadAll(self):
        with open("Rts.csv", "r") as inpfil:
            reader = csv.reader(inpfil, delimiter=',')
            for csheader in reader:            
                ncol = len(csheader)
                data = list(reader)
                row_count = len(data)

                self.filterall.setRowCount(row_count)
                self.filterall.setColumnCount(ncol)
                #self.filterall.setHorizontalHeaderLabels(Qt.QString('%s' % ', '.join(map(str, csheader))).split(","))
                self.filterall.setHorizontalHeaderLabels(csheader)

                for ii in range(0, row_count):
                    mainins = data[ii]
                    for var in range(0, ncol):
                        self.filterall.setItem(ii, var, QTableWidgetItem(mainins[var]))

    def clearFilter(self):
        for i in range(self.filterall.rowCount()):
            self.filterall.setRowHidden(i, False)

    def filterdata(self):

        columnsShow = dict([(i, True) for i in range(self.filterall.rowCount())])

        for i in range(self.filterall.rowCount()):
            for j in range(self.filterall.columnCount()):
                item = self.filterall.item(i, j)
                if self.keywords[j]:
                    if item.text() not in self.keywords[j]:
                        columnsShow[i] = False
        for key, value in columnsShow.iteritems():
            self.filterall.setRowHidden(key, not value)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())