#
# Personalizzazione dei widget librerie Qt
# Questi widget vengono usati direttamente dentro i file di creazione iterfaccia Qt
#

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

###
# Questa classe personalizza il widget QPlainTextEdit aggiungendo a sinistra la barra con i numeri di riga
###
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class MyCustomPlainTextWithNumber(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = self.fontMetrics().horizontalAdvance('9') * digits
        return space + 10

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        #painter.fillRect(event.rect(), QColor(240, 240, 240))
        #painter.fillRect(event.rect(), QColor(50, 50, 50))  # Sfondo scuro
        #painter.fillRect(event.rect())  # Sfondo scuro

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(0, int(top), self.lineNumberArea.width(), int(self.fontMetrics().height()),
                                 1, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

###
# Questa classe crea una combobox per la selezione di un colore tra una serie predefinita
###
class MyColorComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._populate_colors()

    def _create_color_icon(self, color: QColor, size: int = 16) -> QIcon:
        """Crea un'icona quadrata piena del colore specificato."""
        pix = QPixmap(size, size)
        pix.fill(QColor("transparent"))
        painter = QPainter(pix)
        painter.fillRect(0, 0, size, size, color)
        painter.end()
        return QIcon(pix)

    def _populate_colors(self):
        # Definisco 16 colori con nome e codice esadecimale
        palette = {
            "Red":        "#e53935", "Pink":       "#da6c94",
            "Purple":     "#8e24aa", "Deep Purple":"#5e35b1",
            "Indigo":     "#3949ab", "Blue":       "#1e88e5",
            "Light Blue": "#039be5", "Cyan":       "#00acc1",
            "Teal":       "#00897b", "Green":      "#43a047",
            "Light Green":"#7cb342","Lime":       "#c0ca33",
            "Yellow":     "#fdd835","Amber":      "#ffb300",
            "Orange":     "#fb8c00", "Deep Orange":"#f4511e"
        }

        for name, hexcol in palette.items():
            color = QColor(hexcol)
            icon  = self._create_color_icon(color)
            self.addItem(icon, name, userData=color)