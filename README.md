# 🏛️ API Dashboard Alcaldía de Santiago de Cali

Sistema de API robusto y eficiente para la gestión de datos presupuestales y proyectos de la Alcaldía de Santiago de Cali.

## 🚀 Características Principales

- **Framework:** FastAPI con optimizaciones para producción
- **Base de Datos:** PostgreSQL con pool de conexiones optimizado
- **Transformación de Datos:** Sistema automatizado de procesamiento de archivos Excel
- **Rendimiento:** Bulk insert/upsert para cargas masivas eficientes
- **Monitoreo:** Sistema completo de health checks y métricas
- **Mantenimiento:** Scripts automatizados para producción

## 📋 Requisitos del Sistema

- Python 3.8+
- PostgreSQL 12+
- 2GB RAM mínimo
- 10GB espacio en disco
- Microsoft Excel o LibreOffice para archivos .xlsx

## ⚡ Instalación Rápida para Producción

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd api-dashboard-db

# 2. Configurar entorno virtual
python -m venv env
source env/bin/activate  # Linux/Mac
# env\Scripts\activate    # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL

# 5. Despliegue automático
python production_deployment.py
```

## 🔧 Configuración

### Variables de Entorno (.env)

```env
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_contraseña
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=proyectos_alcaldia_db
```

### Estructura de Base de Datos

El sistema maneja automáticamente la creación y migración de las siguientes tablas:

- **centros_gestores** - Catálogo de centros gestores
- **programas** - Catálogo de programas presupuestales
- **areas_funcionales** - Catálogo de áreas funcionales
- **propositos** - Catálogo de propósitos
- **retos** - Catálogo de retos
- **movimientos_presupuestales** - Datos de movimientos presupuestales (clave compuesta: bpin + periodo_corte)
- **ejecucion_presupuestal** - Datos de ejecución presupuestal (clave compuesta: bpin + periodo_corte)
- **seguimiento_actividades_pa** - Actividades de seguimiento del plan de acción
- **seguimiento_productos_pa** - Productos de seguimiento del plan de acción
- **seguimiento_pa** - Resumen de seguimiento del plan de acción

## 📊 Sistema de Transformación de Datos

### Scripts de Transformación (`transformation_app/`)

El sistema incluye módulos especializados para el procesamiento y transformación de datos:

#### **Ejecución Presupuestal**

```bash
python transformation_app/data_transformation_ejecucion_presupuestal.py
```

**Funcionalidad:**

- Procesa archivos Excel desde `app_inputs/ejecucion_presupuestal_input/`
- Genera datos estandarizados de ejecución presupuestal
- Salida: JSON estructurado en `app_outputs/ejecucion_presupuestal_outputs/`

#### **Seguimiento Plan de Acción**

```bash
python transformation_app/data_transformation_seguimiento_pa.py
```

**Funcionalidad:**

- ✨ **NUEVO:** Procesamiento automatizado de seguimiento PA
- Entrada: Archivos Excel (.xlsx) en `app_inputs/seguimiento_pa_input/`
- Detección automática de tipos de archivo (detallados vs resumen)
- Limpieza avanzada de datos numéricos y monetarios
- Genera 3 datasets JSON:
  - `seguimiento_actividades_pa.json` - Actividades con datos presupuestales
  - `seguimiento_productos_pa.json` - Productos con métricas de avance
  - `seguimiento_pa.json` - Resumen consolidado por proyecto

**Características técnicas:**

- 🔧 Preserva valores numéricos originales eliminando solo símbolos de formato
- 🔧 Manejo inteligente de separadores de miles y decimales
- 🔧 Conversión automática de tipos: BPIN → entero, fechas → ISO, valores → decimal(2)
- 🔧 Soporte para archivos con múltiples hojas y formatos
- 📊 Procesa 10,000+ registros eficientemente

#### **Unidades de Proyecto**

```bash
python transformation_app/data_transformation_unidades_proyecto.py
```

**Funcionalidad:**

- Procesa datos de infraestructura y equipamientos
- Entrada: `app_inputs/unidades_proyecto_input/`
- Salida: `app_outputs/unidades_proyecto_outputs/`

### Estructura de Directorios de Transformación

```
transformation_app/
├── data_transformation_ejecucion_presupuestal.py
├── data_transformation_seguimiento_pa.py          # ✨ NUEVO
├── data_transformation_unidades_proyecto.py
├── app_inputs/
│   ├── ejecucion_presupuestal_input/
│   ├── seguimiento_pa_input/                       # ✨ NUEVO
│   └── unidades_proyecto_input/
└── app_outputs/
    ├── ejecucion_presupuestal_outputs/
    ├── seguimiento_pa_outputs/                     # ✨ NUEVO
    └── unidades_proyecto_outputs/
