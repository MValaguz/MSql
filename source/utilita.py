# -*- coding: utf-8 -*-

"""
 Creato da.....: Marco Valaguzza
 Piattaforma...: Python3.11
 Data..........: 09/08/2018 
"""

from PyQt5 import QtGui,QtWidgets
import os

def extract_word_from_cursor_pos(p_string, p_pos):
    """
       Data una stringa completa p_stringa e una posizione di cursore su di essa, 
       estrae la parola che sta "sotto" la posizione del cursore
       Es. p_string = CIAO A TUTTI QUANTI VOI 
           p_pos = 10
           restituisce TUTTI
    """
    # se posizione cursore è oltre la stringa...esco    
    if p_pos >= len(p_string):
        return ''

    # inizio a comporre la parola partendo dalla posizione del cursore (se non trovo nulla esco)
    v_word=p_string[p_pos]    
    if v_word is None or v_word in ('',' ','=',':','.','(',')'):
        return ''

    # mi sposto a sinistra rispetto al cursore e compongo la parola    
    v_index = p_pos
    while True and v_index > 0:
        v_index -= 1
        if v_index < len(p_string):
            if p_string[v_index] not in (' ','=',':','.','(',')'):
                v_word = p_string[v_index] + v_word
            else:
                break
        else:
            break

    # mi sposto a destra rispetto al cursore e compongo la parola
    v_index = p_pos
    while True:
        v_index += 1
        if v_index < len(p_string):
            if p_string[v_index] not in (' ','=',':','\n','\r','.','(',')'):
                v_word += p_string[v_index]
            else:
                break
        else:
            break

    return v_word

def message_error(p_message):
    """
       Visualizza messaggio di errore usando interfaccia qt
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(p_message)    
    msg.setWindowTitle("Error")
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icons/icons/sql_editor.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)    
    msg.setWindowIcon(icon)
    msg.exec_()
    
def message_info(p_message):
    """
       Visualizza messaggio info
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(p_message)    
    msg.setWindowTitle("Info")
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icons/icons/sql_editor.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)    
    msg.setWindowIcon(icon)
    msg.exec_()    
    
def message_question_yes_no(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e restituisce Yes se pulsante OK è stato premuto
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Question)
    msg.setText(p_message)
    msg.setWindowTitle("Question")    
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icons/icons/sql_editor.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QtWidgets.QMessageBox.Yes:
        return 'Yes'
    else:
        return 'No'
    
def message_question_yes_no_cancel(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e Cancel e restituisce Yes se pulsante OK è stato premuto,
       altrimenti No se No, o Cancel se richiesto annullamento operazione!
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Question)
    msg.setText(p_message)
    msg.setWindowTitle("Question")    
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icons/icons/sql_editor.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QtWidgets.QMessageBox.Yes:
        return 'Yes'
    elif valore_di_ritorno == QtWidgets.QMessageBox.No:
        return 'No'
    else:
        return 'Cancel'

def message_warning_yes_no(p_message):
    """
       Visualizza messaggio con pulsanti Yes, No e restituisce Yes se pulsante OK è stato premuto
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Warning)
    msg.setText(p_message)
    msg.setWindowTitle("Warning")    
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/icons/icons/sql_editor.gif"), QtGui.QIcon.Normal, QtGui.QIcon.Off)        
    msg.setWindowIcon(icon)
    msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    
    valore_di_ritorno = msg.exec()
    if valore_di_ritorno == QtWidgets.QMessageBox.Yes:
        return 'Yes'
    else:
        return 'No'
