# api/convert.py
import os
import base64
import json
import email
import requests
import time
import re
from email import policy
from email.message import EmailMessage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from fastapi import FastAPI, Request, Response, Form, File, UploadFile
from fastapi.responses import PlainTextResponse, JSONResponse

# --- CONFIGURACIÓN INICIAL ---
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_SENDER_EMAIL = os.environ.get("SENDGRID_SENDER_EMAIL")

# Crear la aplicación FastAPI
app = FastAPI()

# --- LÓGICA DE CONVERSIÓN ---
def calculate_timeout(pdf_content):
    """Calcula timeout dinámico basado en el tamaño del PDF"""
    import time
    start_time = time.time()
    
    pdf_size_mb = len(pdf_content) / (1024 * 1024)
    
    # Timeout dinámico según tamaño del PDF
    if pdf_size_mb > 10:
        timeout = 600  # 10 minutos para PDFs muy grandes
        print(f"PDF grande ({pdf_size_mb:.2f}MB), usando timeout de {timeout} segundos")
    elif pdf_size_mb > 5:
        timeout = 300  # 5 minutos para PDFs medianos
        print(f"PDF mediano ({pdf_size_mb:.2f}MB), usando timeout de {timeout} segundos")
    elif pdf_size_mb > 2:
        timeout = 180  # 3 minutos para PDFs pequeños
        print(f"PDF pequeño ({pdf_size_mb:.2f}MB), usando timeout de {timeout} segundos")
    else:
        timeout = 120  # 2 minutos para PDFs muy pequeños
        print(f"PDF muy pequeño ({pdf_size_mb:.2f}MB), usando timeout de {timeout} segundos")
    
    return timeout

def sanitize_filename(filename):
    """Limpia el nombre de archivo para evitar problemas con caracteres especiales"""
    # Extraer nombre base y extensión
    name, ext = os.path.splitext(filename)
    
    # Reemplazar caracteres problemáticos con guiones bajos
    # Permitir solo letras, números, guiones, guiones bajos y puntos
    cleaned_name = re.sub(r'[^\w\-_\.]', '_', name)
    
    # Limitar longitud del nombre (sin extensión)
    if len(cleaned_name) > 45:
        cleaned_name = cleaned_name[:45]
    
    # Reconstruir filename con extensión original
    cleaned_filename = cleaned_name + ext
    
    # Si después de la limpieza queda vacío, usar un nombre por defecto
    if not cleaned_name or cleaned_name.isspace():
        cleaned_filename = "document" + ext
    
    print(f"Nombre de archivo sanitizado: '{filename}' → '{cleaned_filename}'")
    return cleaned_filename

def handle_conversion_timeout(pdf_filename, from_email, timeout_used):
    """Maneja el caso cuando una conversión tarda demasiado tiempo"""
    try:
        message = Mail(
            from_email=SENDGRID_SENDER_EMAIL,
            to_emails=from_email,
            subject=f"Tu fichero esta tardando mucho: {pdf_filename}",
            html_content=f"""
            <strong>Hola,</strong><br><br>
            Tu fichero <strong>{pdf_filename}</strong> esta tardando mas tiempo de lo habitual en procesarse.<br><br>
            
            <strong>Informacion del proceso:</strong><br>
            • Archivo: {pdf_filename}<br>
            • Tiempo maximo esperado: {timeout_used} segundos<br>
            • Estado: En proceso (background)<br><br>
            
            <strong>Posibles razones:</strong><br>
            • El PDF es muy grande o complejo<br>
            • Contiene muchas imagenes o graficos complejos<br>
            • Hay alta demanda en el sistema<br><br>
            
            <strong>Que puedes hacer:</strong><br>
            1. Espera unos minutos y recibiras un email cuando termine<br>
            2. Si no recibes nada en 30 minutos, envia el PDF de nuevo<br>
            3. Para PDFs muy grandes, considera comprimirlos primero<br><br>
            
            <small><em>El archivo seguira procesandose en segundo plano. No necesitas hacer nada mas.</em></small>
            """
        )
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email de timeout enviado! Status code: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"Error enviando email de timeout: {e}")
        return False