```

### Calidad de Datos Garantizada

**Tipos de Datos Estandarizados:**

- `bpin` y códigos: **BIGINT** (enteros sin decimales)
- Fechas: **DATE** formato ISO (YYYY-MM-DD)
- Valores monetarios: **DECIMAL(15,2)** (presupuestos, pagos, obligaciones)
- Porcentajes y avances: **DECIMAL(5,2)** (conserva precisión original)
- Nombres y descripciones: **TEXT** (sin límites de caracteres)
- Períodos: **VARCHAR(7)** formato YYYY-MM

**Limpieza Automática:**

- ✅ Eliminación de símbolos monetarios ($, separadores de miles)
- ✅ Normalización de separadores decimales (coma/punto)
- ✅ Preservación de valores numéricos originales
- ✅ Manejo de celdas vacías y valores nulos

## 🏗️ Scripts de Administración

### Inicialización de Base de Datos

```bash
python database_initializer.py
```

- Crea todas las tablas con tipos de datos correctos
- Configura claves primarias compuestas donde sea necesario
- Crea índices para optimizar consultas
- Valida integridad del esquema

### Mantenimiento de Producción

```bash
# Chequeos de salud básicos
python production_maintenance.py

# Con optimizaciones
python production_maintenance.py --optimize

# Con backup de datos
python production_maintenance.py --backup
```

### Despliegue Completo

```bash
# Despliegue con confirmación
python production_deployment.py

# Despliegue automático
python production_deployment.py --force

# Modo silencioso
python production_deployment.py --force --quiet
```

## 🌐 Endpoints del API

### Carga de Datos (POST)

- `POST /centros_gestores` - Cargar centros gestores
- `POST /programas` - Cargar programas
- `POST /areas_funcionales` - Cargar áreas funcionales
- `POST /propositos` - Cargar propósitos
- `POST /retos` - Cargar retos
- `POST /movimientos_presupuestales` - Cargar movimientos presupuestales
- `POST /ejecucion_presupuestal` - Cargar ejecución presupuestal
- `POST /seguimiento_actividades_pa` - Cargar actividades de seguimiento PA
- `POST /seguimiento_productos_pa` - Cargar productos de seguimiento PA
- `POST /seguimiento_pa` - Cargar resumen de seguimiento PA
- `POST /load_all_data` - **Carga masiva optimizada** (recomendado)

### Consulta de Datos (GET)

- `GET /centros_gestores` - Obtener centros gestores
- `GET /programas` - Obtener programas
- `GET /areas_funcionales` - Obtener áreas funcionales
- `GET /propositos` - Obtener propósitos
- `GET /retos` - Obtener retos
- `GET /movimientos_presupuestales` - Obtener movimientos presupuestales
- `GET /ejecucion_presupuestal` - Obtener ejecución presupuestal
- `GET /seguimiento_actividades_pa` - Obtener actividades de seguimiento PA
- `GET /seguimiento_productos_pa` - Obtener productos de seguimiento PA
- `GET /seguimiento_pa` - Obtener resumen de seguimiento PA

### Unidades de Proyecto - Infraestructura

- `POST /unidades_proyecto/equipamientos` - Cargar equipamientos
- `POST /unidades_proyecto/vial` - Cargar infraestructura vial
- `GET /unidades_proyecto/equipamientos` - Consultar equipamientos (filtros: bpin, limit, offset)
- `GET /unidades_proyecto/vial` - Consultar infraestructura vial (filtros: bpin, limit, offset)
- `GET /unidades_proyecto/equipamientos/geojson` - GeoJSON de equipamientos (RFC 7946)
- `GET /unidades_proyecto/vial/geojson` - GeoJSON de infraestructura vial (RFC 7946)
- `GET /unidades_proyecto/equipamientos/count` - Conteo equipamientos
- `GET /unidades_proyecto/vial/count` - Conteo infraestructura vial
- `PUT /unidades_proyecto/equipamientos/{bpin}` - Actualizar registro por BPIN
- `PUT /unidades_proyecto/vial/{bpin}` - Actualizar registro por BPIN

### Administración

- `GET /health` - Verificar estado del sistema
- `GET /database_status` - Estadísticas de la base de datos
- `GET /tables_info` - Información detallada de tablas
- `DELETE /clear_all_data` - ⚠️ Limpiar todos los datos

## � Flujo de Trabajo de Datos

### 1. Transformación de Datos

```bash
# Procesar datos de seguimiento PA
python transformation_app/data_transformation_seguimiento_pa.py

