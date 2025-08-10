from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DECIMAL, SmallInteger, ForeignKey, UniqueConstraint, TIMESTAMP, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from fastapi_project.database import Base

# =============================================================================
class CentroGestor(Base):
    __tablename__ = "centros_gestores"

    cod_centro_gestor = Column(Integer, primary_key=True, index=True)
    nombre_centro_gestor = Column(Text, nullable=False)
    
class Programa(Base):
    __tablename__ = "programas"

    cod_programa = Column(Integer, primary_key=True, index=True)
    nombre_programa = Column(Text, nullable=False)

class AreaFuncional(Base):
    __tablename__ = "areas_funcionales"

    cod_area_funcional = Column(Integer, primary_key=True, index=True)
    nombre_area_funcional = Column(Text, nullable=False)

class Proposito(Base):
    __tablename__ = "propositos"

    cod_proposito = Column(Integer, primary_key=True, index=True)
    nombre_proposito = Column(Text, nullable=False)

class Reto(Base):
    __tablename__ = "retos"

    cod_reto = Column(Integer, primary_key=True, index=True)
    nombre_reto = Column(Text, nullable=False)
       
class MovimientoPresupuestal(Base):
    __tablename__ = "movimientos_presupuestales"

    bpin = Column(BigInteger, primary_key=True, index=True)
    periodo_corte = Column(String, primary_key=True, nullable=False)
    ppto_inicial = Column(Float, nullable=False)
    adiciones = Column(Float, nullable=False)
    reducciones = Column(Float, nullable=False)
    ppto_modificado = Column(Float, nullable=False)

class EjecucionPresupuestal(Base):
    __tablename__ = "ejecucion_presupuestal"

    bpin = Column(BigInteger, primary_key=True, index=True)
    periodo_corte = Column(String, primary_key=True, nullable=False)
    ejecucion = Column(Float, nullable=False)
    pagos = Column(Float, nullable=False)
    saldos_cdp = Column(Float, nullable=False)
    total_acumul_obligac = Column(Float, nullable=False)
    total_acumulado_cdp = Column(Float, nullable=False)
    total_acumulado_rpc = Column(Float, nullable=False)
 
# =============================================================================
# Clase: PROYECTO
# =============================================================================

class Proyecto(Base):
    __tablename__ = "proyectos"
    
    bpin = Column(String(50), primary_key=True)
    nombre_proyecto_bpin = Column(String(500), nullable=False)
    nombre_bp = Column(String(255))
    tipo_proyecto = Column(String(100))
    anio_inicio = Column(SmallInteger)
    anio_fin = Column(SmallInteger)
    urlproyecto = Column(Text)
    
    # Foreign Keys - Solo mantener las que tienen clases/tablas definidas
    cod_programa = Column(String(50), ForeignKey("programas.cod_programa"))
    cod_proposito = Column(String(50), ForeignKey("propositos.cod_proposito"))
    cod_reto = Column(String(50), ForeignKey("retos.cod_reto"))
    cod_area_funcional = Column(String(50), ForeignKey("areas_funcionales.cod_area_funcional"))
    cod_centro_gestor = Column(String(50), ForeignKey("centros_gestores.cod_centro_gestor"))
    
    # Campos que serán simples columnas por ahora (sin FK hasta que se definan las tablas)
    cod_linea_estrategica = Column(String(50))
    cod_dimension = Column(String(50))
    cod_sector = Column(String(50))
    cod_fuente_financiamiento = Column(String(50))
    cod_categoria_alcalde = Column(String(50))
    cod_pospre = Column(String(50))
    bp = Column(String(50))
    cod_comuna = Column(String(50))
    cod_actividad = Column(String(50))
    
    # Relaciones - Solo mantener las que tienen clases definidas
    programa = relationship("Programa")
    proposito = relationship("Proposito")
    reto = relationship("Reto")
    area_funcional = relationship("AreaFuncional")
    centro_gestor = relationship("CentroGestor")
    
    # Relaciones comentadas hasta que se definan las clases correspondientes
    # linea_estrategica = relationship("LineaEstrategica", back_populates="proyectos")
    # dimension = relationship("Dimension", back_populates="proyectos")
    # sector = relationship("Sector", back_populates="proyectos")
    # fuente_financiamiento = relationship("FuenteFinanciamiento", back_populates="proyectos")
    # categoria_alcalde = relationship("CategoriaAlcalde", back_populates="proyectos")
    # pospre = relationship("Pospre", back_populates="proyectos")
    # bp_ref = relationship("BP", back_populates="proyectos")
    
    # Relaciones con otras tablas (comentadas temporalmente para simplificar)
    # movimientos_presupuestales = relationship("MovimientoPresupuestal", back_populates="proyecto")
    # ejecucion_presupuestal = relationship("EjecucionPresupuestal", back_populates="proyecto")
    # seguimiento_pa = relationship("SeguimientoPA", back_populates="proyecto")
    # unidades_proyecto = relationship("UnidadProyecto", back_populates="proyecto")
    # contratos = relationship("Contrato", back_populates="proyecto")

