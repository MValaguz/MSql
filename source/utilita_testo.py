#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 03/10/2023
#  Descrizione...: Funzioni per l'estrazione di codice pl-sql 

import re
from typing import List, Dict

def scrivi_testo_in_output(p_testo):
    """
       Utilizzata per il debug. Scrive nel file C:/MSql/output.txt il parametro p_testo
    """      
    print('Scrittura nel file C:/MSql/output.txt')
    v_file = open('C:/MSql/output.txt','w', newline='')
    v_file.write(p_testo)
    v_file.close()

def scrivi_lista_in_output(p_lista):
    """
       Utilizzata per il debug. Scrive nel file C:/MSql/output.txt il contenuto di p_lista
    """      
    print('Scrittura nel file C:/MSql/output.txt')
    v_file = open('C:/MSql/output.txt','w', encoding='utf-8', newline='')
    for riga in p_lista:
        v_file.write(riga)                
    v_file.close()

def extract_object_name_from_cursor_pos(p_string, p_pos):
    """
       Data una stringa completa p_stringa e una posizione di cursore su di essa, 
       estrae la coppia owner.object che sta "sotto" la posizione del cursore 
       Es. p_string = SELECT * FROM SMI.OP_COM
           p_pos = 20
           restituisce SMI e OP_COM       
       Corretto questo caso dove restituica TA_AZIEN.AZIEN_CO quando invece deve restituire TA_AZIEN
       In pratica se punto si trova a destra della posizione indicata, non viene restituita la doppia stringa
       p_string = SELECT * FROM TA_AZIEN.AZIEN_CO 
       Corretto anche il caso SMILE.TA_AZIEN.AZIEN_CO
    """    
    # se posizione in ingresso è fuori range (caso in cui il cursore era all'inizio) --> imposto a zero
    if p_pos == -1:
        p_pos = 0
    if p_string == '':
        return None, ''
    # ricerco la parola dove posizionato cursore senza tenere conto del "." 
    v_word_with_dot = extract_word_from_cursor_pos(p_string, p_pos, False)
    v_word = extract_word_from_cursor_pos(p_string, p_pos, True)
    # divido la parola se contiene un punto    
    v_pos_dot = v_word_with_dot.find('.')
    #print(f"{v_pos_dot} {v_word_with_dot} {v_word}")
    v_indice = v_word_with_dot.find(v_word) + len(v_word)
    v_word_with_dot = v_word_with_dot[:v_indice]    
    #print(f"{v_pos_dot} {v_word_with_dot} {v_word}")
    # se trovato il punto, controllo che il punto non sia alla destra della posizione in quanto va considerato solo se a sinitra
    # questo per evitare casi dove c'è NOME_TABELLA.NOME_CAMPO rispetto a NOME_SCHEMA.NOME_TABELLA
    if v_pos_dot != -1 and v_word_with_dot.find(v_word) > v_pos_dot:
        parts = v_word_with_dot.split('.', 1)        
        return parts[0], parts[1]
    else:        
        return None, v_word

def extract_word_from_cursor_pos(p_string, p_pos, p_period=True):
    """
       Data una stringa completa p_stringa e una posizione di cursore su di essa, 
       estrae la parola che sta "sotto" la posizione del cursore
       Es. p_string = CIAO A TUTTI QUANTI VOI 
           p_pos = 10
           restituisce TUTTI       
       Se passato il parametro p_period a False, il carattere punto non verrà considerato come separatore e ad esempio la stringa SMI.OP_COM verrà considerata come unica parola
    """                
    # è stato richiesto di considerare "." come separatore di parola
    if p_period:
        v_check1_chars = ('',' ','=',':','.','(',')',';',',',chr(9))
        v_check2_chars = (' ','=',':','.','(',')',';',',',chr(9))
        v_check3_chars = (' ','=',':','\n','\r','.','(',')',';',',',chr(9))
    # ... altrimenti di non considerarlo
    else:
        v_check1_chars = ('',' ','=',':','(',')',';',',',chr(9))
        v_check2_chars = (' ','=',':','(',')',';',',',chr(9))
        v_check3_chars = (' ','=',':','\n','\r','(',')',';',',',chr(9))
    
    # se posizione cursore è oltre la stringa...esco        
    if p_pos > len(p_string):
        return ''
    elif p_pos == len(p_string):
        p_pos -= 1

    # se il cursore è su uno spazio, se riesco lo sposto verso destra (modifica inserita in data 10/04/2025)
    if p_string[p_pos] == ' ' and p_string[p_pos+1] != None:
        p_pos += 1

    # inizio a comporre la parola partendo dalla posizione del cursore (se non trovo nulla esco)
    v_word=p_string[p_pos]
    if (v_word is None or v_word in v_check1_chars):                
        return ''

    # mi sposto a sinistra rispetto al cursore e compongo la parola    
    v_index = p_pos
    while True and v_index > 0:
        v_index -= 1                
        if v_index < len(p_string):                 
            if p_string[v_index] not in v_check2_chars:
                v_word = p_string[v_index] + v_word                
            else:                
                break
        else:
            break

    # mi sposto a destra rispetto al cursore e compongo la parola
    v_index = p_pos
    while True:
        v_index += 1
        if v_index < len(p_string):
            if p_string[v_index] not in v_check3_chars:
                v_word += p_string[v_index]
            else:
                break
        else:
            break

    return v_word