def convert_pdf_to_docx_with_libreoffice(pdf_path, temp_dir, pdf_filename, timeout):
    """Intenta convertir PDF a DOCX usando LibreOffice/soffice con múltiples filtros"""
    import subprocess
    from datetime import datetime
    
    # Determinar nombre del archivo de salida
    output_filename = pdf_filename.replace('.pdf', '.docx')
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Intentando conversión con LibreOffice/soffice")
    
    # Estrategia 1: Filtro DOCX estándar
    commands_to_try = [
        {
            'name': 'DOCX estándar',
            'command': [
                'soffice',
                '--headless',
                '--writer',
                '--convert-to', 'docx',
                '--outdir', temp_dir,
                pdf_path
            ]
        },
        {
            'name': 'DOCX MS Word 2007',
            'command': [
                'soffice',
                '--headless',
                '--writer',
                '--convert-to', 'docx:MS Word 2007 XML',
                '--outdir', temp_dir,
                pdf_path
            ]
        },
        {
            'name': 'DOCX OOXML',
            'command': [
                'soffice',
                '--headless',
                '--writer',
                '--convert-to', 'docx:OpenDocument Text Flat XML',
                '--outdir', temp_dir,
                pdf_path
            ]
        }
    ]
    
    for cmd_info in commands_to_try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Probando con filtro: {cmd_info['name']}")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Ejecutando: {' '.join(cmd_info['command'])}")
        
        try:
            result = subprocess.run(
                cmd_info['command'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Return code: {result.returncode}")
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STDOUT: {result.stdout}")
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STDERR: {result.stderr}")
            
            # Verificar si es éxito o error de filtro
            if result.returncode == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ✅ Éxito con filtro: {cmd_info['name']}")
                return True
            elif "no export filter" in result.stderr.lower():
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Filtro no disponible: {cmd_info['name']}")
                continue  # Intentar siguiente filtro
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Error con filtro: {cmd_info['name']}")
                continue  # Intentar siguiente filtro
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Error ejecutando filtro {cmd_info['name']}: {e}")
            continue
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ❌ Todos los filtros LibreOffice fallaron")
    return False

def convert_pdf_to_docx_with_unoconv(pdf_path, temp_dir, pdf_filename, timeout):
    """Intenta convertir PDF a DOCX usando unoconv como fallback"""
    import subprocess
    from datetime import datetime
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Intentando conversión con unoconv (fallback)")
    
    # Comando con unoconv
    command = [
        'unoconv',
        '-f', 'docx',
        '-o', temp_dir,
        pdf_path
    ]
    
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Ejecutando: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Return code: {result.returncode}")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STDOUT: {result.stdout}")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] STDERR: {result.stderr}")
        
        if result.returncode == 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error con unoconv: {e}")
        return False

