# Cambios y Mejoras (Agosto 2025)

Versión actual: 2.1.0

## Versión 2.1.0 - Agosto 11, 2025

### ✨ Nuevas Funcionalidades

**Sistema de Transformación de Datos "Seguimiento PA"**

- ➕ Nuevo módulo `transformation_app/data_transformation_seguimiento_pa.py`
- ➕ Procesamiento automático de archivos Excel (.xlsx) desde `app_inputs/seguimiento_pa_input/`
- ➕ Generación de 3 datasets JSON estandarizados:
  - `seguimiento_actividades_pa.json` - Actividades de proyectos con datos presupuestales
  - `seguimiento_productos_pa.json` - Productos de proyectos con métricas de avance
  - `seguimiento_pa.json` - Resumen consolidado por proyecto

**Mejoras en Procesamiento de Datos**

- 🔧 Función avanzada de limpieza numérica que preserva valores originales
- 🔧 Soporte para múltiples formatos de números (separadores de miles, decimales)
- 🔧 Detección automática de tipos de archivos Excel (detallados vs resumen)
- 🔧 Manejo robusto de caracteres especiales y encoding UTF-8

**Normalización de Datos**

- 📊 Procesamiento de 10,737+ registros de actividades
- 📊 Procesamiento de 1,990+ registros de productos
- 📊 Generación de 1,396+ registros de resumen
- 📊 Limpieza automática de símbolos monetarios ($, separadores de miles)
- 📊 Conversión inteligente de porcentajes sin pérdida de precisión

### 🛠️ Mejoras Técnicas

**Calidad de Datos**

- ✅ Validación de tipos de datos según estándares del proyecto
- ✅ Códigos BPIN y actividades como enteros (BIGINT)
- ✅ Valores monetarios como decimales con 2 cifras de precisión
- ✅ Fechas en formato ISO estándar (YYYY-MM-DD)
- ✅ Manejo de valores nulos y campos vacíos

**Rendimiento**

- ⚡ Procesamiento batch de múltiples archivos Excel
- ⚡ Salida optimizada en formato JSON para consumo API
- ⚡ Logging detallado del proceso de transformación
- ⚡ Gestión eficiente de memoria para archivos grandes

## Versión 2.0.0 - Agosto 2025

Cambios desde la versión anterior:

- ADMIN dinámico: /database_status y /clear_all_data ahora recorren todas las tablas del schema public.
- tables_info consolidado: atributos por tabla + status (sin segregación por variable).
- NUEVO: PUT de edición por BPIN para equipamientos y vial.
- Removidos: PUT de corrección por BPIN inválido (a petición explícita).
- Cargas masivas más robustas: upsert con ON CONFLICT (claves simples/compuestas) y validación Pydantic.
- Unidades de proyecto: endpoints GET/POST + GeoJSON RFC7946.
- Inicialización: verificación/corrección automática de tipos críticos (bpin BIGINT, identificador VARCHAR).
