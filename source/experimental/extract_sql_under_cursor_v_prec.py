def extract_sql_under_cursor(p_testo: str, p_cursor_pos: int):
    """
    Estrae l'istruzione SQL sotto la posizione p_cursor_pos in p_testo,
    considerando come separatori i caratteri ';' e '/' ma ignorandoli se fanno parte di commenti
    block (/* ... */) o single-line (-- ...).

    Se p_cursor_pos supera la lunghezza del testo viene portato a len(p_testo).  
    Se sotto il cursore ci sono spazi, il cursore viene spostato al primo carattere 
    non-spazio alla sinistra.

    Ritorna una tupla (statement, start_idx, end_idx):
      - statement: il testo dell'istruzione SQL ripulito da spazi, '/' e ';' ai bordi  
      - start_idx: indice di inizio (inclusivo) nell'originale p_testo  
      - end_idx: indice di fine (esclusivo) nell'originale p_testo  
    """
    n = len(p_testo)

    # 1) Clamp del cursore nell'intervallo valido
    if p_cursor_pos > n:
        p_cursor_pos = n
    if p_cursor_pos < 0:
        p_cursor_pos = 0

    # 2) Se sotto il cursore ci sono spazi (o è OOB alla fine), sposto sinistra
    if p_cursor_pos == n or p_testo[p_cursor_pos].isspace():
        # punto di partenza (se p_cursor_pos==n, guardo l'ultimo char)
        i = n - 1 if p_cursor_pos == n else p_cursor_pos
        # scendo finché trovo spazi
        while i >= 0 and p_testo[i].isspace():
            i -= 1
        # se non ho trovato nulla di non-spazio, non c'è statement
        if i < 0:
            return "", 0, 0
        p_cursor_pos = i

    # 3) Costruisco maschera commenti
    comment_mask = [False] * n
    i = 0
    while i < n:
        if i + 1 < n and p_testo[i:i+2] == '/*':
            j = p_testo.find('*/', i+2)
            end_c = (j + 2) if j != -1 else n
            for k in range(i, end_c):
                comment_mask[k] = True
            i = end_c
        elif i + 1 < n and p_testo[i:i+2] == '--':
            j = p_testo.find('\n', i+2)
            end_c = j if j != -1 else n
            for k in range(i, end_c):
                comment_mask[k] = True
            i = end_c
        else:
            i += 1

    separators = {';', '/'}
    # 4) Trovo inizio istruzione (scan backwards)
    start = p_cursor_pos
    if start < n and not comment_mask[start] and p_testo[start] in separators:
        start -= 1
    while start > 0:
        c = p_testo[start-1]
        if not comment_mask[start-1] and c in separators:
            break
        start -= 1

    # 5) Trovo fine istruzione (scan forwards)
    end = p_cursor_pos
    if end > 0 and not comment_mask[end-1] and p_testo[end-1] in separators:
        pass
    while end < n:
        c = p_testo[end]
        if not comment_mask[end] and c in separators:
            break
        end += 1

    # 6) Estraggo e ripulisco dai caratteri trim
    raw = p_testo[start:end]
    trim_chars = {' ', '\t', '\r', '\n', ';', '/'}
    left = 0
    while left < len(raw) and raw[left] in trim_chars:
        left += 1
    right = len(raw)
    while right > 0 and raw[right-1] in trim_chars:
        right -= 1

    statement = raw[left:right]
    final_start = start + left
    final_end = start + right

    return statement, final_start, final_end
