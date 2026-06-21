"""
Tests automatizados para el Asistente del Banco de Bogota
Uso: python test_api.py
Requiere: requests (pip install requests)
"""

import requests
import time
import json
from typing import Tuple, Optional

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30


def print_result(name: str, passed: bool, detail: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"   {status} - {name}")
    if detail:
        print(f"         {detail}")


def test_health() -> bool:
    """Endpoint de salud para monitoreo"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        data = resp.json()
        passed = resp.status_code == 200 and data.get("status") == "ok"
        print_result("Health check", passed, str(data))
        return passed
    except Exception as e:
        print_result("Health check", False, str(e))
        return False


def test_root() -> bool:
    """Endpoint raiz"""
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        data = resp.json()
        passed = resp.status_code == 200
        print_result("Root endpoint", passed, str(data))
        return passed
    except Exception as e:
        print_result("Root endpoint", False, str(e))
        return False


def test_swagger() -> bool:
    """Documentacion API (Swagger UI)"""
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        passed = resp.status_code == 200 and "swagger" in resp.text.lower()
        print_result("Swagger UI", passed, "Disponible en /docs")
        return passed
    except Exception as e:
        print_result("Swagger UI", False, str(e))
        return False


def test_metrics_api() -> bool:
    """Endpoint de metricas (JSON)"""
    try:
        resp = requests.get(f"{BASE_URL}/metrics", timeout=5)
        data = resp.json()
        required_fields = ["total_preguntas", "preguntas_resueltas", "tasa_resolucion"]
        passed = resp.status_code == 200 and all(f in data for f in required_fields)
        print_result("Metrics API", passed, f"Tasa: {data.get('tasa_resolucion', 0)}%")
        return passed
    except Exception as e:
        print_result("Metrics API", False, str(e))
        return False


def test_admin_dashboard() -> bool:
    """Dashboard HTML de administracion"""
    try:
        resp = requests.get(f"{BASE_URL}/admin", timeout=5)
        passed = (
            resp.status_code == 200 and
            resp.headers.get("content-type", "").startswith("text/html") and
            ("Banco de Bogota" in resp.text or "Banco de Bogotá" in resp.text)
        )
        print_result("Admin Dashboard", passed, "HTML disponible en /admin")
        return passed
    except Exception as e:
        print_result("Admin Dashboard", False, str(e))
        return False


def test_reset_metrics() -> bool:
    """Reset de metricas"""
    try:
        resp = requests.post(f"{BASE_URL}/metrics/reset", timeout=5)
        metrics = requests.get(f"{BASE_URL}/metrics", timeout=5).json()
        passed = resp.status_code == 200 and metrics.get("total_preguntas") == 0
        print_result("Reset Metrics", passed, f"Total: {metrics.get('total_preguntas')}")
        return passed
    except Exception as e:
        print_result("Reset Metrics", False, str(e))
        return False


def test_chat_basico() -> bool:
    """Chat basico sin historial"""
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "Que es SARLAFT?"},
            timeout=TIMEOUT
        )
        data = resp.json()
        passed = (
            resp.status_code == 200 and
            "respuesta" in data and
            "fuentes" in data
        )
        detail = f"{len(data.get('respuesta', ''))} chars" if passed else str(data)
        print_result("Chat basico", passed, detail)
        return passed
    except Exception as e:
        print_result("Chat basico", False, str(e))
        return False


def test_chat_con_historial() -> bool:
    """Chat con historial de conversacion"""
    try:
        historial = [
            {"rol": "usuario", "texto": "Que documentos necesito para abrir una cuenta?"},
            {"rol": "asistente", "texto": "Para abrir una cuenta necesitas..."}
        ]
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={
                "texto": "Y si es una empresa SAS?",
                "historial": historial
            },
            timeout=TIMEOUT
        )
        passed = resp.status_code == 200 and "respuesta" in resp.json()
        print_result("Chat con historial", passed)
        return passed
    except Exception as e:
        print_result("Chat con historial", False, str(e))
        return False


def test_confianza_baja() -> bool:
    """Deteccion de baja confianza"""
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "xyz123 fuera de contexto aleatorio 456"},
            timeout=TIMEOUT
        )
        data = resp.json()
        passed = resp.status_code == 200 and "confianza" in data
        print_result("Baja confianza", passed, f"Confianza: {data.get('confianza')}")
        return passed
    except Exception as e:
        print_result("Baja confianza", False, str(e))
        return False


def test_streaming() -> bool:
    """Respuesta en streaming (SSE)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/stream",
            json={"texto": "Cual es el proceso de vinculacion?"},
            stream=True,
            timeout=TIMEOUT + 10
        )
        
        chunks = 0
        fuentes = None
        confianza = None
        fin = False
        
        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data['tipo'] == 'fuentes':
                        fuentes = data['valor']
                    elif data['tipo'] == 'confianza':
                        confianza = data['valor']
                    elif data['tipo'] == 'chunk':
                        chunks += 1
                    elif data['tipo'] == 'fin':
                        fin = True
        
        passed = chunks > 0 and fin
        print_result("Streaming SSE", passed, f"{chunks} chunks, fin={fin}")
        return passed
    except Exception as e:
        print_result("Streaming SSE", False, str(e))
        return False


