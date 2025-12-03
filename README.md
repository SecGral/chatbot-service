# SST Agent

Agente inteligente para Seguridad y Salud en el Trabajo.

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn sst_agent.app.main:app --reload


/*(venv) fabrica@Fabrica:~/Documentos/PROYECTOS/Agente_Inteligente/sst_agent$ uvicorn app.main:app --reload*/


# Para cargar el archivo:
curl -X POST http://127.0.0.1:8000/api/index

#para preguntar algo:
Aurl -X POST http://127.0.0.1:8000/api/query -H "Content-Type: application/json" -d '{"question":"Qué es un incidente laboral"}'

#para empezar el agente:
 uvicorn sst_agent.app.main:app --reload

 "tener en cuenta que deben estar dentro del entorno virtual:
 
 source venv/bin/activate
 
 si no activa hayq ue instalarlo"