def extract_table_name_from_select(p_string):
    """
       Data istruzione sql in p_string, restituisce nome della tabella interessata da istruzione from
       (es. SELECT AZIEN_CO FROM TA_AZIEN WHERE AZIEN_CO='PROVA' restituisce TA_AZIEN)
    """
    v_split = p_string.split()
    for v_i in range(0,len(v_split)):
        if v_split[v_i].upper() == 'FROM':
            return v_split[v_i+1]
    return ''

def x_y_from_offset_text(p_text, p_offset):
    """
       Analizzando il testo presente in p_text, restituisce il numero riga e colonna
       della posizione p_offset       
    """
    v_riga = 0    
    v_prog = 0
    v_col = 1
    # scorro il testo carattere per carattere e ad ogni ritorno a capo conto la riga
    # da notare come usata funzione per contare il numero di byte per ogni carattere...nella codifica utf-8 ad esempio il carattere "è" occupa due byte mentre in ansi 1
    # da notare come per il ritorno a capo usato solo \n in quanto ci sono anche dei file con ritorni a capo misti!
    for v_testo in p_text:
        v_prog += len(v_testo.encode("utf-8"))
        if v_prog >= p_offset:            
            return v_riga, v_col
        if v_testo == '\n':        
            v_riga += 1
            v_col = 1
        else:
            v_col += 1
    
    # se arrivo qui vuol dire che non ho trovato il punto di ricerca
    return 0,0

class class_definizione():
    """
       Questa classe viene compilata dalla procedura estrai_procedure_function
       e contiene la lista di tutte le procedure-funzioni trovate all'interno di un testo
       e per ogni procedura-funzione una "sotto lista" che elenca i parametri della singola procedura-funzione trovata
    """
    def __init__(self):
        self.nome_definizione = ''
        self.numero_riga_testo = 0
        self.lista_parametri = []
    
    def aggiungi_parametro(self,p_nome_parametro):
        self.lista_parametri.append(p_nome_parametro)

def estrai_procedure_function(p_testo):
    """
       Estrae da p_testo le procedure e le funzioni con i rispetti parametri
       p_testo è una lista di riga di testo!
       Il risultato è una lista formata dalla classe "class_definizione" che contiene 
       in prima battuta il nome della definizione e secondariamente una lista dei paramatri       
    """
    # importo la libreria delle regular expression
    import re

    # controllo se il testo che mi è stato passato ha sia il package specification che il body
    # se esistono entrambi andrò ad analizzare solo la parte di body
    # se non esistono perché siamo in presenza solo di una singola procedura-funzione, considero
    # valido tutto il testo
    # la var v_prima_riga_valida conterrà 0 se non trovato il body oppure la posizione del body
    v_prima_riga_valida = 0
    v_conta = 0
    for result in p_testo:
        v_conta += 1
        v_riga_raw = result.upper()
        if v_riga_raw.find('PACKAGE BODY') != -1:
            v_prima_riga_valida = v_conta
            break

    # analizzo il sorgente e ne estraggo il nome di funzioni e procedure
    v_start = False
    v_start_sezione = False
    v_text_sezione = ''  
    v_lista_definizioni = []      
    v_numero_riga_testo = 0
    for result in p_testo:                       
        # incremento il numero di righe (questo contatore è esterno e serve per la posizione nel testo)                 
        v_numero_riga_testo += 1

        # se la riga è valida perché siamo nel body....
        if v_numero_riga_testo > v_prima_riga_valida:            
            # normalizzo la riga
            v_riga_raw = result.upper()
            v_riga = v_riga_raw.replace('\n','') # tolgo ritorno a capo dalla riga
            v_riga = v_riga.replace('\r','') # tolgo ritorno a capo dalla riga
            v_riga = v_riga.replace('\t',' ') # sostituisco i tab con gli spazi
            v_riga = v_riga.replace('"','') # tolgo i doppi apici dalla riga (potrebbero essere presenti nella dichiarazione della procedura)
            if v_riga.find('--') != -1: # se presente un commento, lo tolgo
                v_riga = v_riga[0:v_riga.find('--')]
            v_riga = v_riga.lstrip() # tolgo gli spazi a sinistra
            v_riga = v_riga.rstrip() # tolgo gli spazi a destra            
            v_riga = re.sub(' +', ' ', v_riga) # tolgo i doppi spazi utilizzando le regular expression                               
            # individuo riga di procedura-funzione        
            if v_riga[0:9] == 'PROCEDURE' or v_riga[0:8] == 'FUNCTION' or v_riga[0:38] == 'CREATE OR REPLACE EDITIONABLE FUNCTION' or v_riga[0:39] == 'CREATE OR REPLACE EDITIONABLE PROCEDURE':                        
                if v_riga[0:38] == 'CREATE OR REPLACE EDITIONABLE FUNCTION' or v_riga[0:39] == 'CREATE OR REPLACE EDITIONABLE PROCEDURE':
                    # il nome della procedura-funzione inizia dal primo carattere punto (uso la funzione che ricava la parola data una posizione su una stringa...)            
                    # es. CREATE OR REPLACE EDITIONABLE PROCEDURE "SMILE"."ACTION_OF_OCLEG_AT"
                    v_nome = extract_word_from_cursor_pos(v_riga, v_riga.find('.')+1)            
                else:
                    # il nome della procedura-funzione inizia dal primo carattere spazio (uso la funzione che ricava la parola data una posizione su una stringa...)            
                    v_nome = extract_word_from_cursor_pos(v_riga, v_riga.find(' ')+1)            
                # creo il nodo con il nome della procedura-funzione
                v_definizione = class_definizione()
                v_definizione.nome_definizione = v_nome
                v_definizione.numero_riga_testo = v_numero_riga_testo                
                v_lista_definizioni.append(v_definizione)
                # indico che lo start di procedure-function è iniziato
                v_start = True
            # indico che sono all'interno di una nuova sezione, terminata la quale poi dovrò esplodere elenco parametri                       
            if v_start:
                # procedura-funzione senza parametri (notare come viene inclusa anche la presenza della parola chiave IS)....
                if not v_start_sezione and v_riga.find('(') == -1 and v_riga.find(' IS') != -1:
                    v_text_sezione = ''
                    v_start = False
                    v_start_sezione = False
                # aperta tonda per i parametri...
                elif v_riga.find('(') != -1:
                    v_start_sezione = True
                    v_text_sezione = v_riga               
                # ...continua la sezione di parametri....
                elif v_start_sezione:
                    v_text_sezione += v_riga
            # elaboro la sezione che contiene i parametri della procedura-funzione
            if v_start_sezione and v_riga.find(')') != -1:                        
                v_text_sezione = v_text_sezione[v_text_sezione.find('(')+1:v_text_sezione.find(')')]                        
                v_elenco_parametri = v_text_sezione.split(',')                
                for v_txt_parametro in v_elenco_parametri:                            
                    v_stringa = v_txt_parametro.lstrip().rstrip()                    
                    # se trovo che il fine parametro è uno spazio prendo solo fino allo spazio 
                    # eliminando di fatto il tipo parametro! Questo perché la struttura verrà usata anche
                    # per fare l'import all'interno dell'editor e quindi meglio non avere il parametro
                    v_pos = v_stringa.find(' ')
                    if v_pos != -1:
                        v_parametro = v_stringa[0:v_pos]
                    else:
                        v_parametro = v_stringa                    
                    v_definizione.aggiungi_parametro(v_parametro)                                                            
                v_text_sezione = ''
                v_start = False
                v_start_sezione = False

    # restituisco la lista delle definizioni che ho trovato
    return v_lista_definizioni

