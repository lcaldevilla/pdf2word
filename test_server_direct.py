#!/usr/bin/env python3
"""
Script de prueba directa al servidor de conversión para diagnosticar problemas de timeout
Este script permite probar el servidor externo directamente sin pasar por SendGrid
"""

import requests
import time
import json
import sys
from datetime import datetime

# Configuración
API_URL = "http://lcfcloud.ddns.net:8000"
API_KEY = "yW22q7[+4h0"
TEST_TIMEOUT = 120  # Timeout para la prueba

def create_test_pdf():
    """Crea un PDF de prueba simple similar al que causa problemas"""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World - Test PDF) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000054 00000 n 
0000000115 00000 n 
0000000258 00000 n 
0000000345 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
456
%%EOF"""

def test_server_connectivity():
    """Prueba básica de conectividad con el servidor"""
    print(f"\n{'='*60}")
    print("🔍 PRUEBA 1: CONECTIVIDAD BÁSICA")
    print(f"{'='*60}")
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Probando conexión a {API_URL}")
        
        start_time = time.time()
        response = requests.get(f"{API_URL}/", timeout=10)
        connection_time = time.time() - start_time
        
        print(f"✅ Conexión exitosa en {connection_time:.2f}s")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout de 10s al conectar con {API_URL}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_health_check():
    """Prueba del health check detallado del servidor"""
    print(f"\n{'='*60}")
    print("🏥 PRUEBA 2: HEALTH CHECK DETALLADO")
    print(f"{'='*60}")
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Verificando health check...")
        
        start_time = time.time()
        response = requests.get(f"{API_URL}/health", timeout=30)
        health_time = time.time() - start_time
        
        print(f"✅ Health check completado en {health_time:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"Estado general: {health_data.get('status', 'unknown')}")
            
            # Mostrar detalles de cada check
            checks = health_data.get('checks', {})
            for check_name, check_data in checks.items():
                status = check_data.get('status', 'unknown')
                if status == 'ok':
                    print(f"  ✅ {check_name}: OK")
                    if 'version' in check_data:
                        print(f"     Versión: {check_data['version']}")
                    elif 'percent_used' in check_data:
                        print(f"     Uso: {check_data['percent_used']:.1f}%")
                else:
                    print(f"  ❌ {check_name}: {status}")
                    print(f"     Error: {check_data.get('error', 'N/A')}")
        else:
            print(f"❌ Health check falló: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout de 30s en health check")
        return False
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_libreoffice_direct():
    """Prueba directa del endpoint de test de LibreOffice"""
    print(f"\n{'='*60}")
    print("🔧 PRUEBA 3: TEST DIRECTO DE LIBREOFFICE")
    print(f"{'='*60}")
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Probando LibreOffice directamente...")
        
        headers = {"X-API-Key": API_KEY}
        
        start_time = time.time()
        response = requests.post(f"{API_URL}/test-libreoffice", headers=headers, timeout=60)
        test_time = time.time() - start_time
        
        print(f"⏱️  Test de LibreOffice completado en {test_time:.2f}s")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            test_data = response.json()
            print(f"✅ Test exitoso: {test_data.get('message', 'N/A')}")
            print(f"   Duración: {test_data.get('test_duration_seconds', 'N/A')}s")
            print(f"   Tamaño DOCX: {test_data.get('docx_size_bytes', 'N/A')} bytes")
            
            if test_data.get('stdout'):
                print(f"   STDOUT: {test_data['stdout']}")
            if test_data.get('stderr'):
                print(f"   STDERR: {test_data['stderr']}")
        else:
            print(f"❌ Test de LibreOffice falló:")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'N/A')}")
                if error_data.get('stdout'):
                    print(f"   STDOUT: {error_data['stdout']}")
                if error_data.get('stderr'):
                    print(f"   STDERR: {error_data['stderr']}")
            except:
                print(f"   Response: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout de 60s en test de LibreOffice")
        return False
    except Exception as e:
        print(f"❌ Error en test de LibreOffice: {e}")
        return False

def test_pdf_conversion():
    """Prueba completa de conversión de PDF"""
    print(f"\n{'='*60}")
    print("📄 PRUEBA 4: CONVERSIÓN COMPLETA DE PDF")
    print(f"{'='*60}")
    
    try:
        # Crear PDF de prueba
        test_pdf = create_test_pdf()
        filename = "test_timeout_diagnosis.pdf"
        
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Iniciando conversión de {filename}")
        print(f"   Tamaño PDF: {len(test_pdf)} bytes")
        
        headers = {"X-API-Key": API_KEY}
        files = {'file': (filename, test_pdf, 'application/pdf')}
        
        # Medir diferentes fases
        connection_start = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Enviando solicitud HTTP...")
        
        response = requests.post(f"{API_URL}/convert", files=files, headers=headers, timeout=TEST_TIMEOUT)
        
        connection_time = time.time() - connection_start
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Respuesta recibida en {connection_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        if response.status_code == 200:
            # Verificar si es archivo o JSON
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                # Es respuesta JSON (archivo grande)
                result_data = response.json()
                print(f"✅ Conversión exitosa (archivo grande)")
                print(f"   Resultado: {result_data}")
            else:
                # Es archivo directo
                docx_content = response.content
                print(f"✅ Conversión exitosa (archivo directo)")
                print(f"   Tamaño DOCX: {len(docx_content)} bytes")
                
                # Guardar archivo para verificación
                with open("test_output.docx", "wb") as f:
                    f.write(docx_content)
                print(f"   Archivo guardado como: test_output.docx")
                
        else:
            print(f"❌ Conversión falló (Status: {response.status_code})")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', error_data)}")
            except:
                print(f"   Response: {response.text[:500]}")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"❌ Timeout de {TEST_TIMEOUT}s en conversión de PDF")
        return False
    except Exception as e:
        print(f"❌ Error en conversión de PDF: {e}")
        return False

def main():
    """Función principal que ejecuta todas las pruebas"""
    print("🚀 INICIANDO DIAGNÓSTICO DEL SERVIDOR DE CONVERSIÓN")
    print(f"🎯 Objetivo: Identificar por qué los PDFs pequeños tardan >120s")
    print(f"🌐 Servidor: {API_URL}")
    print(f"⏰ Timeout máximo: {TEST_TIMEOUT}s")
    
    # Ejecutar pruebas en secuencia
    tests = [
        ("Conectividad Básica", test_server_connectivity),
        ("Health Check", test_health_check),
        ("Test LibreOffice", test_libreoffice_direct),
        ("Conversión PDF", test_pdf_conversion)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Error inesperado en prueba '{test_name}': {e}")
            results[test_name] = False
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE RESULTADOS")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
    
    # Recomendaciones
    print(f"\n🎯 RECOMENDACIONES:")
    
    if not results.get("Conectividad Básica", False):
        print("❌ El servidor no está accesible. Verificar:")
        print("   - Que el servidor está corriendo")
        print("   - Que hay conectividad de red")
        print("   - Que el firewall no bloquea el puerto 8000")
    
    elif not results.get("Health Check", False):
        print("❌ El servidor responde pero el health check falla. Verificar:")
        print("   - Que LibreOffice está instalado")
        print("   - Que hay recursos suficientes (memoria, disco)")
    
    elif not results.get("Test LibreOffice", False):
        print("❌ LibreOffice no funciona correctamente. Verificar:")
        print("   - Instalación de LibreOffice")
        print("   - Permisos para ejecutar subprocess")
        print("   - Variables de entorno de LibreOffice")
    
    elif not results.get("Conversión PDF", False):
        print("❌ La conversión de PDF falla. Verificar:")
        print("   - El endpoint /convert funciona correctamente")
        print("   - El procesamiento de archivos multipart")
        print("   - Los timeouts internos")
    
    else:
        print("✅ Todas las pruebas pasaron. El problema podría estar en:")
        print("   - El archivo PDF específico que causa el problema")
        print("   - La configuración de timeouts en Railway")
        print("   - Problemas de red específicos de Railway")
    
    print(f"\n🔍 Próximos pasos recomendados:")
    print("1. Si el servidor externo falla, repararlo primero")
    print("2. Si el servidor funciona, probar con el PDF problemático real")
    print("3. Considerar mover la conversión a Railway para mayor control")
    
    # Retornar código de salida
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
