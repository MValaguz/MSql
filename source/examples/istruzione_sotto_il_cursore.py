def extract_sql_under_cursor(p_text, p_offset):
    """
       All'interno di p_text e usando come posizione p_offset, ricerca "istruzione" sql....più corretto dire che ricerca un blocco di istruzioni
       Utilizza come delimitatori di istruzione i caratteri (/),(;) e (riga di separazione con solo CRLF/LF)
       Restituisce posizione di inizio e fine 
    """    
    # calcolo lunghezza totale del testo 
    v_len = len(p_text)
    
    # rilevo interlinea se Windows o Linux
    if '\r\n' in p_text:
        v_inter = 2
    else:
        v_inter = 1

    ###
    # 1° STEP --> ricerco il simbolo di limitazione dalla posizione del cursore verso la fine del testo
    ###        
    
    # ricerco se c'è un limitatore verso la fine del testo, identificato dal simbolo (/)
    v_end = p_offset    
    v_ok = False
    for i in range(p_offset,v_len):
        if p_text[i] == '/':                        
            if (i+1 < len(p_text)) and (i-1 >= 0) and (p_text[i+1] != '*') and (p_text[i-1] != '*'):
                v_ok = True
                break
        v_end += 1

    # ricerco se c'è un limitatore verso la fine del testo, identificato dal simbolo (;)
    if not v_ok:        
        v_end = p_offset    
        v_ok = False
        for i in range(p_offset,v_len):
            if p_text[i] == ';':                                            
                v_ok = True
                break
            v_end += 1
    
    # ricerco se c'è un limitatore verso la fine del testo, identificato dal simbolo (riga di separazione con solo CRLF/LF)
    if not v_ok:
        v_end = p_offset
        v_crlf = 0
        for i in range(p_offset,v_len):            
            if p_text[i] in ('\n','\r'):
                v_crlf += 1
            elif p_text[i] in ('\t',' '):
                pass
            else:
                v_crlf = 0
            if v_crlf > v_inter:            
                v_end = v_end - v_crlf + 1           
                break            
            v_end += 1

    # pulisco la fine della stringa dai simboli speciali
    if v_end > 0:                
        for i in range(v_end,0,-1):            
            if (i < len(p_text)) and (i-1 >= 0):                
                if p_text[i] in ('/',';','\n','\r'):                               
                    v_end -= 1
                else:         
                    v_end += 1       
                    break
    
    # se posizione fine supera la lunghezza --> lo normalizzo
    if v_end > v_len:        
        v_end = v_len

    ###
    # 2° STEP --> ricerco il simbolo di limitazione dalla posizione del cursore verso l'inizio del testo
    ###        

    # ricerco se c'è un limitatore verso l'inizio del testo, identificato dal simbolo (/)
    v_start = p_offset
    v_ok = False
    for i in range(p_offset,0,-1):                
        if p_offset < v_len and p_text[i] == '/':
            v_start += 1
            if (i+1 < len(p_text)) and (i-1 >= 0) and (p_text[i+1] != '*') and (p_text[i-1] != '*'):            
                v_start += 1
                v_ok = True
                break
        v_start -= 1

    # ricerco se c'è un limitatore verso l'inizio del testo, identificato dal simbolo (;)    
    if not v_ok:
        v_start = p_offset
        v_ok = False
        for i in range(p_offset,0,-1):        
            if p_offset < v_len and p_text[i] == ';':                
                v_start += 1
                v_ok = True
                break
            v_start -= 1

    # ricerco se c'è un limitatore verso l'inizio del testo, identificato dal simbolo (riga di separazione con solo CRLF/LF)
    if not v_ok:
        v_start = p_offset
        v_crlf = 0
        for i in range(p_offset,0,-1):        
            if p_offset < v_len:
                if p_text[i] in ('\n','\r'):
                    v_crlf += 1
                elif p_text[i] in ('\t',' '):
                    pass
                else:
                    v_crlf = 0
                if v_crlf > v_inter:
                    v_start = v_start + v_crlf            
                    break
                v_start -= 1        

    # pulisco inizio della stringa dai simboli speciali
    if v_start > 0:        
        for i in range(v_start,v_len):
            if p_text[i] in ('/',';','\n','\r','\t',' '):                
                v_start += 1
            else:                
                break            

    return v_start, v_end

