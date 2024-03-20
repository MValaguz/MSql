# Programma utilizzato per debuggare la funzione slot_esegui che riceve in input del testo e lo normalizza per essere eseguito dal motore sql

def esegui_script(p_testo, p_boolean):
    """
    """
    print('RICHIAMATO FUNZIONE ESEGUI_SCRIPT')    

def esegui_istruzione(p_testo):
    """
    """
    print('RICHIAMATO FUNZIONE ESEGUI_ISTRUZIONE')
    print(p_testo)

def slot_esegui(p_testo):
        """
           Prende tutto il testo selezionato ed inizia ad eseguirlo step by step
           Se si attiva v_debug, variabile interna, verrà eseguito l'output di tutte le righe processate
        """
        # se metto a true v_debug usciranno tutti i messaggi di diagnostica della ricerca delle istruzioni
        v_debug = False
        def debug_interno(p_message):
            if v_debug:
                print(p_message)        

        # imposto la var di select corrente che serve in altre funzioni
        v_select_corrente = ''

        # prendo tutto il testo o solo quello evidenziato dall'utente
        v_testo = p_testo            
        v_offset_numero_di_riga = 0

        if v_testo == '':
            # emetto errore sulla barra di stato 
            print('No instruction!')                                 
            return 'ko'
        
        # prendo il testo e inizio ad eseguire le istruzioni
        # divido il testo ricevuto in input riga per riga (ritorno a capo è il divisore)
        v_righe_testo = v_testo.split(chr(10))
        # leggo riga per riga
        v_commento_multi = False
        v_istruzione = False
        v_plsql = False
        v_plsql_idx = 0
        v_ok = ""
        for v_riga_raw in v_righe_testo:
            # dalla riga elimino gli spazi a sinistra e a destra
            v_riga = v_riga_raw.lstrip()
            v_riga = v_riga.rstrip()            
            # continuazione plsql (da notare come lo script verrà composto con v_riga_raw)
            if v_plsql:            
                debug_interno('Continuo con script plsql ' + v_riga)
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
                    v_ok = esegui_script(v_plsql_str, False)
                    if v_ok == 'ko':                        
                        return 'ko'
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
            # continuazione di una select, insert, update, delete....
            elif v_istruzione and v_riga.find(';') == -1:
                 v_istruzione_str += chr(10) + v_riga
            # fine di una select, insert, update, delete.... con punto e virgola
            elif v_istruzione and v_riga[-1] == ';':
                v_istruzione = False
                v_istruzione_str += chr(10) + v_riga[0:len(v_riga)-1]
                v_ok = esegui_istruzione(v_istruzione_str)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... monoriga
            elif not v_istruzione and v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','ALTER','DROP') and v_riga[-1] == ';':
                v_istruzione_str = v_riga[0:len(v_riga)-1]
                v_ok = esegui_istruzione(v_istruzione_str)
                if v_ok == 'ko':
                    return 'ko'
                v_istruzione_str = ''
            # inizio select, insert, update, delete.... multiriga
            elif v_riga.split()[0].upper() in ('SELECT','INSERT','UPDATE','DELETE','GRANT','ALTER','DROP'):
                v_istruzione = True
                v_istruzione_str = v_riga
            # riga di codice pl-sql (da notare come lo script verrà composto con v_riga_raw)       
            elif v_riga.split()[0].upper() in ('DECLARE','BEGIN','CREATE','REPLACE','FUNCTION','PROCEDURE'):
                debug_interno('Inizio plsql ')
                v_plsql = True
                v_plsql_idx += 1
                v_plsql_str = v_riga_raw
            else:
                print('Unknown command type: ' + v_riga_raw + '.....')
                return 'ko'                

        # se a fine scansione mi ritrovo che v_plsql è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo
        if v_plsql and v_plsql_str != '':
            v_ok = esegui_script(v_plsql_str, False)            
        
        # se a fine scansione mi ritrovo che v_istruzione è ancora attiva, vuol dire che ho ancora un'istruzione in canna, e quindi la eseguo          
        if v_istruzione and v_istruzione_str != '':
            v_ok = esegui_istruzione(v_istruzione_str)  

        return v_ok

slot_esegui("""
SELECT DESCR,VALORE
FROM (  /*-------------
           RIGHE LISTA
		---------------*/  
        /* TIPO C=COLLO ORDINE */
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'C'		
		UNION
        SELECT 'Recupero OdP' DESCR, 4 VALORE
        FROM  DUAL
        WHERE 'P' = 'C'
		/* TIPO B=RIGA LISTA */
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'B'		
		UNION
        SELECT 'Recupero OdP' DESCR, 4 VALORE
        FROM  DUAL
        WHERE 'P' = 'B'
		/* TIPO L=DIRETTO IN POSTAZIONE */
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'L'		
		UNION
        SELECT 'Recupero OdP' DESCR, 4 VALORE
        FROM  DUAL
        WHERE 'P' = 'L'
		/* TIPO A=ALTRE LISTE BORDO LINEA */
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'A'		
		UNION
        SELECT 'Recupero OdP' DESCR, 4 VALORE
        FROM  DUAL
        WHERE 'P' = 'A'
        /*-------------
           RIGHE N
		---------------*/  		
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'P'        
        UNION        
        SELECT 'Mancante' DESCR, 2 VALORE
        FROM  DUAL
        WHERE 'P' = 'P'         
        UNION
        SELECT 'Eccesso' DESCR, 3 VALORE
        FROM  DUAL
        WHERE 'P' = 'P'		
        UNION
        SELECT 'Recupero OdP' DESCR, 4 VALORE
        FROM  DUAL
        WHERE 'P' = 'P'
		/*-------------
           DOCUMENTALE
		---------------*/  		
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'D'        
        UNION        
        SELECT 'Documentale' DESCR, 5 VALORE
        FROM  DUAL
        WHERE 'P' = 'D'         
		/*-------------
           DOCUMENTALE COFI
		---------------*/  		
		UNION
        SELECT 'Articolo NC' DESCR, 1 VALORE
        FROM  DUAL
        WHERE 'P' = 'F'        
        UNION        
        SELECT 'Documentale' DESCR, 5 VALORE
        FROM  DUAL
        WHERE 'P' = 'F'         
		/*-------------
           PER TUTTI GLI ALTRI CASI VIENE CONCESSO IL VALORE NULL
		---------------*/  		
		UNION
		SELECT NULL DESCR, NULL VALORE
        FROM  DUAL        
)
""")        