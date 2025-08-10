# 🏛️ API Dashboard Alcaldía de Santiago de Cali

Sistema de API robusto y eficiente para la gestión de datos presupuestales y proyectos de la Alcaldía de Santiago de Cali.

## 🚀 Características Principales

- **Framework:** FastAPI con optimizaciones para producción
- **Base de Datos:** PostgreSQL con pool de conexiones optimizado
- **Rendimiento:** Bulk insert/upsert para cargas masivas eficientes
- **Monitoreo:** Sistema completo de health checks y métricas
- **Mantenimiento:** Scripts automatizados para producción

## 📋 Requisitos del Sistema

- Python 3.8+
- PostgreSQL 12+
- 2GB RAM mínimo
- 10GB espacio en disco

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
- `POST /load_all_data` - **Carga masiva optimizada** (recomendado)

### Consulta de Datos (GET)

- `GET /centros_gestores` - Obtener centros gestores
- `GET /programas` - Obtener programas
- `GET /areas_funcionales` - Obtener áreas funcionales
- `GET /propositos` - Obtener propósitos
- `GET /retos` - Obtener retos
- `GET /movimientos_presupuestales` - Obtener movimientos presupuestales
- `GET /ejecucion_presupuestal` - Obtener ejecución presupuestal

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

## 🚀 Ejecución en Producción

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

### Métricas Monitoreadas

- Tiempo de respuesta de consultas
- Estado del pool de conexiones
- Conteo de registros por tabla
- Espacio usado por la base de datos
- Conexiones activas

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

## 📞 Soporte

Para soporte técnico, revisar:

1. Logs del sistema
2. Endpoint `/health` para estado general
3. Endpoint `/database_status` para métricas
4. Archivo `maintenance_report_*.md` más reciente

---

**Versión:** 2.0.0  
**Última actualización:** Agosto 2025  
**Desarrollado para:** Alcaldía de Santiago de Cali
