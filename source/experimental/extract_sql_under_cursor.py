# def extract_sql_under_cursor(p_testo, p_cursor_pos):
#     """
#         Ricerca blocco sql o pl-sql che si trova sotto la posizione del cursore
#         Questo codice è la copia della funzione slot_esegui presente nel file principale di MSql_editor!
#         Questa versione restituisce numero riga inizio e fine
#     """
#     v_trovato = False

#     def fine_istruzione(p_stringa):
#         """
#             Funzione interna per controllare se la riga ha un termine di istruzione '/' oppure ;
#         """
#         # se istruzione è / --> allora termine istruzione
#         if p_stringa == '/':
#             return True
#         # se istruzione finisce con ; e il punto e virgola però non è tra apici 
#         v_reg = "^(?!.*(['\"].*;\1)).*;$"
#         if re.match(v_reg, p_stringa):
#             return True        

#         return False
        
#     # divido il testo ricevuto in input riga per riga (ritorno a capo è il divisore)    
#     # prestare sempre attenzione ai ritorni a capo!
#     if '\r\n' in p_testo:
#         v_len_eol = 2
#         v_righe_testo = p_testo.split('\r\n')
#     else:
#         v_righe_testo = p_testo.split('\n')    
#         v_len_eol = 1                                   
    
#     #print(f"Posizione del cursore {p_cursor_pos} con eol {v_len_eol}")
                    
#     # prendo il testo e inizio ad eseguire le istruzioni        
#     v_commento_multi = False
#     v_istruzione = False
#     v_istruzione_str = ''
#     v_plsql = False
#     v_plsql_idx = 0    
#     v_offset_numero_di_riga = 0
#     v_pos_progress = 0 
#     v_riga_inizio = 0
#     v_riga_fine = 0        
#     for v_riga_raw in v_righe_testo:
#         #print(f"Riga: {v_riga_raw} {len(v_riga_raw)}")
#         v_pos_progress += len(v_riga_raw) + v_len_eol
#         v_riga_fine += 1
#         if v_pos_progress >= p_cursor_pos:
#             v_trovato = True
#             #print('HO SUPERATO LA POSIZIONE!!!!' + v_riga_raw)
#             #print(len(v_riga_raw))
#         # dalla riga elimino gli spazi a sinistra e a destra
#         v_riga = v_riga_raw.lstrip()
#         v_riga = v_riga.rstrip()               
#         # continuazione plsql (da notare come lo script verrà composto con v_riga_raw)
#         if v_plsql:            
#             print('Continuo con script plsql ' + v_riga)
#             if v_riga != '':
#                 # se trovo "aperture" aumento indice
#                 if v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE') != -1:
#                     v_plsql_idx += 1
#                 # se trovo chiusure diminuisco indice
#                 elif v_riga.split()[0].upper() == 'END;' != -1:
#                     v_plsql_idx -= 1
#             # aggiungo riga
#             if v_riga != '/':
#                 v_plsql_str += chr(10) + v_riga_raw
#             else:
#                 v_offset_numero_di_riga += 1
#             # la chiusura trovata era l'ultima (oppure trovato chiusura dello script tramite slash) --> quindi eseguo lo script
#             if v_plsql_idx <= 0 or v_riga == '/':                                           
#                 if v_trovato:
#                     return v_plsql_str, 'PL-SQL', v_riga_inizio, v_riga_fine
#                 v_riga_inizio = v_riga_fine
#                 v_plsql = False
#                 v_plsql_str = ''
#                 v_plsql_idx = 0
#         # riga vuota (ma esterna a plsql)
#         elif v_riga == '':            
#             v_offset_numero_di_riga += 1
#         # se siamo all'interno di un commento multiplo, controllo se abbiamo raggiunto la fine (se è un'istruzione non faccio pulizia dei commenti)
#         elif v_commento_multi and v_riga.find('*/') == -1 and v_istruzione_str == '':
#             v_offset_numero_di_riga += 1
#         elif v_commento_multi and v_riga.find('*/') != -1 and v_istruzione_str == '':        
#             v_offset_numero_di_riga += 1
#             v_commento_multi = False
#         # commenti monoriga (se è un'istruzione non faccio pulizia dei commenti)
#         elif (v_riga[0:2] == '--' or v_riga[0:6] == 'PROMPT' or (v_riga[0:2] == '/*' and v_riga.find('*/') != -1)) and v_istruzione_str == '':                
#             v_offset_numero_di_riga += 1
#         # commento multi multiriga (se è un'istruzione non faccio pulizia dei commenti)
#         elif v_riga[0:2] == '/*' and v_istruzione_str == '':
#             v_offset_numero_di_riga += 1
#             v_commento_multi = True                        
#         # continuazione di una select dove la riga inizia con una costante
#         elif v_istruzione and v_riga[0] == "'":
#             v_istruzione_str += v_riga
#         # fine di una select, insert, update, delete.... con punto e virgola o /
#         elif v_istruzione and fine_istruzione(v_riga):
#             v_istruzione = False
#             v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]            
#             if v_trovato:
#                 return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine
#             v_riga_inizio = v_riga_fine
#             v_istruzione_str = ''
#         # continuazione di una select, insert, update, delete....
#         elif v_istruzione and not fine_istruzione(v_riga):
#                 v_istruzione_str += chr(10) + v_riga
#         # inizio select, insert, update, delete.... monoriga
#         elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','REVOKE','ALTER','DROP','COMMENT','TRUNCATE') and v_riga[-1] == ';':
#             v_istruzione_str = v_riga[0:len(v_riga)-1]            
#             if v_trovato:
#                 return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine
#             v_riga_inizio = v_riga_fine
#             v_istruzione_str = ''
#         # inizio select, insert, update, delete.... multiriga            
#         elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','REVOKE','ALTER','DROP','COMMENT','TRUNCATE'):
#             v_istruzione = True
#             v_istruzione_str = v_riga
#         # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)             
#         elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
#             print('Inizio plsql ')
#             v_plsql = True
#             v_plsql_idx += 1
#             v_plsql_str = v_riga_raw
#         # dichiarazione di una bind variabile (secondo lo standard definito da sql developer es. VARIABLE v_nome_var VARCHAR2(100))
#         # sono accettati solo i tipi VARCHAR2, NUMBER e DATE
#         elif v_riga.split()[0].upper() in ('VARIABLE','VAR'):                                
#             v_split = v_riga.split()
#         else:            
#             return '', '', 0,0                

