# Lista di istruzioni SQL su più righe
sql_instructions = [
    "SELECT * FROM TA_AZIEN",
    " ",
    "SELECT *",
    "FROM MS_UTN",
    "WHERE LOGIN_CO='MVALAGUZ'"
]

# Concatenare tutte le istruzioni in un'unica stringa con segnaposto per le righe
sql_text = "\n".join(sql_instructions)

# Supponiamo di avere un puntatore che indica la posizione attuale (ad esempio, 35)
cursor_position = 10

# Lista di parole chiave SQL che indicano l'inizio di una nuova istruzione
sql_keywords = ["SELECT", "UPDATE", "DELETE", "INSERT"]

# Funzione per ottenere l'istruzione completa sotto al cursore
def get_complete_instruction(sql_text, position):
    start_pos = sql_text.rfind('\n', 0, position) + 1
    end_pos = position
    
    # Continuare fino alla fine del testo o fino a trovare una nuova istruzione
    instruction = []
    current_pos = start_pos
    while current_pos < len(sql_text):
        line_end = sql_text.find('\n', current_pos)
        if line_end == -1:
            line_end = len(sql_text)
        line = sql_text[current_pos:line_end].strip()
        if line and any(line.upper().startswith(keyword) for keyword in sql_keywords) and current_pos != start_pos:
            break
        instruction.append(line)
        end_pos = line_end
        current_pos = line_end + 1
    
    # Trovare la posizione di inizio dell'istruzione
    while start_pos > 0:
        prev_line_start = sql_text.rfind('\n', 0, start_pos - 1)
        if prev_line_start == -1:
            prev_line_start = 0
        prev_line = sql_text[prev_line_start:start_pos].strip()
        if any(prev_line.upper().startswith(keyword) for keyword in sql_keywords):
            start_pos = prev_line_start
            break
        start_pos = prev_line_start
    
    # Aggiungi la parte precedente dell'istruzione SQL completa
    instruction = []
    prev_pos = start_pos
    while prev_pos < end_pos:
        line_end = sql_text.find('\n', prev_pos)
        if line_end == -1:
            line_end = len(sql_text)
        line = sql_text[prev_pos:line_end].strip()
        instruction.append(line)
        prev_pos = line_end + 1
    
    return " ".join(instruction).strip(), start_pos, end_pos

# Ottieni l'istruzione completa sotto al cursore e i numeri di carattere di inizio e fine
complete_instruction, start_char, end_char = get_complete_instruction(sql_text, cursor_position)
print(f"Istruzione SQL: {complete_instruction}")
print(f"Posizione di inizio (carattere): {start_char}")
print(f"Posizione di fine (carattere): {end_char}")
