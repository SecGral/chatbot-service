from groq import Groq
from sst_agent.app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def generate(prompt: str, max_tokens: int = 500):
    """
    Genera una respuesta usando Groq LLM.
    
    Args:
        prompt: El prompt a enviar al modelo
        max_tokens: Número máximo de tokens en la respuesta
        
    Returns:
        str: La respuesta generada por el modelo
    """
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en Seguridad y Salud en el Trabajo"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=max_tokens
    )

    return completion.choices[0].message.content
