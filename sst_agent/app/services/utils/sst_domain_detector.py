"""
Detector de dominio SST.
Identifica si una pregunta está relacionada con Seguridad y Salud en el Trabajo.
"""
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class DomainType(Enum):
    """Tipos de dominio detectados."""
    SST = "sst"
    OTHER = "other"


class SSTDomainDetector:
    """Detecta si una pregunta está relacionada con SST."""
    
    # Palabras clave relacionadas con SST
    SST_KEYWORDS = [
        # Seguridad general
        "seguridad", "peligro", "riesgo", "accidente", "lesión", "lesiones",
        "herida", "injury", "hazard", "safety", "dangerous", "peligroso",
        
        # Salud ocupacional
        "salud", "enfermedad", "enfermedad ocupacional", "salud ocupacional",
        "health", "occupational", "disease", "illness", "enfermedad profesional",
        
        # Trabajo
        "trabajo", "laboral", "empleado", "trabajador", "employee", "worker",
        "workplace", "sitio de trabajo", "puesto",
        
        # Equipos y EPP
        "ppe", "epp", "equipo de protección", "protección personal", "protective",
        "casco", "chaleco", "guantes", "respirador", "arnés", "boots",
        
        # Normativas SST
        "norma", "decreto", "resolución", "ley", "reglamento", "regulation",
        "compliance", "normativa", "1072", "1562", "1401",
        
        # Procedimientos
        "procedimiento", "protocolo", "evaluación", "assessment", "auditoría",
        "capacitación", "training", "emergencia", "evacuación", "reporte",
        "incident", "accidente", "aro",
        
        # Comités y responsables
        "comité", "copasst", "sst", "responsable", "delegado",
        "coordinador", "supervisor",
        
        # Factores de riesgo
        "ruido", "químico", "ergonómico", "biológico", "psicosocial",
        "estrés", "fatiga", "quemadura", "intoxicación", "virus",
        "bacteria", "exposición", "contaminación",
        
        # Documentos
        "ausentismo", "reporte de accidente", "matriz de riesgos",
        "plan de emergencia", "brigada", "primeros auxilios",
    ]
    
    # Palabras clave de SEGUIMIENTO/COMPARACIÓN - permiten continuar conversación SST
    FOLLOW_UP_KEYWORDS = [
        "diferencia", "comparar", "comparación", "vs", "versus",
        "también", "además", "entonces", "y", "pero",
        "cual es la diferencia", "que diferencia",
        "cual es la relacion", "como", "cual es la ventaja",
        "inconveniente", "cuales son", "en que se parecen"
    ]
    
    # Palabras contextuales que refuerzan SST
    SST_CONTEXT = [
        "empresa", "organización", "fábrica", "oficina", "industria",
        "construcción", "minería", "hospital", "institución", "empresa"
    ]
    
    @classmethod
    def detect_domain(cls, question: str) -> DomainType:
        """
        Detecta si una pregunta es sobre SST o no.
        
        Estrategia:
        1. Si contiene palabras clave SST explícitas → SST
        2. Si es una pregunta de SEGUIMIENTO/COMPARACIÓN → SST 
           (asume que sigue conversación anterior)
        3. Si no tiene nada → OTHER
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            DomainType: SST u OTHER
        """
        question_lower = question.lower()
        logger.debug(f"Detectando dominio para: {question[:50]}...")
        
        # 1. Contar coincidencias con palabras clave SST
        sst_matches = sum(1 for keyword in cls.SST_KEYWORDS if keyword in question_lower)
        
        if sst_matches > 0:
            logger.debug(f"✓ SST por palabras clave ({sst_matches} coincidencias)")
            return DomainType.SST
        
        # 2. Si es pregunta de seguimiento/comparación → asumir que es SST
        # Esto permite que "¿cual es la diferencia entre esos dos?" continúe
        # la conversación de accidentes vs incidentes
        is_follow_up = any(keyword in question_lower for keyword in cls.FOLLOW_UP_KEYWORDS)
        
        if is_follow_up:
            logger.debug(f"✓ SST por pregunta de SEGUIMIENTO (diferencia, comparación, etc)")
            return DomainType.SST
        
        logger.debug("❌ NO-SST: sin palabras clave ni seguimiento")
        return DomainType.OTHER
    
    @classmethod
    def is_sst_related(cls, question: str) -> bool:
        """
        Ataño para verificar si es SST.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            bool: True si es SST
        """
        return cls.detect_domain(question) == DomainType.SST
