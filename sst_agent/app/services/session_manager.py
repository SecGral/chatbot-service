"""
Gestor de sesiones de conversación.
Mantiene el histórico de mensajes en RAM durante la sesión del usuario.
Se limpia cuando el usuario recarga la página o cierra el navegador.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class Message:
    """Representa un mensaje en la conversación."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """
        Args:
            role: 'user' o 'assistant'
            content: Contenido del mensaje
            timestamp: Momento del mensaje
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class Session:
    """Representa una sesión de conversación."""
    
    def __init__(self, session_id: str, max_messages: int = 50):
        """
        Args:
            session_id: ID único de la sesión
            max_messages: Máximo de mensajes a mantener en memoria
        """
        self.session_id = session_id
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.max_messages = max_messages
    
    def add_user_message(self, content: str) -> None:
        """Añade mensaje del usuario."""
        self.messages.append(Message("user", content))
        self.last_activity = datetime.now()
        self._cleanup_old_messages()
    
    def add_assistant_message(self, content: str) -> None:
        """Añade mensaje del asistente."""
        self.messages.append(Message("assistant", content))
        self.last_activity = datetime.now()
    
    def get_history(self) -> List[Dict]:
        """Retorna histórico de mensajes."""
        return [msg.to_dict() for msg in self.messages]
    
    def get_context_summary(self) -> str:
        """
        Genera un resumen breve del contexto de la conversación.
        Útil para pasarlo al LLM.
        
        Returns:
            str: Resumen en formato texto
        """
        if not self.messages:
            return ""
        
        # Tomar últimos 5 pares pregunta-respuesta para contexto
        recent = self.messages[-10:]
        context_lines = []
        
        for msg in recent:
            prefix = "Usuario:" if msg.role == "user" else "Asistente:"
            context_lines.append(f"{prefix} {msg.content[:100]}...")
        
        return "\n".join(context_lines)
    
    def _cleanup_old_messages(self) -> None:
        """Limpia mensajes antiguos si exceden el máximo."""
        if len(self.messages) > self.max_messages:
            # Mantener solo los últimos max_messages
            self.messages = self.messages[-self.max_messages:]
            logger.debug(f"Sesión {self.session_id}: limpieza de mensajes antiguos")


class SessionManager:
    """Gestor central de sesiones."""
    
    _instance = None
    _sessions: Dict[str, Session] = {}
    _session_timeout = 3600  # 1 hora de inactividad
    
    def __new__(cls):
        """Singleton para mantener sesiones globales."""
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def create_session(cls) -> str:
        """
        Crea una nueva sesión.
        
        Returns:
            str: ID de la sesión
        """
        manager = cls()
        session_id = str(uuid.uuid4())
        manager._sessions[session_id] = Session(session_id)
        
        logger.info(f"Nueva sesión creada: {session_id}")
        return session_id
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Session]:
        """
        Obtiene una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Session o None si no existe
        """
        manager = cls()
        session = manager._sessions.get(session_id)
        
        if session:
            # Verificar si ha expirado
            age = (datetime.now() - session.last_activity).total_seconds()
            if age > cls._session_timeout:
                logger.info(f"Sesión {session_id} expirada por inactividad")
                del manager._sessions[session_id]
                return None
        
        return session
    
    @classmethod
    def add_user_message(cls, session_id: str, content: str) -> bool:
        """
        Añade mensaje de usuario a la sesión.
        
        Returns:
            bool: True si se añadió, False si sesión no existe
        """
        session = cls.get_session(session_id)
        if session:
            session.add_user_message(content)
            return True
        return False
    
    @classmethod
    def add_assistant_message(cls, session_id: str, content: str) -> bool:
        """
        Añade mensaje del asistente a la sesión.
        
        Returns:
            bool: True si se añadió, False si sesión no existe
        """
        session = cls.get_session(session_id)
        if session:
            session.add_assistant_message(content)
            return True
        return False
    
    @classmethod
    def get_history(cls, session_id: str) -> List[Dict]:
        """Obtiene histórico de una sesión."""
        session = cls.get_session(session_id)
        if session:
            return session.get_history()
        return []
    
    @classmethod
    def get_context_summary(cls, session_id: str) -> str:
        """Obtiene resumen de contexto de la sesión."""
        session = cls.get_session(session_id)
        if session:
            return session.get_context_summary()
        return ""
    
    @classmethod
    def clear_session(cls, session_id: str) -> bool:
        """
        Limpia una sesión manualmente.
        
        Returns:
            bool: True si se limpió, False si no existía
        """
        manager = cls()
        if session_id in manager._sessions:
            del manager._sessions[session_id]
            logger.info(f"Sesión {session_id} limpiada manualmente")
            return True
        return False
    
    @classmethod
    def get_active_sessions_count(cls) -> int:
        """Retorna número de sesiones activas."""
        manager = cls()
        return len(manager._sessions)
    
    @classmethod
    def cleanup_expired_sessions(cls) -> int:
        """
        Limpia sesiones expiradas.
        
        Returns:
            int: Número de sesiones limpiadas
        """
        manager = cls()
        expired_ids = []
        
        for session_id, session in manager._sessions.items():
            age = (datetime.now() - session.last_activity).total_seconds()
            if age > cls._session_timeout:
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            del manager._sessions[session_id]
        
        if expired_ids:
            logger.info(f"Sesiones expiradas limpiadas: {len(expired_ids)}")
        
        return len(expired_ids)
