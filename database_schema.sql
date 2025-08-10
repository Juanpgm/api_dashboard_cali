-- Corrected Database Schema
-- Date: 2025-08-06
-- Description: This script creates the normalized database schema, fixing circular dependencies and incorrect foreign key relationships.

BEGIN;

-- =================================================================
-- TABLE CREATION
-- =================================================================

-- Catalogs and Dimension Tables
CREATE TABLE IF NOT EXISTS public.programas
(
    cod_programa character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_programa character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT programas_pkey PRIMARY KEY (cod_programa)
);

CREATE TABLE IF NOT EXISTS public.centros_gestores
(
    cod_centro_gestor character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_centro_gestor character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT centros_gestores_pkey PRIMARY KEY (cod_centro_gestor)
);

CREATE TABLE IF NOT EXISTS public.lineas_estrategicas
(
    cod_linea_estrategica character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_linea_estrategica character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT lineas_estrategicas_pkey PRIMARY KEY (cod_linea_estrategica)
);

CREATE TABLE IF NOT EXISTS public.propositos
(
    cod_proposito character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_proposito character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT propositos_pkey PRIMARY KEY (cod_proposito)
);

CREATE TABLE IF NOT EXISTS public.categorias_alcalde
(
    cod_categoria_alcalde character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_categoria_alcalde character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT categorias_alcalde_pkey PRIMARY KEY (cod_categoria_alcalde)
);

CREATE TABLE IF NOT EXISTS public.areas_funcionales
(
    cod_area_funcional character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_area_funcional character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT areas_funcionales_pkey PRIMARY KEY (cod_area_funcional)
);

CREATE TABLE IF NOT EXISTS public.dimensiones
(
    cod_dimension character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_dimension character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT dimensiones_pkey PRIMARY KEY (cod_dimension)
);

CREATE TABLE IF NOT EXISTS public.retos
(
    cod_reto character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_reto character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT retos_pkey PRIMARY KEY (cod_reto)
);

CREATE TABLE IF NOT EXISTS public.sectores
(
    cod_sector character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_sector character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT sectores_pkey PRIMARY KEY (cod_sector)
);

CREATE TABLE IF NOT EXISTS public.supervisores
(
    cod_supervisor character varying(50) COLLATE pg_catalog."default" NOT NULL,
    n_documento_supervisor character varying(50) COLLATE pg_catalog."default" UNIQUE,
    nombre_supervisor character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT supervisores_pkey PRIMARY KEY (cod_supervisor)
);

CREATE TABLE IF NOT EXISTS public.bp
(
    bp character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_bp character varying(255) COLLATE pg_catalog."default",
    programa_bp character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT bp_pkey PRIMARY KEY (bp)
);

CREATE TABLE IF NOT EXISTS public.ordenadores_gasto
(
    cod_ordenador_gasto character varying(50) COLLATE pg_catalog."default" NOT NULL,
    n_documento_ordenador character varying(50) COLLATE pg_catalog."default" UNIQUE,
    nombre_ordenador character varying(255) COLLATE pg_catalog."default",
    CONSTRAINT ordenadores_gasto_pkey PRIMARY KEY (cod_ordenador_gasto)
);

CREATE TABLE IF NOT EXISTS public.actividades
(
    cod_actividad character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_actividad character varying(500) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT actividades_pkey PRIMARY KEY (cod_actividad)
);

CREATE TABLE IF NOT EXISTS public.productos
(
    cod_producto character varying(50) COLLATE pg_catalog."default" NOT NULL,
    cod_producto_mga character varying(50) COLLATE pg_catalog."default",
    nombre_producto character varying(500) COLLATE pg_catalog."default" NOT NULL,
    tipo_meta_producto character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT productos_pkey PRIMARY KEY (cod_producto)
);


