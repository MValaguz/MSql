import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QVBoxLayout, QWidget, QPushButton, QPlainTextEdit, QGraphicsProxyWidget,
    QScrollArea, QLabel, QGraphicsPathItem
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, pyqtSignal

# ------------------------
# FieldLabel: etichetta cliccabile per i campi
# ------------------------
class FieldLabel(QLabel):
    clicked = pyqtSignal(object)  # emette se stessa come parametro

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("padding: 2px; border: 1px solid #ccc;")
        # Non rendiamo trasparente i click in modo che possano essere cliccati
        # (il widget contenitore farà propagare gli eventi sulla parte header)

    def mousePressEvent(self, event):
        self.clicked.emit(self)
        super().mousePressEvent(event)

# ------------------------
# TableWidget: widget con header e area scroll per i campi
# ------------------------
class TableWidget(QWidget):
    def __init__(self, table_name, fields, click_callback, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.fields = fields
        self.click_callback = click_callback  # callback per i click sui campi

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (nome tabella)
        self.header = QLabel(table_name)
        self.header.setFixedHeight(30)
        self.header.setStyleSheet("background-color: lightgray; font-weight: bold; padding: 4px;")
        # Impostiamo l'header trasparente ai click per permettere lo spostabilità
        self.header.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.header)

        # Area scrollabile per i campi
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        # Container per i campi
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(2)
        self.field_labels = []
        for field in fields:
            label = FieldLabel(field)
            label.clicked.connect(self.fieldClicked)
            self.fields_layout.addWidget(label)
            self.field_labels.append(label)
        self.fields_container.setLayout(self.fields_layout)
        self.scroll_area.setWidget(self.fields_container)

    def fieldClicked(self, label):
        if self.click_callback:
            self.click_callback(self, label)