#     # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
#     if v_plsql and v_plsql_str != '':        
#         if v_trovato:
#             return v_plsql_str, 'PL-SQL', v_riga_inizio , v_riga_fine
    
#     # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
#     if v_istruzione and v_istruzione_str != '':        
#         if v_trovato:
#             return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine

#     return '', '', 0,0                

# def extract_sql_under_cursor(p_testo, p_cursor_pos):
#     """
#         Ricerca blocco sql o pl-sql che si trova sotto la posizione del cursore
#         Questo codice è la copia della funzione slot_esegui presente nel file principale di MSql_editor!
#         Restituisce istruzione, tipo_istruzione, posizione di inizio e posizione di fine istruzione
#     """         
#     def fine_istruzione(p_stringa):
#         if p_stringa == '/':
#             return True
#         # se istruzione finisce con ; e il punto e virgola però non è tra apici 
#         v_reg = "^(?!.*(['\"].*;\1)).*;$"
#         if re.match(v_reg, p_stringa):
#             return True        

#         return False
    
#     # se il cursore è a fine testo o il carattere a sinistra è ; allora viene spostato indietro di una posizione
#     # per eseguire istruzione che sta alla sinistra
#     if p_cursor_pos > len(p_testo) or p_testo[p_cursor_pos-2] == ';':        
#         p_cursor_pos -= 1
    
#     # scegli il separatore di riga e dividi
#     if '\r\n' in p_testo:
#         eol = '\r\n'
#     else:
#         eol = '\n'
#     righe = p_testo.split(eol)

#     # variabili di stato
#     absolute_pos = 0            # offset assoluto all’inizio di ogni riga
#     found_cursor = False
#     in_sql = False
#     in_plsql = False
#     sql_str = ''
#     plsql_str = ''
#     plsql_depth = 0

#     snippet_start = None
#     snippet_end = None

#     for raw in righe:
#         start_of_line = absolute_pos
#         line = raw.strip()
#         # aggiorno cursore
#         absolute_pos += len(raw) + len(eol)
#         # ho superato la posizione del cursore?
#         if start_of_line + len(raw) >= p_cursor_pos and not found_cursor:
#             found_cursor = True

#         # PL/SQL: inizio blocco
#         first = line.split()[0].upper() if line else ''
#         if not in_sql and first in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
#             in_plsql = True
#             plsql_depth = 1
#             plsql_str = raw
#             snippet_start = start_of_line
#             continue

#         # dentro un blocco PL/SQL
#         if in_plsql:
#             # conto aperture/chiusure
#             tok = first
#             if tok in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
#                 plsql_depth += 1
#             elif tok.startswith('END'):
#                 plsql_depth -= 1

#             plsql_str += eol + raw

#             # fine blocco: profondità 0 o slash standalone
#             if plsql_depth <= 0 or line == '/':
#                 snippet_end = start_of_line + len(raw)
#                 if found_cursor:
#                     return plsql_str, 'PL-SQL', snippet_start, snippet_end
#                 # reset per cercare il prossimo
#                 in_plsql = False
#                 plsql_str = ''
#             continue

#         # salto commenti vuoti
#         if not line or line.startswith('--') or line.upper().startswith('PROMPT'):
#             continue

#         # gestione SQL
#         # inizio istruzione multiriga o monoriga
#         if not in_sql and first in ('SELECT','INSERT','UPDATE','DELETE',
#                                     'GRANT','REVOKE','ALTER','DROP',
#                                     'COMMENT','TRUNCATE'):
#             in_sql = True
#             sql_str = raw
#             snippet_start = start_of_line
#             # se è monoriga già finisce con ;
#             if fine_istruzione(line):
#                 snippet_end = start_of_line + len(raw)
#                 if found_cursor:
#                     # rimuovo eventuale ultimo ; per coerenza
#                     return sql_str.rstrip(';'), 'SQL', snippet_start, snippet_end
#                 in_sql = False
#             continue

#         # continuiamo SQL multiriga
#         if in_sql:
#             sql_str += eol + raw
#             if fine_istruzione(line):
#                 snippet_end = start_of_line + len(raw)
#                 if found_cursor:
#                     return sql_str.rstrip(';/'), 'SQL', snippet_start, snippet_end
#                 in_sql = False
#             continue

#     # se il file finisce dentro un blocco aperto
#     if in_plsql and found_cursor:
#         return plsql_str, 'PL-SQL', snippet_start, absolute_pos
#     if in_sql and found_cursor:
#         return sql_str, 'SQL', snippet_start, absolute_pos

#     # nulla trovato
#     return '', '', 0, 0