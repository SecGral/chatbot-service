"""
Detector de intenciones del usuario.
Identifica saludos, despedidas, agradecimientos y preguntas.
"""
import logging
from enum import Enum
import re

logger = logging.getLogger(__name__)


class IntentionType(Enum):
    """Tipos de intención detectados."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    THANKS = "thanks"
    CONTACT_REQUEST = "contact_request"  # Nueva intención
    QUESTION = "question"


class IntentionDetector:
    """Detecta la intención detrás de una consulta del usuario."""
    
    GREETINGS = ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "holi", "saludos"]
    FAREWELLS = ["adios", "chao", "hasta luego", "nos vemos", "bye", "adiós"]
    THANKS = ["gracias", "muchas gracias", "thanks", "thank you"]
    
    # Palabras clave para detectar solicitud de contacto
    CONTACT_KEYWORDS = ["numero", "números", "teléfono", "telefono", "móvil", "celular", 
                       "llamar", "contacto", "contactar", "llamada", "cómo", "como"]
    
    # Regiones de Colombia
    COLOMBIAN_REGIONS = ["caribe", "andina", "pacífica", "pacifica", "orinoquía", 
                        "orinoquia", "amazonía", "amazonia", "insular"]
    
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
        
        # Detectar solicitud de contacto
        if cls._is_contact_request(question_lower):
            return IntentionType.CONTACT_REQUEST
        
        # Si no es ninguna de las anteriores, es una pregunta
        return IntentionType.QUESTION
    
    @classmethod
    def _is_contact_request(cls, question_lower: str) -> bool:
        """
        Determina si la pregunta es una solicitud de contacto/números.
        
        Args:
            question_lower: Pregunta en minúsculas
            
        Returns:
            bool: True si es una solicitud de contacto
        """
        # Buscar palabras clave de contacto
        has_contact_keyword = any(keyword in question_lower for keyword in cls.CONTACT_KEYWORDS)
        
        # Buscar regiones mencionadas
        has_region = any(region in question_lower for region in cls.COLOMBIAN_REGIONS)
        
        # Es solicitud de contacto si tiene ambos: palabra clave + región
        return has_contact_keyword and has_region
    
    @classmethod
    def extract_region(cls, question: str) -> str:
        """
        Extrae la región mencionada en la pregunta.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            str: Nombre de la región encontrada o string vacío
        """
        question_lower = question.lower()
        
        for region in cls.COLOMBIAN_REGIONS:
            if region in question_lower:
                return region
        
        return ""
    
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
