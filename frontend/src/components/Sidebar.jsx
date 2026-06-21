import React from "react";

const CATEGORIAS = {
  A: { nombre: "App Carpeta Digital", subcategorias: ["Carpetas", "Inventarios", "Arqueos", "Orden Desembolso", "Demanda en Línea"] },
  B: { nombre: "Framework", subcategorias: ["GDO", "Revisión Documental"] },
  C: { nombre: "Tu Gestor", subcategorias: [] },
  D: { nombre: "Componente Transversal", subcategorias: [] },
  E: { nombre: "Tableros", subcategorias: [] },
  F: { nombre: "Vinculaciones", subcategorias: [] },
};

export default function Sidebar({ 
  categoriaActiva, 
  onSeleccionarCategoria, 
  onLimpiarChat,
  rolActivo = "General",
  onCambiarRol
}) {
  return (
    <div style={{
      width: "280px",
      background: "var(--card-bg)",
      borderRight: "1px solid var(--card-border)",
      display: "flex",
      flexDirection: "column",
      height: "100%",
      flexShrink: 0,
      zIndex: 5,
      transition: "all var(--transition-normal)"
    }}>
      {/* Session Controls */}
      <div style={{ padding: "20px 16px", borderBottom: "1px solid var(--card-border)", display: "flex", flexDirection: "column", gap: "12px" }}>
        <button 
          onClick={onLimpiarChat}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
            background: "var(--primary-gradient)",
            color: "#FFFFFF",
            border: "none",
            borderRadius: "12px",
            padding: "12px",
            fontSize: "14px",
            fontWeight: "600",
            cursor: "pointer",
            boxShadow: "var(--shadow-bubble-user)",
            transition: "all var(--transition-fast)",
            fontFamily: "'Montserrat', sans-serif"
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nueva Consulta
        </button>

        {/* Perfil de Usuario / Rol */}
        <div style={{ marginTop: "4px" }}>
          <label style={{
            fontSize: "10px",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: "var(--text-muted)",
            display: "block",
            marginBottom: "6px",
            fontWeight: "700"
          }}>
            Perfil / Rol de Usuario
          </label>
          <select 
            value={rolActivo} 
            onChange={(e) => onCambiarRol(e.target.value)}
            style={{
              width: "100%",
              padding: "10px 12px",
              borderRadius: "10px",
              border: "2px solid var(--input-border)",
              background: "var(--input-bg)",
              color: "var(--text-main)",
              fontSize: "13px",
              fontWeight: "600",
              cursor: "pointer",
              outline: "none",
              transition: "all var(--transition-fast)"
            }}
          >
            <option value="General">General (Default)</option>
            <option value="Cajero">Cajero de Oficina</option>
            <option value="Director de Oficina">Director de Oficina</option>
            <option value="Analista TI">Analista Soporte TI</option>
          </select>
        </div>
      </div>

      {/* Navigation Categories */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 12px" }}>
        <h3 style={{
          fontSize: "11px",
          textTransform: "uppercase",
          letterSpacing: "1px",
          color: "var(--text-muted)",
          marginBottom: "12px",
          paddingLeft: "10px",
          fontWeight: "700"
        }}>
          Categorías de Consulta
        </h3>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {Object.entries(CATEGORIAS).map(([clave, valor]) => {
            const esActiva = categoriaActiva === clave;
            return (
              <button
                key={clave}
                onClick={() => onSeleccionarCategoria(clave)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  background: esActiva ? "var(--primary-light)" : "transparent",
                  color: esActiva ? "var(--primary)" : "var(--text-main)",
                  border: "none",
                  borderRadius: "10px",
                  padding: "10px 12px",
                  fontSize: "13px",
                  fontWeight: esActiva ? "700" : "500",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  transition: "all var(--transition-fast)",
                  fontFamily: "inherit"
                }}
              >
                <span>{valor.nombre}</span>
                {valor.subcategorias.length > 0 && (
                  <span style={{
                    fontSize: "9px",
                    background: esActiva ? "var(--primary)" : "var(--input-border)",
                    color: esActiva ? "#FFFFFF" : "var(--text-muted)",
                    padding: "2px 6px",
                    borderRadius: "8px",
                    fontWeight: "700"
                  }}>
                    {valor.subcategorias.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Corporate Help Section */}
      <div style={{
        padding: "20px 16px",
        borderTop: "1px solid var(--card-border)",
        background: "var(--input-bg)",
        borderBottomLeftRadius: "var(--radius-lg)"
      }}>
        <h4 style={{ 
          fontSize: "12px", 
          fontWeight: "700", 
          color: "var(--text-main)",
          marginBottom: "6px" 
        }}>
          Guías Rápidas
        </h4>
        <p style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.4" }}>
          Pregunta sobre el sistema de vinculación PJ, inventarios, arboles de decisión en carpetas o normas de SARLAFT.
        </p>
      </div>
    </div>
  );
}
