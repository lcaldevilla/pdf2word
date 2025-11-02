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

def convert_with_self_hosted_server(pdf_content, pdf_filename):
    """
    Convierte un PDF a DOCX usando el servicio LibreOffice auto-alojado
    Retorna: (docx_content, download_info) donde download_info es None o un dict con info de descarga
    """
    from datetime import datetime
    
    # Obtener variables de entorno
    api_url = os.getenv("CONVERSION_API_URL")
    api_key = os.getenv("CONVERSION_API_KEY")
    max_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "25"))

    if not api_url:
        raise ValueError("Error: La variable de entorno CONVERSION_API_URL no esta configurada")
    
    if not api_key:
        raise ValueError("Error: La variable de entorno CONVERSION_API_KEY no esta configurada")
    
    headers = {"api-key": api_key}
    files = {'file': (pdf_filename, pdf_content, 'application/pdf')}
    
    # Calcular timeout dinámico
    timeout = calculate_timeout(pdf_content)
    
    # Determinar si usar conversión directa o almacenamiento temporal
    # Primero intentamos la conversión normal para ver el tamaño
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Iniciando conversión de {pdf_filename} (timeout: {timeout}s)")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Conectando a: {api_url}")
        
        # Medir tiempo de conexión específicamente
        connection_start = time.time()
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Enviando solicitud HTTP...")
        
        response = requests.post(api_url, files=files, headers=headers, timeout=timeout)
        
        connection_time = time.time() - connection_start
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Respuesta recibida en {connection_time:.2f}s")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Status Code: {response.status_code}")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Content-Length: {response.headers.get('content-length', 'N/A')}")
        
        response.raise_for_status()
        
        # Verificar si es una respuesta JSON (archivo grande) o archivo binario
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            # Es un archivo grande, nos devuelve información de descarga
            download_info = response.json()
            print(f"Archivo grande, proporcionando enlace de descarga: {download_info}")
            return None, download_info
        else:
            # Es un archivo directo, verificar tamaño
            expected_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            if expected_type not in content_type:
                print(f"Advertencia: Content-Type inesperado: {content_type}")
            
            docx_content = response.content
            
            if not docx_content:
                raise ValueError("El servidor devolvio una respuesta vacía")
            
            # Verificar tamaño
            file_size_mb = len(docx_content) / (1024 * 1024)
            print(f"Conversión directa exitosa. Tamaño DOCX: {file_size_mb:.2f} MB")
            
            if file_size_mb > max_size_mb:
                # Archivo muy grande, intentar almacenamiento temporal
                print(f"Archivo demasiado grande ({file_size_mb:.2f}MB > {max_size_mb}MB), intentando almacenamiento temporal")
                return convert_and_store_large_file(pdf_content, pdf_filename, api_url, api_key)
            
            return docx_content, None
        
    except requests.exceptions.Timeout:
        print(f"Timeout de {timeout} segundos alcanzado para {pdf_filename}")
        # En lugar de lanzar excepción, manejar amigablemente
        # Para esto necesitaríamos el email del destinatario, pero no lo tenemos aquí
        # Así que lanzamos una excepción más informativa
        raise Exception(f"El archivo {pdf_filename} esta tardando mas de {timeout} segundos en procesarse. Por favor, intenta de nuevo en unos minutos o considera comprimir el PDF antes de convertirlo.")
        
    except requests.exceptions.RequestException as e:
        # Capturar detalles específicos del error 422
        from datetime import datetime
        
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            content_type = e.response.headers.get('content-type', '')
            
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error HTTP {status_code}")
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Content-Type: {content_type}")
            
            try:
                if 'application/json' in content_type:
                    error_details = e.response.json()
                    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error JSON: {error_details}")
                    
                    # Si es error 422, dar detalles específicos
                    if status_code == 422:
                        detail = error_details.get('detail', str(error_details))
                        raise Exception(f"Error 422 del servidor: {detail}")
                    
                    raise Exception(f"Error del servidor {status_code}: {error_details}")
                else:
                    error_text = e.response.text
                    print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error texto: {error_text}")
                    
                    if status_code == 422:
                        raise Exception(f"Error 422 del servidor: {error_text}")
                    
                    raise Exception(f"Error del servidor {status_code}: {error_text}")
            except:
                error_text = e.response.text
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Error texto (fallback): {error_text[:200]}")
                
                if status_code == 422:
                    raise Exception(f"Error 422 del servidor: {error_text[:100]}")
                
                raise Exception(f"Error del servidor {status_code}: {error_text[:100]}")
        
        raise Exception(f"Error llamando al servicio de conversion: {e}")

def convert_and_store_large_file(pdf_content, pdf_filename, api_url, api_key):
    """
    Convierte y almacena un archivo grande usando el endpoint de almacenamiento temporal
    """
    headers = {"api-key": api_key}
    files = {'file': (pdf_filename, pdf_content, 'application/pdf')}
    
    # Usar el endpoint de almacenamiento temporal
    store_url = api_url.replace('/convert', '/convert-and-store')
    
    try:
        print(f"Enviando archivo grande a almacenamiento temporal: {store_url}")
        response = requests.post(store_url, files=files, headers=headers, timeout=180)
        response.raise_for_status()
        
        download_info = response.json()
        print(f"Archivo almacenado exitosamente: {download_info}")
        return None, download_info
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error almacenando archivo temporal: {e}")

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
        print("Iniciando conversión a DOCX con servicio externo...")
        
        # Medir tiempo de conversión
        conversion_start_time = time.time()
        
        try:
            docx_buffer, download_info = convert_with_self_hosted_server(file_buffer, sanitized_filename)
            conversion_end_time = time.time()
            conversion_duration = conversion_end_time - conversion_start_time
            
            print(f"Conversión completada en {conversion_duration:.2f} segundos.")
            
            # Log detallado del resultado
            if download_info:
                print(f"Resultado: Archivo grande - Enlace generado")
                print(f"Info: Tamaño={download_info.get('size_mb', 'N/A')}MB, Expira={download_info.get('expires_at', 'N/A')}")
            else:
                if docx_buffer:
                    docx_size = len(docx_buffer) / (1024 * 1024)
                    print(f"Resultado: Archivo pequeño - {docx_size:.2f}MB adjunto")
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
        
        if download_info:
            # Archivo grande - enviar enlace de descarga
            base_url = os.getenv("CONVERSION_API_URL", "").replace('/convert', '')
            download_url = f"{base_url}{download_info['download_url']}"
            expires_at = download_info['expires_at']
            size_mb = download_info['size_mb']
            
            message = Mail(
                from_email=SENDGRID_SENDER_EMAIL,
                to_emails=from_email,
                subject=f"Tu fichero convertido: {output_filename}",
                html_content=f"""
                <strong>Hola,</strong><br><br>
                Hemos convertido tu fichero <strong>{original_filename}</strong> a formato Word (.docx).<br><br>
                
                <strong>Información del archivo:</strong><br>
                • Nombre: {output_filename}<br>
                • Tamaño: {size_mb} MB<br>
                • Válido hasta: {expires_at}<br><br>
                
                El archivo es demasiado grande para enviarlo por email, pero puedes descargarlo desde el siguiente enlace:<br><br>
                
                <a href="{download_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Descargar Archivo</a><br><br>
                
                <small><em>Este enlace expirará en 24 horas por seguridad.</em></small>
                """
            )
        else:
            # Archivo pequeño - enviar adjunto directo
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
