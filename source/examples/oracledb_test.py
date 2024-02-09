import oracledb
import getpass
import os


#Reimposto la pathname! Attenzione al ; alla fine della pathname!!!!
os.environ["PATH"] = r"C:\oracle\Middleware\Oracle_Home\bin;" + os.environ["PATH"]
#Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
try:
    #cx_Oracle.init_oracle_client(lib_dir=r'C:\oracle\Middleware\Oracle_Home\bin')
    oracledb.init_oracle_client()
except Exception as err:
    if str(err) == 'Oracle Client library has already been initialized':
        pass
    else:
        print('------------------------------------------------------------------------------')
        print('ERRORE DURANTE INIZIALIZZAZIONE LIBRERIA CX_ORACLE IN LIBRERIA ORACLE_MY_LIB!!')
        print(err)
        print('------------------------------------------------------------------------------')

#v_password = getpass.getpass('SMILE')

v_con = oracledb.connect(user='SMILE', password='SMILE', host='10.0.4.11', port=1521, sid='SMIG')
v_cur = v_con.cursor()
v_cur.execute('SELECT AZIEN_CO FROM TA_AZIEN')
v_dati=v_cur.fetchall()

for v_rec in v_dati:
    print(v_rec)

v_cur.close()
v_con.close()