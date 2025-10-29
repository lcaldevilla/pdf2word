# Usar una imagen oficial de Python como base
FROM python:3.9-slim

# Instalar un conjunto robusto de dependencias del sistema operativo para OpenCV
# Esta combinación cubre la mayoría de los requisitos de OpenCV en diferentes versiones de Debian
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar primero el archivo de dependencias para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que correrá la aplicación
EXPOSE 8000

# El comando para ejecutar la aplicación cuando el contenedor se inicie
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]