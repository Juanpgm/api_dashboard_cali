"""
Script para verificar y corregir el esquema de la base de datos
específicamente para las columnas periodo_corte que deben ser VARCHAR/TEXT, no DATE
"""

from sqlalchemy import create_engine, text
from fastapi_project.database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_schema():
    """Verifica y corrige el esquema de la base de datos"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            
            # Verificar tipos de columnas actuales
            logger.info("🔍 Verificando tipos de columnas actuales...")
            
            check_query = text("""
                SELECT table_name, column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('movimientos_presupuestales', 'ejecucion_presupuestal')
                AND column_name = 'periodo_corte'
                ORDER BY table_name;
            """)
            
            result = connection.execute(check_query)
            
            for row in result:
                table_name, column_name, data_type, max_length = row
                logger.info(f"📊 {table_name}.{column_name}: {data_type} ({max_length})")
        
        # Usar una nueva conexión para las modificaciones
        with engine.connect() as connection:
            with connection.begin():
                # Corregir tipos si es necesario
                tables_to_fix = ['movimientos_presupuestales', 'ejecucion_presupuestal']
                
                for table_name in tables_to_fix:
                    logger.info(f"🔧 Corrigiendo {table_name}.periodo_corte...")
                    
                    try:
                        # Primero intentar cambio directo
                        fix_query = text(f"""
                            ALTER TABLE {table_name} 
                            ALTER COLUMN periodo_corte TYPE VARCHAR(50)
                        """)
                        connection.execute(fix_query)
                        logger.info(f"✅ {table_name}.periodo_corte actualizado a VARCHAR(50)")
                        
                    except Exception as e:
                        if "cannot be cast automatically" in str(e) or "invalid input syntax" in str(e):
                            # Si hay datos incompatibles, necesitamos usar USING para convertir
                            logger.info(f"🔄 Convirtiendo datos existentes en {table_name}...")
                            fix_query_with_conversion = text(f"""
                                ALTER TABLE {table_name} 
                                ALTER COLUMN periodo_corte TYPE VARCHAR(50) USING periodo_corte::TEXT
                            """)
                            connection.execute(fix_query_with_conversion)
                            logger.info(f"✅ {table_name}.periodo_corte convertido a VARCHAR(50)")
                        else:
                            logger.error(f"❌ Error corrigiendo {table_name}: {e}")
                            raise
        
        # Verificar después de la corrección
        with engine.connect() as connection:
            logger.info("🔍 Verificando después de la corrección...")
            result = connection.execute(check_query)
            
            for row in result:
                table_name, column_name, data_type, max_length = row
                logger.info(f"📊 {table_name}.{column_name}: {data_type} ({max_length})")
        
        logger.info("🎉 Esquema verificado y corregido exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la verificación/corrección del esquema: {str(e)}")
        raise

if __name__ == "__main__":
    check_and_fix_schema()
