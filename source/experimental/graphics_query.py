import sys
import json
import oracledb

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import oracle_my_lib

# ============================================================
# ORACLE METADATA SERVICE
# ============================================================
class OracleMetadata:
    def __init__(self, conn, schema):
        self.conn = conn
        self.schema = schema.upper()

    def tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT table_name
            FROM all_tables
            WHERE owner = :s
            ORDER BY table_name
        """, s=self.schema)
        return [r[0] for r in cur]

    def columns(self, table):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT column_name
            FROM all_tab_columns
            WHERE owner = :s AND table_name = :t
            ORDER BY column_id
        """, s=self.schema, t=table)
        return [r[0] for r in cur]

    def pk(self, table):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT cols.column_name
            FROM all_constraints cons
            JOIN all_cons_columns cols
              ON cons.constraint_name = cols.constraint_name
             AND cons.owner = cols.owner
            WHERE cons.constraint_type = 'P'
              AND cons.owner = :s
              AND cons.table_name = :t
        """, s=self.schema, t=table)
        return {r[0] for r in cur}

    def fk(self, table):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT a.column_name, c_pk.table_name, b.column_name
            FROM all_constraints c
            JOIN all_cons_columns a ON c.constraint_name = a.constraint_name
            JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
            JOIN all_cons_columns b
              ON c_pk.constraint_name = b.constraint_name
             AND a.position = b.position
            WHERE c.constraint_type = 'R'
              AND c.owner = :s
              AND c.table_name = :t
        """, s=self.schema, t=table)
        return [(r[0], r[1], r[2]) for r in cur]

# ============================================================
# GRAPHICS ITEMS
# ============================================================
class JoinItem:
    def __init__(self, f1, f2, line, join_type="INNER"):
        self.f1 = f1
        self.f2 = f2
        self.line = line
        self.join_type = join_type

class FieldItem(QGraphicsRectItem):
    def __init__(self, name, parent, view, is_pk=False, is_fk=False):
        super().__init__(parent)
        self.name = name
        self.parent_table = parent
        self.view = view
        self.is_pk = is_pk
        self.is_fk = is_fk
        self.joins = []

        self.alias = ""
        self.filter = ""
        self.order = ""

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setRect(0, 0, parent.rect().width()-16, 16)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        self.text = QGraphicsSimpleTextItem(name, self)
        self.text.setPos(18, 0)

        if is_pk or is_fk:
            self.icon = QGraphicsEllipseItem(4, 4, 8, 8, self)
            self.icon.setBrush(QBrush(QColor("gold") if is_pk else QColor("orange")))
            self.icon.setPen(QPen(Qt.GlobalColor.black))
        else:
            self.icon = None

    def mouseDoubleClickEvent(self, event):
        if self.view.parent_widget:
            if self not in self.view.parent_widget.selected_fields:
                self.view.parent_widget.selected_fields.append(self)
                self.view.parent_widget.manual_field_selection = True
            self.view.parent_widget.update_sql_preview()
        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu()
        alias_action = menu.addAction("Imposta alias")
        filter_action = menu.addAction("Imposta filtro")
        order_action = menu.addAction("Imposta ordine")
        remove_action = menu.addAction("Rimuovi dal SELECT")
        action = menu.exec(event.screenPos())
        if action == alias_action:
            text, ok = QInputDialog.getText(None, "Alias", "Inserisci alias:", text=self.alias)
            if ok: self.alias = text
        elif action == filter_action:
            text, ok = QInputDialog.getText(None, "Filtro", "Inserisci filtro:", text=self.filter)
            if ok: self.filter = text
        elif action == order_action:
            items = ["ASC", "DESC"]
            text, ok = QInputDialog.getItem(None, "Ordine", "Seleziona ordine:", items, editable=False)
            if ok: self.order = text
        elif action == remove_action:
            if self.view.parent_widget and self in self.view.parent_widget.selected_fields:
                self.view.parent_widget.selected_fields.remove(self)
        if self.view.parent_widget:
            self.view.parent_widget.update_sql_preview()

