# Mejoras en Respuestas del SST Bot

## 📊 Flujo General Actualizado

```
┌─ PREGUNTA DEL USUARIO
│
├─ ¿Intención especial? (saludo/despedida/gracias)
│  └─ SÍ → Responder directamente
│
├─ ¿Es sobre SST? (detector de palabras clave)
│  │
│  ├─ NO → Responder inmediatamente sin buscar en PDFs ✅
│  │
│  └─ SÍ → Verificar documentos indexados
│     │
│     ├─ No hay documentos → Error
│     │
│     ├─ Búsqueda sin resultados → Proporcionar contacto ✅
│     │
│     └─ Hay resultados → Respuesta normal con fuentes ✅
```

## Cambios Implementados

Se ha mejorado la lógica de respuestas del chatbot para diferenciar entre preguntas relacionadas con SST y preguntas ajenas al dominio.

### 1. **Nuevo Detector de Dominio SST** 
**Archivo:** `sst_agent/app/services/utils/sst_domain_detector.py`

- Detecta automáticamente si una pregunta está relacionada con **Seguridad y Salud en el Trabajo (SST)**
- Utiliza palabras clave específicas del dominio (procedimientos, riesgos, normativas, etc.)
- Retorna `DomainType.SST` o `DomainType.OTHER`

**Palabras clave detectadas:**
- Seguridad, riesgos, accidentes, lesiones
- Salud ocupacional, enfermedad profesional
- Normativas (Decreto 1072, Ley 1562, Resolución 1401)
- Equipos de protección (EPP)
- Factores de riesgo (ruido, químico, ergonómico, etc.)

### 2. **Servicio de Directorio**
**Archivo:** `sst_agent/app/services/utils/directory_service.py`

- Gestiona contactos para derivaciones
- Actualmente incluye contactos generales y de emergencia
- **Estructura preparada** para futuros contactos por región/ciudad desde el PDF

**Métodos disponibles:**
- `get_general_contact()` - Contacto general SST
- `get_emergency_contact()` - Contacto de emergencia
- `get_regional_contact(region, ciudad)` - Contactos regionales (futuro)
- `format_contact_info()` - Formatea contactos para presentación al usuario

### 3. **Nuevas Respuestas en ResponseFormatter**
**Archivo:** `sst_agent/app/services/utils/response_formatter.py`

Se agregaron dos nuevos métodos:

#### `format_non_sst_query_response()`
Cuando la pregunta **NO es sobre SST**:
```
"Lo siento, mi especialidad es responder preguntas sobre Seguridad y Salud en el Trabajo (SST). 
Tu pregunta no parece estar relacionada con este tema.

Te sugiero que consultes otras fuentes de información especializadas en el tema que mencionas."
```

#### `format_sst_no_results_response(contact_info)`
Cuando la pregunta **SÍ es sobre SST** pero no hay información en los PDFs:
```
"Lo siento, no encontré información específica sobre esto en la documentación disponible. 
Sin embargo, como se trata de un tema relacionado con SST, te puedo proporcionar un contacto 
que puede ayudarte:

[INFORMACIÓN DE CONTACTO]"
```

### 4. **Lógica en QueryService**
**Archivo:** `sst_agent/app/services/query_service.py`

**Nuevo flujo mejorado - Detección ANTES de buscar:**

```python
# 1. Detectar intención
intention = IntentionDetector.detect(question)

# 2. Si es saludo/despedida/gracias → responder directamente
if intention == IntentionType.GREETING:
    return ResponseFormatter.format_greeting_response()

# 3. Detectar dominio SST ANTES de buscar en PDFs
is_sst = SSTDomainDetector.is_sst_related(question)

# 4. Si NO es SST → responder sin buscar en PDFs
if not is_sst:
    return ResponseFormatter.format_non_sst_query_response()

# 5. Si ES SST → buscar en PDFs
results = RAGService.search_context(question)

if not results:
    # SST pero sin información → proporcionar contactos
    contact_info = DirectoryService.get_formatted_contact()
    return ResponseFormatter.format_sst_no_results_response(contact_info)

# 6. Hay resultados SST → respuesta normal
answer = generate(prompt_text, context=context)
return ResponseFormatter.format_query_response(answer, results)
```

**Ventaja clave:** Las preguntas no-SST se responden inmediatamente sin acceder a los PDFs de SST.

## Ejemplos de Comportamiento

### Pregunta NO-SST (ej: "¿qué es un carro?")
**Antes (sin esta mejora):**
```
Lo siento, pero no hay información sobre un "carro" en el contexto proporcionado. 
El contexto parece estar relacionado con la salud ocupacional...
Si deseas saber qué es un "carro" en un contexto general, puedo decirte que...

📚 Fuentes consultadas:
1. resolucion-1401-2007.pdf
2. Ley-1562-de-2012.pdf
3. Decreto_1072_de_2015_Sector_Trabajo.pdf
```

**Ahora (con esta mejora) - Respuesta inmediata:**
```
Lo siento, mi especialidad es responder preguntas sobre Seguridad y Salud en el Trabajo (SST). 
Tu pregunta no parece estar relacionada con este tema.

Te sugiero que consultes otras fuentes de información especializadas en el tema que mencionas.
```

### Pregunta SST sin documentos (ej: "¿cuál es el protocolo para...")
**Antes:**
```
No encontré información relevante en los documentos indexados.
```

**Ahora:**
```
Lo siento, no encontré información específica sobre esto en la documentación disponible. 
Sin embargo, como se trata de un tema relacionado con SST, te puedo proporcionar un contacto 
que puede ayudarte:

**Servicio Nacional de SST**
Contacto general para consultas específicas
📞 Teléfono: +57 1 3200000
📧 Email: contacto@sst.gov.co
```

## Mejoras Futuras

1. **Contactos Regionales Específicos**
   - Leer contactos del PDF `Directorio_Regional_Colombia_Ficticio.pdf`
   - Extraer por región, ciudad y dependencia
   - Proporcionar contacto más específico al usuario

2. **Geolocalización del Usuario**
   - Detectar ubicación del usuario (región/ciudad)
   - Proporcionar contacto automáticamente de su zona

3. **Refinamiento de Palabras Clave**
   - Añadir más palabras clave específicas según feedback
   - Implementar búsqueda más sofisticada (NLP)

4. **Categorización de Preguntas SST**
   - Diferenciar entre tipos de preguntas SST (procedimientos, riesgos, normativas, etc.)
   - Proporcionar contactos más especializados
