import { useState, useRef, useEffect } from "react"
import Navbar from "./components/Navbar"
import Sidebar from "./components/Sidebar"
import MessageItem from "./components/MessageItem"
import ChatInput from "./components/ChatInput"

const getApiUrlFromParams = () => {
  const params = new URLSearchParams(window.location.search)
  return params.get('apiUrl') || null
}

const isIframe = window.self !== window.top
const API_URL = isIframe 
  ? (getApiUrlFromParams() || 'http://localhost:8000')
  : (import.meta.env.VITE_API_URL || "http://localhost:8000")

const SUGERENCIAS = [
  "¿Qué documentos necesito para una vinculación?",
  "¿Qué es SARLAFT?",
  "¿Cómo administro los usuarios de la Oficina?",
  "¿Qué puedo hacer en el Módulo de Inventarios?",
]

const CATEGORIAS = {
  A: { nombre: "App Carpeta Digital", subcategorias: ["Carpetas", "Inventarios", "Arqueos", "Orden Desembolso", "Demanda en Línea"] },
  B: { nombre: "Framework", subcategorias: ["GDO", "Revisión Documental"] },
  C: { nombre: "Tu Gestor", subcategorias: [] },
  D: { nombre: "Componente Transversal", subcategorias: [] },
  E: { nombre: "Tableros", subcategorias: [] },
  F: { nombre: "Vinculaciones", subcategorias: [] },
}