def convert_pdf_to_docx_local(pdf_content, pdf_filename):
    """
    Convierte un PDF a DOCX usando LibreOffice con fallback a unoconv
    Retorna: (docx_content, download_info) donde download_info siempre es None (conversión local)
    """
    import subprocess
    import tempfile
    import os
    from datetime import datetime
    
    # Calcular timeout dinámico
    timeout = calculate_timeout(pdf_content)
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Iniciando conversión local de {pdf_filename} (timeout: {timeout}s)")
        
        # Crear directorio temporal
        with tempfile.TemporaryDirectory() as temp_dir:
            # Guardar PDF en archivo temporal
            pdf_path = os.path.join(temp_dir, pdf_filename)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] PDF guardado en: {pdf_path}")
            
            # Intentar conversión con múltiples métodos
            conversion_start = time.time()
            
            # Método 1: LibreOffice/soffice
            libreoffice_success = convert_pdf_to_docx_with_libreoffice(pdf_path, temp_dir, pdf_filename, timeout)
            
            # Método 2: Fallback a unoconv si LibreOffice falla
            if not libreoffice_success:
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] LibreOffice falló, intentando unoconv...")
                unoconv_success = convert_pdf_to_docx_with_unoconv(pdf_path, temp_dir, pdf_filename, timeout)
                
                if not unoconv_success:
                    raise Exception("Ambos métodos de conversión (LibreOffice y unoconv) fallaron")
            
            conversion_time = time.time() - conversion_start
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Conversión completada en {conversion_time:.2f}s")
            
            # Listar todos los archivos en el directorio para debugging
            all_files = os.listdir(temp_dir)
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Archivos en directorio temporal: {all_files}")
            
            # Buscar cualquier archivo DOCX generado
            docx_files = [f for f in all_files if f.lower().endswith('.docx')]
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Archivos DOCX encontrados: {docx_files}")
            
            # Si no encuentra .docx, buscar otros archivos que puedan ser DOCX
            if not docx_files:
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Buscando archivos alternativos...")
                alternative_files = [f for f in all_files if not f.endswith('.pdf')]
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Archivos alternativos: {alternative_files}")
                
                # Intentar renombrar archivos alternativos
                for alt_file in alternative_files:
                    alt_path = os.path.join(temp_dir, alt_file)
                    
                    try:
                        # Verificar si el archivo tiene contenido válido
                        with open(alt_path, 'rb') as f:
                            alt_content = f.read()
                        
                        # Si parece un DOCX (empieza con PK)
                        if alt_content.startswith(b'PK'):
                            if '.' not in alt_file:
                                new_name = alt_file + '.docx'
                            else:
                                base_name = os.path.splitext(alt_file)[0]
                                new_name = base_name + '.docx'
                            
                            new_path = os.path.join(temp_dir, new_name)
                            os.rename(alt_path, new_path)
                            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Renombrando '{alt_file}' a '{new_name}'")
                            docx_files = [new_name]
                            break
                    except Exception as e:
                        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error procesando archivo alternativo '{alt_file}': {e}")
            
            if not docx_files:
                # Último intento: usar cualquier archivo no-PDF
                non_pdf_files = [f for f in all_files if not f.endswith('.pdf')]
                if non_pdf_files:
                    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Usando último archivo disponible: {non_pdf_files[0]}")
                    docx_files = [non_pdf_files[0]]
                else:
                    raise Exception(f"No se encontró el archivo DOCX generado. Archivos en directorio: {all_files}")
            
            docx_path = os.path.join(temp_dir, docx_files[0])
            
            # Leer y validar el archivo DOCX generado
            with open(docx_path, 'rb') as f:
                docx_content = f.read()
            
            # Verificar que sea un DOCX válido
            if not docx_content.startswith(b'PK'):
                raise Exception(f"El archivo generado no es un DOCX válido (no empieza con PK)")
            
            # Verificar tamaño
            file_size_mb = len(docx_content) / (1024 * 1024)
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Conversión local exitosa. Tamaño DOCX: {file_size_mb:.2f} MB")
            
            return docx_content, None
        
    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Timeout de {timeout} segundos alcanzado para {pdf_filename}")
        raise Exception(f"El archivo {pdf_filename} esta tardando mas de {timeout} segundos en procesarse. Por favor, intenta de nuevo en unos minutos o considera comprimir el PDF antes de convertirlo.")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error en conversión local: {e}")
        raise Exception(f"Error en la conversión local: {e}")

