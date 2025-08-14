"""
Script unificado de inicialización de base de datos para entornos locales y externos (Railway).
Este script configura automáticamente toda la estructura de base de datos
y carga los datos necesarios para el API Dashboard de la Alcaldía de Cali.

Funcionalidades:
- Detecta automáticamente si está en entorno local o Railway
- Crea estructura de base de datos completa
- Carga datos desde archivos JSON/CSV disponibles
- Maneja variables de entorno (.env para Railway)
- Verifica integridad de datos cargados
"""

import logging
import sys
import os
import json
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Dict, List, Tuple, Optional
import time
import datetime
from dotenv import load_dotenv
from tqdm import tqdm
import psutil
import hashlib

# Cargar variables de entorno
load_dotenv()

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
    """Inicializa y configura la base de datos completa para entornos locales y externos.

    Responsabilidades:
    - Detectar entorno (local/Railway) automáticamente
    - Verificar conexión y configuración
    - Crear estructura de base de datos
    - Cargar datos incrementalmente (solo nuevos datos)
    - Generar reportes detallados de métricas
    """
    
    def __init__(self):
        """Inicializa el configurador de base de datos."""
        self.engine = engine
        self.start_time = time.time()
        self.metrics = {
            'start_time': datetime.datetime.now(),
            'environment': self._detect_environment(),
            'tables_created': 0,
            'tables_updated': 0,
            'data_loaded': {},
            'data_skipped': {},
            'errors': [],
            'performance': {},
            'memory_usage': {},
            'files_processed': 0,
            'total_records': 0,
            'failed_records': 0
        }
        logger.info(f"🌍 Entorno detectado: {self.metrics['environment']}")
        
    def _detect_environment(self) -> str:
        """Detecta si está ejecutándose en Railway o entorno local."""
        if os.getenv('RAILWAY_ENVIRONMENT'):
            return 'Railway (Producción)'
        elif os.getenv('DATABASE_URL') and 'railway' in os.getenv('DATABASE_URL', ''):
            return 'Railway (Desarrollo)'
        return 'Local (Desarrollo)'
        
    def _get_memory_usage(self) -> Dict[str, float]:
        """Obtiene el uso actual de memoria."""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Memoria física
            'vms_mb': memory_info.vms / 1024 / 1024,  # Memoria virtual
            'percent': process.memory_percent()
        }

    def _get_file_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 de un archivo para detectar cambios."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def _check_table_exists_and_has_data(self, table_name: str) -> Tuple[bool, int]:
        """Verifica si una tabla existe y cuántos registros tiene."""
        try:
            with self.engine.connect() as conn:
                # Verificar si la tabla existe
                if not self.engine.dialect.has_table(conn, table_name):
                    return False, 0
                
                # Contar registros
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                return True, count
        except Exception as e:
            logger.warning(f"Error verificando tabla {table_name}: {e}")
            return False, 0
            
    def _should_load_data(self, table_name: str, file_path: Path) -> bool:
        """Determina si se deben cargar datos basándose en existencia y cambios."""
        exists, count = self._check_table_exists_and_has_data(table_name)
        
        if not exists:
            logger.info(f"📥 {table_name}: Tabla no existe, se cargará")
            return True
            
        if count == 0:
            logger.info(f"📥 {table_name}: Tabla vacía, se cargará")
            return True
            
        # TODO: Implementar verificación de hash de archivo para detectar cambios
        # Por ahora, no cargar si ya tiene datos
        logger.info(f"⏭️ {table_name}: Ya tiene {count:,} registros, se omite")
        self.metrics['data_skipped'][table_name] = count
        return False
        
    def test_connection(self) -> bool:
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
            'ejecucion_presupuestal', 'datos_caracteristicos_proyectos',  # Nueva tabla
            'unidades_proyecto_infraestructura_equipamientos',
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
        """Crea/actualiza tablas usando SQLAlchemy modelos con esquema corregido."""
        logger.info("🔧 Creando/actualizando estructura de tablas desde modelos SQLAlchemy...")
        
        try:
            # Obtener tablas existentes antes
            existing_tables = self.get_existing_tables()
            
            # Para Railway, aseguramos que las tablas problemáticas se actualicen
            if self.is_railway_environment():
                self._update_problematic_tables()
            
            # Usar SQLAlchemy para crear todas las tablas definidas en models.py
            models.Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Todas las tablas creadas/verificadas desde modelos SQLAlchemy")
            
            # Listar las tablas creadas
            created_tables = self.get_existing_tables()
            logger.info(f"📊 Tablas existentes encontradas: {len(created_tables)}")
            logger.info(f"📊 Tablas disponibles ({len(created_tables)}):")
            for table in sorted(created_tables):
                logger.info(f"   • {table}")
            
            # Crear índices importantes para rendimiento
            self.create_performance_indexes()
                    
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            raise

    def _update_problematic_tables(self):
        """Actualiza tablas que tienen diferencias de esquema en Railway."""
        problematic_tables = [
            'movimientos_presupuestales',
            'unidades_proyecto_infraestructura_equipamientos', 
            'unidades_proyecto_infraestructura_vial'
        ]
        
        for table_name in problematic_tables:
            try:
                # Agregar columnas faltantes si no existen
                if table_name == 'movimientos_presupuestales':
                    self._add_columns_if_missing(table_name, [
                        ('aplazamiento', 'BIGINT DEFAULT 0'),
                        ('desaplazamiento', 'BIGINT DEFAULT 0')
                    ])
                elif 'infraestructura' in table_name:
                    self._add_columns_if_missing(table_name, [
                        ('avance_físico_obra', 'FLOAT'),
                        ('ejecucion_financiera_obra', 'FLOAT')
                    ])
            except Exception as e:
                logger.warning(f"⚠️ No se pudo actualizar {table_name}: {e}")

    def _add_columns_if_missing(self, table_name: str, columns: list):
        """Agrega columnas a una tabla si no existen."""
        with self.engine.connect() as conn:
            for column_name, column_type in columns:
                try:
                    # Verificar si la columna existe
                    result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{column_name}'
                    """))
                    
                    if not result.fetchone():
                        # La columna no existe, agregarla
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                        logger.info(f"✅ Columna {column_name} agregada a {table_name}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo agregar columna {column_name} a {table_name}: {e}")
                    pass
    
    def create_performance_indexes(self):
        """Crea índices importantes para mejorar el rendimiento de consultas con barra de progreso."""
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
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod3 ON seguimiento_actividades_pa(cod_pd_lvl_3)",
            
            # ✅ Índices para contratos SECOP
            "CREATE INDEX IF NOT EXISTS idx_contratos_bpin ON contratos(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_cod_contrato ON contratos(cod_contrato)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_estado ON contratos(estado_contrato)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_proveedor ON contratos(codigo_proveedor)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_valores_bpin ON contratos_valores(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_valores_cod_contrato ON contratos_valores(cod_contrato)"
        ]
        
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    # Crear índices con barra de progreso
                    with tqdm(total=len(indices), desc="Creando índices", 
                             unit="índices", ncols=100) as pbar:
                        
                        for index_sql in indices:
                            try:
                                # Extraer nombre del índice para mostrar
                                index_name = index_sql.split('idx_')[1].split(' ')[0]
                                pbar.set_description(f"Creando índice {index_name}")
                                
                                connection.execute(text(index_sql))
                                logger.info(f"✅ Índice creado: {index_name}")
                                
                            except Exception as e:
                                if "already exists" in str(e):
                                    logger.info(f"⚠️ Índice ya existe: {index_name}")
                                else:
                                    logger.warning(f"⚠️ Error creando índice {index_name}: {e}")
                            
                            pbar.update(1)
                    
                    logger.info(f"✅ Procesamiento de índices completado ({len(indices)} índices)")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error durante creación de índices: {e}")
    
    def fix_existing_schema_issues(self):
        """Corrige problemas comunes de tipos de columnas en tablas existentes con barra de progreso."""
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
                # Procesar correcciones con barra de progreso
                with tqdm(total=len(schema_fixes), desc="Corrigiendo esquemas", 
                         unit="columnas", ncols=100) as pbar:
                    
                    for fix in schema_fixes:
                        pbar.set_description(f"Corrigiendo {fix['table']}.{fix['column']}")
                        
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
                        
                        pbar.update(1)
                
                logger.info(f"✅ Correcciones de esquema completadas ({len(schema_fixes)} verificaciones)")
                        
        except Exception as e:
            logger.error(f"❌ Error durante corrección de esquemas: {e}")
    
    def verify_final_schema(self) -> bool:
        """Verifica que el esquema final esté correcto consultando information_schema."""
        logger.info("🔍 Verificando esquema final...")
        
        expected_tables = [
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal', 'datos_caracteristicos_proyectos',  # Nueva tabla
            'unidades_proyecto_infraestructura_equipamientos',
            'unidades_proyecto_infraestructura_vial', 'seguimiento_pa',
            'seguimiento_productos_pa', 'seguimiento_actividades_pa',
            'contratos', 'contratos_valores'  # ✅ Nuevas tablas de contratos SECOP
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
                                     'seguimiento_actividades_pa', 'contratos', 'contratos_valores')
                    AND column_name IN ('bpin', 'periodo_corte', 'identificador', 'id_seguimiento_pa',
                                      'cod_pd_lvl_1', 'cod_pd_lvl_2', 'cod_pd_lvl_3', 'cod_contrato')
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
                    elif column_name == 'cod_contrato' and data_type != 'character varying':
                        logger.error(f"❌ {table_name}.cod_contrato debería ser varchar, es {data_type}")
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
    
    def load_json_data_to_table(self, json_path: str, table_name: str) -> Tuple[bool, int]:
        """Carga datos desde un archivo JSON a una tabla específica con verificación incremental."""
        start_time = time.time()
        
        try:
            if not os.path.exists(json_path):
                logger.debug(f"📂 Archivo JSON no encontrado: {json_path}")
                return False, 0
            
            # Verificar si se debe cargar la tabla
            json_file_path = Path(json_path)
            if not self._should_load_data(table_name, json_file_path):
                return True, 0  # Éxito pero sin cargar datos nuevos
                
            # Registrar memoria antes de cargar
            memory_before = self._get_memory_usage()
            
            # Mostrar que estamos cargando el archivo
            file_size_mb = os.path.getsize(json_path) / (1024 * 1024)
            logger.info(f"📥 Cargando {os.path.basename(json_path)} ({file_size_mb:.2f} MB)")
            
            # Leer archivo JSON con barra de progreso
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                logger.warning(f"📂 Archivo JSON vacío: {json_path}")
                return False, 0
            
            if not isinstance(data, list):
                logger.error(f"❌ El archivo JSON debe contener una lista: {json_path}")
                return False, 0
                
            if len(data) == 0:
                logger.warning(f"📂 Lista vacía en JSON: {json_path}")
                return False, 0
            
            total_records = len(data)
            logger.info(f"📊 Procesando {total_records:,} registros para tabla '{table_name}'")
            
            # Registrar métricas del archivo
            self.metrics['files_processed'] += 1
            self.metrics['performance'][f'{table_name}_file_size_mb'] = file_size_mb
            self.metrics['performance'][f'{table_name}_total_records'] = total_records
            
            # Verificar estructura del primer registro
            sample = data[0]
            if not isinstance(sample, dict):
                logger.error(f"❌ Los registros deben ser diccionarios: {json_path}")
                return False, 0
                
            columns = list(sample.keys())
            logger.info(f"📋 Columnas detectadas: {len(columns)} ({', '.join(columns[:5])}{'...' if len(columns) > 5 else ''})")
            
            # Limpiar datos antes de insertar
            clean_data = self._clean_data_for_insert(data, table_name)
            
            # Limpiar tabla antes de cargar si tiene datos
            self._should_clean_table_before_load(table_name)
            
            # Preparar statement SQL
            placeholders = ', '.join([f':{col}' for col in columns])
            columns_str = ', '.join(columns)
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Insertar datos en lotes con barra de progreso
            batch_size = 500  # Reducir tamaño de lote para mejor manejo de errores
            successful_inserts = 0
            failed_inserts = 0
            
            with self.engine.begin() as connection:
                # Crear barra de progreso
                with tqdm(total=total_records, desc=f"Insertando en {table_name}", 
                         unit="registros", ncols=100) as pbar:
                    
                    for i in range(0, total_records, batch_size):
                        batch = clean_data[i:i + batch_size]
                        try:
                            # Insertar lote
                            connection.execute(text(insert_sql), batch)
                            successful_inserts += len(batch)
                            pbar.update(len(batch))
                            
                        except Exception as batch_error:
                            logger.warning(f"⚠️ Error en lote {i//batch_size + 1}: {batch_error}")
                            
                            # Intentar insertar registro por registro en este lote
                            for record in batch:
                                try:
                                    connection.execute(text(insert_sql), record)
                                    successful_inserts += 1
                                except Exception as record_error:
                                    failed_inserts += 1
                                    logger.debug(f"❌ Error en registro: {record_error}")
                                
                                pbar.update(1)
            
            # Reportar resultados
            if successful_inserts > 0:
                # Registrar métricas
                end_time = time.time()
                load_time = end_time - start_time
                memory_after = self._get_memory_usage()
                
                self.metrics['data_loaded'][table_name] = successful_inserts
                self.metrics['total_records'] += successful_inserts
                self.metrics['failed_records'] += failed_inserts
                self.metrics['performance'][f'{table_name}_load_time_seconds'] = load_time
                self.metrics['performance'][f'{table_name}_records_per_second'] = successful_inserts / load_time if load_time > 0 else 0
                self.metrics['memory_usage'][f'{table_name}_memory_before_mb'] = memory_before['rss_mb']
                self.metrics['memory_usage'][f'{table_name}_memory_after_mb'] = memory_after['rss_mb']
                self.metrics['memory_usage'][f'{table_name}_memory_increase_mb'] = memory_after['rss_mb'] - memory_before['rss_mb']
                
                logger.info(f"✅ {table_name}: {successful_inserts:,} registros cargados exitosamente")
                logger.info(f"⏱️ {table_name}: Cargado en {load_time:.2f}s ({successful_inserts/load_time:.1f} reg/s)")
                if failed_inserts > 0:
                    logger.warning(f"⚠️ {table_name}: {failed_inserts:,} registros fallaron")
                    self.metrics['errors'].append({
                        'table': table_name,
                        'type': 'failed_records',
                        'count': failed_inserts,
                        'timestamp': datetime.datetime.now()
                    })
                return True, successful_inserts
            else:
                logger.error(f"❌ {table_name}: No se pudo cargar ningún registro")
                self.metrics['errors'].append({
                    'table': table_name,
                    'type': 'complete_failure',
                    'message': 'No se pudo cargar ningún registro',
                    'timestamp': datetime.datetime.now()
                })
                return False, 0
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error de formato JSON en {json_path}: {e}")
            return False, 0
        except Exception as e:
            logger.error(f"❌ Error cargando {json_path} a {table_name}: {e}")
            return False, 0

    def _clean_data_for_insert(self, data: list, table_name: str) -> list:
        """Limpia y prepara los datos para inserción, manejando valores NULL y tipos."""
        clean_data = []
        
        for record in data:
            cleaned_record = {}
            for key, value in record.items():
                # Manejar valores NULL, NaN, y strings vacíos
                if value is None or value == '' or (isinstance(value, str) and value.lower() in ['null', 'nan', 'none']):
                    cleaned_record[key] = None
                # Manejar números como strings
                elif isinstance(value, str) and value.replace('.', '', 1).replace('-', '', 1).isdigit():
                    try:
                        # Intentar convertir a entero o float
                        if '.' in value:
                            cleaned_record[key] = float(value)
                        else:
                            cleaned_record[key] = int(value)
                    except ValueError:
                        cleaned_record[key] = value
                # Para fechas, asegurar formato correcto
                elif key in ['fecha_inicio_planeado', 'fecha_fin_planeado', 'fecha_inicio_real', 'fecha_fin_real', 'fecha_actualizacion']:
                    if value and isinstance(value, str) and value.strip():
                        cleaned_record[key] = value.strip()
                    else:
                        cleaned_record[key] = None
                # Para campos BPIN, asegurar que sea numérico
                elif key == 'bpin':
                    if value is None or value == '':
                        # Para Railway, mejor omitir el registro si BPIN es NULL
                        if self.is_railway_environment():
                            return clean_data  # Salir temprano, omitir este registro
                        cleaned_record[key] = None
                    else:
                        try:
                            cleaned_record[key] = int(float(str(value))) if value else None
                        except (ValueError, TypeError):
                            if self.is_railway_environment():
                                return clean_data  # Omitir registro con BPIN inválido
                            cleaned_record[key] = None
                else:
                    cleaned_record[key] = value
            
            # Solo agregar si el registro no está vacío
            if cleaned_record:
                clean_data.append(cleaned_record)
        
        return clean_data

    def _should_clean_table_before_load(self, table_name: str) -> bool:
        """Determina si una tabla debe limpiarse antes de cargar datos."""
        # Solo limpiar si no está vacía
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            if count > 0:
                logger.info(f"🧹 Tabla '{table_name}' limpiada antes de cargar")
                conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE"))
                conn.commit()
                return True
        return False
    
    def load_available_data(self) -> Dict[str, int]:
        """Busca y carga todos los datos disponibles desde archivos JSON con barras de progreso."""
        logger.info("📦 Iniciando búsqueda y carga de datos...")
        
        loaded_counts = {}
        
        # Mapeo de archivos a tablas
        file_table_mapping = {
            # Catálogos básicos (JSON)
            "centros_gestores.json": "centros_gestores",
            "programas.json": "programas", 
            "areas_funcionales.json": "areas_funcionales",
            "propositos.json": "propositos",
            "retos.json": "retos",
            "proyectos.json": "proyectos",
            
            # Datos principales (nombres reales de archivos)
            "movimientos_presupuestales.json": "movimientos_presupuestales",
            "ejecucion_presupuestal.json": "ejecucion_presupuestal",
            "datos_caracteristicos_proyectos.json": "datos_caracteristicos_proyectos",
            "seguimiento_pa.json": "seguimiento_pa",
            "seguimiento_productos_pa.json": "seguimiento_productos_pa", 
            "seguimiento_actividades_pa.json": "seguimiento_actividades_pa",
            "unidad_proyecto_infraestructura_equipamientos.json": "unidades_proyecto_infraestructura_equipamientos",
            "unidad_proyecto_infraestructura_vial.json": "unidades_proyecto_infraestructura_vial",
            "contratos.json": "contratos",
            "contratos_valores.json": "contratos_valores"
        }
        
        # Buscar todos los archivos disponibles
        files_found = []
        
        # Buscar en directorios de datos
        for data_dir in self.data_directories:
            if not os.path.exists(data_dir):
                continue
                
            for file_name, table_name in file_table_mapping.items():
                json_path = os.path.join(data_dir, file_name)
                if os.path.exists(json_path):
                    files_found.append((json_path, table_name, file_name))
        
        # También buscar en directorio raíz
        for file_name, table_name in file_table_mapping.items():
            if os.path.exists(file_name):
                files_found.append((file_name, table_name, file_name))
        
        if not files_found:
            logger.warning("⚠️ No se encontraron archivos de datos para cargar")
            return loaded_counts
        
        logger.info(f"📋 Encontrados {len(files_found)} archivos para procesar")
        
        # Procesar archivos con barra de progreso general
        with tqdm(total=len(files_found), desc="Procesando archivos", 
                 unit="archivos", ncols=100, position=0) as file_pbar:
            
            for json_path, table_name, file_name in files_found:
                file_pbar.set_description(f"Procesando {file_name}")
                
                # Limpiar tabla antes de cargar (opcional)
                try:
                    with self.engine.begin() as connection:
                        connection.execute(text(f"DELETE FROM {table_name}"))
                    logger.info(f"🧹 Tabla '{table_name}' limpiada antes de cargar")
                except Exception as e:
                    logger.debug(f"⚠️ No se pudo limpiar {table_name}: {e}")
                
                # Cargar datos
                success, count = self.load_json_data_to_table(json_path, table_name)
                
                if success and count > 0:
                    loaded_counts[table_name] = count
                    logger.info(f"✅ {table_name}: {count:,} registros cargados correctamente")
                else:
                    logger.warning(f"⚠️ {table_name}: No se cargaron datos desde {file_name}")
                
                file_pbar.update(1)
        
        # Resumen final
        total_loaded = sum(loaded_counts.values())
        logger.info("=" * 60)
        logger.info(f"🎉 Carga completada: {len(loaded_counts)}/{len(files_found)} archivos procesados exitosamente")
        logger.info(f"📊 Total de registros cargados: {total_loaded:,}")
        
        if loaded_counts:
            logger.info("📋 Resumen por tabla:")
            for table, count in sorted(loaded_counts.items()):
                logger.info(f"   • {table}: {count:,} registros")
        
        return loaded_counts
    
    def verify_data_integrity(self, loaded_counts: Dict[str, int]) -> bool:
        """Verifica que los datos se hayan cargado correctamente."""
        logger.info("🔍 Verificando integridad de datos...")
        
        try:
            with self.engine.connect() as connection:
                # Verificar totales por tabla
                total_records = 0
                tables_with_data = 0
                
                expected_tables = [
                    'centros_gestores', 'programas', 'areas_funcionales',
                    'propositos', 'retos', 'movimientos_presupuestales', 
                    'ejecucion_presupuestal', 'datos_caracteristicos_proyectos',
                    'unidades_proyecto_infraestructura_equipamientos',
                    'unidades_proyecto_infraestructura_vial', 'seguimiento_pa',
                    'seguimiento_productos_pa', 'seguimiento_actividades_pa',
                    'contratos', 'contratos_valores'
                ]
                
                logger.info("📊 Estado de datos por tabla:")
                for table in expected_tables:
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        total_records += count
                        
                        if count > 0:
                            tables_with_data += 1
                            logger.info(f"   ✅ {table}: {count:,} registros")
                        else:
                            logger.warning(f"   ⚠️ {table}: Sin datos")
                            
                    except Exception as e:
                        logger.error(f"   ❌ {table}: Error - {e}")
                
                logger.info(f"📊 Resumen: {tables_with_data}/{len(expected_tables)} tablas con datos")
                logger.info(f"📊 Total de registros: {total_records:,}")
                
                # Verificaciones de integridad básicas
                integrity_ok = True
                
                # Verificar que existan catálogos básicos
                basic_catalogs = ['centros_gestores', 'programas', 'areas_funcionales', 'propositos', 'retos']
                for catalog in basic_catalogs:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {catalog}"))
                    count = result.scalar()
                    if count == 0:
                        logger.warning(f"⚠️ Catálogo básico vacío: {catalog}")
                        # No es crítico, solo advertencia
                
                # Verificar consistencia de claves foráneas en proyectos
                if total_records > 1000:  # Solo si hay datos significativos
                    try:
                        # Verificar que los BPIN en movimientos existan en ejecución si ambas tienen datos
                        result = connection.execute(text("""
                            SELECT COUNT(*) FROM movimientos_presupuestales m 
                            WHERE NOT EXISTS (
                                SELECT 1 FROM ejecucion_presupuestal e 
                                WHERE e.bpin = m.bpin
                            ) AND (SELECT COUNT(*) FROM movimientos_presupuestales) > 0 
                            AND (SELECT COUNT(*) FROM ejecucion_presupuestal) > 0
                        """))
                        orphan_movements = result.scalar()
                        
                        if orphan_movements > 0:
                            logger.warning(f"⚠️ {orphan_movements} movimientos sin ejecución correspondiente")
                        else:
                            logger.info("✅ Consistencia BPIN verificada")
                            
                    except Exception as e:
                        logger.debug(f"Verificación de integridad opcional falló: {e}")
                
                return integrity_ok
                
        except Exception as e:
            logger.error(f"❌ Error durante verificación de integridad: {e}")
            return False
    
    def initialize_database(self) -> bool:
        """Orquesta el flujo completo de inicialización, carga de datos y verificación."""
        return self.complete_initialization()
    
    def complete_initialization(self) -> bool:
        """Ejecuta el proceso completo de inicialización con métricas."""
        try:
            logger.info("🚀 Iniciando inicialización completa de la base de datos")
            logger.info("=" * 70)
            
            # 1. Verificar conexión
            if not self.test_connection():
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
            
            # 6. Cargar datos disponibles
            logger.info("=" * 50)
            logger.info("📦 FASE DE CARGA DE DATOS")
            loaded_counts = self.load_available_data()
            
            # 7. Verificar integridad de datos
            if not self.verify_data_integrity(loaded_counts):
                logger.warning("⚠️ Algunas verificaciones de integridad fallaron, pero la estructura está lista")
            
            # 8. Reporte final
            logger.info("=" * 70)
            logger.info("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("📊 Resumen final:")
            logger.info(f"   🌍 Entorno: {self.metrics['environment']}")
            logger.info(f"   🗄️ Tablas verificadas/creadas: {len(self.get_existing_tables())}")
            logger.info(f"   📦 Tablas con datos: {len(loaded_counts)}")
            
            total_loaded = sum(loaded_counts.values())
            logger.info(f"   📊 Total de registros: {total_loaded:,}")
            
            if loaded_counts:
                logger.info("   📋 Datos cargados por tabla:")
                for table, count in sorted(loaded_counts.items()):
                    logger.info(f"      • {table}: {count:,} registros")
            
            logger.info("   🚀 Base de datos lista para el API")
            logger.info("=" * 70)
            
            # 9. Generar reporte detallado
            report_file = self.save_report()
            self.print_summary_report()
            
            if report_file:
                logger.info(f"📄 Reporte completo disponible en: {report_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante la inicialización: {e}")
            self.metrics['errors'].append({
                'table': 'initialization',
                'type': 'fatal_error',
                'message': str(e),
                'timestamp': datetime.datetime.now()
            })
            return False
                logger.warning("⚠️ Algunas verificaciones de integridad fallaron, pero la estructura está lista")
            
            # 8. Reporte final
            logger.info("=" * 70)
            logger.info("🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("📊 Resumen final:")
            logger.info(f"   🌍 Entorno: {'Railway (Producción)' if self.is_railway else 'Local (Desarrollo)'}")
            logger.info(f"   🗄️ Tablas verificadas/creadas: {len(self.get_existing_tables())}")
            logger.info(f"   📦 Tablas con datos: {len(loaded_counts)}")
            
            total_loaded = sum(loaded_counts.values())
            logger.info(f"   📊 Total de registros: {total_loaded:,}")
            
            if loaded_counts:
                logger.info("   📋 Datos cargados por tabla:")
                for table, count in sorted(loaded_counts.items()):
                    logger.info(f"      • {table}: {count:,} registros")
            
            logger.info("   🚀 Base de datos lista para el API")
            logger.info("=" * 70)
            
            # 9. Generar reporte detallado
            report_file = self.save_report()
            self.print_summary_report()
            
            if report_file:
                logger.info(f"📄 Reporte completo disponible en: {report_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante la inicialización: {e}")
            self.metrics['errors'].append({
                'table': 'initialization',
                'type': 'fatal_error',
                'message': str(e),
                'timestamp': datetime.datetime.now()
            })
            return False
            
    def generate_markdown_report(self) -> str:
        """Genera un reporte completo en formato Markdown con métricas y gráficos."""
        end_time = datetime.datetime.now()
        total_duration = (end_time - self.metrics['start_time']).total_seconds()
        
        report = f"""# 📊 Reporte de Inicialización de Base de Datos
