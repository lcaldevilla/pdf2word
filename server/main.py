import os
import subprocess
import tempfile
import uuid
import time
import shutil
from datetime import datetime, timedelta
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import FileResponse, JSONResponse

# --- CONFIGURACIÓN ---
# ¡CAMBIA ESTA CLAVE por una segura y larga!
API_KEY = "yW22q7[+4h0" 

# Configuración para almacenamiento temporal
TEMP_DIR = "temp_files"
MAX_FILE_SIZE_MB = 25  # Límite para envío directo por email
FILE_EXPIRY_HOURS = 24  # Tiempo de vida de los archivos temporales

# Crear directorio temporal si no existe
os.makedirs(TEMP_DIR, exist_ok=True)

app = FastAPI()

# Diccionario para rastrear archivos (en producción usar BD)
file_registry = {}

def cleanup_expired_files():
    """Eliminar archivos expirados"""
    current_time = datetime.now()
    expired_files = []
    
    for file_id, file_info in file_registry.items():
        if current_time > file_info['expires_at']:
            expired_files.append(file_id)
            try:
                os.remove(file_info['path'])
                print(f"Archivo expirado eliminado: {file_info['path']}")
            except Exception as e:
                print(f"Error eliminando archivo {file_info['path']}: {e}")
    
    # Limpiar registro
    for file_id in expired_files:
        del file_registry[file_id]

@app.get("/admin/cleanup")
async def manual_cleanup(api_key: str = Header(..., name="X-API-Key")):
    """Endpoint manual para limpieza de archivos expirados"""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clave de API inválida")
    
    cleanup_expired_files()
    return {"status": "Cleanup completed", "active_files": len(file_registry)}

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clave de API inválida")

@app.post("/convert")
async def convert_pdf_to_docx(
    file: UploadFile = File(...),
    # El nombre 'X-API-Key' es un estándar, pero puedes usar el que prefieras
    api_key: str = Header(..., name="X-API-Key") 
):
    # 1. Verificar la clave de API
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clave de API inválida")

    # 2. Validar el tipo de archivo
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # 3. Crear un directorio temporal para la conversión
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, file.filename)
        
        # Guardar el PDF subido
        with open(pdf_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 4. Ejecutar la conversión con LibreOffice
        try:
            command = [
                'libreoffice',
                '--headless',
                '--convert-to', 'docx',
                '--outdir', tmpdir,
                pdf_path
            ]
            process = subprocess.run(command, check=True, capture_output=True, text=True)

            # 5. Preparar el archivo DOCX para la respuesta
            base_name = os.path.splitext(file.filename)[0]
            docx_path = os.path.join(tmpdir, f"{base_name}.docx")

            if not os.path.exists(docx_path):
                raise HTTPException(status_code=500, detail="La conversión falló, no se encontró el archivo de salida.")

            # 6. Devolver el archivo convertido
            return FileResponse(
                path=docx_path,
                media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                filename=f"{base_name}.docx"
            )

        except subprocess.CalledProcessError as e:
            print(f"Error en LibreOffice: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"Error durante la conversión: {e.stderr}")

@app.post("/convert-and-store")
async def convert_and_store_pdf(
    file: UploadFile = File(...),
    api_key: str = Header(..., name="X-API-Key")
):
    """Convertir PDF a DOCX y almacenar temporalmente para archivos grandes"""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Clave de API inválida")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # Limpiar archivos expirados primero
    cleanup_expired_files()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, file.filename)
        
        # Guardar el PDF subido
        with open(pdf_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        try:
            command = [
                'libreoffice',
                '--headless',
                '--convert-to', 'docx',
                '--outdir', tmpdir,
                pdf_path
            ]
            process = subprocess.run(command, check=True, capture_output=True, text=True)

            base_name = os.path.splitext(file.filename)[0]
            docx_path = os.path.join(tmpdir, f"{base_name}.docx")

            if not os.path.exists(docx_path):
                raise HTTPException(status_code=500, detail="La conversión falló, no se encontró el archivo de salida.")

            # Verificar tamaño del archivo
            file_size_mb = os.path.getsize(docx_path) / (1024 * 1024)
            
            # Generar ID único y mover a almacenamiento temporal
            file_id = str(uuid.uuid4())
            temp_filename = f"{file_id}_{base_name}.docx"
            temp_path = os.path.join(TEMP_DIR, temp_filename)
            
            shutil.copy2(docx_path, temp_path)
            
            # Registrar archivo
            expires_at = datetime.now() + timedelta(hours=FILE_EXPIRY_HOURS)
            file_registry[file_id] = {
                'path': temp_path,
                'original_filename': f"{base_name}.docx",
                'size_mb': file_size_mb,
                'created_at': datetime.now(),
                'expires_at': expires_at
            }
            
            # Construir URL de descarga (asumiendo que el servidor corre en el mismo host)
            download_url = f"/download/{file_id}"
            
            return JSONResponse({
                "status": "success",
                "message": "Archivo convertido y almacenado temporalmente",
                "file_id": file_id,
                "download_url": download_url,
                "original_filename": f"{base_name}.docx",
                "size_mb": round(file_size_mb, 2),
                "expires_at": expires_at.isoformat()
            })

        except subprocess.CalledProcessError as e:
            print(f"Error en LibreOffice: {e.stderr}")
            raise HTTPException(status_code=500, detail=f"Error durante la conversión: {e.stderr}")

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Descargar archivo almacenado temporalmente"""
    if file_id not in file_registry:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o expirado")
    
    file_info = file_registry[file_id]
    
    # Verificar si el archivo ha expirado
    if datetime.now() > file_info['expires_at']:
        try:
            os.remove(file_info['path'])
        except:
            pass
        del file_registry[file_id]
        raise HTTPException(status_code=404, detail="Archivo expirado")
    
    # Verificar que el archivo existe físicamente
    if not os.path.exists(file_info['path']):
        del file_registry[file_id]
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=file_info['path'],
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=file_info['original_filename']
    )

@app.get("/")
def read_root():
    return {"status": "API de conversión de PDF a DOCX funcionando."}