def test_rate_limit() -> bool:
    """Rate limiting (20/min)"""
    try:
        denegadas = 0
        aceptadas = 0
        
        for i in range(25):
            try:
                resp = requests.post(
                    f"{BASE_URL}/chat",
                    json={"texto": f"Test rate limit {i}"},
                    timeout=30
                )
                if resp.status_code == 429:
                    denegadas += 1
                elif resp.status_code == 200:
                    aceptadas += 1
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.05)
        
        passed = denegadas > 0
        print_result("Rate limiting", passed, f"{denegadas} denegadas, {aceptadas} aceptadas")
        return passed
    except Exception as e:
        print_result("Rate limiting", False, str(e))
        return False


def test_metrics_increment() -> bool:
    """Verificar que las metricas se incrementan"""
    try:
        before = requests.get(f"{BASE_URL}/metrics", timeout=5).json()
        before_total = before.get("total_preguntas", 0)
        
        requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "Test increment metrics"},
            timeout=TIMEOUT
        )
        
        after = requests.get(f"{BASE_URL}/metrics", timeout=5).json()
        after_total = after.get("total_preguntas", 0)
        
        passed = after_total > before_total
        print_result("Metrics incrementan", passed, f"{before_total} -> {after_total}")
        return passed
    except Exception as e:
        print_result("Metrics incrementan", False, str(e))
        return False


def test_crear_ticket() -> bool:
    """Creacion de tickets de soporte tecnico"""
    try:
        payload = {
            "conversacion_id": 1,
            "session_id": "test_session_123",
            "categoria": "Soporte Tecnico",
            "descripcion": "No funciona la conexion VPN al intentar acceder"
        }
        resp = requests.post(f"{BASE_URL}/tickets", json=payload, timeout=5)
        data = resp.json()
        passed = resp.status_code == 200 and "ticket_id" in data
        
        # Verificar que sale en metricas
        metrics = requests.get(f"{BASE_URL}/metrics", timeout=5).json()
        tickets_creados = metrics.get("tickets_creados", 0)
        
        # Verificar que esta en admin html
        admin_resp = requests.get(f"{BASE_URL}/admin", timeout=5)
        in_admin = "test_session_123" in admin_resp.text
        
        passed = passed and tickets_creados > 0 and in_admin
        print_result("Crear ticket de soporte", passed, f"Ticket ID: {data.get('ticket_id')}, Creados: {tickets_creados}")
        return passed
    except Exception as e:
        print_result("Crear ticket de soporte", False, str(e))
        return False

def test_chat_con_rol() -> bool:
    """Chat con rol específico de usuario (ej. Cajero)"""
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "Cuáles son los requisitos de arqueo?", "rol": "Cajero"},
            timeout=TIMEOUT
        )
        data = resp.json()
        passed = (
            resp.status_code == 200 and
            "respuesta" in data
        )
        print_result("Chat con rol (Cajero)", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        print_result("Chat con rol (Cajero)", False, str(e))
        return False


def test_ocr_imagen() -> bool:
    """Endpoint de OCR para imágenes"""
    try:
        from PIL import Image
        import io
        
        img = Image.new('RGB', (100, 100), color = 'white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {'file': ('test_image.png', img_bytes, 'image/png')}
        resp = requests.post(
            f"{BASE_URL}/chat/ocr",
            files=files,
            timeout=TIMEOUT
        )
        passed = resp.status_code == 200
        data = resp.json()
        print_result("OCR de Imagen", passed, f"Texto extraído: '{data.get('texto')}'")
        return passed
    except Exception as e:
        print_result("OCR de Imagen", False, str(e))
        return False


def test_upload_pdf() -> bool:
    """Subida e indexación de PDF en caliente"""
    try:
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources << >>\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Texto de prueba de vinculacion de cuenta) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000062 00000 n\n0000000125 00000 n\n0000000230 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n0000000325\n%%EOF"
        
        import io
        pdf_file = io.BytesIO(pdf_content)
        files = {'file': ('test_doc_vinculacion_caja.pdf', pdf_file, 'application/pdf')}
        
        resp = requests.post(
            f"{BASE_URL}/admin/upload",
            files=files,
            allow_redirects=False,
            timeout=TIMEOUT
        )
        
        passed = (
            resp.status_code == 303 and
            "success=uploaded" in resp.headers.get("location", "")
        )
        print_result("Subida PDF en caliente", passed, f"Redirige a: {resp.headers.get('location')}")
        return passed
    except Exception as e:
        print_result("Subida PDF en caliente", False, str(e))
        return False


def run_tests():
    """Ejecuta todas las pruebas"""
    print("\n" + "=" * 60)
    print("PRUEBAS AUTOMATIZADAS - Asistente Banco de Bogota")
    print("=" * 60)
    print(f"URL Base: {BASE_URL}")
    print("=" * 60 + "\n")
    
    tests = [
        ("Infraestructura", [
            test_health,
            test_root,
            test_swagger,
        ]),
        ("Metricas", [
            test_metrics_api,
            test_admin_dashboard,
            test_reset_metrics,
        ]),
        ("Chat", [
            test_chat_basico,
            test_chat_con_historial,
            test_confianza_baja,
            test_streaming,
            test_metrics_increment,
            test_crear_ticket,
        ]),
        ("Nuevas Mejoras Soporte e IA", [
            test_chat_con_rol,
            test_ocr_imagen,
            test_upload_pdf,
        ]),
        ("Seguridad", [
            test_rate_limit,
        ]),
    ]
    
    total_passed = 0
    total_tests = 0
    
    for category, test_functions in tests:
        print(f"\n--- {category} ---")
        for test in test_functions:
            total_tests += 1
            if test():
                total_passed += 1
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"\n   Pruebas aprobadas: {total_passed}/{total_tests}")
    print(f"   Porcentaje: {round(total_passed/total_tests*100, 1)}%")
    print("=" * 60 + "\n")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
