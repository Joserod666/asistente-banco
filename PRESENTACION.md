# Presentación Técnica - Asistente Virtual "Helpdesk Copilot" RAG
## Banco de Bogotá

---

## 1. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                      USUARIO FINAL                          │
│         (Cajero, Asesor, Director, Analista TI)             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  • Vista Híbrida: Widget flotante / Pantalla completa       │
│  • Selector de Roles (General, Cajero, Director, TI)        │
│  • Diagnóstico Interactivo (Botones Rápidos)                │
│  • Carga de Imagen para Soporte OCR                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS (JSON / Multipart / SSE Streams)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                          │
│  • Pipeline RAG con LangChain                               │
│  • Rate Limiting dinámico por IP (20 req/min)               │
│  • Procesador OCR con EasyOCR local                         │
│  • Ingestor en Caliente para PDFs                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┼───────────┬───────────┐
          ▼           ▼           ▼           ▼
 ┌───────────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐
 │   CHROMADB    │ │   GROQ   │ │  SQLITE  │ │  DOCUMENTOS   │
 │ Base Vectorial│ │ (Llama   │ │ Base de  │ │ Almacén local │
 │ Embeddings HF │ │ 3.1 8B)  │ │ Tickets  │ │ de manuales   │
 └───────────────┘ └──────────┘ └──────────┘ └───────────────┘
```

---

## 2. STACK TECNOLÓGICO

| Componente | Tecnología | Ventaja / Rol |
| :--- | :--- | :--- |
| **Frontend** | React 18 + Vite | Carga ultra rápida (<1s), interfaz reactiva con CSS vanilla premium. |
| **Backend** | FastAPI | Framework asíncrono de alto rendimiento con autodocumentación interactiva. |
| **Base Vectorial** | ChromaDB | Almacenamiento local de embeddings semánticos para búsquedas ultrarrápidas. |
| **Embeddings** | HuggingFace (`all-MiniLM-L6-v2`) | Modelos de vectores locales y gratuitos (ejecución offline). |
| **OCR local** | EasyOCR + PyTorch | Extracción de texto de capturas de pantalla de errores sin salir del host. |
| **Base de Datos** | SQLite | Base de datos relacional integrada para auditoría de tickets de soporte. |
| **LLM** | Groq (Llama 3.1 8B) | Inferencia ultra rápida (< 3 segundos) con respuestas de nivel humano. |

---

## 3. COMPONENTES Y FLUJOS PRINCIPALES

### 3.1 Pipeline RAG Multimodal con OCR

```
  Captura de Pantalla (Frontend)
             │
             ▼
      [ POST /chat/ocr ]
             │
      ┌──────┴──────┐
      ▼             ▼
┌───────────┐ ┌───────────┐
│  EasyOCR  │ │ EMBEDDINGS│ → Convierte texto de consulta a vector
│  (Local)  │ │  (Local)  │
└─────┬─────┘ └─────┬─────┘
      │             │
      │ Extrae      ▼
      │ error  ┌───────────┐
      │ texto  │ CHROMADB  │ → Recupera fragmentos de manuales (k=6)
      ▼        └─────┬─────┘
┌────────────────────┴──────┐
│       COMBINADOR DE       │ → Inyecta: Prompt por Rol + Contexto PDF
│          CONTEXTO         │   + Historial de chat + Texto del OCR
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│     GROQ LLM (STREAM)     │ → Genera respuesta con streaming en vivo
└───────────────────────────┘
```

### 3.2 Ingestión "en Caliente" (Hot Indexing)
* **Antes:** Se requería ejecutar scripts offline para recrear la base vectorial.
* **Ahora:** Un administrador sube un PDF a través de `/admin`, y el backend ejecuta el pipeline (Splitter -> Embeddings -> ChromaDB insertion) en caliente, estando disponible para consultas inmediatamente.

### 3.3 Diagnóstico Interactivo (Quick Replies)
* El LLM genera guías técnicas estructuradas que el frontend convierte en botones dinámicos (ej: `[Boton: Sí, continuar]`). Esto permite crear árboles de decisión automatizados de manera interactiva.

---

## 4. FUNCIONALIDADES CLAVE IMPLEMENTADAS

### 4.1 Chat Inteligente & Multimodal
* ✅ Respuestas en streaming palabra por palabra.
* ✅ Carga de imágenes con diagnóstico OCR.
* ✅ Historial conversacional completo.

### 4.2 Soporte de Nivel 2 (Mesa de Ayuda)
* ✅ Detección automática de insolubilidad.
* ✅ Botón para escalado a especialista humano.
* ✅ Persistencia de tickets de soporte en SQLite.

### 4.3 Control de Roles y Contexto
* ✅ Prompt personalizado según el rol seleccionado (`General`, `Cajero`, `Director de Oficina`, `Analista TI`).
* ✅ Restricciones de seguridad para evitar fugas de información.

### 4.4 Dashboard de Control Administrativo
* ✅ Gráficas de volumen y tasa de resolución (ROI).
* ✅ Visualizador y gestor de tickets en cola.
* ✅ Panel para carga e indexación en vivo de PDFs.

---

## 5. MÉTRICAS DE RENDIMIENTO

| Métrica | Valor | Objetivo |
| :--- | :--- | :--- |
| **Tiempo de Inferencia Inicial** | < 1.2 segundos | < 3.0 segundos |
| **Tamaño de Bundle Frontend** | 205 KB | Mínima latencia de carga |
| **Precisión de Búsqueda Semántica** | > 85% de similitud | Minimizar falsos positivos |
| **Tasa de Resolución Estimada** | 80% de consultas directas | Reducir carga de Nivel 1 |

---

## 6. SEGURIDAD Y CONTROL

* **Rate Limiting:** Control de concurrencia y prevención de abusos (20 peticiones por minuto por IP).
* **Robustez ante Caídas:** Si la API de Groq o el OCR fallan, el sistema captura el error y sugiere al usuario generar un ticket directamente, evitando que la interfaz se congele.
* **Privacidad de Datos:** Almacenamiento local de manuales y tickets. Los nombres de archivos internos no se exponen al cliente final.

---

## 7. MANTENIMIENTO Y OPERACIÓN

### Actualización de Manuales
1. **Vía Panel UI:** Cargar en `/admin` (Indexación en caliente).
2. **Vía Script CLI:**
   ```bash
   python backend/cargar_docs.py
   ```

### Monitoreo de Tickets
* Acceder a `http://localhost:5173/admin` para revisar el buzón de incidencias de Nivel 2 escaladas por los funcionarios.

---

¿Preguntas sobre la implementación o la arquitectura del Copilot?
