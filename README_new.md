# 🏛️ API Dashboard Alcaldía de Santiago de Cali

Sistema integral de gestión de datos presupuestales, proyectos y contratos para la Alcaldía de Santiago de Cali. Proporciona una API robusta y eficiente para el manejo de información gubernamental con capacidades avanzadas de transformación y análisis de datos.

## 📋 Descripción del Proyecto

Este sistema está diseñado para centralizar y gestionar la información presupuestal, contractual y de seguimiento de proyectos de la Alcaldía de Santiago de Cali. Ofrece una arquitectura escalable que integra múltiples fuentes de datos y proporciona endpoints especializados para diferentes tipos de consultas y operaciones.

### Funcionalidades Principales

- **Gestión Presupuestal**: Manejo de movimientos y ejecución presupuestal con datos históricos
- **Contratos SECOP**: Sistema optimizado para gestión de contratos con arquitectura BPIN-centric
- **Seguimiento de Proyectos**: Monitoreo del Plan de Acción con métricas de avance y productos
- **Infraestructura**: Gestión de unidades de proyecto, equipamientos e infraestructura vial
- **Transformación de Datos**: Procesamiento automatizado de archivos Excel a formatos estandarizados
- **API RESTful**: Endpoints especializados para consultas, cargas masivas y administración

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
api-dashboard-db/
├── fastapi_project/           # Aplicación principal FastAPI
│   ├── main.py               # Endpoints y configuración API
│   ├── models.py             # Modelos SQLAlchemy
│   ├── schemas.py            # Esquemas Pydantic
│   └── database.py           # Configuración base de datos
├── transformation_app/       # Sistema de transformación de datos
│   ├── data_transformation_*.py  # Scripts de transformación
│   ├── app_inputs/          # Directorio de archivos de entrada
│   └── app_outputs/         # Directorio de archivos procesados
├── docs/                    # Documentación del proyecto
├── database_initializer.py # Inicialización y migración de BD
├── production_*.py         # Scripts de producción y mantenimiento
└── requirements.txt        # Dependencias del proyecto
```

### Stack Tecnológico

- **Backend**: FastAPI (Python 3.8+)
- **Base de Datos**: PostgreSQL 12+
- **ORM**: SQLAlchemy
- **Validación**: Pydantic
- **Documentación**: Swagger UI automático
- **Procesamiento**: Pandas, OpenPyXL para archivos Excel

## 🛠️ Configuración e Instalación

### Requisitos del Sistema

- **Python**: 3.8 o superior
- **PostgreSQL**: 12 o superior
- **RAM**: Mínimo 2GB, recomendado 4GB
- **Almacenamiento**: Mínimo 10GB para datos y logs
- **Herramientas**: Git, Microsoft Excel o LibreOffice para archivos .xlsx

### Configuración de Base de Datos

#### 1. Crear Base de Datos PostgreSQL

```sql
-- Conectar como superusuario
CREATE DATABASE api_dashboard_cali;
CREATE USER api_user WITH PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE api_dashboard_cali TO api_user;
```

#### 2. Variables de Entorno

Crear archivo `.env` en el directorio raíz:

```env
# Configuración PostgreSQL
POSTGRES_USER=api_user
POSTGRES_PASSWORD=tu_contraseña_segura
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=api_dashboard_cali

# Configuración API (opcional)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

### Instalación del Sistema

#### Método 1: Instalación Manual

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd api-dashboard-db

# 2. Crear entorno virtual
python -m venv env

# 3. Activar entorno virtual
# En Windows:
env\Scripts\activate
# En Linux/Mac:
source env/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno
# Editar archivo .env con las credenciales correctas

# 6. Inicializar base de datos
python database_initializer.py

# 7. Ejecutar servidor
uvicorn fastapi_project.main:app --reload
```

#### Método 2: Despliegue Automatizado

```bash
# Despliegue completo automatizado
python production_deployment.py

