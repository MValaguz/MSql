import re

def extract_sql_under_cursor(p_testo, p_cursor_pos):
    """
        Ricerca blocco sql o pl-sql che si trova sotto la posizione del cursore
        Questo codice è la copia della funzione slot_esegui presente nel file principale di MSql_editor!
    """
    v_trovato = False

    def fine_istruzione(p_stringa):
        """
            Funzione interna per controllare se la riga ha un termine di istruzione '/' oppure ;
        """
        # se istruzione è / --> allora termine istruzione
        if p_stringa == '/':
            return True
        # se istruzione finisce con ; e il punto e virgola però non è tra apici 
        v_reg = "^(?!.*(['\"].*;\1)).*;$"
        if re.match(v_reg, p_stringa):
            return True        

        return False
    
    # calcolo la lunghezza del ritorno a capo in base al fatto che eol sia Windows o Linux
    if '\r\n' in p_testo:
        v_len_eol = 2
    else:
        v_len_eol = 1                                   
                        
    # prendo il testo e inizio ad eseguire le istruzioni
    # divido il testo ricevuto in input riga per riga (ritorno a capo è il divisore)
    v_righe_testo = p_testo.split(chr(10))
    # leggo riga per riga
    v_commento_multi = False
    v_istruzione = False
    v_istruzione_str = ''
    v_plsql = False
    v_plsql_idx = 0
    #v_ok = ""
    v_offset_numero_di_riga = 0
    
    v_pos_progress = 0 
    v_riga_inizio = 0
    v_riga_fine = 0        
    for v_riga_raw in v_righe_testo:
        v_pos_progress += len(v_riga_raw) + v_len_eol
        v_riga_fine += 1
        if v_pos_progress >= p_cursor_pos:
            v_trovato = True
            print('HO SUPERATO LA POSIZIONE!!!!')
        # dalla riga elimino gli spazi a sinistra e a destra
        v_riga = v_riga_raw.lstrip()
        v_riga = v_riga.rstrip()               
        # continuazione plsql (da notare come lo script verrà composto con v_riga_raw)
        if v_plsql:            
            print('Continuo con script plsql ' + v_riga)
            if v_riga != '':
                # se trovo "aperture" aumento indice
                if v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE') != -1:
                    v_plsql_idx += 1
                # se trovo chiusure diminuisco indice
                elif v_riga.split()[0].upper() == 'END;' != -1:
                    v_plsql_idx -= 1
            # aggiungo riga
            if v_riga != '/':
                v_plsql_str += chr(10) + v_riga_raw
            else:
                v_offset_numero_di_riga += 1
            # la chiusura trovata era l'ultima (oppure trovato chiusura dello script tramite slash) --> quindi eseguo lo script
            if v_plsql_idx <= 0 or v_riga == '/':                           
                #v_ok = esegui_codice(v_plsql_str)                    
                if v_trovato:
                    return v_plsql_str, 'PL-SQL', v_riga_inizio, v_riga_fine
                v_riga_inizio = v_riga_fine
                #if v_ok == 'ko':                        
                #    return 'ko'
                v_plsql = False
                v_plsql_str = ''
                v_plsql_idx = 0
        # riga vuota (ma esterna a plsql)
        elif v_riga == '':            
            v_offset_numero_di_riga += 1
        # se siamo all'interno di un commento multiplo, controllo se abbiamo raggiunto la fine (se è un'istruzione non faccio pulizia dei commenti)
        elif v_commento_multi and v_riga.find('*/') == -1 and v_istruzione_str == '':
            v_offset_numero_di_riga += 1
        elif v_commento_multi and v_riga.find('*/') != -1 and v_istruzione_str == '':        
            v_offset_numero_di_riga += 1
            v_commento_multi = False
        # commenti monoriga (se è un'istruzione non faccio pulizia dei commenti)
        elif (v_riga[0:2] == '--' or v_riga[0:6] == 'PROMPT' or (v_riga[0:2] == '/*' and v_riga.find('*/') != -1)) and v_istruzione_str == '':                
            v_offset_numero_di_riga += 1
        # commento multi multiriga (se è un'istruzione non faccio pulizia dei commenti)
        elif v_riga[0:2] == '/*' and v_istruzione_str == '':
            v_offset_numero_di_riga += 1
            v_commento_multi = True                        
        # continuazione di una select dove la riga inizia con una costante
        elif v_istruzione and v_riga[0] == "'":
            v_istruzione_str += v_riga
        # fine di una select, insert, update, delete.... con punto e virgola o /
        elif v_istruzione and fine_istruzione(v_riga):
            v_istruzione = False
            v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]
            #v_ok = esegui_codice(v_istruzione_str)
            if v_trovato:
                return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine
            v_riga_inizio = v_riga_fine
            #if v_ok == 'ko':
            #    return 'ko'
            v_istruzione_str = ''
        # continuazione di una select, insert, update, delete....
        elif v_istruzione and not fine_istruzione(v_riga):
                v_istruzione_str += chr(10) + v_riga
        # inizio select, insert, update, delete.... monoriga
        elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','REVOKE','ALTER','DROP','COMMENT','TRUNCATE') and v_riga[-1] == ';':
            v_istruzione_str = v_riga[0:len(v_riga)-1]
            #v_ok = esegui_codice(v_istruzione_str)
            if v_trovato:
                return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine
            v_riga_inizio = v_riga_fine
            #if v_ok == 'ko':
            #    return 'ko'
            v_istruzione_str = ''
        # inizio select, insert, update, delete.... multiriga            
        elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','REVOKE','ALTER','DROP','COMMENT','TRUNCATE'):
            v_istruzione = True
            v_istruzione_str = v_riga
        # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)             
        elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
            print('Inizio plsql ')
            v_plsql = True
            v_plsql_idx += 1
            v_plsql_str = v_riga_raw
        # dichiarazione di una bind variabile (secondo lo standard definito da sql developer es. VARIABLE v_nome_var VARCHAR2(100))
        # sono accettati solo i tipi VARCHAR2, NUMBER e DATE
        elif v_riga.split()[0].upper() in ('VARIABLE','VAR'):                                
            v_split = v_riga.split()
        else:            
            return '', '', 0,0                

    # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
    if v_plsql and v_plsql_str != '':
        #v_ok = esegui_codice(v_plsql_str)            
        if v_trovato:
            return v_plsql_str, 'PL-SQL', v_riga_inizio , v_riga_fine
    
    # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
    if v_istruzione and v_istruzione_str != '':
        #v_ok = esegui_codice(v_istruzione_str)  
        if v_trovato:
            return v_istruzione_str, 'SQL', v_riga_inizio, v_riga_fine

    return '', '', 0,0                

