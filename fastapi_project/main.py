"""
FastAPI application exposing budget and project endpoints, admin diagnostics,
and units of project (infraestructura) management.

- Database: PostgreSQL via SQLAlchemy SessionLocal and engine
- Validation: Pydantic schemas in fastapi_project.schemas
- Purpose: Route definitions, data loaders (bulk upsert), and admin tools

Note: This file intentionally avoids complex business logic. Keep edits
documentational where possible; changing behavior requires updating docs.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import os
import unicodedata
import re
from typing import List, Dict, Any, Type, TypeVar, Optional
import time
import json
import logging
from contextlib import contextmanager

from fastapi_project import models, schemas
from fastapi_project.database import SessionLocal, engine, get_database_info, test_connection
import glob

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verificar conexión a la base de datos al iniciar
if not test_connection():
    logger.error("❌ No se puede conectar a la base de datos. Verificar configuración.")
    raise Exception("Error de conexión a la base de datos")

# Crear tablas si no existen (usando el inicializador automático)
def initialize_database():
    """Inicializar la base de datos con manejo robusto de errores"""
    try:
        logger.info("🔄 Iniciando proceso de inicialización de base de datos...")
        
        # Intentar usar el inicializador automático
        try:
            from database_initializer import DatabaseInitializer
            logger.info("📦 DatabaseInitializer importado correctamente")
            
            initializer = DatabaseInitializer()
            logger.info("🔍 Verificando esquema de base de datos...")
            
            if not initializer.verify_final_schema():
                logger.info("🔄 Esquema no verificado, ejecutando inicialización automática...")
                initializer.initialize_database()
                logger.info("✅ Inicialización automática completada")
            else:
                logger.info("✅ Esquema de base de datos ya está verificado")
                
        except ImportError as ie:
            logger.warning(f"⚠️ No se pudo importar DatabaseInitializer: {ie}")
            logger.info("🔄 Usando inicialización tradicional...")
            models.Base.metadata.create_all(bind=engine)
            logger.info("✅ Inicialización tradicional completada")
            
        except Exception as e:
            logger.error(f"❌ Error en inicialización automática: {e}")
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.info("🔄 Intentando método de respaldo...")
            try:
                models.Base.metadata.create_all(bind=engine)
                logger.info("✅ Método de respaldo completado")
            except Exception as fallback_error:
                logger.error(f"❌ Error crítico en método de respaldo: {fallback_error}")
                raise Exception(f"No se pudo inicializar la base de datos: {fallback_error}")
                
    except Exception as critical_error:
        logger.error(f"❌ Error crítico durante inicialización: {critical_error}")
        raise

# Ejecutar inicialización
try:
    initialize_database()
except Exception as init_error:
    logger.error(f"❌ Fallo crítico en inicialización de base de datos: {init_error}")
    # No elevar la excepción para permitir que la aplicación continúe
    logger.warning("⚠️ La aplicación continuará sin inicialización completa")

# Información de la aplicación
app_info = get_database_info()
logger.info(f"📊 Conectado a {app_info['database_type']} en {app_info['server']}:{app_info['port']}")

app = FastAPI(
    title="API Proyectos Alcaldía de Santiago de Cali",
    description="Un API que sirve como fuente única de verdad que es confiable y validada para el uso de la Secretaría de Gobierno",
    version="2.0.0",  # Versión alineada con documentación del proyecto
    docs_url="/docs",
    redoc_url="/redoc"
)

# Habilitar CORS para permitir consumir la API desde apps web (Leaflet, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obtener las rutas de todos los archivos dentro de la carpeta especificada
OUTPUTS_DIR = "transformation_app/app_outputs/ejecucion_presupuestal_outputs"
JSON_FILE_PATHS = glob.glob(os.path.join(OUTPUTS_DIR, "*.json"))

# Rutas para unidades de proyecto
UNIDADES_PROYECTO_DIR = "transformation_app/app_outputs/unidades_proyecto_outputs"
UNIDADES_PROYECTO_JSON_PATHS = glob.glob(os.path.join(UNIDADES_PROYECTO_DIR, "*.json"))

# Mapeo de archivos JSON a modelos y esquemas
DATA_MAPPING = {
    "datos_caracteristicos_proyectos.json": {
        "model": models.DatosCaracteristicosProyecto,
        "schema": schemas.DatosCaracteristicosProyecto,
        "primary_key": "bpin"
    },
    "movimientos_presupuestales.json": {
        "model": models.MovimientoPresupuestal,
        "schema": schemas.MovimientoPresupuestal,
        "primary_key": ["bpin", "periodo"]  # Clave compuesta
    },
    "ejecucion_presupuestal.json": {
        "model": models.EjecucionPresupuestal,
        "schema": schemas.EjecucionPresupuestal,
        "primary_key": ["bpin", "periodo"]  # Clave compuesta
    }
}

# PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN - Mapeo para seguimiento PA
SEGUIMIENTO_PA_MAPPING = {
    "seguimiento_actividades_pa.json": {
        "model": models.SeguimientoActividadPA,
        "schema": schemas.SeguimientoActividadPA,
        "primary_key": ["bpin", "cod_actividad", "periodo_corte"]  # Clave compuesta
    },
    "seguimiento_productos_pa.json": {
        "model": models.SeguimientoProductoPA,
        "schema": schemas.SeguimientoProductoPA,
        "primary_key": ["bpin", "cod_producto", "periodo_corte"]  # Clave compuesta
    },
    "seguimiento_pa.json": {
        "model": models.SeguimientoPA,
        "schema": schemas.SeguimientoPA,
        "primary_key": "id_seguimiento_pa"  # Clave primaria simple auto-increment
    }
}

# Mapeo para unidades de proyecto
UNIDADES_PROYECTO_MAPPING = {
    "unidad_proyecto_infraestructura_equipamientos.json": {
        "model": models.UnidadProyectoInfraestructuraEquipamientos,
        "schema": schemas.UnidadProyectoInfraestructuraEquipamientos,
        "primary_key": "bpin"
    },
    "unidad_proyecto_infraestructura_vial.json": {
        "model": models.UnidadProyectoInfraestructuraVial,
        "schema": schemas.UnidadProyectoInfraestructuraVial,
        "primary_key": "bpin"
    }
}

# Dependency para obtener la sesión de la base de datos
def get_db():
    """Yield a database session bound to the global engine.

    Scoped for one request; ensures proper close even on exceptions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_transaction():
    """Context manager para manejar transacciones de base de datos.

    Commits on success and rolls back on any exception to preserve consistency.
    Use inside request handlers for atomic multi-table operations.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def load_json_file(filename: str) -> List[Dict[str, Any]]:
    """Carga un archivo JSON (ejecución presupuestal) y retorna los datos."""
    file_path = next((path for path in JSON_FILE_PATHS if os.path.basename(path) == filename), None)
    if not file_path:
        raise FileNotFoundError(f"Archivo {filename} no encontrado en la ruta especificada")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"Error al decodificar el archivo JSON: {filename}")

def load_unidades_proyecto_json_file(filename: str) -> List[Dict[str, Any]]:
    """Carga un archivo JSON de unidades de proyecto y retorna los datos."""
    file_path = next((path for path in UNIDADES_PROYECTO_JSON_PATHS if os.path.basename(path) == filename), None)
    if not file_path:
        raise FileNotFoundError(f"Archivo {filename} no encontrado en {UNIDADES_PROYECTO_DIR}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"Error al decodificar el archivo JSON: {filename}")

# PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN - Funciones de carga de datos
def load_seguimiento_pa_json_file(filename: str):
    """Cargar archivo JSON desde el directorio de seguimiento PA"""
    file_path = f"transformation_app/app_outputs/seguimiento_pa_outputs/{filename}"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_and_validate_seguimiento_pa_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función específica para cargar, validar y guardar datos de seguimiento PA.
    Solo procesa registros nuevos o diferentes (upsert inteligente).
    """
    try:
        # Verificar si el archivo existe
        file_path = f"transformation_app/app_outputs/seguimiento_pa_outputs/{filename}"
        if not os.path.exists(file_path):
            logger.warning(f"Archivo {filename} no encontrado en {file_path}")
            raise FileNotFoundError(f"Archivo {filename} no encontrado")
        
        # Cargar datos del archivo JSON desde el directorio de seguimiento PA
        raw_data = load_seguimiento_pa_json_file(filename)
        
        if not raw_data:
            logger.warning(f"Archivo {filename} está vacío o no contiene datos válidos")
            return []
        
        # Validar datos usando el esquema de Pydantic
        validated_data = []
        validation_errors = []
        
        for i, item in enumerate(raw_data):
            try:
                validated_item = schema_class(**item)
                validated_data.append(validated_item)
            except Exception as ve:
                validation_errors.append(f"Registro {i}: {str(ve)}")
        
        if validation_errors:
            logger.warning(f"Se encontraron {len(validation_errors)} errores de validación en {filename}")
            for error in validation_errors[:5]:  # Mostrar solo los primeros 5 errores
                logger.warning(f"  {error}")
            if len(validation_errors) > 5:
                logger.warning(f"  ... y {len(validation_errors) - 5} errores más")
        
        if not validated_data:
            logger.warning(f"No se pudieron validar datos en {filename}")
            return []
        
        # Convertir a diccionarios para la inserción en BD
        data_dicts = [item.dict() for item in validated_data]
        
        # Realizar bulk upsert en la base de datos (solo registros nuevos/diferentes)
        bulk_upsert_data(db, model_class, data_dicts, primary_key)
        
        logger.info(f"Procesados {len(validated_data)} registros válidos de {len(raw_data)} totales en {filename}")
        return validated_data
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado")
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=400, detail=f"Error al decodificar el archivo JSON {filename}: {str(je)}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Error de validación en {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def bulk_upsert_data(db: Session, model_class, data: List[Dict[str, Any]], primary_key):
    """
    Realiza una inserción/actualización masiva eficiente usando PostgreSQL UPSERT.
    Soporta tanto claves primarias simples como compuestas (ON CONFLICT).
    Solo procesa registros nuevos o diferentes para optimizar el rendimiento.
    """
    if not data:
        logger.info(f"No hay datos para procesar en {model_class.__tablename__}")
        return
    
    try:
        # Preparar los datos para inserción
        table = model_class.__table__
        table_name = table.name
        
        # Obtener conteo antes de la operación
        count_before = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        # Crear la consulta de UPSERT usando ON CONFLICT
        columns = list(data[0].keys())
        values_placeholder = ", ".join([f":{col}" for col in columns])
        
        # Manejar claves primarias simples y compuestas
        if isinstance(primary_key, list):
            # Clave compuesta
            conflict_columns = ", ".join(primary_key)
            update_columns = [col for col in columns if col not in primary_key]
        else:
            # Clave simple
            conflict_columns = primary_key
            update_columns = [col for col in columns if col != primary_key]
        
        # Construir la consulta SQL
        if update_columns:
            update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
            insert_stmt = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({values_placeholder})
            ON CONFLICT ({conflict_columns}) DO UPDATE SET
            {update_clause}
            """
        else:
            # Si no hay columnas para actualizar, solo hacer INSERT ... ON CONFLICT DO NOTHING
            insert_stmt = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({values_placeholder})
            ON CONFLICT ({conflict_columns}) DO NOTHING
            """
        
        # Ejecutar la inserción masiva
        result = db.execute(text(insert_stmt), data)
        
        # Obtener conteo después de la operación
        count_after = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        
        records_added = count_after - count_before
        
        logger.info(f"Operación UPSERT en {table_name}: {len(data)} registros procesados, {records_added} nuevos registros añadidos")
        logger.info(f"Estado de la tabla {table_name}: {count_before} → {count_after} registros")
        
    except Exception as e:
        logger.error(f"Error durante bulk upsert para {model_class.__name__}: {str(e)}")
        raise

