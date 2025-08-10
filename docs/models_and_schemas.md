# Modelos (SQLAlchemy) y Esquemas (Pydantic)

Modelos principales (resumen):

- CentroGestor(cod_centro_gestor:int, nombre_centro_gestor:text)
- Programa(cod_programa:int, nombre_programa:text)
- AreaFuncional(cod_area_funcional:int, nombre_area_funcional:text)
- Proposito(cod_proposito:int, nombre_proposito:text)
- Reto(cod_reto:int, nombre_reto:text)
- MovimientoPresupuestal(bpin:bigint, periodo_corte:varchar, ppto_inicial, adiciones, reducciones, ppto_modificado)
- EjecucionPresupuestal(bpin:bigint, periodo*corte:varchar, ejecucion, pagos, saldos_cdp, total*\* )
- UnidadProyectoInfraestructuraEquipamientos(bpin:bigint pk, identificador:varchar(255), ...)
- UnidadProyectoInfraestructuraVial(bpin:bigint pk, identificador:varchar(255), ...)

Esquemas Pydantic: equivalentes a los atributos expuestos por los endpoints de POST/PUT/GET.

Notas:

- Campos geométricos no se almacenan en tablas de atributos; GeoJSON se sirve desde archivos.
- bpin se maneja como BIGINT en BD y como int en Pydantic.
