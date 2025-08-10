# Visión General y Arquitectura

Este API sirve datos presupuestales y de proyectos de la Alcaldía de Santiago de Cali usando FastAPI y PostgreSQL.

Componentes principales:

- FastAPI (fastapi_project/main.py) con CORS habilitado.
- Capa de acceso a datos con SQLAlchemy (database.py, models.py).
- Validación con Pydantic (schemas.py).
- Inicializador de base de datos (database_initializer.py) con verificación/corrección de esquemas.

Puntos clave:

- Cargas masivas mediante upsert (ON CONFLICT) para alto rendimiento.
- Endpoints separados por dominios: PROYECTO y UNIDADES DE PROYECTO.
- Endpoints ADMIN con diagnóstico y limpieza controlada.
