#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11 con libreria pyqt6
#  Data..........: 09/08/2018 

#Libreria per criptare i messaggi
import os
import base64
#Librerie grafiche 
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qtdesigner', 'icons'))

def return_global_work_dir():
    """
       Restituisce la directory di lavoro globale a seconda del sistema operativo
    """
    # Attenzione! Questa dir è possibile aprirla dalla gestione delle preferenze e in quel programma è riportata ancora la stessa dir              
    if os.name == "posix":
        return os.path.expanduser('~//.local//share//MSql//')
    else:
        return os.path.expanduser('~\\AppData\\Local\\MSql\\')
    
def message_error(p_message):
    """
       Visualizza messaggio di errore usando interfaccia qt
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(p_message)    
    msg.setWindowTitle("Error")
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)    
    msg.setWindowIcon(icon)
    msg.exec()
    
def message_info(p_message):
    """
       Visualizza messaggio info
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText(p_message)    
    msg.setWindowTitle("Info")
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)    
    msg.setWindowIcon(icon)
    msg.exec()    
    
def message_question_yes_no(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e restituisce Yes se pulsante OK è stato premuto
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setText(p_message)
    msg.setWindowTitle("Question")    
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QMessageBox.StandardButton.Yes:
        return 'Yes'
    else:
        return 'No'
    
def message_question_yes_no_cancel(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e Cancel e restituisce Yes se pulsante OK è stato premuto,
       altrimenti No se No, o Cancel se richiesto annullamento operazione!
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setText(p_message)
    msg.setWindowTitle("Question")    
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QMessageBox.StandardButton.Yes:
        return 'Yes'
    elif valore_di_ritorno == QMessageBox.StandardButton.No:
        return 'No'
    else:
        return 'Cancel'

def message_warning_yes_no(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e restituisce Yes se pulsante OK è stato premuto
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setText(p_message)
    msg.setWindowTitle("Warning")    
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QMessageBox.StandardButton.Yes:
        return 'Yes'
    else:
        return 'No'

def Freccia_Mouse(p_active):
    """
       Attiva o disattiva la freccia del muose indicando la clessidra di elaborazione se p_active = True
    """
    if p_active:
        # sostituisce la freccia del mouse con icona "clessidra"
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))        
    else:
        # ripristino icona freccia del mouse
        QApplication.restoreOverrideCursor()    

def centra_window_figlia(p_window_madre, p_window_figlia): 
    """
        Data la p_window_madre, centra p_window_figlia al centro di p_window_madre
    """
    parent_geometry = p_window_madre.frameGeometry() 
    parent_center = parent_geometry.center() 
    self_geometry = p_window_figlia.frameGeometry() 
    self_geometry.moveCenter(parent_center) 
    p_window_figlia.move(self_geometry.topLeft())

def cripta_messaggio(messaggio):
    """
       Cripta una stringa con la chiave MSql. Il valore restituito è di tipo bytes, lo stesso che deve essere passato
       all'invio dei dati su rete
    """
    key = 'MSql'
    enc = []
    for i in range(len(messaggio)):
        key_c = key[i % len(key)]
        enc_c = (ord(messaggio[i]) + ord(key_c)) % 256
        enc.append(enc_c)
    return base64.urlsafe_b64encode(bytes(enc))

def decripta_messaggio(messaggio):
    """
       decripta una stringa con la chiave MSql. Il valore restituito è di tipo stringa, lo stesso che deve essere 
       passato ai campi di visualizzazione 
    """
    key = 'MSql'
    dec = []
    enc = base64.urlsafe_b64decode(messaggio)
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + enc[i] - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)        

def nome_file_backup(p_nome_file, p_work_dir):
    """
       Calcola il nome file di backup
       Il nome riporta la pathname della dir di backup il PID (process ID) di MSql attualmente in esecuzione e il nome del file di origine
       Siccome non sono ammessi nel nome del file i caratteri : slash backslash, vengono sostituiti usando il punto
    """
    from pathlib import Path

    p_nome_file = p_nome_file.replace('/', '..')
    p_nome_file = p_nome_file.replace('\\', '..')
    p_nome_file = p_nome_file.replace(':','...')
    p_nome_file = p_work_dir + 'backup\\' + 'PID-'+ str(os.getpid()) + 'PID-' + p_nome_file
    p_nome_file = Path(p_nome_file).resolve()

    return f"\\\\?\\{p_nome_file}"

def titolo_window(p_titolo_file):
    """
       Partendo da p_titolo_file restituisce solo la parte di nome file da mettere come titolo della window
    """                       
    v_solo_nome_file = os.path.split(p_titolo_file)[1]
    v_solo_nome_file_senza_suffisso = os.path.splitext(v_solo_nome_file)[0]

    return v_solo_nome_file_senza_suffisso

