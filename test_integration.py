#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del servicio de conversión
con manejo de archivos grandes y enlaces de descarga.
"""

import os
import requests
import json
from pathlib import Path

# Configuración de prueba
API_URL = "http://lcfcloud.ddns.net:8000"
API_KEY = "yW22q7[+4h0"  # Clave del servidor
TEST_PDF_PATH = "test_document.pdf"  # Necesitas tener un PDF de prueba

def test_convert_endpoint():
    """Probar el endpoint /convert normal"""
    print("🧪 Probando endpoint /convert...")
    
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ Error: No se encuentra el archivo de prueba {TEST_PDF_PATH}")
        return False
    
    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': (TEST_PDF_PATH, f.read(), 'application/pdf')}
            headers = {'X-API-Key': API_KEY}
            
            response = requests.post(f"{API_URL}/convert", files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                    file_size = len(response.content) / (1024 * 1024)
                    print(f"✅ Conversión exitosa. Tamaño: {file_size:.2f} MB")
                    
                    # Guardar el resultado para inspección
                    with open("test_output.docx", 'wb') as out_file:
                        out_file.write(response.content)
                    print("💾 Archivo guardado como test_output.docx")
                    return True
                else:
                    print(f"❌ Content-Type inesperado: {content_type}")
                    return False
            else:
                print(f"❌ Error en la API: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

def test_convert_and_store_endpoint():
    """Probar el endpoint /convert-and-store"""
    print("\n🧪 Probando endpoint /convert-and-store...")
    
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ Error: No se encuentra el archivo de prueba {TEST_PDF_PATH}")
        return False
    
    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': (TEST_PDF_PATH, f.read(), 'application/pdf')}
            headers = {'X-API-Key': API_KEY}
            
            response = requests.post(f"{API_URL}/convert-and-store", files=files, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Archivo almacenado exitosamente:")
                print(f"   📁 File ID: {data['file_id']}")
                print(f"   📊 Tamaño: {data['size_mb']} MB")
                print(f"   🔗 Download URL: {data['download_url']}")
                print(f"   ⏰ Expira: {data['expires_at']}")
                
                # Probar la descarga
                return test_download_endpoint(data['file_id'])
            else:
                print(f"❌ Error en la API: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

def test_download_endpoint(file_id):
    """Probar el endpoint de descarga"""
    print(f"\n🧪 Probando endpoint /download/{file_id}...")
    
    try:
        response = requests.get(f"{API_URL}/download/{file_id}", timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                file_size = len(response.content) / (1024 * 1024)
                print(f"✅ Descarga exitosa. Tamaño: {file_size:.2f} MB")
                
                # Guardar el resultado para inspección
                with open("test_downloaded.docx", 'wb') as out_file:
                    out_file.write(response.content)
                print("💾 Archivo guardado como test_downloaded.docx")
                return True
            else:
                print(f"❌ Content-Type inesperado: {content_type}")
                return False
        else:
            print(f"❌ Error en la descarga: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en la descarga: {e}")
        return False

def test_cleanup_endpoint():
    """Probar el endpoint de limpieza"""
    print("\n🧪 Probando endpoint /admin/cleanup...")
    
    try:
        headers = {'X-API-Key': API_KEY}
        response = requests.get(f"{API_URL}/admin/cleanup", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Limpieza completada:")
            print(f"   📁 Archivos activos: {data['active_files']}")
            return True
        else:
            print(f"❌ Error en limpieza: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de integración del servicio de conversión\n")
    
    # Verificar que el servidor está disponible
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ El servidor no está disponible en {API_URL}")
            return
        print(f"✅ Servidor disponible en {API_URL}")
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return
    
    # Ejecutar pruebas
    results = []
    results.append(test_convert_endpoint())
    results.append(test_convert_and_store_endpoint())
    results.append(test_cleanup_endpoint())
    
    # Resumen
    print(f"\n📊 Resumen de pruebas:")
    passed = sum(results)
    total = len(results)
    print(f"   ✅ Pasadas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los logs para más detalles.")

if __name__ == "__main__":
    main()