-- Core Tables
CREATE TABLE IF NOT EXISTS public.proyectos
(
    bpin character varying(50) COLLATE pg_catalog."default" NOT NULL,
    nombre_proyecto_bpin character varying(500) COLLATE pg_catalog."default" NOT NULL,
    nombre_bp character varying(255) COLLATE pg_catalog."default",
    tipo_proyecto character varying(100) COLLATE pg_catalog."default",
    anio_inicio smallint,
    anio_fin smallint,
    urlproyecto text COLLATE pg_catalog."default",
    cod_programa character varying(50) COLLATE pg_catalog."default",
    cod_linea_estrategica character varying(50) COLLATE pg_catalog."default",
    cod_dimension character varying(50) COLLATE pg_catalog."default",
    cod_sector character varying(50) COLLATE pg_catalog."default",
    cod_proposito character varying(50) COLLATE pg_catalog."default",
    cod_reto character varying(50) COLLATE pg_catalog."default",
    cod_area_funcional character varying(50) COLLATE pg_catalog."default",
    cod_centro_gestor character varying(50) COLLATE pg_catalog."default",
    cod_fuente_financiamiento character varying(50) COLLATE pg_catalog."default",
    cod_categoria_alcalde character varying(50) COLLATE pg_catalog."default",
    cod_pospre character varying(50) COLLATE pg_catalog."default",
    bp character varying(50) COLLATE pg_catalog."default",
    cod_comuna character varying(50) COLLATE pg_catalog."default",
    cod_actividad character varying(50) COLLATE pg_catalog."default",
    CONSTRAINT proyectos_pkey PRIMARY KEY (bpin)
);

CREATE TABLE IF NOT EXISTS public.contratos
(
    cod_contrato character varying(100) COLLATE pg_catalog."default" NOT NULL,
    bpin character varying(50) COLLATE pg_catalog."default",
    cod_centro_gestor character varying(50) COLLATE pg_catalog."default",
    cod_proceso_de_compra character varying(100) COLLATE pg_catalog."default",
    duracion_contrato integer,
    dias_adicionados integer,
    estado_contrato character varying(50) COLLATE pg_catalog."default",
    objeto_contrato text COLLATE pg_catalog."default",
    tipo_contrato character varying(100) COLLATE pg_catalog."default",
    descripcion_proceso text COLLATE pg_catalog."default",
    modalidad_contratacion character varying(100) COLLATE pg_catalog."default",
    justificacion_modalidad_contratacion text COLLATE pg_catalog."default",
    condiciones_entrega text COLLATE pg_catalog."default",
    origen_recursos character varying(100) COLLATE pg_catalog."default",
    destino_gasto character varying(100) COLLATE pg_catalog."default",
    estado_bpin character varying(50) COLLATE pg_catalog."default",
    nombre_banco character varying(100) COLLATE pg_catalog."default",
    tipo_cuenta character varying(50) COLLATE pg_catalog."default",
    cod_ordenador_gasto character varying(50) COLLATE pg_catalog."default",
    cod_supervisor character varying(50) COLLATE pg_catalog."default",
    anno_bpin smallint,
    es_pyme boolean,
    habilita_pago_adelantado boolean,
    liquidacion boolean,
    obligacion_ambiental boolean,
    obligaciones_postconsumo boolean,
    reversion boolean,
    espostconflicto boolean,
    contrato_puede_ser_prorrogado boolean,
    urlproceso text COLLATE pg_catalog."default",
    CONSTRAINT contratos_pkey PRIMARY KEY (cod_contrato),
    CONSTRAINT contratos_cod_proceso_de_compra_key UNIQUE (cod_proceso_de_compra)
);

CREATE TABLE IF NOT EXISTS public.contrato_fechas
(
    cod_contrato character varying(100) COLLATE pg_catalog."default" NOT NULL,
    fecha_firma_contrato date,
    fecha_inicio_contrato date,
    fecha_fin_contrato date,
    fecha_notificacion_prorrogacion date,
    ultima_actualizacion timestamp with time zone,
    CONSTRAINT contrato_fechas_pkey PRIMARY KEY (cod_contrato)
);

