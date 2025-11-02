#!/usr/bin/env python3
"""
Script para probar la conversión local con debugging detallado
Simula exactamente el mismo proceso que se ejecuta en Railway
"""
import os
import sys
import tempfile
import subprocess
import time
from datetime import datetime

def test_libreoffice_conversion_with_real_pdf():
    """Prueba la conversión con un PDF que simula el problema real"""
    print("=== PRUEBA DE CONVERSIÓN CON DEBUGGING ===")
    
    # Crear un PDF de prueba más complejo que podría causar problemas
    test_pdf_content = b"""%PDF-1.4
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
/Length 100
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document requerimeintos ddbb) Tj
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
0000000058 00000 n 
0000000115 00000 n 
0000000261 00000 n 
0000000334 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
413
%%EOF"""

    print(f"PDF de prueba creado: {len(test_pdf_content)} bytes")
    
    # Usar el mismo nombre que causa problemas
    pdf_filename = "requerimeintos ddbb.pdf"
    sanitized_filename = "requerimeintos_ddbb.pdf"
    
    # Crear directorio temporal para la prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Directorio temporal: {temp_dir}")
        
        # Guardar PDF en archivo temporal
        pdf_path = os.path.join(temp_dir, sanitized_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(test_pdf_content)
        
        print(f"PDF guardado en: {pdf_path}")
        print(f"Nombre original: {pdf_filename}")
        print(f"Nombre sanitizado: {sanitized_filename}")
        
        # Probar comando de LibreOffice exactamente como en el código
        command = [
            'libreoffice',
            '--headless',
            '--convert-to', 'docx',
            '--outdir', temp_dir,
            pdf_path
        ]
        
        print(f"Ejecutando comando: {' '.join(command)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            conversion_time = time.time() - start_time
            
            print(f"Conversión completada en {conversion_time:.2f} segundos")
            print(f"Código de salida: {result.returncode}")
            
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            
            # Listar todos los archivos en el directorio (como en el código mejorado)
            all_files = os.listdir(temp_dir)
            print(f"Todos los archivos en directorio: {all_files}")
            
            # Buscar archivos DOCX con diferentes métodos
            docx_files = [f for f in all_files if f.lower().endswith('.docx')]
            print(f"Archivos DOCX encontrados: {docx_files}")
            
            # Si no encuentra .docx, buscar otros archivos
            if not docx_files:
                print("Buscando archivos alternativos...")
                alternative_files = [f for f in all_files if not f.endswith('.pdf')]
                print(f"Archivos alternativos: {alternative_files}")
                
                if alternative_files:
                    alt_file = alternative_files[0]
                    print(f"Archivo alternativo encontrado: {alt_file}")
                    
                    # Verificar si el archivo tiene contenido válido
                    alt_path = os.path.join(temp_dir, alt_file)
                    try:
                        with open(alt_path, 'rb') as f:
                            alt_content = f.read()
                        
                        print(f"Tamaño del archivo alternativo: {len(alt_content)} bytes")
                        
                        # Verificar si parece un DOCX (debe empezar con PK - formato ZIP)
                        if alt_content.startswith(b'PK'):
                            print("✅ Formato válido (detectado como ZIP/DOCX)")
                            
                            # Renombrar a .docx si no tiene extensión
                            if '.' not in alt_file:
                                new_name = alt_file + '.docx'
                                new_path = os.path.join(temp_dir, new_name)
                                os.rename(alt_path, new_path)
                                print(f"Renombrado a: {new_name}")
                                docx_files = [new_name]
                            else:
                                docx_files = [alt_file]
                        else:
                            print("❌ Formato inválido (no empieza con PK)")
                            
                    except Exception as e:
                        print(f"Error leyendo archivo alternativo: {e}")
            
            if docx_files:
                docx_path = os.path.join(temp_dir, docx_files[0])
                docx_size = os.path.getsize(docx_path)
                
                print(f"✅ ARCHIVO FINAL: {docx_files[0]}")
                print(f"✅ Tamaño DOCX: {docx_size} bytes ({docx_size/1024:.2f} KB)")
                
                # Verificar contenido
                with open(docx_path, 'rb') as f:
                    docx_content = f.read()
                
                if docx_content.startswith(b'PK'):
                    print("✅ Formato DOCX válido")
                    return True
                else:
                    print("❌ Formato DOCX inválido")
                    return False
            else:
                print("❌ No se encontró ningún archivo válido")
                print(f"Archivos finales en directorio: {os.listdir(temp_dir)}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ TIMEOUT: La conversión tardó más de 30 segundos")
            return False
            
        except subprocess.CalledProcessError as e:
            print(f"❌ ERROR en LibreOffice (código {e.returncode}):")
            if e.stdout:
                print(f"STDOUT: {e.stdout}")
            if e.stderr:
                print(f"STDERR: {e.stderr}")
            return False
            
        except FileNotFoundError:
            print("❌ ERROR: LibreOffice no encontrado en el sistema")
            print("Asegúrate de que LibreOffice está instalado y en el PATH")
            return False
            
        except Exception as e:
            print(f"❌ ERROR INESPERADO: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_filename_sanitization():
    """Prueba la función de sanitización de nombres"""
    print("=== PRUEBA DE SANITIZACIÓN ===")
    
    test_cases = [
        "requerimeintos ddbb.pdf",
        "requerimeintos_ddbb.pdf",
        "Manual de Usuario Touch Point.pdf",
        "archivo con espacios y ñ.pdf",
        "file@#$%&().pdf"
    ]
    
    for original in test_cases:
        # Simular la función sanitize_filename
        import re
        name, ext = os.path.splitext(original)
        cleaned_name = re.sub(r'[^\w\-_\.]', '_', name)
        
        if len(cleaned_name) > 45:
            cleaned_name = cleaned_name[:45]
        
        cleaned_filename = cleaned_name + ext
        
        if not cleaned_name or cleaned_name.isspace():
            cleaned_filename = "document" + ext
        
        print(f"'{original}' → '{cleaned_filename}'")

if __name__ == "__main__":
    print(f"Fecha y hora: {datetime.now()}")
    print()
    
    # Probar sanitización
    test_filename_sanitization()
    print()
    
    # Probar conversión
    if test_libreoffice_conversion_with_real_pdf():
        print("\n✅ PRUEBA EXITOSA: La conversión local funciona correctamente")
        sys.exit(0)
    else:
        print("\n❌ PRUEBA FALLIDA: La conversión local no funciona")
        sys.exit(1)