# Con configuraciones específicas
python production_deployment.py --force --optimize
```

## 📊 Estructura de Datos

### Tablas Principales

#### Catálogos Base

- **centros_gestores**: Centros gestores de la alcaldía
- **programas**: Programas presupuestales
- **areas_funcionales**: Áreas funcionales organizacionales
- **propositos**: Propósitos de proyectos
- **retos**: Retos estratégicos

#### Datos Operacionales

- **movimientos_presupuestales**: Movimientos presupuestales por proyecto (clave: bpin + periodo)
- **ejecucion_presupuestal**: Ejecución presupuestal detallada (clave: bpin + periodo)
- **contratos**: Contratos SECOP con información completa (clave: bpin + cod_contrato)
- **contratos_valores**: Valores financieros de contratos (clave: bpin + cod_contrato)

#### Seguimiento de Proyectos

- **seguimiento_pa**: Resumen de seguimiento del Plan de Acción (PK auto-increment)
- **seguimiento_productos_pa**: Productos del Plan de Acción (clave: cod_pd_lvl_1 + cod_pd_lvl_2)
- **seguimiento_actividades_pa**: Actividades detalladas (clave: cod_pd_lvl_1 + cod_pd_lvl_2 + cod_pd_lvl_3)

#### Infraestructura

- **unidades_proyecto_infraestructura_equipamientos**: Equipamientos por proyecto
- **unidades_proyecto_infraestructura_vial**: Infraestructura vial por proyecto

### Tipos de Datos Estandarizados

- **BPIN**: `BIGINT` - Códigos de proyectos de inversión
- **Períodos**: `VARCHAR(7)` - Formato YYYY-MM
- **Valores monetarios**: `DECIMAL(15,2)` - Presupuestos y pagos
- **Porcentajes**: `DECIMAL(5,2)` - Avances y porcentajes de ejecución
- **Fechas**: `DATE` - Formato ISO (YYYY-MM-DD)
- **Textos**: `TEXT` - Nombres y descripciones sin límite

## 🔄 Sistema de Transformación de Datos

### Procesamiento Automatizado

El sistema incluye scripts especializados para transformar archivos Excel en formatos estandarizados:

#### Scripts Disponibles

1. **Ejecución Presupuestal**: `data_transformation_ejecucion_presupuestal.py`
2. **Contratos SECOP**: `data_transformation_contratos_secop.py`
3. **Seguimiento PA**: `data_transformation_seguimiento_pa.py`
4. **Unidades de Proyecto**: `data_transformation_unidades_proyecto.py`

#### Flujo de Transformación

```bash
# 1. Colocar archivos Excel en directorio de entrada
transformation_app/app_inputs/[tipo_de_datos]_input/

# 2. Ejecutar script de transformación
python transformation_app/data_transformation_[tipo].py

# 3. Archivos JSON procesados se generan en:
transformation_app/app_outputs/[tipo_de_datos]_output/

# 4. Cargar datos a la base de datos via API
curl -X POST "http://localhost:8000/load_all_[tipo]"
```

#### Características de Transformación

- **Limpieza automática**: Eliminación de símbolos monetarios, espacios y caracteres especiales
- **Validación de tipos**: Conversión automática a tipos de datos correctos
- **Normalización**: Estandarización de formatos de fecha, números y texto
- **Detección inteligente**: Identificación automática de estructura de archivos
- **Preservación de datos**: Mantiene valores originales eliminando solo formato

## 🌐 API y Endpoints

### Documentación Interactiva

Una vez que el servidor esté ejecutándose, la documentación interactiva estará disponible en:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Categorías de Endpoints

#### 1. Gestión de Catálogos

- Centros gestores, programas, áreas funcionales, propósitos, retos
- Operaciones: GET, POST para consulta y carga de datos

#### 2. Datos Presupuestales

- Movimientos y ejecución presupuestal
- Operaciones: GET (con filtros), POST (carga individual), POST (carga masiva)

#### 3. Contratos SECOP

- Gestión completa de contratos y valores
- Operaciones: GET (con filtros avanzados), POST (carga masiva optimizada)

#### 4. Seguimiento de Proyectos

- Plan de Acción: resumen, productos, actividades
- Operaciones: GET (con filtros múltiples), POST (carga masiva)

#### 5. Infraestructura

- Equipamientos e infraestructura vial
- Operaciones: GET, POST, PUT, con soporte GeoJSON

#### 6. Administración

- Health checks, estadísticas, información de esquemas
- Operaciones administrativas y de mantenimiento

### Ejemplos de Uso

#### Consultar Contratos con Filtros

```bash
curl "http://localhost:8000/contratos?bpin=2024760010156&limit=10"
```

#### Carga Masiva de Datos

```bash
curl -X POST "http://localhost:8000/load_all_contratos"
```

#### Obtener Estadísticas del Sistema

```bash
curl "http://localhost:8000/database_status"
```

## 🚀 Despliegue en Producción

### Configuraciones Recomendadas

#### Desarrollo Local

```bash
uvicorn fastapi_project.main:app --reload --port 8000
```

#### Producción Básica

```bash
uvicorn fastapi_project.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Producción con Gunicorn (Recomendado)

```bash
pip install gunicorn
gunicorn fastapi_project.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log
```

