# 🚀 Guía de Despliegue Completa - API Dashboard Alcaldía de Cali v2.7.0

## 📋 Índice

1. [🎯 Preparación del Entorno](#-preparación-del-entorno)
2. [🗄️ Configuración de Base de Datos](#-configuración-de-base-de-datos)
3. [⚙️ Instalación del Sistema](#-instalación-del-sistema)
4. [🔧 Database Initializer - Paso a Paso](#-database-initializer---paso-a-paso)
5. [🌐 Despliegue en Railway](#-despliegue-en-railway)
6. [✅ Verificación y Pruebas](#-verificación-y-pruebas)
7. [🛠️ Mantenimiento](#-mantenimiento)

---

## 🎯 Preparación del Entorno

### Requisitos del Sistema

| Componente         | Versión Mínima         | Recomendada |
| ------------------ | ---------------------- | ----------- |
| **Python**         | 3.8+                   | 3.11+       |
| **PostgreSQL**     | 12+                    | 15+         |
| **RAM**            | 2GB                    | 4GB+        |
| **Almacenamiento** | 10GB                   | 20GB+       |
| **SO**             | Windows 10/Linux/macOS | Cualquiera  |

### Herramientas Necesarias

```bash
# Git para clonar repositorio
git --version

# Python y pip
python --version
pip --version

# PostgreSQL cliente
psql --version

# Opcional: Railway CLI para despliegue
railway --version
```

---

## 🗄️ Configuración de Base de Datos

### Paso 1: Instalar PostgreSQL

#### En Windows:

1. Descargar desde [postgresql.org](https://www.postgresql.org/download/windows/)
2. Ejecutar instalador
3. **Recordar contraseña de superusuario**
4. Verificar servicio iniciado

#### En Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### En macOS:

```bash
brew install postgresql
brew services start postgresql
```

### Paso 2: Crear Base de Datos y Usuario

```sql
-- Conectar como superusuario
sudo -u postgres psql  # Linux
psql -U postgres      # Windows

-- Crear base de datos
CREATE DATABASE api_dashboard_cali;

-- Crear usuario específico
CREATE USER api_user WITH PASSWORD 'contraseña_muy_segura_2025';

-- Otorgar permisos completos
GRANT ALL PRIVILEGES ON DATABASE api_dashboard_cali TO api_user;

-- Otorgar permisos en schema público
\c api_dashboard_cali
GRANT ALL ON SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO api_user;

-- Verificar conexión
\q
psql -h localhost -U api_user -d api_dashboard_cali
```

### Paso 3: Configurar Variables de Entorno

Crear archivo `.env` en el directorio raíz del proyecto:

```env
# === CONFIGURACIÓN POSTGRESQL LOCAL ===
POSTGRES_USER=api_user
POSTGRES_PASSWORD=contraseña_muy_segura_2025
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=api_dashboard_cali

# === CONFIGURACIÓN RAILWAY (OPCIONAL) ===
# Solo se usa si existe DATABASE_URL
# DATABASE_URL=postgresql://usuario:pass@host:puerto/database

# === CONFIGURACIÓN API (OPCIONAL) ===
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=True

# === CONFIGURACIÓN DE POOL DE CONEXIONES ===
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

---

## ⚙️ Instalación del Sistema

### Paso 1: Clonar y Preparar Repositorio

```bash
# Clonar repositorio
git clone <repository-url>
cd api-dashboard-db

# Verificar estructura del proyecto
ls -la
# Debe mostrar: fastapi_project/, transformation_app/, docs/, database_initializer.py, etc.
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv env

# Activar entorno virtual
# Windows:
env\Scripts\activate

# Linux/macOS:
source env/bin/activate

# Verificar activación (debe mostrar (env) al inicio del prompt)
which python  # Linux/macOS
where python   # Windows
```

### Paso 3: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación crítica
pip list | grep -E "(fastapi|sqlalchemy|psycopg2|pandas)"
```

### Paso 4: Verificar Configuración

```bash
# Verificar archivo .env
cat .env  # Linux/macOS
type .env # Windows

# Probar conexión a PostgreSQL
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('PostgreSQL Config:')
print(f'User: {os.getenv(\"POSTGRES_USER\")}')
print(f'Host: {os.getenv(\"POSTGRES_SERVER\")}')
print(f'Port: {os.getenv(\"POSTGRES_PORT\")}')
print(f'Database: {os.getenv(\"POSTGRES_DB\")}')
"
```

---

## 🔧 Database Initializer - Paso a Paso

### ¿Por Qué es Crítico el Database Initializer?

El `database_initializer.py` es **EL COMPONENTE MÁS IMPORTANTE** del sistema porque:

- ✅ **Crea la estructura completa** de 25 tablas
- ✅ **Genera 26 índices** de rendimiento automáticamente
- ✅ **Carga datos incrementalmente** (solo archivos nuevos)
- ✅ **Filtra datos inválidos** automáticamente
- ✅ **Funciona en local y Railway** sin cambios
- ✅ **Genera reportes detallados** de cada operación

### Paso 1: Preparar Archivos JSON (Si No Existen)

```bash
# Verificar existencia de archivos JSON
ls -la transformation_app/app_outputs/*/

# Si no existen, ejecutar transformaciones:
python transformation_app/data_transformation_ejecucion_presupuestal.py
python transformation_app/data_transformation_contratos_secop.py
python transformation_app/data_transformation_seguimiento_pa.py
python transformation_app/data_transformation_unidades_proyecto.py
```

### Paso 2: Ejecutar Database Initializer

```bash
# COMANDO PRINCIPAL - Ejecutar inicializador
python database_initializer.py
```

### Paso 3: Monitorear Ejecución en Tiempo Real

La ejecución mostrará estas fases:

#### **FASE 1: Detección de Entorno (5-10 seg)**

```
🏛️ API Dashboard Alcaldía de Cali - Inicializador Unificado
🔧 Estructura + Datos para entornos Locales y Railway
======================================================================
INFO:__main__:🌍 Entorno detectado: Local (Desarrollo)
INFO:__main__:🚀 Iniciando inicialización completa de la base de datos
```

✅ **Verificar**: Debe mostrar "Local (Desarrollo)" o "Railway (Producción)"

#### **FASE 2: Conexión a Base de Datos (2-5 seg)**

```
INFO:fastapi_project.database:✅ Primera conexión a PostgreSQL establecida
INFO:__main__:✅ Conexión a la base de datos exitosa
```

❌ **Si falla**: Verificar `.env` y estado de PostgreSQL

#### **FASE 3: Creación de Estructura (10-20 seg)**

```
INFO:__main__:🔧 Creando estructura de tablas desde modelos SQLAlchemy...
INFO:__main__:✅ Todas las tablas creadas/verificadas desde modelos SQLAlchemy
INFO:__main__:📊 Tablas disponibles (25):
   • areas_funcionales
   • barrios
   • centros_gestores
   [... lista completa de 25 tablas ...]
```

✅ **Verificar**: Debe mostrar exactamente 25 tablas

#### **FASE 4: Creación de Índices (20-30 seg)**

```
INFO:__main__:🔧 Creando índices de rendimiento...
Creando índice: 100%|████████████████| 26/26 [00:02<00:00, 12.93índices/s]
INFO:__main__:✅ Procesamiento de índices completado (26 índices)
```

✅ **Verificar**: Debe crear exactamente 26 índices

#### **FASE 5: Carga de Datos (1-5 min)**

```
INFO:__main__:📦 FASE DE CARGA DE DATOS
INFO:__main__:📋 Encontrados 10 archivos para procesar

# Para archivos ya existentes:
INFO:__main__:⏭️ contratos: Ya tiene 744 registros, se omite

# Para archivos nuevos:
INFO:__main__:📥 datos_caracteristicos_proyectos: Tabla vacía, se cargará
INFO:__main__:📥 Cargando datos_caracteristicos_proyectos.json (1.28 MB)
WARNING:__main__:⚠️ datos_caracteristicos_proyectos: 1 registros rechazados por BPIN NULL/inválido
Insertando en datos_caracteristicos_proyectos: 100%|████████| 1252/1252 [01:27<00:00, 14.29registros/s]
INFO:__main__:✅ datos_caracteristicos_proyectos: 1,252 registros cargados exitosamente
```

⚠️ **Normal**: Registros rechazados por BPIN NULL es comportamiento esperado

#### **FASE 6: Resumen Final**

```
================================================================================
🎉 RESUMEN DE INICIALIZACIÓN COMPLETADA
================================================================================
⏱️ Duración total: 115.73 segundos
🌍 Entorno: Local (Desarrollo)
📁 Archivos procesados: 2
📊 Total registros cargados: 1,489

✅ Base de datos completamente configurada y lista para producción
🚀 Puedes iniciar tu API con: uvicorn fastapi_project.main:app --reload
```

✅ **Éxito Confirmado**: Debe mostrar este mensaje final

### Paso 4: Verificar Archivos Generados

```bash
# Verificar reporte generado
ls -la database_initialization_report_*.md

# Ver contenido del reporte
cat database_initialization_report_$(date +%Y%m%d)_*.md
```

### Paso 5: Manejo de Errores Comunes

#### Error: "No se puede conectar a PostgreSQL"

```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql  # Linux
# o verificar servicios en Windows

# Probar conexión manual
psql -h localhost -U api_user -d api_dashboard_cali

# Verificar variables de entorno
echo $POSTGRES_USER
echo $POSTGRES_PASSWORD
```

#### Error: "Archivos JSON no encontrados"

```bash
# Verificar estructura de directorios
find transformation_app/app_outputs/ -name "*.json" -type f

# Si están vacíos, ejecutar transformaciones
python transformation_app/data_transformation_ejecucion_presupuestal.py
# ... resto de transformaciones
```

#### Error: "Permisos insuficientes"

```sql
-- Conectar como superusuario y otorgar permisos
psql -U postgres -d api_dashboard_cali

GRANT ALL PRIVILEGES ON DATABASE api_dashboard_cali TO api_user;
GRANT ALL ON SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO api_user;
```

---

## 🌐 Despliegue en Railway

### Paso 1: Preparar Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login a Railway
railway login

# Verificar autenticación
railway whoami
```

### Paso 2: Crear Proyecto en Railway

```bash
# Crear nuevo proyecto
railway init

# O conectar a proyecto existente
railway link [PROJECT_ID]

# Verificar configuración
railway status
```

### Paso 3: Configurar Variables de Entorno en Railway

```bash
# Verificar variables actuales
railway variables

# Agregar variables necesarias (si no están)
railway variables set PYTHON_VERSION=3.11
railway variables set PORT=8000

# La variable DATABASE_URL se crea automáticamente por Railway
```

### Paso 4: Ejecutar Database Initializer en Railway

```bash
# El comando más importante - ejecutar inicializador en Railway
railway run python database_initializer.py
```

#### Salida Esperada en Railway:

```
🏛️ API Dashboard Alcaldía de Cali - Inicializador Unificado
🔧 Estructura + Datos para entornos Locales y Railway
======================================================================
INFO:__main__:🌍 Entorno detectado: Railway (Producción)
INFO:__main__:🚀 Iniciando inicialización completa de la base de datos
[... resto del proceso similar al local ...]
✅ Base de datos completamente configurada y lista para producción
```

✅ **Verificar**: Debe mostrar "Railway (Producción)"

### Paso 5: Desplegar API en Railway

```bash
# Desplegar aplicación
railway up

# Verificar despliegue
railway status

# Ver logs en tiempo real
railway logs

# Obtener URL de la aplicación
railway domain
```

### Paso 6: Verificar en Railway

```bash
# Obtener URL del proyecto
railway domain

# Probar health check
curl https://tu-proyecto.railway.app/health

# Probar documentación
# Abrir en navegador: https://tu-proyecto.railway.app/docs
```

---

## ✅ Verificación y Pruebas

### Paso 1: Iniciar API Local

```bash
# Iniciar servidor de desarrollo
uvicorn fastapi_project.main:app --reload

# Verificar inicio exitoso (debe mostrar):
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

### Paso 2: Verificar Health Checks

```bash
# Health check básico
curl http://localhost:8000/health

# Respuesta esperada:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-08-14T02:00:00.000Z"
}

# Estado detallado de base de datos
curl http://localhost:8000/database_status

# Debe mostrar conteos de todas las tablas
```

### Paso 3: Probar Endpoints Principales

```bash
# Datos característicos de proyectos
curl "http://localhost:8000/datos_caracteristicos_proyectos?limit=3"

# Movimientos presupuestales
curl "http://localhost:8000/movimientos_presupuestales?limit=3"

# Contratos
curl "http://localhost:8000/contratos?limit=3"

# Seguimiento PA
curl "http://localhost:8000/seguimiento_pa?limit=3"
```

### Paso 4: Verificar Documentación API

1. Abrir navegador en: `http://localhost:8000/docs`
2. Verificar que aparezcan todos los endpoints
3. Probar algunos endpoints desde la interfaz Swagger
4. Verificar que los datos se devuelven correctamente

### Paso 5: Verificar Base de Datos Directamente

```sql
-- Conectar a base de datos
psql -h localhost -U api_user -d api_dashboard_cali

-- Verificar tablas creadas
\dt

-- Verificar conteos
SELECT
    schemaname,
    tablename,
    n_tup_ins as "Registros"
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_tup_ins DESC;

-- Verificar algunos datos
SELECT bpin, nombre_proyecto FROM datos_caracteristicos_proyectos LIMIT 5;
SELECT bpin, periodo_corte, ppto_inicial FROM movimientos_presupuestales LIMIT 5;
```

---

## 🛠️ Mantenimiento

### Actualización de Datos

```bash
# Para cargar nuevos datos (incremental)
python database_initializer.py

# Solo carga archivos nuevos o tablas vacías
# Omite automáticamente datos existentes
```

### Monitoreo Regular

```bash
# Verificar estado de la API
curl http://localhost:8000/health

# Verificar estadísticas de base de datos
curl http://localhost:8000/database_status

# Ver logs de aplicación
tail -f logs/api.log  # Si configurado
```

### Backup de Base de Datos

```bash
# Crear backup completo
pg_dump -h localhost -U api_user -d api_dashboard_cali > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar desde backup
psql -h localhost -U api_user -d api_dashboard_cali < backup_20250814_120000.sql
```

### Optimización Periódica

```bash
# Ejecutar mantenimiento de PostgreSQL
psql -h localhost -U api_user -d api_dashboard_cali -c "VACUUM ANALYZE;"

# Verificar índices
psql -h localhost -U api_user -d api_dashboard_cali -c "
SELECT
    tablename,
    indexname,
    idx_scan as \"Usos del Índice\"
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
"
```

---

## 🎯 Checklist Final de Despliegue

### ✅ Antes de Considerar Completo

- [ ] PostgreSQL funcionando correctamente
- [ ] Variables de entorno configuradas (`.env`)
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] `database_initializer.py` ejecutado exitosamente
- [ ] Reporte generado (`database_initialization_report_*.md`)
- [ ] API inicia sin errores (`uvicorn fastapi_project.main:app --reload`)
- [ ] Health check responde OK (`curl http://localhost:8000/health`)
- [ ] Documentación accesible (`http://localhost:8000/docs`)
- [ ] Endpoints principales funcionando
- [ ] Al menos 8-10 tablas con datos cargados

### ✅ Para Railway (Adicional)

- [ ] Railway CLI instalado y autenticado
- [ ] Proyecto creado/conectado en Railway
- [ ] `database_initializer.py` ejecutado en Railway
- [ ] API desplegada (`railway up`)
- [ ] Dominio asignado y accesible
- [ ] Health check remoto funcionando

---

## 🚀 Comandos de Referencia Rápida

### Despliegue Local Completo

```bash
git clone <repo>
cd api-dashboard-db
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
# Configurar .env
python database_initializer.py
uvicorn fastapi_project.main:app --reload
```

### Despliegue Railway Completo

```bash
# Después del despliegue local exitoso
railway login
railway init
railway run python database_initializer.py
railway up
railway domain
```

### Verificación Post-Despliegue

```bash
curl http://localhost:8000/health
curl http://localhost:8000/database_status
curl "http://localhost:8000/datos_caracteristicos_proyectos?limit=3"
```

---

**🎉 ¡Sistema completamente desplegado y funcional!**

**API Dashboard Alcaldía de Santiago de Cali v2.7.0**  
**Database Initializer Unificado - Local y Railway Ready**