######################################################################################################################
# TEST DELLA FUNZIONE CHE PARTENDO DA CODICE PL-SQL, RESTITUISCE UN OGGETTO CHE CONTIENE TUTTE LE DEFINIZIONI TROVATE
######################################################################################################################
if __name__ == "__main__":      
    v_testo = """select * 
from   ta_azien
where  azien_co='SMI';

SELECT * FROM CP_DIPEN WHERE AZIEN_CO='SMI' AND DIPEN_CO='00035';

SELECT * 
FROM OC_ORDET 
WHERE AZIEN_CO='SMI' 
AND ESERC_CO='2025';

SELECT *
FROM   MW_PRELI_TMP
WHERE  TIPOR_DO = 'p'
   AND ESERC_CO = '2025'
   AND DEPOS_CO = 'b1'
   AND TORDI_CO = 'orma'
   AND ORDIN_NU = 10
   AND ARTIC_CO IS NOT NULL
   /* LA QTA MANCANTE VIENE NETTIFICATA CON LA QTA DI LISTA */
   AND QTAMA_NU - QTALI_NU = 0
   AND (SELECT DIVPR_CO
     FROM   MA_PRAGE
     WHERE  MA_PRAGE.AZIEN_CO = MW_PRELI_TMP.AZIEN_CO
        AND MA_PRAGE.ARTIC_CO = MW_PRELI_TMP.ARTIC_CO) IS NOT NULL
   AND RIFOP_CO IS NOT NULL
ORDER BY DATAP_DA, PRIOR_NU;

declare
  v_ok varchar2(100);
begin
  v_ok := 'ciao';
end;
"""
    print('-'*100)
    v_istruzione, v_tipo, v_riga_inizio, v_riga_fine = extract_sql_under_cursor(v_testo, 720)    
    print(f"{v_istruzione} {v_tipo},{v_riga_inizio},{v_riga_fine}")
    #print(v_testo[v_riga_inizio:v_riga_fine],)        