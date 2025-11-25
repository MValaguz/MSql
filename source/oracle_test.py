"""
  Programma di test oracle
"""
#Librerie di database
import oracledb
from oracle_my_lib import inizializzo_client

inizializzo_client()
v_oracle_db = oracledb.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')        
v_oracle_cursor = v_oracle_db.cursor()    
                                     
v_oracle_cursor.execute("""
SELECT * FROM TA_AZIEN
""")                                

for rec in v_oracle_cursor:
  print(rec[0])

v_oracle_db.close()