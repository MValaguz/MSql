#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.13
#  Data..........: 15/04/2026
#  Descrizione...: Gestione delle ferie creata senza uso di QtDesigner e grande supporto di AI
import sys
import os
import sqlite3
from datetime import datetime, time, timedelta, date
# Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
# Esportazione Excel
import xlsxwriter
# Preferenze
from preferenze import preferenze
# Utilità
from utilita import centra_window_figlia

# amplifico la path per la ricerca delle icone
QDir.addSearchPath('icons',os.path.join(os.path.dirname(os.path.abspath(__file__)),'qtdesigner', 'icons'))

# --- DB INIT ---
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS UTENTI (UTENTE TEXT PRIMARY KEY, NOME_COGNOME TEXT, TOT_FERIE REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS FERIE (ID INTEGER PRIMARY KEY AUTOINCREMENT, UTENTE TEXT, 
                 DATA_E_ORA_INIZIO TEXT, DATA_E_ORA_FINE TEXT, TUTTO_IL_GIORNO INTEGER, 
                 NOTE TEXT, PROVVISORIO INTEGER DEFAULT 0, NON_CONTEGGIARE INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

# --- CALCOLO PASQUA ---
def get_easter_monday(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    # Lunedì dell'Angelo è il giorno dopo Pasqua
    pasqua = date(year, month, day)
    return pasqua + timedelta(days=1)

# --- LOGICA DI CONTROLLO FESTIVI ---
def is_non_working_day(qdate):
    d, m, y = qdate.day(), qdate.month(), qdate.year()
    festivi_richiesti = [(25, 4), (1, 5), (2, 6), (15, 8), (1, 11), (8, 12), (25, 12), (26,12), (27,12)]
    if qdate.dayOfWeek() >= 6: return True # Sabato e Domenica
    if (d, m) in festivi_richiesti: return True # Lista tua
    if qdate.toPyDate() == get_easter_monday(y): return True # Pasquetta
    return False

# --- CALENDARIO AVANZATO ---
class SharedCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.my_ferie = {}    
        self.others_ferie = {} 
        # Date festive fisse (giorno, mese)
        self.festivi_fissi = [(1,1), (6,1), (25,4), (1,5), (2,6), (15,8), (1,11), (8,12), (25,12), (26,12), (27,12)]

    def paintCell(self, painter, rect, qdate):
        # 1. Recupero logica festivi e tema
        is_holiday = is_non_working_day(qdate)
        is_today = (qdate == QDate.currentDate()) # <--- Controllo se è oggi
        is_dark = self.palette().color(self.backgroundRole()).lightness() < 128

        # 2. DISEGNO SFONDO MANUALE (Invece di super().paintCell)
        painter.save()
        
        # Colore di sfondo della cella standard
        bg_std = self.palette().color(self.backgroundRole())
        if is_holiday:
            # Sfondo festivo
            bg_color = QColor(44, 62, 80) if is_dark else QColor(225, 245, 254)
            painter.fillRect(rect, QBrush(bg_color))
        else:
            # Sfondo normale (pulito, senza il numero '1')
            painter.fillRect(rect, QBrush(bg_std))
        
        # 3. DISEGNO BORDI
        border_color = QColor(255, 255, 255, 60) if is_dark else QColor("#D3D3D3")
        painter.setPen(QPen(border_color, 1))         
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        painter.restore()

        # 4. DISEGNO NUMERO DEL GIORNO (In alto a destra)
        painter.save()
        if is_today:
            # Disegna il cerchietto verde di sfondo per il numero
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#107e3d")) # Un bel verde acceso
            
            # Posizioniamo il cerchio in alto a destra
            # rect.right()-20 sposta il cerchio a sinistra del bordo destro
            bg_rect = QRect(rect.right() - 20, rect.top() + 2, 20, 20)
            painter.drawEllipse(bg_rect) # Oppure drawRoundedRect per un rettangolo
            
            # Testo bianco sopra il verde per contrasto
            painter.setPen(QColor("white"))
        elif is_holiday:
            painter.setPen(QColor("#FF4D4D")) 
        else:
            painter.setPen(self.palette().color(self.foregroundRole()))
            
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        # Margine destro e superiore
        margin_rect = rect.adjusted(0, 2, -5, 0)
        painter.drawText(margin_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(qdate.day()))
        painter.restore()

        # 5. DISEGNO FERIE (Al centro)
        d_str = qdate.toString("yyyy-MM-dd")
        if d_str in self.my_ferie:
            h, is_provv, is_nc = self.my_ferie[d_str]
            painter.save()
            if is_provv == 1:
                color = QColor("#f39c12")    
            elif is_nc  == 1:
                color = QColor("#1f72df")
            else:
                color = QColor("#19e412")
            painter.setPen(color)
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            
            h_f = f"{h:.2f}".replace('.', ',')
            g_f = f"{(h/8):.2f}".replace('.', ',')
            txt = f"{h_f}h ({g_f}g)"
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, txt)
            painter.restore()

        # 6. ALTRI COLLEGHI (In alto a sinistra o sotto il numero)
        if d_str in self.others_ferie:
            colleghi = self.others_ferie[d_str]
            painter.save()
            others_color = QColor("#BDC3C7") if is_dark else QColor("#7f8c8d")
            painter.setPen(others_color)
            font = painter.font()
            font.setPointSize(7)
            font.setItalic(True)
            painter.setFont(font)
            
            nomi_str = "+ " + ", ".join(colleghi)
            # Rettangolo per i nomi (evitiamo sovrapposizione col numero a destra)
            others_rect = rect.adjusted(5, 15, -5, 0)
            elided = painter.fontMetrics().elidedText(nomi_str, Qt.TextElideMode.ElideRight, others_rect.width())
            painter.drawText(others_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, elided)
            painter.restore()

# --- DIALOG GESTIONE GIORNATA ---
class DayFerieDialog(QDialog):
    def __init__(self, uid, qdate, db_path, parent=None):
        super().__init__(parent)
        self.uid, self.qdate, self.db_path = uid, qdate, db_path
        self.setWindowTitle(f"Ferie del {qdate.toString('dd/MM/yyyy')}")
        self.resize(600, 350) # Leggermente più alta per accomodare la nuova riga
        layout = QVBoxLayout(self)

        # centro la window rispetto alla window padre
        centra_window_figlia(parent, self)
        
        # --- SEZIONE CREAZIONE ---
        layout.addWidget(QLabel("Creazione ferie:"))
        
        # Riga 1: Solo Checkbox
        checkbox_row = QHBoxLayout()
        self.all_day = QCheckBox("Tutto il giorno (8 ore)")
        self.provv_cb = QCheckBox("Provvisoria")
        self.non_contegg = QCheckBox("Non conteggiare")
        self.all_day.toggled.connect(self.handle_all_day)
        
        checkbox_row.addWidget(self.all_day)
        checkbox_row.addWidget(self.provv_cb)
        checkbox_row.addWidget(self.non_contegg)
        checkbox_row.addStretch() # Spinge le checkbox a sinistra
        layout.addLayout(checkbox_row)
        
        # Riga 2: Solo Orari
        time_row = QHBoxLayout()
        self.start_t = QTimeEdit(QTime(8, 0))
        self.end_t = QTimeEdit(QTime(17, 0))
        time_row.addWidget(QLabel("Ora Inizio:"))
        time_row.addWidget(self.start_t)
        time_row.addSpacing(20)
        time_row.addWidget(QLabel("Ora Fine:"))
        time_row.addWidget(self.end_t)
        time_row.addStretch() # Mantiene gli orari compatti a sinistra
        layout.addLayout(time_row)

        # Riga 3: Note + Bottone
        note_row = QHBoxLayout()
        self.note = QLineEdit()
        save_icon = QIcon()
        save_icon.addPixmap(QPixmap("icons:disk.png"), QIcon.Mode.Normal, QIcon.State.Off)
        btn_save = QPushButton(" Crea")
        btn_save.setIcon(save_icon)
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self.save_ferie)
        note_row.addWidget(QLabel("Note:"))
        note_row.addWidget(self.note)
        note_row.addWidget(btn_save)
        layout.addLayout(note_row)
        
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken))

        # --- SEZIONE ELENCO ---
        layout.addWidget(QLabel("Elenco ferie registrate:"))
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Full Day", "Inizio", "Fine", "Provv.", "No Cont.", "Note", "Azione"])
        
        h = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 70)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(6, 90)
        
        layout.addWidget(self.table)
        self.load_ferie()

    def handle_all_day(self, checked):
        if checked:
            self.start_t.setTime(QTime(8, 0))
            self.end_t.setTime(QTime(17, 0))
            self.start_t.setEnabled(False)
            self.end_t.setEnabled(False)
        else:
            self.start_t.setEnabled(True)
            self.end_t.setEnabled(True)

    def load_ferie(self):
        self.table.setRowCount(0)
        d_str = self.qdate.toString("yyyy-MM-dd")
        conn = sqlite3.connect(self.db_path)
        query = "SELECT ID, DATA_E_ORA_INIZIO, DATA_E_ORA_FINE, PROVVISORIO, NON_CONTEGGIARE, TUTTO_IL_GIORNO, NOTE FROM FERIE WHERE UTENTE=? AND DATA_E_ORA_INIZIO LIKE ?"
        rows = conn.execute(query, (self.uid, f"{d_str}%")).fetchall()
        
        for r_idx, r_data in enumerate(rows):
            fid, start, end, provv, no_cont, full_day, note_txt = r_data
            self.table.insertRow(r_idx)
            
            # crezione di un item centrato e non editabile per le colonne di testo
            def create_centered_item(text=""):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(Qt.ItemFlag.ItemIsEditable) # Impedisce modifica
                return item

            def set_centered_checkbox(col, checked):
                container = QWidget()
                chk = QCheckBox()
                chk.setCheckState(Qt.CheckState.Checked if checked == 1 else Qt.CheckState.Unchecked)
                chk.setEnabled(False)
                lay = QHBoxLayout(container)
                lay.addWidget(chk)
                lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lay.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(r_idx, col, container)

            set_centered_checkbox(0, full_day)
            self.table.setItem(r_idx, 1, create_centered_item(start.split("T")[-1][:5]))            
            self.table.setItem(r_idx, 2, create_centered_item(end.split("T")[-1][:5]))
            set_centered_checkbox(3, provv)
            set_centered_checkbox(4, no_cont)
            self.table.setItem(r_idx, 5, create_centered_item(str(note_txt or "")))

            btn_del = QPushButton("Elimina")
            btn_del.clicked.connect(lambda chk, f=fid: self.del_f(f))
            self.table.setCellWidget(r_idx, 6, btn_del)
        conn.close()

    def save_ferie(self):
        d_p = self.qdate.toString("yyyy-MM-dd")
        is_full = 1 if self.all_day.isChecked() else 0
        
        conn = sqlite3.connect(self.db_path)
        check = conn.execute("SELECT TUTTO_IL_GIORNO FROM FERIE WHERE UTENTE=? AND DATA_E_ORA_INIZIO LIKE ?", 
                             (self.uid, f"{d_p}%")).fetchall()
        
        if any(r[0] == 1 for r in check):
            QMessageBox.warning(self, "Attenzione", "Esiste già una richiesta per l'intera giornata.")
            conn.close()
            return
        
        if is_full and len(check) > 0:
            QMessageBox.warning(self, "Attenzione", "Impossibile inserire 'Tutto il giorno' se esistono già permessi parziali.")
            conn.close()
            return

        s_dt = datetime.combine(self.qdate.toPyDate(), self.start_t.time().toPyTime()).isoformat()
        e_dt = datetime.combine(self.qdate.toPyDate(), self.end_t.time().toPyTime()).isoformat()
        
        conn.execute("INSERT INTO FERIE (UTENTE, DATA_E_ORA_INIZIO, DATA_E_ORA_FINE, TUTTO_IL_GIORNO, NOTE, PROVVISORIO, NON_CONTEGGIARE) VALUES (?,?,?,?,?,?,?)",
                     (self.uid, s_dt, e_dt, is_full, self.note.text(), 1 if self.provv_cb.isChecked() else 0, 1 if self.non_contegg.isChecked() else 0))
        conn.commit()
        conn.close()
        self.accept()

    def del_f(self, fid):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM FERIE WHERE ID=?", (fid,))
        conn.commit()
        conn.close()
        self.accept()

