import React, { useState } from "react";
import Logo from "../Logo.png";
import { parseMarkdown } from "../utils/markdown";

export default function MessageItem({ mensaje, index, onFeedback, conversacionId, sessionId, apiUrl, preguntaUsuario, onSendOption }) {
  const esUsuario = mensaje.rol === "usuario";
  const [feedbackEnviado, setFeedbackEnviado] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [categoria, setCategoria] = useState("General");
  const [descripcion, setDescripcion] = useState(preguntaUsuario || "");
  const [ticketId, setTicketId] = useState(null);
  const [cargandoTicket, setCargandoTicket] = useState(false);
  const [errorTicket, setErrorTicket] = useState(null);
  
  const handleFeedback = (esUtil) => {
    if (mensaje.id && !feedbackEnviado) {
      onFeedback(mensaje.id, esUtil);
      setFeedbackEnviado(true);
    }
  };

  // Extract quick replies (buttons)
  const buttons = [];
  let textoLimpio = mensaje.texto || "";
  
  if (mensaje.rol === "asistente") {
    const regex = /\[Boton:\s*(.*?)\]/g;
    let match;
    while ((match = regex.exec(mensaje.texto || "")) !== null) {
      buttons.push(match[1].trim());
    }
    textoLimpio = textoLimpio.replace(regex, "").trim();
  }

  const parsedHtml = parseMarkdown(textoLimpio);
  
  return (
    <div 
      style={{
        display: "flex",
        justifyContent: esUsuario ? "flex-end" : "flex-start",
        alignItems: "flex-end",
        gap: "12px",
        marginBottom: "16px",
        animation: "fadeIn 0.3s ease-out",
        animationDelay: `${index * 0.03}s`,
        animationFillMode: "both"
      }}
    >
      {!esUsuario && (
        <div style={{
          width: "40px", 
          height: "40px",
          background: "var(--primary-gradient)",
          borderRadius: "12px",
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center",
          flexShrink: 0,
          boxShadow: "0 4px 12px rgba(0,51,160,0.2)"
        }}>
          <img src={Logo} alt="Banco" style={{ width: "26px", height: "26px", objectFit: "contain" }} />
        </div>
      )}
      
      <div style={{
        maxWidth: "75%",
        padding: "14px 20px",
        borderRadius: esUsuario ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
        background: esUsuario ? "var(--bubble-user)" : "var(--bubble-ai)",
        color: esUsuario ? "#FFFFFF" : "var(--text-main)",
        fontSize: "14px",
        lineHeight: "1.7",
        boxShadow: esUsuario ? "var(--shadow-bubble-user)" : "var(--shadow-sm)",
        border: esUsuario ? "none" : "1px solid var(--bubble-ai-border)",
        position: "relative"
      }}>
        {/* Render markdown using dangerouslySetInnerHTML */}
        <div 
          className="markdown-body" 
          dangerouslySetInnerHTML={{ __html: parsedHtml }} 
        />
        
        {buttons.length > 0 && (
          <div style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
            marginTop: "12px",
            paddingTop: "10px",
            borderTop: "1px solid var(--bubble-ai-border)",
            animation: "fadeIn 0.2s ease-out"
          }}>
            {buttons.map((btn, bIdx) => (
              <button
                key={bIdx}
                onClick={() => onSendOption && onSendOption(btn)}
                style={{
                  background: "var(--card-bg)",
                  border: "1.5px solid var(--primary)",
                  borderRadius: "16px",
                  padding: "8px 14px",
                  fontSize: "12px",
                  color: "var(--primary)",
                  cursor: "pointer",
                  fontWeight: "600",
                  transition: "all var(--transition-fast)",
                  boxShadow: "var(--shadow-sm)",
                  fontFamily: "inherit"
                }}
                onMouseOver={e => {
                  e.currentTarget.style.background = "var(--primary)";
                  e.currentTarget.style.color = "#FFFFFF";
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseOut={e => {
                  e.currentTarget.style.background = "var(--card-bg)";
                  e.currentTarget.style.color = "var(--primary)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                {btn}
              </button>
            ))}
          </div>
        )}
        

        
        {mensaje.confianzaBaja && (
          <div style={{
            marginTop: "12px",
            padding: "14px",
            background: "rgba(245, 168, 0, 0.08)",
            borderRadius: "12px",
            fontSize: "13px",
            color: "var(--text-main)",
            border: "1px solid rgba(245, 168, 0, 0.25)",
            display: "flex",
            flexDirection: "column",
            gap: "10px"
          }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ color: "var(--accent)", flexShrink: 0, marginTop: "2px" }}>
                <path d="M12 2L2 22h20L12 2zm0 15a1.5 1.5 0 110 3 1.5 1.5 0 010-3zm0-8a1.5 1.5 0 011.5 1.5v4a1.5 1.5 0 01-3 0v-4A1.5 1.5 0 0112 9z"/>
              </svg>
              <div>
                <span style={{ fontWeight: "600", color: "var(--accent)" }}>Baja confianza en la respuesta.</span>
                <p style={{ marginTop: "2px", color: "var(--text-muted)", fontSize: "12px" }}>
                  La información en la base de conocimientos es limitada para esta consulta.
                </p>
              </div>
            </div>

            {!showForm && !ticketId && (
              <button
                onClick={() => {
                  setShowForm(true);
                  setDescripcion(preguntaUsuario || "");
                }}
                style={{
                  background: "var(--primary-gradient)",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                  alignSelf: "flex-start",
                  boxShadow: "0 2px 6px rgba(0, 51, 160, 0.15)",
                  transition: "all 0.15s ease",
                  fontFamily: "inherit"
                }}
                onMouseOver={e => e.currentTarget.style.filter = "brightness(1.1)"}
                onMouseOut={e => e.currentTarget.style.filter = "none"}
              >
                Crear Ticket de Soporte
              </button>
            )}

            {showForm && !ticketId && (
              <div style={{
                marginTop: "6px",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                animation: "fadeIn 0.25s ease-out"
              }}>
                <div style={{ borderTop: "1px solid rgba(245, 168, 0, 0.15)", paddingTop: "8px" }}>
                  <label style={{ fontWeight: "600", fontSize: "11px", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "6px" }}>
                    Categoría del Ticket:
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "6px" }}>
                    {["Acceso", "Soporte Técnico", "Normas/Procesos", "General"].map((cat) => {
                      const isSelected = categoria === cat;
                      return (
                        <button
                          key={cat}
                          type="button"
                          onClick={() => setCategoria(cat)}
                          style={{
                            background: isSelected ? "var(--primary)" : "var(--input-bg)",
                            color: isSelected ? "#FFFFFF" : "var(--text-main)",
                            border: `1px solid ${isSelected ? "var(--primary)" : "var(--input-border)"}`,
                            borderRadius: "6px",
                            padding: "6px 8px",
                            fontSize: "11px",
                            fontWeight: isSelected ? "600" : "500",
                            cursor: "pointer",
                            transition: "all 0.15s ease",
                            textAlign: "center",
                            fontFamily: "inherit"
                          }}
                        >
                          {cat}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <label style={{ fontWeight: "600", fontSize: "11px", textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>
                    Descripción del Problema:
                  </label>
                  <textarea
                    value={descripcion}
                    onChange={(e) => setDescripcion(e.target.value)}
                    rows="3"
                    style={{
                      width: "100%",
                      padding: "8px 10px",
                      borderRadius: "6px",
                      background: "var(--input-bg)",
                      color: "var(--text-main)",
                      border: "1px solid var(--input-border)",
                      fontSize: "12px",
                      resize: "vertical",
                      fontFamily: "inherit"
                    }}
                    placeholder="Describe los detalles del problema..."
                  />
                </div>

                {errorTicket && (
                  <div style={{ color: "#EF4444", fontSize: "11px", fontWeight: "500" }}>
                    Error: {errorTicket}
                  </div>
                )}

                <div style={{ display: "flex", gap: "8px", justifyContent: "flex-end", marginTop: "4px" }}>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    style={{
                      background: "transparent",
                      color: "var(--text-muted)",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 12px",
                      fontSize: "11px",
                      fontWeight: "600",
                      cursor: "pointer",
                      fontFamily: "inherit"
                    }}
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    disabled={cargandoTicket || !descripcion.trim()}
                    onClick={async () => {
                      setCargandoTicket(true);
                      setErrorTicket(null);
                      try {
                        const res = await fetch(`${apiUrl}/tickets`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            conversacion_id: conversacionId,
                            session_id: sessionId,
                            categoria: categoria,
                            descripcion: descripcion.trim()
                          })
                        });
                        if (!res.ok) {
                          throw new Error("No se pudo crear el ticket. Código: " + res.status);
                        }
                        const data = await res.json();
                        setTicketId(data.ticket_id);
                        setShowForm(false);
                      } catch (err) {
                        setErrorTicket(err.message || "Error de red");
                      } finally {
                        setCargandoTicket(false);
                      }
                    }}
                    style={{
                      background: "var(--primary-gradient)",
                      color: "#FFFFFF",
                      border: "none",
                      borderRadius: "6px",
                      padding: "6px 12px",
                      fontSize: "11px",
                      fontWeight: "600",
                      cursor: "pointer",
                      boxShadow: "0 2px 4px rgba(0, 51, 160, 0.15)",
                      fontFamily: "inherit"
                    }}
                  >
                    {cargandoTicket ? "Enviando..." : "Enviar Ticket"}
                  </button>
                </div>
              </div>
            )}

            {ticketId && (
              <div style={{
                marginTop: "6px",
                padding: "8px 10px",
                background: "#D1FAE5",
                border: "1px solid #A7F3D0",
                borderRadius: "8px",
                color: "#065F46",
                fontWeight: "600",
                fontSize: "12px",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                animation: "fadeIn 0.3s ease-out"
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" style={{ flexShrink: 0 }}>
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>¡Ticket #{ticketId} creado con éxito! Se ha escalado a Nivel 2.</span>
              </div>
            )}
          </div>
        )}
        
        {!esUsuario && !feedbackEnviado && mensaje.id && (
          <div style={{ 
            marginTop: "12px", 
            paddingTop: "8px", 
            borderTop: "1px solid var(--bubble-ai-border)", 
            display: "flex", 
            alignItems: "center", 
            gap: "10px", 
            fontSize: "11px", 
            color: "var(--text-muted)" 
          }}>
            <span>¿Te fue útil esta respuesta?</span>
            <button 
              onClick={() => handleFeedback(true)} 
              style={{ 
                background: "transparent", 
                border: "none", 
                color: "#10B981", 
                cursor: "pointer", 
                fontWeight: "700",
                fontSize: "11px"
              }}
            >
              Sí
            </button>
            <span style={{ color: "var(--bubble-ai-border)" }}>|</span>
            <button 
              onClick={() => handleFeedback(false)} 
              style={{ 
                background: "transparent", 
                border: "none", 
                color: "var(--text-muted)", 
                cursor: "pointer",
                fontWeight: "500",
                fontSize: "11px"
              }}
            >
              No
            </button>
          </div>
        )}
        
        {feedbackEnviado && !esUsuario && (
          <div style={{ 
            marginTop: "10px", 
            fontSize: "11px", 
            color: "#10B981", 
            fontWeight: "700",
            display: "flex",
            alignItems: "center",
            gap: "4px"
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            ¡Gracias por tu opinión!
          </div>
        )}
      </div>
      
      {esUsuario && (
        <div style={{
          width: "40px", 
          height: "40px",
          background: "var(--accent-gradient)",
          borderRadius: "12px",
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center",
          flexShrink: 0,
          boxShadow: "0 4px 12px rgba(245,168,0,0.2)"
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
      )}
    </div>
  );
}
