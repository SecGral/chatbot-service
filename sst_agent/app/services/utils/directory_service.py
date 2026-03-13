"""
Servicio de Directorio de contactos SST.
Gestiona y proporciona contactos del directorio para derivaciones.
"""
import logging
from typing import Dict, Any, Optional, List
from pypdf import PdfReader
import re
import os

logger = logging.getLogger(__name__)


class DirectoryService:
    """Servicio para acceder al directorio de contactos SST."""
    
    # Contactos generales
    DEFAULT_CONTACTS = {
        "nacional": {
            "nombre": "Servicio Nacional de SST",
            "email": "contacto@sst.gov.co",
            "telefono": "+57 1 3200000",
            "descripcion": "Contacto general para consultas específicas"
        },
        "emergencia": {
            "nombre": "Línea de Emergencia SST",
            "telefono": "018000",
            "descripcion": "Para reportes de emergencias y accidentes graves"
        }
    }
    
    # Cache de directorios regionales
    _regional_directory_cache = None
    
    @classmethod
    def _load_regional_directory(cls) -> Dict[str, Dict[str, Any]]:
        """
        Carga el directorio regional desde el PDF.
        Utiliza caché para evitar lecturas repetidas.
        
        Returns:
            Dict: Directorio regional organizado por nombre de región
        """
        if cls._regional_directory_cache is not None:
            return cls._regional_directory_cache
        
        try:
            # Buscar el PDF del directorio
            pdf_path = "sst_agent/app/data/docs/Directorio_Regional_Colombia_Ficticio.pdf"
            
            # Si no existe con ruta relativa, intentar con ruta absoluta
            if not os.path.exists(pdf_path):
                import pathlib
                base_path = pathlib.Path(__file__).parent.parent.parent.parent.parent
                pdf_path = base_path / "sst_agent/app/data/docs/Directorio_Regional_Colombia_Ficticio.pdf"
            
            if not os.path.exists(pdf_path):
                logger.warning(f"No se encontró directorio regional en {pdf_path}")
                return {}
            
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "")
            
            # Parsear el texto para extraer regiones y contactos
            directory = cls._parse_directory_text(text)
            cls._regional_directory_cache = directory
            logger.info(f"Directorio regional cargado: {len(directory)} regiones encontradas")
            return directory
            
        except Exception as e:
            logger.error(f"Error cargando directorio regional: {e}")
            return {}
    
    @classmethod
    def _parse_directory_text(cls, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Parsea el texto del PDF para extraer información regional.
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            Dict: Directorio organizado por región
        """
        directory = {}
        
        # Patrón para encontrar regiones y sus datos
        # Busca "Región [Nombre]" seguido de teléfono, móvil, correo
        region_pattern = r'Región\s+([^\n]+)\n(.*?)(?=Región|Nota:|$)'
        
        for match in re.finditer(region_pattern, text, re.DOTALL | re.IGNORECASE):
            region_name = match.group(1).strip()
            region_data = match.group(2)
            
            # Extraer datos específicos
            tel_match = re.search(r'Tel:\s*([^\n]+)', region_data)
            movil_match = re.search(r'Móvil:\s*([^\n]+)', region_data)
            email_match = re.search(r'Correo:\s*([^\n]+)', region_data)
            
            directory[region_name.lower()] = {
                "nombre": region_name,
                "telefono": tel_match.group(1).strip() if tel_match else "No disponible",
                "movil": movil_match.group(1).strip() if movil_match else "No disponible",
                "email": email_match.group(1).strip() if email_match else "No disponible",
                "descripcion": f"Oficina Regional de {region_name}"
            }
        
        return directory
    
    @classmethod
    def get_general_contact(cls) -> Dict[str, Any]:
        """
        Obtiene contacto general para consultas SST.
        
        Returns:
            Dict: Información de contacto general
        """
        try:
            # Obtener del PDF en futuro
            contact = cls.DEFAULT_CONTACTS.get("nacional", {})
            logger.info("Contacto general solicitado")
            return contact
        except Exception as e:
            logger.error(f"Error obteniendo contacto general: {e}")
            return cls.DEFAULT_CONTACTS.get("nacional", {})
    
    @classmethod
    def get_emergency_contact(cls) -> Dict[str, Any]:
        """
        Obtiene contacto de emergencia.
        
        Returns:
            Dict: Información de contacto de emergencia
        """
        try:
            contact = cls.DEFAULT_CONTACTS.get("emergencia", {})
            logger.info("Contacto de emergencia solicitado")
            return contact
        except Exception as e:
            logger.error(f"Error obteniendo contacto de emergencia: {e}")
            return cls.DEFAULT_CONTACTS.get("emergencia", {})
    
    @classmethod
    def get_regional_contact(cls, region: Optional[str] = None, 
                            ciudad: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene contacto regional específico.
        
        Args:
            region: Región o departamento (opcional)
            ciudad: Ciudad (opcional)
            
        Returns:
            Dict: Información de contacto regional o contacto general
        """
        if not region:
            logger.info("Contacto regional solicitado sin región específica")
            return cls.get_general_contact()
        
        # Cargar directorio regional
        directory = cls._load_regional_directory()
        
        # Buscar región normalizada
        region_lower = region.lower().strip()
        
        # Búsqueda exacta
        if region_lower in directory:
            logger.info(f"Contacto regional encontrado: {region}")
            return directory[region_lower]
        
        # Búsqueda parcial (contiene el término)
        for key, contact in directory.items():
            if region_lower in key or key in region_lower:
                logger.info(f"Contacto regional encontrado con búsqueda parcial: {contact['nombre']}")
                return contact
        
        logger.info(f"Contacto regional no encontrado para: {region}. Retornando contacto general")
        return cls.get_general_contact()
    
    @classmethod
    def format_contact_info(cls, contact: Dict[str, Any]) -> str:
        """
        Formatea la información de contacto para presentación.
        
        Args:
            contact: Diccionario con datos de contacto
            
        Returns:
            str: Texto formateado
        """
        info_parts = []
        
        if contact.get("nombre"):
            info_parts.append(f"**{contact['nombre']}**")
        
        if contact.get("descripcion"):
            info_parts.append(contact["descripcion"])
        
        if contact.get("telefono"):
            info_parts.append(f"📞 Teléfono: {contact['telefono']}")
        
        if contact.get("movil"):
            info_parts.append(f"📱 Célular: {contact['movil']}")
        
        if contact.get("email"):
            info_parts.append(f"📧 Email: {contact['email']}")
        
        if contact.get("horario"):
            info_parts.append(f"🕐 Horario: {contact['horario']}")
        
        return "\n".join(info_parts)
    
    @classmethod
    def get_formatted_contact(cls, contact_type: str = "general", 
                            region: Optional[str] = None) -> str:
        """
        Obtiene contacto formateado listo para mostrar al usuario.
        
        Args:
            contact_type: Tipo de contacto (general, emergencia, regional)
            region: Región específica si es tipo regional
            
        Returns:
            str: Contacto formateado
        """
        if contact_type == "emergencia":
            contact = cls.get_emergency_contact()
        elif contact_type == "regional" and region:
            contact = cls.get_regional_contact(region=region)
        else:
            contact = cls.get_general_contact()
        
        return cls.format_contact_info(contact)
    
    @classmethod
    def get_all_regions(cls) -> List[str]:
        """
        Obtiene la lista de todas las regiones disponibles.
        
        Returns:
            List[str]: Lista de nombres de regiones
        """
        directory = cls._load_regional_directory()
        return [contact["nombre"] for contact in directory.values()]
