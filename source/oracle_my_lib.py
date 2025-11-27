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

def inizializzo_client():
   """
      Inizializzo il client di Oracle 
   """
   # In base al sistema operativo imposto il percorso della libreria Oracle Instant Client
   if os.name == "posix":
      # Percorso al tuo Oracle Instant Client su Linux      
      return 'ok'      
   else:
      # Reimposto la pathname! Attenzione al ; alla fine della pathname!!!!      
      os.environ["PATH"] = r"C:\oracle\Middleware\Oracle_Home\bin;" + os.environ["PATH"]
   
   #Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
   try:
      #oracledb.init_oracle_client(lib_dir=r'C:\oracle\Middleware\Oracle_Home\bin')
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
   inizializzo_client()
   # TEST LINUX   
   if os.name == "posix":
      v_oracle_db = oracledb.connect(user='SMILE_PY', password='SMILE_PY', dsn='10.0.4.11:1521/SMIG')        # corrisponde a BACKUP_815
   # TEST WINDOWS
   else:
      v_oracle_db = oracledb.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')        
   
   v_oracle_cursor = v_oracle_db.cursor()    

   v_oracle_cursor.execute("""SELECT * FROM TA_AZIEN""")                                
   for rec in v_oracle_cursor:
      print(rec[0])      