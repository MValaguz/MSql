def extract_word_from_cursor_pos(p_string, p_pos):
    """
       Data una stringa completa p_stringa e una posizione di cursore su di essa, 
       estrae la parola che sta "sotto" la posizione del cursore
       Es. p_string = CIAO A TUTTI QUANTI VOI 
           p_pos = 10
           restituisce TUTTI
    """
    # se posizione cursore è oltre la stringa...esco    
    if p_pos >= len(p_string):
        return ''

    # inizio a comporre la parola partendo dalla posizione del cursore (se non trovo nulla esco)
    v_word=p_string[p_pos]    
    if v_word is None or v_word in ('',' ','=',':'):
        return ''

    # mi sposto a sinistra rispetto al cursore e compongo la parola    
    v_index = p_pos
    while True and v_index > 0:
        v_index -= 1
        if v_index < len(p_string):
            if p_string[v_index] not in (' ','=',':'):
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
            if p_string[v_index] not in (' ','=',':'):
                v_word += p_string[v_index]
            else:
                break
        else:
            break

    return v_word

print(extract_word_from_cursor_pos("FROM   APEX_WORKSPACE_ACTIVITY_LOG", 11))