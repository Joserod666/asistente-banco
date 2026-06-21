from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
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

import db

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
            try:
                data = json.load(f)
                # Garantizar que todas las llaves existan
                for key in ["total_preguntas", "preguntas_resueltas", "preguntas_escaladas", "sesiones_iniciadas"]:
                    if key not in data:
                        data[key] = 0
                if "tickets_creados" not in data:
                    data["tickets_creados"] = 0
                return data
            except Exception:
                pass
    return {
        "total_preguntas": 0,
        "preguntas_resueltas": 0,
        "preguntas_escaladas": 0,
        "sesiones_iniciadas": 0,
        "tickets_creados": 0,
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

def registrar_ticket():
    metricas = cargar_metricas()
    metricas["tickets_creados"] = metricas.get("tickets_creados", 0) + 1
    guardar_metricas(metricas)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vector_db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)
retriever = vector_db.as_retriever(search_kwargs={"k": 6})
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


class Mensaje(BaseModel):
    rol: str
    texto: str


class Pregunta(BaseModel):
    texto: str
    historial: Optional[List[Mensaje]] = []
    categoria: Optional[str] = None
    rol: Optional[str] = "General"


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
    if not docs:
        return "Documentación Interna"
    fuentes = set()
    for doc in docs:
        fuente = doc.metadata.get("fuente")
        if fuente:
            fuentes.add(fuente)
    if fuentes:
        return ", ".join(sorted(fuentes))
    return "Documentación Interna"


def verificar_confianza(docs_and_scores, contexto):
    if not docs_and_scores or len(docs_and_scores) == 0:
        return False
    # docs_and_scores es una lista de tuplas (Document, score)
    # Chroma retorna la distancia L2. Menor distancia = mayor similitud.
    # Un score >= 0.80 indica baja similitud semántica.
    best_doc, best_score = docs_and_scores[0]
    if best_score >= 0.80:
        return False
    if not contexto or len(contexto.strip()) < 50:
        return False
    return True


