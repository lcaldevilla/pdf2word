# Usar una imagen oficial de Python como base
FROM python:3.9-slim

# Instalar dependencias del sistema operativo que necesita OpenCV
# libgl1-mesa-dri: El paquete moderno que proporciona libGL.so.1
# libglib2.0-0, libsm6, libxext6, libxrender-dev: Otras dependencias comunes de OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-dri libglib2.0-0 libsm6 libxext6 libxrender-dev

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