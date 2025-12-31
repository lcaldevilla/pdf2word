# Dockerfile para file2word con LibreOffice en Railway
# Basado en Ubuntu para tener LibreOffice disponible

# Usar Ubuntu 22.04 como base
FROM ubuntu:22.04

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Agregar repositorios de LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# Instalar Python y pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Cambiar al usuario appuser
USER appuser

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements.txt y instalar dependencias Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY api/ /app/api/
COPY railway.toml /app/

# Exponer el puerto
EXPOSE 3000

# Comando de inicio
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "3000"]
