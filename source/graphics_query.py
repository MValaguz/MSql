import sys
import json

from PyQt6.QtWidgets import (
    QApplication, QWidget, QTreeWidget, QTreeWidgetItem,
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
    QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QPainter


# ------------------------------------------------------------
# FieldItem (campo di una tabella)
# ------------------------------------------------------------
class FieldItem(QGraphicsSimpleTextItem):
    def __init__(self, name, parent_table, query_table, view):
        super().__init__(name)
        self.name = name
        self.parent_table = parent_table
        self.query_table = query_table
        self.view = view

        self.setBrush(QBrush(Qt.GlobalColor.black))
        self.setFlag(QGraphicsSimpleTextItem.GraphicsItemFlag.ItemIsSelectable)

    def mouseDoubleClickEvent(self, event):
        """Aggiunge il campo alla SELECT"""
        self.view.add_field_to_query(self)
        super().mouseDoubleClickEvent(event)


# ------------------------------------------------------------
# TableItem (rettangolo tabella)
# ------------------------------------------------------------
class TableItem(QGraphicsRectItem):
    def __init__(self, name, fields, query_table, view):
        super().__init__(0, 0, 160, 25 + len(fields) * 20)

        self.name = name
        self.query_table = query_table
        self.view = view

        self.setBrush(QBrush(QColor("#AED6F1")))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)

        title = QGraphicsSimpleTextItem(name, self)
        title.setPos(5, 2)

        self.field_items = []
        for i, field in enumerate(fields):
            f = FieldItem(field, self, query_table, view)
            f.setParentItem(self)
            f.setPos(8, 25 + i * 18)
            self.field_items.append(f)


# ------------------------------------------------------------
# Graphics View (lavagna)
# ------------------------------------------------------------
class DesignerView(QGraphicsView):
    def __init__(self, scene, query_table, sql_preview):
        super().__init__(scene)
        self.query_table = query_table
        self.sql_preview = sql_preview

        self.start_field = None
        self.joins = []  # (f1, f2, line)

        self.setRenderHints(
            self.renderHints() | QPainter.RenderHint.Antialiasing
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, FieldItem):
                self.start_field = item
        elif event.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, FieldItem):
                self.remove_joins_for_field(item)

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start_field:
            end_item = self.itemAt(event.position().toPoint())
            if isinstance(end_item, FieldItem) and end_item != self.start_field:
                self.create_join(self.start_field, end_item)

        self.start_field = None
        super().mouseReleaseEvent(event)

    # ---------------- JOIN MANAGEMENT ----------------

    def create_join(self, f1, f2):
        line = self.scene().addLine(
            f1.scenePos().x() + 70, f1.scenePos().y() + 8,
            f2.scenePos().x() + 70, f2.scenePos().y() + 8,
            QPen(Qt.GlobalColor.red, 2)
        )
        self.joins.append((f1, f2, line))

        self.add_field_to_query(f1)
        self.add_field_to_query(f2)
        self.update_sql_preview()

    def remove_joins_for_field(self, field):
        to_remove = [j for j in self.joins if field in j]
        for j in to_remove:
            self.scene().removeItem(j[2])
            self.joins.remove(j)
        self.update_sql_preview()

    # ---------------- QUERY TABLE ----------------

    def add_field_to_query(self, field):
        for row in range(self.query_table.rowCount()):
            if (
                self.query_table.item(row, 0).text() == field.name
                and self.query_table.item(row, 1).text() == field.parent_table.name
            ):
                return

        self.query_table.blockSignals(True)

        row = self.query_table.rowCount()
        self.query_table.insertRow(row)
        self.query_table.setItem(row, 0, QTableWidgetItem(field.name))
        self.query_table.setItem(row, 1, QTableWidgetItem(field.parent_table.name))
        self.query_table.setItem(row, 2, QTableWidgetItem(""))
        self.query_table.setItem(row, 3, QTableWidgetItem(""))
        self.query_table.setItem(row, 4, QTableWidgetItem(""))

        self.query_table.blockSignals(False)
        field.setBrush(QBrush(QColor("#27AE60")))

        self.update_sql_preview()

    # ---------------- SQL PREVIEW ----------------

    def update_sql_preview(self):
        if self.query_table.rowCount() == 0:
            self.sql_preview.setPlainText("Nessun campo selezionato")
            return

        select_clause = []
        tables = set()

        for row in range(self.query_table.rowCount()):
            it_c = self.query_table.item(row, 0)
            it_t = self.query_table.item(row, 1)
            it_a = self.query_table.item(row, 2)

            if not it_c or not it_t:
                continue

            campo = it_c.text()
            tabella = it_t.text()
            alias = it_a.text() if it_a else ""

            tables.add(tabella)
            select_clause.append(
                f"{tabella}.{campo}" + (f" AS {alias}" if alias else "")
            )

        sql = "SELECT " + ", ".join(select_clause)

        # FROM + JOIN
        if not self.joins:
            sql += " FROM " + ", ".join(tables)
        else:
            base = next(iter(tables))
            sql += f" FROM {base}"
            for f1, f2, _ in self.joins:
                sql += (
                    f" INNER JOIN {f2.parent_table.name}"
                    f" ON {f1.parent_table.name}.{f1.name}"
                    f" = {f2.parent_table.name}.{f2.name}"
                )

        # WHERE
        where = []
        for row in range(self.query_table.rowCount()):
            it_f = self.query_table.item(row, 3)
            if it_f and it_f.text():
                t = self.query_table.item(row, 1).text()
                c = self.query_table.item(row, 0).text()
                where.append(f"{t}.{c} {it_f.text()}")
        if where:
            sql += " WHERE " + " AND ".join(where)

        # ORDER BY
        order = []
        for row in range(self.query_table.rowCount()):
            it_o = self.query_table.item(row, 4)
            if it_o and it_o.text():
                t = self.query_table.item(row, 1).text()
                c = self.query_table.item(row, 0).text()
                order.append(f"{t}.{c} {it_o.text()}")
        if order:
            sql += " ORDER BY " + ", ".join(order)

        self.sql_preview.setPlainText(sql)


