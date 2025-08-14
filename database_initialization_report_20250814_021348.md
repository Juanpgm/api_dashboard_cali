# 📊 Reporte de Inicialización de Base de Datos
## API Dashboard Alcaldía de Cali

**Fecha de ejecución:** 2025-08-14 02:11:52  
**Duración total:** 115.73 segundos  
**Entorno:** Local (Desarrollo)  

---

## 📈 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| 🗄️ Tablas creadas/actualizadas | 1 |
| 📁 Archivos procesados | 2 |
| 📊 Total de registros cargados | 1,489 |
| ❌ Registros fallidos | 0 |
| ✅ Tasa de éxito | 100.0% |

---

## 📋 Detalle por Tabla

### ✅ Datos Cargados

#### 📊 datos_caracteristicos_proyectos
- **Registros:** 1,252
- **Tiempo de carga:** 88.61s
- **Velocidad:** 14.1 registros/segundo
- **Tamaño del archivo:** 1.28 MB

#### 📊 unidades_proyecto_infraestructura_equipamientos
- **Registros:** 237
- **Tiempo de carga:** 17.79s
- **Velocidad:** 13.3 registros/segundo
- **Tamaño del archivo:** 0.35 MB

### ⏭️ Datos Omitidos (ya existentes)
- **contratos:** 744 registros existentes
- **contratos_valores:** 753 registros existentes
- **movimientos_presupuestales:** 11,880 registros existentes
- **ejecucion_presupuestal:** 11,742 registros existentes
- **seguimiento_pa:** 1,396 registros existentes
- **seguimiento_productos_pa:** 1,990 registros existentes
- **seguimiento_actividades_pa:** 10,737 registros existentes
- **unidades_proyecto_infraestructura_vial:** 21 registros existentes

---

## ⚡ Métricas de Rendimiento

### 🕐 Tiempos de Procesamiento

```
Tiempos de carga por tabla:
datos_caracteristicos_proyectos     ████████████████████████████████████████  88.61s
unidades_proyecto_infraestructura_equipamientos ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  17.79s
```

### 💾 Uso de Memoria

**Aumento total de memoria:** 5.34 MB

```
Aumento de memoria por tabla:
datos_caracteristicos_proyectos         4.76 MB
unidades_proyecto_infraestructura_equipamientos     0.59 MB
```

### 📈 Distribución de Registros Cargados

```
Distribución por tabla:
datos_caracteristicos_proyectos     ██████████████████████████████████████████████████    1,252 ( 84.1%)
unidades_proyecto_infraestructura_equipamientos █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      237 ( 15.9%)
```

---

## 💡 Recomendaciones

### 🔧 Optimizaciones Identificadas

- 🐌 **datos_caracteristicos_proyectos:** 14.1 reg/s - considerar optimización de índices
- 🐌 **unidades_proyecto_infraestructura_equipamientos:** 13.3 reg/s - considerar optimización de índices

### 📊 Próximos Pasos
- ✅ Base de datos lista para consultas
- 🚀 Iniciar API: `uvicorn fastapi_project.main:app --reload`
- 📊 Monitorear logs para consultas lentas
- 🔄 Programar respaldos incrementales

---

*Reporte generado automáticamente el 2025-08-14 02:13:48*
