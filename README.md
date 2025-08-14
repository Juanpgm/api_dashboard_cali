# 🏛️ API Dashboard Alcaldía de Santiago de Cali - v2.6.0

Sistema integral de gestión de datos presupuestales, proyectos y contratos para la Alcaldía de Santiago de Cali. Proporciona una API robusta y eficiente para el manejo de información gubernamental con capacidades avanzadas de transformación y análisis de datos.

## 🎯 Novedades Versión 2.6.0

### ✅ Optimización Completa de la API

- **Modelos y Esquemas Alineados**: Consistencia perfecta entre SQLAlchemy models, Pydantic schemas y estructura PostgreSQL
- **Campos Nullable Corregidos**: Todos los campos críticos con `nullable=False` para garantizar integridad
- **Nombres Unificados**: `periodo_corte` consistente en todas las tablas y endpoints
- **Endpoints Verificados**: Funcionamiento 100% comprobado de todos los endpoints principales
- **Contratos Optimizados**: JOIN simplificado con `contratos_valores` para mejor rendimiento

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

### Stack Tecnológico - Actualizado v2.6.0

- **Backend**: FastAPI (Python 3.8+) con schemas Pydantic optimizados
- **Base de Datos**: PostgreSQL 12+ con modelos SQLAlchemy alineados
- **ORM**: SQLAlchemy con configuración nullable corregida
- **Validación**: Pydantic con from_attributes=True para serialización ORM
- **Documentación**: Swagger UI automático con endpoints reorganizados
- **Procesamiento**: Pandas, OpenPyXL para archivos Excel

## 🛠️ Configuración e Instalación

### Requisitos del Sistema

- **Python**: 3.8 o superior
- **PostgreSQL**: 12 o superior
- **RAM**: Mínimo 2GB, recomendado 4GB
- **Almacenamiento**: Mínimo 10GB para datos y logs
- **Herramientas**: Git, Microsoft Excel o LibreOffice para archivos .xlsx

### 🗄️ Configuración de Base de Datos

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

# Para despliegue en Railway (opcional)
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/database

# Configuración API (opcional)
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
```

### 🚀 Instalación del Sistema

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

# 6. ¡PASO CRÍTICO! Inicializar base de datos
python database_initializer.py

# 7. Ejecutar servidor
uvicorn fastapi_project.main:app --reload
```

## 🏗️ Database Initializer - Guía Completa Paso a Paso

### 📖 ¿Qué es el Database Initializer?

El `database_initializer.py` es el corazón del sistema de inicialización de la base de datos. Este script inteligente:

- ✅ **Detecta automáticamente** si está en entorno local o Railway
- ✅ **Crea la estructura completa** de base de datos usando SQLAlchemy models
- ✅ **Carga datos incrementalmente** (solo datos nuevos)
- ✅ **Maneja errores automáticamente** y filtra datos inválidos
- ✅ **Genera reportes detallados** de métricas y estado
- ✅ **Usa UPSERT inteligente** para evitar duplicados
- ✅ **Optimiza rendimiento** con índices automáticos

### 🎯 Cuándo Usar el Database Initializer

#### ✅ **OBLIGATORIO usar en estos casos:**

- Primera instalación del sistema
- Después de clonar el repositorio
- Cuando agregues nuevos archivos JSON de datos
- Para migrar datos a Railway o nueva base de datos
- Después de cambios en models.py o schemas.py
- Para reparar base de datos corrupta o incompleta

#### ⚠️ **OPCIONAL usar en estos casos:**

- Para cargar datos actualizados (es incremental)
- Como verificación de integridad periódica
- Para optimizar índices de base de datos

### 📋 Preparación Antes de Ejecutar

#### Paso 1: Verificar Estructura de Archivos

Asegúrate de tener esta estructura de directorios:

```
transformation_app/
├── app_outputs/
│   ├── contratos_secop_output/
│   │   ├── contratos.json
│   │   └── contratos_valores.json
│   ├── ejecucion_presupuestal_outputs/
│   │   ├── movimientos_presupuestales.json
│   │   ├── ejecucion_presupuestal.json
│   │   └── datos_caracteristicos_proyectos.json
│   ├── seguimiento_pa_outputs/
│   │   ├── seguimiento_pa.json
│   │   ├── seguimiento_productos_pa.json
│   │   └── seguimiento_actividades_pa.json
│   └── unidades_proyecto_outputs/
│       ├── unidad_proyecto_infraestructura_equipamientos.json
│       └── unidad_proyecto_infraestructura_vial.json
```