# --- ENDPOINT DE LA API ---
@app.post("/api/convert")
async def handler(request: Request):
    try:
        print("Recibiendo solicitud de SendGrid...")
        
        # SendGrid envía los datos como multipart/form-data con el email MIME
        form = await request.form()
        print(f"Campos del formulario: {list(form.keys())}")
        
        # El email completo está en el campo 'email' o 'message' dependiendo de la configuración
        email_content = None
        for field_name in ['email', 'message', 'raw_message']:
            if field_name in form:
                email_content = form[field_name]
                print(f"Email encontrado en campo: {field_name}")
                break
        
        if not email_content:
            print("Error: No se encontró el contenido del email en el formulario")
            return JSONResponse({"error": "No email content found in form data"}, status_code=400)
        
        # Parsear el email MIME
        print("Parseando email MIME...")
        if isinstance(email_content, str):
            # Si es string, convertir a bytes
            email_bytes = email_content.encode('utf-8')
        else:
            # Si ya es bytes o UploadFile, leer el contenido
            if hasattr(email_content, 'read'):
                email_bytes = await email_content.read()
            else:
                email_bytes = email_content
        
        # Parsear el mensaje MIME
        msg = email.message_from_bytes(email_bytes, policy=policy.default)
        
        # Extraer información del email
        from_email = msg.get('From', '').strip()
        subject = msg.get('Subject', '').lower()
        
        print(f"Email de: {from_email}")
        print(f"Asunto: {subject}")
        
        # Validar datos básicos
        if not from_email:
            print("Error: No se encontró email remitente")
            return JSONResponse({"error": "No from email found"}, status_code=400)
        
        # Extraer archivos adjuntos
        pdf_attachments = []
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition', '')
            
            print(f"Parte encontrada - Content-Type: {content_type}, Content-Disposition: {content_disposition}")
            
            # Buscar archivos adjuntos PDF
            if 'attachment' in content_disposition and 'pdf' in content_type.lower():
                filename = part.get_filename()
                if filename and filename.lower().endswith('.pdf'):
                    file_content = part.get_payload(decode=True)
                    if file_content:
                        pdf_attachments.append({
                            'filename': filename,
                            'content': file_content,
                            'content_type': content_type
                        })
                        print(f"PDF adjunto encontrado: {filename}, tamaño: {len(file_content)} bytes")
        
        if not pdf_attachments:
            print("Error: No se encontraron archivos PDF adjuntos")
            return JSONResponse({"error": "No PDF attachments found"}, status_code=400)
        
        # Usar el primer PDF encontrado
        pdf_attachment = pdf_attachments[0]
        original_filename = pdf_attachment['filename']
        file_buffer = pdf_attachment['content']
        
        # Sanitizar el nombre del archivo para evitar problemas
        sanitized_filename = sanitize_filename(original_filename)
        
        print(f"Procesando archivo: {original_filename}")
        print(f"Nombre sanitizado: {sanitized_filename}")

        # 2. VALIDACIÓN
        is_pdf = original_filename.lower().endswith('.pdf')
        wants_docx = 'word' in subject or 'docx' in subject

        print(f"Es PDF: {is_pdf}, Quiere DOCX: {wants_docx}")

        if not is_pdf or not wants_docx:
            print("El fichero no es un PDF o no se pidió conversión a Word. No se hace nada.")
            return PlainTextResponse("OK", status_code=200)

        # 3. CONVERSIÓN
        print("Iniciando conversión a DOCX localmente con LibreOffice...")
        
        # Medir tiempo de conversión
        conversion_start_time = time.time()
        
        try:
            docx_buffer, download_info = convert_pdf_to_docx_local(file_buffer, sanitized_filename)
            conversion_end_time = time.time()
            conversion_duration = conversion_end_time - conversion_start_time
            
            print(f"Conversión completada en {conversion_duration:.2f} segundos.")
            
            # Log detallado del resultado
            if docx_buffer:
                docx_size = len(docx_buffer) / (1024 * 1024)
                print(f"Resultado: Conversión local exitosa - {docx_size:.2f}MB adjunto")
            else:
                print("Resultado: Error - No se generó archivo")
        except Exception as e:
            # Verificar si es un error de timeout
            error_msg = str(e)
            if "tardando mas de" in error_msg.lower() or "timeout" in error_msg.lower():
                print(f"Error de timeout detectado: {error_msg}")
                
                # Enviar email informativo de timeout
                timeout_sent = handle_conversion_timeout(original_filename, from_email, calculate_timeout(file_buffer))
                
                if timeout_sent:
                    print("Email de timeout enviado exitosamente")
                    return PlainTextResponse("Timeout handled", status_code=200)
                else:
                    print("Error enviando email de timeout")
                    return JSONResponse({"error": "Error sending timeout email"}, status_code=500)
            else:
                # Es otro tipo de error, propagarlo
                print(f"Error de conversión no manejado: {error_msg}")
                raise e

        # 4. ENVÍO DEL EMAIL DE RESPUESTA
        output_filename = f"{original_filename.split('.')[0]}.docx"
        
        # Archivo convertido - enviar adjunto directo
        message = Mail(
            from_email=SENDGRID_SENDER_EMAIL,
            to_emails=from_email,
            subject=f"Tu fichero convertido: {output_filename}",
            html_content=f"<strong>Hola,</strong><br>hemos convertido tu fichero <strong>{original_filename}</strong> a formato Word (.docx).<br>Puedes descargarlo adjunto en este correo."
        )

        encoded_file = base64.b64encode(docx_buffer).decode()
        attachment = Attachment(
            FileContent(encoded_file),
            FileName(output_filename),
            FileType('application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            Disposition('attachment')
        )
        message.attachment = attachment

        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"Email enviado! Status code: {response.status_code}")
        except Exception as e:
            print(f"Error al enviar email con SendGrid: {e}")
            return JSONResponse({"error": "Error sending email"}, status_code=500)

        return PlainTextResponse("OK", status_code=200)

    except Exception as e:
        print(f"Error general en el handler: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"Internal server error: {str(e)}"}, status_code=500)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/diagnose")
