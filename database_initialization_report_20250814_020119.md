# 📊 Reporte de Inicialización de Base de Datos
## API Dashboard Alcaldía de Cali

**Fecha de ejecución:** 2025-08-14 01:44:53  
**Duración total:** 985.53 segundos  
**Entorno:** Local (Desarrollo)  

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| 🗄️ Tablas creadas/actualizadas | 1 |
| 📁 Archivos procesados | 4 |
| 📊 Total de registros cargados | 12,880 |
| ❌ Registros fallidos | 253 |
| ✅ Tasa de éxito | 98.1% |

---

## 📋 Detalle por Tabla

### ✅ Datos Cargados

#### 📊 movimientos_presupuestales
- **Registros:** 11,880
- **Tiempo de carga:** 835.13s
- **Velocidad:** 14.2 registros/segundo
- **Tamaño del archivo:** 4.12 MB

#### 📊 datos_caracteristicos_proyectos
- **Registros:** 1,000
- **Tiempo de carga:** 110.59s
- **Velocidad:** 9.0 registros/segundo
- **Tamaño del archivo:** 1.28 MB

### ⏭️ Datos Omitidos (ya existentes)
- **contratos:** 744 registros existentes
- **contratos_valores:** 753 registros existentes
- **ejecucion_presupuestal:** 11,742 registros existentes
- **seguimiento_pa:** 1,396 registros existentes
- **seguimiento_productos_pa:** 1,990 registros existentes
- **seguimiento_actividades_pa:** 10,737 registros existentes

### ❌ Errores Encontrados (3)

#### datos_caracteristicos_proyectos - failed_records
- **Timestamp:** 02:00:46
- **Detalles:** 253

#### unidades_proyecto_infraestructura_equipamientos - complete_failure
- **Timestamp:** 02:01:11
- **Detalles:** No se pudo cargar ningún registro

#### unidades_proyecto_infraestructura_vial - complete_failure
- **Timestamp:** 02:01:19
- **Detalles:** No se pudo cargar ningún registro

---

## ⚡ Métricas de Rendimiento

### 🕐 Tiempos de Procesamiento

```
Tiempos de carga por tabla:
movimientos_presupuestales          ████████████████████████████████████████ 835.13s
datos_caracteristicos_proyectos     █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 110.59s
```

### 💾 Uso de Memoria

**Aumento total de memoria:** 19.19 MB

```
Aumento de memoria por tabla:
movimientos_presupuestales             18.93 MB
datos_caracteristicos_proyectos         0.26 MB
```

### 📈 Distribución de Registros Cargados

```
Distribución por tabla:
movimientos_presupuestales          ██████████████████████████████████████████████████   11,880 ( 92.2%)
datos_caracteristicos_proyectos     ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    1,000 (  7.8%)
```

---

## 💡 Recomendaciones

### 🔧 Optimizaciones Identificadas

- ⚠️ **datos_caracteristicos_proyectos:** 20.2% de registros fallan - revisar calidad de datos
- 🐌 **movimientos_presupuestales:** 14.2 reg/s - considerar optimización de índices
- 🐌 **datos_caracteristicos_proyectos:** 9.0 reg/s - considerar optimización de índices

### 📊 Próximos Pasos
- ✅ Base de datos lista para consultas
- 🚀 Iniciar API: `uvicorn fastapi_project.main:app --reload`
- 📊 Monitorear logs para consultas lentas
- 🔄 Programar respaldos incrementales

---

*Reporte generado automáticamente el 2025-08-14 02:01:19*