#### Paso 2: Verificar Conexión a Base de Datos

```bash
# Probar conexión directa
psql -h localhost -U api_user -d api_dashboard_cali

# O verificar variables de entorno
cat .env
```

#### Paso 3: Activar Entorno Virtual

```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

### 🚀 Ejecutando el Database Initializer

#### Ejecución Básica (Recomendada)

```bash
cd a:\programing_workspace\api-dashboard-db
python database_initializer.py
```

#### ¿Qué Hace Durante la Ejecución?

**FASE 1: Detección de Entorno (5-10 segundos)**

```
🏛️ API Dashboard Alcaldía de Cali - Inicializador Unificado
🔧 Estructura + Datos para entornos Locales y Railway
======================================================================
INFO:__main__:🌍 Entorno detectado: Local (Desarrollo)  # O Railway
INFO:__main__:🚀 Iniciando inicialización completa de la base de datos
```

**FASE 2: Verificación de Conexión (2-5 segundos)**

```
INFO:fastapi_project.database:✅ Primera conexión a PostgreSQL establecida
INFO:__main__:✅ Conexión a la base de datos exitosa
```

**FASE 3: Creación/Verificación de Estructura (10-20 segundos)**

```
INFO:__main__:🔧 Creando estructura de tablas desde modelos SQLAlchemy...
INFO:__main__:✅ Todas las tablas creadas/verificadas desde modelos SQLAlchemy
INFO:__main__:📊 Tablas disponibles (25):
   • areas_funcionales
   • barrios
   • centros_gestores
   [... lista completa de 25 tablas ...]
```

**FASE 4: Creación de Índices de Rendimiento (20-30 segundos)**

```
INFO:__main__:🔧 Creando índices de rendimiento...
Creando índice: 100%|████████████████| 26/26 [00:02<00:00, 12.93índices/s]
INFO:__main__:✅ Procesamiento de índices completado (26 índices)
```

**FASE 5: Carga de Datos (1-5 minutos dependiendo del tamaño)**

```
INFO:__main__:📦 FASE DE CARGA DE DATOS
INFO:__main__:📋 Encontrados 10 archivos para procesar

# Para archivos ya cargados:
INFO:__main__:⏭️ contratos: Ya tiene 744 registros, se omite

# Para archivos nuevos:
INFO:__main__:📥 datos_caracteristicos_proyectos: Tabla vacía, se cargará
INFO:__main__:📥 Cargando datos_caracteristicos_proyectos.json (1.28 MB)
INFO:__main__:📊 Procesando 1,253 registros para tabla 'datos_caracteristicos_proyectos'
WARNING:__main__:⚠️ datos_caracteristicos_proyectos: 1 registros rechazados por BPIN NULL/inválido
Insertando en datos_caracteristicos_proyectos: 100%|████████| 1252/1252 [01:27<00:00, 14.29registros/s]
INFO:__main__:✅ datos_caracteristicos_proyectos: 1,252 registros cargados exitosamente
```

**FASE 6: Resumen Final y Reporte**

```
================================================================================
🎉 RESUMEN DE INICIALIZACIÓN COMPLETADA
================================================================================
⏱️ Duración total: 115.73 segundos
🌍 Entorno: Local (Desarrollo)
📁 Archivos procesados: 2
📊 Total registros cargados: 1,489

📋 Tablas con datos cargados (2):
   • datos_caracteristicos_proyectos: 1,252 registros
   • unidades_proyecto_infraestructura_equipamientos: 237 registros

⏭️ Tablas omitidas (8):
   • contratos: 744 registros existentes
   [... lista de tablas ya cargadas ...]