# --- CLASSI DI SUPPORTO ---
class UserManagement(QDialog):
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.setWindowTitle("Anagrafica Utenti")
        self.resize(400, 200)
        layout = QVBoxLayout(self)
        
        # centro la window rispetto alla window padre
        centra_window_figlia(parent, self)
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Codice", "Cognome e nome", "Ore Totali"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Connettiamo il segnale di modifica dopo aver caricato i dati
        layout.addWidget(self.table)
        
        btn_h = QHBoxLayout()
        add_btn = QPushButton("+ Nuovo"); add_btn.clicked.connect(self.add_u)
        del_btn = QPushButton("- Elimina"); del_btn.clicked.connect(self.del_u)
        btn_h.addWidget(add_btn); btn_h.addWidget(del_btn)
        layout.addLayout(btn_h)
        
        self.load_data()
        # Connettiamo il segnale solo dopo il primo caricamento per evitare loop
        self.table.itemChanged.connect(self.update_user)

    def load_data(self):
        self.table.blockSignals(True) # Evita che l'inserimento triggeri update_user
        self.table.setRowCount(0)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT UTENTE, NOME_COGNOME, TOT_FERIE FROM UTENTI")
        for r_idx, row in enumerate(cursor.fetchall()):
            self.table.insertRow(r_idx)
            # Colonna 0: Codice (Sola lettura)
            it0 = QTableWidgetItem(str(row[0]))
            it0.setFlags(it0.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r_idx, 0, it0)
            # Colonna 1: Nome
            self.table.setItem(r_idx, 1, QTableWidgetItem(str(row[1])))
            # Colonna 2: Ore
            self.table.setItem(r_idx, 2, QTableWidgetItem(f"{row[2]:.2f}".replace('.', ',')))
        conn.close()
        self.table.blockSignals(False)

    def update_user(self, item):
        row = item.row()
        # Recuperiamo la chiave univoca (Codice) dalla colonna 0
        uid = self.table.item(row, 0).text()
        # Recuperiamo i nuovi valori dalle colonne 1 e 2
        nuovo_nome = self.table.item(row, 1).text()
        nuove_ore_str = self.table.item(row, 2).text().replace(',', '.')
        
        try:
            nuove_ore = float(nuove_ore_str)
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE UTENTI SET NOME_COGNOME=?, TOT_FERIE=? WHERE UTENTE=?", 
                         (nuovo_nome, nuove_ore, uid))
            conn.commit()
            conn.close()
            # Feedback visivo opzionale nella barra di stato se necessario
        except ValueError:
            QMessageBox.warning(self, "Errore", "Formato ore non valido. Usa la virgola o il punto.")
            self.load_data() # Ripristina i dati precedenti

    def add_u(self):
        dlg = NewUserDialog(self)
        if dlg.exec():
            uid, n, h = dlg.get_data()
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO UTENTI VALUES (?,?,?)", (uid, n, float(h.replace(',', '.'))))
                conn.commit(); conn.close()
                self.load_data()
            except Exception as e: QMessageBox.critical(self, "Errore", f"Impossibile aggiungere: {e}")

    def del_u(self):
        curr = self.table.currentRow()
        if curr < 0: return
        uid = self.table.item(curr, 0).text()
        risposta = QMessageBox.question(self, "Conferma", f"Eliminare l'utente {uid}?")
        if risposta == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM UTENTI WHERE UTENTE=?", (uid,))
            conn.commit(); conn.close()
            self.load_data()

class NewUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuovo")
        layout = QFormLayout(self)
        self.id_in = QLineEdit(); self.n_in = QLineEdit(); self.h_in = QLineEdit()
        layout.addRow("Codice:", self.id_in); layout.addRow("Nome:", self.n_in); layout.addRow("Ore:", self.h_in)
        b = QPushButton("Salva"); b.clicked.connect(self.accept); layout.addWidget(b)
    def get_data(self): return self.id_in.text(), self.n_in.text(), self.h_in.text()

# --- TABELLONE ANNUALE ---
class AnnualReportDialog(QDialog):
    def __init__(self, uid, db_path, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.db_path = db_path
        self.setWindowTitle("Tabellone Annuale Ferie")
        self.resize(1400, 650)
        
        layout = QVBoxLayout(self)
        
        # Filtro Anno
        top_layout = QHBoxLayout()
        self.year_sel = QSpinBox()
        self.year_sel.setRange(2000, 2100)
        self.year_sel.setValue(QDate.currentDate().year())
        self.year_sel.valueChanged.connect(self.load_data)
        top_layout.addWidget(QLabel("Seleziona Anno:"))
        top_layout.addWidget(self.year_sel)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Tabellone (12 mesi x 31 giorni)
        self.table = QTableWidget(12, 31)
        self.months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                       "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        self.table.setVerticalHeaderLabels(self.months)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 32)])
        
        # Estetica tabella
        self.table.horizontalHeader().setDefaultSectionSize(30)
        self.table.verticalHeader().setDefaultSectionSize(35)
        layout.addWidget(self.table)
        
        # Legenda
        legenda = QHBoxLayout()
        legenda.addWidget(self.create_label(" Confermate", "#19e412"))
        legenda.addWidget(self.create_label(" Provvisorie", "#f39c12"))
        legenda.addWidget(self.create_label(" Non Conteggiate", "#1f72df"))
        layout.addLayout(legenda)

        self.load_data()

    def create_label(self, text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background-color: {color}; color: black; border-radius: 3px; padding: 2px; font-weight: bold;")
        return lbl

    def load_data(self):
        self.table.clearContents()
        year = self.year_sel.value()
        
        conn = sqlite3.connect(self.db_path)
        # Query con raggruppamento per sommare le ore del singolo giorno
        # Calcoliamo la differenza tra fine e inizio in ore (assumendo formato ISO)
        query = """
            SELECT 
                strftime('%Y-%m-%d', DATA_E_ORA_INIZIO) as giorno,
                SUM((julianday(DATA_E_ORA_FINE) - julianday(DATA_E_ORA_INIZIO)) * 24) as tot_ore,
                MAX(PROVVISORIO), 
                MAX(NON_CONTEGGIARE), 
                MAX(TUTTO_IL_GIORNO)
            FROM FERIE 
            WHERE UTENTE=? AND DATA_E_ORA_INIZIO LIKE ?
            GROUP BY giorno
        """
        rows = conn.execute(query, (self.uid, f"{year}%")).fetchall()
        conn.close()

        # Mappa: (mese, giorno) -> (ore, provv, nc, full)
        ferie_map = {}
        for r in rows:
            dt = QDate.fromString(r[0], "yyyy-MM-dd")
            ferie_map[(dt.month(), dt.day())] = r

        for m in range(1, 13):
            for d in range(1, 32):
                test_date = QDate(year, m, d)
                
                if not test_date.isValid():
                    item = QTableWidgetItem()
                    item.setBackground(QColor("#3F3C3C"))
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.table.setItem(m-1, d-1, item)
                    continue

                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Weekend
                if test_date.dayOfWeek() >= 6:
                    item.setBackground(QColor("#3F3C3C"))

                # Se ci sono ferie
                if (m, d) in ferie_map:
                    _, ore, is_provv, is_nc, is_full = ferie_map[(m, d)]
                    
                    # Colore (Priorità: Provvisorio > Non Conteggiato > Confermato)
                    color = "#19e412"
                    if is_provv: color = "#f39c12"
                    elif is_nc: color = "#1f72df"
                    
                    item.setBackground(QColor(color))
                    item.setForeground(QColor("black")) # Testo nero per contrasto
                    
                    # Formattazione testo simile al calendario
                    # Se è "tutto il giorno" forziamo 8h anche se il calcolo orario differisce
                    h_val = 8.0 if is_full else ore
                    g_val = h_val / 8.0
                    
                    txt = f"{h_val:.1f}h\n({g_val:.1f}g)"
                    item.setText(txt)
                    
                    font = item.font()
                    font.setPointSize(7)
                    font.setBold(True)
                    item.setFont(font)

                self.table.setItem(m-1, d-1, item)
        
        # Opzionale: adatta l'altezza delle righe per leggere il testo su due righe
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.horizontalHeader().setDefaultSectionSize(40)

# --- APP PRINCIPALE ---
class AppFerie(QMainWindow):
    def __init__(self, db_dir):
        super().__init__()
        
        # Configurazione Finestra
        icon = QIcon()
        icon.addPixmap(QPixmap("icons:MGrep.ico"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)
        
        self.db_dir = db_dir
        self.db_path = os.path.join(db_dir, 'calendar.db')
        init_db(self.db_path)
        self.setWindowTitle("Calendar")
        self.resize(900, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # --- BARRA DI NAVIGAZIONE ---
        nav = QHBoxLayout()
        
        # Profilo (Combo)        
        nav.addWidget(QLabel("Utente:"))
        self.user_sel = QComboBox()
        self.user_sel.setMinimumWidth(200)
        self.user_sel.currentIndexChanged.connect(self.refresh_ui)
        nav.addWidget(self.user_sel, 0)
                
        # --- LO SPACER (Molla) ---
        nav.addStretch()

        # Bottone Oggi        
        today_btn = QPushButton(" Oggi")
        today_btn.setToolTip("Vai alla data odierna")
        t_icon = QIcon()
        t_icon.addPixmap(QPixmap("icons:calendar.png"), QIcon.Mode.Normal, QIcon.State.Off)
        today_btn.setIcon(t_icon)

        today_btn.clicked.connect(lambda: self.cal.setSelectedDate(QDate.currentDate()))
        nav.addWidget(today_btn)
        
        # Bottone Gestione Utenti
        u_btn = QPushButton(" Gestione Utenti")
        u_btn.setToolTip("Aggiungi, modifica o elimina utenti")
        u_icon = QIcon()
        u_icon.addPixmap(QPixmap("icons:user.png"), QIcon.Mode.Normal, QIcon.State.Off)
        u_btn.setIcon(u_icon)
        u_btn.clicked.connect(self.open_users)
        nav.addWidget(u_btn)
        
        # Bottone Export
        x_btn = QPushButton(" Export")
        x_btn.setToolTip("Esporta le ferie dell'utente selezionato in un file Excel")
        x_icon = QIcon()
        x_icon.addPixmap(QPixmap("icons:excel.png"), QIcon.Mode.Normal, QIcon.State.Off)
        x_btn.setIcon(x_icon)
        x_btn.clicked.connect(self.to_excel)
        nav.addWidget(x_btn)
                
        # Bottone Tabellone Annuale
        a_btn = QPushButton(" Annuale")
        a_btn.setToolTip("Visualizza riepologo annuale delle ferie")
        a_icon = QIcon()
        a_icon.addPixmap(QPixmap("icons:table.png"), QIcon.Mode.Normal, QIcon.State.Off)
        a_btn.setIcon(a_icon)
        a_btn.clicked.connect(self.open_annual_report)
        nav.addWidget(a_btn)
        
        main_layout.addLayout(nav)

        # --- CALENDARIO ---
        self.cal = SharedCalendar()
        self.cal.clicked.connect(self.open_day)
        main_layout.addWidget(self.cal)

        # --- FOOTER ---
        footer = QHBoxLayout()
        self.stat_rich = QLabel("Richieste: 0h")
        self.stat_rim = QLabel("Residue: 0h")
        for s in [self.stat_rich, self.stat_rim]:
            s.setStyleSheet("font-weight: bold; font-size: 13px;")
            footer.addWidget(s)
        
        footer.addStretch()
        main_layout.addLayout(footer)
        
        self.load_users()
    
    def open_annual_report(self):
        # Recupera l'ID dell'utente selezionato nella combo
        uid = self.user_sel.currentData() 
        if uid:
            dialog = AnnualReportDialog(uid, self.db_path, self)
            centra_window_figlia(self, dialog) # Usiamo la tua funzione di centratura
            dialog.exec()

    def open_users(self):        
        UserManagement(self.db_path, self).exec()
        self.load_users()

    def load_users(self):
        self.user_sel.blockSignals(True)
        curr = self.user_sel.currentData()
        self.user_sel.clear()
        conn = sqlite3.connect(self.db_path)
        for u, n in conn.execute("SELECT UTENTE, NOME_COGNOME FROM UTENTI").fetchall():
            self.user_sel.addItem(n, u)
        conn.close()
        idx = self.user_sel.findData(curr)
        if idx >= 0: self.user_sel.setCurrentIndex(idx)
        self.user_sel.blockSignals(False)
        self.refresh_ui()
        self.cal.updateCells()

    def refresh_ui(self):
        my_uid = self.user_sel.currentData()
        if not my_uid: return
        
        conn = sqlite3.connect(self.db_path)
        
        # 1. Mie Ferie
        tot_res = conn.execute("SELECT TOT_FERIE FROM UTENTI WHERE UTENTE=?", (my_uid,)).fetchone()
        tot_user = tot_res[0] if tot_res else 0.0
        
        # Conteggio ore escludendo quelle da non conteggiare
        my_rows = conn.execute("SELECT DATA_E_ORA_INIZIO, DATA_E_ORA_FINE, TUTTO_IL_GIORNO, PROVVISORIO, NON_CONTEGGIARE FROM FERIE WHERE UTENTE=?", (my_uid,)).fetchall()
        my_map = {}
        total_used = 0.0
        for s, e, ad, pr, nc in my_rows:
            d_key = s.split("T")[0]
            h = 8.0 if ad == 1 else (datetime.fromisoformat(e) - datetime.fromisoformat(s)).total_seconds() / 3600
            old_h, old_pr, old_nc = my_map.get(d_key, (0.0, 0, 0))
            my_map[d_key] = (old_h + h, max(old_pr, pr), max(old_nc, nc))
            if nc == 0:
                total_used += h

        # 2. Altri Colleghi
        others_map = {}
        others_rows = conn.execute("""
            SELECT F.DATA_E_ORA_INIZIO, U.NOME_COGNOME 
            FROM FERIE F JOIN UTENTI U ON F.UTENTE = U.UTENTE 
            WHERE F.UTENTE != ?""", (my_uid,)).fetchall()
        
        for dt, nome in others_rows:
            d_key = dt.split("T")[0]
            if d_key not in others_map: others_map[d_key] = set()
            others_map[d_key].add(nome.split()[0]) # Solo primo nome

        conn.close()
        
        self.cal.my_ferie = my_map
        self.cal.others_ferie = {k: list(v) for k, v in others_map.items()}
        self.cal.updateCells()
        
        rich_str = f"{total_used:.2f}".replace('.', ',')
        rich_g_str = f"{(total_used/8):.2f}".replace('.', ',')
        self.stat_rich.setText(f"Richieste: {rich_str}h ({rich_g_str}g)")
        
        rem = tot_user - total_used
        rem_str = f"{rem:.2f}".replace('.', ',')
        rem_g_str = f"{(rem/8):.2f}".replace('.', ',')
        self.stat_rim.setText(f"Residue: {rem_str}h ({rem_g_str}g)")

    def open_day(self, qdate):
        # Blocco totale per Sabato, Domenica e Festivi
        if is_non_working_day(qdate):
            return 

        uid = self.user_sel.currentData()
        if uid:
            dlg = DayFerieDialog(uid, qdate, self.db_path, self)
            if dlg.exec():                
                self.refresh_ui()

    def to_excel(self):
        uid = self.user_sel.currentData()
        if not uid: return
        path = f"report_ferie_{uid}.xlsx"
        wb = xlsxwriter.Workbook(os.path.join(self.db_dir, path))
        ws = wb.add_worksheet()
        for i, h in enumerate(["Inizio", "Fine", "Ore", "Provv.", "Note"]):
            ws.write(0, i, h)
        
        conn = sqlite3.connect(self.db_path)
        data = conn.execute("SELECT DATA_E_ORA_INIZIO, DATA_E_ORA_FINE, TUTTO_IL_GIORNO, PROVVISORIO, NOTE FROM FERIE WHERE UTENTE=?", (uid,)).fetchall()
        for r, row in enumerate(data, 1):
            h = 8.0 if row[2] == 1 else (datetime.fromisoformat(row[1]) - datetime.fromisoformat(row[0])).total_seconds()/3600
            ws.write(r, 0, row[0])
            ws.write(r, 1, row[1])
            ws.write(r, 2, h)
            ws.write(r, 3, "Sì" if row[3] == 1 else "No")
            ws.write(r, 4, row[4])
        wb.close()
        conn.close()
        QMessageBox.information(self, "OK", f"Esportato in {path}")

if __name__ == "__main__":       
    # carico le preferenze di MGrep
    o_preferenze = preferenze()
    o_preferenze.carica()    
    # apro app per test
    app = QApplication(sys.argv)
    window = AppFerie(o_preferenze.work_dir)
    window.show()
    sys.exit(app.exec())
