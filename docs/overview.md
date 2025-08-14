# Visión General y Arquitectura - v2.7.0

Este API sirve datos presupuestales y de proyectos de la Alcaldía de Santiago de Cali usando FastAPI y PostgreSQL.

## Componentes Principales

- **FastAPI** (fastapi_project/main.py) con CORS habilitado
- **Capa de acceso a datos** con SQLAlchemy (database.py, models.py)
- **Validación** con Pydantic (schemas.py)
- **🚀 Inicializador Unificado** (database_initializer.py) con detección automática Local/Railway
- **Sistema de transformación optimizado** (transformation_app/) para procesamiento de datos Excel con arquitectura BPIN-centric

## 🗄️ Database Initializer v2.7.0 - El Corazón del Sistema

### Funcionalidades Avanzadas

- **🌍 Detección automática de entorno**: Local (desarrollo) vs Railway (producción)
- **📊 Carga incremental inteligente**: Solo procesa archivos nuevos o tablas vacías
- **🚫 Filtrado automático**: Rechaza registros con BPIN NULL automáticamente
- **🔄 Sistema UPSERT**: ON CONFLICT DO UPDATE para evitar duplicados
- **🏗️ Creación automática de BD**: Usa SQLAlchemy models como fuente de verdad
- **📄 Reportes detallados**: Genera reportes markdown con métricas completas

### Mapeo de Archivos Alineado con API

```
transformation_app/app_outputs/
├── contratos_secop_output/
│   ├── contratos.json
│   └── contratos_valores.json
├── ejecucion_presupuestal_outputs/
│   ├── movimientos_presupuestales.json
│   ├── ejecucion_presupuestal.json
│   └── datos_caracteristicos_proyectos.json
├── seguimiento_pa_outputs/
│   ├── seguimiento_pa.json
│   ├── seguimiento_productos_pa.json
│   └── seguimiento_actividades_pa.json
└── unidades_proyecto_outputs/
    ├── unidad_proyecto_infraestructura_equipamientos.json
    └── unidad_proyecto_infraestructura_vial.json
```

### Resultados Comprobados v2.7.0

- ✅ **25 tablas** creadas/verificadas automáticamente
- ✅ **26 índices** de rendimiento generados
- ✅ **10 archivos JSON** procesados con mapeo exacto
- ✅ **1,489 registros** cargados exitosamente
- ✅ **Filtrado automático**: 89 registros rechazados por BPIN NULL
- ⏱️ **115.73 segundos**: Tiempo total de inicialización completa

## Dominios de Datos

### PROYECTO (Datos Base)

- Catálogos: centros gestores, programas, áreas funcionales, propósitos, retos
- Transaccionales: movimientos presupuestales, ejecución presupuestal

### 🚀 PROYECTO: CONTRATOS SECOP (OPTIMIZADO v2.5.0)

- **Arquitectura BPIN-centric**: Sistema optimizado con BPIN como fuente primaria
- **Performance mejorado 60%**: Ejecución en ~30 segundos vs 76s anterior
- **contratos.json**: Datos principales de contratos (647.6 KB)
- **contratos_valores.json**: Información financiera asociada (83.4 KB)
- **753 registros procesados** con 100% cobertura BPIN

### ✨ PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN (v2.2.0)

- **seguimiento_pa**: Resumen consolidado (1,396 registros)
- **seguimiento_productos_pa**: Productos del plan (1,990 registros)
- **seguimiento_actividades_pa**: Actividades detalladas (10,737 registros)

### PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA (v2.7.0)

- **Equipamientos**: 237 registros con filtrado BPIN NULL automático
- **Infraestructura vial**: 103 registros con capacidades geoespaciales
- **Clave primaria**: BPIN único (corregido desde clave compuesta)

### ADMIN

- Diagnóstico, limpieza controlada y métricas del sistema

## Puntos Clave de Arquitectura v2.7.0

- **🗄️ Inicialización unificada**: Un comando para local y Railway
- **📊 Carga incremental**: Solo datos nuevos en ejecuciones posteriores
- **🚫 Filtrado automático**: Datos inválidos rechazados sin intervención manual
- **🔄 UPSERT inteligente**: ON CONFLICT DO UPDATE con detección automática de PK
- **🏗️ Schema automático**: SQLAlchemy models como fuente de verdad para estructura BD
- **⚡ Performance optimizado**: 60% mejora en contratos, carga incremental para resto
- **📄 Reportes automáticos**: Documentación completa de cada inicialización
- **✅ Validación robusta**: Esquemas Pydantic + filtrado automático + integridad BD
- **🔍 Índices inteligentes**: 26 índices automáticos para consultas optimizadas
- **🌍 Multi-entorno**: Local (PostgreSQL directo) + Railway (DATABASE_URL)

## Flujo de Datos v2.7.0

1. **Transformación**: Excel → JSON optimizado (transformation_app/) con arquitectura BPIN-centric
2. **Detección**: database_initializer.py detecta entorno y archivos disponibles
3. **Filtrado**: Automático de registros con BPIN NULL/inválido
4. **Carga**: UPSERT inteligente a PostgreSQL con incrementalidad
5. **Validación**: Pydantic schemas + verificación de integridad
6. **Consulta**: API REST con filtros optimizados y performance mejorado
7. **Reporte**: Documentación automática de métricas y estado final

## Ventajas del Sistema Unificado

- **🎯 Un solo comando**: `python database_initializer.py` para cualquier entorno
- **⚡ Velocidad**: Incremental en segundos vs minutos completos
- **🛡️ Robustez**: Manejo automático de datos problemáticos
- **📊 Transparencia**: Reportes detallados de cada operación
- **🔧 Mantenibilidad**: SQLAlchemy models como única fuente de verdad
- **🚀 Escalabilidad**: Diseñado para Railway y entornos de producción
