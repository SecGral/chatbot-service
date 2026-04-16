# Sistema de Memoria de Sesión

## Descripción General

Se ha implementado un sistema de **memoria de sesión en RAM** para mantener el contexto de conversación dentro de la misma sesión del usuario. 

**Importante:** La memoria se pierde cuando:
- ❌ El usuario recarga la página
- ❌ El usuario cierra el navegador
- ❌ El usuario navega a otra sección del aplicativo (si es diferente instancia)
- ❌ Pasan 1 hora sin actividad (timeout automático)

## Cómo Funciona

### 1. Crear Sesión (Una vez)

**Endpoint:** `POST /api/session/create`

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Uso en Frontend:**
```javascript
// Al cargar la aplicación
const response = await fetch('/api/session/create', { method: 'POST' });
const data = await response.json();
const sessionId = data.session_id;
// Guardar sessionId en variable global o state
```

### 2. Enviar Pregunta con Session ID

**Endpoint:** `POST /api/query`

**Solicitud:**
```json
{
  "question": "¿Qué es un riesgo ergonómico?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta:**
```json
{
  "answer": "Un riesgo ergonómico...",
  "sources": [...],
  "context_used": 3,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Uso en Frontend:**
```javascript
// En cada pregunta
const response = await fetch('/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: userQuestion,
    session_id: sessionId
  })
});
const data = await response.json();
sessionId = data.session_id; // Actualizar (por si fue auto-creada)
```

### 3. Obtener Histórico (Opcional)

**Endpoint:** `GET /api/session/history/{session_id}`

**Respuesta:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "history": [
    {
      "role": "user",
      "content": "¿Qué es un riesgo ergonómico?",
      "timestamp": "2026-03-13T10:30:00"
    },
    {
      "role": "assistant",
      "content": "Un riesgo ergonómico...",
      "timestamp": "2026-03-13T10:30:05"
    },
    {
      "role": "user",
      "content": "¿Cómo prevenirlo?",
      "timestamp": "2026-03-13T10:31:00"
    }
  ]
}
```

### 4. Limpiar Sesión (Opcional)

**Endpoint:** `POST /api/session/clear/{session_id}`

**Respuesta:**
```json
{
  "message": "Sesión limpiada"
}
```

## Flujo Técnico

```
FRONTEND                          BACKEND
   │                                │
   ├─ POST /session/create ────────>│
   │                                │ Crea Session en RAM
   │                                │ Genera UUID
   │<─────────────────── session_id ┤
   │ (Almacena en variable)         │
   │                                │
   │◄─ Usuario pregunta ────────────┤
   │                                │
   ├─ POST /query ─────────────────>│
   │  (question + session_id)       │
   │                                │ Busca Session por ID
   │                                │ Añade mensaje usuario
   │                                │ Obtiene histórico previo
   │                                │ Genera prompt con contexto
   │                                │ Obtiene respuesta LLM
   │                                │ Guarda respuesta
   │<───────────────────────────────┤
   │  (response + session_id)       │
   │ (Muestra al usuario)           │
```

## Comportamiento de Memoria

### Con Session ID Válido

```
Pregunta 1: "¿Qué es un riesgo ergonómico?"
  → LLM responde basado en PDFs
  → Se guarda en sesión

Pregunta 2: "¿Cómo prevenirlo?"
  → LLM recibe contexto: "Usuario preguntó antes sobre riesgos ergonómicos..."
  → Responde de forma coherente con contexto
  → Se guarda en sesión
```

### Sin Session ID (o expirado)

```
Pregunta 1: "¿Qué es un riesgo ergonómico?"
  → Se crea nueva sesión automáticamente
  → LLM responde
  → Se devuelve session_id

Pregunta 2: Sin enviar session_id
  → Se crea NUEVA sesión
  → LLM no tiene contexto de pregunta anterior
  → Responde "en frío"
```

## Ejemplo Frontend - React

```javascript
import useState, useEffect from 'react';

function ChatApp() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  
  // Crear sesión al cargar
  useEffect(() => {
    const createSession = async () => {
      const res = await fetch('/api/session/create', { method: 'POST' });
      const data = await res.json();
      setSessionId(data.session_id);
    };
    createSession();
  }, []);
  
  // Enviar pregunta
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;
    
    // Añadir pregunta al chat
    setMessages(prev => [...prev, { role: 'user', content: input }]);
    
    // Enviar al servidor
    const res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: input,
        session_id: sessionId
      })
    });
    
    const data = await res.json();
    
    // Actualizar session_id si cambió
    setSessionId(data.session_id);
    
    // Añadir respuesta al chat
    setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    
    // Limpiar input
    setInput('');
  };
  
  return (
    <div>
      <div className="chat">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregunta algo..."
        />
        <button type="submit">Enviar</button>
      </form>
    </div>
  );
}
```

## Configuración

### Timeout de Sesión

En `session_manager.py`:
```python
_session_timeout = 3600  # 1 hora en segundos
```

Cambiar a otro valor si es necesario.

### Máximo de Mensajes por Sesión

En `session_manager.py`, al crear sesión:
```python
Session(session_id, max_messages=50)
```

Si la sesión excede 50 mensajes, se eliminan los más antiguos automáticamente.

## Ventajas

✅ El LLM "recuerda" el contexto de la conversación  
✅ Respuestas más coherentes y contextuales  
✅ No requiere base de datos (todo en RAM)  
✅ Automático - el cliente solo envía session_id  
✅ Se limpia automáticamente al recargar/navegar  
✅ Timeout automático después de 1 hora  

## Limitaciones

⚠️ Se pierde al recargar página  
⚠️ Se pierde al cerrarse el navegador  
⚠️ No persiste entre dispositivos  
⚠️ Máximo 50 mensajes por sesión (configurable)  
⚠️ Si el servidor reinicia, todas las sesiones se pierden  
