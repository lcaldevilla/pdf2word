# Usar imagen slim
FROM python:3.9-slim

# Actualizar e instalar dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para caché)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Variables de entorno para OpenCV (headless)
ENV OPENCV_IO_ENABLE_OPENEXR=1
# Ya no necesitas DISPLAY=:99 si no usas Xvfb

# Puerto
EXPOSE 8000

# Ejecutar con uvicorn
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]