## API Dashboard Alcaldía de Cali

**Fecha de ejecución:** {self.metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}  
**Duración total:** {total_duration:.2f} segundos  
**Entorno:** {self.metrics['environment']}  

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| 🗄️ Tablas creadas/actualizadas | {self.metrics.get('tables_created', 0)} |
| 📁 Archivos procesados | {self.metrics['files_processed']} |
| 📊 Total de registros cargados | {self.metrics['total_records']:,} |
| ❌ Registros fallidos | {self.metrics['failed_records']:,} |
| ✅ Tasa de éxito | {((self.metrics['total_records']/(self.metrics['total_records']+self.metrics['failed_records']))*100) if (self.metrics['total_records']+self.metrics['failed_records']) > 0 else 100:.1f}% |

---

## 📋 Detalle por Tabla

### ✅ Datos Cargados
"""
        
        # Datos cargados
        if self.metrics['data_loaded']:
            for table, count in self.metrics['data_loaded'].items():
                load_time = self.metrics['performance'].get(f'{table}_load_time_seconds', 0)
                rate = self.metrics['performance'].get(f'{table}_records_per_second', 0)
                file_size = self.metrics['performance'].get(f'{table}_file_size_mb', 0)
                
                report += f"""
#### 📊 {table}
- **Registros:** {count:,}
- **Tiempo de carga:** {load_time:.2f}s
- **Velocidad:** {rate:.1f} registros/segundo
- **Tamaño del archivo:** {file_size:.2f} MB
"""
        else:
            report += "\n*No se cargaron datos nuevos.*\n"
            
        # Datos omitidos
        if self.metrics['data_skipped']:
            report += "\n### ⏭️ Datos Omitidos (ya existentes)\n"
            for table, count in self.metrics['data_skipped'].items():
                report += f"- **{table}:** {count:,} registros existentes\n"
        
        # Errores
        if self.metrics['errors']:
            report += f"\n### ❌ Errores Encontrados ({len(self.metrics['errors'])})\n"
            for error in self.metrics['errors']:
                report += f"""