INFO:__main__:📄 Reporte completo disponible en: database_initialization_report_20250814_021348.md
✅ Base de datos completamente configurada y lista para producción
🚀 Puedes iniciar tu API con: uvicorn fastapi_project.main:app --reload
```

### 📊 Interpretando los Resultados

#### ✅ **Indicadores de Éxito**

- **"✅ Conexión a la base de datos exitosa"**: La conexión PostgreSQL funciona
- **"✅ Todas las tablas creadas/verificadas"**: Estructura de BD correcta
- **"✅ X registros cargados exitosamente"**: Datos insertados sin errores
- **"⏭️ tabla: Ya tiene X registros, se omite"**: Comportamiento incremental correcto
- **"🚀 Base de datos lista para el API"**: Sistema completamente funcional

#### ⚠️ **Advertencias Normales (No son errores)**

- **"⚠️ X registros rechazados por BPIN NULL/inválido"**: Limpieza automática de datos
- **"⏭️ tabla: Ya tiene X registros, se omite"**: Carga incremental trabajando

#### ❌ **Indicadores de Error**

- **"❌ Error de conexión a la base de datos"**: Verificar .env y PostgreSQL
- **"❌ Error creando tablas"**: Problemas con models.py o permisos de BD
- **"❌ tabla: No se pudo cargar ningún registro"**: Archivos JSON corruptos o formato incorrecto

### 🔧 Opciones Avanzadas de Ejecución

#### Para Desarrollo (Recomendada)

```bash
python database_initializer.py
```

#### Para Railway (Automático)

```bash
railway run python database_initializer.py
```

#### Con Variables de Entorno Específicas

```bash
# Para forzar entorno específico
ENVIRONMENT=Railway python database_initializer.py

# Con base de datos específica
DATABASE_URL="postgresql://user:pass@host:port/db" python database_initializer.py
```

### 🛠️ Solución de Problemas del Database Initializer

#### Error: "No se puede conectar a PostgreSQL"

**Síntomas:**

```
❌ Error de conexión a la base de datos: connection to server at "localhost" failed
```

**Soluciones:**

```bash
# 1. Verificar que PostgreSQL esté ejecutándose
sudo service postgresql status  # Linux
# o
pg_ctl status  # Windows

# 2. Verificar variables de entorno
cat .env

# 3. Probar conexión manual
psql -h localhost -U api_user -d api_dashboard_cali

# 4. Verificar firewall y puertos
telnet localhost 5432
```

#### Error: "Archivos JSON no encontrados"

**Síntomas:**

```
📂 Archivo JSON no encontrado: transformation_app/app_outputs/.../archivo.json
```

**Soluciones:**

```bash
# 1. Verificar estructura de directorios
ls -la transformation_app/app_outputs/

# 2. Ejecutar transformaciones para generar archivos
python transformation_app/data_transformation_ejecucion_presupuestal.py
python transformation_app/data_transformation_contratos_secop.py
python transformation_app/data_transformation_seguimiento_pa.py
python transformation_app/data_transformation_unidades_proyecto.py

