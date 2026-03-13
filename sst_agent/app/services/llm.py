from groq import Groq
import logging
from sst_agent.app.core.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are an expert in Occupational Safety and Health (SST/OSH).

**Core Behavior:**
- Respond professionally and clearly based on SST best practices and regulations
- Always cite the source material when providing information
- If information is not available in the context, clearly state it
- Be conversational and friendly, not robotic
- Prefer direct answers over lengthy explanations

**When Answering Questions:**
- If exact information exists: explain it completely and contextually
- If related information exists: share it and connect it to the question
- If definitions are found: cite them textually
- Never fabricate information or make assumptions beyond context

**Response Format:**
- Lead with the most relevant answer
- Include source references when applicable
- Keep language accessible but professional
"""

client = Groq(api_key=GROQ_API_KEY)

def generate(prompt: str, max_tokens: int = 500, context: str = None) -> str:
    """
    Genera una respuesta usando Groq LLM.
    
    Args:
        prompt: Pregunta del usuario
        max_tokens: Máximo de tokens en la respuesta
        context: (Opcional) Contexto RAG para inyectar
    """
    try:
        # Construir mensaje de usuario con contexto si existe
        user_message = prompt
        if context:
            user_message = f"{context}\n\n---\n\nUSER QUESTION: {prompt}"
        
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=max_tokens
        )

        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error llamando a Groq: {e}")
        return "Lo siento, ocurrió un error al generar la respuesta."
    