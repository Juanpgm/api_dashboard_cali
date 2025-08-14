# 📚 Índice de Documentación - API Dashboard Alcaldía de Cali v2.7.0

## 📖 Documentación Principal

### 🚀 Guías de Inicio

| Documento                                                                    | Descripción                         | Cuándo Usar                 |
| ---------------------------------------------------------------------------- | ----------------------------------- | --------------------------- |
| **[README.md](../README.md)**                                                | Guía principal del proyecto         | Primera lectura obligatoria |
| **[🚀 Guía de Despliegue Completa](deployment_guide.md)**                    | Instrucciones paso a paso completas | Primera instalación         |
| **[🗄️ Database Initializer - Guía Completa](database_initializer_guide.md)** | Manual detallado del inicializador  | Problemas con BD o datos    |

### 📊 Arquitectura y Componentes

| Documento                                            | Descripción                        | Audiencia                    |
| ---------------------------------------------------- | ---------------------------------- | ---------------------------- |
| **[📊 Arquitectura del Sistema](overview.md)**       | Visión general y componentes       | Desarrolladores, arquitectos |
| **[🌐 Endpoints de la API](endpoints.md)**           | Lista completa de endpoints        | Desarrolladores frontend, QA |
| **[⚙️ Modelos y Esquemas](models_and_schemas.md)**   | Estructura de datos y validaciones | Desarrolladores backend      |
| **[🏗️ Schema de Base de Datos](database_schema.md)** | Estructura detallada de tablas     | DBAs, desarrolladores        |

### 🔧 Operaciones y Mantenimiento

| Documento                                  | Descripción                      | Audiencia               |
| ------------------------------------------ | -------------------------------- | ----------------------- |
| **[🔧 Mantenimiento](maintenance.md)**     | Procedimientos de mantenimiento  | Administradores, DevOps |
| **[📋 Registro de Cambios](changelog.md)** | Historial de versiones y mejoras | Todo el equipo          |

---

## 🗄️ Database Initializer v2.7.0 - El Corazón del Sistema

### 🎯 Importancia Crítica

El **Database Initializer** es el componente más importante del sistema porque:

- ✅ **Detección automática**: Local vs Railway sin configuración manual
- ✅ **Estructura completa**: 25 tablas + 26 índices automáticamente
- ✅ **Carga incremental**: Solo datos nuevos en ejecuciones posteriores
- ✅ **Filtrado inteligente**: Rechaza automáticamente datos inválidos (BPIN NULL)
- ✅ **UPSERT automático**: Evita duplicados con ON CONFLICT DO UPDATE
- ✅ **Reportes detallados**: Documentación completa de cada operación

### 📋 Documentación Específica

| Documento                                                                    | Enfoque                   | Detalle                                    |
| ---------------------------------------------------------------------------- | ------------------------- | ------------------------------------------ |
| **[🗄️ Database Initializer - Guía Completa](database_initializer_guide.md)** | Manual técnico completo   | Todas las funcionalidades, troubleshooting |
| **[🚀 Guía de Despliegue](deployment_guide.md)**                             | Instrucciones paso a paso | Proceso completo de instalación            |
| **[README.md](../README.md)**                                                | Visión general            | Resumen ejecutivo y comandos básicos       |

---

## 📊 Sistemas de Transformación de Datos

### 🔄 Módulos de Transformación

| Sistema                    | Archivo                                         | Descripción                             | Estado v2.7.0                       |
| -------------------------- | ----------------------------------------------- | --------------------------------------- | ----------------------------------- |
| **Ejecución Presupuestal** | `data_transformation_ejecucion_presupuestal.py` | Movimientos y ejecución presupuestal    | ✅ 11,880 + 11,742 registros        |
| **Contratos SECOP**        | `data_transformation_contratos_secop.py`        | Contratos con arquitectura BPIN-centric | ✅ 744 + 753 registros              |
| **Seguimiento PA**         | `data_transformation_seguimiento_pa.py`         | Plan de Acción detallado                | ✅ 1,396 + 1,990 + 10,737 registros |
| **Unidades Proyecto**      | `data_transformation_unidades_proyecto.py`      | Infraestructura y equipamientos         | ✅ 237 + 103 registros              |

