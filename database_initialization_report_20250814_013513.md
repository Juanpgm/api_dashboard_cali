# 📊 Reporte de Inicialización de Base de Datos
## API Dashboard Alcaldía de Cali

**Fecha de ejecución:** 2025-08-14 01:17:55  
**Duración total:** 1038.44 segundos  
**Entorno:** Local (Desarrollo)  

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| 🗄️ Tablas creadas/actualizadas | 1 |
| 📁 Archivos procesados | 4 |
| 📊 Total de registros cargados | 1,000 |
| ❌ Registros fallidos | 253 |
| ✅ Tasa de éxito | 79.8% |

---

## 📋 Detalle por Tabla

### ✅ Datos Cargados

#### 📊 datos_caracteristicos_proyectos
- **Registros:** 1,000
- **Tiempo de carga:** 113.97s
- **Velocidad:** 8.8 registros/segundo
- **Tamaño del archivo:** 1.28 MB

### ⏭️ Datos Omitidos (ya existentes)
- **contratos:** 744 registros existentes
- **contratos_valores:** 753 registros existentes
- **ejecucion_presupuestal:** 11,742 registros existentes
- **seguimiento_actividades_pa:** 10,737 registros existentes
- **seguimiento_pa:** 1,396 registros existentes
- **seguimiento_productos_pa:** 1,990 registros existentes

### ❌ Errores Encontrados (4)

#### datos_caracteristicos_proyectos - failed_records
- **Timestamp:** 01:19:56
- **Detalles:** 253

#### movimientos_presupuestales - complete_failure
- **Timestamp:** 01:34:40
- **Detalles:** No se pudo cargar ningún registro

#### unidades_proyecto_infraestructura_equipamientos - complete_failure
- **Timestamp:** 01:35:04
- **Detalles:** No se pudo cargar ningún registro

#### unidades_proyecto_infraestructura_vial - complete_failure
- **Timestamp:** 01:35:13
- **Detalles:** No se pudo cargar ningún registro

---

## ⚡ Métricas de Rendimiento

### 🕐 Tiempos de Procesamiento

```
Tiempos de carga por tabla:
datos_caracteristicos_proyectos     ████████████████████████████████████████ 113.97s
```

### 💾 Uso de Memoria

**Aumento total de memoria:** 4.68 MB

```
Aumento de memoria por tabla:
datos_caracteristicos_proyectos         4.68 MB
```

### 📈 Distribución de Registros Cargados

```
Distribución por tabla:
datos_caracteristicos_proyectos     ██████████████████████████████████████████████████    1,000 (100.0%)
```

---

## 💡 Recomendaciones

### 🔧 Optimizaciones Identificadas

- ⚠️ **datos_caracteristicos_proyectos:** 20.2% de registros fallan - revisar calidad de datos
- 🐌 **datos_caracteristicos_proyectos:** 8.8 reg/s - considerar optimización de índices

### 📊 Próximos Pasos
- ✅ Base de datos lista para consultas
- 🚀 Iniciar API: `uvicorn fastapi_project.main:app --reload`
- 📊 Monitorear logs para consultas lentas
- 🔄 Programar respaldos incrementales

---

*Reporte generado automáticamente el 2025-08-14 01:35:13*
