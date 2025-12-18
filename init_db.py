#!/usr/bin/env python3
"""
Script para inicializar la base de datos PostgreSQL con pgvector.
Ejecutar antes del primer uso del sistema.
"""
import sys
from sst_agent.app.services.db import init_db
from sst_agent.app.services.vector_db import get_indexed_count
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Inicializa la base de datos y verifica la configuración."""
    print("=" * 60)
    print("Inicializador de Base de Datos - SST Agent")
    print("=" * 60)
    print()
    
    try:
        # Inicializar base de datos
        print("🔄 Inicializando base de datos...")
        init_db()
        print("✅ Base de datos inicializada correctamente")
        print()
        
        # Verificar estado
        print("📊 Verificando estado...")
        count = get_indexed_count()
        print(f"   Documentos indexados: {count}")
        print()
        
        if count == 0:
            print("💡 No hay documentos indexados todavía.")
            print("   Usa el endpoint POST /api/index para indexar tus documentos.")
        else:
            print(f"✅ Sistema listo con {count} documentos indexados.")
        
        print()
        print("=" * 60)
        print("✅ Inicialización completada exitosamente")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR durante la inicialización")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Verifica:")
        print("  1. PostgreSQL está corriendo")
        print("  2. La base de datos 'sst_agent' existe")
        print("  3. Las credenciales en .env son correctas")
        print("  4. El usuario tiene permisos para crear extensiones")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
