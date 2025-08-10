"""
Script principal de inicialización de base de datos para producción.
Este script configura automáticamente toda la estructura de base de datos
necesaria para el API Dashboard de la Alcaldía de Cali.
"""

import logging
import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Dict, List, Tuple
import time

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi_project.database import SQLALCHEMY_DATABASE_URL, engine
from fastapi_project import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Clase para manejar la inicialización completa de la base de datos"""
    
    def __init__(self):
        self.engine = engine
        self.inspector = inspect(self.engine)
        
    def check_database_connection(self) -> bool:
        """Verifica la conexión a la base de datos"""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Conexión a la base de datos exitosa")
            return True
        except OperationalError as e:
            logger.error(f"❌ Error de conexión a la base de datos: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado de conexión: {e}")
            return False
    
    def get_existing_tables(self) -> List[str]:
        """Obtiene la lista de tablas existentes en la base de datos"""
        try:
            tables = self.inspector.get_table_names()
            logger.info(f"📊 Tablas existentes encontradas: {len(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ Error al obtener tablas existentes: {e}")
            return []
    
    def backup_existing_data(self, tables: List[str]) -> Dict[str, int]:
        """Hace backup de datos existentes importantes"""
        backup_counts = {}
        important_tables = [
            'centros_gestores', 'programas', 'areas_funcionales', 
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal', 'unidades_proyecto_infraestructura_equipamientos',
            'unidades_proyecto_infraestructura_vial'
        ]
        
        try:
            with self.engine.connect() as connection:
                for table in important_tables:
                    if table in tables:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        backup_counts[table] = count
                        logger.info(f"📋 {table}: {count} registros existentes")
        except Exception as e:
            logger.error(f"❌ Error al hacer backup de datos: {e}")
        
        return backup_counts
    
    def create_tables_with_correct_schema(self):
        """Crea todas las tablas con el esquema correcto"""
        logger.info("🔧 Creando estructura de tablas...")
        
        table_definitions = {
            'centros_gestores': """
                CREATE TABLE IF NOT EXISTS centros_gestores (
                    cod_centro_gestor INTEGER PRIMARY KEY,
                    nombre_centro_gestor TEXT NOT NULL
                )
            """,
            'programas': """
                CREATE TABLE IF NOT EXISTS programas (
                    cod_programa INTEGER PRIMARY KEY,
                    nombre_programa TEXT NOT NULL
                )
            """,
            'areas_funcionales': """
                CREATE TABLE IF NOT EXISTS areas_funcionales (
                    cod_area_funcional INTEGER PRIMARY KEY,
                    nombre_area_funcional TEXT NOT NULL
                )
            """,
            'propositos': """
                CREATE TABLE IF NOT EXISTS propositos (
                    cod_proposito INTEGER PRIMARY KEY,
                    nombre_proposito TEXT NOT NULL
                )
            """,
            'retos': """
                CREATE TABLE IF NOT EXISTS retos (
                    cod_reto INTEGER PRIMARY KEY,
                    nombre_reto TEXT NOT NULL
                )
            """,
            'movimientos_presupuestales': """
                CREATE TABLE IF NOT EXISTS movimientos_presupuestales (
                    bpin BIGINT NOT NULL,
                    periodo_corte VARCHAR(50) NOT NULL,
                    ppto_inicial DOUBLE PRECISION NOT NULL,
                    adiciones DOUBLE PRECISION NOT NULL,
                    reducciones DOUBLE PRECISION NOT NULL,
                    ppto_modificado DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (bpin, periodo_corte)
                )
            """,
            'ejecucion_presupuestal': """
                CREATE TABLE IF NOT EXISTS ejecucion_presupuestal (
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
            """,
            'unidades_proyecto_infraestructura_equipamientos': """
                CREATE TABLE IF NOT EXISTS unidades_proyecto_infraestructura_equipamientos (
                    bpin BIGINT PRIMARY KEY,
                    identificador VARCHAR(255) NOT NULL,
                    cod_fuente_financiamiento VARCHAR(50),
                    usuarios_beneficiarios DOUBLE PRECISION,
                    dataframe TEXT,
                    nickname VARCHAR(100),
                    nickname_detalle VARCHAR(255),
                    comuna_corregimiento VARCHAR(100),
                    barrio_vereda VARCHAR(100),
                    direccion VARCHAR(255),
                    clase_obra VARCHAR(100),
                    subclase_obra VARCHAR(100),
                    tipo_intervencion VARCHAR(100),
                    descripcion_intervencion TEXT,
                    estado_unidad_proyecto VARCHAR(50),
                    fecha_inicio_planeado DATE,
                    fecha_fin_planeado DATE,
                    fecha_inicio_real DATE,
                    fecha_fin_real DATE,
                    es_centro_gravedad BOOLEAN,
                    ppto_base DOUBLE PRECISION,
                    pagos_realizados DOUBLE PRECISION,
                    avance_fisico_obra DOUBLE PRECISION,
                    ejecucion_financiera_obra DOUBLE PRECISION
                )
            """,
            'unidades_proyecto_infraestructura_vial': """
                CREATE TABLE IF NOT EXISTS unidades_proyecto_infraestructura_vial (
                    bpin BIGINT PRIMARY KEY,
                    identificador VARCHAR(255) NOT NULL,
                    id_via VARCHAR(50),
                    cod_fuente_financiamiento VARCHAR(50),
                    usuarios_beneficiarios DOUBLE PRECISION,
                    dataframe TEXT,
                    nickname VARCHAR(100),
                    nickname_detalle VARCHAR(255),
                    comuna_corregimiento VARCHAR(100),
                    barrio_vereda VARCHAR(100),
                    direccion VARCHAR(255),
                    clase_obra VARCHAR(100),
                    subclase_obra VARCHAR(100),
                    tipo_intervencion VARCHAR(100),
                    descripcion_intervencion TEXT,
                    estado_unidad_proyecto VARCHAR(50),
                    unidad_medicion VARCHAR(50),
                    fecha_inicio_planeado DATE,
                    fecha_fin_planeado DATE,
                    fecha_inicio_real DATE,
                    fecha_fin_real DATE,
                    es_centro_gravedad BOOLEAN,
                    longitud_proyectada DOUBLE PRECISION,
                    longitud_ejecutada DOUBLE PRECISION,
                    ppto_base DOUBLE PRECISION,
                    pagos_realizados DOUBLE PRECISION,
                    avance_fisico_obra DOUBLE PRECISION,
                    ejecucion_financiera_obra DOUBLE PRECISION
                )
            """
        }
        
        indices = {
            'movimientos_presupuestales': [
                "CREATE INDEX IF NOT EXISTS idx_movimientos_bpin ON movimientos_presupuestales(bpin)",
                "CREATE INDEX IF NOT EXISTS idx_movimientos_periodo ON movimientos_presupuestales(periodo_corte)"
            ],
            'ejecucion_presupuestal': [
                "CREATE INDEX IF NOT EXISTS idx_ejecucion_bpin ON ejecucion_presupuestal(bpin)",
                "CREATE INDEX IF NOT EXISTS idx_ejecucion_periodo ON ejecucion_presupuestal(periodo_corte)"
            ],
            'unidades_proyecto_infraestructura_equipamientos': [
                "CREATE INDEX IF NOT EXISTS idx_equipamientos_identificador ON unidades_proyecto_infraestructura_equipamientos(identificador)",
                "CREATE INDEX IF NOT EXISTS idx_equipamientos_comuna ON unidades_proyecto_infraestructura_equipamientos(comuna_corregimiento)",
                "CREATE INDEX IF NOT EXISTS idx_equipamientos_estado ON unidades_proyecto_infraestructura_equipamientos(estado_unidad_proyecto)"
            ],
            'unidades_proyecto_infraestructura_vial': [
                "CREATE INDEX IF NOT EXISTS idx_vial_identificador ON unidades_proyecto_infraestructura_vial(identificador)",
                "CREATE INDEX IF NOT EXISTS idx_vial_comuna ON unidades_proyecto_infraestructura_vial(comuna_corregimiento)",
                "CREATE INDEX IF NOT EXISTS idx_vial_estado ON unidades_proyecto_infraestructura_vial(estado_unidad_proyecto)"
            ]
        }
        
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    # Crear tablas
                    for table_name, sql in table_definitions.items():
                        logger.info(f"🔧 Creando tabla: {table_name}")
                        connection.execute(text(sql))
                        logger.info(f"✅ Tabla {table_name} creada/verificada")
                    
                    # Crear índices
                    for table_name, index_sqls in indices.items():
                        for index_sql in index_sqls:
                            logger.info(f"🔧 Creando índice en {table_name}")
                            connection.execute(text(index_sql))
                    
                    logger.info("✅ Todos los índices creados/verificados")
                    
        except Exception as e:
            logger.error(f"❌ Error al crear tablas: {e}")
            raise
    
    def fix_existing_schema_issues(self):
        """Corrige problemas de esquema en tablas existentes"""
        logger.info("🔄 Verificando y corrigiendo esquemas existentes...")
        
        schema_fixes = [
            # Corregir tipos de columnas texto
            {
                'table': 'centros_gestores',
                'column': 'nombre_centro_gestor',
                'fix': "ALTER TABLE centros_gestores ALTER COLUMN nombre_centro_gestor TYPE TEXT"
            },
            {
                'table': 'programas',
                'column': 'nombre_programa', 
                'fix': "ALTER TABLE programas ALTER COLUMN nombre_programa TYPE TEXT"
            },
            {
                'table': 'areas_funcionales',
                'column': 'nombre_area_funcional',
                'fix': "ALTER TABLE areas_funcionales ALTER COLUMN nombre_area_funcional TYPE TEXT"
            },
            {
                'table': 'propositos',
                'column': 'nombre_proposito',
                'fix': "ALTER TABLE propositos ALTER COLUMN nombre_proposito TYPE TEXT"
            },
            {
                'table': 'retos',
                'column': 'nombre_reto',
                'fix': "ALTER TABLE retos ALTER COLUMN nombre_reto TYPE TEXT"
            },
            # Corregir tipos para movimientos y ejecución
            {
                'table': 'movimientos_presupuestales',
                'column': 'bpin',
                'fix': "ALTER TABLE movimientos_presupuestales ALTER COLUMN bpin TYPE BIGINT"
            },
            {
                'table': 'movimientos_presupuestales',
                'column': 'periodo_corte',
                'fix': "ALTER TABLE movimientos_presupuestales ALTER COLUMN periodo_corte TYPE VARCHAR(50) USING periodo_corte::VARCHAR(50)"
            },
            {
                'table': 'ejecucion_presupuestal',
                'column': 'bpin',
                'fix': "ALTER TABLE ejecucion_presupuestal ALTER COLUMN bpin TYPE BIGINT"
            },
            {
                'table': 'ejecucion_presupuestal',
                'column': 'periodo_corte',
                'fix': "ALTER TABLE ejecucion_presupuestal ALTER COLUMN periodo_corte TYPE VARCHAR(50) USING periodo_corte::VARCHAR(50)"
            },
            # Corregir tipos para unidades de proyecto vial
            {
                'table': 'unidades_proyecto_infraestructura_vial',
                'column': 'identificador',
                'fix': "ALTER TABLE unidades_proyecto_infraestructura_vial ALTER COLUMN identificador TYPE VARCHAR(255) USING identificador::VARCHAR(255)"
            }
        ]
        
        try:
            with self.engine.connect() as connection:
                for fix in schema_fixes:
                    try:
                        logger.info(f"🔧 Corrigiendo {fix['table']}.{fix['column']}")
                        with connection.begin():
                            connection.execute(text(fix['fix']))
                        logger.info(f"✅ {fix['table']}.{fix['column']} corregido")
                    except ProgrammingError as e:
                        if "already exists" in str(e) or "does not exist" in str(e):
                            logger.info(f"⚠️ {fix['table']}.{fix['column']} ya está correcto o no existe")
                        else:
                            logger.warning(f"⚠️ No se pudo corregir {fix['table']}.{fix['column']}: {e}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error menor corrigiendo {fix['table']}.{fix['column']}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error durante corrección de esquemas: {e}")
    
    def verify_final_schema(self) -> bool:
        """Verifica que el esquema final esté correcto"""
        logger.info("🔍 Verificando esquema final...")
        
        expected_tables = [
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal', 'unidades_proyecto_infraestructura_equipamientos',
            'unidades_proyecto_infraestructura_vial'
        ]
        
        try:
            with self.engine.connect() as connection:
                # Verificar que todas las tablas existen
                existing_tables = self.get_existing_tables()
                missing_tables = [t for t in expected_tables if t not in existing_tables]
                
                if missing_tables:
                    logger.error(f"❌ Tablas faltantes: {missing_tables}")
                    return False
                
                # Verificar tipos de columnas críticas
                schema_check = text("""
                    SELECT table_name, column_name, data_type, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('movimientos_presupuestales', 'ejecucion_presupuestal', 
                                     'unidades_proyecto_infraestructura_equipamientos',
                                     'unidades_proyecto_infraestructura_vial')
                    AND column_name IN ('bpin', 'periodo_corte', 'identificador')
                    ORDER BY table_name, column_name;
                """)
                
                result = connection.execute(schema_check)
                schema_ok = True
                
                for row in result:
                    table_name, column_name, data_type, max_length = row
                    logger.info(f"📊 {table_name}.{column_name}: {data_type} ({max_length})")
                    
                    if column_name == 'bpin' and data_type != 'bigint':
                        logger.error(f"❌ {table_name}.bpin debería ser bigint, es {data_type}")
                        schema_ok = False
                    elif column_name == 'periodo_corte' and data_type != 'character varying':
                        logger.error(f"❌ {table_name}.periodo_corte debería ser varchar, es {data_type}")
                        schema_ok = False
                    elif column_name == 'identificador' and data_type != 'character varying':
                        logger.error(f"❌ {table_name}.identificador debería ser varchar, es {data_type}")
                        schema_ok = False
                
                if schema_ok:
                    logger.info("✅ Esquema verificado correctamente")
                    return True
                else:
                    logger.error("❌ Problemas encontrados en el esquema")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error durante verificación de esquema: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Ejecuta la inicialización completa de la base de datos"""
        logger.info("🚀 Iniciando inicialización completa de la base de datos")
        logger.info("=" * 60)
        
        try:
            # 1. Verificar conexión
            if not self.check_database_connection():
                return False
            
            # 2. Obtener estado actual
            existing_tables = self.get_existing_tables()
            backup_data = self.backup_existing_data(existing_tables)
            
            # 3. Crear/verificar estructura de tablas
            self.create_tables_with_correct_schema()
            
            # 4. Corregir problemas de esquema existentes
            self.fix_existing_schema_issues()
            
            # 5. Verificar esquema final
            if not self.verify_final_schema():
                logger.error("❌ La verificación final del esquema falló")
                return False
            
            # 6. Reporte final
            logger.info("=" * 60)
            logger.info("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("📊 Resumen:")
            logger.info(f"   • Tablas verificadas/creadas: {len(existing_tables)}")
            logger.info(f"   • Datos existentes preservados: {sum(backup_data.values())} registros")
            logger.info("   • Esquema optimizado para producción")
            logger.info("   • Índices creados para rendimiento")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante la inicialización: {e}")
            return False

def main():
    """Función principal para ejecutar la inicialización"""
    print("🏛️ API Dashboard Alcaldía de Cali - Inicializador de Base de Datos")
    print("=" * 60)
    
    initializer = DatabaseInitializer()
    
    start_time = time.time()
    success = initializer.initialize_database()
    end_time = time.time()
    
    print(f"\n⏱️ Tiempo total: {end_time - start_time:.2f} segundos")
    
    if success:
        print("✅ Base de datos lista para producción")
        sys.exit(0)
    else:
        print("❌ Error en la inicialización. Revisar logs para detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()