### Scripts de Mantenimiento

#### Mantenimiento Preventivo

```bash
# Verificaciones básicas
python production_maintenance.py

# Con optimizaciones
python production_maintenance.py --optimize

# Con backup completo
python production_maintenance.py --backup --optimize
```

#### Monitoreo del Sistema

```bash
# Estado general del sistema
curl http://localhost:8000/health

# Estadísticas detalladas
curl http://localhost:8000/database_status

# Información de esquemas
curl http://localhost:8000/tables_info
```

## 📈 Rendimiento y Optimizaciones

### Capacidades del Sistema

- **Carga de datos**: Hasta 97,000 registros en menos de 35 segundos
- **Consultas**: Pool de conexiones optimizado para alta concurrencia
- **Transformación**: Procesamiento de archivos Excel con millones de registros
- **Almacenamiento**: Diseñado para manejar años de datos históricos

### Optimizaciones Implementadas

- **Índices de base de datos**: En campos críticos (BPIN, períodos, códigos)
- **Bulk operations**: Inserción y actualización masiva eficiente
- **Pool de conexiones**: Manejo optimizado de conexiones PostgreSQL
- **Validación en capas**: Pydantic + SQLAlchemy para integridad de datos
- **Arquitectura BPIN-centric**: Optimización específica para contratos SECOP

## 🔍 Monitoreo y Logs

### Sistema de Logging

- **Logs de aplicación**: Registro detallado de operaciones API
- **Logs de transformación**: Seguimiento de procesamiento de datos
- **Logs de mantenimiento**: Histórico de operaciones de sistema
- **Logs de base de datos**: Inicialización y migraciones

### Archivos de Log Principales

```
logs/
├── database_init.log              # Inicialización de BD
├── maintenance_YYYYMMDD.log       # Mantenimiento diario
├── deployment_YYYYMMDD_HHMMSS.log # Despliegues
└── transformation_app/
    └── transformation_*.log       # Transformación de datos
```

### Métricas Monitoreadas

- Tiempo de respuesta de endpoints
- Estado del pool de conexiones PostgreSQL
- Conteo de registros por tabla
- Espacio utilizado en base de datos
- Conexiones activas y tiempo de vida
- Performance de transformación de datos

## 🛡️ Seguridad y Buenas Prácticas

### Medidas de Seguridad

- **Variables de entorno**: Credenciales seguras fuera del código
- **Pool de conexiones**: Límites configurados para prevenir agotamiento
- **Validación de entrada**: Schemas Pydantic para todos los endpoints
- **Transacciones**: Rollback automático en caso de errores
- **Logging de seguridad**: Registro de operaciones críticas

### Recomendaciones de Producción

- Usar HTTPS en producción
- Configurar firewall para PostgreSQL
- Implementar backup automático de base de datos
- Monitorear logs regularmente
- Actualizar dependencias periódicamente

## 🐛 Solución de Problemas

### Problemas Comunes y Soluciones

#### Error de Conexión a PostgreSQL

```bash
# Verificar configuración
python database_initializer.py

# Verificar variables de entorno
cat .env

# Probar conexión directa
psql -h localhost -U api_user -d api_dashboard_cali
```

#### Datos Inconsistentes

```bash
# Verificar integridad del esquema
curl http://localhost:8000/tables_info

# Reinicializar si es necesario
python database_initializer.py

# Verificar tipos de datos
python production_maintenance.py --optimize
```

#### Problemas de Rendimiento

```bash
# Verificar estadísticas
curl http://localhost:8000/database_status

# Optimizar base de datos
python production_maintenance.py --optimize

# Verificar logs de consultas lentas
tail -f logs/maintenance_*.log
```

#### Errores en Transformación de Datos

```bash
# Verificar formato de archivos Excel
# Revisar estructura de directorios app_inputs/
# Consultar logs específicos de transformación
tail -f transformation_app/transformation_*.log
```

## 📞 Información de Soporte

### Recursos de Ayuda

1. **Documentación API**: `http://localhost:8000/docs`
2. **Logs del sistema**: Directorio `logs/`
3. **Health checks**: `http://localhost:8000/health`
4. **Estado de BD**: `http://localhost:8000/database_status`

### Archivos de Configuración Importantes

- `.env`: Variables de entorno
- `requirements.txt`: Dependencias Python
- `database_initializer.py`: Configuración de esquema
- `production_deployment.py`: Script de despliegue

---

**Desarrollado para la Alcaldía de Santiago de Cali**  
**Sistema integral de gestión de datos gubernamentales**
