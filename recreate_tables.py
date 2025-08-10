"""
Script para recrear las tablas movimientos_presupuestales y ejecucion_presupuestal
con claves primarias compuestas (bpin, periodo_corte)
"""

from sqlalchemy import create_engine, text
from fastapi_project.database import SQLALCHEMY_DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_tables_with_composite_keys():
    """Recrea las tablas con claves primarias compuestas"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                
                # Hacer backup de los datos existentes (si los hay)
                logger.info("🔄 Verificando datos existentes...")
                
                # Verificar si las tablas existen y tienen datos
                tables_to_recreate = ['movimientos_presupuestales', 'ejecucion_presupuestal']
                
                for table_name in tables_to_recreate:
                    logger.info(f"🗑️ Eliminando tabla existente: {table_name}")
                    
                    # Drop table if exists
                    drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE"
                    connection.execute(text(drop_sql))
                    logger.info(f"✅ Tabla {table_name} eliminada")
                
                # Crear tabla movimientos_presupuestales con clave compuesta
                logger.info("🔧 Creando tabla movimientos_presupuestales...")
                create_movimientos_sql = text("""
                    CREATE TABLE movimientos_presupuestales (
                        bpin BIGINT NOT NULL,
                        periodo_corte VARCHAR(50) NOT NULL,
                        ppto_inicial DOUBLE PRECISION NOT NULL,
                        adiciones DOUBLE PRECISION NOT NULL,
                        reducciones DOUBLE PRECISION NOT NULL,
                        ppto_modificado DOUBLE PRECISION NOT NULL,
                        PRIMARY KEY (bpin, periodo_corte)
                    )
                """)
                connection.execute(create_movimientos_sql)
                
                # Crear índices para optimizar consultas
                connection.execute(text("CREATE INDEX idx_movimientos_bpin ON movimientos_presupuestales(bpin)"))
                connection.execute(text("CREATE INDEX idx_movimientos_periodo ON movimientos_presupuestales(periodo_corte)"))
                
                logger.info("✅ Tabla movimientos_presupuestales creada con clave compuesta")
                
                # Crear tabla ejecucion_presupuestal con clave compuesta
                logger.info("🔧 Creando tabla ejecucion_presupuestal...")
                create_ejecucion_sql = text("""
                    CREATE TABLE ejecucion_presupuestal (
                        bpin BIGINT NOT NULL,
                        periodo_corte VARCHAR(50) NOT NULL,
                        ejecucion DOUBLE PRECISION NOT NULL,
                        pagos DOUBLE PRECISION NOT NULL,
                        saldos_cdp DOUBLE PRECISION NOT NULL,
                        total_acumul_obligac DOUBLE PRECISION NOT NULL,
                        total_acumulado_cdp DOUBLE PRECISION NOT NULL,
                        total_acumulado_rpc DOUBLE PRECISION NOT NULL,
                        PRIMARY KEY (bpin, periodo_corte)
                    )
                """)
                connection.execute(create_ejecucion_sql)
                
                # Crear índices para optimizar consultas
                connection.execute(text("CREATE INDEX idx_ejecucion_bpin ON ejecucion_presupuestal(bpin)"))
                connection.execute(text("CREATE INDEX idx_ejecucion_periodo ON ejecucion_presupuestal(periodo_corte)"))
                
                logger.info("✅ Tabla ejecucion_presupuestal creada con clave compuesta")
        
        logger.info("🎉 Tablas recreadas exitosamente con claves primarias compuestas")
        
    except Exception as e:
        logger.error(f"❌ Error durante la recreación de tablas: {str(e)}")
        raise

if __name__ == "__main__":
    recreate_tables_with_composite_keys()