def search_string_in_text(p_text, p_ricerca):
    """
       Dato un testo in p_text, e una stringa di ricerca p_ricerca
       restituisce un array riportante i numeri di riga dove presente p_ricerca.
       La ricerca è case insensitive
       Ogni elemento dell'array contiene un altro array che riporta:
          - numero di riga
          - posizione iniziale p_ricerca
          - posizione finale p_ricerca
          - testo completo della riga trovato 
    """
    # divido il testo in linee usando il separatore di riga
    v_split_linee = p_text.split("\n")  
    # predispongo array che riporta elenco delle righe dove p_ricerca trovato
    v_array_linee = []  

    # ciclo di ricerca
    for i, v_linea in enumerate(v_split_linee):
        v_pos = v_linea.upper().find(p_ricerca.upper())        
        if v_pos != -1:                        
            v_array_linee.append((i+1,v_pos,v_pos+len(p_ricerca),v_linea))  

    return v_array_linee

def search_first_string_in_text(p_testo, p_pattern):
    """
       Restituisce il numero di riga della prima occorrenza che matcha il pattern regex p_pattern
    """
    return next((i for i, line in enumerate(p_testo.splitlines(), 0)
                 if re.search(p_pattern, line, re.IGNORECASE)), None)

def da_qt_a_formato_data_oracle(p_formato):
    """
       Dato il formato data QT library, restituisce il formato data Oracle       
    """
    p_formato = p_formato.replace("%d","DD")
    p_formato = p_formato.replace("%m","MM")
    p_formato = p_formato.replace("%Y","YYYY")
    p_formato = p_formato.replace("%H","HH24")
    p_formato = p_formato.replace("%M","MI")
    p_formato = p_formato.replace("%S","SS")

    return p_formato

def extract_sql_under_cursor(p_testo: str, p_cursor_pos: int):
    """
    ATTENZIONE! Funzione che verrà sostituita da extract_section_under_cursor, quindi obsoleta

    Estrae l'istruzione SQL sotto p_cursor_pos in p_testo,
    considerando come separatori i caratteri ';' e '/' ma trattando '/'
    come terminatore solo se, tolti spazi/tab, è l’unico carattere
    sulla riga. Ignora i separatori dentro commenti block (/*...*/) o
    single-line (--...).

    Ritorna (statement, start_idx, end_idx).
    """
    text = p_testo
    n = len(text)

    # 1) Clamp del cursore
    if p_cursor_pos > n:
        p_cursor_pos = n
    if p_cursor_pos < 0:
        p_cursor_pos = 0

    # 2) Se sotto il cursore ci sono spazi o OOB, scendo a sinistra
    pos = p_cursor_pos
    if pos == n or text[pos].isspace():
        i = n - 1 if pos == n else pos
        while i >= 0 and text[i].isspace():
            i -= 1
        if i < 0:
            return "", 0, 0
        pos = i

    # 3) Costruisco maschera commenti block e single-line
    comment_mask = [False] * n
    i = 0
    while i < n:
        if i + 1 < n and text[i:i+2] == '/*':
            j = text.find('*/', i+2)
            end_c = (j + 2) if j != -1 else n
            for k in range(i, end_c):
                comment_mask[k] = True
            i = end_c
        elif i + 1 < n and text[i:i+2] == '--':
            j = text.find('\n', i+2)
            end_c = j if j != -1 else n
            for k in range(i, end_c):
                comment_mask[k] = True
            i = end_c
        else:
            i += 1

    # Helper: '/' è reale solo se, tolti whitespace, è l'unico char sulla riga
    def is_real_slash(idx: int) -> bool:
        line_start = text.rfind('\n', 0, idx) + 1
        line_end = text.find('\n', idx)
        if line_end == -1:
            line_end = n
        return text[line_start:line_end].strip() == '/'

    # 4) Trovo inizio istruzione (scan backwards)
    start = pos
    # se siamo su delimitatore reale, skip
    c0 = text[start]
    if not comment_mask[start] and (c0 == ';' or (c0 == '/' and is_real_slash(start))):
        start -= 1

    while start > 0:
        c = text[start-1]
        if not comment_mask[start-1] and (c == ';' or (c == '/' and is_real_slash(start-1))):
            break
        start -= 1

    # 5) Trovo fine istruzione (scan forwards)
    end = pos + 1
    while end < n:
        c = text[end]
        if not comment_mask[end] and (c == ';' or (c == '/' and is_real_slash(end))):
            break
        end += 1

    # 6) Estraggo e trimmo bordi
    raw = text[start:end]
    trim_chars = {' ', '\t', '\r', '\n', ';', '/'}
    left = 0
    while left < len(raw) and raw[left] in trim_chars:
        left += 1
    right = len(raw)
    while right > left and raw[right-1] in trim_chars:
        right -= 1

    statement = raw[left:right]
    final_start = start + left
    final_end = start + right

    return statement, final_start, final_end

