# Configuración con Docker para Railway

Este documento explica cómo configurar file2word con Docker en Railway para resolver el problema de conexión con LibreOffice.

## Problema actual

El error 502 "connection dial timeout" ocurre porque Railway no tiene LibreOffice instalado en su entorno base. La solución es usar un contenedor Docker que incluya LibreOffice preinstalado.

## Solución con Docker

### 1. Dockerfile

He creado un Dockerfile que:
- Usa Ubuntu 22.04 como base
- Instala LibreOffice completo
- Configura Python y las dependencias necesarias
- Ejecuta la aplicación como usuario no root para seguridad

### 2. Configuración de Railway

El archivo `railway.toml` ha sido actualizado para:
- Usar Docker como tipo de build
- Mantener las variables de entorno para Gmail SMTP
- Configurar el puerto y comando de inicio

### 3. Despliegue en Railway

Para desplegar con Docker:

1. **Asegúrate de que el Dockerfile esté en la raíz del proyecto**
2. **Verifica que railway.toml use `type = "Docker"`**
3. **Configura las variables de entorno en Railway**:
   ```
   GMAIL_EMAIL: tu-email@gmail.com
   GMAIL_APP_PASSWORD: tu-contraseña-de-app
   ```

4. **Despliega la aplicación en Railway**

## Ventajas de esta solución

### ✅ **LibreOffice disponible**
- LibreOffice está completamente instalado y configurado
- Todos los filtros de conversión PDF a DOCX funcionarán

### ✅ **Recursos adecuados**
- Docker permite Railway asignar más recursos al contenedor
- El entorno aislado evita problemas de dependencias

### ✅ **Entorno consistente**
- Mismo entorno local y de producción
- Menos problemas de "funciona en mi máquina"

### ✅ **Seguridad**
- La aplicación se ejecuta como usuario no root
- Menos riesgo de vulnerabilidades

## Pruebas después del despliegue

Una vez desplegado, puedes probar:

### 1. **Endpoint de diagnóstico**
```bash
curl https://tu-servicio-railway.app/api/diagnose
```

Deberías ver:
- LibreOffice instalado y disponible
- Todas las dependencias del sistema presentes
- El test de conversión debería funcionar

### 2. **Prueba de conversión**
Envía un PDF pequeño para verificar:
- La conversión funciona correctamente
- El email se envía con Gmail SMTP
- El archivo DOCX adjunto se recibe correctamente

## Si el problema persiste

Si después de usar Docker aún tienes problemas:

### 1. **Revisa los logs de Railway**
- Los logs mostrarán si hay errores en la construcción del Docker
- Verifica los logs en tiempo real durante el despliegue

### 2. **Aumenta los recursos en Railway**
- Ve a la configuración de Railway
- Aumenta los límites de CPU y memoria
- Reinicia el servicio

### 3. **Prueba con PDFs más pequeños**
- Comienza con PDFs pequeños (< 2MB)
- Verifica que la conversión básica funciona
- Luego prueba con archivos más grandes

## Consideraciones adicionales

### Tiempo de construcción
- Docker puede tardar más en construir la primera vez
- Railway cacheará las capas para construcciones posteriores

### Uso de recursos
- Docker usará más recursos que el entorno base
- Monitoriza el uso en Railway para ajustar si es necesario

### Mantenimiento
- Actualiza el Dockerfile regularmente con seguridad
- Monitorea los logs para detectar problemas temprano

## Alternativas

Si Docker no funciona, considera:

1. **API externa**: Usar servicios como Google Docs API
2. **Worker separado**: Mover la conversión a un servicio dedicado
3. **Cola asíncrona**: Implementar un sistema de cola para procesamiento lento

Pero Docker debería resolver el problema actual de conexión con LibreOffice.
