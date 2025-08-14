"""
Script unificado de inicialización de base de datos para entornos locales y externos (Railway).
Este script configura automáticamente toda la estructura de base de datos
y carga los datos necesarios para el API Dashboard de la Alcaldía de Cali.

Funcionalidades:
- Detecta automáticamente si está en entorno local o Railway
- Crea estructura de base de datos completa
- Carga datos incrementalmente (solo nuevos datos)
- Genera reportes detallados de métricas
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
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Memoria física
                'vms_mb': memory_info.vms / 1024 / 1024,  # Memoria virtual
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0}

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
            
        # Por ahora, no cargar si ya tiene datos (implementar hash check más adelante)
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
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"📊 Tablas existentes encontradas: {len(tables)}")
            return tables
        except Exception as e:
            logger.error(f"❌ Error al obtener tablas existentes: {e}")
            return []
    
    def get_primary_key(self, table_name: str):
        """Obtiene la clave primaria de una tabla específica."""
        try:
            inspector = inspect(self.engine)
            pk_constraint = inspector.get_pk_constraint(table_name)
            
            if pk_constraint and pk_constraint['constrained_columns']:
                pk_columns = pk_constraint['constrained_columns']
                # Retornar clave simple si es una sola columna, o lista si es compuesta
                return pk_columns[0] if len(pk_columns) == 1 else pk_columns
            else:
                # Fallback para tablas conocidas
                table_primary_keys = {
                    'movimientos_presupuestales': 'id',
                    'ejecucion_presupuestal': 'id', 
                    'contratos_secop': 'id',
                    'seguimiento_pa': 'id',
                    'datos_caracteristicos_proyectos': 'bpin',
                    'unidades_proyecto_infraestructura_equipamientos': 'bpin',
                    'unidades_proyecto_infraestructura_vial': 'bpin'
                }
                return table_primary_keys.get(table_name, 'id')
                
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo clave primaria de {table_name}: {e}")
            # Fallback por defecto
            return 'id'
    
    def create_tables_with_correct_schema(self):
        """Crea/actualiza tablas usando SQLAlchemy modelos con esquema corregido."""
        logger.info("🔧 Creando estructura de tablas desde modelos SQLAlchemy...")
        
        try:
            # Forzar creación de todas las tablas desde los modelos
            models.Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Todas las tablas creadas/verificadas desde modelos SQLAlchemy")
            self.metrics['tables_created'] += 1
            
            # Verificar que se crearon correctamente
            tables = self.get_existing_tables()
            logger.info(f"📊 Tablas existentes encontradas: {len(tables)}")
            
            if len(tables) > 0:
                logger.info(f"📊 Tablas disponibles ({len(tables)}):")
                for table in sorted(tables):
                    logger.info(f"   • {table}")
                    
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            raise

    def create_performance_indexes(self):
        """Crea índices de rendimiento para consultas optimizadas."""
        logger.info("🔧 Creando índices de rendimiento...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_movimientos_bpin ON movimientos_presupuestales(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_periodo ON movimientos_presupuestales(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_bpin ON ejecucion_presupuestal(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_periodo ON ejecucion_presupuestal(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_bpin ON unidades_proyecto_infraestructura_equipamientos(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_identificador ON unidades_proyecto_infraestructura_equipamientos(identificador)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_comuna ON unidades_proyecto_infraestructura_equipamientos(comuna_corregimiento)",
            "CREATE INDEX IF NOT EXISTS idx_equipamientos_estado ON unidades_proyecto_infraestructura_equipamientos(estado_unidad_proyecto)",
            "CREATE INDEX IF NOT EXISTS idx_vial_bpin ON unidades_proyecto_infraestructura_vial(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_vial_identificador ON unidades_proyecto_infraestructura_vial(identificador)",
            "CREATE INDEX IF NOT EXISTS idx_vial_comuna ON unidades_proyecto_infraestructura_vial(comuna_corregimiento)",
            "CREATE INDEX IF NOT EXISTS idx_vial_estado ON unidades_proyecto_infraestructura_vial(estado_unidad_proyecto)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_pa_periodo ON seguimiento_pa(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_pa_subdireccion ON seguimiento_pa(cod_pd_lvl_1)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_productos_pa_cod1 ON seguimiento_productos_pa(cod_producto)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_productos_pa_cod2 ON seguimiento_productos_pa(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod1 ON seguimiento_actividades_pa(cod_actividad)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod2 ON seguimiento_actividades_pa(periodo_corte)",
            "CREATE INDEX IF NOT EXISTS idx_seguimiento_actividades_pa_cod3 ON seguimiento_actividades_pa(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_bpin ON contratos(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_cod_contrato ON contratos(cod_contrato)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_estado ON contratos(estado_contrato)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_proveedor ON contratos(codigo_proveedor)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_valores_bpin ON contratos_valores(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_contratos_valores_cod_contrato ON contratos_valores(cod_contrato)",
            "CREATE INDEX IF NOT EXISTS idx_datos_caracteristicos_bpin ON datos_caracteristicos_proyectos(bpin)"
        ]
        
        created_count = 0
        with tqdm(total=len(indexes), desc="Creando índice", unit="índices") as pbar:
            try:
                with self.engine.connect() as connection:
                    for index_sql in indexes:
                        try:
                            connection.execute(text(index_sql))
                            created_count += 1
                            index_name = index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unknown"
                            logger.info(f"✅ Índice creado: {index_name}")
                        except Exception as e:
                            index_name = index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unknown"
                            logger.warning(f"⚠️ Error creando índice {index_name}: {e}")
                        pbar.update(1)
                    
                    connection.commit()
                    
            except Exception as e:
                logger.error(f"❌ Error en creación de índices: {e}")
        
        logger.info(f"✅ Procesamiento de índices completado ({len(indexes)} índices)")

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
            
            # Leer archivo JSON
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
            if data:
                columns = list(data[0].keys())
                logger.info(f"📋 Columnas detectadas: {len(columns)} ({', '.join(columns[:5])}{'...' if len(columns) > 5 else ''})")
            
            # Limpiar datos antes de insertar
            clean_data = self._clean_data_for_insert(data, table_name)
            
            if not clean_data:
                logger.warning(f"⚠️ No hay datos válidos para insertar en {table_name}")
                return False, 0
            
            # Preparar consulta de UPSERT 
            if clean_data:
                columns = list(clean_data[0].keys())
                placeholders = ', '.join([f':{col}' for col in columns])
                column_names = ', '.join(columns)
                
                # Obtener la clave primaria de la tabla
                primary_key = self.get_primary_key(table_name)
                
                # Construir la consulta UPSERT
                if isinstance(primary_key, list):
                    # Clave compuesta
                    conflict_columns = ", ".join(primary_key)
                    update_columns = [col for col in columns if col not in primary_key]
                else:
                    # Clave simple (caso de BPIN para unidades_proyecto)
                    conflict_columns = primary_key
                    update_columns = [col for col in columns if col != primary_key]
                
                # Construir la consulta SQL con UPSERT
                if update_columns:
                    update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                    insert_sql = f"""
                    INSERT INTO {table_name} ({column_names}) 
                    VALUES ({placeholders})
                    ON CONFLICT ({conflict_columns}) DO UPDATE SET
                    {update_clause}
                    """
                else:
                    # Si no hay columnas para actualizar, solo hacer INSERT ... ON CONFLICT DO NOTHING
                    insert_sql = f"""
                    INSERT INTO {table_name} ({column_names}) 
                    VALUES ({placeholders})
                    ON CONFLICT ({conflict_columns}) DO NOTHING
                    """
            
            # Insertar datos por lotes
            batch_size = 1000
            successful_inserts = 0
            failed_inserts = 0
            
            with tqdm(total=len(clean_data), desc=f"Insertando en {table_name}", unit="registros") as pbar:
                with self.engine.connect() as connection:
                    for i in range(0, len(clean_data), batch_size):
                        batch = clean_data[i:i + batch_size]
                        
                        try:
                            # Intentar insertar el lote completo
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
                                
                    connection.commit()
            
            # Reportar resultados y métricas
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
        """Limpia y prepara los datos para inserción, manejando valores NULL y tipos según la tabla específica."""
        clean_data = []
        rejected_count = 0
        
        for record in data:
            # Verificar BPIN al inicio - rechazar si es NULL
            if 'bpin' in record and (record['bpin'] is None or record['bpin'] == '' or record['bpin'] == 'None'):
                rejected_count += 1
                continue  # Saltar este registro, no todo el bucle
            
            cleaned_record = {}
            
            for key, value in record.items():
                # Manejar valores nulos
                if value is None or value == '' or value == 'None':
                    cleaned_record[key] = None
                # Manejar BPIN específicamente
                elif key == 'bpin':
                    try:
                        cleaned_record[key] = int(float(str(value))) if value else None
                    except (ValueError, TypeError):
                        rejected_count += 1
                        break  # Saltar este registro
                # Manejar identificador para unidades de proyecto (debe ser string)
                elif key == 'identificador':
                    if value is not None:
                        cleaned_record[key] = str(value)
                    else:
                        cleaned_record[key] = None
                # Manejar números enteros
                elif key in ['bpin', 'bp', 'cod_contrato', 'cod_proceso', 'cod_actividad', 'cod_producto', 'cod_centro_gestor'] and value:
                    try:
                        if isinstance(value, str):
                            # Limpiar strings que pueden tener números
                            value = value.strip()
                            if value.isdigit():
                                cleaned_record[key] = int(value)
                            elif '.' in value:
                                cleaned_record[key] = int(float(value))
                            else:
                                cleaned_record[key] = value
                        else:
                            cleaned_record[key] = int(value)
                    except (ValueError, TypeError):
                        cleaned_record[key] = value
                # Para campos monetarios y decimales
                elif key in ['valor_contrato', 'ppto_base', 'pagos_realizados', 'ejecucion_financiera_obra', 
                           'adiciones', 'creditos', 'contracreditos', 'reducciones', 'aplazamiento', 'desaplazamiento',
                           'ppto_inicial', 'ppto_modificado', 'ejecucion', 'pagos', 'ppto_disponible',
                           'avance_fisico_obra', 'avance_físico_obra', 'longitud_proyectada', 'longitud_ejecutada',
                           'usuarios_beneficiarios']:
                    try:
                        if value is None or value == '':
                            cleaned_record[key] = 0 if key in ['adiciones', 'creditos', 'contracreditos', 'reducciones', 'aplazamiento', 'desaplazamiento'] else None
                        else:
                            cleaned_record[key] = float(value)
                    except (ValueError, TypeError):
                        cleaned_record[key] = 0 if key in ['adiciones', 'creditos', 'contracreditos', 'reducciones', 'aplazamiento', 'desaplazamiento'] else None
                # Para fechas
                elif key in ['fecha_inicio_planeado', 'fecha_fin_planeado', 'fecha_inicio_real', 'fecha_fin_real', 'fecha_actualizacion']:
                    if value and isinstance(value, str) and value.strip():
                        cleaned_record[key] = value.strip()
                    else:
                        cleaned_record[key] = None
                # Para campos booleanos
                elif key in ['es_centro_gravedad']:
                    if value is None or value == '':
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = bool(value)
                # Para strings regulares
                else:
                    cleaned_record[key] = value
            
            # Solo agregar si el registro tiene los campos requeridos y BPIN válido
            if 'bpin' not in cleaned_record:
                # Registros sin BPIN son válidos para algunas tablas
                clean_data.append(cleaned_record)
            elif cleaned_record.get('bpin') is not None:
                # Registros con BPIN válido
                clean_data.append(cleaned_record)
            # Los registros con BPIN NULL ya fueron rechazados arriba
        
        # Reportar registros rechazados si los hay
        if rejected_count > 0:
            logger.warning(f"⚠️ {table_name}: {rejected_count} registros rechazados por BPIN NULL/inválido")
        
        return clean_data

    def load_available_data(self) -> Dict[str, int]:
        """Busca y carga todos los datos disponibles desde archivos JSON con verificación incremental."""
        logger.info("📦 Iniciando búsqueda y carga de datos...")
        
        loaded_counts = {}
        
        # Mapeo de archivos a tablas CON DIRECTORIOS ESPECÍFICOS (siguiendo la API)
        file_table_mapping = {
            # Contratos SECOP
            ("transformation_app/app_outputs/contratos_secop_output", "contratos.json"): "contratos",
            ("transformation_app/app_outputs/contratos_secop_output", "contratos_valores.json"): "contratos_valores",
            
            # Ejecución Presupuestal
            ("transformation_app/app_outputs/ejecucion_presupuestal_outputs", "movimientos_presupuestales.json"): "movimientos_presupuestales",
            ("transformation_app/app_outputs/ejecucion_presupuestal_outputs", "ejecucion_presupuestal.json"): "ejecucion_presupuestal",
            ("transformation_app/app_outputs/ejecucion_presupuestal_outputs", "datos_caracteristicos_proyectos.json"): "datos_caracteristicos_proyectos",
            
            # Seguimiento PA
            ("transformation_app/app_outputs/seguimiento_pa_outputs", "seguimiento_pa.json"): "seguimiento_pa",
            ("transformation_app/app_outputs/seguimiento_pa_outputs", "seguimiento_productos_pa.json"): "seguimiento_productos_pa",
            ("transformation_app/app_outputs/seguimiento_pa_outputs", "seguimiento_actividades_pa.json"): "seguimiento_actividades_pa",
            
            # Unidades de Proyecto
            ("transformation_app/app_outputs/unidades_proyecto_outputs", "unidad_proyecto_infraestructura_equipamientos.json"): "unidades_proyecto_infraestructura_equipamientos",
            ("transformation_app/app_outputs/unidades_proyecto_outputs", "unidad_proyecto_infraestructura_vial.json"): "unidades_proyecto_infraestructura_vial"
        }
        
        found_files = []
        for (directory, filename), table_name in file_table_mapping.items():
            full_path = os.path.join(directory, filename)
            if os.path.exists(full_path):
                found_files.append((full_path, table_name, filename))
        
        logger.info(f"📋 Encontrados {len(found_files)} archivos para procesar")
        
        if not found_files:
            logger.warning("⚠️ No se encontraron archivos JSON para cargar")
            return loaded_counts
        
        # Procesar archivos con barra de progreso
        with tqdm(total=len(found_files), desc="Procesando", unit="archivos") as pbar:
            for json_path, table_name, filename in found_files:
                pbar.set_description(f"Procesando {filename}")
                
                success, count = self.load_json_data_to_table(json_path, table_name)
                if success and count > 0:
                    loaded_counts[table_name] = count
                    logger.info(f"✅ {table_name}: {count:,} registros cargados correctamente")
                elif not success:
                    logger.warning(f"⚠️ {table_name}: No se cargaron datos desde {filename}")
                
                pbar.update(1)
        
        # Resumen final
        logger.info("=" * 60)
        logger.info(f"🎉 Carga completada: {len(loaded_counts)}/{len(found_files)} archivos procesados exitosamente")
        logger.info(f"📊 Total de registros cargados: {sum(loaded_counts.values()):,}")
        
        if loaded_counts:
            logger.info("📋 Resumen por tabla:")
            for table, count in loaded_counts.items():
                logger.info(f"   • {table}: {count:,} registros")
        
        return loaded_counts

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

    def run_complete_initialization(self) -> bool:
        """Ejecuta la inicialización completa de la base de datos con métricas."""
        try:
            logger.info("🚀 Iniciando inicialización completa de la base de datos")
            logger.info("=" * 70)
            
            # 1. Verificar conexión
            if not self.test_connection():
                logger.error("❌ No se pudo establecer conexión a la base de datos")
                return False
            
            # 2. Obtener estado actual
            existing_tables = self.get_existing_tables()
            
            # 3. Crear/verificar estructura de tablas
            self.create_tables_with_correct_schema()
            
            # 4. Crear índices de rendimiento
            self.create_performance_indexes()
            
            # 5. Cargar datos disponibles
            logger.info("=" * 50)
            logger.info("📦 FASE DE CARGA DE DATOS")
            loaded_counts = self.load_available_data()
            
            # 6. Reporte final
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
            
            # 7. Generar reporte detallado
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

def main():
    """Función principal para ejecutar la inicialización completa"""
    print("🏛️ API Dashboard Alcaldía de Cali - Inicializador Unificado")
    print("🔧 Estructura + Datos para entornos Locales y Railway")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        # Crear instancia del inicializador
        initializer = DatabaseInitializer()
        
        # Ejecutar inicialización completa
        success = initializer.run_complete_initialization()
        
        # Calcular tiempo total
        end_time = time.time()
        total_time = end_time - start_time
        
        if success:
            print(f"\n⏱️ Tiempo total de ejecución: {total_time:.2f} segundos")
            print("✅ Base de datos completamente configurada y lista para producción")
            print("🚀 Puedes iniciar tu API con: uvicorn fastapi_project.main:app --reload")
            sys.exit(0)
        else:
            print("❌ Error en la inicialización. Revisar logs para detalles.")
            print("📋 Log guardado en: database_init.log")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}")
        print("❌ Error fatal durante la ejecución. Revisar logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
