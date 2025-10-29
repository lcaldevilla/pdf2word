# api/convert.py
import os
import io
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from pdf2docx import Converter
from fastapi import FastAPI, Request, Response, Form, File, UploadFile
from fastapi.responses import PlainTextResponse

# --- CONFIGURACIÓN INICIAL ---
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_SENDER_EMAIL = os.environ.get("SENDGRID_SENDER_EMAIL")

# Crear la aplicación FastAPI
app = FastAPI()

# --- LÓGICA DE CONVERSIÓN (sin cambios) ---
def convertir_pdf_a_docx_en_memoria(pdf_bytes: bytes) -> bytes:
    # ... (el código de esta función es exactamente el mismo que antes) ...
    pdf_stream = io.BytesIO(pdf_bytes)
    docx_stream = io.BytesIO()
    try:
        cv = Converter(pdf_stream)
        cv.convert(docx_stream)
        cv.close()
        docx_bytes = docx_stream.getvalue()
        return docx_bytes
    except Exception as e:
        print(f"Error durante la conversión PDF a DOCX: {e}")
        raise e
    finally:
        pdf_stream.close()
        docx_stream.close()

# --- ENDPOINT DE LA API ---
@app.post("/api/convert")
async def handler(request: Request):
    try:
        # FastAPI puede parsear el form-data de SendGrid automáticamente
        form = await request.form()
        
        from_email = form.get('from', '').strip()
        subject = form.get('subject', '').lower()
        
        # El fichero está en la clave 'file1'
        file_info = form.get('file1')
        if not file_info or not isinstance(file_info, UploadFile):
            return PlainTextResponse("No file found in request", status_code=400)

        original_filename = file_info.filename
        file_buffer = await file_info.read()

        print(f"Recibido: {original_filename} de {from_email}")

        # 2. VALIDACIÓN
        is_pdf = original_filename.lower().endswith('.pdf')
        wants_docx = 'word' in subject or 'docx' in subject

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
            return PlainTextResponse("Error sending email", status_code=500)

        return PlainTextResponse("OK", status_code=200)

    except Exception as e:
        print(f"Error general en el handler: {e}")
        return PlainTextResponse("Internal Server Error", status_code=500)