from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import traceback
import json
import os
from pathlib import Path

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

METRICS_FILE = Path("metrics.json")

def cargar_metricas():
    if METRICS_FILE.exists():
        with open(METRICS_FILE, "r") as f:
            return json.load(f)
    return {
        "total_preguntas": 0,
        "preguntas_resueltas": 0,
        "preguntas_escaladas": 0,
        "sesiones_iniciadas": 0,
        "ultima_actualizacion": None
    }

def guardar_metricas(metricas):
    metricas["ultima_actualizacion"] = datetime.now().isoformat()
    with open(METRICS_FILE, "w") as f:
        json.dump(metricas, f, indent=2)

def registrar_interaccion(confianza: bool):
    metricas = cargar_metricas()
    metricas["total_preguntas"] += 1
    if confianza:
        metricas["preguntas_resueltas"] += 1
    else:
        metricas["preguntas_escaladas"] += 1
    guardar_metricas(metricas)

def registrar_sesion():
    metricas = cargar_metricas()
    metricas["sesiones_iniciadas"] += 1
    guardar_metricas(metricas)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)
retriever = db.as_retriever(search_kwargs={"k": 6})
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


class Mensaje(BaseModel):
    rol: str
    texto: str


class Pregunta(BaseModel):
    texto: str
    historial: Optional[List[Mensaje]] = []


def formatear_historial(historial: List[Mensaje]) -> str:
    if not historial:
        return ""
    return "\n\n".join(
        f"{'Usuario' if m.rol == 'usuario' else 'Asistente'}: {m.texto}"
        for m in historial
    )