class TableTitleItem(QGraphicsRectItem):
    def __init__(self, text, parent):
        super().__init__(parent)
        self.setRect(0, 0, parent.rect().width(), 24)
        self.setBrush(QColor("#85C1E9"))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        self.label = QGraphicsSimpleTextItem(text, self)
        self.label.setPos(5, 4)

    def mousePressEvent(self, event):
        self.parentItem().setSelected(True)
        super().mousePressEvent(event)

class TableItem(QGraphicsRectItem):
    def __init__(self, name, fields, view):
        super().__init__(0, 0, 190, 30 + len(fields) * 18)
        self.name = name
        self.view = view
        self.field_items = []

        self.setBrush(QBrush(QColor("#AED6F1")))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.title_item = TableTitleItem(name, self)
        self.title_item.setPos(0, 0)

        for i, f in enumerate(fields):
            field = FieldItem(**f, parent=self, view=view)
            field.setParentItem(self)
            field.setPos(10, 26 + i * 16)
            self.field_items.append(field)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.save()
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#1ABC9C"), 2))
            painter.drawRect(self.rect())
            painter.restore()

    def contextMenuEvent(self, event):
        menu = QMenu()
        remove_action = menu.addAction("Elimina tabella")
        action = menu.exec(event.screenPos())
        if action == remove_action:
            for f in self.field_items:
                for j in f.joins[:]:
                    self.view.scene.removeItem(j.line)
                    if j in self.view.joins:
                        self.view.joins.remove(j)
            self.view.scene.removeItem(self)
            if self.view.parent_widget:
                self.view.parent_widget.selected_fields = [
                    f for f in self.view.parent_widget.selected_fields if f.parent_table != self
                ]
                self.view.parent_widget.update_sql_preview()

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            for f in self.field_items:
                for j in f.joins:
                    self.view.update_join_position(j)
        return super().itemChange(change, value)

# ============================================================
# DESIGNER VIEW
# ============================================================
class DesignerView(QGraphicsView):
    def __init__(self, scene, parent_widget=None):
        super().__init__(scene)
        self.scene = scene
        self.start_field = None
        self.joins = []
        self.parent_widget = parent_widget
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        item = self.scene.itemAt(scene_pos, QTransform())
        if isinstance(item, FieldItem):
            self.start_field = item
        elif isinstance(item, (QGraphicsSimpleTextItem, QGraphicsEllipseItem)):
            parent = item.parentItem()
            if isinstance(parent, FieldItem):
                self.start_field = parent
            else:
                self.start_field = None
        else:
            self.start_field = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start_field:
            scene_pos = self.mapToScene(event.position().toPoint())
            end_item = self.scene.itemAt(scene_pos, QTransform())
            if isinstance(end_item, FieldItem):
                f2 = end_item
            elif isinstance(end_item, (QGraphicsSimpleTextItem, QGraphicsEllipseItem)):
                parent = end_item.parentItem()
                f2 = parent if isinstance(parent, FieldItem) else None
            else:
                f2 = None

            if f2 and f2 != self.start_field:
                self.create_join(self.start_field, f2)

        self.start_field = None
        super().mouseReleaseEvent(event)

    def create_join(self, f1, f2, join_type="INNER"):
        line = self.scene.addLine(0, 0, 0, 0)
        join = JoinItem(f1, f2, line, join_type)
        self.joins.append(join)
        f1.joins.append(join)
        f2.joins.append(join)
        self.update_join_style(join)
        self.update_join_position(join)
        if self.parent_widget:
            self.parent_widget.update_sql_preview()

    def update_join_position(self, join):
        f1 = join.f1
        f2 = join.f2
        r1 = f1.sceneBoundingRect()
        r2 = f2.sceneBoundingRect()
        if r1.center().x() < r2.center().x():
            p1 = QPointF(r1.right(), r1.center().y())
            p2 = QPointF(r2.left(), r2.center().y())
        else:
            p1 = QPointF(r1.left(), r1.center().y())
            p2 = QPointF(r2.right(), r2.center().y())
        join.line.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def update_join_style(self, join):
        colors = {"INNER": QColor("#2574A8"), "LEFT": QColor("#27AE60"), "RIGHT": QColor("#F39C12")}
        join.line.setPen(QPen(colors.get(join.join_type, QColor("#2574A8")), 2))

