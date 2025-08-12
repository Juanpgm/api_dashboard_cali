# Cambios y Mejoras (Agosto 2025)

Versión actual: 2.4.0

## Versión 2.4.0 - Agosto 12, 2025

### 🚀 OPTIMIZACIÓN COMPLETA DE ENDPOINTS Y DOCUMENTACIÓN API

**Endpoints de Contratos Optimizados**

- ⚡ **Endpoint `/contratos/simple` mejorado**: Ahora incluye valores de contratos mediante JOIN optimizado
- ⚡ **Endpoint `/contratos` optimizado**: Eliminados JOINs problemáticos con tabla proyectos
- ⚡ **Response model unificado**: Ambos endpoints GET usan `ContratoCompleto` con valores incluidos
- 🔧 **JOIN simplificado**: Solo con `contratos_valores` para evitar conflictos de tipos de datos
- 📊 **Datos completos**: Todos los endpoints GET de contratos muestran `valor_contrato`

**Reorganización de Documentación API**

- 📚 **Endpoints ADMIN reorganizados**: Movidos al final del archivo para aparecer últimos en Swagger
- 🏷️ **Tags simplificados**: Cambiados de "ZZADMIN" a "ADMIN" manteniendo orden correcto
- 📋 **Estructura mejorada**:
  1. Endpoints de negocio (PROYECTO, CONTRATO, etc.)
  2. Endpoints administrativos (ADMIN) al final
- 🎯 **Documentación clara**: Separación lógica entre funcionalidades de negocio y administrativas

**Endpoints ADMIN Consolidados**

- ✅ `/health` - Verificación estado base de datos
- ✅ `/database_status` - Estadísticas detalladas de todas las tablas
- ✅ `/tables_info` - Información de esquemas y columnas
- ✅ `/clear_all_data` - Eliminación masiva (funciones críticas al final)

**Mejoras de Rendimiento**

- 🚀 **Consultas optimizadas**: Eliminación de JOINs innecesarios y problemáticos
- 💾 **Eficiencia de memoria**: Queries más simples y directas
- ⚡ **Tiempo de respuesta**: Mejora significativa en endpoints de contratos
- 🎯 **Compatibilidad de tipos**: Resolución de conflictos BIGINT vs VARCHAR

**Funcionalidad Verificada**

- ✅ **753 contratos** con valores completos en ambos endpoints GET
- ✅ **Carga masiva** funcional con `/load_all_contratos`
- ✅ **Filtros avanzados** por BPIN, estado, proveedor en endpoint principal
- ✅ **Paginación eficiente** en ambos endpoints optimizados
- ✅ **Documentación Swagger** con orden lógico de endpoints

## Versión 2.3.0 - Agosto 12, 2025

### 🏗️ SISTEMA OPTIMIZADO DE CONTRATOS SECOP CON ARQUITECTURA BPIN-CENTRIC

**Nueva Arquitectura de Transformación de Contratos**

- 🔄 **Reestructuración completa**: BPIN como fuente primaria en lugar de SECOP
- ⚡ **Performance mejorado 60%**: Tiempo de ejecución reducido de 76s a 30s
- 📊 **Mejor rendimiento**: 25.0 registros/segundo (vs 9.9 anterior)
- 🎯 **100% cobertura BPIN**: Todos los registros mapeados con BPIN válido

**Fuentes de Datos Integradas**

- 📥 **Fuentes BPIN primarias**:
  - `DatosAbiertosContratosXProyectosInv.csv` (30,745 registros)
  - `DatosAbiertosProcesosXProyectosInv.csv` (28,363 registros)
- 📥 **Fuente secundaria optimizada**:
  - `DACP W-31 PAA BD.xlsx` (1,105 registros) - SECOP_II eliminado por optimización

**Eliminación de Redundancias y Optimización**

- ❌ **Eliminado contratos_unified.json** - redundante con contratos.json (reducción 33% archivos)
- ❌ **Eliminado SECOP_II integration** - mejora significativa de performance
- 🧹 **Limpieza avanzada de datos**:
  - Eliminación completa de valores NaN con validación numpy
  - Remoción de monedas duplicadas (COP por defecto)
  - Consolidación de fechas duplicadas
  - Eliminación de códigos redundantes (cod_proceso = cod_contrato)

**Archivos de Salida Optimizados**

- ✅ `contratos.json` (647.6 KB) - Datos principales con BPIN garantizado
- ✅ `contratos_valores.json` (83.4 KB) - Valores financieros con BPIN
- 📉 **Reducción total**: 731 KB vs 5,400 KB anterior (86% menos datos)

**Mejoras Técnicas Implementadas**

- 🔧 **Mapeo inteligente**: Integración PAA por código y nombre de proyecto
- 🔧 **Validación de datos**: Verificación completa sin pérdida de información
- 🔧 **Optimización JSON**: Eliminación de redundancias preservando integridad
- 🔧 **Progress bars en español**: Visualización clara del progreso de transformación
- 🔧 **BPIN en todas las tablas**: Consistencia total para integraciones

**Resultados del Sistema Optimizado**

- 📝 **753 registros procesados** con 100% éxito
- 🎯 **753 BPINs únicos** mapeados correctamente
- ⚡ **30.11 segundos** tiempo total de ejecución
- 💾 **2 archivos JSON** limpios y optimizados para producción

