# Personalizzazione dei widget librerie Qt

# Librerie grafiche QT
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Librerie QScintilla
from PyQt6.Qsci import *

###
# Questa classe personalizza il widget QsciScintilla 
###
class MyCustomQsciScintilla(QsciScintilla):
    # Il drag contiene elenco di item...allora vengono convertite in una sequenza di testo
    # se il drag non contiene elenco di item, quindi ad esempio del semplice testo, lascio le cose cosi come sono            
    def dragEnterEvent(self, event):        
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):                
            # estraggo gli item e li trasformo in stringa
            v_mime_data = event.mimeData()
            source_item = QStandardItemModel()
            source_item.dropMimeData(v_mime_data, Qt.DropAction.CopyAction, 0,0, QModelIndex())                                                
            v_stringa = ''
            for v_indice in range(0,source_item.rowCount()):
                if v_stringa != '':
                    v_stringa += ',' + source_item.item(v_indice, 0).text()
                else:
                    v_stringa = source_item.item(v_indice, 0).text()                                
            # reimposto la stringa dentro l'oggetto mimedata
            # da notare come l'oggetto v_mime_data punta direttamente all'oggetto event.mimeData!
            v_mime_data.setText(v_stringa)                
        event.acceptProposedAction()
    
    # Possibilità di fare lo scroll orizzontale usando tasto SHIFT+Rotella del mouse
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:  # Se Shift è premuto
            scroll_amount = event.angleDelta().y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - scroll_amount)
        else:
            super().wheelEvent(event)  # Mantieni il comportamento originale

###
# Questa classe personalizza il widget QTreeView 
###
class MyCustomTreeView(QTreeView):
    # Possibilità di fare lo scroll orizzontale usando tasto SHIFT+Rotella del mouse
    def wheelEvent(self, event: QWheelEvent):    
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:  # Se Shift è premuto
            scroll_amount = event.angleDelta().y()  # Recupera il valore della rotella
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - scroll_amount)
        else:
            super().wheelEvent(event)  # Mantieni il comportamento normale
