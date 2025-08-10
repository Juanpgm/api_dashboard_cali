"""
Script de migración para actualizar columnas VARCHAR(255) a TEXT
para permitir nombres más largos en las tablas de catálogos.
"""

from sqlalchemy import create_engine, text
from fastapi_project.database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_column_types():
    """Actualiza las columnas de VARCHAR(255) a TEXT"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Lista de tablas y columnas a actualizar
    updates = [
        ("centros_gestores", "nombre_centro_gestor"),
        ("programas", "nombre_programa"),
        ("areas_funcionales", "nombre_area_funcional"),
        ("propositos", "nombre_proposito"),
        ("retos", "nombre_reto")
    ]
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                for table_name, column_name in updates:
                    sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE TEXT"
                    logger.info(f"Ejecutando: {sql}")
                    connection.execute(text(sql))
                    logger.info(f"✅ Columna {table_name}.{column_name} actualizada a TEXT")
        
        logger.info("🎉 Todas las columnas actualizadas exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {str(e)}")
        raise

if __name__ == "__main__":
    update_column_types()
