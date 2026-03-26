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
            "Banco de Bogota" in resp.text
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
                    timeout=10
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
