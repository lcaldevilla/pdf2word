#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Gmail SMTP
"""
import os
import smtplib
import sys

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv no instalado, usando variables de entorno del sistema")

# Obtener configuración
gmail_email = os.getenv('GMAIL_EMAIL')
gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')

def test_gmail_connection():
    """Probar conexión con Gmail SMTP"""
    print("=== Prueba de conexión Gmail SMTP ===")
    
    if not gmail_email:
        print("❌ Error: GMAIL_EMAIL no configurado")
        return False
    
    if not gmail_app_password:
        print("❌ Error: GMAIL_APP_PASSWORD no configurado")
        return False
    
    print(f"✅ Email configurado: {gmail_email}")
    print("Intentando conexión con Gmail SMTP...")
    
    try:
        # Conectar con Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_email, gmail_app_password)
        server.quit()
        
        print("✅ Conexión y autenticación exitosas")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación: {e}")
        print("   - Verifica tu email y contraseña de aplicación")
        print("   - Asegúrate de haber generado una contraseña de aplicación en Google")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Error de conexión: {e}")
        print("   - Verifica tu conexión a internet")
        print("   - Puede ser un problema de firewall o red")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_email_sending():
    """Probar envío de email"""
    print("\n=== Prueba de envío de email ===")
    
    if not test_gmail_connection():
        return False
    
    # Crear mensaje de prueba
    import email.mime.multipart
    import email.mime.text
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    msg = MIMEMultipart()
    msg['From'] = gmail_email
    msg['To'] = gmail_email  # Enviar a uno mismo para prueba
    msg['Subject'] = 'Prueba de envío desde file2word'
    
    body = """
    <h2>Prueba de envío de email</h2>
    <p>Este es un email de prueba desde el servicio file2word.</p>
    <p>Si recibes este email, la configuración de Gmail SMTP está funcionando correctamente.</p>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    print(f"Enviando email de prueba a {gmail_email}...")
    
    try:
        # Conectar y enviar
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_email, gmail_app_password)
        
        text = msg.as_string()
        server.sendmail(gmail_email, gmail_email, text)
        server.quit()
        
        print("✅ Email enviado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        return False

def check_environment():
    """Verificar entorno de ejecución"""
    print("=== Verificación de entorno ===")
    
    # Versión de Python
    print(f"Versión de Python: {sys.version}")
    
    # Módulos necesarios
    required_modules = ['smtplib', 'email.mime', 'email.mime.multipart', 'email.mime.text']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ Módulo {module} disponible")
        except ImportError:
            print(f"❌ Módulo {module} no disponible")
    
    # Variables de entorno
    print(f"\nVariables de entorno:")
    print(f"  GMAIL_EMAIL: {'Configurado' if gmail_email else 'No configurado'}")
    print(f"  GMAIL_APP_PASSWORD: {'Configurado' if gmail_app_password else 'No configurado'}")

if __name__ == "__main__":
    print("Iniciando prueba de configuración Gmail SMTP...\n")
    
    # Verificar entorno
    check_environment()
    
    # Probar conexión
    connection_ok = test_gmail_connection()
    
    # Probar envío si la conexión funciona
    if connection_ok:
        test_email_sending()
    
    print("\n=== Resumen ===")
    if connection_ok:
        print("✅ La configuración de Gmail SMTP está lista para usar")
        print("   Puedes ejecutar tu aplicación de conversión de PDF")
    else:
        print("❌ Hay problemas con la configuración de Gmail SMTP")
        print("   Verifica los pasos en .env.example")
