# api/convert.py
import os
import base64
import json
import email
import requests
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
def convert_with_self_hosted_server(pdf_content, pdf_filename):
    """
    Convierte un PDF a DOCX usando el servicio LibreOffice auto-alojado
    Retorna: (docx_content, download_info) donde download_info es None o un dict con info de descarga
    """
    # Obtener variables de entorno
    api_url = os.getenv("CONVERSION_API_URL")
    api_key = os.getenv("CONVERSION_API_KEY")
    max_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "25"))

    if not api_url:
        raise ValueError("Error: La variable de entorno CONVERSION_API_URL no está configurada")
    
    if not api_key:
        raise ValueError("Error: La variable de entorno CONVERSION_API_KEY no está configurada")
    
    headers = {"X-API-Key": api_key}
    files = {'file': (pdf_filename, pdf_content, 'application/pdf')}
    
    # Determinar si usar conversión directa o almacenamiento temporal
    # Primero intentamos la conversión normal para ver el tamaño
    try:
        print(f"Intentando conversión directa de {pdf_filename}")
        response = requests.post(api_url, files=files, headers=headers, timeout=120)
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
                raise ValueError("El servidor devolvió una respuesta vacía")
            
            # Verificar tamaño
            file_size_mb = len(docx_content) / (1024 * 1024)
            print(f"Conversión directa exitosa. Tamaño DOCX: {file_size_mb:.2f} MB")
            
            if file_size_mb > max_size_mb:
                # Archivo muy grande, intentar almacenamiento temporal
                print(f"Archivo demasiado grande ({file_size_mb:.2f}MB > {max_size_mb}MB), intentando almacenamiento temporal")
                return convert_and_store_large_file(pdf_content, pdf_filename, api_url, api_key)
            
            return docx_content, None
        
    except requests.exceptions.Timeout:
        raise Exception(f"Timeout llamando al servicio de conversión después de 120 segundos")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error llamando al servicio de conversión: {e}")

def convert_and_store_large_file(pdf_content, pdf_filename, api_url, api_key):
    """
    Convierte y almacena un archivo grande usando el endpoint de almacenamiento temporal
    """
    headers = {"X-API-Key": api_key}
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
        
        print(f"Procesando archivo: {original_filename}")

        # 2. VALIDACIÓN
        is_pdf = original_filename.lower().endswith('.pdf')
        wants_docx = 'word' in subject or 'docx' in subject

        print(f"Es PDF: {is_pdf}, Quiere DOCX: {wants_docx}")

        if not is_pdf or not wants_docx:
            print("El fichero no es un PDF o no se pidió conversión a Word. No se hace nada.")
            return PlainTextResponse("OK", status_code=200)

        # 3. CONVERSIÓN
        print("Iniciando conversión a DOCX con servicio externo...")
        docx_buffer, download_info = convert_with_self_hosted_server(file_buffer, original_filename)
        print("Conversión completada.")

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
