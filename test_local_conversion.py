#!/usr/bin/env python3
"""
Script para probar la conversión local de PDF a DOCX con LibreOffice
"""
import os
import sys
import tempfile
import subprocess
import time
from datetime import datetime

def test_libreoffice_conversion():
    """Prueba la conversión con un PDF de prueba"""
    print("=== PRUEBA DE CONVERSIÓN LOCAL ===")
    
    # Crear un PDF de prueba simple
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
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
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
    
    # Crear directorio temporal para la prueba
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Directorio temporal: {temp_dir}")
        
        # Guardar PDF en archivo temporal
        pdf_filename = "test_documento.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(test_pdf_content)
        
        print(f"PDF guardado en: {pdf_path}")
        
        # Probar comando de LibreOffice
        output_filename = pdf_filename.replace('.pdf', '.docx')
        
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
            
            # Verificar si se creó el archivo DOCX
            docx_files = [f for f in os.listdir(temp_dir) if f.endswith('.docx')]
            
            if docx_files:
                docx_path = os.path.join(temp_dir, docx_files[0])
                docx_size = os.path.getsize(docx_path)
                
                print(f"✅ ARCHIVO DOCX CREADO: {docx_files[0]}")
                print(f"✅ Tamaño DOCX: {docx_size} bytes ({docx_size/1024:.2f} KB)")
                
                # Verificar contenido básico
                with open(docx_path, 'rb') as f:
                    docx_content = f.read()
                
                if docx_content.startswith(b'PK'):
                    print("✅ Formato DOCX válido (formato ZIP)")
                else:
                    print("❌ Formato DOCX inválido")
                
                return True
            else:
                print("❌ No se encontró archivo DOCX")
                print(f"Archivos en directorio: {os.listdir(temp_dir)}")
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
            return False

def check_libreoffice_installation():
    """Verifica si LibreOffice está instalado"""
    print("=== VERIFICANDO INSTALACIÓN DE LIBREOFFICE ===")
    
    try:
        result = subprocess.run(
            ['libreoffice', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ LibreOffice encontrado: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ LibreOffice no funciona (código {result.returncode})")
            return False
            
    except FileNotFoundError:
        print("❌ LibreOffice no encontrado en el sistema")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout verificando LibreOffice")
        return False
    except Exception as e:
        print(f"❌ Error verificando LibreOffice: {e}")
        return False

if __name__ == "__main__":
    print(f"Fecha y hora: {datetime.now()}")
    
    # Verificar instalación
    if not check_libreoffice_installation():
        print("\n❌ NO SE PUEDE CONTINUAR: LibreOffice no está disponible")
        sys.exit(1)
    
    print()
    
    # Probar conversión
    if test_libreoffice_conversion():
        print("\n✅ PRUEBA EXITOSA: La conversión local funciona correctamente")
        sys.exit(0)
    else:
        print("\n❌ PRUEBA FALLIDA: La conversión local no funciona")
        sys.exit(1)
