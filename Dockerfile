# Usar la imagen slim, que es más ligera y rápida
FROM python:3.9-slim

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

# --- EL TRUCO ---
# Establecemos variables de entorno para forzar a OpenCV a funcionar en modo headless
# Esto evita que intente cargar librerías gráficas como libGL.so.1
ENV OPENCV_IO_ENABLE_OPENEXR=1
ENV DISPLAY=:99

# El comando para ejecutar la aplicación cuando el contenedor se inicie
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]