async def diagnose_environment():
    """Endpoint para diagnosticar el entorno de LibreOffice en Railway"""
    import subprocess
    import platform
    import os
    
    diagnosis = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "libreoffice": {},
        "dependencies": {},
        "test_conversion": {}
    }
    
    try:
        # Información del sistema
        diagnosis["system"] = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "working_directory": os.getcwd()
        }
        
        # Verificar instalación de LibreOffice
        try:
            result = subprocess.run(['soffice', '--version'], 
                                capture_output=True, text=True, timeout=10)
            diagnosis["libreoffice"]["soffice_version"] = result.stdout.strip()
            diagnosis["libreoffice"]["soffice_available"] = True
        except Exception as e:
            diagnosis["libreoffice"]["soffice_error"] = str(e)
            diagnosis["libreoffice"]["soffice_available"] = False
        
        try:
            result = subprocess.run(['libreoffice', '--version'], 
                                capture_output=True, text=True, timeout=10)
            diagnosis["libreoffice"]["libreoffice_version"] = result.stdout.strip()
            diagnosis["libreoffice"]["libreoffice_available"] = True
        except Exception as e:
            diagnosis["libreoffice"]["libreoffice_error"] = str(e)
            diagnosis["libreoffice"]["libreoffice_available"] = False
        
        # Verificar dependencias del sistema
        dependencies = ['file', 'python3', 'which', 'whereis']
        for dep in dependencies:
            try:
                result = subprocess.run(['which', dep] if platform.system() != 'Windows' else ['where', dep], 
                                   capture_output=True, text=True, timeout=5)
                diagnosis["dependencies"][dep] = {
                    "available": result.returncode == 0,
                    "path": result.stdout.strip() if result.returncode == 0 else None
                }
            except Exception as e:
                diagnosis["dependencies"][dep] = {
                    "available": False,
                    "error": str(e)
                }
        
        # Probar conversión simple
        try:
            import tempfile
            import base64
            
            # Crear PDF de prueba muy simple
            simple_pdf = b"""%PDF-1.1
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
(Test) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000173 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
249
%%EOF"""
            
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_path = os.path.join(temp_dir, "test.pdf")
                with open(pdf_path, 'wb') as f:
                    f.write(simple_pdf)
                
                command = [
                    'soffice',
                    '--headless',
                    '--writer',
                    '--convert-to', 'docx',
                    '--outdir', temp_dir,
                    pdf_path
                ]
                
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                
                files_after = os.listdir(temp_dir)
                docx_files = [f for f in files_after if f.endswith('.docx')]
                
                diagnosis["test_conversion"] = {
                    "success": len(docx_files) > 0,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "files_before": ["test.pdf"],
                    "files_after": files_after,
                    "docx_files": docx_files
                }
                
                if docx_files:
                    docx_path = os.path.join(temp_dir, docx_files[0])
                    with open(docx_path, 'rb') as f:
                        docx_content = f.read()
                    diagnosis["test_conversion"]["docx_size"] = len(docx_content)
                    diagnosis["test_conversion"]["docx_valid"] = docx_content.startswith(b'PK')
        
        except Exception as e:
            diagnosis["test_conversion"] = {
                "success": False,
                "error": str(e)
            }
        
    except Exception as e:
        diagnosis["error"] = str(e)
    
    return JSONResponse(diagnosis)