CREATE TABLE IF NOT EXISTS public.contrato_valores
(
    cod_contrato character varying(100) COLLATE pg_catalog."default" NOT NULL,
    valor_contrato numeric(18, 2),
    valor_pago_adelantado numeric(18, 2),
    valor_facturado numeric(18, 2),
    valor_pendiente_pago numeric(18, 2),
    valor_pagado numeric(18, 2),
    valor_amortizado numeric(18, 2),
    valor_pendiente_amortizacion numeric(18, 2),
    valor_pendiente_ejecucion numeric(18, 2),
    saldo_cdp numeric(18, 2),
    saldo_vigencia numeric(18, 2),
    presupuesto_general_nacion_pgn numeric(18, 2),
    sistema_general_participaciones numeric(18, 2),
    sistema_general_regalias numeric(18, 2),
    recursos_propios_alcaldia numeric(18, 2),
    recursos_credito numeric(18, 2),
    recursos_propios numeric(18, 2),
    CONSTRAINT contrato_valores_pkey PRIMARY KEY (cod_contrato)
);


-- Transactional Tables
CREATE TABLE IF NOT EXISTS public.movimientos_presupuestales
(
    id_movimiento serial PRIMARY KEY,
    bpin character varying(50) COLLATE pg_catalog."default" NOT NULL,
    periodo_corte date NOT NULL,
    ppto_inicial numeric(18, 2),
    adiciones numeric(18, 2),
    reducciones numeric(18, 2),
    ppto_modificado numeric(18, 2),
    CONSTRAINT movimientos_presupuestales_bpin_periodo_corte_key UNIQUE (bpin, periodo_corte)
);

CREATE TABLE IF NOT EXISTS public.ejecucion_presupuestal
(
    id_ejecucion serial PRIMARY KEY,
    bpin character varying(50) COLLATE pg_catalog."default" NOT NULL,
    periodo_corte date NOT NULL,
    ejecucion numeric(18, 2),
    pagos numeric(18, 2),
    saldos_cdp numeric(18, 2),
    total_acumul_obligac numeric(18, 2),
    total_acumulado_cdp numeric(18, 2),
    total_acumulado_rpc numeric(18, 2),
    CONSTRAINT ejecucion_presupuestal_bpin_periodo_corte_key UNIQUE (bpin, periodo_corte)
);

CREATE TABLE IF NOT EXISTS public.seguimiento_pa
(
    id_seguimiento_pa serial PRIMARY KEY,
    bpin character varying(50) COLLATE pg_catalog."default",
    cod_pd_lvl_1 character varying(50) COLLATE pg_catalog."default",
    cod_pd_lvl_2 character varying(50) COLLATE pg_catalog."default",
    cod_pd_lvl_3 character varying(50) COLLATE pg_catalog."default",
    cod_actividad character varying(50) COLLATE pg_catalog."default",
    cod_producto character varying(50) COLLATE pg_catalog."default",
    subdireccion_subsecretaria character varying(255) COLLATE pg_catalog."default",
    mes_reporte smallint,
    anio_reporte smallint,
    avance_proyecto_pa numeric(5, 2),
    ejecucion_ppto_proyecto_pa numeric(18, 2),
    CONSTRAINT seguimiento_pa_bpin_cod_actividad_cod_producto_anio_reporte_key UNIQUE (bpin, cod_actividad, cod_producto, anio_reporte, mes_reporte)
);

CREATE TABLE IF NOT EXISTS public.seguimiento_actividades_pa
(
    id_seguimiento_actividad serial PRIMARY KEY,
    cod_actividad character varying(50) COLLATE pg_catalog."default",
    cod_centro_gestor character varying(50) COLLATE pg_catalog."default",
    nombre_actividad character varying(500) COLLATE pg_catalog."default",
    descripcion_actividad text COLLATE pg_catalog."default",
    mes_reporte smallint,
    anio_reporte smallint,
    fecha_inicio_actividad date,
    fecha_fin_actividad date,
    ppto_inicial_actividad numeric(18, 2),
    ppto_modificado_actividad numeric(18, 2),
    ejecucion_actividad numeric(18, 2),
    obligado_actividad numeric(18, 2),
    pagos_actividad numeric(18, 2),
    avance_actividad numeric(5, 2),
    avance_real_actividad numeric(5, 2),
    avance_actividad_acumulado numeric(5, 2),
    ponderacion_actividad numeric(5, 2),
    CONSTRAINT seguimiento_actividades_pa_cod_actividad_anio_reporte_mes_r_key UNIQUE (cod_actividad, anio_reporte, mes_reporte)
);

