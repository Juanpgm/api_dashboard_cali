# 📊 Reporte de Inicialización de Base de Datos
## API Dashboard Alcaldía de Cali

**Fecha de ejecución:** 2025-08-14 02:05:51  
**Duración total:** 191.48 segundos  
**Entorno:** Local (Desarrollo)  

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| 🗄️ Tablas creadas/actualizadas | 1 |
| 📁 Archivos procesados | 3 |
| 📊 Total de registros cargados | 1,103 |
| ❌ Registros fallidos | 253 |
| ✅ Tasa de éxito | 81.3% |

---

## 📋 Detalle por Tabla

### ✅ Datos Cargados

#### 📊 datos_caracteristicos_proyectos
- **Registros:** 1,000
- **Tiempo de carga:** 123.94s
- **Velocidad:** 8.1 registros/segundo
- **Tamaño del archivo:** 1.28 MB

#### 📊 unidades_proyecto_infraestructura_vial
- **Registros:** 103
- **Tiempo de carga:** 9.65s
- **Velocidad:** 10.7 registros/segundo
- **Tamaño del archivo:** 0.15 MB

### ⏭️ Datos Omitidos (ya existentes)
- **contratos:** 744 registros existentes
- **contratos_valores:** 753 registros existentes
- **movimientos_presupuestales:** 11,880 registros existentes
- **ejecucion_presupuestal:** 11,742 registros existentes
- **seguimiento_pa:** 1,396 registros existentes
- **seguimiento_productos_pa:** 1,990 registros existentes
- **seguimiento_actividades_pa:** 10,737 registros existentes

### ❌ Errores Encontrados (2)

#### datos_caracteristicos_proyectos - failed_records
- **Timestamp:** 02:08:04
- **Detalles:** 253

#### unidades_proyecto_infraestructura_equipamientos - complete_failure
- **Timestamp:** 02:08:52
- **Detalles:** No se pudo cargar ningún registro

---

## ⚡ Métricas de Rendimiento

### 🕐 Tiempos de Procesamiento

```
Tiempos de carga por tabla:
datos_caracteristicos_proyectos     ████████████████████████████████████████ 123.94s
unidades_proyecto_infraestructura_vial ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   9.65s
```

### 💾 Uso de Memoria

**Aumento total de memoria:** 4.52 MB

```
Aumento de memoria por tabla:
datos_caracteristicos_proyectos         4.04 MB
unidades_proyecto_infraestructura_vial     0.49 MB
```

### 📈 Distribución de Registros Cargados

```
Distribución por tabla:
datos_caracteristicos_proyectos     ██████████████████████████████████████████████████    1,000 ( 90.7%)
unidades_proyecto_infraestructura_vial █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      103 (  9.3%)
```

---

## 💡 Recomendaciones

### 🔧 Optimizaciones Identificadas

- ⚠️ **datos_caracteristicos_proyectos:** 20.2% de registros fallan - revisar calidad de datos
- 🐌 **datos_caracteristicos_proyectos:** 8.1 reg/s - considerar optimización de índices
- 🐌 **unidades_proyecto_infraestructura_vial:** 10.7 reg/s - considerar optimización de índices

### 📊 Próximos Pasos
- ✅ Base de datos lista para consultas
- 🚀 Iniciar API: `uvicorn fastapi_project.main:app --reload`
- 📊 Monitorear logs para consultas lentas
- 🔄 Programar respaldos incrementales

---

*Reporte generado automáticamente el 2025-08-14 02:09:02*
