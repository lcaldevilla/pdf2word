# Imagen base ligera
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt (para caché)
COPY requirements.txt .

# Instalar dependencias del sistema y LibreOffice completo
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-core \
    libreoffice-common \
    unoconv \
    python3-uno \
    libuno-cpp \
    libuno-sal \
    libuno-salhelper \
    libcups2 \
    libxinerama1 \
    libxrandr2 \
    libxrender1 \
    libxcb-randr0 \
    libxcb-xinerama0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Verificar instalación de LibreOffice
RUN soffice --version && libreoffice --version

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 8000

# Ejecutar la app
# Ejecutar con uvicorn, usando $PORT de Railway
CMD ["sh", "-c", "uvicorn api.convert:app --host 0.0.0.0 --port ${PORT:-8000}"]
