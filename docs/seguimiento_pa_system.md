# 🏛️ Sistema de Seguimiento al Plan de Acción

## Resumen del Sistema

El Sistema de Seguimiento al Plan de Acción es un módulo completo que procesa, almacena y consulta datos relacionados con el seguimiento de proyectos de la Alcaldía de Santiago de Cali. Implementado en la versión 2.2.0 del API Dashboard.

### 📊 Datos Procesados

- **1,396 registros** de resumen consolidado por proyecto
- **1,990 registros** de productos del plan de acción
- **10,737 registros** de actividades detalladas
- **Total: 14,123 registros** de seguimiento PA

## 🗄️ Arquitectura de Base de Datos

### Estructura de Tablas

#### `seguimiento_pa` (Resumen)

- **Clave Primaria:** `id_seguimiento_pa` (auto-increment)
- **Propósito:** Datos consolidados por proyecto/subdireccion
- **Campos clave:**
  - Códigos de nivel: `cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3`
  - Organización: `subdireccion_subsecretaria`
  - Avance: `avance_proyecto_pa` (DECIMAL(15,2))

#### `seguimiento_productos_pa` (Productos)

- **Clave Primaria:** Compuesta (`cod_pd_lvl_1`, `cod_pd_lvl_2`)
- **Propósito:** Productos específicos del plan de acción
- **Campos clave:**
  - Identificación: `cod_producto` (nullable)
  - Ubicación: `comuna`, `barrio`, `direccion`
  - Avances: `avance_fisico_producto_pa`, `avance_financiero_producto_pa`

#### `seguimiento_actividades_pa` (Actividades)

- **Clave Primaria:** Compuesta (`cod_pd_lvl_1`, `cod_pd_lvl_2`, `cod_pd_lvl_3`)
- **Propósito:** Actividades detalladas con datos presupuestales
- **Campos clave:**
  - Financiero: `ppto_vigente`, `cdp`, `ppto_ejecutado`
  - Control temporal: `fecha_inicio`, `fecha_fin`
  - Avances: `avance_fisico_actividad_pa`, `avance_financiero_actividad_pa`

### Tipos de Datos Optimizados

- **Valores monetarios:** DECIMAL(15,2) para presupuestos grandes
- **Porcentajes:** DECIMAL(8,4) para alta precisión
- **Fechas:** DATE en formato ISO
- **Códigos:** INTEGER para eficiencia
- **Periodos:** VARCHAR(7) formato YYYY-MM

## 🚀 Endpoints del API

### Carga de Datos

```http
POST /seguimiento_pa
POST /seguimiento_productos_pa
POST /seguimiento_actividades_pa
POST /load_all_seguimiento_pa  # Recomendado para carga masiva
```

### Consulta de Datos

```http
GET /seguimiento_pa?id_seguimiento_pa&periodo_corte&subdireccion_subsecretaria&limit&offset
GET /seguimiento_productos_pa?cod_pd_lvl_1&cod_pd_lvl_2&comuna&estado_producto_pa&limit&offset
GET /seguimiento_actividades_pa?cod_pd_lvl_1&cod_pd_lvl_2&cod_pd_lvl_3&bpin&limit&offset
```

### Ejemplos de Uso

#### Carga Masiva (Recomendado)

```bash
curl -X POST "http://localhost:8000/load_all_seguimiento_pa"
```

#### Consulta por Periodo

```bash
curl "http://localhost:8000/seguimiento_pa?periodo_corte=2024-12&limit=50"
```

#### Consulta por Comuna

```bash
curl "http://localhost:8000/seguimiento_productos_pa?comuna=Comuna%201&limit=20"
```

#### Consulta por BPIN

```bash
curl "http://localhost:8000/seguimiento_actividades_pa?bpin=2021760010222"
```

## 🔧 Transformación de Datos

### Archivo de Transformación

`transformation_app/data_transformation_seguimiento_pa.py`

### Proceso de Transformación

1. **Lectura:** Archivos Excel (.xlsx) desde `app_inputs/seguimiento_pa_input/`
2. **Limpieza:** Eliminación de símbolos monetarios y normalización de números
3. **Categorización:** Detección automática de tipos (actividades, productos, resumen)
4. **Generación:** 3 archivos JSON estandarizados

