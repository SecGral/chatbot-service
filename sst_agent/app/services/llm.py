import os
from dotenv import load_dotenv
from groq import Groq

# Cargar variables de entorno
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate(prompt: str):
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en Seguridad y Salud en el Trabajo"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=500
    )

    return completion.choices[0].message.content
