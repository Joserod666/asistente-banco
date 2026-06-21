import React from "react";

export default function ChatInput({ 
  input, 
  setInput, 
  onSend, 
  onClear, 
  cargando, 
  inputRef,
  onUploadImage
}) {
  const fileInputRef = React.useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onUploadImage(file);
      e.target.value = ""; // reset to allow same upload
    }
  };

  return (
    <div style={{
      background: "var(--card-bg)",
      borderRadius: "24px",
      padding: "16px",
      boxShadow: "var(--shadow-md)",
      border: "1px solid var(--card-border)",
      transition: "all var(--transition-normal)"
    }}>
      <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu pregunta sobre normas, SARLAFT o carpeta digital..."
          rows={2}
          style={{
            flex: 1,
            border: "2px solid var(--input-border)",
            background: "var(--input-bg)",
            borderRadius: "16px",
            padding: "14px 18px",
            color: "var(--text-main)",
            fontSize: "14px",
            resize: "none",
            fontFamily: "inherit",
            lineHeight: "1.6",
            transition: "all var(--transition-fast)"
          }}
          disabled={cargando}
        />
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {/* Hidden File Input for Screen Capture OCR */}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            style={{ display: "none" }} 
          />

          <button 
            onClick={onSend} 
            disabled={cargando || !input.trim()}
            style={{
              background: cargando || !input.trim() 
                ? "var(--scroll-thumb)" 
                : "var(--primary-gradient)",
              border: "none",
              borderRadius: "12px",
              padding: "10px 20px",
              color: "#FFFFFF",
              fontSize: "13px",
              fontWeight: "600",
              cursor: cargando || !input.trim() ? "not-allowed" : "pointer",
              transition: "all var(--transition-fast)",
              boxShadow: cargando || !input.trim() ? "none" : "var(--shadow-bubble-user)",
              fontFamily: "'Montserrat', sans-serif"
            }}
          >
            {cargando ? "Enviando..." : "Enviar"}
          </button>

          <button 
            type="button"
            onClick={() => fileInputRef.current?.click()} 
            disabled={cargando}
            style={{
              background: "transparent",
              border: "1px solid var(--input-border)",
              borderRadius: "12px",
              padding: "8px 16px",
              color: "var(--text-main)",
              fontSize: "11px",
              cursor: "pointer",
              fontWeight: "600",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              transition: "all var(--transition-fast)",
              fontFamily: "'Montserrat', sans-serif"
            }}
            title="Subir captura de pantalla"
            onMouseOver={e => e.currentTarget.style.background = "var(--input-border)"}
            onMouseOut={e => e.currentTarget.style.background = "transparent"}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
              <circle cx="12" cy="13" r="4"></circle>
            </svg>
            Subir Captura
          </button>
          
          <button 
            onClick={onClear}
            style={{
              background: "transparent",
              border: "1px solid var(--input-border)",
              borderRadius: "10px",
              padding: "6px 16px",
              color: "var(--text-muted)",
              fontSize: "11px",
              cursor: "pointer",
              fontWeight: "500",
              transition: "all var(--transition-fast)",
              fontFamily: "'Montserrat', sans-serif"
            }}
          >
            Reiniciar
          </button>
        </div>
      </div>
      <div style={{
        marginTop: "12px",
        fontSize: "11px",
        color: "var(--text-muted)",
        textAlign: "center",
        fontWeight: "500",
        letterSpacing: "0.2px"
      }}>
        Asistente de uso interno · Banco de Bogotá · Cumplimiento Normativo
      </div>
    </div>
  );
}