def load_geojson_file(filename: str) -> dict:
    """Cargar archivo GeoJSON de la carpeta de outputs para servirlo vía API."""
    file_path = f"transformation_app/app_outputs/unidades_proyecto_outputs/{filename}"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Función auxiliar para cargar y validar datos
def load_and_validate_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función genérica para cargar, validar y guardar datos en la base de datos.
    Soporta claves primarias simples y compuestas y aplica bulk upsert.
    Solo procesa registros nuevos o diferentes (upsert inteligente).
    """
    try:
        # Verificar si el archivo existe
        file_path = f"transformation_app/app_outputs/ejecucion_presupuestal_outputs/{filename}"
        if not os.path.exists(file_path):
            logger.warning(f"Archivo {filename} no encontrado en {file_path}")
            raise FileNotFoundError(f"Archivo {filename} no encontrado")
        
        # Cargar datos del archivo JSON
        raw_data = load_json_file(filename)
        
        if not raw_data:
            logger.warning(f"Archivo {filename} está vacío o no contiene datos válidos")
            return []
        
        # Validar datos usando el esquema de Pydantic
        validated_data = []
        validation_errors = []
        
        for i, item in enumerate(raw_data):
            try:
                validated_item = schema_class(**item)
                validated_data.append(validated_item)
            except Exception as ve:
                validation_errors.append(f"Registro {i}: {str(ve)}")
        
        if validation_errors:
            logger.warning(f"Se encontraron {len(validation_errors)} errores de validación en {filename}")
            for error in validation_errors[:5]:  # Mostrar solo los primeros 5 errores
                logger.warning(f"  {error}")
            if len(validation_errors) > 5:
                logger.warning(f"  ... y {len(validation_errors) - 5} errores más")
        
        if not validated_data:
            logger.warning(f"No se pudieron validar datos en {filename}")
            return []
        
        # Convertir a diccionarios para la inserción en BD
        data_dicts = [item.dict() for item in validated_data]
        
        # Realizar bulk upsert en la base de datos (solo registros nuevos/diferentes)
        bulk_upsert_data(db, model_class, data_dicts, primary_key)
        
        logger.info(f"Procesados {len(validated_data)} registros válidos de {len(raw_data)} totales en {filename}")
        return validated_data
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado")
    except json.JSONDecodeError as je:
        raise HTTPException(status_code=400, detail=f"Error al decodificar el archivo JSON {filename}: {str(je)}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Error de validación en {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def load_and_validate_unidades_proyecto_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función específica para cargar, validar y guardar datos de unidades de proyecto.
    Excluye las columnas geométricas de los archivos JSON antes de validar.
    """
    try:
        # Cargar datos del archivo JSON desde el directorio de unidades de proyecto
        raw_data = load_unidades_proyecto_json_file(filename)

        # Preprocesar datos: Convertir valores numéricos en 'barrio_vereda' y 'identificador' a cadenas
        for item in raw_data:
            if isinstance(item.get('barrio_vereda'), int):
                item['barrio_vereda'] = str(item['barrio_vereda'])
            if isinstance(item.get('identificador'), int):
                item['identificador'] = str(item['identificador'])

        # Filtrar datos removiendo columnas geométricas para archivos JSON
        filtered_data = []
        for item in raw_data:
            # Crear una copia sin las columnas geométricas
            filtered_item = {k: v for k, v in item.items() if k not in ['geom', 'geometry', 'longitude', 'latitude', 'geometry_bounds', 'geometry_type']}
            filtered_data.append(filtered_item)

        # Validar datos usando el esquema de Pydantic
        validated_data = [schema_class(**item) for item in filtered_data]

        # Convertir a diccionarios para la inserción en BD
        data_dicts = [item.dict() for item in validated_data]

        # Realizar bulk upsert en la base de datos
        bulk_upsert_data(db, model_class, data_dicts, primary_key)

        return validated_data

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"Error al decodificar el archivo JSON: {filename}")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Error de validación en {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

# ================================================================================================================
# MÉTODOS POST - REFACTORIZADOS PARA EFICIENCIA Y CONEXIÓN A POSTGRESQL
# ================================================================================================================

@app.post('/datos_caracteristicos_proyectos', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.DatosCaracteristicosProyecto])
def load_datos_caracteristicos_proyectos(db: Session = Depends(get_db)):
    """Carga datos característicos de proyectos desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["datos_caracteristicos_proyectos.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "datos_caracteristicos_proyectos.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/movimientos_presupuestales', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.MovimientoPresupuestal])
def load_movimientos_presupuestales(db: Session = Depends(get_db)):
    """Carga movimientos presupuestales desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["movimientos_presupuestales.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "movimientos_presupuestales.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/ejecucion_presupuestal', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.EjecucionPresupuestal])
def load_ejecucion_presupuestal(db: Session = Depends(get_db)):
    """Carga ejecución presupuestal desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["ejecucion_presupuestal.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "ejecucion_presupuestal.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

# ================================================================================================================
# PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN - MÉTODOS POST
# ================================================================================================================

@app.post('/seguimiento_actividades_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoActividadPA])
def load_seguimiento_actividades_pa(db: Session = Depends(get_db)):
    """Carga actividades de seguimiento PA desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = SEGUIMIENTO_PA_MAPPING["seguimiento_actividades_pa.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_seguimiento_pa_data(
            "seguimiento_actividades_pa.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/seguimiento_productos_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoProductoPA])
def load_seguimiento_productos_pa(db: Session = Depends(get_db)):
    """Carga productos de seguimiento PA desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = SEGUIMIENTO_PA_MAPPING["seguimiento_productos_pa.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_seguimiento_pa_data(
            "seguimiento_productos_pa.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/seguimiento_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoPA])
def load_seguimiento_pa(db: Session = Depends(get_db)):
    """Carga resumen de seguimiento PA desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = SEGUIMIENTO_PA_MAPPING["seguimiento_pa.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_seguimiento_pa_data(
            "seguimiento_pa.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/load_all_seguimiento_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"])
def load_all_seguimiento_pa(db: Session = Depends(get_db)):
    """
    Carga todos los datos de seguimiento PA de manera robusta y tolerante a fallos.
    - Si no encuentra archivos, simplemente los omite
    - Solo carga datos nuevos o diferentes (upsert inteligente)
    - Continúa con otros archivos aunque algunos fallen
    """
    results = {}
    successful_loads = 0
    failed_loads = 0
    
    try:
        with get_db_transaction() as db_trans:
            for filename, mapping in SEGUIMIENTO_PA_MAPPING.items():
                try:
                    logger.info(f"Intentando cargar {filename}...")
                    start_time = time.time()
                    
                    # Verificar si el archivo existe antes de intentar cargarlo
                    file_path = f"transformation_app/app_outputs/seguimiento_pa_outputs/{filename}"
                    if not os.path.exists(file_path):
                        logger.warning(f"Archivo {filename} no encontrado en {file_path}, omitiendo...")
                        results[filename] = {
                            "status": "skipped",
                            "reason": "file_not_found",
                            "message": f"Archivo {filename} no encontrado"
                        }
                        continue
                    
                    # Intentar cargar los datos
                    validated_data = load_and_validate_seguimiento_pa_data(
                        filename,
                        mapping["schema"],
                        db_trans,
                        mapping["model"],
                        mapping["primary_key"]
                    )
                    
                    end_time = time.time()
                    load_time = end_time - start_time
                    
                    results[filename] = {
                        "status": "success",
                        "records_processed": len(validated_data),
                        "load_time_seconds": round(load_time, 2)
                    }
                    successful_loads += 1
                    logger.info(f"✓ {filename}: {len(validated_data)} registros procesados en {load_time:.2f}s")
                    
                except FileNotFoundError:
                    logger.warning(f"Archivo {filename} no encontrado, omitiendo...")
                    results[filename] = {
                        "status": "skipped",
                        "reason": "file_not_found",
                        "message": f"Archivo {filename} no encontrado"
                    }
                except json.JSONDecodeError as je:
                    logger.error(f"Error JSON en {filename}: {str(je)}")
                    results[filename] = {
                        "status": "error",
                        "reason": "json_decode_error",
                        "message": f"Error al decodificar JSON: {str(je)}"
                    }
                    failed_loads += 1
                except Exception as e:
                    logger.error(f"Error procesando {filename}: {str(e)}")
                    results[filename] = {
                        "status": "error",
                        "reason": "processing_error", 
                        "message": str(e)
                    }
                    failed_loads += 1
        
        # Preparar respuesta final
        total_files = len(SEGUIMIENTO_PA_MAPPING)
        
        if successful_loads == 0 and failed_loads > 0:
            return {
                "status": "error",
                "message": "No se pudieron cargar datos de seguimiento PA de ningún archivo",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results
            }
        elif failed_loads > 0:
            return {
                "status": "partial_success",
                "message": f"Se cargaron {successful_loads} de {total_files} archivos de seguimiento PA exitosamente",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results
            }
        else:
            return {
                "status": "success",
                "message": f"Todos los archivos disponibles de seguimiento PA ({successful_loads}) fueron procesados exitosamente",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results,
                "total_time": sum(r.get("load_time_seconds", 0) for r in results.values() if r.get("status") == "success")
            }
        
    except Exception as e:
        logger.error(f"Error crítico durante la carga masiva de seguimiento PA: {str(e)}")
        return {
            "status": "critical_error",
            "message": f"Error crítico durante la carga de seguimiento PA: {str(e)}",
            "details": results
        }

# Endpoint para cargar todos los datos de ejecución presupuestal de una vez (más eficiente)
@app.post('/load_all_ejecucion_presupuestal_data', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"])
def load_all_data(db: Session = Depends(get_db)):
    """
    Carga todos los datos de una vez de manera robusta y tolerante a fallos.
    - Si no encuentra archivos, simplemente los omite
    - Solo carga datos nuevos o diferentes (upsert inteligente)
    - Continúa con otros archivos aunque algunos fallen
    """
    results = {}
    successful_loads = 0
    failed_loads = 0
    
    try:
        with get_db_transaction() as db_trans:
            for filename, mapping in DATA_MAPPING.items():
                try:
                    logger.info(f"Intentando cargar {filename}...")
                    start_time = time.time()
                    
                    # Verificar si el archivo existe antes de intentar cargarlo
                    file_path = f"transformation_app/app_outputs/ejecucion_presupuestal_outputs/{filename}"
                    if not os.path.exists(file_path):
                        logger.warning(f"Archivo {filename} no encontrado en {file_path}, omitiendo...")
                        results[filename] = {
                            "status": "skipped",
                            "reason": "file_not_found",
                            "message": f"Archivo {filename} no encontrado"
                        }
                        continue
                    
                    # Intentar cargar los datos
                    data = load_and_validate_data(
                        filename,
                        mapping["schema"],
                        db_trans,
                        mapping["model"],
                        mapping["primary_key"]
                    )
                    
                    load_time = time.time() - start_time
                    results[filename] = {
                        "status": "success",
                        "records_processed": len(data),
                        "load_time_seconds": round(load_time, 2)
                    }
                    successful_loads += 1
                    logger.info(f"✓ {filename}: {len(data)} registros procesados en {load_time:.2f}s")
                    
                except FileNotFoundError:
                    logger.warning(f"Archivo {filename} no encontrado, omitiendo...")
                    results[filename] = {
                        "status": "skipped",
                        "reason": "file_not_found",
                        "message": f"Archivo {filename} no encontrado"
                    }
                except json.JSONDecodeError as je:
                    logger.error(f"Error JSON en {filename}: {str(je)}")
                    results[filename] = {
                        "status": "error",
                        "reason": "json_decode_error",
                        "message": f"Error al decodificar JSON: {str(je)}"
                    }
                    failed_loads += 1
                except Exception as e:
                    logger.error(f"Error procesando {filename}: {str(e)}")
                    results[filename] = {
                        "status": "error", 
                        "reason": "processing_error",
                        "message": str(e)
                    }
                    failed_loads += 1
        
        # Preparar respuesta final
        total_files = len(DATA_MAPPING)
        
        if successful_loads == 0 and failed_loads > 0:
            return {
                "status": "error",
                "message": "No se pudieron cargar datos de ningún archivo",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results
            }
        elif failed_loads > 0:
            return {
                "status": "partial_success",
                "message": f"Se cargaron {successful_loads} de {total_files} archivos exitosamente",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results
            }
        else:
            return {
                "status": "success",
                "message": f"Todos los archivos disponibles ({successful_loads}) fueron procesados exitosamente",
                "summary": {
                    "total_files": total_files,
                    "successful": successful_loads,
                    "failed": failed_loads,
                    "skipped": total_files - successful_loads - failed_loads
                },
                "details": results
            }
        
    except Exception as e:
        logger.error(f"Error crítico durante la carga masiva: {str(e)}")
        return {
            "status": "critical_error",
            "message": f"Error crítico durante la carga: {str(e)}",
            "details": results
        }

# ================================================================================================================
# MÉTODOS POST - UNIDADES DE PROYECTO
# ================================================================================================================

@app.post('/unidades_proyecto/equipamientos', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=List[schemas.UnidadProyectoInfraestructuraEquipamientos])
def load_unidades_proyecto_equipamientos(db: Session = Depends(get_db)):
    """Carga unidades de proyecto de infraestructura de equipamientos desde JSON a PostgreSQL"""
    mapping = UNIDADES_PROYECTO_MAPPING["unidad_proyecto_infraestructura_equipamientos.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_unidades_proyecto_data(
            "unidad_proyecto_infraestructura_equipamientos.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/unidades_proyecto/vial', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=List[schemas.UnidadProyectoInfraestructuraVial])
def load_unidades_proyecto_vial(db: Session = Depends(get_db)):
    """Carga unidades de proyecto de infraestructura vial desde JSON a PostgreSQL"""
    mapping = UNIDADES_PROYECTO_MAPPING["unidad_proyecto_infraestructura_vial.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_unidades_proyecto_data(
            "unidad_proyecto_infraestructura_vial.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )


# ================================================================================================================
# MÉTODOS GET - ENDPOINTS PARA CONSULTAR DATOS DESDE POSTGRESQL
# ================================================================================================================

@app.get('/datos_caracteristicos_proyectos', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.DatosCaracteristicosProyecto])
def get_datos_caracteristicos_proyectos(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    nombre_proyecto: Optional[str] = Query(None, description="Filtrar por nombre de proyecto (búsqueda parcial)"),
    nombre_centro_gestor: Optional[str] = Query(None, description="Filtrar por centro gestor (búsqueda parcial)"),
    tipo_gasto: Optional[str] = Query(None, description="Filtrar por tipo de gasto"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene datos característicos de proyectos desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **nombre_proyecto**: Filtrar por nombre de proyecto (búsqueda parcial)
    - **nombre_centro_gestor**: Filtrar por centro gestor (búsqueda parcial)
    - **tipo_gasto**: Filtrar por tipo de gasto
    - **anio**: Filtrar por año
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.DatosCaracteristicosProyecto)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.DatosCaracteristicosProyecto.bpin == bpin)
        
        if nombre_proyecto:
            query = query.filter(models.DatosCaracteristicosProyecto.nombre_proyecto.ilike(f"%{nombre_proyecto}%"))
        
        if nombre_centro_gestor:
            query = query.filter(models.DatosCaracteristicosProyecto.nombre_centro_gestor.ilike(f"%{nombre_centro_gestor}%"))
        
        if tipo_gasto:
            query = query.filter(models.DatosCaracteristicosProyecto.tipo_gasto.ilike(f"%{tipo_gasto}%"))
        
        if anio:
            query = query.filter(models.DatosCaracteristicosProyecto.anio == anio)
        
        # Aplicar paginación y ordenamiento para consistencia
        datos = query.order_by(models.DatosCaracteristicosProyecto.bpin)\
                     .offset(offset)\
                     .limit(limit)\
                     .all()
        
        logger.info(f"Consulta de datos característicos: {len(datos)} registros devueltos")
        return datos
        
    except Exception as e:
        logger.error(f"Error al consultar datos característicos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/movimientos_presupuestales', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.MovimientoPresupuestal])
def get_movimientos_presupuestales(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    periodo: Optional[str] = Query(None, description="Filtrar por período (ej: '2024-01' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene movimientos presupuestales desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **periodo**: Filtrar por período (puede ser año '2024' o año-mes '2024-01')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.MovimientoPresupuestal)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.MovimientoPresupuestal.bpin == bpin)
        
        if periodo:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo:
                query = query.filter(models.MovimientoPresupuestal.periodo == periodo)
            else:
                query = query.filter(models.MovimientoPresupuestal.periodo.like(f"{periodo}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        movimientos = query.order_by(models.MovimientoPresupuestal.bpin, models.MovimientoPresupuestal.periodo)\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
        
        logger.info(f"Consulta de movimientos presupuestales: {len(movimientos)} registros devueltos")
        return movimientos
        
    except Exception as e:
        logger.error(f"Error al consultar movimientos presupuestales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/ejecucion_presupuestal', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"], response_model=List[schemas.EjecucionPresupuestal])
def get_ejecucion_presupuestal(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    periodo: Optional[str] = Query(None, description="Filtrar por período (ej: '2024-01' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene ejecución presupuestal desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **periodo**: Filtrar por período (puede ser año '2024' o año-mes '2024-01')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.EjecucionPresupuestal)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.EjecucionPresupuestal.bpin == bpin)
        
        if periodo:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo:
                query = query.filter(models.EjecucionPresupuestal.periodo == periodo)
            else:
                query = query.filter(models.EjecucionPresupuestal.periodo.like(f"{periodo}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        ejecucion = query.order_by(models.EjecucionPresupuestal.bpin, models.EjecucionPresupuestal.periodo)\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        logger.info(f"Consulta de ejecución presupuestal: {len(ejecucion)} registros devueltos")
        return ejecucion
        
    except Exception as e:
        logger.error(f"Error al consultar ejecución presupuestal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

# ================================================================================================================
# PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN - MÉTODOS GET
# ================================================================================================================

@app.get('/seguimiento_actividades_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoActividadPA])
def get_seguimiento_actividades_pa(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_actividad: Optional[int] = Query(None, description="Filtrar por código de actividad"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte (ej: '2024-12' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene actividades de seguimiento PA desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **cod_actividad**: Filtrar por código de actividad específico
    - **periodo_corte**: Filtrar por período de corte (puede ser año '2024' o año-mes '2024-12')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.SeguimientoActividadPA)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.SeguimientoActividadPA.bpin == bpin)
        
        if cod_actividad:
            query = query.filter(models.SeguimientoActividadPA.cod_actividad == cod_actividad)
        
        if periodo_corte:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoActividadPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoActividadPA.periodo_corte.like(f"{periodo_corte}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        actividades = query.order_by(models.SeguimientoActividadPA.bpin, models.SeguimientoActividadPA.periodo_corte)\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
        
        logger.info(f"Consulta de actividades seguimiento PA: {len(actividades)} registros devueltos")
        return actividades
        
    except Exception as e:
        logger.error(f"Error al consultar actividades seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/seguimiento_productos_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoProductoPA])
def get_seguimiento_productos_pa(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_producto: Optional[int] = Query(None, description="Filtrar por código de producto"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte (ej: '2024-12' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene productos de seguimiento PA desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **cod_producto**: Filtrar por código de producto específico
    - **periodo_corte**: Filtrar por período de corte (puede ser año '2024' o año-mes '2024-12')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.SeguimientoProductoPA)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.SeguimientoProductoPA.bpin == bpin)
        
        if cod_producto:
            query = query.filter(models.SeguimientoProductoPA.cod_producto == cod_producto)
        
        if periodo_corte:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoProductoPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoProductoPA.periodo_corte.like(f"{periodo_corte}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        productos = query.order_by(models.SeguimientoProductoPA.bpin, models.SeguimientoProductoPA.periodo_corte)\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        logger.info(f"Consulta de productos seguimiento PA: {len(productos)} registros devueltos")
        return productos
        
    except Exception as e:
        logger.error(f"Error al consultar productos seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/seguimiento_pa', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"], response_model=List[schemas.SeguimientoPA])
def get_seguimiento_pa(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_actividad: Optional[int] = Query(None, description="Filtrar por código de actividad"),
    cod_producto: Optional[int] = Query(None, description="Filtrar por código de producto"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte (ej: '2024-12' o '2024')"),
    subdireccion_subsecretaria: Optional[str] = Query(None, description="Filtrar por subdirección/subsecretaría"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene resumen de seguimiento PA desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **cod_actividad**: Filtrar por código de actividad específico
    - **cod_producto**: Filtrar por código de producto específico
    - **periodo_corte**: Filtrar por período de corte (puede ser año '2024' o año-mes '2024-12')
    - **subdireccion_subsecretaria**: Filtrar por subdirección/subsecretaría
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.SeguimientoPA)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.SeguimientoPA.bpin == bpin)
        
        if cod_actividad:
            query = query.filter(models.SeguimientoPA.cod_actividad == cod_actividad)
        
        if cod_producto:
            query = query.filter(models.SeguimientoPA.cod_producto == cod_producto)
        
        if subdireccion_subsecretaria:
            query = query.filter(models.SeguimientoPA.subdireccion_subsecretaria.ilike(f"%{subdireccion_subsecretaria}%"))
        
        if periodo_corte:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoPA.periodo_corte.like(f"{periodo_corte}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        seguimiento = query.order_by(models.SeguimientoPA.bpin, models.SeguimientoPA.periodo_corte)\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
        
        logger.info(f"Consulta de resumen seguimiento PA: {len(seguimiento)} registros devueltos")
        return seguimiento
        
    except Exception as e:
        logger.error(f"Error al consultar resumen seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/seguimiento_actividades_pa/count', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"])
def get_seguimiento_actividades_pa_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_actividad: Optional[int] = Query(None, description="Filtrar por código de actividad"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de actividades de seguimiento PA con filtros opcionales"""
    try:
        query = db.query(models.SeguimientoActividadPA)
        
        if bpin:
            query = query.filter(models.SeguimientoActividadPA.bpin == bpin)
        
        if cod_actividad:
            query = query.filter(models.SeguimientoActividadPA.cod_actividad == cod_actividad)
        
        if periodo_corte:
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoActividadPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoActividadPA.periodo_corte.like(f"{periodo_corte}%"))
        
        count = query.count()
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error al contar actividades seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar conteo: {str(e)}")

@app.get('/seguimiento_productos_pa/count', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"])
def get_seguimiento_productos_pa_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_producto: Optional[int] = Query(None, description="Filtrar por código de producto"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de productos de seguimiento PA con filtros opcionales"""
    try:
        query = db.query(models.SeguimientoProductoPA)
        
        if bpin:
            query = query.filter(models.SeguimientoProductoPA.bpin == bpin)
        
        if cod_producto:
            query = query.filter(models.SeguimientoProductoPA.cod_producto == cod_producto)
        
        if periodo_corte:
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoProductoPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoProductoPA.periodo_corte.like(f"{periodo_corte}%"))
        
        count = query.count()
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error al contar productos seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar conteo: {str(e)}")

@app.get('/seguimiento_pa/count', tags=["PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN"])
def get_seguimiento_pa_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_actividad: Optional[int] = Query(None, description="Filtrar por código de actividad"),
    cod_producto: Optional[int] = Query(None, description="Filtrar por código de producto"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte"),
    subdireccion_subsecretaria: Optional[str] = Query(None, description="Filtrar por subdirección/subsecretaría"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de resumen de seguimiento PA con filtros opcionales"""
    try:
        query = db.query(models.SeguimientoPA)
        
        if bpin:
            query = query.filter(models.SeguimientoPA.bpin == bpin)
        
        if cod_actividad:
            query = query.filter(models.SeguimientoPA.cod_actividad == cod_actividad)
        
        if cod_producto:
            query = query.filter(models.SeguimientoPA.cod_producto == cod_producto)
        
        if subdireccion_subsecretaria:
            query = query.filter(models.SeguimientoPA.subdireccion_subsecretaria.ilike(f"%{subdireccion_subsecretaria}%"))
        
        if periodo_corte:
            if '-' in periodo_corte:
                query = query.filter(models.SeguimientoPA.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.SeguimientoPA.periodo_corte.like(f"{periodo_corte}%"))
        
        count = query.count()
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error al contar resumen seguimiento PA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar conteo: {str(e)}")

@app.get('/datos_caracteristicos_proyectos/count', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"])
def get_datos_caracteristicos_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    nombre_proyecto: Optional[str] = Query(None, description="Filtrar por nombre de proyecto"),
    nombre_centro_gestor: Optional[str] = Query(None, description="Filtrar por centro gestor"),
    tipo_gasto: Optional[str] = Query(None, description="Filtrar por tipo de gasto"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de datos característicos con filtros opcionales"""
    try:
        query = db.query(models.DatosCaracteristicosProyecto)
        
        if bpin:
            query = query.filter(models.DatosCaracteristicosProyecto.bpin == bpin)
        
        if nombre_proyecto:
            query = query.filter(models.DatosCaracteristicosProyecto.nombre_proyecto.ilike(f"%{nombre_proyecto}%"))
        
        if nombre_centro_gestor:
            query = query.filter(models.DatosCaracteristicosProyecto.nombre_centro_gestor.ilike(f"%{nombre_centro_gestor}%"))
        
        if tipo_gasto:
            query = query.filter(models.DatosCaracteristicosProyecto.tipo_gasto.ilike(f"%{tipo_gasto}%"))
        
        if anio:
            query = query.filter(models.DatosCaracteristicosProyecto.anio == anio)
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin, "nombre_proyecto": nombre_proyecto, "nombre_centro_gestor": nombre_centro_gestor, "tipo_gasto": tipo_gasto, "anio": anio}}
        
    except Exception as e:
        logger.error(f"Error al contar datos característicos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar conteo: {str(e)}")

@app.get('/movimientos_presupuestales/count', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"])
def get_movimientos_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    periodo: Optional[str] = Query(None, description="Filtrar por período"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de movimientos presupuestales con filtros opcionales"""
    try:
        query = db.query(models.MovimientoPresupuestal)
        
        if bpin:
            query = query.filter(models.MovimientoPresupuestal.bpin == bpin)
        
        if periodo:
            if '-' in periodo:
                query = query.filter(models.MovimientoPresupuestal.periodo == periodo)
            else:
                query = query.filter(models.MovimientoPresupuestal.periodo.like(f"{periodo}%"))
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin, "periodo": periodo}}
        
    except Exception as e:
        logger.error(f"Error al contar movimientos presupuestales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/ejecucion_presupuestal/count', tags=["PROYECTO: EJECUCIÓN PRESUPUESTAL"])
def get_ejecucion_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    periodo: Optional[str] = Query(None, description="Filtrar por período"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de ejecución presupuestal con filtros opcionales"""
    try:
        query = db.query(models.EjecucionPresupuestal)
        
        if bpin:
            query = query.filter(models.EjecucionPresupuestal.bpin == bpin)
        
        if periodo:
            if '-' in periodo:
                query = query.filter(models.EjecucionPresupuestal.periodo == periodo)
            else:
                query = query.filter(models.EjecucionPresupuestal.periodo.like(f"{periodo}%"))
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin, "periodo": periodo}}
        
    except Exception as e:
        logger.error(f"Error al contar ejecución presupuestal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

# ================================================================================================================
# MÉTODOS GET - UNIDADES DE PROYECTO
# ================================================================================================================

@app.get('/unidades_proyecto/equipamientos', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=List[schemas.UnidadProyectoInfraestructuraEquipamientos])
def get_unidades_proyecto_equipamientos(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene unidades de proyecto de infraestructura de equipamientos desde PostgreSQL con filtros
    
    - **bpin**: Filtrar por BPIN específico
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.UnidadProyectoInfraestructuraEquipamientos)
        
        # Aplicar filtro por BPIN si se proporciona
        if bpin:
            query = query.filter(models.UnidadProyectoInfraestructuraEquipamientos.bpin == bpin)
        
        # Aplicar paginación y ordenamiento
        equipamientos = query.order_by(models.UnidadProyectoInfraestructuraEquipamientos.bpin)\
                           .offset(offset)\
                           .limit(limit)\
                           .all()
        
        logger.info(f"Consulta de equipamientos: {len(equipamientos)} registros devueltos")
        return equipamientos
        
    except Exception as e:
        logger.error(f"Error al consultar equipamientos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/unidades_proyecto/vial', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=List[schemas.UnidadProyectoInfraestructuraVial])
def get_unidades_proyecto_vial(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene unidades de proyecto de infraestructura vial desde PostgreSQL con filtros
    
    - **bpin**: Filtrar por BPIN específico
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.UnidadProyectoInfraestructuraVial)
        
        # Aplicar filtro por BPIN si se proporciona
        if bpin:
            query = query.filter(models.UnidadProyectoInfraestructuraVial.bpin == bpin)
        
        # Aplicar paginación y ordenamiento
        vial = query.order_by(models.UnidadProyectoInfraestructuraVial.bpin)\
                   .offset(offset)\
                   .limit(limit)\
                   .all()
        
        logger.info(f"Consulta de infraestructura vial: {len(vial)} registros devueltos")
        return vial
        
    except Exception as e:
        logger.error(f"Error al consultar infraestructura vial: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/unidades_proyecto/vial/geojson', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"])
def get_infraestructura_vial_geojson(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico")
):
    """
    Obtiene datos de infraestructura vial en formato GeoJSON según RFC 7946 para uso en mapas
    
    - **bpin**: Filtrar por BPIN específico
    """
    try:
        # Cargar el archivo GeoJSON directamente
        geojson_data = load_geojson_file("infraestructura_vial.geojson")
        
        # Validar que cumple con el estándar RFC 7946
        if geojson_data.get("type") != "FeatureCollection":
            raise HTTPException(status_code=400, detail="GeoJSON debe ser un FeatureCollection")
        
        features = geojson_data.get("features", [])
        
        # Filtrar por BPIN si se proporciona
        if bpin:
            filtered_features = []
            for feature in features:
                properties = feature.get("properties", {})
                if properties.get("bpin") == bpin:
                    filtered_features.append(feature)
            features = filtered_features
        
        # Crear respuesta RFC 7946 compliant (sin 'crs' por estándar RFC 7946)
        response_geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        logger.info(f"GeoJSON de infraestructura vial: {len(features)} features devueltas")
        return response_geojson
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo infraestructura_vial.geojson no encontrado")
    except Exception as e:
        logger.error(f"Error al obtener GeoJSON de infraestructura vial: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/unidades_proyecto/equipamientos/geojson', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"])
def get_equipamientos_geojson(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico")
):
    """
    Obtiene datos de equipamientos en formato GeoJSON según RFC 7946 para uso en mapas
    
    - **bpin**: Filtrar por BPIN específico
    """
    try:
        # Cargar el archivo GeoJSON directamente
        geojson_data = load_geojson_file("equipamientos.geojson")
        
        # Validar que cumple con el estándar RFC 7946
        if geojson_data.get("type") != "FeatureCollection":
            raise HTTPException(status_code=400, detail="GeoJSON debe ser un FeatureCollection")
        
        features = geojson_data.get("features", [])
        
        # Filtrar por BPIN si se proporciona
        if bpin:
            features = [f for f in features if f.get("properties", {}).get("bpin") == bpin]
        
        # Respuesta RFC 7946 (sin 'crs')
        response_geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        logger.info(f"GeoJSON de equipamientos: {len(features)} features devueltas")
        return response_geojson
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo equipamientos.geojson no encontrado")
    except Exception as e:
        logger.error(f"Error al obtener GeoJSON de equipamientos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/unidades_proyecto/equipamientos/count', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"])
def get_equipamientos_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de unidades de proyecto de equipamientos con filtros opcionales"""
    try:
        query = db.query(models.UnidadProyectoInfraestructuraEquipamientos)
        
        if bpin:
            query = query.filter(models.UnidadProyectoInfraestructuraEquipamientos.bpin == bpin)
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin}}
        
    except Exception as e:
        logger.error(f"Error al contar equipamientos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/unidades_proyecto/vial/count', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"])
def get_vial_count(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de unidades de proyecto de infraestructura vial con filtros opcionales"""
    try:
        query = db.query(models.UnidadProyectoInfraestructuraVial)
        
        if bpin:
            query = query.filter(models.UnidadProyectoInfraestructuraVial.bpin == bpin)
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin}}
        
    except Exception as e:
        logger.error(f"Error al contar infraestructura vial: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

# ================================================================================================================
# MÉTODOS PUT - UNIDADES DE PROYECTO
# ================================================================================================================

@app.put('/unidades_proyecto/equipamientos/{bpin}', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=schemas.UnidadProyectoInfraestructuraEquipamientos)
def update_unidad_proyecto_equipamientos(
    bpin: int,
    equipamiento_data: schemas.UnidadProyectoInfraestructuraEquipamientos,
    db: Session = Depends(get_db)
):
    """
    Actualiza un registro de unidad de proyecto de equipamientos por BPIN
    
    - **bpin**: BPIN del registro a actualizar
    - **equipamiento_data**: Datos actualizados del equipamiento
    """
    try:
        # Buscar el registro existente
        existing_record = db.query(models.UnidadProyectoInfraestructuraEquipamientos).filter(
            models.UnidadProyectoInfraestructuraEquipamientos.bpin == bpin
        ).first()
        
        if not existing_record:
            raise HTTPException(status_code=404, detail=f"No se encontró registro con BPIN {bpin}")
        
        # Actualizar todos los campos
        update_data = equipamiento_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_record, field, value)
        
        db.commit()
        db.refresh(existing_record)
        
        logger.info(f"Actualizado equipamiento con BPIN {bpin}")
        return existing_record
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar equipamiento BPIN {bpin}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar registro: {str(e)}")

@app.put('/unidades_proyecto/vial/{bpin}', tags=["PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA"], response_model=schemas.UnidadProyectoInfraestructuraVial)
def update_unidad_proyecto_vial(
    bpin: int,
    vial_data: schemas.UnidadProyectoInfraestructuraVial,
    db: Session = Depends(get_db)
):
    """
    Actualiza un registro de unidad de proyecto de infraestructura vial por BPIN
    
    - **bpin**: BPIN del registro a actualizar
    - **vial_data**: Datos actualizados de infraestructura vial
    """
    try:
        # Buscar el registro existente
        existing_record = db.query(models.UnidadProyectoInfraestructuraVial).filter(
            models.UnidadProyectoInfraestructuraVial.bpin == bpin
        ).first()
        
        if not existing_record:
            raise HTTPException(status_code=404, detail=f"No se encontró registro con BPIN {bpin}")
        
        # Actualizar todos los campos
        update_data = vial_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_record, field, value)
        
        db.commit()
        db.refresh(existing_record)
        
        logger.info(f"Actualizado infraestructura vial con BPIN {bpin}")
        return existing_record
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al actualizar infraestructura vial BPIN {bpin}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar registro: {str(e)}")

# =============================================================================
# CONTRATOS SECOP - Sistema optimizado con arquitectura BPIN-centric
# =============================================================================

def load_contratos_json_file(filename: str):
    """Cargar archivo JSON desde el directorio de salida de contratos SECOP"""
    file_path = f"transformation_app/app_outputs/contratos_secop_output/{filename}"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo {filename} no encontrado en {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_and_validate_contratos_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función para cargar, validar y guardar datos de contratos SECOP.
    Implementa upsert inteligente con barra de progreso en español.
    """
    try:
        # Cargar datos del archivo JSON
        raw_data = load_contratos_json_file(filename)
        
        if not raw_data:
            logger.warning(f"Archivo {filename} está vacío")
            return []
        
        # Importar tqdm para barra de progreso
        try:
            from tqdm import tqdm
        except ImportError:
            # Fallback si tqdm no está disponible
            def tqdm(iterable, **kwargs):
                return iterable
        
        # Validar datos con barra de progreso
        validated_data = []
        validation_errors = []
        
        print(f"🔍 Validando datos de {filename}...")
        for i, item in tqdm(enumerate(raw_data), total=len(raw_data), desc="📋 Validando registros", unit="registro"):
            try:
                validated_item = schema_class(**item)
                validated_data.append(validated_item)
            except Exception as ve:
                validation_errors.append(f"Error en registro {i}: {str(ve)}")
        
        if validation_errors:
            logger.warning(f"Se encontraron {len(validation_errors)} errores de validación en {filename}")
            for error in validation_errors[:5]:  # Mostrar solo los primeros 5 errores
                logger.warning(error)
        
        if not validated_data:
            logger.warning(f"No hay datos válidos para cargar desde {filename}")
            return []
        
        # Realizar upsert masivo con barra de progreso
        print(f"💾 Guardando {len(validated_data)} registros en base de datos...")
        
        # Convertir datos de Pydantic a diccionario
        data_dicts = [item.model_dump() for item in validated_data]
        bulk_upsert_data(db, model_class, data_dicts, primary_key)
        
        logger.info(f"✅ {filename}: {len(validated_data)} registros procesados exitosamente")
        return validated_data
        
    except FileNotFoundError as e:
        logger.error(f"❌ Archivo no encontrado: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error procesando {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando {filename}: {str(e)}")

# Mapeo de archivos de contratos
CONTRATOS_MAPPING = {
    "contratos.json": {
        "schema": schemas.Contrato,
        "model": models.Contrato,
        "primary_key": ["bpin", "cod_contrato"]
    },
    "contratos_valores.json": {
        "schema": schemas.ContratoValor,
        "model": models.ContratoValor,
        "primary_key": ["bpin", "cod_contrato"]
    }
}

@app.post('/contratos', tags=["CONTRATO"], response_model=List[schemas.Contrato])
def cargar_contratos(db: Session = Depends(get_db)):
    """
    Carga datos principales de contratos SECOP desde contratos.json.
    Implementa upsert con barra de progreso para alta eficiencia.
    """
    try:
        with get_db_transaction() as db_trans:
            return load_and_validate_contratos_data(
                "contratos.json",
                schemas.Contrato,
                db_trans,
                models.Contrato,
                ["bpin", "cod_contrato"]
            )
    except Exception as e:
        logger.error(f"Error cargando contratos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cargando contratos: {str(e)}")

@app.post('/contratos_valores', tags=["CONTRATO"], response_model=List[schemas.ContratoValor])
def cargar_contratos_valores(db: Session = Depends(get_db)):
    """
    Carga datos de valores de contratos SECOP desde contratos_valores.json.
    Implementa upsert con barra de progreso para alta eficiencia.
    """
    try:
        with get_db_transaction() as db_trans:
            return load_and_validate_contratos_data(
                "contratos_valores.json",
                schemas.ContratoValor,
                db_trans,
                models.ContratoValor,
                ["bpin", "cod_contrato"]
            )
    except Exception as e:
        logger.error(f"Error cargando valores de contratos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cargando valores de contratos: {str(e)}")

@app.post('/load_all_contratos', tags=["CONTRATO"])
def cargar_todos_contratos(db: Session = Depends(get_db)):
    """
    Carga todos los datos de contratos SECOP de manera masiva y optimizada.
    - Carga contratos principales y valores en una sola operación
    - Implementa barras de progreso para seguimiento visual
    - Manejo robusto de errores y tolerante a fallos
    """
    results = {}
    successful_loads = 0
    failed_loads = 0
    
    try:
        print("🚀 Iniciando carga masiva de contratos SECOP...")
        
        with get_db_transaction() as db_trans:
            for filename, mapping in CONTRATOS_MAPPING.items():
                try:
                    logger.info(f"🔄 Procesando {filename}...")
                    start_time = time.time()
                    
                    # Verificar si el archivo existe
                    file_path = f"transformation_app/app_outputs/contratos_secop_output/{filename}"
                    if not os.path.exists(file_path):
                        logger.warning(f"⚠️ Archivo {filename} no encontrado, omitiendo...")
                        results[filename] = {
                            "status": "omitido",
                            "message": "Archivo no encontrado",
                            "records_loaded": 0
                        }
                        continue
                    
                    # Cargar y validar datos
                    loaded_data = load_and_validate_contratos_data(
                        filename,
                        mapping["schema"],
                        db_trans,
                        mapping["model"],
                        mapping["primary_key"]
                    )
                    
                    execution_time = time.time() - start_time
                    
                    results[filename] = {
                        "status": "exitoso",
                        "records_loaded": len(loaded_data),
                        "execution_time_seconds": round(execution_time, 2)
                    }
                    
                    successful_loads += 1
                    logger.info(f"✅ {filename} cargado: {len(loaded_data)} registros en {execution_time:.2f}s")
                    
                except Exception as e:
                    failed_loads += 1
                    error_msg = str(e)
                    logger.error(f"❌ Error cargando {filename}: {error_msg}")
                    
                    results[filename] = {
                        "status": "error",
                        "message": error_msg,
                        "records_loaded": 0
                    }
        
        # Resumen final
        total_records = sum(r.get("records_loaded", 0) for r in results.values())
        
        print(f"\n🎉 ¡Carga masiva de contratos completada!")
        print(f"📊 Resumen: {successful_loads} exitosos, {failed_loads} fallidos")
        print(f"📝 Total de registros cargados: {total_records}")
        
        return {
            "status": "completed",
            "summary": {
                "successful_loads": successful_loads,
                "failed_loads": failed_loads,
                "total_records_loaded": total_records
            },
            "details": results,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Error crítico en carga masiva de contratos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crítico en carga masiva: {str(e)}")

@app.get('/contratos', tags=["CONTRATO"], response_model=List[schemas.ContratoCompleto])
def obtener_contratos(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    cod_contrato: Optional[str] = Query(None, description="Filtrar por código de contrato"),
    estado_contrato: Optional[str] = Query(None, description="Filtrar por estado del contrato"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor (búsqueda parcial)"),
    limit: int = Query(100, description="Número máximo de registros"),
    offset: int = Query(0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene contratos SECOP con información completa optimizada.
    Soporta filtros múltiples y paginación para consultas eficientes.
    """
    try:
        # Query optimizada sin JOIN con tablas problemáticas
        query = db.query(
            models.Contrato.bpin,
            models.Contrato.cod_contrato,
            models.Contrato.nombre_proyecto,
            models.Contrato.descripcion_contrato,
            models.Contrato.estado_contrato,
            models.Contrato.codigo_proveedor,
            models.Contrato.proveedor,
            models.Contrato.url_contrato,
            models.Contrato.fecha_actualizacion,
            models.ContratoValor.valor_contrato
        ).outerjoin(
            models.ContratoValor,
            (models.Contrato.bpin == models.ContratoValor.bpin) & 
            (models.Contrato.cod_contrato == models.ContratoValor.cod_contrato)
        )
        
        # Aplicar filtros
        if bpin is not None:
            query = query.filter(models.Contrato.bpin == bpin)
        
        if cod_contrato:
            query = query.filter(models.Contrato.cod_contrato == cod_contrato)
            
        if estado_contrato:
            query = query.filter(models.Contrato.estado_contrato.ilike(f"%{estado_contrato}%"))
            
        if proveedor:
            query = query.filter(models.Contrato.proveedor.ilike(f"%{proveedor}%"))
        
        # Aplicar paginación
        query = query.offset(offset).limit(limit)
        
        # Ejecutar query
        results = query.all()
        
        # Convertir a lista de diccionarios para el schema
        contratos_completos = []
        for row in results:
            contrato_completo = {
                "bpin": row.bpin,
                "cod_contrato": row.cod_contrato,
                "nombre_proyecto": row.nombre_proyecto,
                "descripcion_contrato": row.descripcion_contrato,
                "estado_contrato": row.estado_contrato,
                "codigo_proveedor": row.codigo_proveedor,
                "proveedor": row.proveedor,
                "url_contrato": row.url_contrato,
                "fecha_actualizacion": row.fecha_actualizacion,
                "valor_contrato": row.valor_contrato,
                "cod_centro_gestor": None,  # Simplificado para evitar JOIN problemático
                "nombre_centro_gestor": None  # Simplificado para evitar JOIN problemático
            }
            contratos_completos.append(contrato_completo)
        
        logger.info(f"✅ Consulta de contratos: {len(contratos_completos)} registros encontrados")
        return contratos_completos
        
    except Exception as e:
        logger.error(f"❌ Error consultando contratos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consultando contratos: {str(e)}")

@app.get('/contratos/simple', tags=["CONTRATO"], response_model=List[schemas.ContratoCompleto])
def obtener_contratos_simple(
    limit: int = Query(100, description="Número máximo de registros"),
    offset: int = Query(0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene contratos SECOP con valores incluidos - optimizado para rendimiento.
    """
    try:
        # Query con JOIN para incluir valores
        query = db.query(
            models.Contrato.bpin,
            models.Contrato.cod_contrato,
            models.Contrato.nombre_proyecto,
            models.Contrato.descripcion_contrato,
            models.Contrato.estado_contrato,
            models.Contrato.codigo_proveedor,
            models.Contrato.proveedor,
            models.Contrato.url_contrato,
            models.Contrato.fecha_actualizacion,
            models.ContratoValor.valor_contrato
        ).outerjoin(
            models.ContratoValor,
            (models.Contrato.bpin == models.ContratoValor.bpin) & 
            (models.Contrato.cod_contrato == models.ContratoValor.cod_contrato)
        ).offset(offset).limit(limit)
        
        results = query.all()
        
        # Convertir a lista de diccionarios para el schema
        contratos_completos = []
        for row in results:
            contrato_completo = {
                "bpin": row.bpin,
                "cod_contrato": row.cod_contrato,
                "nombre_proyecto": row.nombre_proyecto,
                "descripcion_contrato": row.descripcion_contrato,
                "estado_contrato": row.estado_contrato,
                "codigo_proveedor": row.codigo_proveedor,
                "proveedor": row.proveedor,
                "url_contrato": row.url_contrato,
                "fecha_actualizacion": row.fecha_actualizacion,
                "valor_contrato": row.valor_contrato,
                "cod_centro_gestor": None,  # Simplificado para rendimiento
                "nombre_centro_gestor": None  # Simplificado para rendimiento
            }
            contratos_completos.append(contrato_completo)
        
        logger.info(f"✅ Consulta simple de contratos: {len(contratos_completos)} registros encontrados")
        return contratos_completos
        
    except Exception as e:
        logger.error(f"❌ Error consultando contratos simples: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consultando contratos: {str(e)}")

@app.get('/contratos/count', tags=["CONTRATO"])
def contar_contratos(
    bpin: Optional[int] = Query(None, description="Filtrar por BPIN específico"),
    estado_contrato: Optional[str] = Query(None, description="Filtrar por estado del contrato"),
    proveedor: Optional[str] = Query(None, description="Filtrar por proveedor"),
    db: Session = Depends(get_db)
):
    """
    Cuenta el número total de contratos con filtros opcionales.
    Útil para paginación y estadísticas.
    """
    try:
        query = db.query(models.Contrato)
        
        # Aplicar los mismos filtros que en la consulta principal
        if bpin is not None:
            query = query.filter(models.Contrato.bpin == bpin)
            
        if estado_contrato:
            query = query.filter(models.Contrato.estado_contrato.ilike(f"%{estado_contrato}%"))
            
        if proveedor:
            query = query.filter(models.Contrato.proveedor.ilike(f"%{proveedor}%"))
        
        count = query.count()
        
        return {
            "total_contratos": count,
            "filters_applied": {
                "bpin": bpin,
                "estado_contrato": estado_contrato,
                "proveedor": proveedor
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error contando contratos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error contando contratos: {str(e)}")

@app.delete('/clear_all_data', tags=["ADMIN"])
def clear_all_data(db: Session = Depends(get_db)):
    """
    CUIDADO: Elimina todos los datos de todas las tablas de la base de datos.
    """
    try:
        with get_db_transaction() as db_trans:
            # Obtener todas las tablas dinámicamente desde information_schema
            query = text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            result = db_trans.execute(query)
            table_names = [row[0] for row in result]

            deleted_counts = {}

            # Eliminar datos en cada tabla
            for table_name in table_names:
                count_before = db_trans.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                db_trans.execute(text(f"DELETE FROM {table_name}"))
                deleted_counts[table_name] = count_before

        return {
            "status": "success",
            "message": "Todos los datos eliminados exitosamente",
            "deleted_records": deleted_counts,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error al limpiar datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al limpiar datos: {str(e)}")

# ================================================================================================================
# ENDPOINTS DE ADMINISTRACIÓN Y DIAGNÓSTICO
# ================================================================================================================

@app.get('/health', tags=["ADMIN"])
def health_check(db: Session = Depends(get_db)):
    """Verificar el estado de la conexión a la base de datos"""
    try:
        # Ejecutar una consulta simple para verificar la conexión
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Base de datos no disponible: {str(e)}")

@app.get('/database_status', tags=["ADMIN"])
def database_status(db: Session = Depends(get_db)):
    """Obtener estadísticas de todas las tablas de la base de datos"""
    try:
        stats = {}

        # Obtener todas las tablas dinámicamente desde information_schema
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        result = db.execute(query)
        table_names = [row[0] for row in result]

        # Contar registros en cada tabla
        for table_name in table_names:
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            stats[table_name] = {
                "records_count": count
            }

        return {
            "status": "success",
            "database_stats": stats,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error al obtener estadísticas de BD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar estadísticas: {str(e)}")

@app.get('/tables_info', tags=["ADMIN"])
def tables_info(db: Session = Depends(get_db)):
    """Obtener información detallada de todas las tablas agrupadas por tabla y con su estado"""
    try:
        tables_info = {}

        # Consultar información de todas las tablas desde information_schema
        query = text("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)

        result = db.execute(query)

        for row in result:
            table_name = row[0]
            if table_name not in tables_info:
                tables_info[table_name] = {
                    "columns": [],
                    "status": "active"  # Assuming all tables are active unless specified otherwise
                }

            tables_info[table_name]["columns"].append({
                "column_name": row[1],
                "data_type": row[2],
                "is_nullable": row[3],
                "column_default": row[4]
            })

        return {
            "status": "success",
            "tables_info": tables_info,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error al obtener información de tablas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar información de tablas: {str(e)}")
