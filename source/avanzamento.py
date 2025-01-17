#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11 con libreria pyqt6
#  Data..........: 11/04/2023
#  Descrizione...: Classe per la gestione di una progressbar (è ad esempio utilizzato in oracle_my_sql.py)

# Librerie di sistema
import sys
import time
# Amplifico la pathname dell'applicazione in modo veda il contenuto della directory qtdesigner dove sono contenuti i layout
sys.path.append('qtdesigner')
# Librerie grafiche
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

# Classe per la visualizzazione della progressbar
class avanzamento_infinito_class(QProgressDialog):
    """
        Visualizzo una progress bar senza fine...
    """       
    def __init__(self, p_icon_name):                 
        # creazione della wait window
        QProgressDialog.__init__(self, None)        
        self.setMinimumDuration(0)        
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle("Wait...")    
        self.setMinimumWidth(400)            
        # icona del titolo
        self.icon = QIcon()
        self.icon.addPixmap(QPixmap("icons:"+p_icon_name), QIcon.Mode.Normal, QIcon.State.Off)        
        self.setWindowIcon(self.icon)        
        # creo un campo label che viene impostato con 100 caratteri in modo venga data una dimensione di base standard
        self.progress_label = QLabel()            
        self.progress_label.setText('...')
        # collego la label già presente nell'oggetto progress bar con la mia label 
        self.setLabel(self.progress_label)                                                        
        # creo una progress personalizzata
        self.progress_bar = QProgressBar()
        # imposto valore minimo e massimo a 0 in modo venga considerata una progress a tempo indefinito
        # Attenzione! dentro nel ciclo deve essere usata la funzione setvalue altrimenti non visualizza e non avanza nulla!
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)        
        self.setBar(self.progress_bar)                
        # imposto il flag che si valorizza se richiesta interruzione da parte dell'utente
        self.richiesta_cancellazione = False
    
    def avanza(self, p_testo, p_valore):
        self.progress_label.setText(p_testo)        
        self.setValue(p_valore)
        # intercetto richiesta di cancellazione
        if self.wasCanceled():
            self.richiesta_cancellazione = True

    def chiudi(self):
        self.close()

# Classe usata solo per lanciare il test della progress infinita
class Ui_Test(object):
    def setupUi(self, TestWindow):
        TestWindow.setObjectName("TestWindow")
        TestWindow.resize(800, 600)

        # creo una barra di avanzamento infinita
        v_progress = avanzamento_infinito_class("sql_editor.gif")

        # carico tutte le pagine fino ad arrivare in fondo (siccome vengono caricati 100 record per pagina....)
        v_counter = 0 
        while v_counter < 100:
            v_counter += 1            
            # visualizzo barra di avanzamento e se richiesto interrompo
            v_progress.avanza('Loading next ' + str(v_counter*100) + ' records',v_counter)
            time.sleep(0.1)        
            if v_progress.richiesta_cancellazione:                        
               break
        
        # chiudo la barra di avanzamento
        v_progress.chiudi()

# ------------------------------------------------
# TEST APPLICAZIONE BARRA DI AVANZAMENTO INFINITO
# ------------------------------------------------
if __name__ == "__main__":    
    app = QApplication(sys.argv)
    TestWindow = QMainWindow()
    ui = Ui_Test()
    ui.setupUi(TestWindow)
    TestWindow.show()
    sys.exit(app.exec_())        