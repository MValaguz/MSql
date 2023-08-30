# MSql
A simple Oracle SQL editor

-- Installation note
-- This package list contains web component not needed for MSql
Package                   Version
------------------------- ---------
altgraph                  0.17.3
click                     8.1.3
colorama                  0.4.6
cx-Oracle                 8.3.0
Flask                     2.2.2
Flask-WTF                 1.1.1
itsdangerous              2.1.2
Jinja2                    3.1.2
MarkupSafe                2.1.2
pefile                    2023.2.7
pip                       23.0
pyfiglet                  0.8.post1
pyinstaller               5.8.0
pyinstaller-hooks-contrib 2023.0
PyQt5                     5.15.9
PyQt5-Qt5                 5.15.2
PyQt5-sip                 12.11.1
PyQtChart                 5.15.6
PyQtChart-Qt5             5.15.2
pywin32-ctypes            0.2.0
QScintilla                2.14.1
setuptools                65.5.0
Werkzeug                  2.2.2
WTForm                    1.0
WTForms                   3.0.1
xlrd                      2.0.1
XlsxWriter                3.0.8

-- Notes: for packages installation via firewall blocker
-- esempio installazione passando da siti certificati 
-- in questo caso si tratta dell'installazione delle librerie dei grafici 

pip install pyqtchart --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org

-- altro esempio di installazione dei driver OCI (diversi da quelli cx_oracle) per oracle. Tramite questi driver è possibile usare gli oggetti avanzati delle librerie QT
-- perché l'installazione arrivi a buon fine è necessario aver installato il compilatore C++. Questo perché vengono scaricati in automatico dei programmi C++ e poi compilati
-- quindi ho dovuto installare https://visualstudio.microsoft.com/it/visual-cpp-build-tools/ il tool e installare la parte relativa a C++ (si parla di 9gbyte di file installati)
-- Oraclebd dovrebbe sostituire la libreria cx_Oracle....ma dopo averla installata mi ha dato un sacco di problemi nell'utilizzo....
-- quindi al momento non la sto usando!
pip install oracledb --upgrade --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org
