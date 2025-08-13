# 📊 Sistema de Ejecución Presupuestal

## 🎯 Versión 2.5.0 - Agosto 13, 2025

### 📋 **Resumen del Sistema**

El sistema de transformación de datos de ejecución presupuestal procesa múltiples archivos CSV mensuales para generar tres tipos de archivos JSON optimizados para consumo API:

1. **Datos característicos de proyectos** (master data)
2. **Movimientos presupuestales** (presupuesto inicial, modificaciones, etc.)
3. **Ejecución presupuestal** (CDPs, obligaciones, pagos, etc.)

---

## 🔧 **Funcionalidades Principales**

### **1. Carga y Normalización de Datos**

- ✅ **Carga automática** de archivos CSV desde `app_inputs/ejecucion_presupuestal_input/`
- ✅ **Detección automática** de separadores (`,`, `;`, `\t`) y encodings (UTF-8, Latin-1, CP1252)
- ✅ **Normalización de columnas**: Eliminación de espacios, acentos y conectores
- ✅ **Mapeo inteligente** de nombres de columnas con variaciones

### **2. Limpieza y Transformación de Datos**

- 🔢 **Limpieza de valores monetarios**: Eliminación de símbolos ($, puntos, comas) preservando dígitos
- 🏷️ **Detección automática de columnas**: Identificación por palabras clave
- 📅 **Generación de períodos**: Formato ISO 8601 basado en nombres de archivo
- 🧹 **Eliminación de datos irrelevantes**: Filtrado de filas con >80% valores nulos

### **3. Agrupación y Consolidación**

- 📊 **Agrupación por BPIN-período**: Eliminación de duplicados manteniendo integridad
- ➕ **Suma de valores**: Agregación correcta de datos financieros por proyecto y fecha
- 🎯 **Reducción inteligente**: 85% menos registros sin pérdida de información

---

## 📁 **Estructura de Archivos**

### **Entrada (Input)**

```
app_inputs/ejecucion_presupuestal_input/
├── EJECUCION_ENERO_2024.csv
├── EJECUCION_FEBRERO_2024.csv
├── EJECUCION_MARZO_2024.csv
├── [... otros meses ...]
├── EJECUCION_ENERO_2025.csv
├── EJECUCION_FEBRERO_2025.csv
└── [... archivos mensuales ...]
```

### **Salida (Output)**

```
app_outputs/ejecucion_presupuestal_outputs/
├── datos_caracteristicos_proyectos.json     # 1,253 registros (1.3 MB)
├── movimientos_presupuestales.json          # 11,880 registros (4.4 MB)
└── ejecucion_presupuestal.json              # 11,742 registros (4.1 MB)
```

---

## 📊 **Esquemas de Datos**

### **1. Datos Característicos de Proyectos**

```json
{
  "bpin": 2019760010223,
  "bp": 7600000123,
  "nombre_proyecto": "Nombre del proyecto",
  "nombre_actividad": "Actividad específica",
  "programa_presupuestal": "Código programa",
  "nombre_centro_gestor": "Centro gestor",
  "nombre_area_funcional": "Área funcional",
  "nombre_fondo": "Nombre del fondo",
  "clasificacion_fondo": "Tipo de fondo",
  "nombre_pospre": "POSPRE",
  "nombre_dimension": "Dimensión",
  "nombre_linea_estrategica": "Línea estratégica",
  "nombre_programa": "Programa",
  "origen": "Origen",
  "anio": 2024,
  "tipo_gasto": "Tipo de gasto"
}
```

### **2. Movimientos Presupuestales**

```json
{
  "bpin": 2019760010223,
  "periodo": "2024-01-31",
  "ppto_inicial": 1000000000,
  "adiciones": 50000000,
  "reducciones": 0,
  "contracreditos": 0,
  "creditos": 0,
  "aplazamiento": 0,
  "desaplazamiento": 0,
  "ppto_modificado": 1050000000,
  "ppto_disponible": 950000000,
  "dataframe_origen": "EJECUCION_ENERO_2024",
  "archivo_origen": "EJECUCION_ENERO_2024.csv"
}
```

### **3. Ejecución Presupuestal**

```json
{
  "bpin": 2019760010223,
  "periodo": "2024-01-31",
  "total_acumulado_cdp": 800000000,
  "total_acumulado_rpc": 600000000,
  "total_acumul_obligac": 500000000,
  "pagos": 400000000,
  "ejecucion": 400000000,
  "saldos_cdp": 200000000,
  "ppto_disponible": 250000000,
  "dataframe_origen": "EJECUCION_ENERO_2024",
  "archivo_origen": "EJECUCION_ENERO_2024.csv"
}
```

