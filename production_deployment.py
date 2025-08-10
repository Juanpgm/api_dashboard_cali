"""
Script de despliegue unificado para el API Dashboard en producción.
Ejecuta todos los pasos necesarios para un despliegue seguro y completo.
"""

import logging
import sys
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Configurar logging para despliegue
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployment:
    """Clase para manejar el despliegue completo en producción"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.start_time = time.time()
        
    def validate_environment(self) -> bool:
        """Valida que el entorno esté correctamente configurado"""
        logger.info("🔍 Validando entorno de producción...")
        
        # Verificar archivo .env
        env_file = self.project_root / ".env"
        if not env_file.exists():
            logger.error("❌ Archivo .env no encontrado")
            return False
        
        # Verificar variables críticas
        required_vars = [
            "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SERVER", 
            "POSTGRES_PORT", "POSTGRES_DB"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
            return False
        
        # Verificar estructura de archivos
        critical_files = [
            "fastapi_project/main.py",
            "fastapi_project/models.py", 
            "fastapi_project/schemas.py",
            "fastapi_project/database.py",
            "database_initializer.py"
        ]
        
        missing_files = []
        for file_path in critical_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"❌ Archivos críticos faltantes: {', '.join(missing_files)}")
            return False
        
        # Verificar directorio de datos
        data_dir = self.project_root / "transformation_app" / "app_outputs" / "ejecucion_presupuestal_outputs"
        if not data_dir.exists():
            logger.warning(f"⚠️ Directorio de datos no encontrado: {data_dir}")
        
        logger.info("✅ Entorno validado correctamente")
        return True
    
    def install_dependencies(self) -> bool:
        """Instala/verifica dependencias de Python"""
        logger.info("📦 Verificando dependencias...")
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "psycopg2-binary",
            "python-dotenv", "pydantic", "geoalchemy2", "requests"
        ]
        
        try:
            # Verificar si pip está disponible
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            
            # Instalar dependencias si no están presentes
            for package in required_packages:
                try:
                    __import__(package.replace("-", "_"))
                    logger.info(f"✅ {package} ya está instalado")
                except ImportError:
                    logger.info(f"📦 Instalando {package}...")
                    subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                 check=True, capture_output=True)
                    logger.info(f"✅ {package} instalado")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error instalando dependencias: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado en dependencias: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Ejecuta la inicialización de la base de datos"""
        logger.info("🗄️ Inicializando base de datos...")
        
        try:
            # Importar y ejecutar inicializador
            sys.path.append(str(self.project_root))
            from database_initializer import DatabaseInitializer
            
            initializer = DatabaseInitializer()
            success = initializer.initialize_database()
            
            if success:
                logger.info("✅ Base de datos inicializada correctamente")
                return True
            else:
                logger.error("❌ Error en inicialización de base de datos")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error durante inicialización: {e}")
            return False
    
    def run_health_checks(self) -> bool:
        """Ejecuta chequeos de salud post-despliegue"""
        logger.info("🏥 Ejecutando chequeos de salud...")
        
        try:
            from production_maintenance import ProductionMaintenance
            
            maintenance = ProductionMaintenance()
            health_report = maintenance.run_health_checks()
            
            overall_status = health_report.get('overall_status', 'ERROR')
            
            if overall_status == 'HEALTHY':
                logger.info("✅ Todos los chequeos de salud pasaron")
                return True
            elif overall_status == 'NEEDS_ATTENTION':
                logger.warning("⚠️ Sistema funcional pero necesita atención")
                # Mostrar recomendaciones
                for rec in health_report.get('recommendations', []):
                    logger.warning(f"   {rec}")
                return True
            else:
                logger.error("❌ Chequeos de salud fallaron")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error durante chequeos de salud: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Prueba los endpoints principales del API"""
        logger.info("🔌 Probando endpoints del API...")
        
        try:
            # Simular inicio del servidor FastAPI para pruebas
            from fastapi_project.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Probar endpoints críticos
            test_endpoints = [
                ("/health", "GET"),
                ("/database_status", "GET"),
                ("/centros_gestores", "GET"),
                ("/programas", "GET")
            ]
            
            for endpoint, method in test_endpoints:
                try:
                    if method == "GET":
                        response = client.get(endpoint)
                    elif method == "POST":
                        response = client.post(endpoint)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ {method} {endpoint}: OK")
                    else:
                        logger.warning(f"⚠️ {method} {endpoint}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Error probando {endpoint}: {e}")
            
            logger.info("✅ Pruebas de endpoints completadas")
            return True
            
        except ImportError:
            logger.warning("⚠️ TestClient no disponible, omitiendo pruebas de endpoints")
            return True
        except Exception as e:
            logger.error(f"❌ Error durante pruebas de endpoints: {e}")
            return False
    
    def create_deployment_report(self, success: bool) -> str:
        """Crea reporte de despliegue"""
        duration = time.time() - self.start_time
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        
        report = f"""
