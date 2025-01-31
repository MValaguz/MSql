import re

def extract_statement_with_positions_space(sql_string, cursor_position):
    # Pattern per ricercare le istruzioni SQL
    v_pattern = re.compile(r'(SELECT|INSERT|UPDATE|DELETE).*?(?=SELECT|INSERT|UPDATE|DELETE|$)', re.DOTALL | re.IGNORECASE)
    
    v_matches = list(v_pattern.finditer(sql_string))
    # Scorro la lista dei risultati
    for v_match in v_matches:        
        # Se trovo il risultato all'interno della posizione del cursore...
        if v_match.start() <= cursor_position <= v_match.end():
            # Imposto posizione di inizio e fine            
            v_start_pos = v_match.start()
            v_end_pos = v_match.end()            
            # Ricerco su quale riga è la posizione di inizio
            v_riga_inizio = 1
            v_posizione = -1
            for c in sql_string:              
              v_posizione += 1
              if c == chr(10):
                v_riga_inizio += 1
              if v_posizione == v_start_pos:
                  break
            # Ricerco su quale riga è la posizine di fine
            v_riga_fine = 0
            v_posizione = -1
            for c in sql_string:              
              v_posizione += 1
              if c == chr(10):
                v_riga_fine += 1
              if v_posizione == v_end_pos:
                  break            
            return v_start_pos, v_end_pos, v_riga_inizio, v_riga_inizio
    
    return None, None, None, None

# Esempio di utilizzo
sql_string = """SELECT * FROM TA_AZIEN
SELECT * FROM MS_UTN WHERE LOGIN_CO='FDAMIANI' 

SELECT * 
FROM   OC_ORTES,
       OC_ORDET
WHERE  OC_ORTES.AZIEN_CO='SMI'
  AND  OC_ORTES.ESERC_CO='2024'
  AND  OC_ORTES.DEPOS_CO='D1'
  AND  OC_ORTES.TORDI_CO='ORPI'  
  AND  OC_ORTES.AZIRF_CO='SMI'
  AND  OC_ORTES.AZIEN_CO = OC_ORDET.AZIEN_CO
  AND  OC_ORTES.ESERC_CO = OC_ORDET.ESERC_CO
  AND  OC_ORTES.DEPOS_CO = OC_ORDET.DEPOS_CO
  AND  OC_ORTES.TORDI_CO = OC_ORDET.TORDI_CO
  AND  OC_ORTES.ORDIN_NU = OC_ORDET.ORDIN_NU
  AND  OC_ORTES.AZIRF_CO = OC_ORDET.AZIRF_CO

SELECT *
FROM MS_UTN
WHERE LOGIN_CO='MVALAGUZ'

SELECT * FROM KARDEX.UTDAT WHERE UTPROG LIKE '2024%16%'
DELETE FROM KARDEX.UTDAT WHERE UTPROG LIKE '2024%16%'

SELECT * 
FROM   OC_ORTES,
       OC_ORDET
WHERE  OC_ORTES.AZIEN_CO='SMI'
  AND  OC_ORTES.ESERC_CO='2024'
  AND  OC_ORTES.DEPOS_CO='D1'
  AND  OC_ORTES.TORDI_CO='ORPI'  
  AND  OC_ORTES.AZIRF_CO='SMI'
  AND  OC_ORTES.AZIEN_CO = OC_ORDET.AZIEN_CO
  AND  OC_ORTES.ESERC_CO = OC_ORDET.ESERC_CO
  AND  OC_ORTES.DEPOS_CO = OC_ORDET.DEPOS_CO
  AND  OC_ORTES.TORDI_CO = OC_ORDET.TORDI_CO
  AND  OC_ORTES.ORDIN_NU = OC_ORDET.ORDIN_NU
  AND  OC_ORTES.AZIRF_CO = OC_ORDET.AZIRF_CO
"""

cursor_position = 10

start_pos, end_pos, start_line, end_line = extract_statement_with_positions_space(sql_string, cursor_position)
print(f"Posizione di inizio: {start_pos}, Posizione di fine: {end_pos}")
print(f"Riga di inizio: {start_line}, Riga di fine: {end_line}")
#print(sql_string[start_pos:end_pos])