def commenta_una_procedura_funzione(p_testo, p_autore):
    """
       Riceve in input una porzione di testo che contiene intestazione di procedura-funzione PL-SQL; ne esplora il 
       contenuto e ritorna un commento composto da:
       Autore          :
       Data creazione  :
       Descrizione     :
       Parametri input :
       Parametri output:       

       Ad esempio partendo da questo codice nell'editor:
       /* Restituisce T se l'utente è abilitato alla nuova funzionalità  di APEX */
       FUNCTION APEX_CTR_WMS_ABILITAZIONE(P_AZIEN_CO    IN VARCHAR2
                                         ,P_LOGIN_CO    IN VARCHAR2)

       Viene restituito                           
       /*
         Creata da.......: Marco Valaguzza
         Data............: 28/08/2025
         Descrizione.....: Restituisce T se l'utente è abilitato alla nuova funzionalità  di APEX

         Parametri INPUT : P_AZIEN_CO = 
                           P_LOGIN_CO = 
       */              
       
       NOTA BENE! E' stato usato come carattere di eol (end of line) il \n senza considerare il fatto che nell'editor da cui si parte potrebbe avere anche la codifica Windows
                  Questo perché al termine dell'operazione l'utente dovrà prendere il commento così creato e inserirlo e la copia si occuperà di fare la conversione!
    """    
    from datetime import datetime

    # definizione della prima parte del risultato finale
    v_risultato = '/*\n'
    v_risultato += ' Creata da.......: ' + p_autore + '\n'
    v_risultato += ' Data............: ' + datetime.today().strftime('%d/%m/%Y') + '\n'

    # ricerco la prima ricorrenza tra /* e */ dove dovrei trovare la prima descrizione della procedura-funzione
    v_match = re.search(r'/\*(.*?)\*/', p_testo, re.DOTALL)
    if v_match:
        v_risultato += ' Descrizione.....: ' + v_match.group(1).strip() + '\n\n'
    
    # analizzo il sorgente e ne estraggo il nome di funzioni e procedure
    v_start = False
    v_start_sezione = False
    v_text_sezione = ''  
    for result in p_testo.split('\n'):                       
        # normalizzo la riga
        v_riga_raw = result.upper()        
        v_riga = v_riga_raw.replace('\n','') # tolgo ritorno a capo dalla riga
        v_riga = v_riga.replace('\r','') # tolgo ritorno a capo dalla riga
        v_riga = v_riga.replace('\t',' ') # sostituisco i tab con gli spazi
        v_riga = v_riga.replace('"','') # tolgo i doppi apici dalla riga (potrebbero essere presenti nella dichiarazione della procedura)
        if v_riga.find('--') != -1: # se presente un commento, lo tolgo
            v_riga = v_riga[0:v_riga.find('--')]
        v_riga = v_riga.lstrip() # tolgo gli spazi a sinistra
        v_riga = v_riga.rstrip() # tolgo gli spazi a destra            
        v_riga = re.sub(' +', ' ', v_riga) # tolgo i doppi spazi utilizzando le regular expression                                       
        # individuo riga di procedura-funzione             
        if v_riga[0:9] == 'PROCEDURE' or v_riga[0:8] == 'FUNCTION' or v_riga[0:38] == 'CREATE OR REPLACE EDITIONABLE FUNCTION' or v_riga[0:39] == 'CREATE OR REPLACE EDITIONABLE PROCEDURE':                        
            # indico che lo start di procedure-function è iniziato
            v_start = True
        # indico che sono all'interno di una nuova sezione, terminata la quale poi dovrò esplodere elenco parametri                       
        if v_start:            
            # procedura-funzione senza parametri (notare come viene inclusa anche la presenza della parola chiave IS)....
            if not v_start_sezione and v_riga.find('(') == -1 and v_riga.find(' IS') != -1:
                v_text_sezione = ''
                v_start = False
                v_start_sezione = False
            # aperta tonda per i parametri...
            elif v_riga.find('(') != -1:
                v_start_sezione = True
                v_text_sezione = v_riga               
            # ...continua la sezione di parametri....
            elif v_start_sezione:
                v_text_sezione += v_riga
        # elaboro la sezione che contiene i parametri della procedura-funzione
        if v_start_sezione and v_riga.find(')') != -1:                        
            v_text_sezione = v_text_sezione[v_text_sezione.find('(')+1:v_text_sezione.find(')')]                                    
            v_elenco_parametri = v_text_sezione.split(',')                       
            v_1a_volta_input = True
            v_1a_volta_output = True
            for v_txt_parametro in v_elenco_parametri:                                            
                v_stringa = v_txt_parametro.lstrip().rstrip()                    
                # se trovo che il fine parametro è uno spazio prendo solo fino allo spazio 
                # eliminando di fatto il tipo parametro! Questo perché la struttura verrà usata anche
                # per fare l'import all'interno dell'editor e quindi meglio non avere il parametro
                v_pos = v_stringa.find(' ')
                if v_pos != -1:
                    v_parametro = v_stringa[0:v_pos]
                else:
                    v_parametro = v_stringa                    
                # parametro di input 
                if ' OUT ' not in v_txt_parametro:
                    if v_1a_volta_input:
                        v_risultato += ' Parametri INPUT : ' + v_parametro + ' = \n'
                        v_1a_volta_input = False
                    else:
                        v_risultato += '                   ' + v_parametro + ' = \n'
                else:
                    if v_1a_volta_output:
                        v_risultato += ' Parametri OUTPUT: ' + v_parametro + ' = \n'
                        v_1a_volta_output = False
                    else:
                        v_risultato += '                   ' + v_parametro + ' = \n'

            v_text_sezione = ''
            v_start = False
            v_start_sezione = False

    # chiusura del commento
    v_risultato += '*/'
    
    return v_risultato