def formatear_docs(docs):
    return "\n\n".join(f"[Fragmento {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs))


def obtener_fuentes(docs):
    return "Documentación Interna"


def verificar_confianza(docs, contexto):
    if not docs or len(docs) == 0:
        return False
    if not contexto or len(contexto.strip()) < 50:
        return False
    return True


def crear_prompt():
    return ChatPromptTemplate.from_template("""
Eres un asistente experto interno del Banco de Bogota. Respondes preguntas de empleados del banco.

Historial de conversacion:
{historial}

Informacion disponible:
{context}

Reglas estrictas:
- Responde SIEMPRE en espanol
- Ve DIRECTO a la respuesta, sin frases introductorias como "con base en...", "segun los documentos...", "te proporcionare..."
- Jamas menciones que tienes documentos, fragmentos o contexto
- Da respuestas completas y detalladas
- Si hay pasos o procedimientos, listalos numerados
- Si hay requisitos o documentos, mencionalos todos con guiones
- Si no tienes informacion suficiente di simplemente: No tengo informacion sobre ese tema.
- Tono profesional y claro

Pregunta actual: {question}

Respuesta detallada:
""")


@app.get("/", tags=["Info"])
async def root():
    """Estado del servicio."""
    return {"mensaje": "Asistente IA Banco de Bogota funcionando"}


@app.get("/health", tags=["Info"])
async def health():
    """Endpoint de salud para monitoreo."""
    return {"status": "ok"}


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Obtener metricas de uso del asistente."""
    metricas = cargar_metricas()
    total = metricas["total_preguntas"]
    resueltas = metricas["preguntas_resueltas"]
    
    return {
        "total_preguntas": total,
        "preguntas_resueltas": resueltas,
        "preguntas_escaladas": metricas["preguntas_escaladas"],
        "sesiones_iniciadas": metricas["sesiones_iniciadas"],
        "tasa_resolucion": round((resueltas / total * 100), 1) if total > 0 else 0,
        "ultima_actualizacion": metricas["ultima_actualizacion"]
    }


@app.get("/admin", tags=["Admin"])
async def admin_dashboard():
    """Dashboard de metricas para administracion."""
    metricas = cargar_metricas()
    total = metricas["total_preguntas"]
    resueltas = metricas["preguntas_resueltas"]
    escaladas = metricas["preguntas_escaladas"]
    tasa = round((resueltas / total * 100), 1) if total > 0 else 0
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Estadisticas - Banco de Bogota</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #F4F6FA;
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .header {{
                background: linear-gradient(135deg, #0033A0, #002280);
                color: white;
                padding: 30px;
                border-radius: 16px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
            .header p {{ opacity: 0.8; font-size: 14px; }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .card {{
                background: white;
                padding: 24px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            .card .number {{
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .card .label {{
                font-size: 13px;
                color: #6B7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .card.total .number {{ color: #0033A0; }}
            .card.resueltas .number {{ color: #10B981; }}
            .card.escaladas .number {{ color: #F59E0B; }}
            .card.tasa .number {{ color: #0033A0; }}
            .chart-section {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            .chart-title {{
                font-size: 18px;
                font-weight: 600;
                color: #1F2937;
                margin-bottom: 20px;
            }}
            .progress-bar {{
                height: 24px;
                background: #E5E7EB;
                border-radius: 12px;
                overflow: hidden;
                display: flex;
            }}
            .progress-resueltas {{
                background: #10B981;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }}
            .progress-escaladas {{
                background: #F59E0B;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }}
            .legend {{
                display: flex;
                justify-content: center;
                gap: 30px;
                margin-top: 16px;
                font-size: 13px;
            }}
            .legend span {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .legend .dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }}
            .dot.green {{ background: #10B981; }}
            .dot.yellow {{ background: #F59E0B; }}
            .refresh {{
                text-align: center;
                margin-top: 30px;
            }}
            .refresh a {{
                background: #0033A0;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                display: inline-block;
            }}
            .refresh a:hover {{ background: #002280; }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #6B7280;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Banco de Bogota</h1>
                <p>Panel de Estadisticas - Asistente Virtual</p>
            </div>
            
            <div class="grid">
                <div class="card total">
                    <div class="number">{total}</div>
                    <div class="label">Total Preguntas</div>
                </div>
                <div class="card resueltas">
                    <div class="number">{resueltas}</div>
                    <div class="label">Resueltas</div>
                </div>
                <div class="card escaladas">
                    <div class="number">{escaladas}</div>
                    <div class="label">Escaladas</div>
                </div>
                <div class="card tasa">
                    <div class="number">{tasa}%</div>
                    <div class="label">Tasa Resolucion</div>
                </div>
            </div>
            
            <div class="chart-section">
                <div class="chart-title">Distribucion de Preguntas</div>
                <div class="progress-bar">
                    <div class="progress-resueltas" style="width: {tasa}%">{tasa}%</div>
                    <div class="progress-escaladas" style="width: {100-tasa}%">{100-tasa}%</div>
                </div>
                <div class="legend">
                    <span><div class="dot green"></div> Resueltas por IA</span>
                    <span><div class="dot yellow"></div> Escaladas a humanos</span>
                </div>
            </div>
            
            <div class="refresh">
                <a href="/admin">Actualizar</a>
            </div>
            
            <div class="footer">
                Ultima actualizacion: {metricas.get('ultima_actualizacion', 'N/A')}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/metrics/reset", tags=["Metrics"])
async def reset_metrics():
    """Reiniciar metricas (solo para testing)."""
    guardar_metricas({
        "total_preguntas": 0,
        "preguntas_resueltas": 0,
        "preguntas_escaladas": 0,
        "sesiones_iniciadas": 0,
        "ultima_actualizacion": datetime.now().isoformat()
    })
    return {"mensaje": "Metricas reiniciadas"}


@app.post("/chat", tags=["Chat"], summary="Enviar pregunta (respuesta completa)")
@limiter.limit("20/minute")
async def chat(request: Request, p: Pregunta):
    """
    Envía una pregunta al asistente y recibe una respuesta completa.
    
    - **texto**: La pregunta del usuario
    - **historial**: Lista de mensajes anteriores (opcional)
    
    Retorna la respuesta junto con fuentes y nivel de confianza.
    """
    try:
        docs = retriever.invoke(p.texto)
        fuentes = obtener_fuentes(docs)
        contexto = formatear_docs(docs)
        historial = formatear_historial(p.historial or [])
        confianza = verificar_confianza(docs, contexto)
        
        prompt = crear_prompt()
        cadena = prompt | llm | StrOutputParser()
        
        respuesta = cadena.invoke({
            "context": contexto,
            "historial": historial if historial else "Sin historial previo.",
            "question": p.texto
        })
        
        registrar_interaccion(confianza)
        
        return {
            "respuesta": respuesta,
            "fuentes": fuentes,
            "confianza": confianza
        }
    except Exception as e:
        print("ERROR DETALLADO:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream", tags=["Chat"], summary="Enviar pregunta (streaming)")
@limiter.limit("20/minute")
async def chat_stream(request: Request, p: Pregunta):
    """
    Envía una pregunta y recibe la respuesta en streaming (SSE).
    
    - **texto**: La pregunta del usuario
    - **historial**: Lista de mensajes anteriores (opcional)
    
    Retorna eventos SSE con: fuentes, confianza, chunks de texto, y fin.
    """
    confianza_registrada = False
    
    async def generate():
        nonlocal confianza_registrada
        try:
            docs = retriever.invoke(p.texto)
            fuentes = obtener_fuentes(docs)
            contexto = formatear_docs(docs)
            historial = formatear_historial(p.historial or [])
            confianza = verificar_confianza(docs, contexto)
            
            yield f"data: {json.dumps({'tipo': 'fuentes', 'valor': fuentes})}\n\n"
            yield f"data: {json.dumps({'tipo': 'confianza', 'valor': confianza})}\n\n"
            
            prompt = crear_prompt()
            cadena = prompt | llm | StrOutputParser()
            
            async for chunk in cadena.astream({
                "context": contexto,
                "historial": historial if historial else "Sin historial previo.",
                "question": p.texto
            }):
                yield f"data: {json.dumps({'tipo': 'chunk', 'valor': chunk})}\n\n"
            
            yield f"data: {json.dumps({'tipo': 'fin'})}\n\n"
            
            if not confianza_registrada:
                registrar_interaccion(confianza)
                confianza_registrada = True
            
        except Exception as e:
            yield f"data: {json.dumps({'tipo': 'error', 'valor': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
