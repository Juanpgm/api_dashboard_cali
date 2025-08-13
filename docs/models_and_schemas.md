# Modelos (SQLAlchemy) y Esquemas (Pydantic)

## Modelos Principales (Resumen) - Versión 2.6.0

### Catálogos Base

- `CentroGestor`(cod_centro_gestor:int, nombre_centro_gestor:text)
- `Programa`(cod_programa:int, nombre_programa:text)
- `AreaFuncional`(cod_area_funcional:int, nombre_area_funcional:text)
- `Proposito`(cod_proposito:int, nombre_proposito:text)
- `Reto`(cod_reto:int, nombre_reto:text)

### Datos Transaccionales

- `MovimientoPresupuestal`(bpin:bigint, periodo_corte:varchar, ppto_inicial, adiciones, reducciones, ppto_modificado)
- `EjecucionPresupuestal`(bpin:bigint, periodo*corte:varchar, ejecucion, pagos, saldos_cdp, total*\*)

### Contratos SECOP - Arquitectura BPIN-Centric

- `Contrato`(bpin:bigint, cod_contrato:varchar, nombre_contrato, estado_contrato, proveedor_contrato, fecha_inicio, fecha_fin_estimada)
- `ContratoValor`(bpin:bigint, cod_contrato:varchar, valor_contrato:decimal, moneda, fecha_registro)

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

## Esquemas Pydantic - Optimizados v2.6.0

Los esquemas Pydantic están perfectamente alineados con los modelos SQLAlchemy, garantizando consistencia completa entre la API y la base de datos.

### Características de Alineación v2.6.0

- ✅ **Campos nullable sincronizados**: Todos los campos opcionales/requeridos coinciden exactamente
- ✅ **Nombres de campos unificados**: `periodo_corte` consistente en todos los esquemas
- ✅ **Tipos de datos validados**: Correspondencia exacta entre Pydantic y SQLAlchemy
- ✅ **from_attributes=True**: Configuración correcta para serialización desde ORM

### Tipos de Datos en Schemas

- `bpin`: int (manejado como BIGINT en BD)
- Campos monetarios: float (convertidos a DECIMAL en BD)
- Fechas: date o str (ISO format)
- Códigos: int
- Textos: str con Optional para campos nullable
- `periodo_corte`: str (formato YYYY-MM o YYYY-MM-DD según tabla)

### Validaciones Específicas

#### Contratos SECOP

- `bpin` y `cod_contrato` requeridos (clave compuesta)
- `valor_contrato` como Decimal para precisión financiera
- Fechas en formato ISO con validación automática

#### Seguimiento PA

- Códigos de nivel requeridos según jerarquía
- Fechas en formato ISO (YYYY-MM-DD)
- Valores monetarios con precisión decimal
- Campos nullable según estructura de datos original

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
