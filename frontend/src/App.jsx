import { useState, useRef, useEffect } from "react"
import Logo from "./Logo.png"

const getApiUrlFromParams = () => {
  const params = new URLSearchParams(window.location.search)
  return params.get('apiUrl') || null
}

const isIframe = window.self !== window.top
const API_URL = isIframe 
  ? (getApiUrlFromParams() || 'http://localhost:8000')
  : (import.meta.env.VITE_API_URL || "http://localhost:8000")

const COLORES = {
  azul: "#0033A0",
  azulOscuro: "#002280",
  azulClaro: "#E8EEF8",
  amarillo: "#F5A800",
  blanco: "#FFFFFF",
  fondo: "#F4F6FA",
  gris: "#6B7280",
  grisClaro: "#E5E7EB",
  texto: "#1F2937",
  verde: "#10B981",
}

function MensajeItem({ mensaje, index }) {
  const esUsuario = mensaje.rol === "usuario"
  return (
    <div 
      style={{
        display: "flex",
        justifyContent: esUsuario ? "flex-end" : "flex-start",
        alignItems: "flex-end",
        gap: "10px",
        marginBottom: "12px",
        animation: "fadeIn 0.3s ease-out",
        animationDelay: `${index * 0.05}s`,
        animationFillMode: "both"
      }}
    >
      {!esUsuario && (
        <div style={{
          width: "40px", 
          height: "40px",
          background: `linear-gradient(135deg, ${COLORES.azul} 0%, ${COLORES.azulOscuro} 100%)`,
          borderRadius: "12px",
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center",
          flexShrink: 0,
          boxShadow: "0 4px 12px rgba(0,51,160,0.25)"
        }}>
          <img src={Logo} alt="Banco" style={{ width: "28px", height: "28px", objectFit: "contain" }} />
        </div>
      )}
      
      <div style={{
        maxWidth: "70%",
        padding: "14px 18px",
        borderRadius: esUsuario ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
        background: esUsuario 
          ? `linear-gradient(135deg, ${COLORES.azul} 0%, ${COLORES.azulOscuro} 100%)` 
          : COLORES.blanco,
        color: esUsuario ? COLORES.blanco : COLORES.texto,
        fontSize: "14px",
        lineHeight: "1.7",
        boxShadow: esUsuario 
          ? "0 4px 16px rgba(0,51,160,0.3)" 
          : "0 2px 8px rgba(0,0,0,0.06)",
        border: esUsuario ? "none" : `1px solid ${COLORES.grisClaro}`,
        position: "relative"
      }}>
        {mensaje.texto.split('\n').map((linea, i) => (
          linea.trim() === ''
            ? <br key={i} />
            : <p key={i} style={{ margin: "2px 0", lineHeight: "1.7" }}>{linea}</p>
        ))}
        
        {mensaje.fuente && (
          <div style={{
            marginTop: "10px",
            paddingTop: "10px",
            borderTop: `1px solid ${esUsuario ? 'rgba(255,255,255,0.2)' : COLORES.grisClaro}`,
            fontSize: "11px",
            color: esUsuario ? "rgba(255,255,255,0.7)" : COLORES.gris,
            display: "flex",
            alignItems: "center",
            gap: "6px"
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
            </svg>
            {mensaje.fuente}
          </div>
        )}
        
        {mensaje.confianzaBaja && (
          <div style={{
            marginTop: "10px",
            padding: "10px 12px",
            background: "rgba(254,243,199,0.95)",
            borderRadius: "10px",
            fontSize: "12px",
            color: "#92400E",
            display: "flex",
            alignItems: "flex-start",
            gap: "8px",
            border: "1px solid #FCD34D"
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#F59E0B" style={{ flexShrink: 0, marginTop: "2px" }}>
              <path d="M12 2L2 22h20L12 2zm0 15a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0-8a1.5 1.5 0 011.5 1.5v4a1.5 1.5 0 01-3 0v-4A1.5 1.5 0 0112 9z"/>
            </svg>
            <span>Información limitada. Te recomiendo verificar con un supervisor.</span>
          </div>
        )}
      </div>
      
      {esUsuario && (
        <div style={{
          width: "40px", 
          height: "40px",
          background: `linear-gradient(135deg, ${COLORES.amarillo} 0%, #E09000 100%)`,
          borderRadius: "12px",
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center",
          flexShrink: 0,
          boxShadow: "0 4px 12px rgba(245,168,0,0.3)"
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ 
      display: "flex", 
      alignItems: "flex-end", 
      gap: "10px", 
      marginBottom: "12px",
      animation: "fadeIn 0.3s ease-out"
    }}>
      <div style={{
        width: "40px", 
        height: "40px",
        background: `linear-gradient(135deg, ${COLORES.azul} 0%, ${COLORES.azulOscuro} 100%)`,
        borderRadius: "12px",
        display: "flex", 
        alignItems: "center", 
        justifyContent: "center",
        boxShadow: "0 4px 12px rgba(0,51,160,0.25)"
      }}>
        <img src={Logo} alt="Banco" style={{ width: "28px", height: "28px", objectFit: "contain" }} />
      </div>
      <div style={{
        padding: "14px 20px",
        borderRadius: "20px 20px 20px 4px",
        background: COLORES.blanco,
        border: `1px solid ${COLORES.grisClaro}`,
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        display: "flex", 
        gap: "6px", 
        alignItems: "center"
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: "8px", 
            height: "8px",
            borderRadius: "50%",
            background: COLORES.azul,
            animation: `bounce 1.4s ease-in-out ${i * 0.2}s infinite`
          }} />
        ))}
      </div>
    </div>
  )
}

const SUGERENCIAS = [
  "¿Qué documentos necesito para una vinculación?",
  "¿Qué es SARLAFT?",
  "¿Cuál es el proceso de apertura de cuenta?",
]

export default function App() {
  const [mensajes, setMensajes] = useState([
    {
      rol: "asistente",
      texto: "¡Hola! Soy el asistente virtual del Banco de Bogotá. Estoy aquí para ayudarte con consultas sobre procesos internos, documentación y procedimientos. ¿En qué puedo ayudarte hoy?"
    }
  ])
  const [input, setInput] = useState("")
  const [cargando, setCargando] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [mensajes, cargando])

  const enviar = async (texto) => {
    const pregunta = (texto || input).trim()
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
        body: JSON.stringify({ texto: pregunta, historial: historialActual }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lineas = chunk.split("\n").filter(l => l.startsWith("data: "))

        for (const linea of lineas) {
          const data = JSON.parse(linea.slice(6))
          
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
    } catch (error) {
      clearTimeout(timeoutId)
      let mensajeError = "Ocurrió un error al procesar tu pregunta. Por favor intenta de nuevo."
      
      if (!response || !response.ok) {
        if (response && response.status === 500) {
          mensajeError = "El servidor encontró un problema. Por favor intenta más tarde."
        } else if (response && response.status === 503) {
          mensajeError = "El servicio no está disponible temporalmente. Intenta en unos minutos."
        } else {
          mensajeError = "No se pudo conectar con el servidor. Verifica tu conexión."
        }
      } else if (error.name === 'AbortError') {
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
    setMensajes([{
      rol: "asistente",
      texto: "Chat reiniciado. ¿En qué puedo ayudarte?"
    }])
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      enviar()
    }
  }

  const mostrarSugerencias = mensajes.length === 1

  return (
    <>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${COLORES.fondo}; font-family: 'Montserrat', 'Segoe UI', sans-serif; }
        
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-8px); }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${COLORES.grisClaro}; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: ${COLORES.gris}; }
        
        textarea:focus, button:focus { outline: none; }
        
        .suggestion-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,51,160,0.2);
        }
        
        .send-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(0,51,160,0.4);
        }
      `}</style>

      <div style={{
        minHeight: "100vh",
        background: `linear-gradient(180deg, ${COLORES.fondo} 0%, #E8EEF8 100%)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "0",
        fontFamily: "'Montserrat', 'Segoe UI', sans-serif"
      }}>

        <div style={{
          width: "100%",
          background: `linear-gradient(135deg, ${COLORES.azul} 0%, ${COLORES.azulOscuro} 100%)`,
          padding: "0 32px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "72px",
          boxShadow: "0 4px 20px rgba(0,51,160,0.25)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{
              background: COLORES.blanco,
              borderRadius: "12px",
              padding: "8px 16px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
            }}>
              <img src={Logo} alt="Banco" style={{ width: "32px", height: "32px" }} />
              <span style={{
                fontWeight: "700",
                fontSize: "16px",
                color: COLORES.azul,
                letterSpacing: "-0.5px"
              }}>
                Banco de Bogotá
              </span>
            </div>
            <div style={{
              color: "rgba(255,255,255,0.85)",
              fontSize: "14px",
              fontWeight: "500"
            }}>
              Asistente Virtual Interno
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{
                width: "8px", 
                height: "8px",
                background: COLORES.verde,
                borderRadius: "50%",
                animation: "pulse 2s ease-in-out infinite"
              }} />
              <span style={{ color: "rgba(255,255,255,0.9)", fontSize: "12px", fontWeight: "500" }}>En linea</span>
            </div>
          </div>
        </div>

        <div style={{
          width: "100%",
          maxWidth: "900px",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "calc(100vh - 72px)",
          padding: "0 24px 24px"
        }}>

          <div style={{
            flex: 1,
            overflowY: "auto",
            padding: "28px 0",
            display: "flex",
            flexDirection: "column",
            gap: "4px"
          }}>
            {mensajes.map((m, i) => (
              <MensajeItem key={i} mensaje={m} index={i} />
            ))}

            {mostrarSugerencias && (
              <div style={{ 
                marginTop: "24px",
                animation: "fadeIn 0.5s ease-out"
              }}>
                <p style={{ 
                  fontSize: "13px", 
                  color: COLORES.gris, 
                  marginBottom: "14px",
                  fontWeight: "500" 
                }}>
                  Preguntas frecuentes:
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                  {SUGERENCIAS.map((s, i) => (
                    <button 
                      key={i} 
                      onClick={() => enviar(s)} 
                      className="suggestion-btn"
                      style={{
                        background: COLORES.blanco,
                        border: `2px solid ${COLORES.azul}`,
                        borderRadius: "24px",
                        padding: "10px 18px",
                        fontSize: "13px",
                        color: COLORES.azul,
                        cursor: "pointer",
                        fontFamily: "'Montserrat', sans-serif",
                        fontWeight: "500",
                        transition: "all 0.2s ease"
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {cargando && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          <div style={{
            background: COLORES.blanco,
            borderRadius: "20px",
            padding: "16px",
            boxShadow: "0 -4px 24px rgba(0,0,0,0.08)",
            border: `1px solid ${COLORES.grisClaro}`
          }}>
            <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Escribe tu pregunta aquí..."
                rows={2}
                style={{
                  flex: 1,
                  border: `2px solid ${COLORES.grisClaro}`,
                  background: COLORES.fondo,
                  borderRadius: "14px",
                  padding: "14px 18px",
                  color: COLORES.texto,
                  fontSize: "14px",
                  resize: "none",
                  fontFamily: "'Montserrat', sans-serif",
                  lineHeight: "1.6",
                  transition: "border-color 0.2s ease"
                }}
              />
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <button 
                  onClick={enviar} 
                  disabled={cargando || !input.trim()}
                  className="send-btn"
                  style={{
                    background: cargando || !input.trim() ? COLORES.grisClaro : `linear-gradient(135deg, ${COLORES.azul} 0%, ${COLORES.azulOscuro} 100%)`,
                    border: "none",
                    borderRadius: "12px",
                    padding: "12px 24px",
                    color: COLORES.blanco,
                    fontSize: "14px",
                    fontWeight: "600",
                    cursor: cargando || !input.trim() ? "not-allowed" : "pointer",
                    fontFamily: "'Montserrat', sans-serif",
                    transition: "all 0.2s ease",
                    boxShadow: cargando || !input.trim() ? "none" : "0 4px 16px rgba(0,51,160,0.3)"
                  }}
                >
                  {cargando ? "Enviando..." : "Enviar"}
                </button>
                <button 
                  onClick={limpiarChat}
                  style={{
                    background: "transparent",
                    border: `1px solid ${COLORES.grisClaro}`,
                    borderRadius: "10px",
                    padding: "8px",
                    color: COLORES.gris,
                    fontSize: "12px",
                    cursor: "pointer",
                    fontFamily: "'Montserrat', sans-serif",
                    fontWeight: "500",
                    transition: "all 0.2s ease"
                  }}
                >
                  Limpiar
                </button>
              </div>
            </div>
            <div style={{
              marginTop: "12px",
              fontSize: "11px",
              color: COLORES.gris,
              textAlign: "center",
              fontWeight: "500"
            }}>
              Asistente de uso interno · Banco de Bogotá
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
