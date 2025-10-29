# Imagen base ligera
FROM python:3.9-slim

# Instalar dependencias del sistema necesarias para OpenCV (headless)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (caché)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer puerto
EXPOSE 8000

# Ejecutar con uvicorn
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]