# ------------------------
# ResizableTableProxyWidget: incapsula un TableWidget in un QGraphicsProxyWidget resizzabile e spostabile
# ------------------------
class ResizableTableProxyWidget(QGraphicsProxyWidget):
    def __init__(self, widget, main_window, parent=None):
        super().__init__(parent)
        self.setWidget(widget)
        self.main_window = main_window
        # Abilitiamo lo spostamento e l'invio di notifiche sulla geometria
        self.setFlag(QGraphicsProxyWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        # Assicuriamoci che il proxy riceva i click
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.resizing = False

    def mousePressEvent(self, event):
        pos = event.pos()
        rect = self.boundingRect()
        # Se il click avviene negli ultimi 10 pixel in basso, inizia il resizing
        if rect.height() - pos.y() < 10:
            self.resizing = True
            self._startPos = event.scenePos()
            self._startHeight = rect.height()
            event.accept()
        # Se il click avviene nella zona header (in alto, ad esempio <30 px),
        # lo gestiamo qui per permettere lo spostamento (grazie al flag ItemIsMovable)
        elif pos.y() < 30:
            # Cambia il cursore per indicare lo spostamento
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            super().mousePressEvent(event)
        else:
            # Altrimenti, lascia che il widget interno (es. il QScrollArea o i FieldLabel)
            # gestisca l'evento (ad es. per lo scrolling o il click sui campi)
            QGraphicsProxyWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.resizing:
            dy = event.scenePos().y() - self._startPos.y()
            new_height = max(50, self._startHeight + dy)  # altezza minima di 50 px
            rect = self.boundingRect()
            new_rect = QRectF(rect.x(), rect.y(), rect.width(), new_height)
            self.setGeometry(new_rect)
            self.main_window.update_connections()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
        else:
            self.unsetCursor()
            super().mouseReleaseEvent(event)

# ------------------------
# ConnectionLine: linea poligonale che collega due campi
# ------------------------
class ConnectionLine(QGraphicsPathItem):
    def __init__(self, table_widget1, field_label1, table_widget2, field_label2, main_window, p1, p2, parent=None):
        super().__init__(parent)
        self.table_widget1 = table_widget1
        self.field_label1 = field_label1
        self.table_widget2 = table_widget2
        self.field_label2 = field_label2
        self.main_window = main_window
        pen = QPen(QColor("blue"))
        pen.setWidth(2)
        self.setPen(pen)
        self.setFlags(
            QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsPathItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.updatePath(p1, p2)

    def updatePath(self, p1, p2):
        path = QPainterPath()
        path.moveTo(p1)
        mid_x = (p1.x() + p2.x()) / 2
        path.lineTo(mid_x, p1.y())
        path.lineTo(mid_x, p2.y())
        path.lineTo(p2)
        self.setPath(path)

    def mousePressEvent(self, event):
        self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            if self.main_window:
                self.main_window.remove_connection(self)
            event.accept()
        else:
            super().keyPressEvent(event)

# ------------------------
# MainWindow: gestisce la scena e la logica dei collegamenti
# ------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Designer per JOIN SQL con tabelle resizzabili e spostabili")
        self.resize(900, 600)

        # Memorizza il campo attualmente selezionato:
        # una tupla (table_widget, field_label, center_in_scene)
        self.current_selected_field = None
        # Lista delle connessioni:
        # ciascuna è una tupla (table_widget1, field_label1, table_widget2, field_label2, connection_line)
        self.connections = []

        # Crea la scena e la view
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Pulsante per generare la query SQL
        self.generate_button = QPushButton("Genera SQL")
        self.generate_button.clicked.connect(self.generate_sql)

        # Output della query SQL
        self.sql_output = QPlainTextEdit()
        self.sql_output.setReadOnly(True)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.sql_output)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Crea le tabelle di esempio con circa 10 campi ciascuna
        self.create_table("Clienti", ["id", "nome", "cognome", "email", "indirizzo", "telefono", "città", "provincia", "CAP", "nazione"], 50, 50)
        self.create_table("Ordini", ["id", "cliente_id", "data", "totale", "sconto", "spedizione", "stato", "tracking", "note", "valuta"], 300, 200)
        self.create_table("Prodotti", ["id", "nome", "prezzo", "categoria", "descrizione", "giacenza", "fornitore", "codice", "peso", "dimensioni"], 550, 100)

    def create_table(self, table_name, fields, x, y):
        table_widget = TableWidget(table_name, fields, self.table_field_clicked)
        proxy = ResizableTableProxyWidget(table_widget, self)
        proxy.setGeometry(QRectF(0, 0, 150, 150))  # dimensione iniziale
        proxy.setPos(x, y)
        self.scene.addItem(proxy)

    def table_field_clicked(self, table_widget, field_label):
        """
        Callback chiamato quando viene cliccato un campo (FieldLabel).
        Calcola la posizione in scena del centro dell'etichetta.
        """
        # Calcola la posizione globale del campo e la converte nelle coordinate della scena
        global_pos = field_label.mapToGlobal(QPoint(0, 0))
        scene_pos = self.view.mapToScene(self.view.mapFromGlobal(global_pos))
        center = scene_pos + QPointF(field_label.width() / 2, field_label.height() / 2)
        if self.current_selected_field is None:
            self.current_selected_field = (table_widget, field_label, center)
            # Evidenzia il campo selezionato
            field_label.setStyleSheet("background-color: red; padding: 2px; border: 1px solid #ccc;")
        else:
            # Se il campo cliccato è lo stesso, non fare nulla
            if self.current_selected_field[1] == field_label:
                return
            p1 = self.current_selected_field[2]
            p2 = center
            connection_line = ConnectionLine(
                self.current_selected_field[0], self.current_selected_field[1],
                table_widget, field_label, self, p1, p2
            )
            self.scene.addItem(connection_line)
            self.connections.append((
                self.current_selected_field[0], self.current_selected_field[1],
                table_widget, field_label, connection_line
            ))
            # Ripristina lo stile del campo precedentemente selezionato
            self.current_selected_field[1].setStyleSheet("padding: 2px; border: 1px solid #ccc;")
            self.current_selected_field = None

    def update_connections(self):
        """
        Aggiorna le posizioni delle linee di collegamento.
        Viene chiamato quando una tabella viene spostata o resizzata.
        """
        for table_widget1, field_label1, table_widget2, field_label2, connection_line in self.connections:
            # Calcola la posizione del primo campo in scena
            global_pos1 = field_label1.mapToGlobal(QPoint(0, 0))
            scene_pos1 = self.view.mapToScene(self.view.mapFromGlobal(global_pos1))
            p1 = scene_pos1 + QPointF(field_label1.width() / 2, field_label1.height() / 2)
            # Calcola la posizione del secondo campo in scena
            global_pos2 = field_label2.mapToGlobal(QPoint(0, 0))
            scene_pos2 = self.view.mapToScene(self.view.mapFromGlobal(global_pos2))
            p2 = scene_pos2 + QPointF(field_label2.width() / 2, field_label2.height() / 2)
            connection_line.updatePath(p1, p2)

    def remove_connection(self, connection_line):
        """
        Rimuove il collegamento (linea) specificato.
        """
        for conn in self.connections:
            if conn[4] is connection_line:
                self.scene.removeItem(connection_line)
                self.connections.remove(conn)
                break

    def generate_sql(self):
        """
        Genera una query SQL basata sui collegamenti definiti.
        Per ogni connessione viene aggiunta la condizione:
          <tabella>.<campo> = <tabella2>.<campo2>
        """
        tables = set()
        conditions = []
        for table_widget1, field_label1, table_widget2, field_label2, _ in self.connections:
            tables.add(table_widget1.table_name)
            tables.add(table_widget2.table_name)
            conditions.append(f"{table_widget1.table_name}.{field_label1.text()} = {table_widget2.table_name}.{field_label2.text()}")
        if not tables:
            sql = "Nessun collegamento definito."
        else:
            sql = "SELECT *\nFROM " + ", ".join(tables)
            if conditions:
                sql += "\nWHERE " + "\n  AND ".join(conditions)
        self.sql_output.setPlainText(sql)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
