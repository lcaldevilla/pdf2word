# Dockerfile para file2word con LibreOffice en Railway
# Basado en Ubuntu para tener LibreOffice disponible

# Usar Ubuntu 22.04 como base
FROM ubuntu:22.04

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Instalar todas las dependencias del sistema en una sola capa
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    software-properties-common \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    python3 \
    python3-pip \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo y directorios temporales con permisos
RUN mkdir -p /app /tmp /home/appuser/.cache

# Crear usuario no root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp

# Establecer el directorio de trabajo
WORKDIR /app

# Cambiar al usuario appuser
USER appuser

# Copiar requirements.txt y instalar dependencias Python
COPY --chown=appuser:appuser requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY --chown=appuser:appuser api/ /app/api/
COPY --chown=appuser:appuser railway.toml /app/

# Exponer el puerto
EXPOSE 3000

# Comando de inicio actualizado
CMD ["python", "-m", "uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "${PORT:-3000}"]
