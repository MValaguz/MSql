#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 09/02/2023
#  Descrizione...: Funzione per inizializzare correttamente la libreria oracledb di Oracle
#  Note..........: 
#                  SISTEMA OPERATIVO WINDOWS
#                  Nel caso di Windows si usano le librerie Oracle Client 64bit che a seconda dell'installazione
#                  va indicata la pathname corretta.
#                  
#                  SISTEMA OPERATIVO LINUX
#                  Nel caso di Linux invece si è usata la modalità "Thin" che non necessita di librerie esterne ma
#                  necessita che lo user abbia determintate caratteristiche.
#                  A QUESTO PUNTO, TRAMITE SYS E' STATO CREATO UN UTENTE CHE PERMETTA ALLA LIBRERIA ORACLE DI COLLEGARSI E VEDERE GLI OGGETTI SU CUI LAVORARE 
#      
#                  CREATE USER SMILE_PY IDENTIFIED BY SMILE_PY;
#                  GRANT CONNECT, RESOURCE TO SMILE_PY;
#                  GRANT SMILE_ROLE TO SMILE_PY;
#                  ALTER USER SMILE_PY DEFAULT ROLE SMILE_ROLE;
#                  GRANT CREATE SESSION TO SMILE_PY;

# Importo la libreria oracledb versione dalla 8.3 in su
import oracledb
import os
# Classe per la gestione delle preferenze
from preferences import preferences_class
# Libreria delle utilità
from utilita import return_global_work_dir

def inizializzo_client():
   """
      Inizializzo il client di Oracle 
      connection_mode: 0=Thin 1=Thick
      oracleclient_path: percorso della libreria Oracle Client (se connection_mode=1) generalmente impostato con "C:/oracle/Middleware/Oracle_Home/bin"
   """
   # Recupero la cartella di lavoro globale
   v_global_work_dir = return_global_work_dir()
   # Carico le preferenze globali (lo faccio qui dentro per evitare il passaggio dei parametri che sarebbe scomodo)
   o_global_preferences = preferences_class(v_global_work_dir + 'MSql.ini', v_global_work_dir + 'MSql_connections.ini')

   # Se connection mode è Thin=diretto esco senza fare nulla
   if o_global_preferences.connection_mode == 0:
      return 'ok'
   
   # Connection mode Thick=con libreria Oracle Client --> quindi devo caricare la libreria prendendola da qualche parte e quindi   
   # reimposto la pathname! Attenzione al ; alla fine della pathname!!!!      
   os.environ["PATH"] = o_global_preferences.oracleclient_path + ";" + os.environ["PATH"]
   
   # Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
   try:      
      oracledb.init_oracle_client()
   except Exception as err:
      if str(err) == 'Oracle Client library has already been initialized':
         pass
      else:
         print('------------------------------------------------------------------------------')
         print('ERRORE DURANTE INIZIALIZZAZIONE LIBRERIA oracledb IN LIBRERIA ORACLE_MY_LIB!  ')
         print(err)
         print('------------------------------------------------------------------------------')

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":       
   # TEST LINUX   
   if os.name == "posix":      
      v_oracle_db = oracledb.connect(user='SMILE_PY', password='SMILE_PY', dsn='10.0.4.11:1521/SMIG')        # corrisponde a BACKUP_815
   # TEST WINDOWS (viene inizializzato il client con libreria Oracle Client)
   else:
      inizializzo_client()
      v_oracle_db = oracledb.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')        
   
   v_oracle_cursor = v_oracle_db.cursor()    

   v_oracle_cursor.execute("""SELECT * FROM TA_AZIEN""")                                
   for rec in v_oracle_cursor:
      print(rec[0])      