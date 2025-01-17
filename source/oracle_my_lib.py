#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 09/02/2023
#  Descrizione...: Scopo di questa classe è wrappare la libreria di connessione a Oracle, così da rendere disponibile ai programmi MGrep un oggetto comune

#Importo la libreria cx_Oracle versione dalla 8.3 in su
import cx_Oracle
import os

def inizializzo_client():
   """
      Inizializzo il client di Oracle 
   """
   #Reimposto la pathname! Attenzione al ; alla fine della pathname!!!!
   os.environ["PATH"] = r"C:\oracle\Middleware\Oracle_Home\bin;" + os.environ["PATH"]
   #Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
   try:
      #cx_Oracle.init_oracle_client(lib_dir=r'C:\oracle\Middleware\Oracle_Home\bin')
      cx_Oracle.init_oracle_client()
   except Exception as err:
      if str(err) == 'Oracle Client library has already been initialized':
         pass
      else:
         print('------------------------------------------------------------------------------')
         print('ERRORE DURANTE INIZIALIZZAZIONE LIBRERIA cx_Oracle IN LIBRERIA ORACLE_MY_LIB!  ')
         print(err)
         print('------------------------------------------------------------------------------')

class cursore():
   """
      Restituisce un cursore aperto su DB Oracle. Al momento dell'instanziazione passare utente, password e dsn.       
   """
   def __init__(self, 
                 p_utente,
                 p_password,
                 p_dsn):
      
      self.utente = p_utente
      self.password = p_password
      self.dsn = p_dsn

      #Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
      inizializzo_client()
      
      #Mi collego a Oracle e apro un cursore
      try:
         self.db = cx_Oracle.connect(user=self.utente, password=self.password, dsn=self.dsn)        
         self.cursor = self.db.cursor()             
         self.connessione_ok = True
      except:                  
         self.connessione_ok = False

   def execute(self, p_sql_instruction):
      """
         Esegue p_sql_instruction nel cursore presente nell'oggetto         
      """
      self.cursor.execute(p_sql_instruction)

# ----------------------------------------
# TEST APPLICAZIONE
# ----------------------------------------
if __name__ == "__main__":    
   v_prova = cursore(p_utente='SMILE', p_password='SMILE', p_dsn='BACKUP_815')
   if v_prova.connessione_ok:
      print('Connessione effettuata con successo!')
   else:
      print('Qualcosa è andato storto nella connessione a Oracle')