# ============================================================
# MAIN WINDOW
# ============================================================
class QueryDesigner(QMainWindow):
    def __init__(self, conn, schema):
        super().__init__()
        self.setWindowTitle("Oracle Query Designer Ultimate")
        self.resize(1600, 850)

        self.meta = OracleMetadata(conn, schema)
        self.conn = conn
        self.manual_field_selection = False
        self.selected_fields = []

        # Toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        btn_save = QAction(QIcon(), "Salva", self)
        btn_load = QAction(QIcon(), "Carica", self)
        btn_exec = QAction(QIcon(), "Preview", self)
        toolbar.addAction(btn_save)
        toolbar.addAction(btn_load)
        toolbar.addAction(btn_exec)
        btn_save.triggered.connect(self.save_json)
        btn_load.triggered.connect(self.load_json)
        btn_exec.triggered.connect(self.run_query)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # === Splitter principale orizzontale ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # =========================
        # LEFT: Tree + Search
        # =========================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(2, 2, 2, 2)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Cerca tabelle...")
        self.search_field.textChanged.connect(self.filter_tree)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tabelle"])

        left_layout.addWidget(self.search_field)
        left_layout.addWidget(self.tree)

        main_splitter.addWidget(left_widget)

        # =========================
        # CENTER: Canvas
        # =========================
        self.scene = QGraphicsScene()
        self.view = DesignerView(self.scene, parent_widget=self)

        main_splitter.addWidget(self.view)

        # =========================
        # RIGHT: SQL + Result (splitter verticale)
        # =========================
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.sql_preview = QTextEdit()
        #self.sql_preview.setReadOnly(True)

        self.result_table = QTableWidget()

        right_splitter.addWidget(self.sql_preview)
        right_splitter.addWidget(self.result_table)

        main_splitter.addWidget(right_splitter)

        # =========================
        # Dimensioni iniziali
        # =========================
        main_splitter.setSizes([200, 900, 300])
        main_splitter.setStretchFactor(0, 1)  # left
        main_splitter.setStretchFactor(1, 4)  # center
        main_splitter.setStretchFactor(2, 2)  # right

        right_splitter.setStretchFactor(0, 1)  # sql
        right_splitter.setStretchFactor(1, 2)  # result

        # Load metadata
        self.load_metadata()
        self.tree.itemDoubleClicked.connect(self.add_table)

    def load_metadata(self):
        for t in self.meta.tables():
            node = QTreeWidgetItem([t])
            self.tree.addTopLevelItem(node)

    def filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setHidden(text not in item.text(0).lower())

    def add_table(self, item):
        name = item.text(0)
        if any(isinstance(o, TableItem) and o.name == name for o in self.scene.items()):
            return
        pk = self.meta.pk(name)
        fk = {f[0] for f in self.meta.fk(name)}
        fields = [{"name": c, "is_pk": c in pk, "is_fk": c in fk} for c in self.meta.columns(name)]
        t = TableItem(name, fields, self.view)

        # disposizione orizzontale
        existing_tables = [i for i in self.scene.items() if isinstance(i, TableItem)]
        if existing_tables:
            last = max(existing_tables, key=lambda x: x.pos().x())
            x = last.pos().x() + last.rect().width() + 40
        else:
            x = 60
        y = 60
        t.setPos(QPointF(x, y))

        self.scene.addItem(t)
        self.update_sql_preview()

    def add_field_to_query(self, field):
        if field not in self.selected_fields:
            self.selected_fields.append(field)

    def update_sql_preview(self):        
        tables = [item for item in self.scene.items() if isinstance(item, TableItem)]
        if not tables:
            self.sql_preview.setPlainText("-- nessuna tabella")
            return
        #if not self.manual_field_selection or len(self.selected_fields) == 0:
        select = []
        tables_alias = {t.name: f"T{i+1}" for i, t in enumerate(tables)}
        for f in self.selected_fields:
            alias = tables_alias[f.parent_table.name]
            col = f"{alias}.{f.name}"
            if f.alias: col += f" AS {f.alias}"
            select.append(col)
        if len(self.selected_fields) == 0:
            select.append("*")
        sql = "SELECT " + ", ".join(select) + "\nFROM "
        if not self.view.joins:
            print('nessuna join')
            sql += ", ".join(f"{t.name} {tables_alias[t.name]}" for t in tables)
        else:            
            sql += ", ".join(f"{t.name} {tables_alias[t.name]}" for t in tables)
            #first = tables[0]
            #sql += f"{first.name} {tables_alias[first.name]}"
            v_first = True
            for j in self.view.joins:
                #jt = j.join_type + " WHERE"
                t2 = j.f2.parent_table.name
                if v_first:
                    sql += "\nWHERE "
                    v_first = False
                else:
                    sql += "AND "
                sql += f"{tables_alias[j.f1.parent_table.name]}.{j.f1.name} = {tables_alias[t2]}.{j.f2.name}\n"
        where = [f"{tables_alias[f.parent_table.name]}.{f.name} {f.filter}" for f in self.selected_fields if f.filter]
        order = [f"{tables_alias[f.parent_table.name]}.{f.name} {f.order}" for f in self.selected_fields if f.order]
        if where: sql += "\nWHERE " + " AND ".join(where)
        if order: sql += "\nORDER BY " + ", ".join(order)
        
        self.sql_preview.setPlainText(sql)

    def save_json(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Salva diagramma", "", "JSON (*.json)")
        if not fn: return
        data = {"tables": [], "joins": [], "fields": []}
        for item in self.scene.items():
            if isinstance(item, TableItem):
                data["tables"].append({"name": item.name, "x": item.pos().x(), "y": item.pos().y()})
                for f in item.field_items:
                    data["fields"].append({"table": item.name, "name": f.name, "alias": f.alias, "filter": f.filter, "order": f.order})
        for j in self.view.joins:
            data["joins"].append({"t1": j.f1.parent_table.name, "f1": j.f1.name,
                                  "t2": j.f2.parent_table.name, "f2": j.f2.name, "type": j.join_type})
        with open(fn, "w") as f:
            json.dump(data, f, indent=2)

    def load_json(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Apri diagramma", "", "JSON (*.json)")
        if not fn: return
        with open(fn) as f:
            data = json.load(f)
        self.scene.clear()
        self.view.joins.clear()
        self.selected_fields = []
        tables_map = {}
        for t in data["tables"]:
            pk = self.meta.pk(t["name"])
            fk = {f[0] for f in self.meta.fk(t["name"])}
            fields = [{"name": c, "is_pk": c in pk, "is_fk": c in fk} for c in self.meta.columns(t["name"])]
            ti = TableItem(t["name"], fields, self.view)
            ti.setPos(QPointF(t["x"], t["y"]))
            self.scene.addItem(ti)
            tables_map[t["name"]] = ti
        for f in data.get("fields", []):
            t = tables_map[f["table"]]
            fi = next((x for x in t.field_items if x.name == f["name"]), None)
            if fi:
                fi.alias = f.get("alias", "")
                fi.filter = f.get("filter", "")
                fi.order = f.get("order", "")
                self.selected_fields.append(fi)
        for j in data.get("joins", []):
            f1 = next(f for f in tables_map[j["t1"]].field_items if f.name == j["f1"])
            f2 = next(f for f in tables_map[j["t2"]].field_items if f.name == j["f2"])
            self.view.create_join(f1, f2, j["type"])
        self.update_sql_preview()

    def run_query(self):
        sql = self.sql_preview.toPlainText()
        if not sql.strip(): return
        try:            
            cur = self.conn.cursor()
            cur.execute(sql + " FETCH FIRST 50 ROWS ONLY")
            cols = [d[0] for d in cur.description]
            print(cols)
            rows = cur.fetchall()
            self.result_table.setColumnCount(len(cols))
            self.result_table.setHorizontalHeaderLabels(cols)
            self.result_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.result_table.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            QMessageBox.critical(self, "Errore SQL", f"Errore durante l'esecuzione della query:\n{str(e)}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    oracle_my_lib.inizializzo_client()
    conn = oracledb.connect(user="SMILE", password="SMILE", dsn="BACKUP_815")
    app = QApplication(sys.argv)
    w = QueryDesigner(conn, "SMILE")
    w.show()
    sys.exit(app.exec())