CREATE TABLE IF NOT EXISTS public.seguimiento_productos_pa
(
    id_seguimiento_producto serial PRIMARY KEY,
    cod_producto character varying(50) COLLATE pg_catalog."default",
    cod_producto_mga character varying(50) COLLATE pg_catalog."default",
    nombre_producto character varying(500) COLLATE pg_catalog."default",
    tipo_meta_producto character varying(100) COLLATE pg_catalog."default",
    descripcion_avance_producto text COLLATE pg_catalog."default",
    mes_reporte smallint,
    anio_reporte smallint,
    cantidad_programada_producto numeric(18, 2),
    ponderacion_producto numeric(5, 2),
    avance_producto numeric(5, 2),
    ejecucion_fisica_producto numeric(18, 2),
    avance_real_producto numeric(5, 2),
    avance_producto_acumulado numeric(5, 2),
    ejecucion_ppto_producto numeric(18, 2),
    CONSTRAINT seguimiento_productos_pa_cod_producto_anio_reporte_mes_repo_key UNIQUE (cod_producto, anio_reporte, mes_reporte)
);


-- =================================================================
-- FOREIGN KEY CONSTRAINTS
-- =================================================================

-- Foreign Keys for 'proyectos' table
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_programa) REFERENCES public.programas (cod_programa) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_linea_estrategica) REFERENCES public.lineas_estrategicas (cod_linea_estrategica) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_dimension) REFERENCES public.dimensiones (cod_dimension) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_sector) REFERENCES public.sectores (cod_sector) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_proposito) REFERENCES public.propositos (cod_proposito) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_reto) REFERENCES public.retos (cod_reto) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_area_funcional) REFERENCES public.areas_funcionales (cod_area_funcional) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_centro_gestor) REFERENCES public.centros_gestores (cod_centro_gestor) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_categoria_alcalde) REFERENCES public.categorias_alcalde (cod_categoria_alcalde) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (bp) REFERENCES public.bp (bp) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.proyectos
    ADD FOREIGN KEY (cod_actividad) REFERENCES public.actividades (cod_actividad) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

-- Foreign Keys for 'contratos' table
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (bpin) REFERENCES public.proyectos (bpin) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (cod_centro_gestor) REFERENCES public.centros_gestores (cod_centro_gestor) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (cod_ordenador_gasto) REFERENCES public.ordenadores_gasto (cod_ordenador_gasto) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (cod_supervisor) REFERENCES public.supervisores (cod_supervisor) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (cod_contrato) REFERENCES public.contrato_fechas (cod_contrato) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.contratos
    ADD FOREIGN KEY (cod_contrato) REFERENCES public.contrato_valores (cod_contrato) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

-- Foreign Keys for Transactional Tables
ALTER TABLE IF EXISTS public.movimientos_presupuestales
    ADD FOREIGN KEY (bpin) REFERENCES public.proyectos (bpin) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

ALTER TABLE IF EXISTS public.ejecucion_presupuestal
    ADD FOREIGN KEY (bpin) REFERENCES public.proyectos (bpin) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

ALTER TABLE IF EXISTS public.seguimiento_pa
    ADD FOREIGN KEY (bpin) REFERENCES public.proyectos (bpin) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.seguimiento_pa
    ADD FOREIGN KEY (cod_actividad) REFERENCES public.actividades (cod_actividad) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.seguimiento_pa
    ADD FOREIGN KEY (cod_producto) REFERENCES public.productos (cod_producto) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

-- Foreign Keys for 'seguimiento_actividades_pa'
ALTER TABLE IF EXISTS public.seguimiento_actividades_pa
    ADD FOREIGN KEY (cod_actividad) REFERENCES public.actividades (cod_actividad) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;
ALTER TABLE IF EXISTS public.seguimiento_actividades_pa
    ADD FOREIGN KEY (cod_centro_gestor) REFERENCES public.centros_gestores (cod_centro_gestor) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

-- Foreign Keys for 'seguimiento_productos_pa'
ALTER TABLE IF EXISTS public.seguimiento_productos_pa
    ADD FOREIGN KEY (cod_producto) REFERENCES public.productos (cod_producto) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION NOT VALID;

END;