#### {error['table']} - {error['type']}
- **Timestamp:** {error['timestamp'].strftime('%H:%M:%S')}
- **Detalles:** {error.get('message', error.get('count', 'N/A'))}
"""
        
        # Métricas de rendimiento
        report += f"""
---

## ⚡ Métricas de Rendimiento

### 🕐 Tiempos de Procesamiento
"""
        
        if self.metrics['performance']:
            # Crear gráfico simple en texto de barras de tiempo
            time_metrics = {k.replace('_load_time_seconds', ''): v for k, v in self.metrics['performance'].items() if '_load_time_seconds' in k}
            if time_metrics:
                max_time = max(time_metrics.values())
                report += "\n```\nTiempos de carga por tabla:\n"
                for table, time_val in sorted(time_metrics.items(), key=lambda x: x[1], reverse=True):
                    bar_length = int((time_val / max_time) * 40) if max_time > 0 else 0
                    bar = "█" * bar_length + "░" * (40 - bar_length)
                    report += f"{table:<35} {bar} {time_val:6.2f}s\n"
                report += "```\n"
        
        # Métricas de memoria
        if self.metrics['memory_usage']:
            report += "\n### 💾 Uso de Memoria\n"
            memory_metrics = {}
            for k, v in self.metrics['memory_usage'].items():
                if '_memory_increase_mb' in k:
                    table = k.replace('_memory_increase_mb', '')
                    memory_metrics[table] = v
            
            if memory_metrics:
                total_memory_increase = sum(memory_metrics.values())
                report += f"\n**Aumento total de memoria:** {total_memory_increase:.2f} MB\n\n"
                report += "```\nAumento de memoria por tabla:\n"
                for table, mem_increase in sorted(memory_metrics.items(), key=lambda x: x[1], reverse=True):
                    report += f"{table:<35} {mem_increase:>8.2f} MB\n"
                report += "```\n"
        
        # Gráfico de distribución de registros
        if self.metrics['data_loaded']:
            report += "\n### 📈 Distribución de Registros Cargados\n"
            total_loaded = sum(self.metrics['data_loaded'].values())
            max_count = max(self.metrics['data_loaded'].values())
            
            report += "\n```\nDistribución por tabla:\n"
            for table, count in sorted(self.metrics['data_loaded'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_loaded) * 100 if total_loaded > 0 else 0
                bar_length = int((count / max_count) * 50) if max_count > 0 else 0
                bar = "█" * bar_length + "░" * (50 - bar_length)
                report += f"{table:<35} {bar} {count:>8,} ({percentage:5.1f}%)\n"
            report += "```\n"
        
        # Recomendaciones
        report += f"""