class SeguimientoPA(Base):
    __tablename__ = "seguimiento_pa"
    
    id_seguimiento_pa = Column(Integer, primary_key=True, autoincrement=True)
    bpin = Column(String(50), ForeignKey("proyectos.bpin"))
    cod_pd_lvl_1 = Column(String(50))
    cod_pd_lvl_2 = Column(String(50))
    cod_pd_lvl_3 = Column(String(50))
    cod_actividad = Column(String(50))
    cod_producto = Column(String(50))
    subdireccion_subsecretaria = Column(String(255))
    mes_reporte = Column(SmallInteger)
    anio_reporte = Column(SmallInteger)
    avance_proyecto_pa = Column(DECIMAL(5, 2))
    ejecucion_ppto_proyecto_pa = Column(DECIMAL(18, 2))
    
    __table_args__ = (
        UniqueConstraint('bpin', 'cod_actividad', 'cod_producto', 'anio_reporte', 'mes_reporte'),
    )
    
    # Relaciones (comentadas temporalmente)
    # proyecto = relationship("Proyecto", back_populates="seguimiento_pa")

class SeguimientoActividadPA(Base):
    __tablename__ = "seguimiento_actividades_pa"
    
    id_seguimiento_actividad = Column(Integer, primary_key=True, autoincrement=True)
    cod_actividad = Column(String(50))
    cod_centro_gestor = Column(String(50))
    nombre_actividad = Column(String(500))
    descripcion_actividad = Column(Text)
    mes_reporte = Column(SmallInteger)
    anio_reporte = Column(SmallInteger)
    fecha_inicio_actividad = Column(Date)
    fecha_fin_actividad = Column(Date)
    ppto_inicial_actividad = Column(DECIMAL(18, 2))
    ppto_modificado_actividad = Column(DECIMAL(18, 2))
    ejecucion_actividad = Column(DECIMAL(18, 2))
    obligado_actividad = Column(DECIMAL(18, 2))
    pagos_actividad = Column(DECIMAL(18, 2))
    avance_actividad = Column(DECIMAL(5, 2))
    avance_real_actividad = Column(DECIMAL(5, 2))
    avance_actividad_acumulado = Column(DECIMAL(5, 2))
    ponderacion_actividad = Column(DECIMAL(5, 2))
    
    __table_args__ = (
        UniqueConstraint('cod_actividad', 'anio_reporte', 'mes_reporte'),
    )

class SeguimientoProductoPA(Base):
    __tablename__ = "seguimiento_productos_pa"
    
    id_seguimiento_producto = Column(Integer, primary_key=True, autoincrement=True)
    cod_producto = Column(String(50))
    cod_producto_mga = Column(String(50))
    nombre_producto = Column(String(500))
    tipo_meta_producto = Column(String(100))
    descripcion_avance_producto = Column(Text)
    mes_reporte = Column(SmallInteger)
    anio_reporte = Column(SmallInteger)
    cantidad_programada_producto = Column(DECIMAL(18, 2))
    ponderacion_producto = Column(DECIMAL(5, 2))
    avance_producto = Column(DECIMAL(5, 2))
    ejecucion_fisica_producto = Column(DECIMAL(18, 2))
    avance_real_producto = Column(DECIMAL(5, 2))
    avance_producto_acumulado = Column(DECIMAL(5, 2))
    ejecucion_ppto_producto = Column(DECIMAL(18, 2))
    
    __table_args__ = (
        UniqueConstraint('cod_producto', 'anio_reporte', 'mes_reporte'),
    )

class UnidadProyecto(Base):
    __tablename__ = "unidades_proyecto"
    
    identificador = Column(Integer, primary_key=True, autoincrement=True)
    bpin = Column(String(50), ForeignKey("proyectos.bpin"), nullable=False)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    tipo_proyecto = Column(String(100))
    tipo_unidad_proyecto = Column(String(100))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    ppto_base = Column(DECIMAL(18, 2))
    pagos_realizados = Column(DECIMAL(18, 2))
    geom = Column(Geometry('POINT', srid=4326))
    
    # Relaciones (comentadas temporalmente)
    # proyecto = relationship("Proyecto", back_populates="unidades_proyecto")