### Archivos de Salida

- `seguimiento_actividades_pa.json` - Actividades detalladas
- `seguimiento_productos_pa.json` - Productos del plan
- `seguimiento_pa.json` - Resumen consolidado

## 📈 Rendimiento y Optimizaciones

### Índices de Base de Datos

```sql
-- Índices para seguimiento_pa
CREATE INDEX idx_seguimiento_pa_periodo ON seguimiento_pa(periodo_corte);
CREATE INDEX idx_seguimiento_pa_subdireccion ON seguimiento_pa(subdireccion_subsecretaria);

-- Índices para seguimiento_productos_pa
CREATE INDEX idx_seguimiento_productos_pa_cod1 ON seguimiento_productos_pa(cod_pd_lvl_1);
CREATE INDEX idx_seguimiento_productos_pa_cod2 ON seguimiento_productos_pa(cod_pd_lvl_2);

-- Índices para seguimiento_actividades_pa
CREATE INDEX idx_seguimiento_actividades_pa_cod1 ON seguimiento_actividades_pa(cod_pd_lvl_1);
CREATE INDEX idx_seguimiento_actividades_pa_cod2 ON seguimiento_actividades_pa(cod_pd_lvl_2);
CREATE INDEX idx_seguimiento_actividades_pa_cod3 ON seguimiento_actividades_pa(cod_pd_lvl_3);
```

### Métricas de Rendimiento

- **Carga completa:** ~3.7 segundos para 14,123 registros
- **Consultas indexadas:** Sub-segundo para filtros comunes
- **Bulk upsert:** ON CONFLICT handling automático

## 🔍 Casos de Uso Comunes

### 1. Dashboard Ejecutivo

Consultar resumen por subdireccion para dashboards de alto nivel:

```sql
SELECT subdireccion_subsecretaria,
       AVG(avance_proyecto_pa) as avance_promedio,
       COUNT(*) as total_proyectos
FROM seguimiento_pa
WHERE periodo_corte = '2024-12'
GROUP BY subdireccion_subsecretaria;
```

### 2. Seguimiento Territorial

Consultar productos por comuna para análisis territorial:

```sql
SELECT comuna, estado_producto_pa,
       AVG(avance_fisico_producto_pa) as avance_fisico_promedio
FROM seguimiento_productos_pa
GROUP BY comuna, estado_producto_pa;
```

### 3. Control Presupuestal

Consultar actividades con mayor ejecución presupuestal:

```sql
SELECT cod_pd_lvl_1, cod_pd_lvl_2, cod_pd_lvl_3,
       ppto_vigente, ppto_ejecutado,
       (ppto_ejecutado/ppto_vigente)*100 as porcentaje_ejecucion
FROM seguimiento_actividades_pa
WHERE ppto_vigente > 0
ORDER BY porcentaje_ejecucion DESC;
```

## 🛠️ Mantenimiento

### Verificación de Integridad

```bash
python -c "
from fastapi_project.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Verificar conteos
    result = conn.execute(text('SELECT COUNT(*) FROM seguimiento_pa'))
    print(f'seguimiento_pa: {result.scalar()} registros')
"
```

### Limpieza y Recarga

```bash
# Limpiar datos existentes
curl -X DELETE "http://localhost:8000/clear_all_data"

# Recargar datos
curl -X POST "http://localhost:8000/load_all_seguimiento_pa"
```

## 🔐 Consideraciones de Seguridad

- **Validación:** Esquemas Pydantic validan entrada antes de BD
- **Transacciones:** Rollback automático en caso de error
- **Logging:** Trazabilidad completa de operaciones
- **Sanitización:** Limpieza automática de datos de entrada

## 📋 Checklist de Implementación

- ✅ Modelos SQLAlchemy definidos
- ✅ Esquemas Pydantic validados
- ✅ Endpoints API funcionales
- ✅ Transformación de datos automática
- ✅ Índices de rendimiento creados
- ✅ Sistema de carga masiva
- ✅ Documentación actualizada
- ✅ Pruebas de integración exitosas

---

**Sistema implementado:** Agosto 11, 2025  
**Tag del sistema:** PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN  
**Registros procesados:** 14,123 total  
**Estado:** ✅ Completamente funcional