---

## 💡 Recomendaciones

### 🔧 Optimizaciones Identificadas
"""
        
        recommendations = []
        
        # Verificar si hay tablas con muchos errores
        error_tables = {}
        for error in self.metrics['errors']:
            if error['type'] == 'failed_records':
                table = error['table']
                count = error.get('count', 0)
                error_tables[table] = error_tables.get(table, 0) + count
        
        for table, error_count in error_tables.items():
            total_attempts = self.metrics['data_loaded'].get(table, 0) + error_count
            if total_attempts > 0:
                error_rate = (error_count / total_attempts) * 100
                if error_rate > 10:
                    recommendations.append(f"- ⚠️ **{table}:** {error_rate:.1f}% de registros fallan - revisar calidad de datos")
        
        # Verificar rendimiento
        if self.metrics['performance']:
            slow_tables = []
            for k, v in self.metrics['performance'].items():
                if '_records_per_second' in k and v < 50:  # Menos de 50 registros por segundo
                    table = k.replace('_records_per_second', '')
                    slow_tables.append(f"- 🐌 **{table}:** {v:.1f} reg/s - considerar optimización de índices")
            recommendations.extend(slow_tables)
        
        if recommendations:
            report += "\n" + "\n".join(recommendations) + "\n"
        else:
            report += "\n- ✅ **Rendimiento óptimo:** No se detectaron problemas de rendimiento\n"
        
        report += f"""
