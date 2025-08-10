"""
Database configuration module.

- Loads environment from .env
- Configures SQLAlchemy engine (PostgreSQL) with a production-ready pool
- Exposes SessionLocal and Base for ORM usage
- Provides lightweight helpers for diagnostics
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import os
import logging
from urllib.parse import quote_plus

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Validar que todas las variables necesarias estén configuradas
required_env_vars = {
    "POSTGRES_USER": POSTGRES_USER,
    "POSTGRES_SERVER": POSTGRES_SERVER,
    "POSTGRES_PORT": POSTGRES_PORT,
    "POSTGRES_DB": POSTGRES_DB
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")

# Codificar la contraseña para URL
encoded_password = quote_plus(POSTGRES_PASSWORD) if POSTGRES_PASSWORD else ""

# Construir URL de conexión
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Configurar engine con optimizaciones para producción
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Configuración del pool de conexiones para producción
    poolclass=QueuePool,
    pool_size=10,                    # Número de conexiones permanentes
    max_overflow=20,                 # Conexiones adicionales permitidas
    pool_pre_ping=True,              # Verificar conexiones antes de usar
    pool_recycle=3600,               # Reciclar conexiones cada hora
    # Configuraciones adicionales
    echo=False,                      # No mostrar SQL en producción
    future=True,                     # Usar SQLAlchemy 2.0 style
    connect_args={
        "options": "-c timezone=America/Bogota",  # Zona horaria Colombia
        "application_name": "API_Dashboard_Cali"  # Identificar aplicación en PostgreSQL
    }
)

# Configurar session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True  # SQLAlchemy 2.0 style
)

# Base para modelos
Base = declarative_base()

# Event listeners para optimizaciones
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configuraciones adicionales al conectar (solo para PostgreSQL aquí)"""
    pass

@event.listens_for(engine, "first_connect")
def receive_first_connect(dbapi_connection, connection_record):
    """Ejecutar en la primera conexión"""
    logger.info("✅ Primera conexión a PostgreSQL establecida")

def get_database_info():
    """Obtiene información de la configuración de la base de datos (no sensible)."""
    return {
        "database_type": "PostgreSQL",
        "server": POSTGRES_SERVER,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "pool_size": engine.pool.size(),
        "max_overflow": engine.pool._max_overflow,
        "application_name": "API_Dashboard_Cali"
    }

def test_connection():
    """Prueba la conexión a la base de datos ejecutando SELECT version()."""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Conexión exitosa a PostgreSQL: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Error de conexión: {e}")
        return False
