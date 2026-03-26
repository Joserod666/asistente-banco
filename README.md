# Asistente Virtual - Banco de Bogotá

Asistente interno con IA para consultas sobre procesos, documentación y procedimientos del banco.

## Stack Tecnológico

- **Frontend**: React + Vite
- **Backend**: FastAPI + LangChain
- **Base de conocimiento**: ChromaDB + HuggingFace Embeddings
- **LLM**: Groq (Llama 3.1)

## Instalación

### Backend

```bash
cd asistente-banco/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend

```bash
cd asistente-banco/frontend
npm install
npm run dev
```

## Variables de Entorno

### Backend (`backend/.env`)
```
GROQ_API_KEY=tu_key_de_groq
```

### Frontend (`frontend/.env`)
```
VITE_API_URL=http://localhost:8000
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Estado del servicio |
| GET | `/health` | Monitoreo |
| POST | `/chat` | Chat (respuesta completa) |
| POST | `/chat/stream` | Chat (streaming SSE) |

### Ejemplo de uso

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"texto": "¿Qué es SARLAFT?"}'
```

## Despliegue

### Build producción

```bash
cd asistente-banco/frontend
npm run build
```

Los archivos optimizados están en `dist/`.

### Embeber como widget

```html
<script src="https://tu-dominio.com/widget.js"></script>
<div id="banco-chat"></div>
<script>
  BancoChat.init({
    container: '#banco-chat',
    apiUrl: 'https://tu-api.com'
  });
</script>
```

## Pruebas

```bash
cd asistente-banco/backend
python test_api.py
```

## Documentación API

Swagger UI disponible en: `http://localhost:8000/docs`

## Rate Limiting

- Límite: 20 peticiones por minuto por IP
- Al exceder: código 429

## Cargar documentos

```bash
cd asistente-banco/backend
python cargar_docs.py
```