const generateSessionId = () => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light")
  const [categoria, setCategoria] = useState(null)
  const [sessionId] = useState(() => generateSessionId())
  const [conversacionId, setConversacionId] = useState(null)
  const [mensajes, setMensajes] = useState([
    {
      rol: "asistente",
      texto: "¡Hola! Soy el asistente virtual del Banco de Bogotá.\n\nEstoy aquí para guiarte en normas, trámites y gestiones del banco. Selecciona una categoría en el panel lateral o escribe tu consulta directamente."
    }
  ])
  const [input, setInput] = useState("")
  const [cargando, setCargando] = useState(false)
  const [layoutMode, setLayoutMode] = useState(() => localStorage.getItem("layoutMode") || "full")
  const [widgetMinimized, setWidgetMinimized] = useState(true)
  const [rol, setRol] = useState(() => localStorage.getItem("userRole") || "General")
  
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    localStorage.setItem("userRole", rol)
  }, [rol])

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
    localStorage.setItem("theme", theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem("layoutMode", layoutMode)
  }, [layoutMode])

  const toggleTheme = () => {
    setTheme(prev => prev === "light" ? "dark" : "light")
  }

  useEffect(() => {
    const iniciar = async () => {
      try {
        const res = await fetch(`${API_URL}/conversacion/iniciar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId })
        })
        const data = await res.json()
        setConversacionId(data.conversacion_id)
        if (data.mensajes && data.mensajes.length > 0) {
          setMensajes(data.mensajes.map(m => ({ rol: m.rol, texto: m.texto, id: m.id })))
        }
      } catch (e) { console.log("Error:", e) }
    }
    iniciar()
  }, [sessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [mensajes, cargando])

  const enviar = async (textoOpcional) => {
    const pregunta = (textoOpcional || input).trim()
    if (!pregunta || cargando) return

    const historialActual = mensajes.filter(m => m.rol !== undefined)
    
    setInput("")
    setMensajes(prev => [...prev, { rol: "usuario", texto: pregunta }])
    setMensajes(prev => [...prev, { rol: "asistente", texto: "" }])
    setCargando(true)

    let fuentes = "Documentación Interna"
    let streamingTexto = ""
    let confianzaBaja = false
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          texto: pregunta, 
          historial: historialActual,
          categoria: categoria,
          rol: rol
        }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let streamBuffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        streamBuffer += decoder.decode(value, { stream: true })
        const lineas = streamBuffer.split("\n")
        streamBuffer = lineas.pop()

        for (const linea of lineas) {
          const trimmed = linea.trim()
          if (!trimmed || !trimmed.startsWith("data: ")) continue

          let data
          try {
            data = JSON.parse(trimmed.slice(6))
          } catch (e) {
            console.error("Error parsing JSON line:", trimmed, e)
            continue
          }
          
          if (data.tipo === "fuentes") {
            fuentes = data.valor
          } else if (data.tipo === "confianza") {
            confianzaBaja = !data.valor
          } else if (data.tipo === "chunk") {
            streamingTexto += data.valor
            setMensajes(prev => {
              const nuevos = [...prev]
              nuevos[nuevos.length - 1] = { 
                rol: "asistente", 
                texto: streamingTexto,
                fuente: fuentes,
                confianzaBaja
              }
              return nuevos
            })
          } else if (data.tipo === "error") {
            throw new Error(data.valor)
          }
        }
      }
      
      if (conversacionId) {
        await fetch(`${API_URL}/conversacion/${conversacionId}/mensaje`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rol: "usuario", texto: pregunta })
        })
        await fetch(`${API_URL}/conversacion/${conversacionId}/mensaje`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rol: "asistente", texto: streamingTexto })
        })
      }
    } catch (error) {
      clearTimeout(timeoutId)
      let mensajeError = "Ocurrió un error al procesar tu pregunta. Por favor intenta de nuevo."
      
      if (error.name === 'AbortError') {
        mensajeError = "La solicitud tardó demasiado. Intenta de nuevo."
      }
      
      setMensajes(prev => {
        const nuevos = prev.slice(0, -1)
        nuevos[nuevos.length - 1] = {
          rol: "asistente",
          texto: mensajeError
        }
        return nuevos
      })
    } finally {
      setCargando(false)
      inputRef.current?.focus()
    }
  }

  const limpiarChat = () => {
    setCategoria(null)
    setMensajes([{
      rol: "asistente",
      texto: "Consulta reiniciada. ¿En qué te puedo ayudar hoy?"
    }])
  }

  const enviarFeedback = async (mensajeId, esUtil) => {
    try {
      await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje_id: mensajeId, es_util: esUtil })
      })
    } catch (e) { console.log("Error feedback:", e) }
  }

  const seleccionarCategoria = (cat) => {
    const info = CATEGORIAS[cat.toUpperCase()]
    if (info) {
      setCategoria(cat.toUpperCase())
      let texto = `Has seleccionado la categoría: **${info.nombre}**\n\n`
      if (info.subcategorias.length > 0) {
        texto += "Áreas clave cubiertas:\n" + info.subcategorias.map(s => `- ${s}`).join('\n')
      } else {
        texto += "Puedes hacer cualquier pregunta relacionada con este tema."
      }
      setMensajes([{ rol: "asistente", texto }])
    }
  }

  const subirImagenYProcesarOcr = async (file) => {
    if (cargando) return;
    
    setInput("");
    setMensajes(prev => [...prev, { rol: "usuario", texto: `[Enviando captura: ${file.name}]` }]);
    setMensajes(prev => [...prev, { rol: "asistente", texto: "" }]);
    setCargando(true);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const res = await fetch(`${API_URL}/chat/ocr`, {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) {
        throw new Error("No se pudo procesar la imagen para OCR.");
      }
      
      const data = await res.json();
      const textoExtraido = data.texto;
      
      if (!textoExtraido || !textoExtraido.trim()) {
        setMensajes(prev => {
          const nuevos = prev.slice(0, -1);
          nuevos[nuevos.length - 1] = {
            rol: "asistente",
            texto: "No se encontró ningún texto legible en la captura de pantalla cargada."
          };
          return nuevos;
        });
        setCargando(false);
        return;
      }
      
      setMensajes(prev => {
        const nuevos = [...prev];
        nuevos[nuevos.length - 2] = {
          rol: "usuario",
          texto: `[Texto de captura]: ${textoExtraido}`
        };
        nuevos[nuevos.length - 1] = {
          rol: "asistente",
          texto: "Analizando texto extraído..."
        };
        return nuevos;
      });
      
      let fuentes = "Documentación Interna"
      let streamingTexto = ""
      let confianzaBaja = false
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)

      const historialActual = mensajes.filter(m => m.rol !== undefined)
      
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          texto: textoExtraido, 
          historial: historialActual,
          categoria: categoria,
          rol: rol
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });
        const lineas = streamBuffer.split("\n");
        streamBuffer = lineas.pop();

        for (const linea of lineas) {
          const trimmed = linea.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          let data;
          try {
            data = JSON.parse(trimmed.slice(6));
          } catch (e) {
            console.error("Error parsing JSON line:", trimmed, e);
            continue;
          }
          
          if (data.tipo === "fuentes") {
            fuentes = data.valor;
          } else if (data.tipo === "confianza") {
            confianzaBaja = !data.valor;
          } else if (data.tipo === "chunk") {
            streamingTexto += data.valor;
            setMensajes(prev => {
              const nuevos = [...prev];
              nuevos[nuevos.length - 1] = { 
                rol: "asistente", 
                texto: `**Texto extraído:**\n> ${textoExtraido}\n\n${streamingTexto}`,
                fuente: fuentes,
                confianzaBaja
              };
              return nuevos;
            });
          } else if (data.tipo === "error") {
            throw new Error(data.valor);
          }
        }
      }

      if (conversacionId) {
        await fetch(`${API_URL}/conversacion/${conversacionId}/mensaje`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rol: "usuario", texto: `[Captura de pantalla] - ${textoExtraido}` })
        });
        await fetch(`${API_URL}/conversacion/${conversacionId}/mensaje`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ rol: "asistente", texto: `Texto extraído:\n${textoExtraido}\n\n${streamingTexto}` })
        });
      }

    } catch (error) {
      console.error(error);
      setMensajes(prev => {
        const nuevos = prev.slice(0, -1);
        nuevos[nuevos.length - 1] = {
          rol: "asistente",
          texto: "Hubo un error al procesar el OCR de la imagen: " + error.message
        };
        return nuevos;
      });
    } finally {
      setCargando(false);
    }
  };

  const mostrarSugerencias = mensajes.length === 1

  if (layoutMode === "widget" && widgetMinimized) {
    return (
      <button 
        className="chat-widget-fab"
        onClick={() => setWidgetMinimized(false)}
        title="Abrir asistente de soporte"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    );
  }

  if (layoutMode === "widget" && !widgetMinimized) {
    return (
      <div className="chat-widget-window">
        <Navbar 
          theme={theme} 
          toggleTheme={toggleTheme} 
          layoutMode={layoutMode}
          setLayoutMode={setLayoutMode}
          setWidgetMinimized={setWidgetMinimized}
          rolActivo={rol}
          onCambiarRol={setRol}
        />
        
        <div style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
          padding: "0 16px 16px",
          position: "relative",
          background: "var(--bg-gradient)"
        }}>
          <div style={{
            flex: 1,
            overflowY: "auto",
            minHeight: 0,
            padding: "16px 0",
            display: "flex",
            flexDirection: "column"
          }}>
            {mensajes.map((m, i) => (
              <MessageItem 
                key={i} 
                mensaje={m} 
                index={i} 
                onFeedback={enviarFeedback} 
                conversacionId={conversacionId}
                sessionId={sessionId}
                apiUrl={API_URL}
                preguntaUsuario={i > 0 ? mensajes[i - 1].texto : ""}
                onSendOption={enviar}
              />
            ))}

            {mostrarSugerencias && (
              <div style={{ 
                marginTop: "12px",
                animation: "fadeIn 0.5s ease-out"
              }}>
                <p style={{ 
                  fontSize: "12px", 
                  color: "var(--text-muted)", 
                  marginBottom: "8px",
                  fontWeight: "600" 
                }}>
                  Preguntas sugeridas:
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {SUGERENCIAS.map((sug, i) => (
                    <button 
                      key={i} 
                      onClick={() => enviar(sug)} 
                      style={{
                        background: "var(--card-bg)",
                        border: "1px solid var(--card-border)",
                        borderRadius: "16px",
                        padding: "8px 12px",
                        fontSize: "12px",
                        color: "var(--primary)",
                        cursor: "pointer",
                        fontWeight: "500",
                        transition: "all var(--transition-fast)",
                        boxShadow: "var(--shadow-sm)",
                        fontFamily: "inherit"
                      }}
                      onMouseOver={e => {
                        e.currentTarget.style.transform = "translateY(-1px)";
                        e.currentTarget.style.boxShadow = "var(--shadow-md)";
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.transform = "translateY(0)";
                        e.currentTarget.style.boxShadow = "var(--shadow-sm)";
                      }}
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {cargando && (
              <div style={{ 
                display: "flex", 
                alignItems: "flex-end", 
                gap: "10px", 
                marginBottom: "12px",
                animation: "fadeIn 0.3s ease-out"
              }}>
                <div style={{
                  padding: "12px 16px",
                  borderRadius: "16px 16px 16px 4px",
                  background: "var(--bubble-ai)",
                  border: "1px solid var(--bubble-ai-border)",
                  boxShadow: "var(--shadow-sm)",
                  display: "flex", 
                  gap: "6px", 
                  alignItems: "center"
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: "6px", 
                      height: "6px",
                      borderRadius: "50%",
                      background: "var(--primary)",
                      animation: `bounce 1.4s ease-in-out ${i * 0.2}s infinite`
                    }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <ChatInput 
            input={input} 
            setInput={setInput} 
            onSend={() => enviar()} 
            onClear={limpiarChat} 
            cargando={cargando} 
            inputRef={inputRef} 
            onUploadImage={subirImagenYProcesarOcr}
          />
        </div>
      </div>
    );
  }

  // Full Screen Layout
  return (
    <div style={{
      height: "100vh",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
      background: "var(--bg-gradient)",
      color: "var(--text-main)",
      transition: "background var(--transition-normal)"
    }}>
      {/* Navbar header */}
      <Navbar 
        theme={theme} 
        toggleTheme={toggleTheme} 
        layoutMode={layoutMode}
        setLayoutMode={setLayoutMode}
        setWidgetMinimized={setWidgetMinimized}
        rolActivo={rol}
        onCambiarRol={setRol}
      />

      {/* Main chat body with Sidebar */}
      <div style={{
        display: "flex",
        flex: 1,
        height: "calc(100vh - 72px)",
        width: "100%",
        overflow: "hidden"
      }}>
        <Sidebar 
          categoriaActiva={categoria} 
          onSeleccionarCategoria={seleccionarCategoria} 
          onLimpiarChat={limpiarChat} 
          rolActivo={rol}
          onCambiarRol={setRol}
        />

        {/* Chat window */}
        <div style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
          padding: "0 28px 24px",
          position: "relative"
        }}>
          {/* Scrollable messages panel */}
          <div style={{
            flex: 1,
            overflowY: "auto",
            minHeight: 0,
            padding: "24px 0",
            display: "flex",
            flexDirection: "column"
          }}>
            {mensajes.map((m, i) => (
              <MessageItem 
                key={i} 
                mensaje={m} 
                index={i} 
                onFeedback={enviarFeedback} 
                conversacionId={conversacionId}
                sessionId={sessionId}
                apiUrl={API_URL}
                preguntaUsuario={i > 0 ? mensajes[i - 1].texto : ""}
                onSendOption={enviar}
              />
            ))}

            {mostrarSugerencias && (
              <div style={{ 
                marginTop: "20px",
                animation: "fadeIn 0.5s ease-out"
              }}>
                <p style={{ 
                  fontSize: "13px", 
                  color: "var(--text-muted)", 
                  marginBottom: "12px",
                  fontWeight: "600" 
                }}>
                  Preguntas sugeridas:
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                  {SUGERENCIAS.map((sug, i) => (
                    <button 
                      key={i} 
                      onClick={() => enviar(sug)} 
                      style={{
                        background: "var(--card-bg)",
                        border: "1px solid var(--card-border)",
                        borderRadius: "20px",
                        padding: "10px 16px",
                        fontSize: "13px",
                        color: "var(--primary)",
                        cursor: "pointer",
                        fontWeight: "500",
                        transition: "all var(--transition-fast)",
                        boxShadow: "var(--shadow-sm)",
                        fontFamily: "inherit"
                      }}
                      onMouseOver={e => {
                        e.currentTarget.style.transform = "translateY(-1px)";
                        e.currentTarget.style.boxShadow = "var(--shadow-md)";
                      }}
                      onMouseOut={e => {
                        e.currentTarget.style.transform = "translateY(0)";
                        e.currentTarget.style.boxShadow = "var(--shadow-sm)";
                      }}
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {cargando && (
              <div style={{ 
                display: "flex", 
                alignItems: "flex-end", 
                gap: "10px", 
                marginBottom: "12px",
                animation: "fadeIn 0.3s ease-out"
              }}>
                <div style={{
                  padding: "14px 20px",
                  borderRadius: "20px 20px 20px 4px",
                  background: "var(--bubble-ai)",
                  border: "1px solid var(--bubble-ai-border)",
                  boxShadow: "var(--shadow-sm)",
                  display: "flex", 
                  gap: "6px", 
                  alignItems: "center"
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: "6px", 
                      height: "6px",
                      borderRadius: "50%",
                      background: "var(--primary)",
                      animation: `bounce 1.4s ease-in-out ${i * 0.2}s infinite`
                    }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* User input box */}
          <ChatInput 
            input={input} 
            setInput={setInput} 
            onSend={() => enviar()} 
            onClear={limpiarChat} 
            cargando={cargando} 
            inputRef={inputRef} 
            onUploadImage={subirImagenYProcesarOcr}
          />
        </div>
      </div>
    </div>
  )
}
