# Configuración de Gmail SMTP para file2word en Railway

Este documento explica cómo configurar Gmail SMTP como alternativa a SendGrid para enviar los emails con los archivos PDF convertidos en Railway.

## Requisitos previos

1. Una cuenta de Gmail personal
2. Acceso a la configuración de seguridad de tu cuenta de Google
3. Una cuenta de Railway para despliegue

## Pasos de configuración

### 1. Generar contraseña de aplicación en Google

1. Ve a tu cuenta de Google: [myaccount.google.com](https://myaccount.google.com)
2. Sección "Seguridad"
3. Busca "Contraseñas de aplicación"
4. Haz clic en "Contraseñas de aplicación"
5. Verifica tu identidad si es necesario
6. Selecciona "Otra (nombre personalizado)"
7. Dale un nombre como "file2word-railway"
8. Haz clic en "Generar"
9. Copia la contraseña generada (16 caracteres) - **¡Guárdala en un lugar seguro!**

### 2. Configurar variables de entorno en Railway

**¡Importante!** Railway no usa archivos .env. Las variables se configuran directamente en el panel de Railway:

1. Ve a tu proyecto en [Railway](https://railway.app)
2. Sección "Variables" (Variables de entorno)
3. Agrega las siguientes variables:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `GMAIL_EMAIL` | tu-gmail@ejemplo.com | Tu email de Gmail |
| `GMAIL_APP_PASSWORD` | contraseña-de-16-caracteres | Contraseña de aplicación de Google |

**Ejemplo:**
```
GMAIL_EMAIL: juan.perez@gmail.com
GMAIL_APP_PASSWORD: xhdf abcd ijkl mnop
```

### 3. Instalar dependencias

Las dependencias necesarias ya están en `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Probar la configuración en Railway

Puedes probar la configuración usando el endpoint de diagnóstico:

```bash
curl https://tu-servicio-railway.app/api/diagnose
```

O si tienes acceso a la consola de Railway, puedes ejecutar:

```bash
python test_gmail_smtp.py
```

## Consideraciones importantes

### Límites de Gmail

- **500 emails/día** para cuentas personales de Gmail
- **1000 emails/día** para cuentas de Google Workspace
- Si superas estos límites, Google bloqueará el envío temporalmente

### Seguridad

- **Nunca uses tu contraseña principal de Gmail** en la aplicación
- Siempre usa **contraseñas de aplicación** para mayor seguridad
- Si usas "Acceso a aplicaciones menos seguras", ten en cuenta que es menos seguro

### Errores comunes

#### Error de autenticación
```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
```
Solución:
- Verifica que la contraseña de aplicación sea correcta
- Asegúrate de que no haya espacios extra al copiarla
- Verifica que el email esté correcto

#### Error de conexión
```
smtplib.SMTPConnectError: (10060, 'Connection timed out')
```
Solución:
- Verifica tu conexión a internet
- Puede ser un problema de firewall o red
- Intenta más tarde

#### Error de límite de envío
```
smtplib.SMTPServerDisconnected: Connection unexpectedly closed
```
Solución:
- Has superado el límite de 500 emails/día
- Espera 24 horas antes de volver a enviar
- Considera usar una cuenta de Google Workspace

## Uso en producción

Para usar esta configuración en producción:

1. Configura las variables de entorno en tu servidor
2. Establece límites de envío en tu aplicación
3. Monitorea los envíos para no superar los límites
4. Considera alternativas como SendGrid si necesitas más volumen

## Solución de problemas

### Si el test falla:

1. Verifica que las variables de entorno estén configuradas correctamente
2. Confirma que la contraseña de aplicación sea válida
3. Revisa la configuración de seguridad de tu cuenta de Google
4. Verifica que no haya firelos bloqueando el puerto 587

### Si los emails no llegan:

1. Revisa la carpeta de spam en tu email
2. Verifica que el asunto y contenido no parezcan spam
3. Confirma que el email de remitente es válido
4. Prueba con diferentes destinatarios

## Alternativas

Si necesitas más volumen de envío, considera:

- **SendGrid**: 100 emails/día gratis
- **Mailgun**: 5000 emails/mes gratis
- **Amazon SES**: $0.10 por 1000 emails
- **Brevo (Sendinblue)**: 300 emails/día gratis

## Contacto

Si tienes problemas con la configuración, revisa:
1. La documentación oficial de Gmail sobre contraseñas de aplicación
2. Los logs de tu aplicación para ver mensajes de error específicos
