#!/usr/bin/env python3
"""
Script para actualizar el esquema de la base de datos.
Elimina la tabla antigua y crea la nueva con soporte para chunks.
"""
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from sst_agent.app.services.db import Base, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("Actualización de Esquema de Base de Datos")
    print("=" * 60)
    print()
    print("⚠️  ADVERTENCIA: Esto eliminará todos los documentos indexados")
    print("   y creará las tablas con el nuevo esquema (soporte para chunks).")
    print()
    
    respuesta = input("¿Continuar? (si/no): ").lower()
    
    if respuesta not in ['si', 's', 'yes', 'y']:
        print("❌ Operación cancelada")
        return 1
    
    try:
        print("\n🔄 Eliminando tabla antigua...")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
            conn.commit()
        logger.info("✅ Tabla eliminada")
        
        print("🔄 Creando extensión pgvector...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        logger.info("✅ Extensión creada")
        
        print("🔄 Creando tablas con nuevo esquema...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas")
        
        print()
        print("=" * 60)
        print("✅ Actualización completada exitosamente")
        print("=" * 60)
        print()
        print("📝 Próximos pasos:")
        print("   1. Ejecuta: ./manage.sh index")
        print("   2. Los documentos se indexarán automáticamente en chunks")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR durante la actualización")
        print("=" * 60)
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
