def extract_sql_under_cursor(p_testo: str, p_cur_pos: int):
    """
    Estrae l'istruzione SQL sotto p_cursor_pos in p_testo,
    considerando come separatori i caratteri ';' e '/' ma trattando '/'
    come terminatore solo se, tolti spazi/tab, è l’unico carattere
    sulla riga. Ignora i separatori dentro commenti block (/*...*/) o
    single-line (--...).

    Ritorna (statement, start_idx, end_idx).
    """
    # se non passata posizione --> esco
    if p_cur_pos == 0:
        return '',0,0
    
    # se posizione è oltre la dimensione del testo --> imposto cursore con fine testo
    v_len = len(p_testo)
    if p_cur_pos > v_len-1:
        p_cur_pos = v_len-1
    
    # identifico il carattere di fine riga
    if '\r\n' in p_testo:
        v_eol = '\r\n'
    else:
        v_eol = '\n'

    # parametri di inizio e fine istruzione
    v_start, v_end = 0,0

    ###
    # RICERCO PUNTO DI PARTENZA ISTRUZIONE
    ###

    # 1° caso: ricerco se prima della posizione del cursore è presente una riga singola dove c'è solo il carattere /
    v_found = False
    v_i = p_cur_pos
    v_riga = ''
    while v_i >= 0:
        if p_testo[v_i] in ('\n','\r'):            
            if v_riga.rstrip().lstrip() == '/':
                v_start = v_i
                print('Trovato slash! '+str(v_i)+' '+p_testo[v_i:p_cur_pos]+'|')
                v_found = True
                break
            v_riga = ''
        else:
            v_riga = p_testo[v_i] + v_riga
        v_i -= 1

    # 2° caso: non ho trovato il carattere /, rifaccio il procedimento con il carattere ;
    if not v_found:        
        v_i = p_cur_pos
        v_riga = ''
        while v_i >= 0:
            if p_testo[v_i] in ('\n','\r'):            
                if v_riga.rstrip().lstrip() == ';':
                    v_start = v_i
                    print('Trovato punto-virgola! '+str(v_i)+' '+p_testo[v_i:p_cur_pos]+'|')
                    v_found = True
                    break
                v_riga = ''
            else:
                v_riga = p_testo[v_i] + v_riga
            v_i -= 1

    # 3° caso: non ho trovato nè slash nè punto e virgola, considero inizio l'inizio del testo 
    if not v_found:
        v_start = 0

    ###
    # RICERCO PUNTO DI FINE ISTRUZIONE
    ###

    # 1° caso: ricerco se dopo posizione del cursore è presente una riga singola dove c'è solo il carattere /
    v_found = False
    v_i = p_cur_pos
    v_riga = ''
    while v_i <= v_len:        
        if p_testo[v_i] in ('\n','\r'):            
            if v_riga.rstrip().lstrip() == '/':
                v_end = v_i
                print('Trovato slash! '+str(v_i)+' '+p_testo[v_i:p_cur_pos]+'|')
                v_found = True
                break
            v_riga = ''
        else:
            v_riga = p_testo[v_i] + v_riga
        v_i += 1

    # 2° caso: non ho trovato il carattere /, rifaccio il procedimento con il carattere ;
    if not v_found:        
        v_i = p_cur_pos
        v_riga = ''
        while v_i <= v_len:
            if p_testo[v_i] in ('\n','\r'):            
                if v_riga.rstrip().lstrip() == ';':
                    v_end = v_i
                    print('Trovato punto-virgola! '+str(v_i)+' '+p_testo[v_i:p_cur_pos]+'|')
                    v_found = True
                    break
                v_riga = ''
            else:
                v_riga = p_testo[v_i] + v_riga
            v_i += 1

    # 3° caso: non ho trovato nè slash nè punto e virgola, considero fine la fine del testo 
    if not v_found:
        v_end = v_len-1

    return p_testo[v_start:v_end],v_start,v_end

########
v_testo = """
    select * 
    from   ta_azien
    where  azien_co='SMI'
    /
    SELECT * 
    FROM CP_DIPEN 
    WHERE AZIEN_CO='SMI' AND 
          DIPEN_CO='00035'
    /
    SELECT * 
    FROM CP_DIPEN 
    WHERE AZIEN_CO='TEC' AND 
          DIPEN_CO='00035'
    union
    SELECT * 
    FROM CP_DIPEN 
    WHERE AZIEN_CO='SMI' AND 
          DIPEN_CO='00035'
    /			
    declare
      v_ok varchar2(100);
    begin
      v_ok := 'ciao';
    	dbms_output.put_line(v_ok);
    end;			
    /
    SELECT *
    FROM   MW_PRELI_TMP
    WHERE  TIPOR_DO = 'O'
       AND ESERC_CO = '2025'
       AND DEPOS_CO = 'B1'
       AND TORDI_CO = 'ORPI'
       AND ORDIN_NU = 10
       AND ARTIC_CO IS NOT NULL
       /* LA QTA MANCANTE VIENE NETTIFICATA CON LA QTA DI LISTA */
       AND QTAMA_NU - QTALI_NU = 0
       AND (SELECT DIVPR_CO
         FROM   MA_PRAGE
         WHERE  MA_PRAGE.AZIEN_CO = MW_PRELI_TMP.AZIEN_CO
            AND MA_PRAGE.ARTIC_CO = MW_PRELI_TMP.ARTIC_CO) IS NOT NULL
       AND RIFOP_CO IS NOT NULL
    ORDER BY DATAP_DA, PRIOR_NU"""

v_istruzione, v_riga_inizio, v_riga_fine = extract_sql_under_cursor(v_testo, 200)    
print('-'*100)
print(f"{v_istruzione},{v_riga_inizio},{v_riga_fine}")