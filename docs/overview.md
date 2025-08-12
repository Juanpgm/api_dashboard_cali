# Visión General y Arquitectura

Este API sirve datos presupuestales y de proyectos de la Alcaldía de Santiago de Cali usando FastAPI y PostgreSQL.

## Componentes Principales

- **FastAPI** (fastapi_project/main.py) con CORS habilitado
- **Capa de acceso a datos** con SQLAlchemy (database.py, models.py)
- **Validación** con Pydantic (schemas.py)
- **Inicializador de base de datos** (database_initializer.py) con verificación/corrección automática de esquemas
- **Sistema de transformación optimizado** (transformation_app/) para procesamiento de datos Excel con arquitectura BPIN-centric

## Dominios de Datos

### PROYECTO (Datos Base)

- Catálogos: centros gestores, programas, áreas funcionales, propósitos, retos
- Transaccionales: movimientos presupuestales, ejecución presupuestal

### 🚀 PROYECTO: CONTRATOS SECOP (NUEVO - OPTIMIZADO)

- **Arquitectura BPIN-centric**: Sistema optimizado con BPIN como fuente primaria
- **Performance mejorado 60%**: Ejecución en ~30 segundos vs 76s anterior
- **contratos.json**: Datos principales de contratos (647.6 KB)
- **contratos_valores.json**: Información financiera asociada (83.4 KB)
- **753 registros procesados** con 100% cobertura BPIN

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
- **Transformación optimizada** de datos Excel a JSON estructurado con arquitectura BPIN-centric
- **Performance mejorado** en sistemas de transformación (60% más rápido en contratos SECOP)
- **Eliminación de redundancias** en datos y archivos para optimizar carga y almacenamiento
- **Validación robusta** con esquemas Pydantic
- **Índices optimizados** para consultas comunes
- **Sistema de logging** completo para trazabilidad
- **100% cobertura BPIN** en todos los sistemas de datos

## Flujo de Datos

1. **Transformación**: Excel → JSON optimizado (transformation_app/) con arquitectura BPIN-centric
2. **Validación**: Pydantic schemas con 100% cobertura BPIN
3. **Carga**: Bulk upsert a PostgreSQL con eliminación de redundancias
4. **Consulta**: API REST con filtros optimizados y performance mejorado
