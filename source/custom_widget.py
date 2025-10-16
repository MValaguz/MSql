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
# Libreria per le espressioni regolari
import re

###
# Questa classe personalizza il widget QsciScintilla 
###
class MyCustomQsciScintilla(QsciScintilla):
    def dragEnterEvent(self, event):        
        """
           Il drag contiene elenco di item...allora vengono convertite in una sequenza di testo
           se il drag non contiene elenco di item, quindi ad esempio del semplice testo, lascio le cose cosi come sono            
        """  
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
        
    def wheelEvent(self, event: QWheelEvent):
        """
           Possibilità di fare lo scroll orizzontale usando tasto SHIFT+Rotella del mouse
        """
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:  # Se Shift è premuto
            scroll_amount = event.angleDelta().y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - scroll_amount)
        else:
            super().wheelEvent(event)  # Mantieni il comportamento originale
    
    def mouseDoubleClickEvent(self, event):        
        """
           Quando l'utente fa doppio click su una parola, vengono evidenziate tutte
        """
        # lascia che QScintilla faccia la selezione
        super().mouseDoubleClickEvent(event)

        # posticipa di un ciclo di eventi per essere sicuri che la selezione sia aggiornata
        self.double_click_on_the_word()

    def double_click_on_the_word(self):
        """           
           E' usata per quando utente facendo doppio click su una parola, il programma evidenzia tutti i punti dove quella parola è presente nel testo
        """
        selected_text = self.selectedText()            
        self.clear_selection_highlights()
        # la funzione isidentifier non riconosce i numeri!
        if selected_text.isidentifier():                            
            self._highlight_selected_text(selected_text,case_sensitive=False,regular_expression=True)            

    def clear_selection_highlights(self):
        """
           Pulisce gli indicatori delle parole (viene usato indicatore #4)
        """        
        self.clearIndicatorRange(0,0,self.lines(),self.lineLength(self.lines()-1),4)

    def _highlight_selected_text(self,
                                 highlight_text,
                                 case_sensitive=False,
                                 regular_expression=False):
        """
           Same as the highlight_text function, but adapted for the use
           with the __selection_changed functionality.
        """
        # Setup the indicator style, the highlight indicator will be 0
        self.set_indicator("selection")
        # Get all instances of the text using list comprehension and the re module
        matches = self.find_all(highlight_text,case_sensitive,regular_expression,text_to_bytes=True,whole_words=True)
        # Check if the match list is empty
        if matches:
            # Use the raw highlight function to set the highlight indicators
            self.highlight_raw(matches)

    def highlight_raw(self, highlight_list):
        """
           Core highlight function that uses Scintilla messages to style indicators.
           QScintilla's fillIndicatorRange function is to slow for large numbers of
           highlights!
           INFO:   This is done using the scintilla "INDICATORS" described in the official
                   scintilla API (http://www.scintilla.org/ScintillaDoc.html#Indicators)
        """
        scintilla_command = QsciScintillaBase.SCI_INDICATORFILLRANGE
        for highlight in highlight_list:
            start   = highlight[1]
            length  = highlight[3] - highlight[1]
            self.SendScintilla(scintilla_command,start,length)

    def _set_indicator(self,
                       indicator,
                       fore_color):
        """
           Set the indicator settings
        """
        self.indicatorDefine(QsciScintilla.IndicatorStyle.StraightBoxIndicator,indicator)
        self.setIndicatorForegroundColor(QColor(fore_color),indicator)
        self.SendScintilla(QsciScintillaBase.SCI_SETINDICATORCURRENT,indicator)

    def set_indicator(self, indicator):
        """
          Select the indicator that will be used for use with
          Scintilla's indicator functionality
        """                
        if indicator == "selection":
            # indica il colore da dare alla selezione (usato indicatore #4)
            self._set_indicator(4,'#643A93FF')        

    def find_all(self,
                 search_text,
                 case_sensitive=False,
                 regular_expression=False,
                 text_to_bytes=False,
                 whole_words=False):
        """
           Find all instances of a string and return a list of (line, index_start, index_end)
        """
        #Find all instances of the search string and return the list
        matches = self.index_strings_in_text(search_text,self.text(),case_sensitive,regular_expression,text_to_bytes,whole_words)
        return matches

    def index_strings_in_text(self,
                              search_text, 
                              text, 
                              case_sensitive=False, 
                              regular_expression=False, 
                              text_to_bytes=False,
                              whole_words=False):
        """ 
           Return all instances of the searched text in the text string
           as a list of tuples(0, match_start_position, 0, match_end_position).
        
           Parameters:
               - search_text:
                   the text/expression to search for in the text parameter
               - text:
                   the text that will be searched through
               - case_sensitive:
                   case sensitivity of the performed search
               - regular_expression:
                   selection of whether the search string is a regular expression or not
               - text_to_bytes:
                   whether to transform the search_text and text parameters into byte objects
               - whole_words:
                   match only whole words
        """
        # Check if whole words only should be matched
        if whole_words == True:
            search_text = r"\b(" + search_text + r")\b"
        # Convert text to bytes so that utf-8 characters will be parsed correctly
        if text_to_bytes == True:
            search_text = bytes(search_text, "utf-8")
            text = bytes(text, "utf-8")
        # Set the search text according to the regular expression selection
        if regular_expression == False:
            search_text = re.escape(search_text)
        # Compile expression according to case sensitivity flag
        if case_sensitive == True:
            compiled_search_re = re.compile(search_text)
        else:
            compiled_search_re = re.compile(search_text, re.IGNORECASE)
        # Create the list with all of the matches
        list_of_matches = [(0, match.start(), 0, match.end()) for match in re.finditer(compiled_search_re, text)]
        return list_of_matches

###
# Questa classe personalizza il widget QTreeView 
###
class MyCustomTreeView(QTreeView):
    """
       Possibilità di fare lo scroll orizzontale usando tasto SHIFT+Rotella del mouse
    """
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
        """
           Crea un'icona quadrata piena del colore specificato.
        """
        pix = QPixmap(size, size)
        pix.fill(QColor("transparent"))
        painter = QPainter(pix)
        painter.fillRect(0, 0, size, size, color)
        painter.end()
        return QIcon(pix)

    def _populate_colors(self):
        """
           Definisco 16 colori con nome e codice esadecimale
        """
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