---

## ⚙️ **Configuración y Uso**

### **Prerrequisitos**

```bash
pip install pandas numpy tqdm psutil python-dateutil
```

### **Ejecución**

```bash
cd a:\programing_workspace\api-dashboard-db
python transformation_app\data_transformation_ejecucion_presupuestal.py
```

### **Parámetros de Configuración**

| Parámetro        | Descripción                 | Valor por defecto                             |
| ---------------- | --------------------------- | --------------------------------------------- |
| `input_dir`      | Directorio de archivos CSV  | `app_inputs/ejecucion_presupuestal_input/`    |
| `output_dir`     | Directorio de salida JSON   | `app_outputs/ejecucion_presupuestal_outputs/` |
| `null_threshold` | Umbral de eliminación filas | 80% valores nulos                             |

---

## 🚀 **Optimizaciones Implementadas**

### **Integridad de Datos Financieros**

- ✅ **Valores numéricos puros**: Sin decimales, puntos o símbolos
- ✅ **Preservación completa**: Todos los dígitos originales mantenidos
- ✅ **Función clean_monetary_value optimizada**: Solo elimina formateo

### **Performance**

- ⚡ **Tiempo de ejecución**: 9.99 segundos para 96,664 filas
- 💾 **Uso de memoria**: 255.05 MB durante procesamiento
- 📊 **Progress bars**: Visualización detallada del progreso

### **Calidad de Datos**

- 🎯 **Agrupación por BPIN-período**: Eliminación inteligente de duplicados
- 📈 **Reducción de registros**: 85% menos datos sin pérdida de información
- 🔍 **Validación automática**: Filtros para registros significativos

---

## 📈 **Métricas de Rendimiento**

### **Antes de la Optimización**

- ❌ Valores alterados con decimales incorrectos
- ❌ Columnas monetarias faltantes
- ❌ Registros duplicados sin agrupar
- ❌ Datos sin validar

### **Después de la Optimización (v2.5.0)**

- ✅ **Integridad 100%**: Valores financieros exactos
- ✅ **Completitud 100%**: Todas las columnas incluidas
- ✅ **Eficiencia 85%**: Reducción de registros sin pérdida
- ✅ **Performance optimizado**: 9.99s para procesamiento completo

---

## 🔍 **Validación y Calidad**

### **Validaciones Automáticas**

1. **Verificación de BPIN**: Todos los registros deben tener BPIN válido
2. **Validación de período**: Formato ISO 8601 correcto
3. **Integridad monetaria**: Valores numéricos sin alteraciones
4. **Completitud de datos**: Verificación de columnas requeridas

### **Controles de Calidad**

- 🔒 **0 valores NaN**: Eliminación completa de datos faltantes problemáticos
- 🔒 **100% cobertura BPIN**: Consistencia total de identificadores
- 🔒 **Validación de tipos**: Enteros para códigos, valores puros para monetarios
- 🔒 **Trazabilidad**: Origen de datos preservado en cada registro

---

## 🛠️ **Mantenimiento y Actualizaciones**

### **Monitoreo**

- 📊 **Logs detallados**: Información completa del proceso
- 📊 **Métricas de performance**: Tiempo, memoria, registros procesados
- 📊 **Validación de salida**: Verificación automática de archivos generados

### **Escalabilidad**

- 🔧 **Detección automática**: Adaptación a nuevas estructuras de CSV
- 🔧 **Configuración flexible**: Parámetros ajustables según necesidades
- 🔧 **Extensibilidad**: Fácil adición de nuevas transformaciones

---

## 📚 **Documentación Técnica**

### **Funciones Principales**

1. `load_csv_files()` - Carga automática con detección de formato
2. `normalize_dataframes()` - Normalización de nombres de columnas
3. `clean_monetary_value()` - Limpieza de valores financieros
4. `consolidate_dataframes()` - Consolidación y agrupación
5. `create_movimientos_presupuestales()` - Generación de movimientos
6. `create_ejecucion_presupuestal()` - Generación de ejecución

### **Flujo de Procesamiento**

```mermaid
graph TD
    A[Carga CSV] --> B[Normalización]
    B --> C[Mapeo Columnas]
    C --> D[Limpieza Datos]
    D --> E[Consolidación]
    E --> F[Conversión Tipos]
    F --> G[Agrupación BPIN-Período]
    G --> H[Generación JSON]
```

---

**Versión**: 2.5.0  
**Fecha**: Agosto 13, 2025  
**Estado**: Producción Ready  
**Integridad Financiera**: 100%  
**Performance**: Optimizado  
**Archivos obsoletos**: Eliminados
