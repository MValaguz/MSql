import cx_Oracle
import getpass
import os

#Reimposto la pathname! Attenzione al ; alla fine della pathname!!!!
os.environ["PATH"] = r"C:\oracle\Middleware\Oracle_Home\bin;" + os.environ["PATH"]
#Imposto il percorso per collegarmi alla libreria Oracle a 64bit (che supporta anche UTF-8)
try:
    cx_Oracle.init_oracle_client(lib_dir=r'C:\oracle\Middleware\Oracle_Home\bin')    
except Exception as err:
    if str(err) == 'Oracle Client library has already been initialized':
        pass
    else:
        print('------------------------------------------------------------------------------')
        print('ERRORE DURANTE INIZIALIZZAZIONE LIBRERIA CX_ORACLE IN LIBRERIA ORACLE_MY_LIB!!')
        print(err)
        print('------------------------------------------------------------------------------')



#v_password = getpass.getpass('SMILE')
#v_lista_bind = {':AZIENDA':'',':DIPENDENTE':''}
v_con = cx_Oracle.connect(user='SMILE', password='SMILE', dsn='BACKUP_815')        
v_cur = v_con.cursor()
v_cur.callproc("dbms_output.enable", [1000000])        
#v_cur.execute("SELECT DIPEN_DE FROM CP_DIPEN WHERE AZIEN_CO=:AZIENDA AND DIPEN_CO=:DIPENDENTE",v_lista_bind)
#v1_azienda = v_cur.var(str)
#v1_dipendente = v_cur.var(str)
v_lista_var =[]
v_lista_var.append(v_cur.var(str))
v_lista_var.append(v_cur.var(str))
print(v_lista_var)
#v_dipendente = v_cur.var(str)
v_cur.execute("""
BEGIN  
  :V_AZIENDA := 'TEC'; 
  :V_DIPENDENTE := '00035';
END;
""", v_lista_var)

v_cur.execute("""
DECLARE
  v_output VARCHAR2(100);
BEGIN
  select DIPEN_DE
  into   v_output
  from   CP_DIPEN
  where  AZIEN_CO=:V_AZIENDA AND
         DIPEN_CO=:V_DIPENDENTE;
  Dbms_Output.Put_Line(v_output);
  Dbms_Output.Put_Line('output interno a pl-sql ' || :V_DIPENDENTE);
  Dbms_Output.Put_Line('output interno a pl-sql ' || :V_AZIENDA);  
END;""", v_lista_var)

#v_azienda=v1_azienda,v_dipendente=v1_dipendente)

print(v_lista_var[0].getvalue())
print(v_lista_var[1].getvalue())

# preparo le var per leggere l'output dello script
v_chunk = 100
v_dbms_ret = ''            
v_m_line = v_cur.arrayvar(str, v_chunk)
v_m_num_lines = v_cur.var(int)
v_m_num_lines.setvalue(0, v_chunk)

# leggo output dello script
while True:
    v_cur.callproc("dbms_output.get_lines", (v_m_line, v_m_num_lines))    
    v_num_lines = int(v_m_num_lines.getvalue())
    v_lines = v_m_line.getvalue()[:v_num_lines]
    for line in v_lines:
        v_dbms_ret += str(line) + '\n'
    if v_num_lines < v_chunk:
        break

# porto l'output a video (tipico è quello di script che contengono dbms_output)
if v_dbms_ret != '':
   print('output ' + v_dbms_ret)    
                
"""
# altra istruzione                
v_cur.execute("SELECT DIPEN_DE FROM CP_DIPEN WHERE AZIEN_CO=:AZIENDA AND DIPEN_CO=:DIPENDENTE",v_lista_bind)

v_dati=v_cur.fetchall()

for v_rec in v_dati:
    print(v_rec)
"""

v_cur.close()
v_con.close()