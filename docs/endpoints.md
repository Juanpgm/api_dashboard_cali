# Endpoints de la API - Versión 2.6.0

## Tag: PROYECTO - Datos Básicos y Presupuestales

### Catálogos Base

- POST /centros_gestores
- POST /programas
- POST /areas_funcionales
- POST /propositos
- POST /retos
- GET /centros_gestores
- GET /programas
- GET /areas_funcionales
- GET /propositos
- GET /retos

### Datos Presupuestales (✅ Optimizados v2.6.0)

- POST /movimientos_presupuestales
- POST /ejecucion_presupuestal
- POST /load_all_data
- GET /movimientos_presupuestales?bpin&periodo_corte&limit&offset
- GET /ejecucion_presupuestal?bpin&periodo_corte&limit&offset
- GET /movimientos_presupuestales/count
- GET /ejecucion_presupuestal/count

**Nota v2.6.0**: Todos los filtros ahora usan `periodo_corte` (antes `periodo`) para consistencia total.

## Tag: PROYECTO: CONTRATOS SECOP (✅ Arquitectura BPIN-Centric)

### Endpoints de Contratos Optimizados

- POST /contratos - Carga individual de contratos
- POST /contratos_valores - Carga individual de valores
- POST /load_all_contratos - Carga masiva optimizada (recomendado)
- GET /contratos?bpin&estado_contrato&proveedor_contrato&limit&offset
- GET /contratos/simple?bpin&limit&offset

### Características v2.6.0

- ✅ **JOIN optimizado**: Solo con `contratos_valores` para incluir montos
- ✅ **Response unificado**: Ambos endpoints GET usan `ContratoCompleto`
- ✅ **Filtros avanzados**: Por BPIN, estado, proveedor
- ✅ **Performance mejorado**: Eliminación de JOINs problemáticos

## ✨ Tag: PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN (NUEVO)

### Endpoints de Carga (POST)

- POST /seguimiento_pa - Cargar datos de resumen PA
- POST /seguimiento_productos_pa - Cargar productos PA
- POST /seguimiento_actividades_pa - Cargar actividades PA
- POST /load_all_seguimiento_pa - Carga masiva optimizada (recomendado)

### Endpoints de Consulta (GET)

- GET /seguimiento_pa?id_seguimiento_pa&periodo_corte&subdireccion_subsecretaria&limit&offset
- GET /seguimiento_productos_pa?cod_pd_lvl_1&cod_pd_lvl_2&comuna&estado_producto_pa&limit&offset
- GET /seguimiento_actividades_pa?cod_pd_lvl_1&cod_pd_lvl_2&cod_pd_lvl_3&bpin&limit&offset

### Filtros Específicos Seguimiento PA

- `periodo_corte`: YYYY-MM (formato corto)
- `subdireccion_subsecretaria`: Texto exacto o parcial
- `estado_producto_pa`: Estados definidos en el sistema
- `bpin`: Código BPIN específico
- `cod_pd_lvl_*`: Códigos de nivel de plan de desarrollo

## Tag: PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA

- POST /unidades_proyecto/equipamientos
- POST /unidades_proyecto/vial
- GET /unidades_proyecto/equipamientos?bpin&limit&offset
- GET /unidades_proyecto/vial?bpin&limit&offset
- GET /unidades_proyecto/equipamientos/geojson?bpin
- GET /unidades_proyecto/vial/geojson?bpin
- GET /unidades_proyecto/equipamientos/count
- GET /unidades_proyecto/vial/count
- PUT /unidades_proyecto/equipamientos/{bpin}
- PUT /unidades_proyecto/vial/{bpin}

## Tag: ADMIN (✅ Reorganizados v2.6.0)

### Endpoints Administrativos (Aparecen al final en Swagger UI)

- GET /health - Verificación básica del estado de la base de datos
- GET /database_status - Estadísticas detalladas de todas las tablas
- GET /tables_info - Información de esquemas y columnas
- DELETE /clear_all_data - Eliminación masiva de todas las tablas

**Nota v2.6.0**: Los endpoints ADMIN ahora aparecen al final en la documentación de Swagger para mejor organización.

## Notas de Uso - Actualizadas v2.6.0

### Consistencia de Campos (✅ Nueva v2.6.0)

- **periodo_corte**: Usado consistentemente en todas las tablas
- **Campos nullable**: Perfectamente alineados entre models, schemas y BD
- **Tipos de datos**: Validación completa entre Pydantic y SQLAlchemy
- **Nombres de campos**: Unificados en toda la aplicación

### Paginación

- `limit`: 1-10000 registros por página
- `offset`: >=0, registro inicial

### Filtros de Fecha

- `periodo_corte`: exacto (YYYY-MM) o por año (YYYY%)

### Formatos de Respuesta

- **JSON**: Endpoints estándar con schemas validados
- **GeoJSON**: RFC 7946 compatible (FeatureCollection) para endpoints geoespaciales

### Performance y Optimización (✅ Mejorados v2.6.0)

- **Carga masiva**: Usar endpoints `load_all_*` para mejor rendimiento
- **Bulk upsert**: ON CONFLICT handling automático
- **Índices**: Optimizados para consultas comunes
- **Consultas**: Eliminación de JOINs problemáticos y optimización de queries
- **Validación**: Schemas Pydantic alineados para mejor performance