def pulisci_commenti_inizio_riga(text: str) -> str:
    """
    Rimuove i commenti all'inizio del testo:
    - righe che iniziano con -- (fino a newline)
    - blocchi /* ... */ (anche multilinea)
    Continua a rimuovere finché all'inizio c'è un commento o spazi vuoti.
    Restituisce il testo rimanente (senza i commenti iniziali).
    """
    if text is None:
        return ""

    i = 0
    n = len(text)

    while True:
        # Salta spazi bianchi iniziali (ma non altri contenuti)
        m = re.match(r'\s*', text[i:])
        if m:
            i += m.end()

        if text.startswith('--', i):
            # rimuove fino al primo newline (incluso) o fino alla fine
            nl = text.find('\n', i)
            if nl == -1:
                # tutta la riga è commento: risultato vuoto
                return ""
            i = nl + 1
            continue

        if text.startswith('/*', i):
            # trova la chiusura */
            end = text.find('*/', i + 2)
            if end == -1:
                # commento non chiuso: rimuoviamo tutto fino alla fine
                return ""
            i = end + 2
            continue

        # se non ci sono commenti iniziali, fermati
        break

    return text[i:]

# Funzione creata da CoPilot con le seguenti direttive
# vorrei creare una funzione python che ricevendo in pasto la stringa "connect username/password@tns_alias" 
# o quella con proxy "connect proxy_user[destination_user]/proxy_password@tns_alias" 
# restituisca i parametri di connessione separati
def extract_connect_info_from_string(connect_string):
    """
        Da una stringa di connect, estrai info di connessione a Oracle DB.
    """
    
    # Rimuove eventuale prefisso "connect"
    connect_string = connect_string.strip()
    if connect_string.lower().startswith("connect "):
        connect_string = connect_string[8:].strip()

    # Regex per proxy: proxy_user[destination_user]/proxy_password@tns_alias
    proxy_pattern = r'^([\w.-]+)\[([\w.-]+)\]/(.+?)@(.+)$'
    # Regex per standard: username/password@tns_alias
    standard_pattern = r'^([\w.-]+)/(.+?)@(.+)$'

    proxy_match = re.match(proxy_pattern, connect_string)
    if proxy_match:
        return {
            "e_user_name": proxy_match.group(2),  # destination_user
            "e_user_proxy": proxy_match.group(1),  # proxy_user
            "e_password": proxy_match.group(3),
            "e_server_name": proxy_match.group(4),
            "e_user_mode": "proxy"
        }

    standard_match = re.match(standard_pattern, connect_string)
    if standard_match:
        return {
            "e_user_name": standard_match.group(1),
            "e_user_proxy": "",
            "e_password": standard_match.group(2),
            "e_server_name": standard_match.group(3),
            "e_user_mode": "standard"
        }

    return {}