## Versión 2.2.0 - Agosto 11, 2025

### 🏛️ SISTEMA COMPLETO DE SEGUIMIENTO AL PLAN DE ACCIÓN

**Nuevas Tablas de Base de Datos**

- ➕ `seguimiento_pa` - Tabla resumen con auto-increment PK `id_seguimiento_pa`
- ➕ `seguimiento_productos_pa` - Productos con clave compuesta (cod_pd_lvl_1, cod_pd_lvl_2)
- ➕ `seguimiento_actividades_pa` - Actividades con clave compuesta (cod_pd_lvl_1, cod_pd_lvl_2, cod_pd_lvl_3)

**Nuevos Endpoints API (Tag: PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN)**

- ➕ `POST /seguimiento_pa` - Cargar datos de resumen PA
- ➕ `POST /seguimiento_productos_pa` - Cargar productos PA
- ➕ `POST /seguimiento_actividades_pa` - Cargar actividades PA
- ➕ `POST /load_all_seguimiento_pa` - Carga masiva optimizada (recomendado)
- ➕ `GET /seguimiento_pa` - Consultar resumen con filtros
- ➕ `GET /seguimiento_productos_pa` - Consultar productos con filtros
- ➕ `GET /seguimiento_actividades_pa` - Consultar actividades con filtros

**Modelos SQLAlchemy Actualizados**

- 🔧 `SeguimientoPA` - Auto-increment PK, campos nullable optimizados
- 🔧 `SeguimientoProductoPA` - Clave compuesta, DECIMAL(15,2) para valores monetarios
- 🔧 `SeguimientoActividadPA` - Clave compuesta, DECIMAL(8,4) para porcentajes

**Inicializador de Base de Datos Mejorado**

- 🔧 `database_initializer.py` ahora usa SQLAlchemy models automáticamente
- 🔧 Creación automática de todas las tablas definidas en `models.py`
- 🔧 Índices de rendimiento para tablas de seguimiento PA
- 🔧 Verificación de esquema incluye nuevas tablas

### 📊 Datos Procesados Exitosamente

- ✅ 1,396 registros en `seguimiento_pa` (resumen por subdir/subsecr)
- ✅ 1,990 registros en `seguimiento_productos_pa` (productos del plan)
- ✅ 10,737 registros en `seguimiento_actividades_pa` (actividades detalladas)

## Versión 2.1.0 - Agosto 11, 2025

### ✨ Nuevas Funcionalidades

**Sistema de Transformación de Datos "Seguimiento PA"**

- ➕ Nuevo módulo `transformation_app/data_transformation_seguimiento_pa.py`
- ➕ Procesamiento automático de archivos Excel (.xlsx) desde `app_inputs/seguimiento_pa_input/`
- ➕ Generación de 3 datasets JSON estandarizados:
  - `seguimiento_actividades_pa.json` - Actividades de proyectos con datos presupuestales
  - `seguimiento_productos_pa.json` - Productos de proyectos con métricas de avance
  - `seguimiento_pa.json` - Resumen consolidado por proyecto

**Mejoras en Procesamiento de Datos**

- 🔧 Función avanzada de limpieza numérica que preserva valores originales
- 🔧 Soporte para múltiples formatos de números (separadores de miles, decimales)
- 🔧 Detección automática de tipos de archivos Excel (detallados vs resumen)
- 🔧 Manejo robusto de caracteres especiales y encoding UTF-8

**Normalización de Datos**

- 📊 Procesamiento de 10,737+ registros de actividades
- 📊 Procesamiento de 1,990+ registros de productos
- 📊 Generación de 1,396+ registros de resumen
- 📊 Limpieza automática de símbolos monetarios ($, separadores de miles)
- 📊 Conversión inteligente de porcentajes sin pérdida de precisión

### 🛠️ Mejoras Técnicas

**Calidad de Datos**

- ✅ Validación de tipos de datos según estándares del proyecto
- ✅ Códigos BPIN y actividades como enteros (BIGINT)
- ✅ Valores monetarios como decimales con 2 cifras de precisión
- ✅ Fechas en formato ISO estándar (YYYY-MM-DD)
- ✅ Manejo de valores nulos y campos vacíos

**Rendimiento**

- ⚡ Procesamiento batch de múltiples archivos Excel
- ⚡ Salida optimizada en formato JSON para consumo API
- ⚡ Logging detallado del proceso de transformación
- ⚡ Gestión eficiente de memoria para archivos grandes

## Versión 2.0.0 - Agosto 2025

Cambios desde la versión anterior:

- ADMIN dinámico: /database_status y /clear_all_data ahora recorren todas las tablas del schema public.
- tables_info consolidado: atributos por tabla + status (sin segregación por variable).
- NUEVO: PUT de edición por BPIN para equipamientos y vial.
- Removidos: PUT de corrección por BPIN inválido (a petición explícita).
- Cargas masivas más robustas: upsert con ON CONFLICT (claves simples/compuestas) y validación Pydantic.
- Unidades de proyecto: endpoints GET/POST + GeoJSON RFC7946.
- Inicialización: verificación/corrección automática de tipos críticos (bpin BIGINT, identificador VARCHAR).
