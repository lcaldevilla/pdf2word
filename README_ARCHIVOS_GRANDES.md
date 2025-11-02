# Solución para Manejo de Archivos Grandes en Conversión PDF a DOCX

## Problema Resuelto

El error `HTTP Error 413: Request Entity Too Large` ocurría cuando SendGrid intentaba enviar emails con archivos DOCX adjuntos mayores a 25MB, que es el límite estándar de SendGrid.

## Solución Implementada

Se ha implementado un sistema dual que maneja automáticamente tanto archivos pequeños como grandes:

### 🔄 Flujo de Procesamiento

```
PDF → Conversión LibreOffice → 
  Si DOCX ≤25MB → Email con adjunto directo
  Si DOCX >25MB → Almacenar temporal → Generar enlace → Email con enlace
```

## Componentes de la Solución

### 1. **Servidor de Conversión (server/main.py)**

#### Nuevos Endpoints:

- **`POST /convert-and-store`**: Convierte PDF y almacena el DOCX temporalmente
- **`GET /download/{file_id}`**: Descarga archivos almacenados temporalmente
- **`GET /admin/cleanup`**: Limpieza manual de archivos expirados

#### Características:

- ✅ **Almacenamiento temporal** por 24 horas
- ✅ **IDs únicos** para seguridad
- ✅ **Limpieza automática** de archivos expirados
- ✅ **Validación de tamaño** y tipo de archivo

### 2. **API Principal (api/convert.py)**

#### Mejoras Implementadas:

- ✅ **Detección automática** de tamaño de archivo
- ✅ **Lógica dual** para manejo según tamaño
- ✅ **Emails personalizados** para cada caso
- ✅ **Manejo robusto de errores**

## Configuración

### Variables de Entorno Requeridas

```bash
# Servicio de conversión
CONVERSION_API_URL=http://lcfcloud.ddns.net:8000/convert
CONVERSION_API_KEY=tu-api-key-aqui
MAX_FILE_SIZE_MB=25

# SendGrid
SENDGRID_API_KEY=tu-sendgrid-api-key-aqui
SENDGRID_SENDER_EMAIL=tu-email@ejemplo.com
```

## Ejemplos de Emails Generados

### 📧 Email para Archivos Pequeños (≤25MB)

```
Asunto: Tu fichero convertido: documento.docx
Cuerpo: Hola, hemos convertido tu fichero documento.pdf a formato Word (.docx). 
        Puedes descargarlo adjunto en este correo.
Adjunto: documento.docx
```

### 📧 Email para Archivos Grandes (>25MB)

```
Asunto: Tu fichero convertido: documento.docx
Cuerpo: Hola, hemos convertido tu fichero documento.pdf a formato Word (.docx).

Información del archivo:
• Nombre: documento.docx
• Tamaño: 45.2 MB
• Válido hasta: 2025-01-03T07:30:00

El archivo es demasiado grande para enviarlo por email, pero puedes descargarlo 
desde el siguiente enlace:

[Descargar Archivo]

Este enlace expirará en 24 horas por seguridad.
```

## Estructura de Archivos

```
file2word/
├── api/
│   └── convert.py              # API principal con lógica dual
├── server/
│   └── main.py                # Servidor de conversión LibreOffice
├── temp_files/                # Directorio para almacenamiento temporal
├── .env.example              # Plantilla de variables de entorno
├── test_integration.py        # Script de pruebas
└── README_ARCHIVOS_GRANDES.md # Esta documentación
```

## Seguridad Implementada

### 🔒 Enlaces de Descarga

- **IDs únicos UUID**: Impiden adivinanzas
- **Expiración automática**: 24 horas por seguridad
- **Validación de existencia**: Verificación física del archivo
- **Limpieza programada**: Eliminación de archivos expirados

### 🛡️ Validaciones

- **API Key**: Requerida en todos los endpoints
- **Tipo de archivo**: Solo PDF permitidos
- **Tamaño máximo**: Configurable (default 25MB)
- **Content-Type**: Verificación estricta

## Pruebas

### Ejecutar Tests de Integración

```bash
# Asegúrate de tener un PDF de prueba
cp tu_documento.pdf test_document.pdf

# Ejecutar pruebas
python test_integration.py
```

### Casos de Prueba

1. **Conversión directa**: Archivos pequeños ≤25MB
2. **Almacenamiento temporal**: Archivos grandes >25MB
3. **Descarga de enlaces**: Verificar enlaces temporales
4. **Limpieza automática**: Eliminación de archivos expirados

## Monitoreo y Mantenimiento

### 📊 Logs Importantes

El sistema genera logs detallados para:

- ✅ Seguimiento de conversiones
- ✅ Tamaños de archivos procesados
- ✅ Enlaces generados y expirados
- ✅ Errores y excepciones

### 🧹 Mantenimiento

- **Limpieza automática**: Cada vez que se procesa un archivo grande
- **Limpieza manual**: Via endpoint `/admin/cleanup`
- **Monitorización**: Revisar logs regularmente

## Mejoras Futuras

### 🚀 Sugerencias

1. **Base de datos**: Reemplazar registro en memoria por Redis/PostgreSQL
2. **CDN**: Usar servicio de almacenamiento como AWS S3
3. **Compresión**: Implementar compresión ZIP para optimizar tamaño
4. **Dashboard**: Interfaz administrativa para monitoreo
5. **Analíticas**: Estadísticas de uso y rendimiento

## Resolución de Problemas

### ❌ Issues Comunes

1. **Error 413**: Resuelto con almacenamiento temporal
2. **Enlace expirado**: Usuario debe solicitar nueva conversión
3. **Archivo no encontrado**: Verificar ID o nueva conversión
4. **Timeout**: Ajustar timeout según tamaño de archivo

### 🛠️ Debugging

- Verificar logs del servidor de conversión
- Revisar variables de entorno
- Probar con script `test_integration.py`
- Validar conectividad entre servicios

---

## 🎉 Resultado Final

- ✅ **Sin errores 413**: Manejo automático de archivos grandes
- ✅ **Experiencia fluida**: Usuario recibe su archivo siempre
- ✅ **Seguridad**: Enlaces temporales y validaciones
- ✅ **Escalabilidad**: Sistema preparado para alto volumen
- ✅ **Mantenibilidad**: Código limpio y documentado

La solución garantiza que los usuarios siempre reciban sus archivos convertidos, sin importar el tamaño, manteniendo la seguridad y el rendimiento del sistema.