### 📊 Próximos Pasos
- ✅ Base de datos lista para consultas
- 🚀 Iniciar API: `uvicorn fastapi_project.main:app --reload`
- 📊 Monitorear logs para consultas lentas
- 🔄 Programar respaldos incrementales

---

*Reporte generado automáticamente el {end_time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
        
    def save_report(self) -> str:
        """Guarda el reporte en un archivo Markdown."""
        report_content = self.generate_markdown_report()
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"database_initialization_report_{timestamp}.md"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"📄 Reporte guardado en: {filename}")
            return filename
        except Exception as e:
            logger.error(f"❌ Error guardando reporte: {e}")
            return ""
            
    def print_summary_report(self):
        """Imprime un resumen del reporte en consola."""
        total_duration = (datetime.datetime.now() - self.metrics['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("🎉 RESUMEN DE INICIALIZACIÓN COMPLETADA")
        print("="*80)
        print(f"⏱️ Duración total: {total_duration:.2f} segundos")
        print(f"🌍 Entorno: {self.metrics['environment']}")
        print(f"📁 Archivos procesados: {self.metrics['files_processed']}")
        print(f"📊 Total registros cargados: {self.metrics['total_records']:,}")
        if self.metrics['failed_records'] > 0:
            print(f"❌ Registros fallidos: {self.metrics['failed_records']:,}")
        
        if self.metrics['data_loaded']:
            print(f"\n📋 Tablas con datos cargados ({len(self.metrics['data_loaded'])}):")
            for table, count in self.metrics['data_loaded'].items():
                print(f"   • {table}: {count:,} registros")
        
        if self.metrics['data_skipped']:
            print(f"\n⏭️ Tablas omitidas ({len(self.metrics['data_skipped'])}):")
            for table, count in self.metrics['data_skipped'].items():
                print(f"   • {table}: {count:,} registros existentes")
        
        print("="*80)

def main():
    """Función principal para ejecutar la inicialización completa"""
    print("🏛️ API Dashboard Alcaldía de Cali - Inicializador Unificado")
    print("🔧 Estructura + Datos para entornos Locales y Railway")
    print("=" * 70)
    
    initializer = DatabaseInitializer()
    
    start_time = time.time()
    success = initializer.initialize_database()
    end_time = time.time()
    
    print(f"\n⏱️ Tiempo total de ejecución: {end_time - start_time:.2f} segundos")
    
    if success:
        print("✅ Base de datos completamente configurada y lista para producción")
        print("🚀 Puedes iniciar tu API con: uvicorn fastapi_project.main:app --reload")
        sys.exit(0)
    else:
        print("❌ Error en la inicialización. Revisar logs para detalles.")
        print("📋 Log guardado en: database_init.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
