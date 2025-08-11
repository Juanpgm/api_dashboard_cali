# Visión General y Arquitectura

Este API sirve datos presupuestales y de proyectos de la Alcaldía de Santiago de Cali usando FastAPI y PostgreSQL.

## Componentes Principales

- **FastAPI** (fastapi_project/main.py) con CORS habilitado
- **Capa de acceso a datos** con SQLAlchemy (database.py, models.py)
- **Validación** con Pydantic (schemas.py)
- **Inicializador de base de datos** (database_initializer.py) con verificación/corrección automática de esquemas
- **Sistema de transformación** (transformation_app/) para procesamiento de datos Excel

## Dominios de Datos

### PROYECTO (Datos Base)

- Catálogos: centros gestores, programas, áreas funcionales, propósitos, retos
- Transaccionales: movimientos presupuestales, ejecución presupuestal

### ✨ PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN (NUEVO)

- **seguimiento_pa**: Resumen consolidado (1,396 registros)
- **seguimiento_productos_pa**: Productos del plan (1,990 registros)
- **seguimiento_actividades_pa**: Actividades detalladas (10,737 registros)

### PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA

- Equipamientos y infraestructura vial con capacidades geoespaciales

### ADMIN

- Diagnóstico, limpieza controlada y métricas del sistema

## Puntos Clave de Arquitectura

- **Cargas masivas** mediante upsert (ON CONFLICT) para alto rendimiento
- **Endpoints separados** por dominios funcionales
- **Transformación automática** de datos Excel a JSON estructurado
- **Validación robusta** con esquemas Pydantic
- **Índices optimizados** para consultas comunes
- **Sistema de logging** completo para trazabilidad

## Flujo de Datos

1. **Transformación**: Excel → JSON (transformation_app/)
2. **Validación**: Pydantic schemas
3. **Carga**: Bulk upsert a PostgreSQL
4. **Consulta**: API REST con filtros optimizados
