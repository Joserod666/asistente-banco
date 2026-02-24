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
retriever = db.as_retriever(search_kwargs={"k": 3})
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

prompt = ChatPromptTemplate.from_template("""
Eres un asistente interno del banco. Responde en espanol
basandote unicamente en el siguiente contexto.
Si no encuentras la respuesta di: No tengo informacion sobre ese tema.

Contexto:
{context}

Pregunta: {question}
""")

def formatear_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

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
        respuesta = cadena.invoke(p.texto)
        return {"respuesta": respuesta}
    except Exception as e:
        print("ERROR DETALLADO:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"mensaje": "Asistente IA Bancario funcionando"}
