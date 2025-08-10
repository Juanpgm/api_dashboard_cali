# API Dashboard - Estado Actual y Configuración

## ✅ Estado de la API

### Servidor

- **URL Base:** `http://127.0.0.1:8000`
- **Estado:** ✅ Ejecutándose correctamente
- **Framework:** FastAPI con documentación automática en `/docs`

### Base de Datos

- **Registros Totales:** 96,664 registros cargados
- **Estado:** ✅ Poblada con datos de ejecución presupuestal
- **Tabla Principal:** `project_execution`

### Vistas Materializadas

- **dashboard_metrics_mv:** ✅ 1 registro (métricas principales)
- **dashboard_timeline_mv:** ✅ 18 registros (datos temporales)
- **dashboard_top_programs_mv:** ✅ 8,586 registros (programas)
- **dashboard_centers_summary_mv:** ✅ 29 registros (centros gestores)
- **dashboard_filter_options_mv:** ✅ 22,557 registros (opciones de filtros)

## 📊 Endpoints Principales para Frontend

### 1. Carga Completa de Dashboard (RECOMENDADO)

```
GET /load_materialized_views/
```

- **Propósito:** Carga todas las vistas materializadas en una sola llamada
- **Optimizado para:** Next.js y frontends que necesitan datos completos
- **Respuesta:** JSON con todas las vistas organizadas por secciones

### 2. Endpoints Individuales de Dashboard

#### Métricas Principales

```
GET /dashboard/metrics/
```

- Totales de proyectos, centros gestores, programas
- Presupuestos, ejecución, pagos
- Porcentajes de ejecución

#### Línea de Tiempo

```
GET /dashboard/timeline/
```

- Datos históricos por período
- Evolución de presupuestos y ejecución
- Proyectos activos por período

#### Top Programas

```
GET /dashboard/top_programs/?limit=10
```

- Programas ordenados por presupuesto
- Porcentajes de ejecución por programa
- Filtrable por cantidad

#### Resumen de Centros Gestores

```
GET /dashboard/centers_summary/
```

- Totales por centro gestor
- Proyectos y programas por centro
- Porcentajes de ejecución

#### Opciones de Filtros

```
GET /dashboard/filters_options/
```

- Centros gestores disponibles
- Programas presupuestales
- Proyectos, líneas estratégicas
- Años con datos disponibles

#### Proyectos Paginados (con Filtros)

```
GET /dashboard/projects_paginated/?page=1&size=50&search=&center_filter=&program_filter=&year_filter=
```

- Paginación completa
- Filtros múltiples
- Búsqueda por texto

#### Comparación Anual

```
GET /dashboard/yearly_comparison/
```

- Métricas comparativas por año
- Crecimiento año a año
- Rankings por diferentes métricas

### 3. Gestión de Datos

#### Carga de Datos

```
POST /upload_and_process_data_from/
Body: directory_path=C:\ruta\a\datos
```

- Procesa archivos CSV/Excel desde directorio
- Normaliza columnas automáticamente
- Retorna estadísticas de procesamiento

#### Configuración del Dashboard

```
POST /setup_dashboard/
```

- Crea/actualiza vistas materializadas
- Valida existencia de datos
- Prepara la API para consumo frontend

#### Actualización de Vistas

```
POST /refresh_materialized_views/
```

- Actualiza vistas con datos más recientes
- Usar después de cargar nuevos datos
- Mantiene el rendimiento optimizado

### 4. Información y Monitoreo

#### Estado de la Base de Datos

```
GET /database_info/
```

- Cantidad de registros
- Muestra de datos
- Estado general

#### Estado de Vistas Materializadas

```
GET /check_materialized_views/
```

- Verificación de existencia
- Conteo de registros por vista
- Diagnóstico completo

## 🔧 Configuración para Next.js

### Variables de Entorno Sugeridas

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### Hook Recomendado

```javascript
export const useDashboardData = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/load_materialized_views/`)
      .then((res) => res.json())
      .then((result) => {
        if (result.status === "success") {
          setData(result.materialized_views);
        }
        setLoading(false);
      });
  }, []);

  return { data, loading };
};
```

## 📈 Datos Disponibles

### Métricas Principales

- **1,252 proyectos únicos**
- **27 centros gestores**
- **932 programas presupuestales**
- **$6.36T presupuesto modificado**
- **$3.98T en ejecución (61.6%)**
- **$3.45T en pagos (43.28%)**

### Cobertura Temporal

- **Años:** 2024-2025
- **Períodos:** Enero 2024 - Junio 2025
- **18 períodos mensuales** con datos

### Filtros Disponibles

- **Centros Gestores:** 27 opciones
- **Programas:** 932 opciones
- **Proyectos:** Miles de opciones
- **Líneas Estratégicas:** Múltiples opciones
- **Años:** 2024, 2025

## 🚀 Flujo de Trabajo Frontend

### 1. Inicialización

```javascript
// Verificar estado
const dbInfo = await fetch("/database_info/").then((r) => r.json());

// Si hay datos, cargar dashboard
if (dbInfo.total_records > 0) {
  const dashboard = await fetch("/load_materialized_views/").then((r) =>
    r.json()
  );
}
```

### 2. Carga de Dashboard

```javascript
// Opción 1: Carga completa (recomendado)
const allData = await fetch("/load_materialized_views/").then((r) => r.json());

// Opción 2: Carga por componentes
const metrics = await fetch("/dashboard/metrics/").then((r) => r.json());
const timeline = await fetch("/dashboard/timeline/").then((r) => r.json());
```

### 3. Actualización de Datos

```javascript
// Cuando se suban nuevos datos
await fetch("/refresh_materialized_views/", { method: "POST" });

// Recargar dashboard
const updatedData = await fetch("/load_materialized_views/").then((r) =>
  r.json()
);
```

## ✅ Lista de Verificación

- [x] ✅ API FastAPI funcionando en puerto 8000
- [x] ✅ Base de datos poblada con 96,664 registros
- [x] ✅ 5 vistas materializadas creadas y pobladas
- [x] ✅ Endpoint unificado para carga completa (`/load_materialized_views/`)
- [x] ✅ Endpoints individuales para componentes específicos
- [x] ✅ Sistema de filtros y paginación
- [x] ✅ Gestión de errores y validaciones
- [x] ✅ Documentación automática en `/docs`
- [x] ✅ Manejo de datos nulos y formatos
- [x] ✅ Optimización de rendimiento con vistas materializadas

## 🎯 Listo para Integración

La API está **completamente configurada y optimizada** para ser consumida por Next.js. Todas las vistas materializadas están pobladas con datos reales y los endpoints están respondiendo correctamente.

**Siguiente paso:** Implementar la integración en Next.js usando los endpoints documentados arriba.
