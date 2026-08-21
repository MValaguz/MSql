#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11 con libreria pyqt6
#  Contenuto.....: Contiene classi di utilità per MSql

#Libreria di sistema
import os
import sys
#Libreria oracle
import oracledb
#Librerie grafiche 
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Libreria network usata per capire se MSql è già in esecuzione
from PyQt6.QtNetwork import *
# Libreria che permette di creare arte ascii grafica
from art import text2art, FONT_NAMES
#Utilità
from utilita import centra_window_figlia, message_error
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

class classChangeLog(QWidget):
    """
       Visualizza in una window specifica, il file di changelog
    """
    def __init__(self,p_window_padre):
        super().__init__()
        self.setWindowTitle("MSql-Changelog")
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(v_icon)
        self.setGeometry(0, 0, 600, 500)

        layout = QVBoxLayout()
        # creo un text edit di sola lettura dove visualizzo il contenuto del changelog
        self.text_edit = QTextEdit()
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setReadOnly(True)  
        # imposto font a larghezza fissa per migliore visualizzazione
        v_font = QFont()
        v_font.setFamily("Courier New")
        v_font.setPointSize(10)
        self.text_edit.setFont(v_font)

        # se sto eseguendo il programma da pyinstaller, vado in apposita cartella
        v_nome_file = "help/changelog.txt"
        if getattr(sys, 'frozen', False): 
            v_nome_file = "_internal/" + v_nome_file               
        elif os.name == "posix":
            v_nome_file = os.getcwd() + '/source/' + v_nome_file
        else:
            v_nome_file = os.getcwd() + '/' + v_nome_file

        # leggo il file di changelog
        try:            
            with open(v_nome_file, "r", encoding='UTF-8') as file:
                self.text_edit.setText(file.read())
        except:
            pass

        # imposto il layout
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        # centro la window rispetto alla window padre
        centra_window_figlia(p_window_padre, self)