# Funzione creata da Copilot con le seguenti direttive
# ho un testo che è diviso in sezioni logiche
# un primo modo per identificare il termine di una sezione logica è il carattere "punto e virgola" che può trovarsi in qualsiasi posizione del testo
# un secondo modo per identificare il termine di una sezione è una riga isolata dove è presente solo il carattere slash (ignorare spazi o/o tab)
# un terzo modo per identificare il termine di una sezione è che ci sia una riga vuota (ignorare spazi e/o tab) prima e dopo la sezione stessa
# ora vorrei creare una funzione python che ricevendo in ingresso il testo (che può essere formattato avendo come carattere di fine riga sia LF che CRLF)
# e un altro parametro di input che indica il carattere su cui è posizionato il cursore, restituisca la sezione di testo.
# La funzione, partendo dalla posizione del cursore, vada indietro sul testo a cercare un inizio di sezione e poi vada avanti, rispetto al cursore, cercando una fine di sezione.
# Quindi restituisca due parametri che indicano la posizione di inizio e fine sezione
# Attenzione! Se una sezione viene in qualche modo identificata tramite slash (ad inizio e fine testo se non c'è, è come se ci fosse),
# allora questa sezione ha la priorità sul cercare una seconda sezione con punto "punto e virgola" (ad inizio e fine testo se non c'è, è come se ci fosse),.
# Lo stesso nel caso di cerchi la terza sezione, solo a fronte del fatto che non trovato nulla con i due metodi precedenti
# la funzione si deve chiamare extract_section_under_cursor
#def extract_section_under_cursor(text: str, cursor_pos: int):
    # """
    # Restituisce (start, end) della sezione logica contenente il cursore.
    # - Accetta testo con terminatori LF, CRLF o CR.
    # - Priorità: sezioni delimitate da righe che contengono solo '/' (ignorando spazi/tab).
    # - Se non ci sono slash, usa ';' come delimitatore (ultimo ';' prima del cursore e primo ';' dopo).
    # - Indici ritornati sono relativi al testo originale e possono essere usati per slicing.
    # """

    # # --- Normalizza la posizione del cursore dentro i limiti del testo
    # if cursor_pos < 0:
    #     cursor_pos = 0
    # if cursor_pos > len(text):
    #     cursor_pos = len(text)

    # # --- Suddivido il testo in righe preservando gli offset originali
    # # Evito l'uso di re: scorro carattere per carattere e riconosco \r\n, \r e \n
    # lines: List[Dict] = []
    # i = 0
    # n = len(text)
    # while i < n:
    #     line_start = i
    #     # avanza fino a trovare \r o \n oppure la fine del testo
    #     while i < n and text[i] not in ('\r', '\n'):
    #         i += 1
    #     # testo della riga (senza terminatore)
    #     line_text = text[line_start:i]

    #     # determina la lunghezza del terminatore di riga (0, 1 o 2)
    #     if i < n and text[i] == '\r':
    #         if i + 1 < n and text[i + 1] == '\n':
    #             line_break_len = 2  # CRLF
    #         else:
    #             line_break_len = 1  # solo CR
    #     elif i < n and text[i] == '\n':
    #         line_break_len = 1  # solo LF
    #     else:
    #         line_break_len = 0  # fine testo senza newline

    #     line_end = i + line_break_len  # indice subito dopo il terminatore di riga
    #     # salvo informazioni utili: testo riga, inizio, fine (incluso newline), fine parte testo
    #     lines.append({
    #         'text': line_text,
    #         'start': line_start,
    #         'end': line_end,
    #         'line_only_end': line_start + len(line_text)
    #     })

    #     # salto oltre il terminatore
    #     i = line_end

    # # se il testo è vuoto, restituisco (0,0)
    # if not lines:
    #     return 0, 0

    # # --- Trovo l'indice della riga che contiene il cursore
    # cursor_line_idx = len(lines) - 1
    # for idx, ln in enumerate(lines):
    #     # la riga contiene il cursore se il cursore è tra start e end (inclusi bordi)
    #     if ln['start'] <= cursor_pos <= ln['end']:
    #         cursor_line_idx = idx
    #         break

    # # --- Helper: verifica se una riga è "slash line"
    # def is_slash_line(s: str) -> bool:
    #     # vogliamo True solo se, dopo aver rimosso spazi e tab ai lati, la riga è esattamente "/"
    #     left = 0
    #     right = len(s) - 1
    #     # rimuovo spazi e tab da sinistra
    #     while left <= right and s[left] in (' ', '\t'):
    #         left += 1
    #     # rimuovo spazi e tab da destra
    #     while right >= left and s[right] in (' ', '\t'):
    #         right -= 1
    #     # se l'area rimanente è esattamente un singolo carattere '/' allora è una slash line
    #     return left == right and left < len(s) and s[left] == '/'

    # # --- Lista indici delle righe che sono slash
    # slash_indices = [i for i, ln in enumerate(lines) if is_slash_line(ln['text'])]

    # # --- Se esistono righe slash, usiamo la delimitazione slash con priorità
    # if slash_indices:
    #     # cerco la slash precedente rispetto alla riga del cursore (scendendo dall'alto)
    #     prev_slash_idx = None
    #     for i in range(cursor_line_idx, -1, -1):
    #         if i in slash_indices:
    #             prev_slash_idx = i
    #             break

    #     # determina inizio sezione: subito dopo la riga slash precedente (includendo newline)
    #     if prev_slash_idx is not None:
    #         start = lines[prev_slash_idx]['end']
    #     else:
    #         # se non c'è slash precedente, inizio sezione = inizio del testo
    #         start = 0

    #     # cerco la slash successiva rispetto alla riga del cursore
    #     next_slash_idx = None
    #     for i in range(cursor_line_idx, len(lines)):
    #         if i in slash_indices:
    #             # se il cursore è nella riga slash corrente, saltiamo questa come "successiva"
    #             # e consideriamo come precedente quella riga (la sezione è la successiva dopo questa riga)
    #             if i == cursor_line_idx and lines[i]['start'] <= cursor_pos <= lines[i]['end']:
    #                 if prev_slash_idx is None:
    #                     prev_slash_idx = i
    #                     start = lines[i]['end']
    #                 continue
    #             next_slash_idx = i
    #             break

    #     # determina fine sezione: inizio della riga slash successiva (esclude la riga slash)
    #     if next_slash_idx is not None:
    #         end = lines[next_slash_idx]['start']
    #     else:
    #         # se non c'è slash successiva, fine sezione = fine del testo
    #         end = len(text)

    #     # sicurezza: assicurarsi che la sezione contenga il cursore; se qualcosa non quadra,
    #     # ritorniamo i bordi del testo per evitare risultati inconsistenti
    #     if start > cursor_pos:
    #         start = 0
    #     if end < cursor_pos:
    #         end = len(text)

    #     return start, end

    # # --- Se non ci sono slash, fallback su delimitatori ';'
    # # Trovo l'ultimo punto e virgola prima del cursore
    # last_semicolon = -1
    # # iterazione fino a cursor_pos-1 per trovare l'ultima occorrenza
    # for i in range(0, min(len(text), cursor_pos)):
    #     if text[i] == ';':
    #         last_semicolon = i
    # sem_start = last_semicolon + 1 if last_semicolon != -1 else 0

    # # Trovo il primo punto e virgola a partire da cursor_pos (incluso)
    # next_semicolon = -1
    # for i in range(cursor_pos, len(text)):
    #     if text[i] == ';':
    #         next_semicolon = i
    #         break
    # sem_end = next_semicolon if next_semicolon != -1 else len(text)

    # # Assicuro che la sezione contenga il cursore; in caso contrario estendo ai bordi
    # if sem_start > cursor_pos:
    #     sem_start = 0
    # if sem_end < cursor_pos:
    #     sem_end = len(text)

    # return sem_start, sem_end

