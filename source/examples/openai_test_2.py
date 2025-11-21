import os
import oracledb
import faiss
import numpy as np
from openai import OpenAI
from oracle_my_lib import inizializzo_client

inizializzo_client()

# 🔑 Connessione a Oracle
conn = oracledb.connect(
    user="SMILE",
    password="SMILE",
    dsn="BACKUP_815"
)
cursor = conn.cursor()

# 🔍 1. Recupera tutte le tabelle visibili
cursor.execute("""
    SELECT table_name FROM user_tables
""")
tabelle = [r[0] for r in cursor.fetchall()]

# 📐 2. Crea descrizioni testuali delle tabelle
descrizioni = []
for tabella in tabelle:
    cursor.execute(f"""
        SELECT column_name, data_type FROM user_tab_columns
        WHERE table_name = :nome_tabella
    """, [tabella])
    colonne = cursor.fetchall()
    schema = f"Tabella: {tabella}\n" + "\n".join([f"- {col[0]} ({col[1]})" for col in colonne])
    descrizioni.append(schema)

# 🧠 3. Crea embedding con OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
embedding_vettori = []
for descrizione in descrizioni:
    emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=descrizione
    ).data[0].embedding
    embedding_vettori.append(np.array(emb, dtype="float32"))

# 🔎 4. Indicizza con FAISS
dimensione = len(embedding_vettori[0])
index = faiss.IndexFlatL2(dimensione)
index.add(np.array(embedding_vettori))

# 🗣️ 5. Ricevi la domanda dell’utente
domanda = input("Scrivi la tua richiesta SQL (es. mostra i dipendenti con stipendio > 3000): ")

# 🔍 6. Embedding della domanda
query_emb = client.embeddings.create(
    model="text-embedding-3-small",
    input=domanda
).data[0].embedding

# 🎯 7. Trova le tabelle più rilevanti
_, indici_rilevanti = index.search(np.array([query_emb], dtype="float32"), k=5)
schema_rilevante = "\n\n".join([descrizioni[i] for i in indici_rilevanti[0]])

# 🤖 8. Chiamata a OpenAI con schema selezionato
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "Sei un assistente esperto in SQL e PL/SQL per Oracle."},
        {"role": "user", "content": f"Schema rilevante:\n{schema_rilevante}\n\nDomanda: {domanda}"},
    ]
)

# 📤 9. Stampa la query generata
print("\n✅ Query generata:")
print(response.choices[0].message.content)

# 🔚 Chiudi la connessione
cursor.close()
conn.close()