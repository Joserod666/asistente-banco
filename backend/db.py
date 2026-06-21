import sqlite3
from datetime import datetime
from typing import List, Optional, Dict

DB_PATH = "conversaciones.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversacion_id INTEGER NOT NULL,
            rol TEXT NOT NULL,
            texto TEXT NOT NULL,
            feedback_util BOOLEAN,
            FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversacion_id INTEGER,
            session_id TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (conversacion_id) REFERENCES conversaciones(id)
        )
    """)
    
    conn.commit()
    conn.close()

def crear_conversacion(session_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversaciones (session_id, fecha) VALUES (?, ?)",
        (session_id, datetime.now().isoformat())
    )
    conv_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conv_id

def get_conversacion(session_id: str) -> Optional[int]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM conversaciones WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def agregar_mensaje(conversacion_id: int, rol: str, texto: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO mensajes (conversacion_id, rol, texto) VALUES (?, ?, ?)",
        (conversacion_id, rol, texto)
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_mensajes(conversacion_id: int) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, rol, texto, feedback_util FROM mensajes WHERE conversacion_id = ?",
        (conversacion_id,)
    )
    mensajes = [
        {"id": row[0], "rol": row[1], "texto": row[2], "feedback_util": row[3]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return mensajes

def set_feedback(mensaje_id: int, es_util: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE mensajes SET feedback_util = ? WHERE id = ?",
        (es_util, mensaje_id)
    )
    conn.commit()
    conn.close()

def get_estadisticas() -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mensajes WHERE feedback_util = 1")
    utiles = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM mensajes WHERE feedback_util = 0")
    no_utiles = cursor.fetchone()[0]
    conn.close()
    return {"utiles": utiles, "no_utiles": no_utiles}

def crear_ticket(conversacion_id: Optional[int], session_id: str, categoria: str, descripcion: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tickets (conversacion_id, session_id, categoria, descripcion, fecha, estado) VALUES (?, ?, ?, ?, ?, ?)",
        (conversacion_id, session_id, categoria, descripcion, datetime.now().isoformat(), "Abierto")
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_tickets() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, conversacion_id, session_id, categoria, descripcion, fecha, estado FROM tickets ORDER BY id DESC")
    tickets = [
        {
            "id": row[0],
            "conversacion_id": row[1],
            "session_id": row[2],
            "categoria": row[3],
            "descripcion": row[4],
            "fecha": row[5],
            "estado": row[6]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return tickets

init_db()