def slot_ctrl_invio(self):
        """
           L'utente ha premuto CTRL+Invio: viene ricercata l'istruzione dove il cursore di testo è attualmente posizionato
           e viene inviata all'esecutore. Se l'utente ha selezionato del testo, viene eseguito il testo selezionato; questo
           per mantenere un comportamento coerente con l'esecuzione tramite F5.
        """
        # se indicato dalla preferenza, prima di partire ad eseguire, pulisco l'output
        if o_global_preferences.auto_clear_output:
            self.slot_clear('OUT')
        
        # controllo se utente ha selezionato del testo specifico che vuole eseguire
        v_istruzione = self.e_sql.selectedText()                
        if v_istruzione is not None and v_istruzione != '':            
            # eseguo l'istruzione selezionata                          
            self.esegui_istruzione(v_istruzione, False)        
        # ... altrimenti....
        else:
            # prendo posizione cursore in riga e colonna
            v_pos_line, v_pos_column = self.e_sql.getCursorPosition()
            # imposto var generali
            self.v_offset_numero_di_riga = 0
            # prendo posizione attuale del cursore (relativa!)
            v_pos_relativa_cursore = self.e_sql.SendScintilla(self.e_sql.SCI_GETCURRENTPOS)
            # richiamo funzione interna per estrazione dell'istruzione sql (istruzione che termina con ; o /)             
            v_start_pos, v_end_pos = extract_sql_under_cursor(self.e_sql.text(), v_pos_relativa_cursore)      
            #print('-'*100)
            #print(f"{v_pos_relativa_cursore} {v_start_pos}:{v_end_pos}")                                              
            #print(self.e_sql.text()[v_start_pos:v_end_pos])
            if v_start_pos > -1  and v_end_pos > -1 and v_start_pos < v_end_pos:                                
                # eseguo l'istruzione                            
                self.esegui_istruzione(self.e_sql.text()[v_start_pos:v_end_pos], False)                        
                # Imposta la selezione tra due offset assoluti
                self.e_sql.SendScintilla(QsciScintilla.SCI_SETSEL, v_start_pos, v_end_pos)
            else:
                # altrimenti errore
                message_error(QCoreApplication.translate('MSql_win2','No statement found as SELECT, INSERT, UPDATE, DELETE!'))
                return 'ko'   
            
######################################################################################################################
# TEST DELLA FUNZIONE CHE PARTENDO DA CODICE PL-SQL, RESTITUISCE UN OGGETTO CHE CONTIENE TUTTE LE DEFINIZIONI TROVATE
######################################################################################################################
if __name__ == "__main__":      
    v_testo = """select * 
from   ta_azien
where  azien_co='SMI';
/
SELECT * FROM CP_DIPEN WHERE AZIEN_CO='SMI' AND DIPEN_CO='00035';

SELECT * 
FROM OC_ORDET 
WHERE AZIEN_CO='SMI' 
AND ESERC_CO='2025';

SELECT *
FROM   MW_PRELI_TMP
WHERE  TIPOR_DO = R_VA_MW_PREOP_TMP.TIPOR_DO
   AND ESERC_CO = R_VA_MW_PREOP_TMP.ESERC_CO
   AND DEPOS_CO = R_VA_MW_PREOP_TMP.DEPOS_CO
   AND TORDI_CO = R_VA_MW_PREOP_TMP.TORDI_CO
   AND ORDIN_NU = R_VA_MW_PREOP_TMP.ORDIN_NU
   AND ARTIC_CO IS NOT NULL
   /* LA QTA MANCANTE VIENE NETTIFICATA CON LA QTA DI LISTA */
   AND QTAMA_NU - QTALI_NU = 0
   AND (SELECT DIVPR_CO
     FROM   MA_PRAGE
     WHERE  MA_PRAGE.AZIEN_CO = MW_PRELI_TMP.AZIEN_CO
        AND MA_PRAGE.ARTIC_CO = MW_PRELI_TMP.ARTIC_CO) IS NOT NULL
   AND RIFOP_CO IS NOT NULL
ORDER BY DATAP_DA, PRIOR_NU;
"""
    print('-'*100)
    v_riga_inizio, v_riga_fine = extract_sql_under_cursor(v_testo, 10)    
    print(f"{v_riga_inizio},{v_riga_fine}")
    print(v_testo[v_riga_inizio:v_riga_fine],)            