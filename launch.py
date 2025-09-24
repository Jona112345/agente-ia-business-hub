"""
Sistema de Automatización Documental con IA
Script de inicio para el dashboard y API
"""
import os
import sys
import subprocess
import time
import threading
import webbrowser
from pathlib import Path

def print_banner():
    """Mostrar información del sistema"""
    print("\n" + "="*70)
    print("    SISTEMA DE AUTOMATIZACIÓN DOCUMENTAL CON IA")  
    print("    Desarrollado por Jonathan Ibáñez")
    print("    Versión 1.0.0")
    print("="*70 + "\n")

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro} detectado")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Se requiere Python 3.8 o superior")
        return False
    return True

def check_dependencies():
    """Verificar dependencias críticas"""
    print("Verificando dependencias del sistema...")
    
    required = {
        'streamlit': 'Dashboard web',
        'fastapi': 'API REST', 
        'uvicorn': 'Servidor ASGI',
        'pandas': 'Análisis de datos',
        'requests': 'HTTP requests'
    }
    
    missing = []
    installed = []
    
    for package, desc in required.items():
        try:
            __import__(package)
            installed.append(f"OK  {package} - {desc}")
        except ImportError:
            missing.append(package)
            installed.append(f"FALTA  {package} - {desc}")
    
    for item in installed:
        print(f"  {item}")
    
    if missing:
        print(f"\nInstalando dependencias faltantes: {', '.join(missing)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade'
            ] + missing)
            print("Dependencias instaladas correctamente")
        except subprocess.CalledProcessError as e:
            print(f"Error instalando dependencias: {e}")
            return False
    
    return True

def find_dashboard_file():
    """Encontrar archivo del dashboard"""
    possible_files = [
        'src/dashboard/app.py',
        'enhanced_dashboard.py',
        'dashboard.py', 
        'main_dashboard.py',
        'app.py'
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            print(f"Dashboard encontrado: {file_path}")
            return file_path
    
    print("ERROR: No se encontró archivo de dashboard")
    print("Archivos buscados:", possible_files)
    return None

def find_api_file():
    """Encontrar archivo de la API"""
    possible_files = [
        'src/api/main.py',
        'api/main.py',
        'main_api.py',
        'api.py'
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            print(f"API encontrada: {file_path}")
            return file_path
    
    print("AVISO: No se encontró archivo de API (opcional)")
    return None

def create_env_file():
    """Crear archivo .env básico"""
    if os.path.exists('.env'):
        print("Archivo .env ya existe")
        return
    
    print("Creando archivo .env...")
    
    env_content = """# Configuración Sistema Automatización IA

# Configuración Web
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8501
API_HOST=127.0.0.1
API_PORT=8000

# Configuración IA
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.1
OPENAI_API_KEY=sk-opcional-para-gpt

# Archivos
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# Sistema
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Dashboard
PROJECT_NAME=Sistema de Automatización IA
VERSION=1.0.0
DESCRIPTION=Sistema de automatización documental con inteligencia artificial
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("Archivo .env creado exitosamente")
    except Exception as e:
        print(f"Error creando .env: {e}")

def run_dashboard_only():
    """Ejecutar solo el dashboard"""
    dashboard_file = find_dashboard_file()
    
    if not dashboard_file:
        print("\nERROR: No se puede ejecutar sin archivo de dashboard")
        print("Asegúrate de tener el archivo del dashboard en tu directorio")
        return False
    
    print(f"\nEjecutando Dashboard: {dashboard_file}")
    print("URL: http://localhost:8501")
    print("Presiona Ctrl+C para detener\n")
    
    # Abrir navegador después de 3 segundos
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open('http://localhost:8501')
            print("Navegador abierto automáticamente")
        except:
            pass
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Ejecutar Streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            dashboard_file,
            '--server.port', '8501',
            '--server.address', '127.0.0.1',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ])
        return True
    except KeyboardInterrupt:
        print("\nDashboard detenido por el usuario")
        return True
    except Exception as e:
        print(f"Error ejecutando dashboard: {e}")
        return False

def run_api_only():
    """Ejecutar solo la API"""
    api_file = find_api_file()
    
    if not api_file:
        print("ERROR: No se encontró archivo de API")
        return False
    
    # Convertir ruta a módulo para uvicorn
    if api_file == 'src/api/main.py':
        module_path = 'src.api.main:app'
    else:
        module_path = api_file.replace('.py', '').replace('/', '.').replace('\\', '.') + ':app'
    
    print(f"\nEjecutando API: {api_file}")
    print("Documentación: http://localhost:8000/docs")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            module_path,
            '--host', '127.0.0.1',
            '--port', '8000',
            '--reload'
        ])
        return True
    except KeyboardInterrupt:
        print("\nAPI detenida por el usuario")
        return True
    except Exception as e:
        print(f"Error ejecutando API: {e}")
        return False

def run_full_system():
    """Ejecutar sistema completo (API + Dashboard)"""
    api_file = find_api_file()
    dashboard_file = find_dashboard_file()
    
    if not dashboard_file:
        print("ERROR: No se puede ejecutar sin dashboard")
        return False
    
    print("\nEjecutando sistema completo...")
    print("Dashboard: http://localhost:8501")
    
    if api_file:
        print("API: http://localhost:8000/docs")
        
        # Ejecutar API en hilo separado
        def run_api():
            if api_file == 'src/api/main.py':
                module_path = 'src.api.main:app'
            else:
                module_path = api_file.replace('.py', '').replace('/', '.').replace('\\', '.') + ':app'
                
            subprocess.run([
                sys.executable, '-m', 'uvicorn',
                module_path,
                '--host', '127.0.0.1',
                '--port', '8000',
                '--reload'
            ])
        
        api_thread = threading.Thread(target=run_api, daemon=True)
        api_thread.start()
        time.sleep(2)  # Dar tiempo a la API para iniciar
    
    # Ejecutar dashboard en hilo principal
    return run_dashboard_only()

def main():
    """Función principal"""
    print_banner()
    
    # Verificaciones básicas
    if not check_python_version():
        return
    
    if not check_dependencies():
        print("\nError: Faltan dependencias críticas")
        return
    
    create_env_file()
    
    print("\nSelecciona una opción:")
    print("1. Solo Dashboard (Recomendado para empezar)")
    print("2. Sistema Completo (Dashboard + API)")
    print("3. Solo API")
    print("4. Abrir URLs en navegador")
    print("5. Salir")
    
    while True:
        try:
            choice = input("\nSelecciona opción (1-5): ").strip()
            
            if choice == '1':
                run_dashboard_only()
                break
            elif choice == '2':
                run_full_system()
                break
            elif choice == '3':
                run_api_only()
                break
            elif choice == '4':
                print("\nAbriendo URLs en navegador...")
                webbrowser.open('http://localhost:8501')
                webbrowser.open('http://localhost:8000/docs')
                break
            elif choice == '5':
                print("Saliendo del programa...")
                break
            else:
                print("Opción inválida, intenta de nuevo")
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError inesperado: {e}")
        print("\nPuedes ejecutar manualmente:")
        print("   streamlit run src/dashboard/app.py")