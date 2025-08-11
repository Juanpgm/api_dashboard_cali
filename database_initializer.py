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
    """Inicializa y verifica la estructura de la base de datos para el API.

    Responsabilidades:
    - Verificar conexión
    - Crear tablas e índices si faltan (tipos correctos)
    - Corregir discrepancias de esquema típicas
    - Validar que el esquema final cumpla las expectativas

    Notas: No migra datos complejos; se centra en estructura e índices.
    """
    
    def __init__(self):
        self.engine = engine
        self.inspector = inspect(self.engine)
        
    def check_database_connection(self) -> bool:
        """Verifica la conexión a la base de datos mediante un SELECT 1."""
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
        """Obtiene la lista de tablas existentes en la base de datos."""
        try:
            tables = self.inspector.get_table_names()
            logger.info(f"📊 Tablas existentes encontradas: {len(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ Error al obtener tablas existentes: {e}")
            return []
    
    def backup_existing_data(self, tables: List[str]) -> Dict[str, int]:
        """Cuenta registros por tabla importante para fines de backup rápido (metadatos)."""
        backup_counts = {}
        important_tables = [
            'centros_gestores', 'programas', 'areas_funcionales', 
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal', 'unidades_proyecto_infraestructura_equipamientos',
            'unidades_proyecto_infraestructura_vial', 'seguimiento_pa',
            'seguimiento_productos_pa', 'seguimiento_actividades_pa'
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
        """Crea/verifica tablas usando SQLAlchemy modelos (incluye todas las tablas definidas)."""
        logger.info("🔧 Creando estructura de tablas desde modelos SQLAlchemy...")
        
        try:
            # Usar SQLAlchemy para crear todas las tablas definidas en models.py
            models.Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Todas las tablas creadas/verificadas desde modelos SQLAlchemy")
            
            # Listar las tablas creadas
            created_tables = self.get_existing_tables()
            logger.info(f"📊 Tablas disponibles ({len(created_tables)}):")
            for table in sorted(created_tables):
                logger.info(f"   • {table}")
                
        except Exception as e:
            logger.error(f"❌ Error al crear tablas desde modelos: {e}")
            raise
            
            # Crear índices importantes para rendimiento
            self.create_performance_indexes()
                    
        except Exception as e:
            logger.error(f"❌ Error al crear tablas: {e}")
            raise
    
    def create_performance_indexes(self):
        """Crea índices importantes para mejorar el rendimiento de consultas."""
        logger.info("🔧 Creando índices de rendimiento...")
        
        indices = [
            # Índices para movimientos presupuestales
            "CREATE INDEX IF NOT EXISTS idx_movimientos_bpin ON movimientos_presupuestales(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_periodo ON movimientos_presupuestales(periodo_corte)",
            
            # Índices para ejecución presupuestal
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_bpin ON ejecucion_presupuestal(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_periodo ON ejecucion_presupuestal(periodo_corte)",
            
            # Índices para equipamientos
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_identificador ON unidades_proyecto_infraestructura_equipamientos(identificador)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_comuna ON unidades_proyecto_infraestructura_equipamientos(comuna_corregimiento)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_estado ON unidades_proyecto_infraestructura_equipamientos(estado_unidad_proyecto)",
            
            # Índices para infraestructura vial
            "CREATE INDEX IF NOT EXISTS idx_vial_identificador ON unidades_proyecto_infraestructura_vial(identificador)",
            "CREATE INDEX IF NOT EXISTS idx_vial_comuna ON unidades_proyecto_infraestructura_vial(comuna_corregimiento)",
            "CREATE INDEX IF NOT EXISTS idx_vial_estado ON unidades_proyecto_infraestructura_vial(estado_unidad_proyecto)",
            
            # Índices para seguimiento PA
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_pa_periodo ON seguimiento_pa(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_pa_subdireccion ON seguimiento_pa(subdireccion_subsecretaria)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_productos_pa_cod1 ON seguimiento_productos_pa(cod_pd_lvl_1)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_productos_pa_cod2 ON seguimiento_productos_pa(cod_pd_lvl_2)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod1 ON seguimiento_actividades_pa(cod_pd_lvl_1)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod2 ON seguimiento_actividades_pa(cod_pd_lvl_2)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod3 ON seguimiento_actividades_pa(cod_pd_lvl_3)"
        ]
        
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    for index_sql in indices:
                        try:
                            connection.execute(text(index_sql))
                            logger.info(f"✅ Índice creado: {index_sql.split('idx_')[1].split(' ')[0]}")
                        except Exception as e:
                            if "already exists" in str(e):
                                logger.info(f"⚠️ Índice ya existe: {index_sql.split('idx_')[1].split(' ')[0]}")
                            else:
                                logger.warning(f"⚠️ Error creando índice: {e}")
                    
                    logger.info("✅ Todos los índices procesados")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error durante creación de índices: {e}")
    
    def fix_existing_schema_issues(self):
        """Corrige problemas comunes de tipos de columnas en tablas existentes."""
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
        """Verifica que el esquema final esté correcto consultando information_schema."""
        logger.info("🔍 Verificando esquema final...")
        
        expected_tables = [
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal', 'unidades_proyecto_infraestructura_equipamientos',
            'unidades_proyecto_infraestructura_vial', 'seguimiento_pa',
            'seguimiento_productos_pa', 'seguimiento_actividades_pa'
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
                                     'unidades_proyecto_infraestructura_vial',
                                     'seguimiento_pa', 'seguimiento_productos_pa', 
                                     'seguimiento_actividades_pa')
                    AND column_name IN ('bpin', 'periodo_corte', 'identificador', 'id_seguimiento_pa',
                                      'cod_pd_lvl_1', 'cod_pd_lvl_2', 'cod_pd_lvl_3')
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
        """Orquesta el flujo completo de inicialización y verificación de la base de datos."""
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
