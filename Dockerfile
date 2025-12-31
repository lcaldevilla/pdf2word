# Dockerfile para file2word con pdf2docx en Railway
# Basado en Ubuntu 22.04

# Usar Ubuntu 22.04 como base
FROM ubuntu:22.04

# Configurar variables de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (más ligero sin LibreOffice)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    wget \
    gnupg \
    software-properties-common \
    python3 \
    python3-pip \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y wheel para evitar problemas de compatibilidad
RUN pip3 install --upgrade pip setuptools wheel

# Crear directorio de trabajo y directorios temporales con permisos
RUN mkdir -p /app /tmp /home/appuser/.cache

# Copiar requirements.txt antes de cambiar usuario para poder instalar como root
COPY requirements.txt .

# Instalar dependencias Python como ROOT para evitar problemas de permisos
RUN pip3 install --no-cache-dir -r requirements.txt

# Crear usuario no root para seguridad
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp /home/appuser

# Establecer el directorio de trabajo
WORKDIR /app

# Cambiar al usuario appuser
USER appuser

# Copiar el código de la aplicación (el código ya tiene permisos de appuser)
COPY --chown=appuser:appuser api/ /app/api/
COPY --chown=appuser:appuser railway.toml /app/

# Exponer el puerto
EXPOSE 3000

# Comando de inicio actualizado
CMD ["python3", "-m", "uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "${PORT:-3000}"]
