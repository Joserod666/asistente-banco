from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import shutil

CARPETA_DOCS = "../documentos"
CARPETA_DB = "chroma_db"

# Limpiar la base de datos anterior
if os.path.exists(CARPETA_DB):
    shutil.rmtree(CARPETA_DB)
    print("Base de datos anterior eliminada")

# Cargar todos los PDFs
documentos = []
pdfs_encontrados = 0

for archivo in os.listdir(CARPETA_DOCS):
    if archivo.endswith(".pdf"):
        ruta = os.path.join(CARPETA_DOCS, archivo)
        print(f"Cargando: {archivo}")
        loader = PyPDFLoader(ruta)
        docs = loader.load()
        for doc in docs:
            doc.metadata["fuente"] = archivo
        documentos.extend(docs)
        pdfs_encontrados += 1

if pdfs_encontrados == 0:
    print("No se encontraron PDFs en la carpeta documentos/")
    exit()

print(f"\nTotal PDFs cargados: {pdfs_encontrados}")
print(f"Total paginas: {len(documentos)}")

# Dividir en fragmentos
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
fragmentos = splitter.split_documents(documentos)
print(f"Total fragmentos: {len(fragmentos)}")

# Crear embeddings y guardar en ChromaDB
print("\nCreando base de conocimiento, esto puede tardar unos minutos...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
db = Chroma.from_documents(
    fragmentos,
    embeddings,
    persist_directory=CARPETA_DB
)

print(f"\nBase de conocimiento creada exitosamente")
print(f"Total fragmentos indexados: {len(fragmentos)}")
