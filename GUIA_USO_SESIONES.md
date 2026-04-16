# Guía: Cómo Usar Correctamente la API de Chat con Sesiones

## El Problema

El servidor mantiene la memoria en sesiones, pero si el **cliente NO guarda y reenvia el `session_id`**, cada pregunta crea una **nueva sesión vacía**. Por eso ves:

```
1. Primera pregunta → Nueva sesión: abc123 ✓
2. Segunda pregunta → Nueva sesión: def456 ✗ (debería usar abc123)
```

## La Solución: Guardar el `session_id`

### ❌ INCORRECTO - Crea nueva sesión cada vez

```javascript
// MALO: No guarda session_id
async function askQuestion(question) {
  const response = await fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({ question })
    // ❌ SIN session_id
  });
  return await response.json();
}
```

### ✅ CORRECTO - Reutiliza la misma sesión

```javascript
// BIEN: Guarda y reenvia session_id
let sessionId = null;

async function initChat() {
  // 1. Crear sesión UNA SOLA VEZ
  const res = await fetch('/api/session/create', { method: 'POST' });
  sessionId = (await res.json()).session_id;
  console.log('Sesión iniciada:', sessionId);
}

async function askQuestion(question) {
  if (!sessionId) {
    await initChat(); // Asegurar que existe sesión
  }
  
  // 2. Enviar pregunta CON session_id
  const response = await fetch('/api/query', {
    method: 'POST',
    body: JSON.stringify({
      question,
      session_id: sessionId  // ✅ IMPORTANTE
    })
  });
  
  const data = await response.json();
  sessionId = data.session_id; // Guardar (por si cambió)
  return data;
}

// FLUJO CORRECTO:
// 1. Al cargar la página: initChat()
// 2. Usuario pregunta: askQuestion("¿Qué es SST?")
// 3. Usuario pregunta: askQuestion("¿Cómo prevenirlo?") ← Mantiene contexto
```

## Ejemplo React Completo

```javascript
import { useState, useEffect } from 'react';

function Chat() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Crear sesión al montar
  useEffect(() => {
    const initSession = async () => {
      try {
        const res = await fetch('/api/session/create', { method: 'POST' });
        const data = await res.json();
        setSessionId(data.session_id);
        console.log('✓ Sesión creada:', data.session_id);
      } catch (err) {
        console.error('Error creando sesión:', err);
      }
    };
    
    initSession();
  }, []);

  // Enviar pregunta
  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          session_id: sessionId  // ✅ CLAVE
        })
      });

      const data = await response.json();
      
      // Guardar nuevo sessionId (por si fue auto-creado)
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      const assistantMsg = { 
        role: 'assistant', 
        content: data.answer,
        sources: data.sources 
      };
      setMessages(prev => [...prev, assistantMsg]);
      
    } catch (err) {
      console.error('Error enviando pregunta:', err);
      const errorMsg = { role: 'assistant', content: 'Error: ' + err.message };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <p>{msg.content}</p>
            {msg.sources && (
              <small className="sources">
                Fuentes: {msg.sources.map(s => s.file).join(', ')}
              </small>
            )}
          </div>
        ))}
        {loading && <div className="loading">Escribiendo...</div>}
      </div>

      <form onSubmit={handleSend} className="input-form">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregunta sobre SST..."
          disabled={!sessionId}
        />
        <button type="submit" disabled={!sessionId || loading}>
          Enviar
        </button>
      </form>
      
      {sessionId && (
        <small className="session-info">
          Sesión: {sessionId.slice(0, 8)}...
        </small>
      )}
    </div>
  );
}

export default Chat;
```

## Verificación en Logs

Después de arreglar el cliente, deberías ver:

```
✓ Sesión recibida del cliente: 550e8400-e29b-41d4-a716...  ← BIEN
✓ Usando session_id del cliente: 550e8400...  ← BIEN

Vs.

⚠️ Cliente NO envió session_id → Nueva sesión: 550e8400...  ← PROBLEMA
```

## Puntos Clave

1. **Crear sesión UNA SOLA VEZ** al cargar la aplicación
2. **Guardar el `session_id`** que retorna
3. **Enviar `session_id` en CADA pregunta** en el JSON
4. **Reutilizar el mismo `session_id`** mientras está en la misma página
5. Al recargar/navegar → Se pierde el `session_id` → Nueva sesión (esto es correcto)

## Alternativa: localStorage (para persistencia entre recargas)

Si quieres que la sesión **persista entre recargas** (opcional):

```javascript
// Guardar sesión en localStorage
useEffect(() => {
  if (sessionId) {
    localStorage.setItem('chatSessionId', sessionId);
  }
}, [sessionId]);

// Restaurar sesión al cargar
useEffect(() => {
  const savedSessionId = localStorage.getItem('chatSessionId');
  if (savedSessionId) {
    setSessionId(savedSessionId);
    console.log('✓ Sesión restaurada desde localStorage');
  } else {
    // Crear nueva si no existe
    initSession();
  }
}, []);
```

⚠️ **Limitación**: La sesión servidor caduca después de 1 hora sin actividad, así que localStorage solo funciona si el usuario vuelve dentro de ese tiempo.
