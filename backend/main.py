from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import traceback

load_dotenv()

app = FastAPI()
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

prompt = ChatPromptTemplate.from_template("""
Eres un asistente experto interno del Banco de Bogota. Respondes preguntas de empleados del banco.

Reglas estrictas:
- Responde SIEMPRE en espanol
- Ve DIRECTO a la respuesta, sin frases introductorias como "con base en...", "segun los documentos...", "te proporcionare..."
- Jamas menciones que tienes documentos, fragmentos o contexto
- Da respuestas completas y detalladas
- Si hay pasos o procedimientos, listalos numerados
- Si hay requisitos o documentos, mencionalos todos con guiones
- Si no tienes informacion suficiente di simplemente: No tengo informacion sobre ese tema.
- Tono profesional y claro

Informacion disponible:
{context}

Pregunta: {question}


Respuesta detallada:
""")

def formatear_docs(docs):
    return "\n\n".join(f"[Fragmento {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs))

def obtener_fuentes(docs):
    fuentes = list(set(doc.metadata.get("fuente", "Documento interno") for doc in docs))
    return ", ".join(fuentes)

cadena = (
    {"context": retriever | formatear_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

class Pregunta(BaseModel):
    texto: str

@app.post("/chat")
async def chat(p: Pregunta):
    try:
        docs = retriever.invoke(p.texto)
        fuentes = obtener_fuentes(docs)
        respuesta = cadena.invoke(p.texto)
        return {
            "respuesta": respuesta,
            "fuentes": fuentes
        }
    except Exception as e:
        print("ERROR DETALLADO:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"mensaje": "Asistente IA Banco de Bogota funcionando"}
