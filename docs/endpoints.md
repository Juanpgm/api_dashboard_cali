# Endpoints de la API

## Tag: PROYECTO

- POST /centros_gestores
- POST /programas
- POST /areas_funcionales
- POST /propositos
- POST /retos
- POST /movimientos_presupuestales
- POST /ejecucion_presupuestal
- POST /load_all_data
- GET /centros_gestores
- GET /programas
- GET /areas_funcionales
- GET /propositos
- GET /retos
- GET /movimientos_presupuestales?bpin&periodo_corte&limit&offset
- GET /ejecucion_presupuestal?bpin&periodo_corte&limit&offset
- GET /movimientos_presupuestales/count
- GET /ejecucion_presupuestal/count

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

## Tag: ADMIN

- GET /health
- GET /database_status (todas las tablas de public)
- GET /tables_info (atributos por tabla + status)
- DELETE /clear_all_data (todas las tablas de public)

## Notas de Uso

### Paginación

- `limit`: 1-10000 registros por página
- `offset`: >=0, registro inicial

### Filtros de Fecha

- `periodo_corte`: exacto (YYYY-MM) o por año (YYYY%)

### Formatos de Respuesta

- **JSON**: Endpoints estándar
- **GeoJSON**: RFC 7946 compatible (FeatureCollection) para endpoints geoespaciales

### Rendimiento

- **Carga masiva**: Usar endpoints `load_all_*` para mejor rendimiento
- **Bulk upsert**: ON CONFLICT handling automático
- **Índices**: Optimizados para consultas comunes