class UnidadProyectoInfraestructuraEquipamientos(Base):
    __tablename__ = "unidades_proyecto_infraestructura_equipamientos"
    
    identificador = Column(Integer, primary_key=True, autoincrement=True)
    cod_fuente_financiamiento = Column(String(50))
    usuarios_beneficiarios = Column(Integer)
    dataframe = Column(Text)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    comuna_corregimiento = Column(String(100))
    barrio_vereda = Column(String(100))
    direccion = Column(String(255))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    ppto_base = Column(DECIMAL(18, 2))
    pagos_realizados = Column(DECIMAL(18, 2))
    avance_fisico_obra = Column(DECIMAL(5, 2))
    ejecucion_financiera_obra = Column(DECIMAL(18, 2))
    geom = Column(Geometry('POINT', srid=4326))

class UnidadProyectoInfraestructuraVial(Base):
    __tablename__ = "unidades_proyecto_infraestructura_vial"
    
    identificador = Column(Integer, primary_key=True, autoincrement=True)
    id_via = Column(String(50))
    cod_fuente_financiamiento = Column(String(50))
    usuarios_beneficiarios = Column(Integer)
    dataframe = Column(Text)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    comuna_corregimiento = Column(String(100))
    barrio_vereda = Column(String(100))
    direccion = Column(String(255))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    unidad_medicion = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    longitud_proyectada = Column(DECIMAL(10, 2))
    longitud_ejecutada = Column(DECIMAL(10, 2))
    ppto_base = Column(DECIMAL(18, 2))
    pagos_realizados = Column(DECIMAL(18, 2))
    avance_fisico_obra = Column(DECIMAL(5, 2))
    ejecucion_financiera_obra = Column(DECIMAL(18, 2))
    geom = Column(Geometry('MULTILINESTRING', srid=4326))

# =============================================================================
# Clase: CONTRATO
# =============================================================================

class OrdenadorGasto(Base):
    __tablename__ = "ordenadores_gasto"
    
    cod_ordenador_gasto = Column(String(50), primary_key=True)
    n_documento_ordenador = Column(String(50))
    nombre_ordenador = Column(String(255))

class Supervisor(Base):
    __tablename__ = "supervisores"
    
    cod_supervisor = Column(String(50), primary_key=True)
    n_documento_supervisor = Column(String(50))
    nombre_supervisor = Column(String(255))

class Contrato(Base):
    __tablename__ = "contratos"
    
    cod_contrato = Column(String(100), primary_key=True)
    bpin = Column(String(50), ForeignKey("proyectos.bpin"))
    cod_centro_gestor = Column(String(50), ForeignKey("centros_gestores.cod_centro_gestor"))
    cod_proceso_de_compra = Column(String(100), unique=True)
    duracion_contrato = Column(Integer)
    dias_adicionados = Column(Integer)
    estado_contrato = Column(String(50))
    objeto_contrato = Column(Text)
    tipo_contrato = Column(String(100))
    descripcion_proceso = Column(Text)
    modalidad_contratacion = Column(String(100))
    justificacion_modalidad_contratacion = Column(Text)
    condiciones_entrega = Column(Text)
    origen_recursos = Column(String(100))
    destino_gasto = Column(String(100))
    estado_bpin = Column(String(50))
    nombre_banco = Column(String(100))
    tipo_cuenta = Column(String(50))
    nombre_ordenador_gasto = Column(String(255))
    nombre_supervisor = Column(String(255))
    anno_bpin = Column(SmallInteger)
    es_pyme = Column(Boolean)
    habilita_pago_adelantado = Column(Boolean)
    liquidacion = Column(Boolean)
    obligacion_ambiental = Column(Boolean)
    obligaciones_postconsumo = Column(Boolean)
    reversion = Column(Boolean)
    espostconflicto = Column(Boolean)
    contrato_puede_ser_prorrogado = Column(Boolean)
    urlproceso = Column(Text)
    
    # Relaciones (comentadas temporalmente)
    # proyecto = relationship("Proyecto", back_populates="contratos")
    centro_gestor = relationship("CentroGestor")
    valores = relationship("ContratoValor", back_populates="contrato", uselist=False)
    fechas = relationship("ContratoFecha", back_populates="contrato", uselist=False)

