# Imagen base
FROM python:3.9-slim

# Instalar dependencias del sistema para OpenCV (headless)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \                 # ← ¡AQUÍ ESTÁ EL CAMBIO!
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copiar app
COPY . .

# Puerto
EXPOSE 8000

# Ejecutar
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]