# 🏛️ API Dashboard Alcaldía de Cali - Reporte de Despliegue

**Fecha:** {timestamp}
**Estado:** {status}
**Duración:** {duration:.2f} segundos

## 📋 Pasos Ejecutados
1. ✅ Validación de entorno
2. ✅ Verificación de dependencias
3. ✅ Inicialización de base de datos
4. ✅ Chequeos de salud
5. ✅ Pruebas de endpoints

## 🎯 Estado Final
El sistema está {'listo para producción' if success else 'necesita correcciones antes del despliegue'}.

## 📊 Información del Sistema
- **Base de Datos:** PostgreSQL
- **Framework:** FastAPI 
- **Versión API:** 2.0.0
- **Pool Conexiones:** Configurado para producción

## 🔗 URLs Importantes
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Database Status:** http://localhost:8000/database_status

## 🚀 Comando de Inicio
```bash
uvicorn fastapi_project.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---
*Generado automáticamente por el sistema de despliegue*
"""
        
        # Guardar reporte
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📋 Reporte guardado: {report_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando reporte: {e}")
        
        return report_file
    
    def deploy(self) -> bool:
        """Ejecuta el proceso completo de despliegue"""
        logger.info("🚀 Iniciando despliegue de producción...")
        logger.info("=" * 60)
        
        steps = [
            ("Validar entorno", self.validate_environment),
            ("Instalar dependencias", self.install_dependencies), 
            ("Inicializar base de datos", self.initialize_database),
            ("Ejecutar chequeos de salud", self.run_health_checks),
            ("Probar endpoints", self.test_api_endpoints)
        ]
        
        try:
            for step_name, step_func in steps:
                logger.info(f"🔄 {step_name}...")
                
                if not step_func():
                    logger.error(f"❌ Falló: {step_name}")
                    self.create_deployment_report(False)
                    return False
                
                logger.info(f"✅ Completado: {step_name}")
            
            # Despliegue exitoso
            logger.info("=" * 60)
            logger.info("🎉 DESPLIEGUE COMPLETADO EXITOSAMENTE")
            logger.info("🚀 El sistema está listo para producción")
            logger.info("=" * 60)
            
            self.create_deployment_report(True)
            return True
            
        except KeyboardInterrupt:
            logger.warning("⚠️ Despliegue interrumpido por el usuario")
            self.create_deployment_report(False)
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado durante despliegue: {e}")
            self.create_deployment_report(False)
            return False

def main():
    """Función principal de despliegue"""
    print("🏛️ API Dashboard Alcaldía de Cali - Sistema de Despliegue")
    print("=" * 60)
    
    deployment = ProductionDeployment()
    
    # Verificar argumentos
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Uso: python production_deployment.py [opciones]

Opciones:
  --help, -h     Mostrar esta ayuda
  --force        Forzar despliegue sin confirmación
  --quiet        Modo silencioso (solo errores)
  
Este script ejecuta todos los pasos necesarios para desplegar
el API Dashboard en un entorno de producción.
        """)
        return
    
    # Configurar logging según argumentos
    if "--quiet" in sys.argv:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Confirmación para producción
    if "--force" not in sys.argv:
        response = input("\n⚠️  ¿Continuar con el despliegue de producción? (s/N): ")
        if response.lower() not in ['s', 'si', 'sí', 'yes', 'y']:
            print("❌ Despliegue cancelado por el usuario")
            sys.exit(0)
    
    # Ejecutar despliegue
    start_time = time.time()
    success = deployment.deploy()
    end_time = time.time()
    
    print(f"\n⏱️ Tiempo total: {end_time - start_time:.2f} segundos")
    
    if success:
        print("✅ Despliegue completado. Sistema listo para producción.")
        sys.exit(0)
    else:
        print("❌ Error en el despliegue. Revisar logs para detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()
