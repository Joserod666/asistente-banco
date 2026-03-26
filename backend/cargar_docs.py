import os
import shutil
import easyocr
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CARPETA_DOCS = "../documentos"
CARPETA_DB = "chroma_db"

print("=" * 60)
print("CARGADOR DE DOCUMENTOS - Banco de Bogota")
print("=" * 60)

if os.path.exists(CARPETA_DB):
    shutil.rmtree(CARPETA_DB)
    print("Base de datos anterior eliminada")

documentos = []
pdfs_encontrados = 0
imagenes_encontradas = 0

print("\nInicializando OCR (solo la primera vez)...")
reader = easyocr.Reader(['es', 'en'], gpu=False)

for archivo in os.listdir(CARPETA_DOCS):
    ruta = os.path.join(CARPETA_DOCS, archivo)
    
    if archivo.endswith(".pdf"):
        try:
            from langchain_community.document_loaders import PyPDFLoader
            print(f"Cargando PDF: {archivo}")
            loader = PyPDFLoader(ruta)
            docs = loader.load()
            for doc in docs:
                doc.metadata["fuente"] = archivo
                doc.metadata["tipo"] = "pdf"
            documentos.extend(docs)
            pdfs_encontrados += 1
        except Exception as e:
            print(f"  Error con {archivo}: {e}")
    
    elif archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        try:
            print(f"Procesando imagen: {archivo}")
            resultados = reader.readtext(ruta)
            texto = "\n".join([r[1] for r in resultados if r[2] > 0.3])
            
            if texto.strip():
                doc = Document(
                    page_content=texto.strip(),
                    metadata={"fuente": archivo, "tipo": "imagen"}
                )
                documentos.append(doc)
                print(f"  Texto extraido: {len(texto)} caracteres")
            else:
                print(f"  No se encontro texto en la imagen")
            imagenes_encontradas += 1
        except Exception as e:
            print(f"  Error con {archivo}: {e}")

print(f"\n--- Resumen ---")
print(f"PDFs procesados: {pdfs_encontrados}")
print(f"Imagenes procesadas: {imagenes_encontradas}")
print(f"Total paginas/documentos: {len(documentos)}")

if len(documentos) == 0:
    print("\nNo se encontraron documentos para procesar.")
    exit()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
fragmentos = splitter.split_documents(documentos)
print(f"Total fragmentos creados: {len(fragmentos)}")

print("\nCreando embeddings (esto puede tardar unos minutos)...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma.from_documents(
    fragmentos,
    embeddings,
    persist_directory=CARPETA_DB
)

print(f"\nBase de conocimiento creada exitosamente!")
print(f"Total fragmentos indexados: {len(fragmentos)}")