class classFontArtViewer(QWidget):
    """
       Visualizza in una window specifica, elenco dei font che mette a disposizione la libreria ascii art 
    """
    def __init__(self, p_window_padre, o_global_preferences, v_global_font_ascii_art):        
        super().__init__()        
        self.v_font_ascii_art = v_global_font_ascii_art
        self.setWindowTitle("Ascii art Font Selector")
        v_icon = QIcon()
        v_icon.addPixmap(QPixmap("icons:MSql.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(v_icon)
        self.setGeometry(0, 0, 400, 450)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        # creo la lista dei font dove il primo elemento è il vuoto che corrisponde al default
        v_lista = []
        v_lista.append('')
        for i in FONT_NAMES:            
            v_lista.append(i)
        self.list_widget.addItems(v_lista)
        layout.addWidget(self.list_widget)        
            
        # Label informativa
        info_label = QLabel(QCoreApplication.translate('MSql_win1',"Double-click to select the font"))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        layout.addWidget(info_label)
        
        # Area di anteprima dove il font è lo stesso impostato come preferenza dell'editor
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)        
        v_split = o_global_preferences.font_editor.split(',')                        
        v_font = QFont(str(v_split[0]),int(v_split[1]))
        self.preview.setFont(v_font)  
        layout.addWidget(self.preview)

        # Compongo il layout
        self.setLayout(layout)

        # mi posiziono sul font attualmente attivo 
        if v_global_font_ascii_art != '' and v_global_font_ascii_art in FONT_NAMES:
            index = self.list_widget.findItems(v_global_font_ascii_art, Qt.MatchFlag.MatchExactly)
            if index:
                self.list_widget.setCurrentItem(index[0])
                self.list_widget.scrollToItem(index[0])

        # Evento click per anteprima e doppio click per la scelta
        self.list_widget.currentItemChanged.connect(lambda item: self.update_preview(item.text()))        

        # centro la window rispetto alla window padre
        centra_window_figlia(p_window_padre, self)

    def update_preview(self, font_name):        
        """
           Visualizza anteprima del font
        """
        art_text = text2art("art", font=font_name)
        self.preview.setPlainText(art_text)

def return_ascii_art_text(p_text, p_font_ascii_art):
    """ 
         Restituisce il testo in ascii art, con il font selezionato 
    """
    if p_font_ascii_art == '':
       return text2art(p_text)
    else:
       return text2art(p_text, p_font_ascii_art)

class classSingleInstanceManager(QObject):
    """
       Classe che avvia un server che controlla all'avvio di MSql, se ci sono altre istanze di MSql in esecuzione
       Questa classe è utilizzata per permettere di aprire un file, facendo doppio click da desktop, nella stessa
       istanza già in esecuzione di MSql. Il codice di chiamata è tutto concentrato nella sezione di Start.
    """
    # Adesso emettiamo un singolo percorso (str), non più lista
    messageReceived = pyqtSignal(str)    

    def __init__(self, server_name: str):
        super().__init__()
        self.server_name = server_name
        self.server = None

    def try_send_to_running_instance(self, file_path: str) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(200):
            socket.abort()
            return False

        try:
            # Invia il percorso come stringa UTF-8
            data = file_path.encode("utf-8")
            socket.write(data)
            socket.flush()
            socket.waitForBytesWritten(200)
        finally:
            socket.disconnectFromServer()
            socket.close()

        return True

    def start_listening(self) -> bool:
        QLocalServer.removeServer(self.server_name)
        self.server = QLocalServer(self)
        if not self.server.listen(self.server_name):
            return False
        self.server.newConnection.connect(self._handle_new_connection)
        return True

    def _handle_new_connection(self):
        while self.server.hasPendingConnections():
            sock = self.server.nextPendingConnection()
            sock.readyRead.connect(lambda s=sock: self._read_message(s))

    def _read_message(self, socket: QLocalSocket):
        raw = socket.readAll().data()
        try:
            # Decodifica semplice del path
            path = raw.decode("utf-8")            
            self.messageReceived.emit(path)
        except Exception as e:
            print(f"Errore da clasInstanceManager gestore SIM! Messaggio non valido: {e}")
        finally:
            socket.disconnectFromServer()
            socket.close()

class MyFileExtensionFilterProxyModel(QSortFilterProxyModel):
    """
       Filtra i file mostrati nel file system tree view:
        - Esclude file e cartelle nascoste
        - Mostra tutte le cartelle visibili per navigare
        - Mostra solo i file che NON hanno estensioni vietate
        - (Opzionale) Applica un filtro regex sui nomi dei file
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.not_allowed_extensions = ['.dat', '.rnd', '.dll', '.bat', '.exe', '.rhk']
        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        if not index.isValid():
            return False

        file_info = QFileInfo(model.filePath(index))

        # Escludi file e cartelle nascoste
        if file_info.isHidden() or file_info.fileName().startswith('.'):
            return False

        # Le cartelle visibili devono sempre comparire per la navigazione
        if file_info.isDir():
            return True

        # Escludi file con estensioni vietate
        file_name = file_info.fileName().lower()
        if any(file_name.endswith(ext) for ext in self.not_allowed_extensions):
            return False

        # Applica filtro regex (solo ai file)
        regex = self.filterRegularExpression()
        if regex and regex.pattern():
            return regex.match(file_name).hasMatch()

        return True

class CompactListDelegate(QStyledItemDelegate):
    """
       Dopo essere passati alla versione 6.10 delle librerie PyQt, l'altezza delle righe di alcuni oggetti non era più corretta
       Tramite questa classe si forza l'altezza desiderata
    """
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(18)   # ← imposta qui l’altezza desiderata
        return size

class OracleTableDialog(QDialog):
    def __init__(self, parent, table_name, nomi_intestazioni, tipi_intestazioni, p_tipo="I"):
        """
        p_tipo: "I" per INSERT (comportamento standard con campi obbligatori)
                "S" per SEARCH/SELECT (nessun campo obbligatorio, genera la clausola WHERE)
        """
        super().__init__(parent if isinstance(parent, QDialog.__base__) else None)
        
        self.table_name = table_name
        self.nomi_intestazioni = nomi_intestazioni
        self.tipi_intestazioni = tipi_intestazioni
        self.p_tipo = p_tipo.upper()  # Forza il maiuscolo per evitare errori di battitura
        
        # Stringa SQL generata che verrà letta dalla finestra principale
        self.sql_generata = ""
        
        # Dizionario per mappare i widget e i relativi metadati
        self.mappa_widgets = {}
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.table_name.upper())
        layout_principale = QVBoxLayout(self)
        
        # Impostazione distanze fisse (Valori in pixel)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        # Numero di colonne di input desiderate
        COLONNE_MAX = 5        
        
        # Generazione dinamica dei campi di input nella griglia
        for idx, colonna in enumerate(self.nomi_intestazioni):            
            widget = QLineEdit()                
            riga = idx // COLONNE_MAX
            colonna_logica = idx % COLONNE_MAX            
            
            # Ogni colonna logica occupa 2 colonne fisiche (Label + Widget)
            col_fisica_label = colonna_logica * 2
            col_fisica_widget = col_fisica_label + 1            
            
            # Estrazione dei metadati dalla tupla di cursor.description
            tupla_descrizione = self.tipi_intestazioni[idx]
            tipo_oracle = tupla_descrizione[1]
            null_ok = tupla_descrizione[6]
            
            # Se p_tipo è "I" e null_ok è False, la colonna è obbligatoria. 
            # Se p_tipo è "S", forziamo l'obbligatorietà a False per tutti i campi.
            if self.p_tipo == "S":
                obbligatorio = False
            else:
                obbligatorio = not null_ok
            
            # Gestione del testo della Label
            testo_label = colonna
            if obbligatorio:
                testo_label += " (*)"
                widget.setPlaceholderText("Mandatory field")
            
            grid_layout.addWidget(QLabel(testo_label), riga, col_fisica_label)
            grid_layout.addWidget(widget, riga, col_fisica_widget)            
            
            # Memorizzazione del widget, del tipo Oracle e del flag di obbligatorietà
            self.mappa_widgets[colonna] = (widget, tipo_oracle, obbligatorio)
            
        layout_principale.addLayout(grid_layout)
        
        # Gestione testo del bottone in base alla modalità
        testo_bottone = "Create WHERE" if self.p_tipo == "S" else "Create INSERT"
        btn_azione = QPushButton(testo_bottone)
        btn_azione.clicked.connect(self.on_action_clicked)
        layout_principale.addWidget(btn_azione)

    def on_action_clicked(self):
        colonne_sql = []
        valori_sql = []            
        condizioni_where = []
        
        for colonna, (widget, tipo, obbligatorio) in self.mappa_widgets.items():                
            testo = widget.text().strip()
            
            # Validazione campi obbligatori (attiva solo in modalità "I")
            if obbligatorio and not testo:
                QMessageBox.warning(
                    self, 
                    "Mandatory Field Missing", 
                    f"The field '{colonna}' is mandatory and cannot be left empty."
                )
                return
            
            # Se il campo è vuoto, lo saltiamo in entrambe le modalità
            if not testo:
                continue
                
            # Formattazione del valore in base al tipo Oracle
            if tipo in (oracledb.NUMBER, oracledb.DB_TYPE_LONG):
                valore_formattato = testo.replace(",", ".")  
            elif tipo == oracledb.DATETIME:                                 
                valore_formattato = f"TO_DATE('{testo}', 'DD/MM/YYYY HH24:MI:SS')"
            else:
                valore_formattato = f"'{testo}'"                
            
            # Popolamento delle liste in base alla modalità operativa
            if self.p_tipo == "S":
                condizioni_where.append(f"{colonna} = {valore_formattato}")
            else:
                colonne_sql.append(colonna)
                valori_sql.append(valore_formattato)
        
        # Se l'utente non ha inserito alcun dato, evita di generare query vuote
        if self.p_tipo == "S" and not condizioni_where:
            self.reject()
            return
        elif self.p_tipo != "S" and not colonne_sql:
            self.reject()
            return

        # Generazione della stringa SQL finale
        if self.p_tipo == "S":
            str_where = " AND ".join(condizioni_where)
            self.sql_generata = f"\nWHERE {str_where};"
        else:
            str_colonne = ", ".join(colonne_sql)
            str_valori = ", ".join(valori_sql)
            self.sql_generata = f"\nINSERT INTO {self.table_name} ({str_colonne}) VALUES ({str_valori});"
            
        self.accept()