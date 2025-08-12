"""
Script de verificación de salud para monitoreo en producción.
Compatible con Render, Railway, Heroku y otras plataformas.
"""

import os
import sys
import requests
import time
from typing import Dict, Any

def check_api_health(base_url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Verifica el estado de salud de la API.
    
    Args:
        base_url: URL base de la API (ej: https://mi-api.onrender.com)
        timeout: Tiempo límite en segundos
    
    Returns:
        Dict con el resultado de la verificación
    """
    health_endpoint = f"{base_url}/health"
    
    try:
        print(f"🔍 Verificando salud de la API: {health_endpoint}")
        
        response = requests.get(health_endpoint, timeout=timeout)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API está funcionando correctamente")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Database: {health_data.get('database')}")
            return {
                "status": "healthy",
                "api_response": health_data,
                "response_time": response.elapsed.total_seconds()
            }
        else:
            print(f"⚠️ API respondió con código {response.status_code}")
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con la API: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

def check_database_status(base_url: str) -> Dict[str, Any]:
    """Verifica el estado de la base de datos a través de la API"""
    try:
        endpoint = f"{base_url}/database_status"
        response = requests.get(endpoint, timeout=30)
        
        if response.status_code == 200:
            db_stats = response.json()
            total_records = sum(
                table_info.get("records_count", 0) 
                for table_info in db_stats.get("database_stats", {}).values()
            )
            
            print(f"✅ Base de datos operativa")
            print(f"   Tablas: {len(db_stats.get('database_stats', {}))}")
            print(f"   Registros totales: {total_records:,}")
            
            return {
                "status": "healthy",
                "tables_count": len(db_stats.get("database_stats", {})),
                "total_records": total_records
            }
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

def main():
    """Función principal del health check"""
    
    # Obtener URL base desde variable de entorno o usar por defecto
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print("🏥 Iniciando verificación de salud del sistema...")
    print(f"🌐 URL base: {base_url}")
    print("=" * 50)
    
    # Verificar API
    api_health = check_api_health(base_url)
    
    # Verificar base de datos si la API está funcionando
    if api_health["status"] == "healthy":
        db_health = check_database_status(base_url)
    else:
        db_health = {"status": "not_checked", "reason": "API unhealthy"}
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SALUD DEL SISTEMA:")
    print(f"   🔌 API: {api_health['status'].upper()}")
    print(f"   🗄️  Database: {db_health['status'].upper()}")
    
    # Determinar código de salida
    if api_health["status"] == "healthy" and db_health["status"] == "healthy":
        print("✅ Sistema completamente operativo")
        sys.exit(0)
    else:
        print("❌ Sistema con problemas detectados")
        sys.exit(1)

if __name__ == "__main__":
    main()
