from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional, List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import traceback
import json

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
    async def generate():
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
            
        except Exception as e:
            yield f"data: {json.dumps({'tipo': 'error', 'valor': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
