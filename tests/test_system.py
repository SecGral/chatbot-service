#!/usr/bin/env python3
"""
Script de prueba para verificar todo el sistema RAG con PostgreSQL.
"""
import sys
import os

# Agregar el proyecto al path
sys.path.insert(0, os.path.abspath('.'))

from sst_agent.app.services import vector_db
from sst_agent.app.services.embeddings import embed_text
from sst_agent.app.services.loader import get_all_files, load_file
from sst_agent.app.services.llm import generate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_indexing():
    """Prueba la indexación de documentos."""
    print("\n" + "=" * 60)
    print("PRUEBA 1: Indexación de Documentos")
    print("=" * 60)
    
    try:
        # Inicializar BD
        vector_db.init_vector_db()
        logger.info("✅ Base de datos inicializada")
        
        # Obtener archivos
        files = get_all_files()
        logger.info(f"📁 Archivos encontrados: {len(files)}")
        
        indexed = 0
        skipped = 0
        
        for file_path in files:
            filename = os.path.basename(file_path)
            
            # Verificar si ya está indexado
            if vector_db.document_exists(filename):
                logger.info(f"⏭️  '{filename}' ya indexado")
                skipped += 1
                continue
            
            # Cargar y procesar
            logger.info(f"📄 Procesando '{filename}'...")
            content = load_file(file_path)
            logger.info(f"   Tamaño: {len(content)} caracteres")
            
            # Generar embedding
            logger.info("🔢 Generando embedding...")
            embedding = embed_text([content])[0].tolist()
            
            # Guardar en BD
            if vector_db.add_document(filename, content, embedding):
                logger.info(f"✅ '{filename}' indexado correctamente")
                indexed += 1
            else:
                logger.error(f"❌ Error indexando '{filename}'")
        
        total_docs = vector_db.get_indexed_count()
        
        print(f"\n📊 Resumen:")
        print(f"   Nuevos indexados: {indexed}")
        print(f"   Ya existentes: {skipped}")
        print(f"   Total en BD: {total_docs}")
        
        return total_docs > 0
        
    except Exception as e:
        logger.error(f"❌ Error en indexación: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query(question: str):
    """Prueba una consulta al sistema."""
    print("\n" + "=" * 60)
    print("PRUEBA 2: Consulta al Sistema")
    print("=" * 60)
    print(f"❓ Pregunta: {question}")
    print()
    
    try:
        # Verificar documentos indexados
        doc_count = vector_db.get_indexed_count()
        logger.info(f"📚 Documentos disponibles: {doc_count}")
        
        if doc_count == 0:
            logger.error("❌ No hay documentos indexados")
            return False
        
        # Generar embedding de consulta
        logger.info("🔍 Buscando documentos relevantes...")
        q_vec = embed_text([question])[0].tolist()
        
        # Buscar documentos similares
        results = vector_db.search_similar(q_vec, k=3)
        logger.info(f"📄 Documentos encontrados: {len(results)}")
        
        if not results:
            logger.warning("⚠️  No se encontraron documentos relevantes")
            return False
        
        # Mostrar fuentes
        print("\n📚 Fuentes utilizadas:")
        for i, r in enumerate(results, 1):
            print(f"   {i}. {r['file']}")
        
        # Construir contexto
        context = "\n\n---\n\n".join(r["content"] for r in results)
        
        # Generar respuesta
        logger.info("🤖 Generando respuesta con LLM...")
        prompt = f"""Eres un especialista en Seguridad y Salud en el Trabajo.

Responde usando SOLO el contexto proporcionado.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

        answer = generate(prompt, max_tokens=800)
        
        print("\n💬 Respuesta:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en consulta: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "=" * 60)
    print("🧪 SUITE DE PRUEBAS - Sistema RAG SST Agent")
    print("=" * 60)
    
    success = True
    
    # Prueba 1: Indexación
    if not test_indexing():
        logger.error("❌ Falló la indexación")
        success = False
    else:
        logger.info("✅ Indexación exitosa")
    
    # Prueba 2: Consulta
    question = "¿Qué es un incidente laboral?"
    if not test_query(question):
        logger.error("❌ Falló la consulta")
        success = False
    else:
        logger.info("✅ Consulta exitosa")
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TODAS LAS PRUEBAS PASARON")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
