#!/usr/bin/env python3
"""
Script para probar la construcción del Dockerfile localmente
"""
import subprocess
import sys
import os

def test_docker_build():
    """Probar la construcción del Dockerfile"""
    print("=== Prueba de construcción Docker ===")
    
    try:
        # Verificar que Dockerfile existe
        if not os.path.exists("Dockerfile"):
            print("❌ Error: Dockerfile no encontrado")
            return False
        
        print("✅ Dockerfile encontrado")
        
        # Verificar que railway.toml existe
        if not os.path.exists("railway.toml"):
            print("❌ Error: railway.toml no encontrado")
            return False
        
        print("✅ railway.toml encontrado")
        
        # Verificar que api/convert.py existe
        if not os.path.exists("api/convert.py"):
            print("❌ Error: api/convert.py no encontrado")
            return False
        
        print("✅ api/convert.py encontrado")
        
        # Verificar que requirements.txt existe
        if not os.path.exists("requirements.txt"):
            print("❌ Error: requirements.txt no encontrado")
            return False
        
        print("✅ requirements.txt encontrado")
        
        # Intentar construir la imagen Docker
        print("\nIntentando construir imagen Docker...")
        build_command = ["docker", "build", "-t", "file2word-test", "."]
        
        result = subprocess.run(
            build_command,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            print("✅ Construcción Docker exitosa")
            print(f"Salida: {result.stdout}")
            
            # Probar que la imagen se creó
            list_command = ["docker", "images", "file2word-test"]
            list_result = subprocess.run(list_command, capture_output=True, text=True)
            
            if "file2word-test" in list_result.stdout:
                print("✅ Imagen Docker creada correctamente")
                
                # Limpiar
                print("\nLimpiando imagen de prueba...")
                cleanup_command = ["docker", "rmi", "file2word-test"]
                cleanup_result = subprocess.run(cleanup_command, capture_output=True, text=True)
                
                if cleanup_result.returncode == 0:
                    print("✅ Imagen de prueba eliminada")
                    return True
                else:
                    print("⚠️  No se pudo eliminar la imagen de prueba")
                    return True
            else:
                print("❌ La imagen no se creó correctamente")
                return False
        else:
            print("❌ Error en construcción Docker")
            print(f"Return code: {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout en construcción Docker")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def check_docker_installation():
    """Verificar que Docker esté instalado"""
    print("=== Verificación de Docker ===")
    
    try:
        # Verificar Docker está instalado
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Docker instalado: {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker no instalado")
            return False
            
    except FileNotFoundError:
        print("❌ Docker no encontrado. Por favor instala Docker.")
        return False
    except Exception as e:
        print(f"❌ Error verificando Docker: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando prueba de construcción Docker para file2word\n")
    
    # Verificar Docker
    docker_ok = check_docker_installation()
    
    if not docker_ok:
        print("\n❌ No se puede continuar sin Docker instalado")
        return False
    
    # Probar construcción
    build_ok = test_docker_build()
    
    if build_ok:
        print("\n✅ ¡Prueba completada exitosamente!")
        print("   El Dockerfile está listo para Railway")
        return True
    else:
        print("\n❌ La prueba falló")
        print("   Revisa el Dockerfile y los archivos necesarios")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
