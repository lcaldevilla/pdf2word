# Usar una imagen oficial de Python como base
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar primero el archivo de dependencias para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que correrá la aplicación (FastAPI usa 8000 por defecto)
EXPOSE 8000

# El comando para ejecutar la aplicación cuando el contenedor se inicie
# Usaremos Uvicorn, un servidor ASGI para correr FastAPI
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "8000"]