# ------------------------------------------------------------
# Main Window
# ------------------------------------------------------------
class QueryDesigner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Query Designer stile Access (PyQt6)")
        self.resize(1400, 750)

        layout = QHBoxLayout(self)

        # Tree tabelle
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tabelle"])
        layout.addWidget(self.tree, 1)

        # Scene
        self.scene = QGraphicsScene()
        self.query_table = QTableWidget(0, 5)
        self.query_table.setHorizontalHeaderLabels(
            ["Campo", "Tabella", "Alias", "Filtro", "Ordine"]
        )
        self.query_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.sql_preview = QTextEdit()
        self.sql_preview.setReadOnly(True)

        self.view = DesignerView(self.scene, self.query_table, self.sql_preview)

        center = QVBoxLayout()
        center.addWidget(self.view)
        center.addWidget(self.sql_preview)
        layout.addLayout(center, 3)

        right = QVBoxLayout()
        right.addWidget(self.query_table)
        layout.addLayout(right, 2)

        self.load_tables()
        self.tree.itemDoubleClicked.connect(self.add_table)

    def load_tables(self):
        def add_table(name, fields):
            t = QTreeWidgetItem([name])
            for f in fields:
                t.addChild(QTreeWidgetItem([f]))
            self.tree.addTopLevelItem(t)

        add_table("Clienti", ["ID", "Nome", "Cognome"])
        add_table("Ordini", ["ID", "ID_Cliente", "Data"])
        add_table("Prodotti", ["ID", "Descrizione", "Prezzo"])

    def add_table(self, item, column):
        if item.childCount() == 0:
            parent = item.parent()
            name = parent.text(0)
            fields = [parent.child(i).text(0) for i in range(parent.childCount())]

            for obj in self.scene.items():
                if isinstance(obj, TableItem) and obj.name == name:
                    return

            t = TableItem(name, fields, self.query_table, self.view)
            t.setPos(QPointF(50, 50 + len(self.scene.items()) * 25))
            self.scene.addItem(t)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QueryDesigner()
    w.show()
    sys.exit(app.exec())
