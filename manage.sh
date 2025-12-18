#!/bin/bash

# Script de gestión del SST Agent
# Uso: ./manage.sh [comando]

set -e

VENV_PATH="venv"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Activar entorno virtual
activate_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Entorno virtual no encontrado. Ejecuta: python3 -m venv venv"
        exit 1
    fi
    source "$VENV_PATH/bin/activate"
}

# Comando: start - Iniciar servidor
cmd_start() {
    print_info "Iniciando servidor SST Agent..."
    activate_venv
    uvicorn sst_agent.app.main:app --reload
}

# Comando: start-bg - Iniciar servidor en background
cmd_start_bg() {
    print_info "Iniciando servidor en background..."
    activate_venv
    nohup uvicorn sst_agent.app.main:app --reload > server.log 2>&1 &
    echo $! > .server.pid
    print_success "Servidor iniciado (PID: $(cat .server.pid))"
    print_info "Ver logs: tail -f server.log"
}

# Comando: stop - Detener servidor
cmd_stop() {
    if [ -f .server.pid ]; then
        PID=$(cat .server.pid)
        print_info "Deteniendo servidor (PID: $PID)..."
        kill $PID 2>/dev/null || print_warning "El proceso ya no existe"
        rm .server.pid
        print_success "Servidor detenido"
    else
        print_warning "No hay servidor corriendo"
    fi
}

# Comando: status - Ver estado
cmd_status() {
    print_info "Verificando estado del sistema..."
    activate_venv
    
    # Verificar BD
    python -c "from sst_agent.app.services import vector_db; vector_db.init_vector_db(); count = vector_db.get_indexed_count(); print(f'\n📊 Documentos indexados: {count}')" 2>/dev/null || print_error "Error conectando a la BD"
    
    # Verificar servidor
    if [ -f .server.pid ]; then
        PID=$(cat .server.pid)
        if ps -p $PID > /dev/null 2>&1; then
            print_success "Servidor corriendo (PID: $PID)"
        else
            print_warning "Archivo PID existe pero proceso no está corriendo"
            rm .server.pid
        fi
    else
        print_warning "Servidor no está corriendo"
    fi
}

# Comando: index - Indexar documentos
cmd_index() {
    print_info "Indexando documentos..."
    activate_venv
    
    python -c "
from sst_agent.app.services import vector_db
from sst_agent.app.services.embeddings import embed_text
from sst_agent.app.services.loader import get_all_files, load_file
from sst_agent.app.services.chunking import split_by_sections
import os

vector_db.init_vector_db()
files = get_all_files()
print(f'\n📁 Archivos encontrados: {len(files)}')

indexed = 0
skipped = 0

for file_path in files:
    filename = os.path.basename(file_path)
    
    if vector_db.document_exists(filename):
        print(f'⏭️  {filename} (ya indexado)')
        skipped += 1
        continue
    
    print(f'📄 Indexando {filename}...')
    content = load_file(file_path)
    
    # Dividir en chunks
    chunks = split_by_sections(content, max_chunk_size=2000)
    print(f'   Dividido en {len(chunks)} chunks')
    
    # Indexar cada chunk
    for chunk_idx, chunk in enumerate(chunks):
        embedding = embed_text([chunk])[0].tolist()
        if vector_db.add_document_chunk(filename, chunk, embedding, chunk_idx):
            print(f'   ✓ Chunk {chunk_idx + 1}/{len(chunks)}')
    
    print(f'✅ {filename} indexado con {len(chunks)} chunks')
    indexed += 1

total = vector_db.get_indexed_count()
print(f'\n📊 Resumen:')
print(f'   Archivos nuevos: {indexed}')
print(f'   Ya existentes: {skipped}')
print(f'   Total chunks en BD: {total}')
"
}

# Comando: query - Hacer consulta
cmd_query() {
    if [ -z "$1" ]; then
        print_error "Uso: ./manage.sh query \"tu pregunta aquí\""
        exit 1
    fi
    
    print_info "Consultando: $1"
    curl -X POST http://127.0.0.1:8000/api/query \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"$1\"}" \
        2>/dev/null | python -m json.tool || print_error "Error en consulta. ¿Está el servidor corriendo?"
}

# Comando: init - Inicializar base de datos
cmd_init() {
    print_info "Inicializando base de datos..."
    activate_venv
    python init_db.py
}

# Comando: test - Ejecutar pruebas
cmd_test() {
    print_info "Ejecutando pruebas..."
    activate_venv
    python test_system.py
}

# Comando: install - Instalar dependencias
cmd_install() {
    print_info "Instalando dependencias..."
    
    if [ ! -d "$VENV_PATH" ]; then
        print_info "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    activate_venv
    pip install -r requirements.txt
    print_success "Dependencias instaladas"
}

# Comando: logs - Ver logs
cmd_logs() {
    if [ -f server.log ]; then
        tail -f server.log
    else
        print_warning "No hay archivo de logs. El servidor no está corriendo en background."
    fi
}

# Comando: help - Mostrar ayuda
cmd_help() {
    cat << EOF

🤖 SST Agent - Sistema de Gestión

USO:
    ./manage.sh [comando] [argumentos]

COMANDOS:

    start           Inicia el servidor (modo interactivo)
    start-bg        Inicia el servidor en background
    stop            Detiene el servidor en background
    status          Muestra el estado del sistema
    
    install         Instala todas las dependencias
    init            Inicializa la base de datos
    index           Indexa documentos en data/docs/
    
    query "texto"   Hace una consulta al chatbot
    test            Ejecuta las pruebas del sistema
    logs            Muestra los logs del servidor
    
    help            Muestra esta ayuda

EJEMPLOS:

    # Primera vez
    ./manage.sh install
    ./manage.sh init
    ./manage.sh index
    ./manage.sh start
    
    # Uso diario
    ./manage.sh start-bg
    ./manage.sh query "¿Qué es un incidente laboral?"
    ./manage.sh stop
    
    # Agregar documentos nuevos
    # 1. Colocar archivos en sst_agent/app/data/docs/
    # 2. ./manage.sh index
    
    # Ver estado
    ./manage.sh status

EOF
}

# Main
main() {
    cd "$PROJECT_DIR"
    
    case "${1:-help}" in
        start)      cmd_start ;;
        start-bg)   cmd_start_bg ;;
        stop)       cmd_stop ;;
        status)     cmd_status ;;
        index)      cmd_index ;;
        query)      cmd_query "$2" ;;
        init)       cmd_init ;;
        test)       cmd_test ;;
        install)    cmd_install ;;
        logs)       cmd_logs ;;
        help|*)     cmd_help ;;
    esac
}

main "$@"
