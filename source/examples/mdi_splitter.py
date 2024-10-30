from PyQt6.QtWidgets import QApplication, QMainWindow, QMdiArea, QSplitter, QTextEdit, QVBoxLayout, QWidget, QMdiSubWindow

app = QApplication([])

main_window = QMainWindow()

# Creazione della QMdiArea
mdi_area = QMdiArea()
mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)

# Widget per contenere lo splitter
splitter_container = QWidget()
splitter_layout = QVBoxLayout(splitter_container)

# Creazione dello splitter
splitter = QSplitter()

# Aggiunta di due text edit allo splitter
splitter.addWidget(QTextEdit("Left Pane"))
splitter.addWidget(QTextEdit("Right Pane"))

# Aggiunta dello splitter al layout del container
splitter_layout.addWidget(splitter)

# Creazione di una subwindow per lo splitter
sub_window = QMdiSubWindow()
sub_window.setWidget(splitter_container)

# Aggiunta della subwindow alla QMdiArea
mdi_area.addSubWindow(sub_window)
sub_window.show()

main_window.setCentralWidget(mdi_area)
main_window.show()

app.exec()