# Funzione creata da ChatGPT con le seguenti direttive
# ho un testo che è diviso in sezioni logiche
# un primo modo per identificare il termine di una sezione logica è il carattere "punto e virgola" che può trovarsi in qualsiasi posizione del testo
# un secondo modo per identificare il termine di una sezione è una riga isolata dove è presente solo il carattere slash (ignorare spazi o/o tab)
# un terzo modo per identificare il termine di una sezione è che ci sia una riga vuota (ignorare spazi e/o tab) prima e dopo la sezione stessa
# ora vorrei creare una funzione python che ricevendo in ingresso il testo (che può essere formattato avendo come carattere di fine riga sia LF che CRLF)
# e un altro parametro di input che indica il carattere su cui è posizionato il cursore, restituisca la sezione di testo.
# La funzione, partendo dalla posizione del cursore, vada indietro sul testo a cercare un inizio di sezione e poi vada avanti, rispetto al cursore, cercando una fine di sezione.
# Quindi restituisca due parametri che indicano la posizione di inizio e fine sezione
# Attenzione! Se una sezione viene in qualche modo identificata tramite slash (ad inizio e fine testo se non c'è, è come se ci fosse),
# allora questa sezione ha la priorità sul cercare una seconda sezione con punto "punto e virgola" (ad inizio e fine testo se non c'è, è come se ci fosse),.
# Lo stesso nel caso di cerchi la terza sezione, solo a fronte del fatto che non trovato nulla con i due metodi precedenti
# la funzione si deve chiamare extract_section_under_cursor
def extract_section_under_cursor(text: str, cursor_pos: int):
    """
    Identifica la sezione logica che contiene il cursore.
    Priorità:
      1) blocchi delimitati da una riga contenente solo '/'
      2) blocchi delimitati da ';'
      3) blocchi delimitati da righe vuote
    Restituisce: (start, end) come indici sul testo originale.
    """

    # --- Normalizzazione posizione cursore ---
    cursor_pos = max(0, min(cursor_pos, len(text)))

    # --- Parser delle righe con riconoscimento CR, LF, CRLF ---
    lines: List[Dict] = []
    i = 0
    n = len(text)

    while i < n:
        line_start = i
        while i < n and text[i] not in ('\r', '\n'):
            i += 1

        line_text = text[line_start:i]

        if i < n and text[i] == '\r':
            if i + 1 < n and text[i + 1] == '\n':
                brk_len = 2   # CRLF
            else:
                brk_len = 1   # CR
        elif i < n and text[i] == '\n':
            brk_len = 1       # LF
        else:
            brk_len = 0

        line_end = i + brk_len

        lines.append({
            "text": line_text,
            "start": line_start,
            "end": line_end,
            "line_only_end": line_start + len(line_text)
        })

        i = line_end

    if not lines:
        return 0, 0

    # --- Trovo la riga del cursore ---
    cursor_line_idx = len(lines) - 1
    for idx, ln in enumerate(lines):
        if ln['start'] <= cursor_pos <= ln['end']:
            cursor_line_idx = idx
            break

    # ------------------------------------------------------
    # 1) SLASH '/'
    # ------------------------------------------------------
    def is_slash_line(s: str) -> bool:
        return s.strip() == "/"

    slash_indices = [i for i, ln in enumerate(lines) if is_slash_line(ln['text'])]

    has_prev_slash = any(i < cursor_line_idx for i in slash_indices)
    has_next_slash = any(i > cursor_line_idx for i in slash_indices)

    if has_prev_slash or has_next_slash:
        prev_slash = None
        for i in range(cursor_line_idx, -1, -1):
            if i in slash_indices:
                prev_slash = i
                break
        start = lines[prev_slash]['end'] if prev_slash is not None else 0

        next_slash = None
        for i in range(cursor_line_idx + 1, len(lines)):
            if i in slash_indices:
                next_slash = i
                break
        end = lines[next_slash]['start'] if next_slash is not None else len(text)

        return start, end  # priorità massima

    # ------------------------------------------------------
    # 2) PUNTO E VIRGOLA
    # ------------------------------------------------------
    last_semicolon = text.rfind(";", 0, cursor_pos)
    next_semicolon = text.find(";", cursor_pos)

    if last_semicolon != -1 or next_semicolon != -1:
        sem_start = last_semicolon + 1 if last_semicolon != -1 else 0
        sem_end = next_semicolon if next_semicolon != -1 else len(text)

        if sem_start <= cursor_pos <= sem_end:
            return sem_start, sem_end

    # ------------------------------------------------------
    # 3) RIGHE VUOTE (fallback) - logica definitiva
    # ------------------------------------------------------
    def is_empty_line(s: str) -> bool:
        return s.strip() == ""

    # --- Inizio della sezione ---
    start_idx = cursor_line_idx
    while start_idx > 0 and not is_empty_line(lines[start_idx - 1]['text']) and not is_slash_line(lines[start_idx - 1]['text']):
        start_idx -= 1
    start = lines[start_idx]['start']

    # --- Fine della sezione ---
    end_idx = cursor_line_idx
    while end_idx < len(lines) - 1 and not is_empty_line(lines[end_idx + 1]['text']) and not is_slash_line(lines[end_idx + 1]['text']):
        end_idx += 1
    end = lines[end_idx]['end']

    return start, end

