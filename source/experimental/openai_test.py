import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.responses.create(
    model="gpt-4o",
    instructions="Sei un assistente esperto in SQL e PL/SQL.",
    input="Scrivi una query che mostra i dipendenti con stipendio > 3000",
)

print(response.output_text)
