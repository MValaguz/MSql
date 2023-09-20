import sys

from PyQt5 import QtWidgets, QtCore

class TestGraphicsWidget(QtWidgets.QGraphicsWidget):
    """

    """
    comboBoxIndexChanged = QtCore.pyqtSignal(str)
    lineEditTextChanged = QtCore.pyqtSignal(str)

    def __init__(self, scene=None):
        super(TestGraphicsWidget, self).__init__(parent=None)

        combo = QtWidgets.QComboBox()
        combo.addItems([str(i) for i in range(5)])
        combo.currentIndexChanged[unicode].connect(self.comboBoxIndexChanged)

        line = QtWidgets.QLineEdit()
        line.textChanged.connect(self.lineEditTextChanged)

        self.lineEdit = scene.addWidget(line)
        self.comboBox = scene.addWidget(combo)


        layout = QtWidgets.QGraphicsLinearLayout()
        layout.addItem(self.lineEdit)
        layout.addItem(self.comboBox)

        self.setLayout(layout)


class Window(QtWidgets.QDialog):
    """

    """
    def __init__(self, parent=None):
        super(Window, self).__init__(parent=parent)
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)

        self.pushButtonAdd = QtWidgets.QPushButton('Add')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.pushButtonAdd)

        self.setLayout(layout)

        self.pushButtonAdd.pressed.connect(self.addTestItem)

    @QtCore.Slot(object)
    def printOutput(self, text):
        print(text)

    @QtCore.Slot()
    def addTestItem(self):
        """

        :return:
        """
        item = QtWidgets.QGraphicsRectItem()
        item.setRect(QtCore.QRectF(0, 0, 200, 40))
        w = TestGraphicsWidget(self.scene)
        w.setParentItem(item)
        w.comboBoxIndexChanged.connect(self.printOutput)
        w.lineEditTextChanged.connect(self.printOutput)
        self.scene.addItem(item)


if __name__ in ('__main__', '__builtin__'):

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setStyle('plastique')

    dialog = Window(None)
    dialog.show()
    sys.exit(app.exec_())