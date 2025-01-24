import re

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

# Espressione regolare per catturare le istruzioni SQL complete
sql_pattern = re.compile(r"(?i)\b(" + "|".join(sql_keywords) + r")\b.*?(?=\b(" + "|".join(sql_keywords) + r")\b|$)", re.DOTALL)

# Funzione per ottenere l'istruzione completa sotto al cursore
def get_complete_instruction(sql_text, position):
    match = sql_pattern.finditer(sql_text)
    for m in match:
        start, end = m.span()
        if start <= position < end:
            # Calcolare la riga di inizio e la riga di fine
            start_line = sql_text[:start].count('\n') + 1
            end_line = sql_text[:end].count('\n') + 1
            return m.group().strip(), start_line, end_line
    return None, -1, -1

# Ottieni l'istruzione completa sotto al cursore e le righe di inizio e fine
complete_instruction, start_line, end_line = get_complete_instruction(sql_text, cursor_position)
print(f"Istruzione SQL: {complete_instruction}")
print(f"Riga di inizio: {start_line}")
print(f"Riga di fine: {end_line}")
