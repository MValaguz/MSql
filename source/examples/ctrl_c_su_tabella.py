from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class View(QTableView):
    def __init__(self):
        super(View, self).__init__(parent=None)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            print('Ctrl + C')
        if event.matches(QKeySequence.Paste):
            print('Ctrl + V')
        QTableView.keyPressEvent(self, event)


app = QApplication([])
view = View()
view.show()
qApp.exec_()