# Endpoints de la API

Tag: PROYECTO

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

Tag: PROYECTO: UNIDADES DE PROYECTO - INFRAESTRUCTURA

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

Tag: ADMIN

- GET /health
- GET /database_status (todas las tablas de public)
- GET /tables_info (atributos por tabla + status)
- DELETE /clear_all_data (todas las tablas de public)

Notas:

- Paginación: limit (1-10000), offset (>=0)
- Filtro periodo_corte: exacto (YYYY-MM) o por año (YYYY%)
- GeoJSON: RFC 7946 compatible (FeatureCollection)
