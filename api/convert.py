# api/convert.py
import os
import io
import base64
import json
import email
from email import policy
from email.message import EmailMessage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from pdf2docx import Converter
from fastapi import FastAPI, Request, Response, Form, File, UploadFile
from fastapi.responses import PlainTextResponse, JSONResponse

# --- CONFIGURACIÓN INICIAL ---
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_SENDER_EMAIL = os.environ.get("SENDGRID_SENDER_EMAIL")

# Crear la aplicación FastAPI
app = FastAPI()

# --- LÓGICA DE CONVERSIÓN ---
def convertir_pdf_a_docx_en_memoria(pdf_bytes: bytes) -> bytes:
    print(f"Iniciando conversión, tamaño del PDF: {len(pdf_bytes)} bytes")
    
    # Crear el stream para el PDF y asegurar que el puntero está al inicio
    pdf_stream = io.BytesIO(pdf_bytes)
    pdf_stream.seek(0)  # Asegurar que el puntero está al inicio
    
    docx_stream = io.BytesIO()
    try:
        print("Creando converter...")
        cv = Converter(pdf_stream)
        print("Iniciando conversión...")
        cv.convert(docx_stream)
        cv.close()
        
        # Asegurar que el puntero del stream de salida esté al inicio
        docx_stream.seek(0)
        docx_bytes = docx_stream.getvalue()
        
        print(f"Conversión completada, tamaño del DOCX: {len(docx_bytes)} bytes")
        return docx_bytes
    except Exception as e:
        print(f"Error durante la conversión PDF a DOCX: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        pdf_stream.close()
        docx_stream.close()

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
        print("Iniciando conversión a DOCX...")
        docx_buffer = convertir_pdf_a_docx_en_memoria(file_buffer)
        print("Conversión completada.")

        # 4. ENVÍO DEL EMAIL DE RESPUESTA
        output_filename = f"{original_filename.split('.')[0]}.docx"
        
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

# ... (todo tu código existente) ...

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
