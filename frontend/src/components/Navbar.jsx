import React from "react";
import Logo from "../Logo.png";

export default function Navbar({ 
  theme, 
  toggleTheme, 
  layoutMode = "full", 
  setLayoutMode, 
  setWidgetMinimized,
  rolActivo = "General",
  onCambiarRol
}) {
  return (
    <div style={{
      width: "100%",
      background: "var(--primary-gradient)",
      padding: layoutMode === "full" ? "0 32px" : "0 16px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      height: "72px",
      boxShadow: "var(--shadow-md)",
      zIndex: 10
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{
          background: "#FFFFFF",
          borderRadius: "12px",
          padding: "6px 10px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
        }}>
          <img src={Logo} alt="Banco de Bogotá" style={{ width: "24px", height: "24px", objectFit: "contain" }} />
          <span style={{
            fontWeight: "800",
            fontSize: "13px",
            color: "var(--primary)",
            letterSpacing: "-0.5px",
            fontFamily: "'Montserrat', sans-serif"
          }}>
            Banco de Bogotá
          </span>
        </div>
        {layoutMode === "full" && (
          <div style={{
            color: "rgba(255,255,255,0.9)",
            fontSize: "13px",
            fontWeight: "500",
            letterSpacing: "0.2px"
          }}>
            Asistente Virtual Interno
          </div>
        )}
      </div>
      
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {layoutMode === "widget" && (
          <select 
            value={rolActivo} 
            onChange={(e) => onCambiarRol(e.target.value)}
            style={{
              padding: "6px 8px",
              borderRadius: "8px",
              border: "1px solid rgba(255,255,255,0.25)",
              background: "rgba(255, 255, 255, 0.15)",
              color: "#FFFFFF",
              fontSize: "11px",
              fontWeight: "600",
              cursor: "pointer",
              outline: "none",
              fontFamily: "inherit"
            }}
          >
            <option value="General" style={{ color: "#000000" }}>General</option>
            <option value="Cajero" style={{ color: "#000000" }}>Cajero</option>
            <option value="Director de Oficina" style={{ color: "#000000" }}>Director</option>
            <option value="Analista TI" style={{ color: "#000000" }}>Analista TI</option>
          </select>
        )}
        {layoutMode === "widget" && setWidgetMinimized && (
          <button 
            onClick={() => setWidgetMinimized(true)}
            style={{
              background: "rgba(255, 255, 255, 0.1)",
              border: "none",
              borderRadius: "50%",
              width: "36px",
              height: "36px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: "#FFFFFF",
              transition: "all var(--transition-fast)"
            }}
            title="Minimizar chat"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>
        )}

        {setLayoutMode && (
          <button 
            onClick={() => {
              setLayoutMode(prev => {
                const next = prev === "full" ? "widget" : "full";
                if (next === "widget" && setWidgetMinimized) {
                  setWidgetMinimized(false);
                }
                return next;
              });
            }}
            style={{
              background: "rgba(255, 255, 255, 0.1)",
              border: "none",
              borderRadius: "50%",
              width: "36px",
              height: "36px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: "#FFFFFF",
              transition: "all var(--transition-fast)"
            }}
            title={layoutMode === "full" ? "Cambiar a Widget flotante" : "Cambiar a Pantalla completa"}
          >
            {layoutMode === "full" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              </svg>
            )}
          </button>
        )}

        <button 
          onClick={toggleTheme}
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            border: "none",
            borderRadius: "50%",
            width: "36px",
            height: "36px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "#FFFFFF",
            transition: "all var(--transition-fast)"
          }}
          title={`Cambiar a modo ${theme === "light" ? "oscuro" : "claro"}`}
        >
          {theme === "light" ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.22" x2="5.64" y2="17.78" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>
        
        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginLeft: "4px" }}>
          <div style={{
            width: "8px", 
            height: "8px",
            background: "#10B981",
            borderRadius: "50%",
            animation: "pulse 2s ease-in-out infinite"
          }} />
          {layoutMode === "full" && (
            <span style={{ color: "rgba(255,255,255,0.9)", fontSize: "12px", fontWeight: "600" }}>En línea</span>
          )}
        </div>
      </div>
    </div>
  );
}
