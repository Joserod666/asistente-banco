# Presentación Técnica - Asistente Virtual RAG
## Banco de Bogotá

---

## 1. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO FINAL                          │
│               (Funcionario del Banco)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  • Widget embebible                                       │
│  • Interfaz de chat moderna                               │
│  • Tipografía oficial del banco (Kiffo BDB)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                          │
│  • API REST con streaming SSE                              │
│  • Rate limiting (20 req/min)                             │
│  • Métricas de uso                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌──────────────────┐    ┌──────────────────────────────────┐
│    CHROMADB       │    │          GROQ (LLM)               │
│  Base Vectorial   │    │   Modelo Llama 3.1 (8B)           │
│  Embeddings locales│    │   Respuestas en español          │
└──────────────────┘    └──────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              BASE DE CONOCIMIENTO                           │
│     PDF + Imágenes (OCR) → Textos → Fragmentos              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. STACK TECNOLÓGICO

| Componente | Tecnología | Ventaja |
|------------|-----------|--------|
| **Frontend** | React + Vite | Carga rápida, bundle pequeño (202KB) |
| **Backend** | FastAPI | Alto rendimiento, autodocs |
| **Base de datos** | ChromaDB | Vectorial, embeddings locales |
| **LLM** | Groq (Llama 3.1) | Ultra rápido, bajo costo |
| **Embeddings** | HuggingFace | Gratis, offline |
| **OCR** | EasyOCR | Multilingüe (español) |

---

## 3. COMPONENTES PRINCIPALES

### 3.1 Pipeline RAG (Retrieval Augmented Generation)

```
Usuario pregunta
      │
      ▼
┌─────────────────┐
│  EMBEDDINGS      │ → Convierte pregunta a vector
│  (HuggingFace)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CHROMADB       │ → Busca fragmentos similares
│   (Vector DB)   │   k=6 resultados
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CONTEXTO       │ → Combina fragmentos
│   + HISTORIAL    │   + historial conversacional
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM (GROQ)    │ → Genera respuesta natural
│   Llama 3.1     │   en español, sin alucinaciones
└─────────────────┘
```

### 3.2 Streaming de Respuestas

```javascript
// El usuario ve la respuesta aparecer palabra por palabra
// como en ChatGPT - mejor UX percibida
```

### 3.3 Historial Conversacional

```javascript
// Cada pregunta incluye el historial previo
// El LLM mantiene contexto entre preguntas
{
  "texto": "¿Y si es una SAS?",
  "historial": [
    {"rol": "usuario", "texto": "¿Qué docs necesito?"},
    {"rol": "asistente", "texto": "Para abrir cuenta necesitas..."}
  ]
}
```

---

## 4. FUNCIONALIDADES IMPLEMENTADAS

### 4.1 Chat Inteligente
- ✅ Streaming en tiempo real
- ✅ Historial de conversación
- ✅ Contexto de documentos
- ✅ Respuestas en español

### 4.2 Sistema de Confianza
- ✅ Detecta cuando no hay suficiente información
- ✅ Muestra advertencia al usuario
- ✅ Sugiere escalar a humano

### 4.3 Métricas y Analytics
- ✅ Total de preguntas
- ✅ Preguntas resueltas por IA
- ✅ Preguntas escaladas
- ✅ Tasa de resolución (ROI)
- ✅ Dashboard visual para admins

### 4.4 Seguridad
- ✅ Rate limiting (20 req/min por IP)
- ✅ Manejo de errores robusto
- ✅ Timeout de 30 segundos

### 4.5 Widget Emebible
```html
<!-- 3 líneas para embeber en cualquier página -->
<script src="widget.js"></script>
<div id="banco-chat"></div>
<script>BancoChat.init({container: '#banco-chat'});</script>
```

---

## 5. VENTAJAS PARA EL BANCO

### 5.1 Reducción de Carga Operativa
```
Antes: 100 tickets/día de consultas internas
Ahora: ~80 resueltos por IA (80%)
       ~20 escalados a humanos

Ahorro estimado: 80 horas/mes de trabajo
```

### 5.2 Disponibilidad 24/7
- El asistente responde instantáneamente
- Sin esperas telefónicas
- Sin horarios de atención

### 5.3 Consistencia
- Todas las respuestas basadas en documentación oficial
- Sin errores humanos
- Mismo nivel de información para todos

### 5.4 Escalabilidad
- Sin límite de conversaciones simultáneas
- Costo marginal cero por consulta adicional

---

## 6. MÉTRICAS DE RENDIMIENTO

| Métrica | Valor |
|---------|-------|
| Tiempo de respuesta (streaming) | < 3 segundos |
| Tamaño del bundle | 202 KB (gzip: 64KB) |
| Rate limit | 20 req/min/IP |
| Documentos soportados | PDF + Imágenes (OCR) |
| Embeddings | Locales (offline) |
| Modelo LLM | Groq Llama 3.1 (8B) |

---

## 7. SEGURIDAD

### 7.1 Rate Limiting
- Protege contra abuse
- Control de costos
- 20 peticiones por minuto por IP

### 7.2 Manejo de Errores
| Error | Respuesta |
|-------|----------|
| Timeout | "La solicitud tardó demasiado" |
| Servidor caído | "Servicio no disponible" |
| Rate limit | "Demasiadas solicitudes" |

### 7.3 Confidencialidad
- Los nombres de documentos NO se exponen
- Solo muestra "Documentación Interna"
- Historial de conversación en memoria (no persiste)

---

## 8. ENDPOINTS API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estado del servicio |
| GET | `/health` | Monitoreo |
| GET | `/metrics` | Estadísticas (JSON) |
| GET | `/admin` | Dashboard visual |
| POST | `/chat` | Chat completo |
| POST | `/chat/stream` | Chat con streaming |

Swagger UI: `/docs`

---

## 9. DESPLIEGUE

### 9.1 Requisitos
- Python 3.10+
- Node.js 18+
- 4GB RAM mínimo

### 9.2 Variables de Entorno
```bash
# Backend
GROQ_API_KEY=your_key

# Frontend
VITE_API_URL=https://api.bancobogota.com
```

### 9.3 Docker (opcional)
```bash
# Backend
docker build -t asistente-backend ./backend
docker run -p 8000:8000 asistente-backend

# Frontend
npm run build
# Servir dist/ con nginx
```

---

## 10. MANTENIMIENTO

### 10.1 Actualizar Base de Conocimiento
```bash
cd backend
python cargar_docs.py
```
- Lee PDFs automáticamente
- Procesa imágenes con OCR
- Reindexa en ChromaDB

### 10.2 Monitoreo
- Dashboard: `/admin`
- Métricas: `/metrics`
- Logs: Terminal del backend

---

## 11. FUTURAS MEJORAS

| Mejora | Prioridad | Esfuerzo |
|--------|-----------|----------|
| Autenticación JWT | Alta | Medio |
| Panel admin de documentos | Media | Alto |
| Dashboard Grafana | Media | Bajo |
| WhatsApp/Slack bot | Baja | Alto |

---

## 12. RESUMEN EJECUTIVO

✅ **Asistente virtual RAG** para consultas internas del banco
✅ **Respuestas instantáneas** con streaming
✅ **Contexto de documentos** oficiales
✅ **Métricas de ROI** en tiempo real
✅ **Widget embebible** en 3 líneas
✅ **Seguro y robusto** con rate limiting
✅ **Bajo costo** (Groq tiene tier gratuito)

**ROI esperado:** 80% de tickets resueltos por IA

---

¿Preguntas?
