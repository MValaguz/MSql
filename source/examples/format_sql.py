# esempio della libreria format-sql che riformatta istruzioni sql
from sql_formatter.core import format_sql

v_sql = 'select * from ta_azien'

v_sql_new = format_sql(v_sql)

print(v_sql_new)