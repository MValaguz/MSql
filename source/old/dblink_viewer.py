#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 21/08/2025
#  Descrizione...: Scopo dello script è prendere visualizzare la situazione di link pubblici di un database
#  Note..........: Creata utilizzando CoPilot

import sys
import oracledb
from collections import defaultdict
from oracle_my_lib import inizializzo_client
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from utilita import message_error, Freccia_Mouse

class classDBLinkExplorer(QWidget):
    """
       Ricevendo in input una connessione Oracle, apre una window dove a sinistra viene presentato elenco dei link pubblici e a destra elenco degli oggetti che contengono
    """
    # Creazione di un segnale personalizzato che permetterà di restituire l'oggetto scelto tramite doppio click
    object_selected = pyqtSignal(str, str, str)

    def __init__(self, oracle_connection, parent=None):
        super().__init__(parent)
        self.cursor = oracle_connection.cursor()
        self.grouped_data = {}
        self.current_link = None
        self.setWindowTitle("Oracle DB Link Explorer")
        
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(v_icon)
        
        self.resize(700, 500)
        self._init_ui()
        self.load_db_links()

    def _init_ui(self):
        # Lista dei DB Link
        self.link_list = QListWidget()
        self.link_list.itemClicked.connect(self.on_link_selected)

        # Campo di ricerca
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(QCoreApplication.translate('dblink_viewer','Find objects..'))
        self.search_box.textChanged.connect(self.on_search_text_changed)

        # TreeView per gli oggetti
        self.tree_view = QTreeView()
        self.tree_view.doubleClicked.connect(self.on_tree_item_clicked)

        # Modello a due colonne
        self.model = QStandardItemModel()        
        self.tree_view.setModel(self.model)
        
        # Label informativa
        info_label = QLabel(QCoreApplication.translate('dblink_viewer',"Double-click to insert the item into the editor"))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        
        # Layout destro (ricerca + albero)
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.search_box)
        right_layout.addWidget(self.tree_view)
        right_layout.addWidget(info_label)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Splitter orizzontale
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.link_list)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)

        # Layout principale
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(splitter)        

    def load_db_links(self):
        """
           Lettura dei link pubblici
        """
        try:
            self.cursor.execute("""
                SELECT db_link
                  FROM all_db_links
                 WHERE owner = 'PUBLIC'
                 ORDER BY db_link
            """)
            links = [row[0] for row in self.cursor.fetchall()]
            self.link_list.clear()
            self.link_list.addItems(links)
        except Exception as e:
            message_error(str(e))

    def on_link_selected(self, item):
        """
           Caricamento degli oggetti dopo che è stato scelto il link
        """
        # azzero ricerca e albero, memorizzo il link corrente
        self.search_box.clear()
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Object", "Type"])

        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(True)
        
        # Configura header
        header = self.tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.repaint()
        self.current_link = item.text()        
        try:
            self.cursor.execute(f"""
                SELECT object_type, object_name
                  FROM all_objects@{self.current_link}
                 WHERE object_type IN (
                   'TABLE','VIEW','PROCEDURE','FUNCTION','PACKAGE'
                 )
                 ORDER BY object_type, object_name
            """)
            rows = self.cursor.fetchall()
            grouped = defaultdict(list)
            for obj_type, obj_name in rows:                
                grouped[obj_type].append(obj_name)

            self.grouped_data = grouped            
            self.populate_tree(grouped)
            self.tree_view.expandAll()

        except Exception as e:
            message_error(f"{self.current_link}:\n{e}")
            self.model.removeRows(0, self.model.rowCount())

        # sostituisce la freccia del mouse con icona "clessidra"
        Freccia_Mouse(False)

    def populate_tree(self, grouped):
        self.model.removeRows(0, self.model.rowCount())
        for obj_type in sorted(grouped):
            parent_item = QStandardItem(obj_type.capitalize())
            parent_item.setEditable(False)
            parent_item.setSelectable(False)
            for name in grouped[obj_type]:
                child = QStandardItem(name)
                child.setEditable(False)
                type_item = QStandardItem(obj_type)
                type_item.setEditable(False)
                parent_item.appendRow([child, type_item])
            self.model.appendRow(parent_item)

    def on_search_text_changed(self, text):
        if not self.grouped_data:
            return
        term = text.strip().lower()
        if term:
            filtered = {
                t: [n for n in names if term in n.lower()]
                for t, names in self.grouped_data.items()
                if any(term in n.lower() for n in names)
            }
        else:
            filtered = self.grouped_data
        self.populate_tree(filtered)
        self.tree_view.expandAll()

    def on_tree_item_clicked(self, index: QModelIndex):
        # emit solo per nodi foglia (object name)
        if not index.isValid() or index.parent() == QModelIndex():
            return

        # recupero nome e tipo
        obj_name = self.model.itemFromIndex(index.sibling(index.row(), 0)).text()
        obj_type = self.model.itemFromIndex(index.parent()).text().lower()

        # emetto il signal con link, tipo e nome
        self.object_selected.emit(self.current_link, obj_type, obj_name)

        # chiusura della window a seguito scelta effettuata
        self.close()

###
# TEST DELL'APPLICAZIONE
###
if __name__ == "__main__":
    inizializzo_client()
    conn = oracledb.connect(user="SMILE", password="SMILE", dsn="BACKUP_815")    

    app = QApplication(sys.argv)
    explorer = classDBLinkExplorer(conn)

    # esempio di connessione al signal
    explorer.object_selected.connect(
        lambda link, typ, name: print(f"Link: {link} — Tipo: {typ} — Nome: {name}")
    )

    explorer.show()
    sys.exit(app.exec())