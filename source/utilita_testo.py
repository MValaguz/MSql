#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python3.11
#  Data..........: 03/10/2023
#  Descrizione...: Funzioni per l'estrazione di codice pl-sql 

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
    """    
    # se posizione in ingresso è fuori range (caso in cui il cursore era all'inizio) --> imposto a zero
    if p_pos == -1:
        p_pos = 0
    # ricerco la parola dove posizionato cursore senza tenere conto del "." 
    v_word = extract_word_from_cursor_pos(p_string, p_pos, False)
    # Divide la parola se contiene un punto
    if '.' in v_word:
        parts = v_word.split('.', 1)
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
    #v_owner, v_object = extract_object_name_from_cursor_pos('	select * from ta_azien ',23)    
    #print(f"{v_owner} {v_object}")    
    
    # test funzione che restituisce parola sotto il cursore
    v_owner, v_oggetto = extract_object_name_from_cursor_pos('select * from ta_azien', 13)                        
    print(f"{v_owner},{v_oggetto}")    