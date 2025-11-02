# Imagen base ligera
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt (para caché)
COPY requirements.txt .

# Instalar dependencias del sistema y LibreOffice completo con filtros
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-core \
    libreoffice-common \
    libreoffice-filter-bin \
    libreoffice-java-common \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación completa de LibreOffice
RUN soffice --version && echo "LibreOffice installation completed successfully"

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 8000

# Ejecutar la app
# Ejecutar con uvicorn, usando $PORT de Railway
CMD ["sh", "-c", "uvicorn api.convert:app --host 0.0.0.0 --port ${PORT:-8000}"]
