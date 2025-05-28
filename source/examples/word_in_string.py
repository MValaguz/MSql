v_testo = """
SELECT *
FROM  ma_prage
WHERE  azien_co='SMI' 
  AND ARTIC_CO='MA400520'

	
	/

SELECT * FROM 
CP_DETOR
WHERE AZIEN_CO='TEC'
AND DIPEN_CO='00035'


/

select * from ta_azien
"""

def estrai_istruzione(p_testo, p_cursor):
    """
       Dato un testo p_testo, cerca l'istruzione che si trova sotto la posizione del cursore
       Tale istruzione deve avere i seguenti delimitatori:
         - punto e virgola
         - / ma inserito solitario in una riga
    """
    p_testo = p_testo.split('\n')    
    v_istruzione = ''
    v_num_caratteri = 0
    v_riga_inizio = 0
    v_riga_fine = 0
    v_riga = 0
    v_found = False
    for linea in p_testo:
        v_riga += 1
        v_num_caratteri += len(linea)
        v_linea_netto = linea.lstrip().rstrip()
        v_istruzione += ' ' + linea
        print(f"{v_riga} {linea}")
        
        if len(v_linea_netto) > 0 and (v_linea_netto == '/' or v_linea_netto[-1] == ';') :                        
            v_riga_fine = v_riga            
            v_riga_inizio = v_riga_fine
            v_riga_fine = 0        
            v_found = True
                    
        # fine del testo, prendo ultima istruzione
        if v_riga == len(p_testo) :            
            print('found'+str(v_num_caratteri))
            v_riga_fine = v_riga            
            v_riga_inizio = v_riga_fine
            v_riga_fine = 0        
            v_found = True
                    
        if v_found:
            if p_cursor <= v_num_caratteri:
                return v_istruzione, v_riga_inizio, v_riga_fine
            v_istruzione = ''
            v_found = False
    
    return '',0,0

v_istruzione, v_inizio, v_fine = estrai_istruzione(v_testo, 190)        

print(f"{v_istruzione}, {v_inizio}, {v_fine}")