# Procesar datos de ejecución presupuestal
python transformation_app/data_transformation_ejecucion_presupuestal.py

# Procesar unidades de proyecto
python transformation_app/data_transformation_unidades_proyecto.py
```

### 2. Carga a Base de Datos

```bash
# Usar los endpoints POST del API para cargar los JSON generados
curl -X POST "http://localhost:8000/seguimiento_actividades_pa" \
     -H "Content-Type: application/json" \
     -d @transformation_app/app_outputs/seguimiento_pa_outputs/seguimiento_actividades_pa.json
```

### 3. Consulta de Datos

```bash
# Consultar datos a través del API
curl "http://localhost:8000/seguimiento_actividades_pa?bpin=2021760010222"
```

## �🚀 Ejecución en Producción

### Modo Desarrollo

```bash
uvicorn fastapi_project.main:app --reload --port 8000
```

### Modo Producción

```bash
uvicorn fastapi_project.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Con Gunicorn (Recomendado para producción)

```bash
pip install gunicorn
gunicorn fastapi_project.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📊 Optimizaciones Implementadas

### Rendimiento de Base de Datos

- **Bulk Insert/Upsert:** Carga de ~97,000 registros en <35 segundos
- **Pool de Conexiones:** Configurado para alta concurrencia
- **Índices Optimizados:** En campos críticos (bpin, periodo_corte)
- **Transacciones:** Manejo seguro con rollback automático

### Arquitectura

- **Código DRY:** Función genérica para eliminación de duplicación
- **Validación:** Pydantic schemas antes de inserción en BD
- **Logging:** Sistema completo de logging para debugging
- **Error Handling:** Manejo robusto de excepciones

### Tipos de Datos Optimizados

- `BIGINT` para campos bpin (soporte números grandes)
- `TEXT` para nombres largos (sin límite de 255 caracteres)
- `VARCHAR(50)` para periodo_corte (formato YYYY-MM)
- `DOUBLE PRECISION` para valores monetarios

## 🔍 Monitoreo y Logs

### Archivos de Log

- `database_init.log` - Inicialización de base de datos
- `maintenance_YYYYMMDD.log` - Mantenimiento diario
- `deployment_YYYYMMDD_HHMMSS.log` - Logs de despliegue
- `transformation_app/transformation_*.log` - Logs de transformación de datos

### Métricas Monitoreadas

- Tiempo de respuesta de consultas
- Estado del pool de conexiones
- Conteo de registros por tabla
- Espacio usado por la base de datos
- Conexiones activas
- **NUEVO:** Métricas de procesamiento de transformación de datos

## 🛡️ Seguridad

- Credenciales de BD en variables de entorno
- Pool de conexiones con límites configurados
- Validación de entrada con Pydantic
- Logging de operaciones críticas
- Rollback automático en caso de error

## 📈 Escalabilidad

El sistema está diseñado para:

- **Datos:** Millones de registros por tabla
- **Concurrencia:** Múltiples workers con pool compartido
- **Memoria:** Gestión eficiente con bulk operations
- **Red:** Respuestas optimizadas con paginación

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de conexión a PostgreSQL**

   ```bash
   python database_initializer.py
   ```

2. **Tipos de datos incorrectos**

   ```bash
   python production_maintenance.py --optimize
   ```

3. **Rendimiento lento**

   - Verificar índices: `GET /tables_info`
   - Ejecutar VACUUM: `python production_maintenance.py --optimize`

4. **Datos inconsistentes**

   ```bash
   # Backup y recarga
   python production_maintenance.py --backup
   DELETE /clear_all_data
   POST /load_all_data
   ```

5. **Errores en transformación de datos**

   ```bash
   # Verificar formato de archivos Excel
   # Revisar logs de transformación
   # Validar estructura de directorios app_inputs/
   ```

6. **Problemas con valores numéricos**
   ```bash
   # Los scripts automáticamente limpian:
   # - Símbolos monetarios ($)
   # - Separadores de miles (. ,)
   # - Espacios y caracteres especiales
   # - Mantienen precisión decimal original
   ```

## 📞 Soporte

Para soporte técnico, revisar:

1. Logs del sistema
2. Endpoint `/health` para estado general
3. Endpoint `/database_status` para métricas
4. Archivo `maintenance_report_*.md` más reciente

---

**Versión:** 2.1.0  
**Última actualización:** Agosto 11, 2025  
**Desarrollado para:** Alcaldía de Santiago de Cali  
**Nuevas funcionalidades:** Sistema de transformación de seguimiento PA
