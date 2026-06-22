# Asistente Virtual "Helpdesk Copilot" - Banco de Bogotá 🤖🏦

Este proyecto es un **asistente de soporte técnico interno (Helpdesk Copilot)** diseñado para los funcionarios del Banco de Bogotá. Proporciona respuestas rápidas y contextualizadas basadas en la documentación oficial del banco mediante una arquitectura RAG (Generación Aumentada por Recuperación) y soporta flujos avanzados de asistencia técnica.

---

## 🚀 Arquitectura y Mejoras Clave (Fase 4, 5 y 6)

El asistente ha evolucionado de un chat básico a un copiloto de mesa de ayuda completo con las siguientes innovaciones:

1. **Diagnóstico Interactivo (Quick Replies):**
   * El asistente analiza la consulta y genera opciones en forma de botones dinámicos (ej: `[Boton: Reiniciar Router]`, `[Boton: Verificar IP]`) para guiar paso a paso al usuario en la resolución de problemas técnicos comunes.

2. **Indexación "en Caliente" (Hot Indexing):**
   * Panel de administración `/admin` que permite cargar archivos PDF en tiempo real. El sistema los divide en fragmentos (*chunks*), genera embeddings y los agrega inmediatamente a la base vectorial ChromaDB sin necesidad de reiniciar el servidor.

3. **Soporte Multimodal (OCR Local):**
   * Extracción local de texto en capturas de pantalla o imágenes de error usando **EasyOCR** (CPU-based). El texto extraído se inyecta en el prompt del LLM para dar soporte visual y diagnóstico en tiempo real.

4. **Personalización Dinámica por Roles:**
   * Selector de roles en la barra superior (`General`, `Cajero`, `Director de Oficina`, `Analista TI`). Cada rol altera dinámicamente las instrucciones del sistema, adaptando el tono, las políticas y el nivel de detalle de las respuestas.

5. **Mesa de Ayuda y Gestión de Tickets (Nivel 2):**
   * Integración de un sistema de escalado. Si el asistente no puede resolver el problema o el usuario lo solicita, se genera un ticket de soporte de Nivel 2 que se almacena localmente en SQLite y se visualiza en el panel `/admin`.

---

## 🛠️ Stack Tecnológico

* **Frontend:** React 18 + Vite (diseño moderno con la identidad del Banco de Bogotá).
* **Backend:** FastAPI + LangChain.
* **Procesamiento OCR:** EasyOCR + PyTorch (ejecutado localmente en CPU).
* **Base Vectorial:** ChromaDB con HuggingFace Embeddings locales (`all-MiniLM-L6-v2`).
* **Base de Datos Relacional:** SQLite (para métricas y tickets de soporte).
* **LLM:** Groq API con Llama 3.1 (8B) para respuestas ultra rápidas (< 3 segundos).

---

## 📋 Endpoints de la API Backend

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| **GET** | `/` | Estado y saludo del servicio |
| **GET** | `/health` | Monitoreo del estado del backend |
| **POST** | `/chat` | Consulta síncrona al asistente |
| **POST** | `/chat/stream` | Consulta asíncrona con respuestas en streaming (SSE) |
| **POST** | `/chat/ocr` | Extracción de texto OCR de una imagen y consulta al LLM |
| **POST** | `/admin/upload` | Carga de PDFs e indexación vectorial en tiempo real |
| **GET** | `/metrics` | Estadísticas del dashboard (total chats, resueltos, tickets) |
| **GET** | `/tickets` | Listado de tickets generados para Nivel 2 |
| **POST** | `/tickets` | Creación manual de un ticket de soporte |

---

## 📦 Instalación y Ejecución Local

### Requisitos Previos
* **Python 3.10+**
* **Node.js 18+**

> [!IMPORTANT]
> Los modelos de **EasyOCR** y **PyTorch** se encuentran instalados en el entorno virtual raíz (`.venv`). Asegúrese de iniciar el servidor backend usando este entorno virtual para evitar errores de `ModuleNotFoundError`.

### 1. Servidor Backend (FastAPI)

1. Vaya a la carpeta del proyecto:
   ```bash
   cd asistente-banco
   ```
2. Asegúrese de que el archivo `.env` en la carpeta `backend/` contenga la API Key de Groq:
   ```env
   GROQ_API_KEY=gsk_...
   ```
3. Ejecute el servidor backend usando el entorno virtual raíz:
   ```powershell
   # Desde la raíz del proyecto ("d:\Proyecto Practicas")
   & "d:\Proyecto Practicas\.venv\Scripts\python.exe" -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
4. El backend estará disponible en `http://127.0.0.1:8000`. La documentación interactiva (Swagger) se puede consultar en `http://127.0.0.1:8000/docs`.

### 2. Cliente Frontend (React)

1. Navegue a la carpeta del frontend:
   ```bash
   cd asistente-banco/frontend
   ```
2. Instale las dependencias (si no lo ha hecho):
   ```bash
   npm install
   ```
3. Inicie el servidor de desarrollo:
   ```bash
   npm run dev
   ```
4. Abra su navegador en `http://localhost:5173`.

---

## 📊 Panel de Administración e Ingestión
Ingrese a la ruta `http://localhost:5173/admin` para:
* **Ver Métricas de Uso:** Visualice gráficas de la tasa de resolución del asistente y la cantidad de tickets escalados.
* **Cargar Documentos en Caliente:** Suba manuales en formato PDF. Serán indexados automáticamente en ChromaDB.
* **Mesa de Entrada de Tickets:** Gestione y revise los tickets de soporte técnico de Nivel 2 generados por los usuarios.

---

## 🎓 Guía para la Demo Universitaria
Si está preparando la presentación para el PM o los evaluadores universitarios, revise la guía completa paso a paso en [guia_exposicion.md](file:///C:/Users/josgu/.gemini/antigravity/brain/6d59ba51-a99c-49d5-ba76-8c71afc63926/guia_exposicion.md) para realizar pruebas en vivo y demostraciones de todos los flujos críticos.
