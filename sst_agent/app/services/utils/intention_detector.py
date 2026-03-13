"""
Detector de intenciones del usuario.
Identifica saludos, despedidas, agradecimientos y preguntas.
"""
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class IntentionType(Enum):
    """Tipos de intención detectados."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    THANKS = "thanks"
    QUESTION = "question"


class IntentionDetector:
    """Detecta la intención detrás de una consulta del usuario."""
    
    GREETINGS = ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "holi", "saludos"]
    FAREWELLS = ["adios", "chao", "hasta luego", "nos vemos", "bye", "adiós"]
    THANKS = ["gracias", "muchas gracias", "thanks", "thank you"]
    
    @classmethod
    def detect(cls, question: str) -> IntentionType:
        """
        Detecta la intención de una pregunta.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            IntentionType: Tipo de intención detectada
        """
        question_lower = question.lower().strip()
        words = question_lower.split()
        
        # Detectar saludo (máximo 3 palabras)
        if len(words) <= 3:
            if any(saludo == question_lower or question_lower.startswith(saludo) for saludo in cls.GREETINGS):
                return IntentionType.GREETING
            
            # Detectar despedida
            if any(despedida in question_lower for despedida in cls.FAREWELLS):
                return IntentionType.FAREWELL
        
        # Detectar agradecimiento (máximo 4 palabras)
        if len(words) <= 4:
            if any(gracias == question_lower for gracias in cls.THANKS):
                return IntentionType.THANKS
        
        # Si no es ninguna de las anteriores, es una pregunta
        return IntentionType.QUESTION
    
    @classmethod
    def has_greeting_prefix(cls, question: str) -> bool:
        """
        Verifica si la pregunta comienza con un saludo.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            bool: True si tiene saludo al inicio
        """
        words = question.lower().split()
        return any(saludo in words[:3] for saludo in cls.GREETINGS)
