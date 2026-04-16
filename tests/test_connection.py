#!/usr/bin/env python3
"""
Script para probar la conexión a PostgreSQL y configurar la contraseña.
"""
import sys
import getpass
from sqlalchemy import create_engine, text

def test_connection(database_url):
    """Prueba la conexión a la base de datos."""
    try:
        engine = create_engine(database_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conexión exitosa!")
            print(f"📊 PostgreSQL: {version[:50]}...")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    print("=" * 60)
    print("Configurador de Conexión PostgreSQL")
    print("=" * 60)
    print()
    
    # Opciones comunes
    print("Probando configuraciones comunes...")
    print()
    
    # Opción 1: Sin contraseña (peer authentication)
    print("1️⃣  Probando sin contraseña (peer authentication)...")
    url1 = "postgresql://postgres@localhost:5432/sst_agent"
    if test_connection(url1):
        print()
        print("🎉 ¡Funciona! Copia esta línea a tu .env:")
        print(f"DATABASE_URL={url1}")
        return 0
    print()
    
    # Opción 2: Con usuario actual del sistema
    import os
    current_user = os.getenv("USER")
    print(f"2️⃣  Probando con usuario del sistema ({current_user})...")
    url2 = f"postgresql://{current_user}@localhost:5432/sst_agent"
    if test_connection(url2):
        print()
        print("🎉 ¡Funciona! Copia esta línea a tu .env:")
        print(f"DATABASE_URL={url2}")
        return 0
    print()
    
    # Opción 3: Pedir contraseña
    print("3️⃣  Prueba con contraseña personalizada")
    print()
    username = input("Usuario de PostgreSQL [postgres]: ").strip() or "postgres"
    password = getpass.getpass("Contraseña: ")
    
    url3 = f"postgresql://{username}:{password}@localhost:5432/sst_agent"
    if test_connection(url3):
        print()
        print("🎉 ¡Funciona! Copia esta línea a tu .env:")
        print(f"DATABASE_URL=postgresql://{username}:{password}@localhost:5432/sst_agent")
        return 0
    
    print()
    print("=" * 60)
    print("❌ No se pudo establecer conexión")
    print("=" * 60)
    print()
    print("Sugerencias:")
    print("1. Verifica que PostgreSQL esté corriendo:")
    print("   sudo systemctl status postgresql")
    print()
    print("2. Intenta conectar manualmente:")
    print("   psql -U postgres -d sst_agent")
    print()
    print("3. Si usas 'peer authentication', conéctate como usuario del sistema:")
    print("   sudo -u postgres psql sst_agent")
    print()
    return 1

if __name__ == "__main__":
    sys.exit(main())