def prossimo_export_file(v_directory, v_nome_base, v_estensione='csv'):
    """
       Genera un percorso file unico. Se il file esiste, aggiunge un progressivo (es. _1, _2).
    """
    # Rimuove il punto dall'estensione se presente, per gestirlo uniformemente
    v_estensione = v_estensione.lstrip('.')
    
    # Costruisce il percorso iniziale: /cartella/Export_data.csv
    v_percorso_completo = os.path.join(v_directory, f"{v_nome_base}.{v_estensione}")
    
    v_contatore = 1
    # Ciclo finché non trova un nome di file non ancora esistente
    while os.path.exists(v_percorso_completo):
        v_nuovo_nome = f"{v_nome_base}_{v_contatore}.{v_estensione}"
        v_percorso_completo = os.path.join(v_directory, v_nuovo_nome)
        v_contatore += 1
        
    return v_percorso_completo

def salvataggio_editor(o_global_preferences, v_global_work_dir, p_save_as, p_nome, p_testo, p_codifica_utf8, p_timestamp_ultima_modifica=None):
    """
        Salvataggio di p_testo dentro il file p_nome        
        Se p_save_as è True oppure il titolo dell'editor inizia con "!" --> viene richiesto di salvarlo come nuovo file
        Viene restituita la nuova data di ultima modifica del file
    """
    # salvo in var temporanea il nome ricevuto in input (lo userò per eliminare il vecchio backup)
    p_nome_originario = p_nome

    # se il primo carattere del titolo inizia con un punto esclamativo, significa che il file è stato creato partendo dall'object navigator
    # e quindi l'operazione di salva deve chiedere il nome del file e la posizione dove salvare
    if p_nome[0:1] == '!':
        p_save_as = True
        p_nome = p_nome.lstrip('!')

    # se indicato il save as, oppure il file è nuovo e non è mai stato salvato --> richiedo un nuovo nome di file    
    if p_save_as or (not p_save_as and p_nome[0:8]=='Untitled'):
        # la dir di default è quella richiesta dall'utente o la Documenti        
        if o_global_preferences.save_dir == '':
            v_default_save_dir = QDir.homePath() + "\\Documents\\"
        else:
            v_default_save_dir = o_global_preferences.save_dir

        # propongo un nuovo nome di file dato dalla dir di default + il titolo ricevuto in input
        v_file_save_as = v_default_save_dir + '\\' + p_nome        
     
        p_nome = QFileDialog.getSaveFileName(None, "Save a SQL file",v_file_save_as,"MSql files (*.msql);;SQL files (*.sql *.pls *.plb *.trg);;All files (*.*)") [0]                                  
        if not p_nome:
            message_error(QCoreApplication.translate('Save','Error saving'))
            return 'ko', None, None
        # se nel nome del file non è presente un suffisso --> imposto .msql            
        if p_nome.find('.') == -1:
            p_nome += '.msql'
        # reimposto la dir di default in modo che in questa sessione del programma rimanga quella che l'utente ha scelto per salvare il file
        o_global_preferences.save_dir = os.path.split( p_nome )[0]

    # procedo con il salvataggio
    try:
        # controllo se il file è stato modificato da un altro programma
        try:
            v_timestamp_ultima_modifica = os.path.getmtime(p_nome)
        except:
            v_timestamp_ultima_modifica = None
        if p_timestamp_ultima_modifica is not None and v_timestamp_ultima_modifica is not None and p_timestamp_ultima_modifica != v_timestamp_ultima_modifica:
            if message_warning_yes_no(QCoreApplication.translate('Save','The file has been modified by another program since it was opened. Do you want to overwrite it?')) == 'Yes':
                pass
            else:
                return 'ko', None
        # scrittura usando utf-8 (il newline come parametro è molto importante per la gestione corretta degli end of line)                                                            
        if p_codifica_utf8:            
            v_file = open(p_nome,'w',encoding='utf-8', newline='')
        # scrittura usando ansi (il newline come parametro è molto importante per la gestione corretta degli end of line)                                        
        else:            
            v_file = open(p_nome,'w', newline='')
        v_file.write(p_testo)
        v_file.close()            
        # procedo con il cancellare eventuale file di backup precedente (si ripartirà con un nuovo salvataggio che conterrà il nuovo nome di file)                
        v_nome_file_backup = nome_file_backup(p_nome_originario, v_global_work_dir)                
        if os.path.exists(v_nome_file_backup):
            os.remove(v_nome_file_backup)		
            print('Remove old backup --> ' + v_nome_file_backup)
        # ricavo la data di ultima modifica del file e la restituisco (serve per il controllo di modifiche da parte di altri programmi)
        try:
            v_timestamp_ultima_modifica = os.path.getmtime(p_nome)
        except:
            v_timestamp_ultima_modifica = None
        # esco con tutto ok
        return 'ok', p_nome, v_timestamp_ultima_modifica
    except Exception as err:
        # esco con errore
        message_error(QCoreApplication.translate('Save','Error to write the file:') + ' ' + str(err))
        return 'ko', None