######################################################################################################################
# TEST DELLA FUNZIONE CHE PARTENDO DA CODICE PL-SQL, RESTITUISCE UN OGGETTO CHE CONTIENE TUTTE LE DEFINIZIONI TROVATE
######################################################################################################################
if __name__ == "__main__":       
    # v_file = open('c:\Msql\APEX_AJAX_UPLOAD.msql','r', newline='').read()   
    # v_lista_def = estrai_procedure_function(v_file.split(chr(10)))
    # # emetto a video il contenuto di tutto quello che ho trovato nel testo
    # v_write = open('c:\\Msql\\output.txt','w', newline='')
    # for ele in v_lista_def:
    #         v_write.write(ele.nome_definizione+' '+str(ele.numero_riga_testo)+'\r\n')
    #         for par in ele.lista_parametri:
    #             v_write.write('   ' + par + '\r\n')    
    # #scrivi_lista_in_output(['ciao\n','marco\r\n'])
    
    # test funzione che restituisce owner e object    
    #v_owner, v_object = extract_object_name_from_cursor_pos('select smile.oc_ortes.azien_co ',19)    
    #print(f"{v_owner} {v_object}")    
    #v_owner, v_object = extract_object_name_from_cursor_pos('select * from smi.op_com ',20)    
    #print(f"{v_owner} {v_object}")    
    
    # test funzione che restituisce parola sotto il cursore
    #v_owner, v_oggetto = extract_object_name_from_cursor_pos('select * from ta_azien', 13)                        
    #print(f"{v_owner},{v_oggetto}")    

    # # test funzione di ricerca di una stringa in un testo
    # v_testo = """
    #             questo è un testo di prova
    #             dove la stringa si ripete
    #             su più righe
    #             e dove il testo ricercato
    #             è la parola stringa
    #             e dove stringa è solo un esempio
    #           """
    # v_lista = search_string_in_text(v_testo, 'stringa')
    # print(v_lista)

    # test della funzione che restituisce istruzione sql che sta sotto il cursore
    # v_testo = """select * 
    # from   ta_azien
    # where  azien_co='SMI'
    # /
    # SELECT * 
    # FROM CP_DIPEN 
    # WHERE AZIEN_CO='SMI' AND 
    #       DIPEN_CO='00035'
    # /
    # SELECT * 
    # FROM CP_DIPEN 
    # WHERE AZIEN_CO='TEC' AND 
    #       DIPEN_CO='00035'
    # union
    # SELECT * 
    # FROM CP_DIPEN 
    # WHERE AZIEN_CO='SMI' AND 
    #       DIPEN_CO='00035'
    # /			
    # declare
    #   v_ok varchar2(100);
    # begin
    #   v_ok := 'ciao';
    # 	dbms_output.put_line(v_ok);
    # end;			
    # /
    # SELECT *
    # FROM   MW_PRELI_TMP
    # WHERE  TIPOR_DO = 'O'
    #    AND ESERC_CO = '2025'
    #    AND DEPOS_CO = 'B1'
    #    AND TORDI_CO = 'ORPI'
    #    AND ORDIN_NU = 10
    #    AND ARTIC_CO IS NOT NULL
    #    /* LA QTA MANCANTE VIENE NETTIFICATA CON LA QTA DI LISTA */
    #    AND QTAMA_NU - QTALI_NU = 0
    #    AND (SELECT DIVPR_CO
    #      FROM   MA_PRAGE
    #      WHERE  MA_PRAGE.AZIEN_CO = MW_PRELI_TMP.AZIEN_CO
    #         AND MA_PRAGE.ARTIC_CO = MW_PRELI_TMP.ARTIC_CO) IS NOT NULL
    #    AND RIFOP_CO IS NOT NULL
    # ORDER BY DATAP_DA, PRIOR_NU
    # /
    # """
    #     print('-'*100)
    #     #v_istruzione, v_tipo, v_riga_inizio, v_riga_fine = extract_sql_under_cursor(v_testo, 20)    
    #     #print(f"{v_istruzione} {v_tipo},{v_riga_inizio},{v_riga_fine}")
    #     v_istruzione, v_riga_inizio, v_riga_fine = extract_sql_under_cursor(v_testo, 20)    
    #     print(f"{v_istruzione} ,{v_riga_inizio},{v_riga_fine}")
    #     #print(v_testo[v_riga_inizio:v_riga_fine],)   

    v_testo = """    select * 
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
    ORDER BY DATAP_DA, PRIOR_NU
/		

select * from ta_azien

select * from ma_depos
"""
    v_start, v_end = extract_section_under_cursor(v_testo, 20)
    print(v_testo[v_start:v_end])
    v_start, v_end = extract_section_under_cursor(v_testo, 400)
    print(v_testo[v_start:v_end])
    v_start, v_end = extract_section_under_cursor(v_testo, 1100)
    print(v_testo[v_start:v_end])