class ContratoValor(Base):
    __tablename__ = "contrato_valores"
    
    cod_contrato = Column(String(100), ForeignKey("contratos.cod_contrato"), primary_key=True)
    valor_contrato = Column(DECIMAL(18, 2))
    valor_pago_adelantado = Column(DECIMAL(18, 2))
    valor_facturado = Column(DECIMAL(18, 2))
    valor_pendiente_pago = Column(DECIMAL(18, 2))
    valor_pagado = Column(DECIMAL(18, 2))
    valor_amortizado = Column(DECIMAL(18, 2))
    valor_pendiente_amortizacion = Column(DECIMAL(18, 2))
    valor_pendiente_ejecucion = Column(DECIMAL(18, 2))
    saldo_cdp = Column(DECIMAL(18, 2))
    saldo_vigencia = Column(DECIMAL(18, 2))
    presupuesto_general_nacion_pgn = Column(DECIMAL(18, 2))
    sistema_general_participaciones = Column(DECIMAL(18, 2))
    sistema_general_regalias = Column(DECIMAL(18, 2))
    recursos_propios_alcaldia = Column(DECIMAL(18, 2))
    recursos_credito = Column(DECIMAL(18, 2))
    recursos_propios = Column(DECIMAL(18, 2))
    
    # Relaciones
    contrato = relationship("Contrato", back_populates="valores")

class ContratoFecha(Base):
    __tablename__ = "contrato_fechas"
    
    cod_contrato = Column(String(100), ForeignKey("contratos.cod_contrato"), primary_key=True)
    fecha_firma_contrato = Column(Date)
    fecha_inicio_contrato = Column(Date)
    fecha_fin_contrato = Column(Date)
    fecha_notificacion_prorrogacion = Column(Date)
    ultima_actualizacion = Column(TIMESTAMP(timezone=True))
    
    # Relaciones
    contrato = relationship("Contrato", back_populates="fechas")

# =============================================================================
# Clase: CARTOGRAFIA_BASE
# =============================================================================

class Corregimiento(Base):
    __tablename__ = "corregimientos"
    
    id_corregimiento = Column(String(50), primary_key=True)
    nombre_corregimiento = Column(String(100), nullable=False)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))

class Comuna(Base):
    __tablename__ = "comunas"
    
    id_comuna = Column(String(50), primary_key=True)
    nombre_comuna = Column(String(100), nullable=False)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))

class Vereda(Base):
    __tablename__ = "veredas"
    
    id_vereda = Column(String(50), primary_key=True)
    nombre_vereda = Column(String(100), nullable=False)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))

class Barrio(Base):
    __tablename__ = "barrios"
    
    id_barrio = Column(String(50), primary_key=True)
    nombre_barrio = Column(String(100), nullable=False)
    estrato_barrio = Column(SmallInteger)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))

class Equipamiento(Base):
    __tablename__ = "equipamientos"
    
    id_equipamiento = Column(String(50), primary_key=True)
    nombre_equipamiento = Column(String(255), nullable=False)
    servicio_equipamiento = Column(String(100))
    escala_equipamiento = Column(String(100))
    geom = Column(Geometry('POINT', srid=4326))

class Via(Base):
    __tablename__ = "vias"
    
    id_via = Column(String(50), primary_key=True)
    nombre_via = Column(String(255))
    longitud_via = Column(DECIMAL(10, 2))
    geom = Column(Geometry('MULTILINESTRING', srid=4326))

# =============================================================================
# Mantener el modelo original para compatibilidad hacia atrás
# =============================================================================

class ProjectExecution(Base):
    __tablename__ = "project_execution"

    id = Column(Integer, primary_key=True, index=True)
    bpin = Column(String, index=True)
    adiciones = Column(Float)
    anio = Column(Integer)
    aplazamiento = Column(Float)
    area_funcional = Column(String)
    bp = Column(String)
    centro_gestor = Column(String)
    clasificacion_fondo = Column(String)
    comuna = Column(String)
    contracreditos = Column(Float)
    creditos = Column(Float)
    dataframe_origen = Column(String)
    desaplazamiento = Column(Float)
    dimension = Column(String)
    ejecucion = Column(Float)
    fondo = Column(String)
    linea_estrategica = Column(String)
    nombre_actividad = Column(String)
    nombre_area_funcional = Column(String)
    nombre_centro_gestor = Column(String)
    nombre_dimension = Column(String)
    nombre_fondo = Column(String)
    nombre_linea_estrategica = Column(String)
    nombre_pospre = Column(String)
    nombre_programa = Column(String)
    nombre_proyecto = Column(String)
    organismo = Column(String)
    origen = Column(String)
    pagos = Column(Float)
    periodo = Column(Date)
    pospre = Column(String)
    ppto_disponible = Column(Float)
    ppto_inicial = Column(Float)
    ppto_modificado = Column(Float)
    programa_presupuestal = Column(String)
    reducciones = Column(Float)
    saldos_cdp = Column(Float)
    tipo_gasto = Column(String)
    total_acumul_obligac = Column(Float)
    total_acumulado_cdp = Column(Float)
    total_acumulado_rpc = Column(Float)
    vigencia = Column(Integer)
