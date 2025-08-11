# Modelos (SQLAlchemy) y Esquemas (Pydantic)

## Modelos Principales (Resumen)

### Catálogos Base

- `CentroGestor`(cod_centro_gestor:int, nombre_centro_gestor:text)
- `Programa`(cod_programa:int, nombre_programa:text)
- `AreaFuncional`(cod_area_funcional:int, nombre_area_funcional:text)
- `Proposito`(cod_proposito:int, nombre_proposito:text)
- `Reto`(cod_reto:int, nombre_reto:text)

### Datos Transaccionales

- `MovimientoPresupuestal`(bpin:bigint, periodo_corte:varchar, ppto_inicial, adiciones, reducciones, ppto_modificado)
- `EjecucionPresupuestal`(bpin:bigint, periodo*corte:varchar, ejecucion, pagos, saldos_cdp, total*\*)

### Unidades de Proyecto

- `UnidadProyectoInfraestructuraEquipamientos`(bpin:bigint pk, identificador:varchar(255), ...)
- `UnidadProyectoInfraestructuraVial`(bpin:bigint pk, identificador:varchar(255), ...)

### ✨ Seguimiento al Plan de Acción (NUEVO)

**SeguimientoPA** - Tabla resumen

- PK: `id_seguimiento_pa` (auto-increment)
- Códigos: `cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3` (integer, nullable)
- Organización: `subdireccion_subsecretaria` (text)
- Temporal: `periodo_corte` (varchar(7))
- Presupuestal: `avance_proyecto_pa` (decimal(15,2))
- Relacionales: `bpin` (bigint, nullable)

**SeguimientoProductoPA** - Productos del plan

- PK Compuesta: (`cod_pd_lvl_1`, `cod_pd_lvl_2`)
- Identificación: `cod_producto` (text, nullable)
- Ubicación: `comuna`, `barrio`, `direccion` (text)
- Métricas: `avance_fisico_producto_pa`, `avance_financiero_producto_pa` (decimal(8,4))
- Estado: `estado_producto_pa` (text)
- Temporal: `periodo_corte` (varchar(7))

**SeguimientoActividadPA** - Actividades detalladas

- PK Compuesta: (`cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3`)
- Financiero: `ppto_vigente`, `cdp`, `ppto_ejecutado` (decimal(15,2))
- Avance: `avance_fisico_actividad_pa`, `avance_financiero_actividad_pa` (decimal(8,4))
- Control: `fecha_inicio`, `fecha_fin` (date)
- Descriptivo: `observaciones_actividad` (text)
- Relacionales: `bpin` (bigint), `periodo_corte` (varchar(7))

## Esquemas Pydantic

Los esquemas Pydantic son equivalentes a los atributos expuestos por los endpoints POST/PUT/GET, con las siguientes consideraciones:

### Tipos de Datos en Schemas

- `bpin`: int (manejado como BIGINT en BD)
- Campos monetarios: float (convertidos a DECIMAL en BD)
- Fechas: date o str (ISO format)
- Códigos: int
- Textos: str con Optional para campos nullable

### Validaciones Especiales Seguimiento PA

- Códigos de nivel requeridos según jerarquía
- Fechas en formato ISO (YYYY-MM-DD)
- Valores monetarios con precisión decimal
- Campos nullable según estructura JSON original

## Notas Técnicas

### Almacenamiento Geoespacial

- Campos geométricos no se almacenan en tablas de atributos
- GeoJSON se sirve desde archivos estáticos optimizados

### Gestión de Claves

- **Claves simples**: Auto-increment para tablas resumen
- **Claves compuestas**: Para datos jerárquicos (productos, actividades)
- **ON CONFLICT handling**: Upsert automático en cargas masivas

### Optimizaciones de Tipos

- `BIGINT` para campos bpin (soporte números grandes)
- `TEXT` para campos descriptivos (sin límite de caracteres)
- `DECIMAL(15,2)` para valores monetarios (alta precisión)
- `DECIMAL(8,4)` para porcentajes (precisión de 4 decimales)
