# Esquema de Base de Datos

- Catálogos: centros_gestores, programas, areas_funcionales, propositos, retos
- Transaccionales: movimientos_presupuestales, ejecucion_presupuestal
- Unidades de Proyecto: unidades_proyecto_infraestructura_equipamientos, unidades_proyecto_infraestructura_vial

Convenciones:

- bpin: BIGINT
- periodo_corte: VARCHAR(50) (YYYY-MM)
- identificador (unidades*proyecto*\*): VARCHAR(255)

Índices recomendados:

- movimientos_presupuestales(bpin), (periodo_corte)
- ejecucion_presupuestal(bpin), (periodo_corte)
- unidades*proyecto*\* (identificador), (comuna_corregimiento), (estado_unidad_proyecto)
