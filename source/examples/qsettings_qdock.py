from PyQt5.QtWidgets import QMainWindow, QDockWidget, QTextEdit, QApplication
from PyQt5.QtCore import QSettings, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("Marco Valaguzza", "MSql")
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.loadSettings()

        self.dock1 = QDockWidget("Dock 1", self)
        self.dock1.setWidget(QTextEdit())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock1)

        self.dock2 = QDockWidget("Dock 2", self)
        self.dock2.setWidget(QTextEdit())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock2)

        self.tabifyDockWidget(self.dock1, self.dock2)

        self.loadDockSettings()

    def closeEvent(self, event):
        self.saveSettings()
        self.saveDockSettings()
        event.accept()

    def loadSettings(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)

    def saveSettings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def loadDockSettings(self):
        for dock in [self.dock1, self.dock2]:
            geometry = self.settings.value(f"{dock.objectName()}_geometry")
            if geometry:
                dock.restoreGeometry(geometry)

    def saveDockSettings(self):
        for dock in [self.dock1, self.dock2]:
            self.settings.setValue(f"{dock.objectName()}_geometry", dock.saveGeometry())

if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()

