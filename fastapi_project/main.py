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
    version="1.1.1",  # Incrementar versión por las mejoras
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
    "centros_gestores.json": {
        "model": models.CentroGestor,
        "schema": schemas.CentroGestor,
        "primary_key": "cod_centro_gestor"
    },
    "programas.json": {
        "model": models.Programa,
        "schema": schemas.Programa,
        "primary_key": "cod_programa"
    },
    "areas_funcionales.json": {
        "model": models.AreaFuncional,
        "schema": schemas.AreaFuncional,
        "primary_key": "cod_area_funcional"
    },
    "propositos.json": {
        "model": models.Proposito,
        "schema": schemas.Proposito,
        "primary_key": "cod_proposito"
    },
    "retos.json": {
        "model": models.Reto,
        "schema": schemas.Reto,
        "primary_key": "cod_reto"
    },
    "movimientos_presupuestales.json": {
        "model": models.MovimientoPresupuestal,
        "schema": schemas.MovimientoPresupuestal,
        "primary_key": ["bpin", "periodo_corte"]  # Clave compuesta
    },
    "ejecucion_presupuestal.json": {
        "model": models.EjecucionPresupuestal,
        "schema": schemas.EjecucionPresupuestal,
        "primary_key": ["bpin", "periodo_corte"]  # Clave compuesta
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_transaction():
    """Context manager para manejar transacciones de base de datos"""
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
    """Carga un archivo JSON y retorna los datos"""
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
    """Carga un archivo JSON desde el directorio de unidades de proyecto y retorna los datos"""
    file_path = next((path for path in UNIDADES_PROYECTO_JSON_PATHS if os.path.basename(path) == filename), None)
    if not file_path:
        raise FileNotFoundError(f"Archivo {filename} no encontrado en {UNIDADES_PROYECTO_DIR}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        raise ValueError(f"Error al decodificar el archivo JSON: {filename}")

def bulk_upsert_data(db: Session, model_class, data: List[Dict[str, Any]], primary_key):
    """
    Realiza una inserción/actualización masiva eficiente usando PostgreSQL UPSERT
    Soporta tanto claves primarias simples como compuestas.
    """
    if not data:
        return
    
    try:
        # Preparar los datos para inserción
        table = model_class.__table__
        
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
            INSERT INTO {table.name} ({', '.join(columns)})
            VALUES ({values_placeholder})
            ON CONFLICT ({conflict_columns}) DO UPDATE SET
            {update_clause}
            """
        else:
            # Si no hay columnas para actualizar, solo hacer INSERT ... ON CONFLICT DO NOTHING
            insert_stmt = f"""
            INSERT INTO {table.name} ({', '.join(columns)})
            VALUES ({values_placeholder})
            ON CONFLICT ({conflict_columns}) DO NOTHING
            """
        
        # Ejecutar la inserción masiva
        db.execute(text(insert_stmt), data)
        logger.info(f"Upserted {len(data)} records in {table.name}")
        
    except Exception as e:
        logger.error(f"Error during bulk upsert for {model_class.__name__}: {str(e)}")
        raise

def load_geojson_file(filename: str) -> dict:
    """Cargar archivo GeoJSON de la carpeta de outputs"""
    file_path = f"transformation_app/app_outputs/unidades_proyecto_outputs/{filename}"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Función auxiliar para cargar y validar datos
def load_and_validate_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función genérica para cargar, validar y guardar datos en la base de datos
    Soporta claves primarias simples y compuestas.
    """
    try:
        # Cargar datos del archivo JSON
        raw_data = load_json_file(filename)
        
        # Validar datos usando el esquema de Pydantic
        validated_data = [schema_class(**item) for item in raw_data]
        
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

def load_and_validate_unidades_proyecto_data(filename: str, schema_class, db: Session, model_class, primary_key) -> List:
    """
    Función específica para cargar, validar y guardar datos de unidades de proyecto en la base de datos
    Excluye las columnas geométricas de los archivos JSON
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

@app.post('/centros_gestores', tags=["PROYECTO"], response_model=List[schemas.CentroGestor])
def load_centros_gestores(db: Session = Depends(get_db)):
    """Carga centros gestores desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["centros_gestores.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "centros_gestores.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/programas', tags=["PROYECTO"], response_model=List[schemas.Programa])
def load_programas(db: Session = Depends(get_db)):
    """Carga programas desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["programas.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "programas.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/areas_funcionales', tags=["PROYECTO"], response_model=List[schemas.AreaFuncional])
def load_areas_funcionales(db: Session = Depends(get_db)):
    """Carga áreas funcionales desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["areas_funcionales.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "areas_funcionales.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/propositos', tags=["PROYECTO"], response_model=List[schemas.Proposito])
def load_propositos(db: Session = Depends(get_db)):
    """Carga propósitos desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["propositos.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "propositos.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/retos', tags=["PROYECTO"], response_model=List[schemas.Reto])
def load_retos(db: Session = Depends(get_db)):
    """Carga retos desde JSON a PostgreSQL con validación y upsert eficiente"""
    mapping = DATA_MAPPING["retos.json"]
    
    with get_db_transaction() as db_trans:
        return load_and_validate_data(
            "retos.json",
            mapping["schema"],
            db_trans,
            mapping["model"],
            mapping["primary_key"]
        )

@app.post('/movimientos_presupuestales', tags=["PROYECTO"], response_model=List[schemas.MovimientoPresupuestal])
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

@app.post('/ejecucion_presupuestal', tags=["PROYECTO"], response_model=List[schemas.EjecucionPresupuestal])
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

# Endpoint para cargar todos los datos de una vez (más eficiente)
@app.post('/load_all_data', tags=["PROYECTO"])
def load_all_data(db: Session = Depends(get_db)):
    """
    Carga todos los datos de una vez de manera transaccional y eficiente.
    Recomendado para cargas iniciales o actualizaciones completas.
    """
    results = {}
    
    try:
        with get_db_transaction() as db_trans:
            for filename, mapping in DATA_MAPPING.items():
                logger.info(f"Cargando {filename}...")
                start_time = time.time()
                
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
                    "records_loaded": len(data),
                    "load_time_seconds": round(load_time, 2)
                }
                logger.info(f"Completado {filename}: {len(data)} registros en {load_time:.2f}s")
        
        return {
            "status": "success",
            "message": "Todos los datos cargados exitosamente",
            "details": results
        }
        
    except Exception as e:
        logger.error(f"Error durante la carga masiva de datos: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error durante la carga masiva: {str(e)}"
        )

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

@app.get('/centros_gestores', tags=["PROYECTO"], response_model=List[schemas.CentroGestor])
def get_centros_gestores(db: Session = Depends(get_db)):
    """Obtiene todos los centros gestores desde PostgreSQL"""
    try:
        centros = db.query(models.CentroGestor).all()
        return centros
    except Exception as e:
        logger.error(f"Error al consultar centros gestores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/programas', tags=["PROYECTO"], response_model=List[schemas.Programa])
def get_programas(db: Session = Depends(get_db)):
    """Obtiene todos los programas desde PostgreSQL"""
    try:
        programas = db.query(models.Programa).all()
        return programas
    except Exception as e:
        logger.error(f"Error al consultar programas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/areas_funcionales', tags=["PROYECTO"], response_model=List[schemas.AreaFuncional])
def get_areas_funcionales(db: Session = Depends(get_db)):
    """Obtiene todas las áreas funcionales desde PostgreSQL"""
    try:
        areas = db.query(models.AreaFuncional).all()
        return areas
    except Exception as e:
        logger.error(f"Error al consultar áreas funcionales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/propositos', tags=["PROYECTO"], response_model=List[schemas.Proposito])
def get_propositos(db: Session = Depends(get_db)):
    """Obtiene todos los propósitos desde PostgreSQL"""
    try:
        propositos = db.query(models.Proposito).all()
        return propositos
    except Exception as e:
        logger.error(f"Error al consultar propósitos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/retos', tags=["PROYECTO"], response_model=List[schemas.Reto])
def get_retos(db: Session = Depends(get_db)):
    """Obtiene todos los retos desde PostgreSQL"""
    try:
        retos = db.query(models.Reto).all()
        return retos
    except Exception as e:
        logger.error(f"Error al consultar retos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/movimientos_presupuestales', tags=["PROYECTO"], response_model=List[schemas.MovimientoPresupuestal])
def get_movimientos_presupuestales(
    bpin: Optional[str] = Query(None, description="Filtrar por BPIN específico"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte (ej: '2024-01' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene movimientos presupuestales desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **periodo_corte**: Filtrar por período de corte (puede ser año '2024' o año-mes '2024-01')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.MovimientoPresupuestal)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.MovimientoPresupuestal.bpin == bpin)
        
        if periodo_corte:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo_corte:
                query = query.filter(models.MovimientoPresupuestal.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.MovimientoPresupuestal.periodo_corte.like(f"{periodo_corte}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        movimientos = query.order_by(models.MovimientoPresupuestal.bpin, models.MovimientoPresupuestal.periodo_corte)\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
        
        logger.info(f"Consulta de movimientos presupuestales: {len(movimientos)} registros devueltos")
        return movimientos
        
    except Exception as e:
        logger.error(f"Error al consultar movimientos presupuestales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/ejecucion_presupuestal', tags=["PROYECTO"], response_model=List[schemas.EjecucionPresupuestal])
def get_ejecucion_presupuestal(
    bpin: Optional[str] = Query(None, description="Filtrar por BPIN específico"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte (ej: '2024-01' o '2024')"),
    limit: int = Query(100, ge=1, le=10000, description="Límite de registros a devolver"),
    offset: int = Query(0, ge=0, description="Número de registros a omitir"),
    db: Session = Depends(get_db)
):
    """
    Obtiene ejecución presupuestal desde PostgreSQL con filtros y paginación optimizada
    
    - **bpin**: Filtrar por BPIN específico
    - **periodo_corte**: Filtrar por período de corte (puede ser año '2024' o año-mes '2024-01')
    - **limit**: Máximo número de registros a devolver (default: 100, max: 10000)
    - **offset**: Número de registros a omitir para paginación (default: 0)
    """
    try:
        # Construir la query base
        query = db.query(models.EjecucionPresupuestal)
        
        # Aplicar filtros si se proporcionan
        if bpin:
            query = query.filter(models.EjecucionPresupuestal.bpin == bpin)
        
        if periodo_corte:
            # Si contiene guión, buscar exacto, si no, buscar que comience con el año
            if '-' in periodo_corte:
                query = query.filter(models.EjecucionPresupuestal.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.EjecucionPresupuestal.periodo_corte.like(f"{periodo_corte}%"))
        
        # Aplicar paginación y ordenamiento para consistencia
        ejecucion = query.order_by(models.EjecucionPresupuestal.bpin, models.EjecucionPresupuestal.periodo_corte)\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        logger.info(f"Consulta de ejecución presupuestal: {len(ejecucion)} registros devueltos")
        return ejecucion
        
    except Exception as e:
        logger.error(f"Error al consultar ejecución presupuestal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/movimientos_presupuestales/count', tags=["PROYECTO"])
def get_movimientos_count(
    bpin: Optional[str] = Query(None, description="Filtrar por BPIN específico"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de movimientos presupuestales con filtros opcionales"""
    try:
        query = db.query(models.MovimientoPresupuestal)
        
        if bpin:
            query = query.filter(models.MovimientoPresupuestal.bpin == bpin)
        
        if periodo_corte:
            if '-' in periodo_corte:
                query = query.filter(models.MovimientoPresupuestal.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.MovimientoPresupuestal.periodo_corte.like(f"{periodo_corte}%"))
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin, "periodo_corte": periodo_corte}}
        
    except Exception as e:
        logger.error(f"Error al contar movimientos presupuestales: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar datos: {str(e)}")

@app.get('/ejecucion_presupuestal/count', tags=["PROYECTO"])
def get_ejecucion_count(
    bpin: Optional[str] = Query(None, description="Filtrar por BPIN específico"),
    periodo_corte: Optional[str] = Query(None, description="Filtrar por período de corte"),
    db: Session = Depends(get_db)
):
    """Obtiene el conteo de ejecución presupuestal con filtros opcionales"""
    try:
        query = db.query(models.EjecucionPresupuestal)
        
        if bpin:
            query = query.filter(models.EjecucionPresupuestal.bpin == bpin)
        
        if periodo_corte:
            if '-' in periodo_corte:
                query = query.filter(models.EjecucionPresupuestal.periodo_corte == periodo_corte)
            else:
                query = query.filter(models.EjecucionPresupuestal.periodo_corte.like(f"{periodo_corte}%"))
        
        count = query.count()
        return {"total_registros": count, "filtros": {"bpin": bpin, "periodo_corte": periodo_corte}}
        
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
