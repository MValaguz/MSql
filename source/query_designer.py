#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 05/01/2026
#  Descrizione...: Creatore di query visuale per Oracle DB
#  Note..........: Creato utilizzando ChatGPT 
import sys
import json
import oracledb

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from utilita import Freccia_Mouse

import oracle_my_lib

# ============================================================
# ORACLE METADATA SERVICE
# ============================================================
class OracleMetadata:
    def __init__(self, conn, schema):
        self.conn = conn
        self.schema = schema.upper()

    def tables(self):
        Freccia_Mouse(True)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT table_name, comments
            FROM all_tab_comments
            WHERE owner = :s 
              AND table_name NOT IN (SELECT object_name FROM user_recyclebin)
            ORDER BY table_name
        """, s=self.schema)
        Freccia_Mouse(False)
        return [(r[0], r[1] or "") for r in cur]

    def columns(self, table):
        Freccia_Mouse(True)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT column_name
            FROM all_tab_columns
            WHERE owner = :s AND table_name = :t
            ORDER BY column_id
        """, s=self.schema, t=table)
        Freccia_Mouse(False)
        return [r[0] for r in cur]

    def pk(self, table):
        Freccia_Mouse(True)
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
        Freccia_Mouse(False)
        return {r[0] for r in cur}

# ============================================================
# GRAPHICS ITEMS
# ============================================================
class JoinLine(QGraphicsLineItem):
    def __init__(self, join, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.join = join

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        # ---- Endpoint (pallini) ----
        self.radius = 3

        self.start_dot = QGraphicsEllipseItem(
            -self.radius, -self.radius,
            self.radius * 2, self.radius * 2,
            self
        )

        self.end_dot = QGraphicsEllipseItem(
            -self.radius, -self.radius,
            self.radius * 2, self.radius * 2,
            self
        )

        for dot in (self.start_dot, self.end_dot):
            dot.setPen(QPen(Qt.GlobalColor.black, 0.5))
            dot.setZValue(self.zValue() + 1)

    def setLine(self, x1, y1, x2, y2):
        super().setLine(x1, y1, x2, y2)

        # aggiorna posizione pallini
        self.start_dot.setPos(x1, y1)
        self.end_dot.setPos(x2, y2)

    def set_color(self, color: QColor):
        pen = QPen(color, 2)
        self.setPen(pen)

        brush = QBrush(color)
        self.start_dot.setBrush(brush)
        self.end_dot.setBrush(brush)

    def contextMenuEvent(self, event):
        menu = QMenu()

        inner = menu.addAction("Inner Join")
        left = menu.addAction("Left Join")
        right = menu.addAction("Right Join")

        menu.addSeparator()
        remove = menu.addAction("Remove join")

        action = menu.exec(event.screenPos())
        if not action:
            return

        # Cambio tipo join
        if action in (inner, left, right):
            self.join.join_type = action.text().split()[0].upper()
            self.join.view.update_join_style(self.join)
        # Eliminazione join
        elif action == remove:
            view = self.join.view
            join = self.join
            # rimuovi riferimenti dai campi
            if join in join.f1.joins:
                join.f1.joins.remove(join)
            if join in join.f2.joins:
                join.f2.joins.remove(join)
            # rimuovi dalla view
            if join in view.joins:
                view.joins.remove(join)
            # rimuovi linea grafica
            view.scene.removeItem(join.line)
        # aggiorna SQL
        if self.join.view.parent_widget:
            self.join.view.parent_widget.update_sql_preview()

class JoinItem:
    def __init__(self, f1, f2, line, join_type="INNER", view=None):
        self.f1 = f1
        self.f2 = f2
        self.line = line
        self.join_type = join_type
        self.view = view

class FieldItem(QGraphicsRectItem):
    def __init__(self, name, parent, view, is_pk=False, is_fk=False):
        super().__init__(parent)
        self.name = name
        self.parent_table = parent
        self.view = view
        self.is_pk = is_pk
        self.is_fk = is_fk
        self.joins = []

        self.filter = ""
        self.order = ""

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setRect(0, 0, parent.rect().width() - 16, 16)
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        # Testo del campo
        self.text = QGraphicsSimpleTextItem(name, self)
        self.text.setPos(18, 0)

        # Icona per Chiave Primaria (PK)
        if is_pk:
            self.icon = QGraphicsEllipseItem(4, 4, 8, 8, self)
            self.icon.setBrush(QBrush(QColor("gold")))
            self.icon.setPen(QPen(Qt.GlobalColor.black))
        else:
            # Creiamo un elemento di testo per la spunta verde (sarà nascosto all'inizio)
            self.icon = QGraphicsSimpleTextItem("", self)
            self.icon.setPos(4, -2)
            font_v = QFont()
            font_v.setBold(True)
            self.icon.setFont(font_v)
            self.icon.setBrush(QBrush(QColor("green")))

    def update_visual_state(self):
        """Aggiorna la grafica del campo se è selezionato nella query o meno"""
        font = QFont()
        if self.view.parent_widget and self in self.view.parent_widget.selected_fields:
            # ---- STATO SELEZIONATO ----
            font.setBold(True)
            self.text.setFont(font)
            self.text.setBrush(QBrush(QColor("#1A5276"))) # Blu scuro nei campi attivi
            
            if not self.is_pk:
                self.icon.setText("✓") # Mostra la spunta se non è PK
        else:
            # ---- STATO NORMALE ----
            font.setBold(False)
            self.text.setFont(font)
            self.text.setBrush(QBrush(Qt.GlobalColor.black))
            
            if not self.is_pk:
                self.icon.setText("") # Nasconde la spunta

    def mouseDoubleClickEvent(self, event):
        if self.view.parent_widget:
            if self not in self.view.parent_widget.selected_fields:
                self.view.parent_widget.selected_fields.append(self)
            else:
                # il doppio clic consecutivo ora lo rimuove anche!
                self.view.parent_widget.selected_fields.remove(self)
                self.filter = ""
                self.order = ""
            
            # Aggiorna la grafica di questo campo e la preview SQL
            self.update_visual_state()
            self.view.parent_widget.update_sql_preview()
        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu()
        filter_action = menu.addAction("Set Filter")
        order_action = menu.addAction("Set Order By")
        remove_action = menu.addAction("Remove field from SELECT")
        action = menu.exec(event.screenPos())
        
        if not action:
            return

        if action == filter_action:
            text, ok = QInputDialog.getText(None, "Filter", f"Filter for {self.name}:", text=self.filter)
            if ok:
                self.filter = text
                if self.view.parent_widget and self not in self.view.parent_widget.selected_fields:
                    self.view.parent_widget.selected_fields.append(self)
        elif action == order_action:
            items = ["ASC", "DESC"]
            text, ok = QInputDialog.getItem(None, "Order", f"Order {self.name}:", items, editable=False)
            if ok:
                self.order = text
                if self.view.parent_widget and self not in self.view.parent_widget.selected_fields:
                    self.view.parent_widget.selected_fields.append(self)
        elif action == remove_action:
            if self.view.parent_widget and self in self.view.parent_widget.selected_fields:
                self.view.parent_widget.selected_fields.remove(self)
                self.filter = ""
                self.order = ""

        # Aggiorna sia l'aspetto visivo del campo che la preview SQL
        self.update_visual_state()
        if self.view.parent_widget:
            self.view.parent_widget.update_sql_preview()

class TableItem(QGraphicsRectItem):
    def __init__(self, name, comment, fields, view, alias=""):
        # dimensione totale
        super().__init__(0, 0, 190, 30 + len(fields) * 18)
        self.name = name
        self.comment = comment
        self.view = view
        self.alias = alias  # ✅ Memorizza l'alias (es. "T1")
        self.field_items = []

        # flags per drag, selezione, aggiornamenti
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        # Titolo integrato con Alias: Nome (Alias) - Commento
        full_title = f"{name} ({alias})" + (f" - {comment}" if comment else "")

        font = QFont()
        font.setBold(True)
        font.setPointSize(8)

        metrics = QFontMetrics(font)

        max_width = int(self.rect().width() - 16)
        elided = metrics.elidedText(
            full_title,
            Qt.TextElideMode.ElideRight,
            max_width
        )

        self.title_text = QGraphicsSimpleTextItem(elided, self)
        self.title_text.setFont(font)
        self.title_text.setPos(8, 4)
        self.title_text.setToolTip(full_title)

        # campi
        for i, f in enumerate(fields):
            field = FieldItem(**f, parent=self, view=view)
            field.setPos(10, 26 + i * 16)
            self.field_items.append(field)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        radius = 8
        title_height = 24

        # ---- Titolo (solo angoli superiori stondati) ----
        title_rect = QRectF(rect.left(), rect.top(), rect.width(), title_height)
        path = QPainterPath()
        path.moveTo(title_rect.bottomLeft())
        path.lineTo(title_rect.topLeft().x(), title_rect.topLeft().y() + radius)
        path.quadTo(title_rect.topLeft().x(), title_rect.topLeft().y(),
                    title_rect.topLeft().x() + radius, title_rect.topLeft().y())
        path.lineTo(title_rect.topRight().x() - radius, title_rect.topRight().y())
        path.quadTo(title_rect.topRight().x(), title_rect.topRight().y(),
                    title_rect.topRight().x(), title_rect.topRight().y() + radius)
        path.lineTo(title_rect.bottomRight())
        path.lineTo(title_rect.bottomLeft())
        path.closeSubpath()

        painter.fillPath(path, QBrush(QColor("#85C1E9")))

        # ---- Corpo ----
        body_rect = QRectF(rect.left(), rect.top() + title_height, rect.width(), rect.height() - title_height)
        painter.setBrush(QColor("#AED6F1"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(body_rect)

        # ---- Bordo stondato in alto ----
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.isSelected():
            painter.setPen(QPen(QColor("#1ABC9C"), 2))
        else:
            painter.setPen(QPen(QColor("#5DADE2")))
        painter.drawPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            for f in self.field_items:
                for j in f.joins:
                    self.view.update_join_position(j)
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        remove_action = menu.addAction("Remove table")
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
            self.start_field = parent if isinstance(parent, FieldItem) else None
        else:
            self.start_field = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start_field:
            scene_pos = self.mapToScene(event.position().toPoint())
            item = self.scene.itemAt(scene_pos, QTransform())
            if isinstance(item, FieldItem):
                f2 = item
            elif isinstance(item, (QGraphicsSimpleTextItem, QGraphicsEllipseItem)):
                parent = item.parentItem()
                f2 = parent if isinstance(parent, FieldItem) else None
            else:
                f2 = None

            if f2 and f2 != self.start_field:
                self.create_join(self.start_field, f2)

        self.start_field = None
        super().mouseReleaseEvent(event)

    def create_join(self, f1, f2, join_type="INNER"):
        line = JoinLine(None)
        self.scene.addItem(line)
        join = JoinItem(f1, f2, line, join_type, view=self)
        line.join = join
        self.joins.append(join)
        f1.joins.append(join)
        f2.joins.append(join)
        self.update_join_style(join)
        self.update_join_position(join)
        if self.parent_widget:
            self.parent_widget.update_sql_preview()

    def update_join_position(self, join):
        r1 = join.f1.sceneBoundingRect()
        r2 = join.f2.sceneBoundingRect()
        if r1.center().x() < r2.center().x():
            p1 = QPointF(r1.right(), r1.center().y())
            p2 = QPointF(r2.left(), r2.center().y())
        else:
            p1 = QPointF(r1.left(), r1.center().y())
            p2 = QPointF(r2.right(), r2.center().y())
        join.line.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def update_join_style(self, join):
        colors = {
            "INNER": QColor("#2574A8"),
            "LEFT": QColor("#27AE60"),
            "RIGHT": QColor("#F39C12")
        }
        color = colors.get(join.join_type, QColor("#2574A8"))
        join.line.set_color(color)

# ============================================================
# QUERY DESIGNER MAIN WINDOW
# ============================================================
class QueryDesigner(QMainWindow):         
    def __init__(self, conn, schema, file_to_load=None, parent=None):
        # Passiamo il parent al costruttore di QMainWindow
        super().__init__(parent)         
        # Aggiungiamo un flag per renderla una finestra indipendente ma legata al parent
        self.setWindowFlags(Qt.WindowType.Window)
        
        self.setWindowTitle("Query Designer")
        self.resize(1600, 850)
        icon = QIcon()
        icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)

        self.meta = OracleMetadata(conn, schema)
        self.conn = conn
        self.selected_fields = []

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        font = QFont()
        font.setPointSize(8)        

        # LEFT
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.search_field = QLineEdit()
        self.search_field.textChanged.connect(self.filter_tree)
        
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Table", "Comment"])
        self.tree.setIndentation(0)
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 200)
        self.tree.setFont(font)
        self.tree.setAlternatingRowColors(True)
        
        left_layout.addWidget(self.search_field)
        left_layout.addWidget(self.tree)
        main_splitter.addWidget(left_widget)

        # CENTER
        self.scene = QGraphicsScene()
        self.view = DesignerView(self.scene, parent_widget=self)
        main_splitter.addWidget(self.view)

        # RIGHT
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.sql_preview = QTextEdit()

        # ---- BUTTON BAR ----
        button_bar = QWidget()
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(4, 4, 4, 4)

        btn_save = QPushButton(QIcon("icons:disk.png"), QCoreApplication.translate('query_designer','Save'))
        btn_load = QPushButton(QIcon("icons:folder.png"), QCoreApplication.translate('query_designer','Load'))
        btn_exec = QPushButton(QIcon("icons:go.png"), QCoreApplication.translate('query_designer','Preview'))
        btn_copy = QPushButton(QIcon("icons:copy.png"), QCoreApplication.translate('query_designer','Copy SQL'))

        btn_save.clicked.connect(self.save_json)
        btn_load.clicked.connect(self.load_json)
        btn_exec.clicked.connect(self.run_query)
        btn_copy.clicked.connect(self.copy_sql_to_clipboard)

        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_load)
        button_layout.addWidget(btn_exec)
        button_layout.addStretch()
        button_layout.addWidget(btn_copy)

        self.result_table = QTableWidget()

        right_splitter.addWidget(self.sql_preview)
        right_splitter.addWidget(button_bar)
        right_splitter.addWidget(self.result_table)

        right_splitter.setStretchFactor(0, 2)
        right_splitter.setStretchFactor(1, 0)
        right_splitter.setStretchFactor(2, 3)

        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(1, 4)

        self.load_metadata()
        self.tree.itemDoubleClicked.connect(self.add_table)

        # ✅ Se è stato passato un file all'avvio, lo carica immediatamente
        if file_to_load:
            self.apri_file_diagramma(file_to_load)

    def apri_file_diagramma(self, fn):
        """Metodo centralizzato per leggere il file JSON/MSQL_QD ed inserirlo nella scena"""
        try:
            with open(fn) as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Impossibile leggere il file:\n{str(e)}")
            return
            
        self.scene.clear()
        self.view.joins.clear()
        self.selected_fields = []
        tables_map = {}
        
        # 1. Ripristino delle tabelle
        for idx, t in enumerate(data["tables"]):
            alias = t.get("alias", f"T{idx+1}")             
            pk = self.meta.pk(t["name"])
            fields = [{"name": c, "is_pk": c in pk, "is_fk": False} for c in self.meta.columns(t["name"])]
            comment = next((c for n, c in self.meta.tables() if n == t["name"]), "")            
            
            ti = TableItem(t["name"], comment, fields, self.view, alias=alias)
            ti.setPos(QPointF(t["x"], t["y"]))
            self.scene.addItem(ti)            
            tables_map[alias] = ti
            
        # 2. Ripristino dei campi
        for f in data.get("fields", []):
            t = tables_map.get(f["table"])
            if t:
                fi = next((x for x in t.field_items if x.name == f["name"]), None)
                if fi:
                    fi.filter = f.get("filter", "")
                    fi.order = f.get("order", "")
                    self.selected_fields.append(fi)                
                    fi.update_visual_state() 
                    
        # 3. Ripristino delle linee di Join
        for j in data.get("joins", []):
            t1 = tables_map.get(j["t1"])
            t2 = tables_map.get(j["t2"])
            if t1 and t2:
                f1 = next((f for f in t1.field_items if f.name == j["f1"]), None)
                f2 = next((f for f in t2.field_items if f.name == j["f2"]), None)
                if f1 and f2:
                    self.view.create_join(f1, f2, j["type"])
                    
        self.update_sql_preview()

    def copy_sql_to_clipboard(self):
        QApplication.clipboard().setText(self.sql_preview.toPlainText())
        QToolTip.showText(QCursor.pos(),QCoreApplication.translate('query_designer','SQL copiato nella clipboard'),self)

    def load_metadata(self):
        for t, comment in self.meta.tables():
            node = QTreeWidgetItem([t, comment])
            node.setData(0, Qt.ItemDataRole.UserRole, (t, comment))
            self.tree.addTopLevelItem(node)

    def filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            name, comment = item.data(0, Qt.ItemDataRole.UserRole)
            match_name = text in name.lower()
            match_comment = text in comment.lower() if comment else False            
            # Mostra l'elemento se c'è una corrispondenza in uno dei due campi, altrimenti nascondilo
            item.setHidden(not (match_name or match_comment))

    def add_table(self, item):
        name, comment = item.data(0, Qt.ItemDataRole.UserRole)
        existing_tables = [i for i in self.scene.items() if isinstance(i, TableItem)]
        
        # Permettiamo di inserire la stessa tabella più volte usando gli alias!
        # Rimuoviamo il blocco 'if any(...): return' precedente.

        # Genera alias progressivo (T1, T2, T3...)
        alias_num = len(existing_tables) + 1
        alias = f"T{alias_num}"

        pk = self.meta.pk(name)
        fields = [{"name": c, "is_pk": c in pk, "is_fk": False} for c in self.meta.columns(name)]
        
        # Passiamo l'alias al costruttore
        t = TableItem(name, comment, fields, self.view, alias=alias)

        # posizione
        x = max([i.pos().x() + i.rect().width() + 40 for i in existing_tables], default=60)
        y = 60
        t.setPos(QPointF(x, y))
        self.scene.addItem(t)
        self.update_sql_preview()

    def update_sql_preview(self):
        tables = [item for item in self.scene.items() if isinstance(item, TableItem)]
        if not tables:
            self.sql_preview.setPlainText("-- nessuna tabella")
            return

        # =========================
        # SELECT (usa gli alias dei parent_table)
        # =========================
        select = [f"{f.parent_table.alias}.{f.name}" for f in self.selected_fields]
        if not select:
            select.append("*")
        sql = "SELECT " + ", ".join(select)

        # =========================
        # FROM + JOIN
        # =========================
        joins = self.view.joins
        used_tables = set()  # memorizziamo gli alias usati

        if joins:
            # --- prima join ---
            first = joins[0]
            t1_name, t1_alias = first.f1.parent_table.name, first.f1.parent_table.alias
            t2_name, t2_alias = first.f2.parent_table.name, first.f2.parent_table.alias
            
            cond = f"{t1_alias}.{first.f1.name} = {t2_alias}.{first.f2.name}"
            join_type = first.join_type.upper()
            
            # Sintassi: FROM TABELLA1 T1 INNER JOIN TABELLA2 T2 ON T1.CAMPO = T2.CAMPO
            sql += f"\nFROM {t1_name} {t1_alias} {join_type} JOIN {t2_name} {t2_alias} ON {cond}"
            used_tables.update([t1_alias, t2_alias])

            # --- join successive ---
            for j in joins[1:]:
                t1_name, t1_alias = j.f1.parent_table.name, j.f1.parent_table.alias
                t2_name, t2_alias = j.f2.parent_table.name, j.f2.parent_table.alias
                cond = f"{t1_alias}.{j.f1.name} = {t2_alias}.{j.f2.name}"
                join_type = j.join_type.upper()

                # determino quale tabella (alias) è nuova
                new_table_name = None
                new_table_alias = None
                if t2_alias not in used_tables:
                    new_table_name = t2_name
                    new_table_alias = t2_alias
                elif t1_alias not in used_tables:
                    new_table_name = t1_name
                    new_table_alias = t1_alias

                if new_table_alias:
                    sql += f"\n{join_type} JOIN {new_table_name} {new_table_alias} ON {cond}"
                    used_tables.add(new_table_alias)
                else:
                    # entrambe già incluse → solo condizione AND
                    sql += f"\nAND {cond}"
        else:
            # nessuna join grafica → FROM semplice con alias (es: FROM CLIENTI T1, FATTURE T2)
            sql += "\nFROM " + ", ".join(f"{t.name} {t.alias}" for t in tables)

        # =========================
        # FILTRI (WHERE / AND usando alias)
        # =========================
        filters = [f"{f.parent_table.alias}.{f.name} {f.filter}" 
                for f in self.selected_fields if f.filter]
        if filters:
            sql += ("\nWHERE " if not joins else "\nAND ") + " AND ".join(filters)

        # =========================
        # ORDINI (ORDER BY usando alias)
        # =========================
        orders = [f"{f.parent_table.alias}.{f.name} {f.order}" 
                for f in self.selected_fields if f.order]
        if orders:
            sql += "\nORDER BY " + ", ".join(orders)

        # =========================
        # aggiorna la preview
        # =========================
        self.sql_preview.setPlainText(sql)

    def save_json(self):
        fn, _ = QFileDialog.getSaveFileName(self, QCoreApplication.translate('query_designer','Save diagram'), "", "MSql Query Designer (*.msql_qd)")
        if not fn:
            return

        data = {"tables": [], "joins": [], "fields": []}

        for item in self.scene.items():
            if isinstance(item, TableItem):
                data["tables"].append({
                    "name": item.name,
                    "alias": item.alias, # Salva l'alias univoco della tabella
                    "x": item.pos().x(),
                    "y": item.pos().y()
                })

                for f in item.field_items:
                    # Salviamo solo i campi che hanno filtri o ordinamenti attivi o sono in SELECT
                    if f.filter or f.order or (f in self.selected_fields):
                        data["fields"].append({
                            "table": item.alias, # colleghiamo il campo all'alias, non al nome
                            "name": f.name,
                            "filter": f.filter,
                            "order": f.order
                        })

        for j in self.view.joins:
            data["joins"].append({
                "t1": j.f1.parent_table.alias, # salviamo l'alias di partenza
                "f1": j.f1.name,
                "t2": j.f2.parent_table.alias, # salviamo l'alias di arrivo
                "f2": j.f2.name,
                "type": j.join_type
            })

        with open(fn, "w") as f:
            json.dump(data, f, indent=2)

    def load_json(self):
        """Apertura tramite pulsante grafico della toolbar"""
        fn, _ = QFileDialog.getOpenFileName(self, QCoreApplication.translate('query_designer','Open diagram'), "", "MSql Query Designer (*.msql_qd)")
        if fn:
            self.apri_file_diagramma(fn)

    def run_query(self):
        sql = self.sql_preview.toPlainText()
        Freccia_Mouse(True)
        if not sql.strip(): return
        try:
            cur = self.conn.cursor()
            cur.execute(sql + " FETCH FIRST 50 ROWS ONLY")
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            self.result_table.setColumnCount(len(cols))
            self.result_table.setHorizontalHeaderLabels(cols)
            self.result_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.result_table.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            v_text = QCoreApplication.translate('query_designer',"Errore durante l'esecuzione della query:")
            QMessageBox.critical(self, QCoreApplication.translate('query_designer','SQL Error'), f"{v_text}\n{str(e)}")
        Freccia_Mouse(False)

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