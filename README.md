# MSql
A simple Oracle SQL editor

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
