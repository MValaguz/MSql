# MSql
MSql is a text editor designed to connect to Oracle databases and execute SQL/PL-SQL code.

It is written in Python (version 3.13.7).

The "compile" folder contains the scripts for creating the Windows executable using pyinstaller. 
However, it is currently executable and adapted for Linux, but without an installation script.

English and Italian are currently supported; 
comments and program objects are written in a mixed English-Italian language; 
so I apologize for this ambiguity!!!

The main libraries used by this program are:
 - oracledb = connection to Oracle
 - pyqt6 = graphical user interface framework, where the layout creation was done using the
           Qt Designer graphical tool
 - qscintilla = the core of the text editor
 - qtlinguist = translation management, already native to the PyQt6 libraries but handled
                graphically through the Qt Linguist tool

Below is a list of the libraries that must be installed for the program to work.
								
Package                   Version
------------------------- ---------
altgraph                  0.17.5
art                       6.5
cffi                      2.0.0
cryptography              46.0.3
keyboard                  0.13.5
oracledb                  3.4.1
packaging                 25.0
pefile                    2024.8.26
pip                       25.3
platformdirs              4.5.1
psutil                    7.1.3
pycparser                 2.23
pyinstaller               6.17.0
pyinstaller-hooks-contrib 2025.10
PyQt6                     6.10.1
PyQt6-Charts              6.10.0
PyQt6-Charts-Qt6          6.10.1
PyQt6-QScintilla          2.14.1
PyQt6-Qt6                 6.10.1
PyQt6_sip                 13.10.3
pyscard                   2.3.1
pywin32-ctypes            0.2.3
setuptools                80.9.0
sql-formatter             0.6.2
typing_extensions         4.15.0
xlrd                      2.0.2
xlsxwriter                3.2.9