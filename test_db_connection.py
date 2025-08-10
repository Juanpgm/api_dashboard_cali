#!/usr/bin/env python3
"""
Test script para verificar la conexión a la base de datos
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== VERIFICACIÓN DE CONEXIÓN A BASE DE DATOS ===")
print()

# Mostrar variables de entorno
print("📋 Variables de entorno:")
print(f"   POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"   POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'No configurada'}")
print(f"   POSTGRES_SERVER: {os.getenv('POSTGRES_SERVER')}")
print(f"   POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
print(f"   POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
print()

try:
    # Intentar importar y probar conexión
    print("🔌 Probando conexión...")
    from fastapi_project.database import test_connection, get_database_info
    
    # Mostrar información de configuración
    db_info = get_database_info()
    print("📊 Configuración de base de datos:")
    for key, value in db_info.items():
        print(f"   {key}: {value}")
    print()
    
    # Probar conexión
    result = test_connection()
    
    if result:
        print("✅ ¡Conexión exitosa!")
    else:
        print("❌ Error de conexión")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    sys.exit(1)

print()
print("=== VERIFICACIÓN COMPLETADA ===")