# 3. Verificar permisos de archivos
chmod 644 transformation_app/app_outputs/*/*.json
```

#### Error: "Registros rechazados por BPIN NULL"

**Síntomas:**

```
⚠️ unidades_proyecto_infraestructura_equipamientos: 88 registros rechazados por BPIN NULL/inválido
```

**Explicación:**
Esto es NORMAL. El sistema automáticamente filtra registros con BPIN nulo porque violan las restricciones de integridad de la base de datos. Los registros válidos se cargan correctamente.

#### Error: "Error creando índices"

**Síntomas:**

```
⚠️ Error creando índice idx_movimientos_bpin: relation "tabla" does not exist
```

**Soluciones:**

```bash
# 1. Reinicializar con borrado de tablas
psql -d api_dashboard_cali -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python database_initializer.py

# 2. Verificar permisos de usuario
GRANT ALL PRIVILEGES ON DATABASE api_dashboard_cali TO api_user;
GRANT ALL ON SCHEMA public TO api_user;
```

### 📈 Optimización y Mejores Prácticas

#### Para Mejor Rendimiento

1. **Ejecutar con SSD**: El inicializador es intensivo en I/O
2. **Cerrar aplicaciones pesadas**: Liberar RAM durante la carga
3. **Usar PostgreSQL local**: Evitar conexiones de red lentas para desarrollo

#### Para Entornos de Producción

```bash
# 1. Configurar pool de conexiones más grande
# En .env:
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# 2. Ejecutar durante horas de menor tráfico
python database_initializer.py

# 3. Verificar logs posteriores
tail -f database_initialization_report_*.md
```

#### Para Actualizar Datos Regularmente

```bash
# El inicializador es seguro de ejecutar repetidamente
# Solo carga datos nuevos (incremental)
python database_initializer.py

# Para forzar recarga completa (solo si es necesario)
# 1. Truncar tablas específicas en PostgreSQL
# 2. Ejecutar inicializador
```

### 📄 Reportes Generados

Cada ejecución genera un reporte detallado:

```
database_initialization_report_YYYYMMDD_HHMMSS.md
```

**Contenido del reporte:**

- Duración total de la operación
- Entorno detectado (Local/Railway)
- Lista detallada de tablas creadas
- Estadísticas de registros por tabla
- Archivos procesados y omitidos
- Métricas de rendimiento
- Errores y advertencias encontrados

### 🎯 Verificación Post-Inicialización

#### 1. Verificar Estado de la Base de Datos

```bash
# Iniciar la API
uvicorn fastapi_project.main:app --reload

# En otra terminal, verificar salud
curl http://localhost:8000/health

# Verificar estadísticas
curl http://localhost:8000/database_status
```

#### 2. Probar Endpoints Principales

```bash
# Datos caracteristicos de proyectos
curl "http://localhost:8000/datos_caracteristicos_proyectos?limit=5"

# Movimientos presupuestales
curl "http://localhost:8000/movimientos_presupuestales?limit=5"

# Contratos
curl "http://localhost:8000/contratos?limit=5"
```

#### 3. Verificar Documentación API

Abrir en navegador: `http://localhost:8000/docs`

---

### ✅ Checklist de Verificación Final

Después de ejecutar el `database_initializer.py`, verificar:

- [ ] ✅ El script terminó con mensaje "🚀 Base de datos lista para el API"
- [ ] ✅ Se generó archivo de reporte `database_initialization_report_*.md`
- [ ] ✅ La API inicia sin errores: `uvicorn fastapi_project.main:app --reload`
- [ ] ✅ Health check responde OK: `curl http://localhost:8000/health`
- [ ] ✅ Documentación accesible: `http://localhost:8000/docs`
- [ ] ✅ Al menos 8-10 tablas tienen datos cargados
- [ ] ✅ No hay errores críticos en los logs

**¡Tu sistema está listo para producción! 🎉**

## 📚 Documentación Detallada

### Guías Específicas

- **[🗄️ Database Initializer - Guía Completa](docs/database_initializer_guide.md)**: Manual detallado del sistema de inicialización
- **[🚀 Guía de Despliegue Completa](docs/deployment_guide.md)**: Instrucciones paso a paso para local y Railway
- **[📊 Arquitectura del Sistema](docs/overview.md)**: Visión general y componentes principales
- **[🌐 Endpoints de la API](docs/endpoints.md)**: Lista completa de endpoints disponibles
- **[📋 Registro de Cambios](docs/changelog.md)**: Historial detallado de versiones y mejoras

### Documentación por Módulos

- **[⚙️ Modelos y Esquemas](docs/models_and_schemas.md)**: Estructura de datos y validaciones
- **[🔧 Mantenimiento](docs/maintenance.md)**: Procedimientos de mantenimiento y optimización
- **[🏗️ Schema de Base de Datos](docs/database_schema.md)**: Estructura detallada de tablas

### Sistema de Transformación

- **[📊 Ejecución Presupuestal](docs/ejecucion_presupuestal_system.md)**: Procesamiento de datos presupuestales
- **[📝 Contratos SECOP](docs/contratos_secop_system.md)**: Sistema de contratos optimizado
- **[📈 Seguimiento PA](docs/seguimiento_pa_system.md)**: Sistema de seguimiento al Plan de Acción

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

### Tipos de Datos Estandarizados - v2.6.0

- **BPIN**: `BIGINT` - Códigos de proyectos de inversión
- **Períodos**: `VARCHAR(50)` para movimientos/ejecución, `VARCHAR(7)` para seguimiento - Formato YYYY-MM
- **Valores monetarios**: `DECIMAL(15,2)` - Presupuestos y pagos
- **Porcentajes**: `DECIMAL(5,2)` - Avances y porcentajes de ejecución
- **Fechas**: `DATE` - Formato ISO (YYYY-MM-DD)
- **Textos**: `TEXT` - Nombres y descripciones sin límite
- **Campos críticos**: `nullable=False` para garantizar integridad de datos

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

### Categorías de Endpoints - Actualizadas v2.6.0

#### 1. Gestión de Catálogos

- Centros gestores, programas, áreas funcionales, propósitos, retos
- Operaciones: GET, POST para consulta y carga de datos

#### 2. Datos Presupuestales (✅ Optimizados v2.6.0)

- Movimientos y ejecución presupuestal con filtros corregidos
- Operaciones: GET (con `periodo_corte`), POST (carga individual), POST (carga masiva)
- **Mejora**: Campos y filtros unificados para consistencia total

#### 3. Contratos SECOP (✅ Arquitectura BPIN-Centric v2.6.0)

- Gestión completa de contratos y valores con JOIN optimizado
- Operaciones: GET (con filtros avanzados), POST (carga masiva optimizada)
- **Mejora**: Response unificado `ContratoCompleto` con valores incluidos

#### 4. Seguimiento de Proyectos

- Plan de Acción: resumen, productos, actividades
- Operaciones: GET (con filtros múltiples), POST (carga masiva)

#### 5. Infraestructura

- Equipamientos e infraestructura vial
- Operaciones: GET, POST, PUT, con soporte GeoJSON

#### 6. Administración (✅ Reorganizados v2.6.0)

- Health checks, estadísticas, información de esquemas
- Operaciones administrativas y de mantenimiento
- **Mejora**: Aparecen al final en Swagger UI para mejor organización

### Ejemplos de Uso - Actualizados v2.6.0

#### Consultar Movimientos Presupuestales con Filtros Corregidos

```bash
curl "http://localhost:8000/movimientos_presupuestales?periodo_corte=2024-01&limit=10"
```

#### Consultar Contratos con JOIN Optimizado

```bash
curl "http://localhost:8000/contratos?bpin=2024760010156&limit=10"
```

#### Carga Masiva de Contratos (Recomendado)

```bash
curl -X POST "http://localhost:8000/load_all_contratos"
```

#### Obtener Estadísticas del Sistema

```bash
curl "http://localhost:8000/database_status"
```

#### Verificar Estado de la API

```bash
curl "http://localhost:8000/health"
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

### Capacidades del Sistema - v2.6.0

- **Carga de datos**: Hasta 97,000 registros en menos de 35 segundos
- **Consultas**: Pool de conexiones optimizado para alta concurrencia
- **Transformación**: Procesamiento de archivos Excel con millones de registros
- **Almacenamiento**: Diseñado para manejar años de datos históricos
- **Integridad**: Validación completa entre models, schemas y base de datos
- **Consistencia**: Nombres de campos unificados en toda la aplicación

### Optimizaciones Implementadas - v2.6.0

- **Índices de base de datos**: En campos críticos (BPIN, períodos, códigos)
- **Bulk operations**: Inserción y actualización masiva eficiente
- **Pool de conexiones**: Manejo optimizado de conexiones PostgreSQL
- **Validación en capas**: Pydantic + SQLAlchemy alineados para integridad de datos
- **Arquitectura BPIN-centric**: Optimización específica para contratos SECOP
- **Schemas optimizados**: from_attributes=True para mejor serialización ORM
- **JOIN simplificados**: Eliminación de JOINs problemáticos para mejor rendimiento

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

#### Datos Inconsistentes - v2.6.0

```bash
# Verificar integridad del esquema y alineación models/schemas
curl http://localhost:8000/tables_info

# Reinicializar si es necesario (ahora con validación completa)
python database_initializer.py

# Verificar tipos de datos y campos nullable
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
**Sistema integral de gestión de datos gubernamentales v2.6.0**  
**Optimizado con modelos, esquemas y API completamente alineados**
