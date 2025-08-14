"""
Script para cargar datos desde archivos locales a PostgreSQL en Railway
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
from fastapi_project.database import SQLALCHEMY_DATABASE_URL, engine

# Directorios donde están los datos
INPUT_DIRS = [
    "transformation_app/app_outputs/contratos_secop_output",
    "transformation_app/app_outputs/ejecucion_presupuestal_outputs", 
    "transformation_app/app_outputs/seguimiento_pa_outputs",
    "transformation_app/app_outputs/unidades_proyecto_outputs"
]

def load_csv_to_table(csv_path: str, table_name: str, engine):
    """Carga un archivo CSV a una tabla específica"""
    try:
        if not os.path.exists(csv_path):
            logger.warning(f"📂 Archivo no encontrado: {csv_path}")
            return False
            
        # Leer CSV
        df = pd.read_csv(csv_path)
        logger.info(f"📊 {csv_path}: {len(df)} registros")
        
        if len(df) == 0:
            logger.warning(f"📂 Archivo vacío: {csv_path}")
            return False
        
        # Cargar a PostgreSQL
        df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
        logger.info(f"✅ {table_name}: {len(df)} registros cargados")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cargando {csv_path} a {table_name}: {e}")
        return False

def load_all_data():
    """Carga todos los datos disponibles"""
    logger.info("🚀 Iniciando carga de datos a PostgreSQL en Railway")
    logger.info("=" * 60)
    
    total_loaded = 0
    total_files = 0
    
    # Mapeo de archivos a tablas
    file_table_mapping = {
        # Ejecución presupuestal
        "movimientos_presupuestales_cleaned.csv": "movimientos_presupuestales",
        "ejecucion_presupuestal_cleaned.csv": "ejecucion_presupuestal",
        "datos_caracteristicos_proyectos_cleaned.csv": "datos_caracteristicos_proyectos",
        
        # Seguimiento PA
        "seguimiento_pa_cleaned.csv": "seguimiento_pa",
        "seguimiento_productos_pa_cleaned.csv": "seguimiento_productos_pa", 
        "seguimiento_actividades_pa_cleaned.csv": "seguimiento_actividades_pa",
        
        # Unidades de proyecto
        "unidades_proyecto_infraestructura_equipamientos_cleaned.csv": "unidades_proyecto_infraestructura_equipamientos",
        "unidades_proyecto_infraestructura_vial_cleaned.csv": "unidades_proyecto_infraestructura_vial",
        
        # Contratos SECOP
        "contratos_cleaned.csv": "contratos",
        "contratos_valores_cleaned.csv": "contratos_valores",
        
        # Catálogos
        "centros_gestores.csv": "centros_gestores",
        "programas.csv": "programas", 
        "areas_funcionales.csv": "areas_funcionales",
        "propositos.csv": "propositos",
        "retos.csv": "retos",
        "proyectos.csv": "proyectos"
    }
    
    # Buscar archivos en todos los directorios
    for input_dir in INPUT_DIRS:
        if not os.path.exists(input_dir):
            logger.warning(f"📂 Directorio no encontrado: {input_dir}")
            continue
            
        logger.info(f"📂 Procesando directorio: {input_dir}")
        
        # Buscar archivos CSV
        for file_name, table_name in file_table_mapping.items():
            csv_path = os.path.join(input_dir, file_name)
            total_files += 1
            
            if load_csv_to_table(csv_path, table_name, engine):
                total_loaded += 1
    
    # También buscar en el directorio raíz
    logger.info("📂 Procesando directorio raíz")
    for file_name, table_name in file_table_mapping.items():
        csv_path = file_name
        if os.path.exists(csv_path):
            total_files += 1
            if load_csv_to_table(csv_path, table_name, engine):
                total_loaded += 1
    
    # Reporte final
    logger.info("=" * 60)
    logger.info(f"🎉 Carga completada: {total_loaded}/{total_files} archivos procesados")
    
    # Verificar conteos finales
    try:
        with engine.connect() as connection:
            logger.info("📊 Resumen de datos cargados:")
            
            tables_to_check = [
                "centros_gestores", "programas", "areas_funcionales", "propositos", "retos",
                "movimientos_presupuestales", "ejecucion_presupuestal", "datos_caracteristicos_proyectos",
                "unidades_proyecto_infraestructura_equipamientos", "unidades_proyecto_infraestructura_vial",
                "seguimiento_pa", "seguimiento_productos_pa", "seguimiento_actividades_pa",
                "contratos", "contratos_valores"
            ]
            
            total_records = 0
            for table in tables_to_check:
                try:
                    result = connection.execute(text(f"SELECT count(*) FROM {table}"))
                    count = result.scalar()
                    total_records += count
                    logger.info(f"   • {table}: {count:,} registros")
                except Exception as e:
                    logger.warning(f"   • {table}: Error al contar - {e}")
            
            logger.info(f"📊 Total de registros cargados: {total_records:,}")
            
    except Exception as e:
        logger.error(f"❌ Error verificando conteos: {e}")
    
    logger.info("✅ Base de datos lista con datos en Railway!")

if __name__ == "__main__":
    load_all_data()
