# Mejoras aplicadas al Dockerfile

Este documento detalla las mejoras realizadas al Dockerfile para resolver errores en Railway.

## Problemas identificados

### 1. CMD usaba uvicorn directamente
**Problema:**
```dockerfile
CMD ["uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "3000"]
```
- Contradecía el cambio en railway.toml para usar `python -m uvicorn`
- Railway podría ignorar el startCommand de railway.toml

**Solución:**
```dockerfile
CMD ["python", "-m", "uvicorn", "api.convert:app", "--host", "0.0.0.0", "--port", "${PORT:-3000}"]
```
- Usa `python -m uvicorn` para consistencia
- Compatible tanto con Railway como local

### 2. Puerto hardcodeado
**Problema:**
```dockerfile
"--port", "3000"
```
- Railway usa variable de entorno `$PORT` dinámica
- El puerto 3000 podría no ser el correcto

**Solución:**
```dockerfile
"--port", "${PORT:-3000}"
```
- Usa variable de entorno de Railway
- Valor por defecto 3000 para desarrollo local

### 3. Faltaban dependencias para python-magic
**Problema:**
- `python-magic` requiere librerías del sistema adicionales en Ubuntu
- Podría fallar durante la instalación de requirements.txt

**Solución:**
```dockerfile
libmagic1 \
file \
```
- Agrega libmagic1 y file para soporte de python-magic
- Garantiza que la instalación de dependencias Python funcione

### 4. Problemas de permisos con appuser
**Problema:**
- LibreOffice podría tener problemas ejecutándose como usuario no root
- Faltaban directorios temporales necesarios

**Solución:**
```dockerfile
RUN mkdir -p /app /tmp /home/appuser/.cache
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /tmp
```
- Crea directorios temporales con permisos apropiados
- Asegura que appuser pueda escribir en /tmp
- Agrega directorio de cache para Python

### 5. Optimización de capas
**Problema:**
- Varias llamadas a apt-get en capas separadas
- Aumenta el tamaño de la imagen
- Hace la construcción más lenta

**Solución:**
```dockerfile
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
```
- Combina todas las instalaciones en una sola capa
- Reduce el tamaño de la imagen
- Mejora la velocidad de construcción

## Mejoras adicionales

### PYTHONUNBUFFERED=1
```dockerfile
ENV PYTHONUNBUFFERED=1
```
- Muestra la salida de Python inmediatamente
- Mejora el debugging en Railway
- No pierde mensajes de log en buffering

### COPY con chown
```dockerfile
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser api/ /app/api/
COPY --chown=appuser:appuser railway.toml /app/
```
- Asegura que los archivos copiados tengan permisos correctos
- Evita problemas de permisos en tiempo de ejecución

## Resumen de mejoras

✅ **Consistencia entre Dockerfile y railway.toml**
- Ambos usan `python -m uvicorn`
- Menos confusión y errores

✅ **Soporte para puerto dinámico**
- Funciona en Railway con cualquier puerto
- Valor por defecto para desarrollo local

✅ **Dependencias completas**
- python-magic funcionará correctamente
- Todas las librerías del sistema necesarias

✅ **Permisos correctos**
- LibreOffice puede ejecutarse como appuser
- Directorios temporales disponibles con permisos

✅ **Optimización de imagen**
- Menor tamaño de imagen
- Construcción más rápida
- Mejor caché de capas

✅ **Mejor debugging**
- Salida de Python inmediata
- Logs más claros en Railway

## Pruebas recomendadas

### 1. Construcción local (si tienes Docker)
```bash
python test_docker_build.py
```

### 2. Prueba en Railway
```bash
curl https://tu-servicio-railway.app/api/diagnose
```

### 3. Prueba de conversión
- Enviar un PDF pequeño
- Verificar que la conversión funcione
- Confirmar que el email se envíe correctamente

## Resultado esperado

Con estas mejoras, el Dockerfile debería:
- Construir sin errores
- Ejecutar correctamente en Railway
- Tener todas las dependencias necesarias
- Funcionar con LibreOffice sin problemas de permisos
- Ser más eficiente y mantenible
