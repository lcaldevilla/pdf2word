# Imagen base ligera
FROM python:3.9-slim

# Instalar dependencias del sistema para OpenCV (headless)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt (para caché)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 8000

# Ejecutar la app
# Ejecutar con uvicorn, usando $PORT de Railway
CMD ["sh", "-c", "uvicorn api.convert:app --host 0.0.0.0 --port ${PORT:-8000}"]