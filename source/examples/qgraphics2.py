import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QVBoxLayout, QWidget, QPushButton, QPlainTextEdit, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsSimpleTextItem, QGraphicsPathItem
)
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPainterPath
from PyQt6.QtCore import Qt

class FieldItem(QGraphicsTextItem):
    """
    Rappresenta un campo di tabella (testo cliccabile).
    """
    def __init__(self, text, table_name, field_name, click_callback=None, parent=None):
        super().__init__(text, parent)
        self.table_name = table_name
        self.field_name = field_name
        self.click_callback = click_callback
        self.setDefaultTextColor(QColor("black"))
        self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback(self)
        super().mousePressEvent(event)

class ConnectionLine(QGraphicsPathItem):
    """
    Rappresenta il collegamento poligonale tra due campi.
    Il percorso è costruito con una serie di segmenti che creano un effetto "a scalini".
    Permette la cancellazione selezionando la linea e premendo il tasto Canc.
    """
    def __init__(self, field1, field2, main_window, p1, p2, parent=None):
        super().__init__(parent)
        self.field1 = field1
        self.field2 = field2
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
        """
        Aggiorna il percorso poligonale tra p1 e p2.
        Utilizza un punto intermedio con la coordinata x media per creare un collegamento a "scalini".
        """
        path = QPainterPath()
        path.moveTo(p1)
        mid_x = (p1.x() + p2.x()) / 2
        # Primo segmento: orizzontale da p1 fino al punto (mid_x, p1.y())
        path.lineTo(mid_x, p1.y())
        # Secondo segmento: verticale fino a (mid_x, p2.y())
        path.lineTo(mid_x, p2.y())
        # Terzo segmento: orizzontale fino a p2
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

class TableItem(QGraphicsRectItem):
    """
    Rappresenta graficamente una tabella: un rettangolo con il nome e i campi.
    Abilita il movimento e notifica il MainWindow sugli spostamenti per aggiornare i collegamenti.
    """
    def __init__(self, table_name, fields, x, y, click_callback, main_window,
                 width=150, header_height=20, field_height=20):
        height = header_height + len(fields) * field_height
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        self.table_name = table_name
        self.main_window = main_window

        # Abilita il movimento e l'invio di notifiche sugli spostamenti
        self.setFlags(
            QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setBrush(QBrush(QColor("lightgray")))
        self.setPen(QPen(Qt.GlobalColor.black))

        # Aggiungi il nome della tabella (header)
        title_item = QGraphicsSimpleTextItem(table_name, self)
        title_item.setPos(5, 0)

        # Disegna una linea separatrice sotto l'header
        separator = QGraphicsPathItem(self)
        separator_path = QPainterPath()
        separator_path.moveTo(0, header_height)
        separator_path.lineTo(width, header_height)
        separator.setPath(separator_path)
        separator.setPen(QPen(Qt.GlobalColor.black))

        # Aggiunge i campi come FieldItem
        self.field_items = []
        for i, field in enumerate(fields):
            field_item = FieldItem(field, table_name, field, click_callback, parent=self)
            field_item.setPos(5, header_height + i * field_height)
            self.field_items.append(field_item)

    def itemChange(self, change, value):
        """
        Quando la posizione della tabella cambia, notifica il MainWindow per aggiornare i collegamenti.
        """
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange or \
           change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            if self.main_window:
                self.main_window.update_connections()
        return super().itemChange(change, value)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Designer per JOIN SQL")
        self.resize(700, 500)

        # Variabili per la logica dei collegamenti
        self.current_selected_field = None
        # Lista di tuple: (FieldItem1, FieldItem2, ConnectionLine)
        self.connections = []

        # Crea la scena e la view per il disegno
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Crea alcune tabelle di esempio
        table1 = TableItem("Clienti", ["id", "nome", "cognome", "email"], 50, 50, self.field_clicked, self)
        table2 = TableItem("Ordini", ["id", "cliente_id", "data", "totale"], 300, 200, self.field_clicked, self)
        table3 = TableItem("Prodotti", ["id", "nome", "prezzo"], 300, 50, self.field_clicked, self)

        self.scene.addItem(table1)
        self.scene.addItem(table2)
        self.scene.addItem(table3)

        # Pulsante per generare la query SQL
        self.generate_button = QPushButton("Genera SQL")
        self.generate_button.clicked.connect(self.generate_sql)

        # Area di testo per mostrare la query generata
        self.sql_output = QPlainTextEdit()
        self.sql_output.setReadOnly(True)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.sql_output)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def field_clicked(self, field_item):
        """
        Gestisce il click sui campi:
        - Se nessun campo è selezionato, il campo cliccato viene evidenziato.
        - Se un campo è già selezionato, viene creato un collegamento grafico fra i due.
        """
        if self.current_selected_field is None:
            self.current_selected_field = field_item
            field_item.setDefaultTextColor(QColor("red"))
        else:
            if field_item == self.current_selected_field:
                return

            # Crea una linea poligonale che collega il centro dei due campi
            p1 = self.current_selected_field.mapToScene(self.current_selected_field.boundingRect().center())
            p2 = field_item.mapToScene(field_item.boundingRect().center())
            connection_line = ConnectionLine(self.current_selected_field, field_item, self, p1, p2)
            self.scene.addItem(connection_line)

            self.connections.append((self.current_selected_field, field_item, connection_line))
            self.current_selected_field.setDefaultTextColor(QColor("black"))
            self.current_selected_field = None

    def update_connections(self):
        """
        Aggiorna dinamicamente le linee di collegamento in base alle posizioni correnti dei campi.
        """
        for field1, field2, connection_line in self.connections:
            p1 = field1.mapToScene(field1.boundingRect().center())
            p2 = field2.mapToScene(field2.boundingRect().center())
            connection_line.updatePath(p1, p2)

    def remove_connection(self, connection_line):
        """
        Rimuove il collegamento associato a connection_line.
        Viene chiamato dalla ConnectionLine quando si preme il tasto Canc.
        """
        for conn in self.connections:
            if conn[2] is connection_line:
                self.scene.removeItem(connection_line)
                self.connections.remove(conn)
                break

    def generate_sql(self):
        """
        Genera una query SQL basata sui collegamenti definiti.
        Per ogni collegamento viene aggiunta la condizione:
          <tabella1>.<campo1> = <tabella2>.<campo2>
        Le tabelle coinvolte vengono elencate nella clausola FROM.
        """
        tables = set()
        conditions = []
        for field1, field2, _ in self.connections:
            tables.add(field1.table_name)
            tables.add(field2.table_name)
            conditions.append(f"{field1.table_name}.{field1.field_name} = {field2.table_name}.{field2.field_name}")

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