@app.post("/api/test-timeout")
async def test_timeout_handler():
    """Endpoint específico para probar el problema de timeout con el archivo problemático"""
    try:
        print("=== TEST TIMEOUT: Iniciando prueba manual ===")
        
        # Simular el archivo problemático "Manual de Usuario Touch Point.pdf"
        # Nota: Esto es solo para pruebas, necesitarías el archivo real
        test_filename = "Manual de Usuario Touch Point.pdf"
        
        # Crear un PDF de prueba simple (solo para simular el problema)
        test_pdf_content = b"%PDF-1.4\n%)\n1 0 obj\n<<\n/Length 1000\n>>\nstream\nBT\n/F1 12 Tf\n72 0 Td\n(Hello World) Tj\nET\nendstream\nendobj\n\ntrailer\n<<\n/Size 1000\n/Root 1 0 R\n>>\nstartxref\n123\n%%EOF"
        
        print(f"Simulando procesamiento de: {test_filename}")
        print(f"Tamaño del PDF de prueba: {len(test_pdf_content)} bytes")
        
        # Calcular timeout dinámico
        timeout = calculate_timeout(test_pdf_content)
        print(f"Timeout calculado: {timeout} segundos")
        
        # Simular la conversión (en realidad esto no llama al servicio externo)
        # Es solo para probar el flujo completo de la API
        conversion_time = min(timeout * 0.8, timeout - 10)  # Simular que tarda casi todo el timeout
        
        print(f"Simulando conversión que tardará: {conversion_time} segundos")
        
        # Esperar para simular el tiempo de procesamiento
        import asyncio
        await asyncio.sleep(min(conversion_time, 5))  # Max 5 segundos para no hacer esperar mucho
        
        if conversion_time >= timeout:
            print("SIMULACIÓN: Timeout alcanzado")
            raise Exception(f"El archivo {test_filename} esta tardando mas de {timeout} segundos en procesarse. Por favor, intenta de nuevo en unos minutos o considera comprimir el PDF antes de convertirlo.")
        
        # Simular respuesta exitosa
        result_info = {
            "test_file": test_filename,
            "timeout_used": timeout,
            "conversion_time": conversion_time,
            "pdf_size_mb": len(test_pdf_content) / (1024 * 1024),
            "status": "success"
        }
        
        print(f"SIMULACIÓN: Conversión exitosa simulada")
        return JSONResponse({
            "status": "test_completed",
            "message": f"Prueba de timeout completada para {test_filename}",
            "details": result_info
        })
        
    except Exception as e:
        print(f"Error en prueba de timeout: {e}")
        return JSONResponse({
            "status": "test_failed", 
            "error": str(e),
            "message": "Error en la simulación de timeout"
        }, status_code=500)

# Endpoint de prueba para depuración
@app.post("/api/debug")
async def debug_handler(request: Request):
    """Endpoint para depurar qué está recibiendo la API de SendGrid"""
    try:
        print("=== DEBUG: Recibiendo solicitud ===")
        
        # Mostrar headers
        headers = dict(request.headers)
        print(f"Headers: {headers}")
        
        # Mostrar content type
        content_type = request.headers.get('content-type', 'unknown')
        print(f"Content-Type: {content_type}")
        
        # Intentar parsear como form-data primero
        if 'multipart/form-data' in content_type:
            print("Parseando como multipart/form-data...")
            form = await request.form()
            print(f"Campos del formulario: {list(form.keys())}")
            
            for key, value in form.items():
                print(f"Campo '{key}': {type(value)}")
                if hasattr(value, 'filename'):
                    print(f"  - Filename: {value.filename}")
                    print(f"  - Content-Type: {value.content_type}")
                elif len(str(value)) < 200:
                    print(f"  - Valor: {value}")
                else:
                    print(f"  - Valor: [demasiado largo, longitud: {len(str(value))}]")
        
        # Intentar parsear como JSON
        elif 'application/json' in content_type:
            print("Parseando como JSON...")
            data = await request.json()
            print(f"Datos JSON: {json.dumps(data, indent=2)}")
        
        else:
            # Mostrar el cuerpo raw
            body = await request.body()
            print(f"Cuerpo raw (primeros 500 bytes): {body[:500]}")
        
        print("=== DEBUG: Fin de la solicitud ===")
        
        return JSONResponse({
            "status": "debug_complete",
            "content_type": content_type,
            "headers": dict(request.headers),
            "message": "Revisa los logs de Railway para ver los detalles completos"
        })
        
    except Exception as e:
        print(f"Error en debug: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