### 📚 Documentación por Sistema

| Documento                                                         | Sistema        | Descripción                           |
| ----------------------------------------------------------------- | -------------- | ------------------------------------- |
| **[📊 Ejecución Presupuestal](ejecucion_presupuestal_system.md)** | Presupuestos   | Procesamiento de datos presupuestales |
| **[📝 Contratos SECOP](contratos_secop_system.md)**               | Contratos      | Sistema de contratos optimizado       |
| **[📈 Seguimiento PA](seguimiento_pa_system.md)**                 | Plan de Acción | Sistema de seguimiento detallado      |

---

## 🚀 Flujo de Trabajo Recomendado

### Para Nuevos Desarrolladores

1. **Lectura inicial**: [README.md](../README.md)
2. **Primera instalación**: [🚀 Guía de Despliegue](deployment_guide.md)
3. **Entender el inicializador**: [🗄️ Database Initializer - Guía](database_initializer_guide.md)
4. **Explorar arquitectura**: [📊 Arquitectura del Sistema](overview.md)
5. **Revisar endpoints**: [🌐 Endpoints de la API](endpoints.md)

### Para Administradores de Sistema

1. **Despliegue inicial**: [🚀 Guía de Despliegue](deployment_guide.md)
2. **Configuración de BD**: [🗄️ Database Initializer - Guía](database_initializer_guide.md)
3. **Mantenimiento regular**: [🔧 Mantenimiento](maintenance.md)
4. **Monitoreo**: [🌐 Endpoints ADMIN](endpoints.md#tag-admin)

### Para Desarrolladores Frontend

1. **Endpoints disponibles**: [🌐 Endpoints de la API](endpoints.md)
2. **Estructura de datos**: [⚙️ Modelos y Esquemas](models_and_schemas.md)
3. **Documentación interactiva**: `http://localhost:8000/docs`

### Para Analistas de Datos

1. **Estructura de datos**: [🏗️ Schema de Base de Datos](database_schema.md)
2. **Sistemas de transformación**: Documentos específicos por sistema
3. **Verificación de datos**: [🗄️ Database Initializer - Reportes](database_initializer_guide.md#-reportes-generados)

---

## 🔧 Comandos de Referencia Rápida

### 🚀 Instalación Completa

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

### 🗄️ Solo Database Initializer

```bash
cd api-dashboard-db
env\Scripts\activate
python database_initializer.py
```

### ✅ Verificación Rápida

```bash
curl http://localhost:8000/health
curl http://localhost:8000/database_status
```

### 🌐 Railway

```bash
railway run python database_initializer.py
railway up
```

---

## 📞 Soporte y Recursos

### 🔍 Diagnóstico de Problemas

1. **Errores de conexión**: [Database Initializer - Solución de Problemas](database_initializer_guide.md#-solución-de-problemas)
2. **Errores de datos**: [Guía de Despliegue - Manejo de Errores](deployment_guide.md#paso-5-manejo-de-errores-comunes)
3. **Performance**: [Mantenimiento](maintenance.md)

### 📊 Verificación de Estado

- **Health Check**: `http://localhost:8000/health`
- **Estado de BD**: `http://localhost:8000/database_status`
- **Documentación**: `http://localhost:8000/docs`
- **Reportes del inicializador**: `database_initialization_report_*.md`

### 🎯 Contacto y Contribución

- **Issues**: Reportar en repositorio GitHub
- **Mejoras**: Pull requests bienvenidos
- **Documentación**: Mantener actualizada con cambios

---

**API Dashboard Alcaldía de Santiago de Cali v2.7.0**  
**Sistema integral con Database Initializer Unificado**