def crear_prompt(rol: str = "General"):
    instrucciones_rol = ""
    if rol == "Cajero":
        instrucciones_rol = """
- Tu rol es atender a un Cajero de Oficina. Prioriza respuestas extremadamente agiles, precisas y detalladas sobre procedimientos de caja, arqueos, manejo de efectivo, seguridad fisica, limites de transacciones y boveda.
- Si hay dudas sobre un proceso operativo de caja, guialo de forma secuencial y recalca las medidas de control.
"""
    elif rol == "Director de Oficina":
        instrucciones_rol = """
- Tu rol es atender a un Director de Oficina. Prioriza directrices de cumplimiento normativo (SARLAFT), politicas de riesgo comercial, limites de autorizacion de excepciones, firmas de gerencia, escalamientos organizativos y control comercial.
- Tu lenguaje debe ser ejecutivo, formal y enfocado en la toma de decisiones y gobernanza.
"""
    elif rol == "Analista TI":
        instrucciones_rol = """
- Tu rol es atender a un Analista de Soporte TI. Proporciona detalles tecnicos profundos: mencione requisitos de sistema, puertos, configuraciones de red (intranet, VPN, proxy), codigos de error especificos de bases de datos e infraestructura, y pasos detallados de resolucion de problemas de software.
- Puedes utilizar terminos tecnicos apropiados de soporte de sistemas.
"""
    else:
        instrucciones_rol = """
- Tu rol es atender a un empleado general del Banco de Bogotá. Responde con un tono profesional, claro y equilibrado sobre cualquier norma o tramite general.
"""

    instrucciones_botones = """
- Diagnostico Interactivo (Quick Replies): Cuando sea posible guiar al usuario a traves de un proceso de descarte o cuando existan alternativas claras en el manual, incluye SIEMPRE al final de tu respuesta de 2 a 4 botones interactivos usando el formato exacto `[Boton: Texto de la opcion]` (ej. `[Boton: Red Oficina]` o `[Boton: Red VPN]`) para que el usuario pueda responder con un clic.
"""

    return ChatPromptTemplate.from_template(f"""
Eres un asistente experto interno del Banco de Bogota. Respondes preguntas de empleados del banco.

{instrucciones_rol}
{instrucciones_botones}

Historial de conversacion:
{{historial}}

Informacion disponible:
{{context}}

Reglas estrictas:
- Responde SIEMPRE en espanol
- Ve DIRECTO a la respuesta, sin frases introductorias como "con base en...", "segun los documentos...", "te proporcionare..."
- Jamas menciones que tienes documentos, fragmentos o contexto
- Da respuestas completas y detalladas
- Si hay pasos o procedimientos, listalos numerados
- Si hay requisitos o documentos, mencionalos todos con guiones
- Si no tienes informacion suficiente di simplemente: No tengo informacion sobre ese tema.
- Tono profesional y claro

Pregunta actual: {{question}}

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
        "tickets_creados": metricas.get("tickets_creados", 0),
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
    tickets_creados = metricas.get("tickets_creados", 0)
    tasa = round((resueltas / total * 100), 1) if total > 0 else 0
    
    tickets = db.get_tickets()
    tickets_rows = ""
    if not tickets:
        tickets_rows = """
        <tr>
            <td colspan="6" style="text-align: center; color: #6B7280; padding: 30px; font-size: 14px;">
                No hay tickets de soporte creados.
            </td>
        </tr>
        """
    else:
        for t in tickets:
            fecha_str = t["fecha"]
            try:
                dt = datetime.fromisoformat(fecha_str)
                fecha_formateada = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                fecha_formateada = fecha_str
                
            cat_lower = t["categoria"].lower()
            if "acceso" in cat_lower:
                cat_style = "background: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5;"
            elif "soporte" in cat_lower or "tecnico" in cat_lower or "técnico" in cat_lower:
                cat_style = "background: #DBEAFE; color: #3B82F6; border: 1px solid #BFDBFE;"
            elif "normas" in cat_lower or "proceso" in cat_lower:
                cat_style = "background: #F3E8FF; color: #8B5CF6; border: 1px solid #E9D5FF;"
            else:
                cat_style = "background: #F3F4F6; color: #4B5563; border: 1px solid #E5E7EB;"
                
            tickets_rows += f"""
            <tr>
                <td style="padding: 12px 16px; font-weight: 600; color: #0033A0; border-bottom: 1px solid #E5E7EB;">#{t["id"]}</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB;">
                    <span style="display: inline-block; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; {cat_style}">
                        {t["categoria"]}
                    </span>
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; color: #1F2937; font-size: 13px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{t["descripcion"]}">
                    {t["descripcion"]}
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-size: 12px; color: #6B7280;">{fecha_formateada}</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-size: 11px; color: #9CA3AF; font-family: monospace;" title="{t["session_id"]}">{t["session_id"][:15]}...</td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB;">
                    <span style="display: inline-block; padding: 4px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0;">
                        {t["estado"]}
                    </span>
                </td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel de Estadísticas - Banco de Bogotá</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                background: #F4F6FA;
                min-height: 100vh;
                padding: 40px 20px;
                color: #1F2937;
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{
                background: linear-gradient(135deg, #0033A0, #002280);
                color: white;
                padding: 30px;
                border-radius: 16px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 51, 160, 0.15);
            }}
            .header h1 {{ font-size: 28px; margin-bottom: 8px; font-weight: 700; }}
            .header p {{ opacity: 0.8; font-size: 14px; }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 16px;
                margin-bottom: 30px;
            }}
            @media (max-width: 900px) {{
                .grid {{ grid-template-columns: repeat(3, 1fr); }}
            }}
            @media (max-width: 600px) {{
                .grid {{ grid-template-columns: repeat(2, 1fr); }}
            }}
            .card {{
                background: white;
                padding: 20px 16px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border: 1px solid #E5E7EB;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            .card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }}
            .card .number {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 6px;
            }}
            .card .label {{
                font-size: 11px;
                color: #6B7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
            }}
            .card.total .number {{ color: #0033A0; }}
            .card.resueltas .number {{ color: #10B981; }}
            .card.escaladas .number {{ color: #F59E0B; }}
            .card.tickets-creados .number {{ color: #EF4444; }}
            .card.tasa .number {{ color: #0033A0; }}
            
            .dashboard-section {{
                background: white;
                padding: 26px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border: 1px solid #E5E7EB;
                margin-bottom: 30px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                color: #1F2937;
                margin-bottom: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
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
            
            .table-container {{
                overflow-x: auto;
                width: 100%;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }}
            th {{
                background: #F9FAFB;
                padding: 12px 16px;
                font-size: 11px;
                text-transform: uppercase;
                color: #6B7280;
                font-weight: 600;
                border-bottom: 2px solid #E5E7EB;
            }}
            tr:hover {{
                background: #F9FAFB;
            }}
            
            .refresh {{
                text-align: center;
                margin-top: 10px;
            }}
            .refresh a {{
                background: #0033A0;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                display: inline-block;
                transition: background 0.2s;
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
                <h1>Banco de Bogotá</h1>
                <p>Panel de Estadísticas - Asistente Virtual de Soporte</p>
            </div>
            
            <div class="grid">
                <div class="card total">
                    <div class="number">{total}</div>
                    <div class="label">Total Consultas</div>
                </div>
                <div class="card resueltas">
                    <div class="number">{resueltas}</div>
                    <div class="label">Resueltas por IA</div>
                </div>
                <div class="card escaladas">
                    <div class="number">{escaladas}</div>
                    <div class="label">Baja Confianza</div>
                </div>
                <div class="card tickets-creados">
                    <div class="number">{tickets_creados}</div>
                    <div class="label">Tickets Creados</div>
                </div>
                <div class="card tasa">
                    <div class="number">{tasa}%</div>
                    <div class="label">Tasa Resolución</div>
                </div>
            </div>
            
            <div class="dashboard-section">
                <div class="section-title">Distribución de Consultas</div>
                <div class="progress-bar">
                    <div class="progress-resueltas" style="width: {tasa}%">{tasa}%</div>
                    <div class="progress-escaladas" style="width: {100-tasa}%">{100-tasa}%</div>
                </div>
                <div class="legend">
                    <span><div class="dot green"></div> Resueltas por IA</span>
                    <span><div class="dot yellow"></div> Baja Confianza (Sugerencia Escalado)</span>
                </div>
            </div>

            <!-- Hot Indexing Section -->
            <div class="dashboard-section" style="border-left: 4px solid #0033A0;">
                <div class="section-title" style="color: #0033A0;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                    Indexación de Documentos "en Caliente" (Carga Rápida PDF)
                </div>
                <form action="/admin/upload" method="post" enctype="multipart/form-data" style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 10px;">
                    <div style="flex: 1; min-width: 250px;">
                        <input type="file" name="file" accept=".pdf" required style="width: 100%; padding: 10px; border: 1px solid #D1D5DB; border-radius: 8px; font-size: 14px; background: #F9FAFB;" />
                    </div>
                    <button type="submit" style="background: #0033A0; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; transition: background 0.2s;">
                        Subir e Indexar PDF
                    </button>
                </form>
                <div id="alert-container" style="margin-top: 12px; display: none;"></div>
            </div>

            <div class="dashboard-section">
                <div class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #0033A0;">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    Tickets de Soporte Escalados (Nivel 2)
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Ticket</th>
                                <th>Categoría</th>
                                <th>Descripción</th>
                                <th>Fecha Creación</th>
                                <th>ID Sesión</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tickets_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="refresh">
                <a href="/admin">Actualizar Panel</a>
            </div>
            
            <div class="footer">
                Última actualización: {metricas.get('ultima_actualizacion', 'N/A')}
            </div>
        </div>
        <script>
            const params = new URLSearchParams(window.location.search);
            const alertContainer = document.getElementById('alert-container');
            if (params.get('success') === 'uploaded') {{
                alertContainer.style.display = 'block';
                alertContainer.style.padding = '12px 16px';
                alertContainer.style.background = '#D1FAE5';
                alertContainer.style.border = '1px solid #A7F3D0';
                alertContainer.style.color = '#065F46';
                alertContainer.style.borderRadius = '8px';
                alertContainer.style.fontSize = '14px';
                alertContainer.style.fontWeight = '600';
                alertContainer.innerHTML = '¡Documento indexado con éxito! Se ha cargado en ChromaDB en tiempo real.';
            }} else if (params.get('error')) {{
                alertContainer.style.display = 'block';
                alertContainer.style.padding = '12px 16px';
                alertContainer.style.background = '#FEE2E2';
                alertContainer.style.border = '1px solid #FCA5A5';
                alertContainer.style.color = '#B91C1C';
                alertContainer.style.borderRadius = '8px';
                alertContainer.style.fontSize = '14px';
                alertContainer.style.fontWeight = '600';
                alertContainer.innerHTML = 'Error al indexar el documento: ' + decodeURIComponent(params.get('error'));
            }}
        </script>
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
        "tickets_creados": 0,
        "ultima_actualizacion": datetime.now().isoformat()
    })
    return {"mensaje": "Metricas reiniciadas"}


ocr_reader = None

def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None:
        import easyocr
        print("Inicializando OCR Reader...")
        ocr_reader = easyocr.Reader(['es', 'en'], gpu=False)
    return ocr_reader


@app.post("/chat/ocr", tags=["Chat"])
async def chat_ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")
        
    try:
        from PIL import Image
        import io
        
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        temp_img_path = Path("temp_ocr_upload.png")
        image.save(temp_img_path)
        
        reader = get_ocr_reader()
        resultados = reader.readtext(str(temp_img_path))
        
        if temp_img_path.exists():
            temp_img_path.unlink()
            
        texto = " ".join([r[1] for r in resultados if r[2] > 0.3])
        return {"texto": texto.strip()}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al procesar la imagen: {str(e)}")


@app.post("/admin/upload", tags=["Admin"])
async def admin_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return RedirectResponse(url="/admin?error=Solo+se+permiten+archivos+PDF.", status_code=303)
    
    try:
        temp_dir = Path("../documentos")
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)
            
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        
        for doc in docs:
            doc.metadata["fuente"] = file.filename
            doc.metadata["tipo"] = "pdf"
            name = file.filename.lower()
            if any(k in name for k in ["carpeta", "inventario", "ingreso", "usuario", "jds", "jop"]):
                doc.metadata["categoria"] = "A"
            elif "gdo" in name or "operaciones" in name:
                doc.metadata["categoria"] = "B"
            elif "gestor" in name:
                doc.metadata["categoria"] = "C"
            elif "vinculacion" in name or "pj" in name:
                doc.metadata["categoria"] = "F"
            else:
                doc.metadata["categoria"] = "D"
                
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)
        
        vector_db.add_documents(chunks)
        return RedirectResponse(url="/admin?success=uploaded", status_code=303)
        
    except Exception as e:
        traceback.print_exc()
        import urllib.parse
        err_msg = urllib.parse.quote(str(e))
        return RedirectResponse(url=f"/admin?error={err_msg}", status_code=303)


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
        if p.categoria:
            docs_and_scores = vector_db.similarity_search_with_score(p.texto, k=6, filter={"categoria": p.categoria})
        else:
            docs_and_scores = vector_db.similarity_search_with_score(p.texto, k=6)
        docs = [doc for doc, score in docs_and_scores]
        fuentes = obtener_fuentes(docs)
        contexto = formatear_docs(docs)
        historial = formatear_historial(p.historial or [])
        confianza = verificar_confianza(docs_and_scores, contexto)
        
        prompt = crear_prompt(p.rol)
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
            if p.categoria:
                docs_and_scores = vector_db.similarity_search_with_score(p.texto, k=6, filter={"categoria": p.categoria})
            else:
                docs_and_scores = vector_db.similarity_search_with_score(p.texto, k=6)
            docs = [doc for doc, score in docs_and_scores]
            fuentes = obtener_fuentes(docs)
            contexto = formatear_docs(docs)
            historial = formatear_historial(p.historial or [])
            confianza = verificar_confianza(docs_and_scores, contexto)
            
            yield f"data: {json.dumps({'tipo': 'fuentes', 'valor': fuentes})}\n\n"
            yield f"data: {json.dumps({'tipo': 'confianza', 'valor': confianza})}\n\n"
            
            prompt = crear_prompt(p.rol)
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


class FeedbackRequest(BaseModel):
    mensaje_id: int
    es_util: bool


class SessionRequest(BaseModel):
    session_id: str


@app.post("/conversacion/iniciar", tags=["Chat"])
def iniciar_conversacion(r: SessionRequest):
    """Iniciar o recuperar conversación."""
    conv_id = db.get_conversacion(r.session_id)
    if not conv_id:
        conv_id = db.crear_conversacion(r.session_id)
    mensajes = db.get_mensajes(conv_id)
    return {"conversacion_id": conv_id, "mensajes": [{"rol": m["rol"], "texto": m["texto"], "id": m["id"]} for m in mensajes]}


@app.post("/conversacion/{conv_id}/mensaje", tags=["Chat"])
def guardar_mensaje(conv_id: int, m: Mensaje):
    """Guardar mensaje en la conversación."""
    msg_id = db.agregar_mensaje(conv_id, m.rol, m.texto)
    return {"mensaje_id": msg_id}


@app.post("/feedback", tags=["Chat"])
def enviar_feedback(f: FeedbackRequest):
    """Guardar feedback del usuario."""
    db.set_feedback(f.mensaje_id, f.es_util)
    return {"mensaje": "OK"}


@app.get("/feedback/estadisticas", tags=["Chat"])
def estadisticas_feedback():
    """Obtener estadísticas de feedback."""
    return db.get_estadisticas()


class TicketRequest(BaseModel):
    conversacion_id: Optional[int] = None
    session_id: str
    categoria: str
    descripcion: str


@app.post("/tickets", tags=["Tickets"])
def crear_nuevo_ticket(t: TicketRequest):
    """Crear un ticket de soporte en la base de datos."""
    try:
        ticket_id = db.crear_ticket(t.conversacion_id, t.session_id, t.categoria, t.descripcion)
        registrar_ticket()
        return {"mensaje": "Ticket creado exitosamente", "ticket_id": ticket_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
