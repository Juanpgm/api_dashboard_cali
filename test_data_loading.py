"""
Script de prueba para verificar que la carga de datos funciona correctamente
después de la migración de columnas.
"""

import requests
import json
import time

def test_data_loading():
    """Prueba la carga de datos en los endpoints refactorizados"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Endpoints a probar
    endpoints = [
        "/centros_gestores",
        "/programas", 
        "/areas_funcionales",
        "/propositos",
        "/retos",
        "/movimientos_presupuestales",
        "/ejecucion_presupuestal"
    ]
    
    print("🚀 Iniciando pruebas de carga de datos...")
    print("=" * 50)
    
    # Primero verificar el health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Conexión a la base de datos verificada")
        else:
            print("❌ Error en conexión a la base de datos")
            return
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        return
    
    # Probar carga individual de cada endpoint
    for endpoint in endpoints:
        print(f"\n📊 Probando {endpoint}...")
        try:
            start_time = time.time()
            response = requests.post(f"{base_url}{endpoint}")
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {len(data)} registros cargados en {load_time:.2f}s")
            else:
                print(f"❌ {endpoint}: Error {response.status_code}")
                print(f"   Detalle: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ {endpoint}: Error de conexión - {e}")
    
    # Probar carga masiva
    print(f"\n🔄 Probando carga masiva...")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/load_all_data")
        load_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Carga masiva completada en {load_time:.2f}s")
            print(f"   Detalles: {json.dumps(data['details'], indent=2)}")
        else:
            print(f"❌ Carga masiva falló: {response.status_code}")
            print(f"   Detalle: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ Error en carga masiva: {e}")
    
    # Verificar estadísticas finales
    print(f"\n📈 Verificando estadísticas de la base de datos...")
    try:
        response = requests.get(f"{base_url}/database_status")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estadísticas de la base de datos:")
            for table, info in stats['database_stats'].items():
                print(f"   📊 {table}: {info['records_count']} registros")
        else:
            print(f"❌ Error al obtener estadísticas: {response.status_code}")
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")

if __name__ == "__main__":
    test_data_loading()
