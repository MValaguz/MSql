# -*- coding: utf-8 -*-

# questa "evoluzione" della classe QTableWidget è stata fatta per intercettare correttamente la combinazione 
# CTRL-C in quanto non ho avuto modo di farla funzionare direttamente dal codice principale!
# Intercettava solo CTRL e non CTRL-C! 

# Questa classe viene utilizzata direttamente dentro QtDesigner! 

from PyQt5.QtWidgets import QApplication,QTableWidget
from PyQt5.QtGui import QKeySequence

class my_QTableWidget(QTableWidget):
    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)

    # Intercetto evento di CTRL-C
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            print('Ctrl + C')
            copied_cells = sorted(self.selectedIndexes())

            copy_text = ''
            max_column = copied_cells[-1].column()
            for c in copied_cells:
                copy_text += self.item(c.row(), c.column()).text()
                if c.column() == max_column:
                    copy_text += '\n'
                else:
                    copy_text += '\t'
                    
            QApplication.clipboard().setText(copy_text)

        QTableWidget.keyPressEvent(self, event)
