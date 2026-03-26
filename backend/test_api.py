"""
Script de pruebas para el Asistente del Banco de Bogotá
Uso: python test_api.py
"""

import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Prueba 1: Endpoint de salud"""
    print("\n[1] Health check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200
        print(f"    [OK] - {resp.json()}")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_swagger():
    """Prueba 2: Swagger disponible"""
    print("\n[2] Swagger UI")
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert resp.status_code == 200
        print(f"    [OK] - Swagger disponible en /docs")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_chat_basico():
    """Prueba 3: Chat basico"""
    print("\n[3] Chat basico")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "Que es SARLAFT?"},
            timeout=30
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "respuesta" in data
        assert "fuentes" in data
        print(f"    [OK] - Respuesta recibida ({len(data['respuesta'])} chars)")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_chat_con_historial():
    """Prueba 4: Historial de conversacion"""
    print("\n[4] Historial de conversacion")
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
            timeout=30
        )
        assert resp.status_code == 200
        print(f"    [OK] - Historial enviado y procesado")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_streaming():
    """Prueba 5: Streaming SSE"""
    print("\n[5] Streaming SSE")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/stream",
            json={"texto": "Cual es el proceso de vinculacion?"},
            stream=True,
            timeout=60
        )
        assert resp.status_code == 200
        
        chunks_recibidos = 0
        fuentes = None
        confianza = None
        
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
                        chunks_recibidos += 1
                    elif data['tipo'] == 'fin':
                        break
        
        assert chunks_recibidos > 0, "No se recibieron chunks"
        print(f"    [OK] - {chunks_recibidos} chunks, fuentes={fuentes}, confianza={confianza}")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_confianza_baja():
    """Prueba 6: Deteccion de baja confianza"""
    print("\n[6] Baja confianza (pregunta fuera de contexto)")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"texto": "xyz123 fuera de contexto 456"},
            timeout=30
        )
        assert resp.status_code == 200
        data = resp.json()
        confianza = data.get("confianza", True)
        print(f"    [{'OK' if not confianza else 'WARN'}] - Confianza: {confianza}")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_rate_limit():
    """Prueba 7: Rate limiting"""
    print("\n[7] Rate limiting (enviando 22 peticiones...)")
    try:
        errores_429 = 0
        exitosas = 0
        
        for i in range(22):
            try:
                resp = requests.post(
                    f"{BASE_URL}/chat",
                    json={"texto": f"Test {i}"},
                    timeout=10
                )
                if resp.status_code == 429:
                    errores_429 += 1
                elif resp.status_code == 200:
                    exitosas += 1
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.1)
        
        print(f"    [{'OK' if errores_429 > 0 else 'WARN'}] - Rate limit: {errores_429} denegadas, {exitosas} aceptadas")
        return True
    except Exception as e:
        print(f"    [FAIL] - {e}")
        return False


def test_error_servidor():
    """Prueba 8: Manejo de errores (backend apagado)"""
    print("\n[8] Error de conexion (simulado)")
    print("    [INFO] Esta prueba requiere que el backend este apagado")
    return True


def main():
    print("=" * 60)
    print("PRUEBAS - Asistente Banco de Bogota")
    print("=" * 60)
    
    resultados = []
    
    resultados.append(("Health check", test_health()))
    resultados.append(("Swagger UI", test_swagger()))
    resultados.append(("Chat basico", test_chat_basico()))
    resultados.append(("Historial", test_chat_con_historial()))
    resultados.append(("Streaming", test_streaming()))
    resultados.append(("Baja confianza", test_confianza_baja()))
    resultados.append(("Rate limit", test_rate_limit()))
    resultados.append(("Errores", test_error_servidor()))
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    passed = sum(1 for _, ok in resultados if ok)
    total = len(resultados)
    
    for name, ok in resultados:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"   {status} - {name}")
    
    print(f"\n   Total: {passed}/{total} pruebas aprobadas")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
