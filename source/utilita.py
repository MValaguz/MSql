# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11 con libreria pyqt6
 Data..........: 09/08/2018 
"""

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
#Amplifico la pathname per ricercare le icone
QDir.addSearchPath('icons', 'qtdesigner/icons/')

def message_error(p_message):
    """
       Visualizza messaggio di errore usando interfaccia qt
    """
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(p_message)    
    msg.setWindowTitle("Error")
    icon = QIcon()
    icon.addPixmap(QPixmap("icons:sql_editor.gif"), QIcon.Mode.Normal, QIcon.State.Off)    
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
    icon.addPixmap(QPixmap("icons:sql_editor.gif"), QIcon.Mode.Normal, QIcon.State.Off)    
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
    icon.addPixmap(QPixmap("icons:sql_editor.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
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
    icon.addPixmap(QPixmap("icons:sql_editor.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
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
    icon.addPixmap(QPixmap("icons:sql_editor.gif"), QIcon.Mode.Normal, QIcon.State.Off)        
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