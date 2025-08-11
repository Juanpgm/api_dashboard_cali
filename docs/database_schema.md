# Esquema de Base de Datos

## Categorías de Tablas

### Catálogos

- `centros_gestores`, `programas`, `areas_funcionales`, `propositos`, `retos`

### Transaccionales

- `movimientos_presupuestales`, `ejecucion_presupuestal`

### Unidades de Proyecto

- `unidades_proyecto_infraestructura_equipamientos`, `unidades_proyecto_infraestructura_vial`

### ✨ Seguimiento al Plan de Acción (NUEVO)

- `seguimiento_pa` - Resumen consolidado por proyecto
- `seguimiento_productos_pa` - Productos del plan de acción
- `seguimiento_actividades_pa` - Actividades detalladas

## Convenciones de Tipos de Datos

### Campos Comunes

- `bpin`: BIGINT
- `periodo_corte`: VARCHAR(50) para datos generales, VARCHAR(7) para seguimiento PA (YYYY-MM)
- `identificador` (unidades*proyecto*\*): VARCHAR(255)

### Seguimiento PA - Tipos Específicos

- `id_seguimiento_pa`: INTEGER AUTO-INCREMENT (PK en tabla resumen)
- `cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3`: INTEGER (códigos de niveles)
- Valores monetarios: DECIMAL(15,2) (presupuestos, avances financieros)
- Porcentajes/avances: DECIMAL(8,4) (alta precisión para porcentajes)
- Textos descriptivos: TEXT (nombres, descripciones, observaciones)

### Claves Primarias

**Seguimiento PA:**

- `seguimiento_pa`: `id_seguimiento_pa` (auto-increment)
- `seguimiento_productos_pa`: Compuesta (`cod_pd_lvl_1`, `cod_pd_lvl_2`)
- `seguimiento_actividades_pa`: Compuesta (`cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3`)

## Índices Recomendados

### Índices Existentes

- `movimientos_presupuestales`(bpin), (periodo_corte)
- `ejecucion_presupuestal`(bpin), (periodo_corte)
- `unidades_proyecto_*` (identificador), (comuna_corregimiento), (estado_unidad_proyecto)

### ✨ Nuevos Índices para Seguimiento PA

- `seguimiento_pa`(periodo_corte), (subdireccion_subsecretaria)
- `seguimiento_productos_pa`(cod_pd_lvl_1), (cod_pd_lvl_2)
- `seguimiento_actividades_pa`(cod_pd_lvl_1), (cod_pd_lvl_2), (cod_pd_lvl_3)

## Estructura de Datos de Seguimiento PA

### Campos Principales por Tabla

**seguimiento_pa (Resumen):**

- Códigos: cod_pd_lvl_1, cod_pd_lvl_2, cod_pd_lvl_3
- Organización: subdireccion_subsecretaria
- Presupuestal: avance_proyecto_pa (DECIMAL)
- Temporal: periodo_corte

**seguimiento_productos_pa:**

- Identificación: cod_producto (nullable)
- Ubicación: Comuna, barrio, direccion
- Métricas: avance_fisico_producto_pa, avance_financiero_producto_pa
- Estado: estado_producto_pa

**seguimiento_actividades_pa:**

- Financiero: ppto_vigente, cdp, ppto_ejecutado
- Avance: avance_fisico_actividad_pa, avance_financiero_actividad_pa
- Control: fecha_inicio, fecha_fin, observaciones_actividad
